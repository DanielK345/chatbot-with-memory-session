"""FastAPI chat endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""
    session_id: str = Field(description="Session identifier")
    message: str = Field(description="User message")
    max_context_tokens: Optional[int] = Field(default=10000, description="Max tokens before summarization")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(description="Assistant response")
    query_understanding: dict = Field(description="Query understanding output")
    session_memory: Optional[dict] = Field(default=None, description="Session memory if available")
    pipeline_metadata: dict = Field(description="Pipeline execution metadata")


# Global pipeline instance (in production, use dependency injection)
_pipeline: Optional[ChatPipeline] = None


def get_pipeline() -> ChatPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        session_store = SessionStore(storage_type="file")  # Use file-based for simplicity
        # Use unified LLM client with Gemini as default, Ollama as fallback
        llm_client = LLMClient(primary="gemini")
        _pipeline = ChatPipeline(session_store, llm_client)
    return _pipeline


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message through the pipeline.
    
    - **session_id**: Unique session identifier
    - **message**: User's message
    - **max_context_tokens**: Optional override for context threshold
    """
    try:
        logger.info(f"Received chat request for session {request.session_id}")
        pipeline = get_pipeline()
        if request.max_context_tokens:
            pipeline.max_context_tokens = request.max_context_tokens
            logger.debug(f"Updated max_context_tokens to {request.max_context_tokens}")
        
        result = await pipeline.process_message(request.session_id, request.message)
        logger.info(f"Successfully processed message for session {request.session_id}")
        return ChatResponse(**result)
    except Exception as e:
        error_msg = f"Error processing message for session {request.session_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a session."""
    logger.debug(f"Fetching messages for session {session_id}")
    pipeline = get_pipeline()
    messages = pipeline.session_store.get_messages(session_id)
    logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
    return {"session_id": session_id, "messages": messages}


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get session summary if available."""
    logger.debug(f"Fetching summary for session {session_id}")
    pipeline = get_pipeline()
    summary = pipeline.session_store.get_summary(session_id)
    if summary:
        logger.info(f"Retrieved summary for session {session_id}")
        return summary.model_dump()
    logger.debug(f"No summary found for session {session_id}")
    return {"message": "No summary available for this session"}
