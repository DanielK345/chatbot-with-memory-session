"""Ambiguity detection for user queries - RULE-FIRST approach per fix.txt."""

import re
from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.query_understanding.schemas import AmbiguityAnalysis
from app.llm.client import LLMClient


class AmbiguityDetector:
    """
    Detects ambiguous queries using RULE-FIRST approach.
    
    Ambiguity types:
    1. Unclear reference (pronouns: it, they, this, that, he, she)
    2. Unclear question (< 4 tokens OR no verb OR no WH-word)
    3. Unclear intent (not a question or imperative)
    4. Other / undecided
    
    LLM is ONLY used if:
    - Multiple ambiguity types detected
    - Rule signals conflict
    - Long query (> 20 tokens) with unclear structure
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize ambiguity detector.
        
        Args:
            llm_client: LLM client instance
        """
        self.llm_client = llm_client
    
    def _heuristic_check(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Heuristic checks for ambiguity - RULE-BASED ONLY (no LLM).
        
        Returns:
            Dict with 'is_ambiguous', 'reason', and 'needs_llm' keys
        """
        tokens = query.strip().split()
        query_lower = query.lower()
        num_tokens = len(tokens)
        
        ambiguity_signals = []
        
        # RULE 1: Check for unclear reference (pronouns)
        pronouns = ['it', 'they', 'this', 'that', 'he', 'she', 'them', 'these', 'those']
        has_pronoun = any(f' {p} ' in f' {query_lower} ' or query_lower.startswith(p + ' ') or query_lower.endswith(f' {p}') for p in pronouns)
        
        if has_pronoun:
            # Pronoun is ambiguous only if we have multiple candidate entities in context
            if context and len(context) >= 2:
                # Count entities in recent context (very simple heuristic)
                context_text = ' '.join([m.get('content', '') for m in context[-2:]])
                entity_count = len(set(word for word in context_text.lower().split() if len(word) > 3))
                if entity_count > 1:
                    ambiguity_signals.append("Unclear reference (pronoun with multiple possible entities)")
            elif not context:
                # No context to resolve pronouns
                ambiguity_signals.append("Unclear reference (pronoun without prior context)")
        
        # RULE 2: Check for unclear question (< 4 tokens or no verb or no WH-word)
        wh_words = ['what', 'which', 'who', 'when', 'where', 'why', 'how']
        has_wh = any(token.lower() in wh_words for token in tokens)
        
        # Simple verb detection (very basic - just check for common verbs)
        common_verbs = ['is', 'are', 'was', 'were', 'can', 'could', 'would', 'should', 'do', 'does', 'did', 'have', 'has', 'will', 'shall', 'may', 'might', 'must', 'be', 'been', 'being']
        has_verb = any(token.lower() in common_verbs for token in tokens)
        
        if num_tokens < 4:
            # Very short - likely ambiguous unless it's a clear question
            if not has_wh and not has_verb:
                ambiguity_signals.append("Unclear question (< 4 tokens, no verb, no WH-word)")
        
        if has_wh and not has_verb and num_tokens < 5:
            ambiguity_signals.append("Incomplete question (WH-word but no complete structure)")
        
        # RULE 3: Check for unclear intent (not question or imperative)
        is_question = query.rstrip().endswith('?') or has_wh
        is_imperative = tokens[0].lower() in ['show', 'tell', 'give', 'explain', 'find', 'search', 'list', 'get', 'help', 'fix', 'improve', 'build', 'create']
        is_declarative = not is_question and not is_imperative
        
        if is_declarative and num_tokens > 5:
            # Long declarative statement without clear intent might be ambiguous
            if '?' not in query and '!' not in query:
                ambiguity_signals.append("Unclear intent (declarative statement without clear question or command)")
        
        is_ambiguous = len(ambiguity_signals) > 0
        
        return {
            "is_ambiguous": is_ambiguous,
            "signals": ambiguity_signals,
            "needs_llm": len(ambiguity_signals) > 1 or (len(ambiguity_signals) == 1 and num_tokens > 20)
        }
    
    async def detect(self, query: str, context: List[Dict[str, Any]] = None) -> AmbiguityAnalysis:
        """
        Detect if a query is ambiguous using RULE-FIRST, LLM-FALLBACK approach.
        
        Args:
            query: User query
            context: Recent conversation context (optional)
            
        Returns:
            AmbiguityAnalysis with is_ambiguous and reason
        """
        # Step 1: Run heuristic check (rule-based, no LLM)
        heuristic_result = self._heuristic_check(query, context)
        
        # If heuristic says clear AND no conflicting signals, return immediately (no LLM)
        if not heuristic_result["is_ambiguous"]:
            return AmbiguityAnalysis(
                is_ambiguous=False,
                ambiguity_reason=None,
                confidence=0.95  # High confidence in heuristic for clear queries
            )
        
        # Step 2: Decide if we need LLM
        needs_llm = heuristic_result["needs_llm"]
        
        if not needs_llm:
            # Single clear signal - return without LLM
            return AmbiguityAnalysis(
                is_ambiguous=True,
                ambiguity_reason=heuristic_result["signals"][0],
                confidence=0.85  # Slightly lower confidence for single signal
            )
        
        # Step 3: LLM FALLBACK - use only if multiple signals or conflicting rules
        context_text = ""
        if context:
            recent_msgs = context[-3:]  # Last 3 messages
            context_text = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in recent_msgs])
        
        system_prompt = """You are a query ambiguity detector. Analyze if a user query is ambiguous.

A query is ambiguous if:
1. Unclear reference (uses pronouns like it, they, this, that without clear context)
2. Unclear question (too short, lacks verb/structure, or unclear intent)
3. Unclear intent (not a question or command, vague declarative statement)

Respond with JSON: {"is_ambiguous": true/false, "reason": "brief reason if ambiguous"}"""
        
        user_prompt = f"""Analyze if this query is ambiguous:

Query: {query}

Recent context:
{context_text if context_text else "(No prior context)"}

Respond only with valid JSON."""
        
        try:
            response = await self.llm_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                json_mode=True,
                temperature=0.2,  # Low temperature for consistent analysis
                max_tokens=100
            )
            
            import json
            # Extract JSON if wrapped in markdown
            json_str = response
            if '```' in response:
                json_str = response.split('```')[1].replace('json', '', 1).strip()
            
            result = json.loads(json_str)
            
            return AmbiguityAnalysis(
                is_ambiguous=result.get("is_ambiguous", False),
                ambiguity_reason=result.get("reason"),
                confidence=0.80  # Confidence in LLM result
            )
        except Exception as e:
            # LLM failed - fall back to heuristic result
            return AmbiguityAnalysis(
                is_ambiguous=heuristic_result["is_ambiguous"],
                ambiguity_reason=heuristic_result["signals"][0] if heuristic_result["signals"] else None,
                confidence=0.70  # Lower confidence due to LLM failure
            )
        
if __name__ == "__main__":
    import asyncio
    from app.llm.client import LLMClient

    async def main():
        llm_client = LLMClient(primary="gemini")
        detector = AmbiguityDetector(llm_client)

        test_queries = [
            "What is the capital of Vietnam?",
            "Tell me about it.",
            "Explain quantum computing.",
            "Is it important?",
            "Fix the code.",
            "Is it going to rain tomorrow?",
            "This is confusing.",
            "How does it work?",
            "List the top 10 movies.",
            "It was great!"
        ]

        for query in test_queries:
            analysis = await detector.detect(query)
            print(f"Query: {query}")
            print(f"  Ambiguous: {analysis.is_ambiguous}")
            if analysis.is_ambiguous:
                print(f"  Reason: {analysis.ambiguity_reason}")
            print(f"  Confidence: {analysis.confidence}\n")

    asyncio.run(main())
