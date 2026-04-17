# VinFast AI Agent — Production Ready

AI Assistant tư vấn xe ô tô điện VinFast, built với LangGraph + FastAPI, production-ready cho Lab 6.

## Features

- 🤖 **LangGraph Agent** — GPT-4o-mini với 3 tools (search_car, check_promotions, calculate_rolling_price)
- 🔐 **API Key Authentication** — Bảo vệ endpoint bằng `X-API-Key`
- ⏱️ **Rate Limiting** — 10 requests/minute per user
- 💰 **Cost Guard** — $10/month budget limit
- 🏥 **Health + Readiness Checks** — `/health`, `/ready`
- 🛑 **Graceful Shutdown** — Xử lý SIGTERM
- 📊 **Structured JSON Logging**
- 🐳 **Docker Multi-stage Build** — Image < 500MB
- ☁️ **Render Deploy Ready** — `render.yaml` included

## Project Structure

```
lab6_vinfast_agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + endpoints
│   ├── config.py            # 12-factor config (env vars)
│   ├── auth.py              # API Key authentication
│   ├── rate_limiter.py      # Rate limiting (10 req/min)
│   └── cost_guard.py        # Budget protection ($10/month)
├── agent.py                 # LangGraph core agent
├── tools.py                 # 3 LangChain tools
├── system_prompt.txt        # System prompt
├── Sale.md                  # VinFast sales policies
├── vinhomes_promotion.md    # Vinhomes promotions
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Local stack
├── render.yaml              # Render Blueprint
├── requirements.txt         # Dependencies
├── .env.example             # Env template
├── .dockerignore            # Docker ignore
└── README.md                # This file
```

## Quick Start

### 1. Setup Environment

```bash
cp .env.example .env.local
# Edit .env.local — add your OPENAI_API_KEY and AGENT_API_KEY
```

### 2. Run Locally

```bash
# With Python
pip install -r requirements.txt
python -m app.main

# Or with Docker Compose
docker compose up
```

### 3. Test

```bash
# Health check
curl http://localhost:8000/health

# Chat (with API key)
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho tôi biết giá VF 5", "session_id": "test-session"}'
```

## Deploy to Railway

### Bước 1: Cài Railway CLI
```bash
npm i -g @railway/cli
```

### Bước 2: Login
```bash
railway login
```

### Bước 3: Init project
```bash
cd lab6_vinfast_agent
railway init
```

### Bước 4: Set environment variables
```bash
railway variables set OPENAI_API_KEY=sk-your-key
railway variables set AGENT_API_KEY=your-secret-key
railway variables set ENVIRONMENT=production
```

### Bước 5: Deploy
```bash
railway up
```

### Bước 6: Lấy public URL
```bash
railway domain
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | App info |
| `/health` | GET | No | Liveness probe |
| `/ready` | GET | No | Readiness probe |
| `/chat` | POST | Yes | Chat with agent |
| `/metrics` | GET | Yes | Usage metrics |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `ENVIRONMENT` | development | dev/staging/production |
| `AGENT_API_KEY` | dev-key-change-me | API Key for auth |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `LLM_MODEL` | gpt-4o-mini | LLM model |
| `RATE_LIMIT_PER_MINUTE` | 10 | Rate limit |
| `MONTHLY_BUDGET_USD` | 10.0 | Cost guard budget |
| `REDIS_URL` | — | Optional Redis URL |

## Lab 6 Checklist

- [x] REST API hoạt động
- [x] Docker multi-stage build
- [x] Config từ environment variables
- [x] API Key authentication
- [x] Rate limiting (10 req/min)
- [x] Cost guard ($10/month)
- [x] Health check endpoint
- [x] Readiness check endpoint
- [x] Graceful shutdown
- [x] Structured JSON logging
- [x] Render deploy ready
