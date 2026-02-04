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
        
        # Precompute recent context text and candidate entities used by multiple rules
        context_text = ' '.join([m.get('content', '') for m in (context or [])[-3:]]).lower()
        stopwords = set(['the', 'and', 'for', 'with', 'from', 'that', 'this', 'these', 'those', 'your', 'you', 'we', 'i', 'it', 'they', 'he', 'she', 'their', 'are', 'is', 'was', 'were', 'a', 'an', 'in', 'on', 'at', 'by', 'to', 'of', 'as', 'be'])
        ctx_tokens = [w for w in re.findall(r"\w+", context_text)]
        candidate_entities = [t for t in ctx_tokens if len(t) > 3 and t not in stopwords]
        unique_candidates = set(candidate_entities)

        # RULE 1: Check for unclear reference (pronouns)
        pronouns = ['it', 'they', 'this', 'that', 'he', 'she', 'them', 'these', 'those']
        has_pronoun = any(re.search(rf"\b{p}\b", query_lower) for p in pronouns)

        if has_pronoun:
            # If there is no context or no clear antecedent, mark pronoun as ambiguous
            if not context or len(unique_candidates) == 0:
                ambiguity_signals.append("Unclear reference (pronoun without prior context or no clear antecedent)")
            elif len(unique_candidates) == 1:
                # Single likely antecedent -> pronoun probably resolvable, do not add a signal
                pass
            else:
                ambiguity_signals.append("Unclear reference (pronoun with multiple possible entities)")

        # RULE 1b: Anaphoric determiners (e.g., "the same principles") that refer back to prior concepts
        anaphors = ['same', 'similar', 'such', 'previous', 'aforementioned']
        if any(re.search(rf"\b{a}\b", query_lower) for a in anaphors):
            # detect pattern like "same <noun>" or "the same <noun>"
            match = re.search(r"\b(?:the\s+)?(?:" + '|'.join(anaphors) + r")\b\s+(\w+)", query_lower)
            if match:
                noun = match.group(1)
                if noun not in context_text:
                    ambiguity_signals.append(f"Unclear reference (anaphoric '{match.group(0)}' without antecedent)")

        # RULE 1c: 'Which one(s)' / selection questions without antecedent or without criteria
        which_one_pattern = re.search(r"\bwhich\b(?:[^\n\w]{0,6}\s+\w+){0,5}?\b(one|ones)\b", query_lower) or re.search(r"\bwhich one\b|\bwhich ones\b", query_lower)
        if which_one_pattern:
            # If there are no clear candidate entities in context, this is ambiguous
            if not context or len(unique_candidates) == 0:
                ambiguity_signals.append("Unclear reference ('which one' without antecedent)")
            else:
                # Even with candidates, a bare 'which one' without selection criteria is underspecified
                ambiguity_signals.append("Choice underspecified ('which one' without selection criteria)")
        
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

        # RULE 2b: WH 'what/which' + choose/pick/select but missing object (e.g., "What should I choose?")
        choose_pattern = re.search(r"^\s*(what|which)\b.*\b(choose|pick|select)\b(\s+(\w+))?\s*\?*$", query_lower)
        if choose_pattern:
            # If no object noun follows choose/pick/select, flag as ambiguous
            if choose_pattern.group(4) is None:
                ambiguity_signals.append("Unclear question (missing object for 'choose/pick/select')")
        
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
