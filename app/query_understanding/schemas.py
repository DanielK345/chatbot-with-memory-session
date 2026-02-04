"""Pydantic schemas for query understanding pipeline per fix.txt."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SpellingCheckResult(BaseModel):
    """Result of spelling check."""
    original_query: str = Field(description="Original user query")
    has_spelling_error: bool = Field(description="Whether spelling errors were found")
    rewritten_query: Optional[str] = Field(default=None, description="Rewritten query if errors found")


class AmbiguityAnalysis(BaseModel):
    """Analysis of query ambiguity (fix.txt section 2)."""
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    ambiguity_reason: Optional[str] = Field(default=None, description="Reason for ambiguity if detected")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")


class AnswerabilityAnalysis(BaseModel):
    """Result of answerability check (fix.txt section 3)."""
    is_answerable: bool = Field(description="Whether the query is answerable")
    reason: str = Field(description="Reason for answerability determination")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence in assessment")
    similar_previous_queries: List[str] = Field(default_factory=list, description="Similar previously answered queries")


class QueryUnderstanding(BaseModel):
    """Complete query understanding output per fix.txt pipeline."""
    original_query: str = Field(description="Original user query")
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    is_answerable: bool = Field(description="Whether the query is answerable")
    rewritten_query: Optional[str] = Field(default=None, description="Rewritten/clarified query if ambiguous")
    ambiguity_reason: Optional[str] = Field(default=None, description="Reason for ambiguity")
    refined_query: Optional[str] = Field(default=None, description="Further refined query with entity resolution")
    needed_context_from_memory: List[str] = Field(
        default_factory=list,
        description="Memory fields needed for context (e.g., 'user_profile.prefs', 'key_facts')"
    )
    clarifying_questions: List[str] = Field(
        default_factory=list,
        description="Clarifying questions (if answerable=false)"
    )
    final_augmented_context: Optional[str] = Field(
        default=None,
        description="Final augmented context combining memory and recent messages"
    )
    pipeline_metadata: dict = Field(
        default_factory=dict,
        description="Metadata about pipeline execution (stages run, confidence scores, etc.)"
    )
