"""FastAPI chat endpoint."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient

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
        pipeline = get_pipeline()
        if request.max_context_tokens:
            pipeline.max_context_tokens = request.max_context_tokens
        
        result = await pipeline.process_message(request.session_id, request.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a session."""
    pipeline = get_pipeline()
    messages = pipeline.session_store.get_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get session summary if available."""
    pipeline = get_pipeline()
    summary = pipeline.session_store.get_summary(session_id)
    if summary:
        return summary.model_dump()
    return {"message": "No summary available for this session"}
