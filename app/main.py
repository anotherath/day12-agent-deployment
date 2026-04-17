"""
Production VinFast AI Agent — Lab 6 Deployment Ready

Checklist:
  ✅ Config from environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting (10 req/min)
  ✅ Cost guard ($10/month)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers
  ✅ CORS
  ✅ Error handling
"""
import os
import sys
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path so we can import agent.py and tools.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import check_rate_limit
from app.cost_guard import check_and_record_cost, get_monthly_spending

# Import the LangGraph agent
from agent import graph

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Lifespan — startup / shutdown
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    time.sleep(0.5)  # simulate init
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        _error_count += 1
        logger.error(json.dumps({
            "event": "error",
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
        }))
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000,
                         description="Your message to the VinFast AI agent")
    session_id: str = Field(default="default_session", min_length=1, max_length=100)

class ChatResponse(BaseModel):
    reply: str
    session_id: str


# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "chat": "POST /chat (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe. Platform restarts container if this fails."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe. Load balancer stops routing here if not ready."""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
async def chat_with_agent(
    body: ChatRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Chat with the VinFast AI Agent.

    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    # Rate limit per API key
    check_rate_limit(_key[:8])

    session_id = body.session_id

    # Initialize session history if it doesn't exist
    # NOTE: In production with Redis, this would use Redis. For now, in-memory.
    from app.main import _SESSIONS
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = []

    # Get the history for this session
    chat_history = _SESSIONS[session_id]

    # Append the new user message
    chat_history.append(("human", body.message))

    # Estimate input tokens (rough: 2 tokens per word)
    input_tokens = len(body.message.split()) * 2
    check_and_record_cost(_key[:8], input_tokens, 0)

    logger.info(json.dumps({
        "event": "agent_call",
        "session_id": session_id,
        "msg_len": len(body.message),
        "client": str(request.client.host) if request.client else "unknown",
    }))

    try:
        # Invoke the LangGraph agent
        result = graph.invoke({"messages": chat_history})

        # Update our session memory with the full history
        _SESSIONS[session_id] = result["messages"]

        # Find the final text response (skip intermediate tool calls)
        final_answer = ""
        for msg in reversed(result["messages"]):
            if hasattr(msg, 'content') and msg.content:
                if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    final_answer = msg.content
                    break

        if not final_answer:
            final_answer = "Xin lỗi, tôi không thể xử lý yêu cầu này lúc này."

        # Estimate output tokens
        output_tokens = len(final_answer.split()) * 2
        check_and_record_cost(_key[:8], 0, output_tokens)

        return ChatResponse(
            reply=final_answer,
            session_id=session_id
        )

    except Exception as e:
        logger.error(json.dumps({
            "event": "agent_error",
            "session_id": session_id,
            "error": str(e),
        }))
        raise HTTPException(status_code=500, detail="Agent processing error. Please try again.")


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Basic metrics (protected)."""
    check_rate_limit(_key[:8])
    spending = get_monthly_spending(_key[:8])
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "monthly_spending": spending,
    }


# In-memory sessions (fallback when Redis not available)
# NOTE: For true statelessness, use Redis.
_SESSIONS: dict = {}


# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
