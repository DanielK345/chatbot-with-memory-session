"""Query rewriting for ambiguous queries."""

from typing import List, Dict, Any
from app.llm.client import OllamaClient


class QueryRewriter:
    """Rewrites ambiguous queries to be clearer."""
    
    def __init__(self, llm_client: OllamaClient):
        """
        Initialize query rewriter.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    async def rewrite(
        self,
        query: str,
        context: List[Dict[str, Any]] = None,
        ambiguity_reason: str = None
    ) -> str:
        """
        Rewrite an ambiguous query to be clearer.
        
        Args:
            query: Original ambiguous query
            context: Recent conversation context
            ambiguity_reason: Reason why query is ambiguous
            
        Returns:
            Rewritten, clearer query
        """
        context_text = ""
        if context:
            recent_msgs = context[-5:]  # Last 5 messages
            context_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent_msgs])
        
        system_prompt = """You are a query clarification assistant. Rewrite ambiguous queries to be clear and specific.

Your rewritten query should:
- Be specific and unambiguous
- Include necessary context from the conversation
- Maintain the user's original intent
- Be a complete, standalone question or request"""
        
        user_prompt = f"""Rewrite this ambiguous query to be clearer:

Original query: {query}

{f'Reason for ambiguity: {ambiguity_reason}' if ambiguity_reason else ''}

{f'Recent conversation context:\n{context_text}' if context_text else 'No recent context.'}

Provide a clear, rewritten version of the query that removes ambiguity while preserving the user's intent."""
        
        rewritten = await self.llm_client.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.5
        )
        
        return rewritten.strip()
