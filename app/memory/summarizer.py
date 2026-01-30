"""Session summarization using LLM with structured output."""

from typing import List, Dict, Any
from app.memory.schemas import SessionSummary, SessionMemory, MessageRange
from app.llm.client import OllamaClient


class SessionSummarizer:
    """Summarizes conversation sessions into structured memory."""
    
    def __init__(self, llm_client: OllamaClient):
        """
        Initialize summarizer.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    async def summarize(
        self,
        messages: List[Dict[str, Any]],
        message_range: MessageRange
    ) -> SessionMemory:
        """
        Summarize a range of messages into structured memory.
        
        Args:
            messages: List of messages to summarize
            message_range: Range of messages being summarized
            
        Returns:
            SessionMemory with structured summary
        """
        # Extract messages in range
        messages_to_summarize = messages[message_range.from_index:message_range.to_index]
        
        # Build conversation text
        conversation_text = self._format_messages(messages_to_summarize)
        
        system_prompt = """You are a session memory extractor. Your task is to analyze a conversation and extract structured information.

Extract:
1. User profile: preferences and constraints mentioned
2. Key facts: important facts or information shared
3. Decisions: decisions made or agreed upon
4. Open questions: questions that were asked but not fully resolved
5. Todos: action items or tasks mentioned

Be concise. Use bullet points. Do not hallucinate - only include information explicitly mentioned or clearly implied."""
        
        user_prompt = f"""Analyze this conversation and extract structured information:

{conversation_text}

Output a structured summary with:
- user_profile: {{"prefs": [], "constraints": []}}
- key_facts: []
- decisions: []
- open_questions: []
- todos: []

Only include information that is clearly present in the conversation."""
        
        summary = await self.llm_client.generate_structured(
            prompt=user_prompt,
            schema=SessionSummary,
            system=system_prompt
        )
        
        return SessionMemory(
            session_summary=summary,
            message_range_summarized=message_range
        )
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages into readable text."""
        formatted = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")
        return "\n".join(formatted)
