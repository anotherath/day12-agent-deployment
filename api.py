from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from agent import graph

app = FastAPI(title="VinFast Assistant API")

# Setup CORS to allow the frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development, specify your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store chat history in memory based on a session ID (simple approach for now)
# In production, this should be a database like Redis or PostgreSQL
SESSIONS = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.get("/")
def read_root():
    return {"message": "Welcome to VinFast Assistant API"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    try:
        session_id = request.session_id
        
        # Initialize session history if it doesn't exist
        if session_id not in SESSIONS:
            SESSIONS[session_id] = []
            
        # Get the history for this session
        chat_history = SESSIONS[session_id]
        
        # Append the new user message
        chat_history.append(("human", request.message))
        
        # Invoke the LangGraph agent
        # LangGraph will wait for all tool calls (thinking) to finish before returning
        result = graph.invoke({"messages": chat_history})
        
        # Update our session memory with the full history
        SESSIONS[session_id] = result["messages"]
        
        # Find the final text response (skip intermediate tool calls)
        final_answer = ""
        for msg in reversed(result["messages"]):
            # Check for content and ensure it's not a tool call message
            if hasattr(msg, 'content') and msg.content:
                # If it's an AIMessage, make sure it doesn't have tool_calls
                if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    final_answer = msg.content
                    break
        
        if not final_answer:
            final_answer = "Xin lỗi, tôi không thể xử lý yêu cầu này lúc này."
            
        return ChatResponse(
            reply=final_answer,
            session_id=session_id
        )
        
    except Exception as e:
        print(f"Error during API call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting VinFast Assistant API on http://0.0.0.0:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
