"""Generates clarifying questions for unclear queries."""

from typing import List, Dict, Any
from app.llm.client import OllamaClient


class ClarifyingQuestionGenerator:
    """Generates clarifying questions when queries remain unclear."""
    
    def __init__(self, llm_client: OllamaClient):
        """
        Initialize clarifier.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    async def generate(
        self,
        query: str,
        rewritten_query: str = None,
        context: List[Dict[str, Any]] = None,
        max_questions: int = 3
    ) -> List[str]:
        """
        Generate clarifying questions if query remains unclear after rewrite.
        
        Args:
            query: Original query
            rewritten_query: Rewritten query (if available)
            context: Conversation context
            max_questions: Maximum number of questions to generate (1-3)
            
        Returns:
            List of clarifying questions
        """
        context_text = ""
        if context:
            recent_msgs = context[-5:]
            context_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent_msgs])
        
        system_prompt = """You are a helpful assistant that generates clarifying questions.

Generate 1-3 specific, actionable questions that would help clarify an ambiguous user query.
Questions should:
- Be specific and answerable
- Not be redundant
- Help narrow down the user's intent
- Be concise (one sentence each)"""
        
        user_prompt = f"""The user asked this query, which may still be unclear:

Original: {query}
{f'Rewritten: {rewritten_query}' if rewritten_query else ''}

{f'Context:\n{context_text}' if context_text else 'No context available.'}

Generate {max_questions} clarifying questions that would help understand what the user really wants. Output as a JSON array of strings."""
        
        try:
            response = await self.llm_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                json_mode=True,
                temperature=0.7
            )
            
            # Extract JSON array
            import json
            import re
            # Remove markdown if present
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response).strip()
            
            questions = json.loads(response)
            if isinstance(questions, list):
                # Limit to max_questions
                return questions[:max_questions]
            else:
                return []
        except Exception:
            # Fallback: generate simple questions
            return [
                "Could you provide more details about what you're looking for?",
                "What specific aspect would you like me to focus on?"
            ]
