"""Pydantic schemas for session memory and summaries."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile extracted from conversation."""
    prefs: List[str] = Field(default_factory=list, description="User preferences")
    constraints: List[str] = Field(default_factory=list, description="User constraints")


class MessageRange(BaseModel):
    """Range of messages that were summarized."""
    from_index: int = Field(description="Starting message index (0-based)")
    to_index: int = Field(description="Ending message index (exclusive)")


class SessionSummary(BaseModel):
    """Structured session summary extracted from conversation."""
    user_profile: UserProfile = Field(default_factory=UserProfile, description="User profile information")
    key_facts: List[str] = Field(default_factory=list, description="Key facts mentioned in conversation")
    decisions: List[str] = Field(default_factory=list, description="Decisions made during conversation")
    open_questions: List[str] = Field(default_factory=list, description="Open questions that remain")
    todos: List[str] = Field(default_factory=list, description="Action items or todos")


class SessionMemory(BaseModel):
    """Complete session memory including summary and metadata."""
    session_summary: SessionSummary = Field(description="Structured session summary")
    message_range_summarized: MessageRange = Field(description="Range of messages that were summarized")
    created_at: Optional[str] = Field(default=None, description="Timestamp when summary was created")
