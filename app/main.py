"""FastAPI application entry point."""

from fastapi import FastAPI
from app.api import chat

app = FastAPI(
    title="Chat Assistant with Session Memory",
    description="A chat assistant backend with automatic session summarization and query understanding",
    version="1.0.0"
)

app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Chat Assistant with Session Memory API",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/chat",
            "session_messages": "/api/sessions/{session_id}/messages",
            "session_summary": "/api/sessions/{session_id}/summary"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
