"""Query refinement using lightweight entity extraction + LLM rewriting."""

from pathlib import Path
import re
import sys
from typing import List, Dict, Any, Optional
from collections import deque
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.memory.schemas import SessionMemory
from app.llm.client import LLMClient


class QueryRefiner:
    """
    Refines pronouns in queries using a hybrid lightweight approach:
    
    1. Detect pronouns (it, they, them, this, that, he, she)
    2. Extract named entities from last 3 queries (cache)
    3. Use LLM to rewrite: "Replace pronouns [pronouns] with entities from [entity_list]"
    
    Only refines when pronouns are detected. Uses minimal LLM prompting.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize query refiner with optional LLM client."""
        self.llm_client = llm_client
        self.query_cache: deque = deque(maxlen=3)  # Store last 3 queries only
        self.pronoun_patterns = {
            'it': r'\bit\b',
            'they': r'\bthey\b',
            'them': r'\bthem\b',
            'this': r'\bthis\b',
            'that': r'\bthat\b',
            'he': r'\bhe\b',
            'she': r'\bshe\b',
        }
    
    def _detect_pronouns(self, query: str) -> List[str]:
        """
        Detect pronouns in query.
        Returns list of pronouns found (it, they, them, this, that, he, she).
        """
        detected = []
        query_lower = query.lower()
        for pronoun, pattern in self.pronoun_patterns.items():
            if re.search(pattern, query_lower):
                detected.append(pronoun)
        return detected
    
    def _extract_entities_from_cache(self) -> List[str]:
        """
        Extract named entities from cached queries (last 3 queries).
        Uses simple capitalized word extraction (no model needed).
        
        Returns:
            List of unique capitalized entities found in recent queries
        """
        entities = []
        bad_words = {'I', 'The', 'This', 'That', 'What', 'Which', 'How', 'Are', 'Is', 'So', 'We', 'You', 'They', 'Can', 'Should', 'Would', 'Could', 'Do', 'Did', 'Have', 'Has', 'Will', 'A', 'Or'}
        
        # Extract from cache (last 3 queries)
        for query_text in self.query_cache:
            # Find capitalized words (proper nouns)
            words = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', query_text)
            for word in words:
                if len(word) >= 3 and word not in bad_words and word not in entities:
                    entities.append(word)
        
        return entities[:10]  # Return top 10 unique entities
    
    def _add_to_cache(self, query: str) -> None:
        """Add query to cache (automatically keeps only last 3)."""
        self.query_cache.append(query)
    
    async def _rewrite_with_llm(
        self,
        query: str,
        pronouns: List[str],
        entities: List[str]
    ) -> Optional[str]:
        """
        Use lightweight LLM to rewrite query, replacing pronouns with entities.
        Uses minimal prompting - just ask for pronoun replacement.
        
        Lightweight Model: Qwen2.5-1.5B (vs llama3.1 8B)
        - Much faster inference (~2-3x speedup)
        - Sufficient for simple pronoun replacement task
        - Falls back to active LLM if unavailable
        
        Args:
            query: Original query with pronouns
            pronouns: List of pronouns detected (it, they, them, etc)
            entities: List of named entities to use as replacements
            
        Returns:
            Refined query or None if LLM fails
        """
        if not self.llm_client or not entities:
            return None
        
        # Build minimal prompt
        entity_str = ', '.join(entities[:5])  # Use top 5 entities
        pronouns_str = ', '.join(pronouns)
        
        prompt = (
            f"Rewrite this query by replacing the pronouns [{pronouns_str}] "
            f"with one of these entities [{entity_str}]:\n\n"
            f"Query: {query}\n\n"
            f"Rewritten query (keep it concise):"
        )
        
        try:
            # Use lightweight model for fast inference
            response = await self.llm_client.generate_lightweight(
                prompt=prompt,
                max_tokens=20,  # Very short response
                temperature=0.3  # Low temperature for deterministic output
            )
            
            # Extract just the rewritten query (remove "Query: " prefix if present)
            refined = response.strip().strip('Query: ').strip('"').strip("'")
            return refined if refined and refined != query else None
        except Exception:
            return None
    

    
    async def refine(
        self,
        query: str,
        session_memory: Optional[SessionMemory] = None,
        context: Optional[List[Dict[str, Any]]] = None,
        use_llm: bool = True
    ) -> Optional[str]:
        """
        Refine query by replacing pronouns with entities from cache.
        
        Process:
        1. Detect pronouns (it, they, them, this, that, he, she)
        2. Extract entities from last 3 cached queries (lightweight)
        3. Use LLM to rewrite with minimal prompting
        
        Args:
            query: Original query
            session_memory: Session memory (not used in this approach)
            context: Conversation context (not used in this approach)
            use_llm: Whether to use LLM for rewriting (default True)
            
        Returns:
            Refined query if pronouns were found and LLM succeeded, None otherwise
        """
        # Add current query to cache
        self._add_to_cache(query)
        
        # Step 1: Detect pronouns
        pronouns = self._detect_pronouns(query)
        if not pronouns:
            return None  # No pronouns, no refinement needed
        
        # Step 2: Extract entities from cache (last 3 queries)
        entities = self._extract_entities_from_cache()
        if not entities:
            return None  # No entities found, can't refine
        
        # Step 3: Use LLM to rewrite
        if use_llm and self.llm_client:
            refined = await self._rewrite_with_llm(query, pronouns, entities)
            return refined
        
        return None


if __name__ == "__main__":
    # Example usage with lightweight Qwen model for fast query refinement
    import asyncio
    from app.llm.client import LLMClient
    
    async def main():
        # Initialize with lightweight Qwen2.5-1.5B model (default for query refinement)
        llm_client = LLMClient(
            primary="ollama",
            ollama_model="llama3.1",
            lightweight_ollama_model="qwen2.5:1.5b"  # Lightweight model for refinement
        )
        refiner = QueryRefiner(llm_client=llm_client)
        
        print("=" * 70)
        print("Query Refinement Example (Using Qwen2.5-1.5B Lightweight Model)")
        print("=" * 70)
        
        # Simulate conversation
        test_queries = [
            "We're building a machine learning system.",
            "Should we use TensorFlow or PyTorch?",
            "How does it perform?",  # Should be refined with TensorFlow/PyTorch
        ]
        
        for i, query in enumerate(test_queries, 1):
            # Process query (adds to cache, detects pronouns, extracts entities, refines)
            refined = await refiner.refine(query)
            
            print(f"\n[{i}] Original: {query}")
            if refined:
                print(f"    Refined:  {refined} ✓")
            else:
                print(f"    No refinement needed (no pronouns or insufficient context)")
        
        print("\n" + "=" * 70)
        print("Example complete. Check logs for lightweight model usage.")
        print("=" * 70)
    
    # Run async example
    asyncio.run(main())

