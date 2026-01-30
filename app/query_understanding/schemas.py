"""Pydantic schemas for query understanding pipeline."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AmbiguityAnalysis(BaseModel):
    """Analysis of query ambiguity."""
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    ambiguity_reason: Optional[str] = Field(default=None, description="Reason for ambiguity if detected")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score for ambiguity detection")


class QueryUnderstanding(BaseModel):
    """Complete query understanding output."""
    original_query: str = Field(description="Original user query")
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    rewritten_query: Optional[str] = Field(default=None, description="Rewritten/clarified query if ambiguous")
    ambiguity_reason: Optional[str] = Field(default=None, description="Reason for ambiguity")
    needed_context_from_memory: List[str] = Field(
        default_factory=list,
        description="Memory fields needed for context (e.g., 'user_profile.prefs', 'open_questions')"
    )
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="Clarifying questions (1-3 max) if query remains unclear after rewrite"
    )
    final_augmented_context: Optional[str] = Field(
        default=None,
        description="Final augmented context combining memory and recent messages"
    )
