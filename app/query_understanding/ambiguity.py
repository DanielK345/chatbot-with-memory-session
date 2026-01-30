"""Ambiguity detection for user queries."""

import re
from typing import Dict, Any
from app.query_understanding.schemas import AmbiguityAnalysis
from app.llm.ollama_client import OllamaClient


class AmbiguityDetector:
    """Detects ambiguous queries using heuristics and LLM."""
    
    def __init__(self, llm_client: OllamaClient):
        """
        Initialize ambiguity detector.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def _heuristic_check(self, query: str) -> Dict[str, Any]:
        """
        Heuristic checks for ambiguity signals.
        
        Returns:
            Dict with 'is_ambiguous' and 'signals' keys
        """
        signals = []
        is_ambiguous = False
        
        # Short query
        if len(query.split()) < 3:
            signals.append("Very short query (< 3 words)")
            is_ambiguous = True
        
        # Pronouns without clear referents
        pronouns = ['it', 'this', 'that', 'they', 'them', 'those', 'these']
        words = query.lower().split()
        has_pronoun = any(word in pronouns for word in words)
        if has_pronoun and len(query.split()) < 5:
            signals.append("Contains pronouns with unclear referents")
            is_ambiguous = True
        
        # Missing object/action (very simple patterns)
        if query.lower().startswith(('what', 'which', 'how')) and len(query.split()) < 4:
            signals.append("Incomplete question")
            is_ambiguous = True
        
        return {
            "is_ambiguous": is_ambiguous,
            "signals": signals
        }
    
    async def detect(self, query: str, context: List[Dict[str, Any]] = None) -> AmbiguityAnalysis:
        """
        Detect if a query is ambiguous.
        
        Args:
            query: User query
            context: Recent conversation context (optional)
            
        Returns:
            AmbiguityAnalysis
        """
        # Heuristic check first
        heuristic_result = self._heuristic_check(query)
        
        # LLM-based classification
        context_text = ""
        if context:
            recent_msgs = context[-3:]  # Last 3 messages
            context_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent_msgs])
        
        system_prompt = """You are a query ambiguity detector. Analyze if a user query is ambiguous or unclear.

A query is ambiguous if:
- It lacks necessary context or referents
- It could be interpreted in multiple ways
- It's too vague to answer without clarification
- It references something not in the conversation context

Respond with JSON: {"is_ambiguous": true/false, "ambiguity_reason": "explanation"}"""
        
        user_prompt = f"""Is this query ambiguous or unclear?

Query: {query}

{f'Recent context:\n{context_text}' if context_text else 'No recent context.'}

Analyze if the query is ambiguous and provide a reason if it is."""
        
        try:
            llm_result = await self.llm_client.generate_structured(
                prompt=user_prompt,
                schema=AmbiguityAnalysis,
                system=system_prompt
            )
            
            # Combine heuristic and LLM results
            # If either says ambiguous, consider it ambiguous
            is_ambiguous = heuristic_result["is_ambiguous"] or llm_result.is_ambiguous
            
            reason = llm_result.ambiguity_reason
            if heuristic_result["signals"]:
                heuristic_reasons = "; ".join(heuristic_result["signals"])
                if reason:
                    reason = f"{reason}; {heuristic_reasons}"
                else:
                    reason = heuristic_reasons
            
            return AmbiguityAnalysis(
                is_ambiguous=is_ambiguous,
                ambiguity_reason=reason,
                confidence=0.8 if is_ambiguous else 0.2
            )
        except Exception as e:
            # Fallback to heuristic if LLM fails
            return AmbiguityAnalysis(
                is_ambiguous=heuristic_result["is_ambiguous"],
                ambiguity_reason="; ".join(heuristic_result["signals"]) if heuristic_result["signals"] else None,
                confidence=0.5
            )
