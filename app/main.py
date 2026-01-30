"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import chat
from app.utils.logging import configure_logging_from_env, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI application."""
    # Startup
    configure_logging_from_env()
    logger = get_logger(__name__)
    logger.info("Starting Chat Assistant with Session Memory API")
    logger.info("Logging configured successfully")
    yield
    # Shutdown (if needed in the future)
    logger.info("Shutting down Chat Assistant API")


app = FastAPI(
    title="Chat Assistant with Session Memory",
    description="A chat assistant backend with automatic session summarization and query understanding",
    version="1.0.0",
    lifespan=lifespan
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
