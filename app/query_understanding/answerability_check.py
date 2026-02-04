"""Answerability check - rule-based with similarity matching (NO LLM per fix.txt)."""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.memory.schemas import SessionMemory


class AnswerabilityChecker:
    """
    Checks if a query is answerable using similarity-based methods.
    
    A query is answerable if:
    1. Intent is clear
    2. References are resolved
    3. Similar to previously answerable queries
    
    Uses lightweight embeddings (no LLM needed).
    """
    
    def __init__(self):
        """Initialize answerability checker."""
        self.embeddings_cache = {}
        # Try to import a lightweight embedding model
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.has_embeddings = True
        except ImportError:
            # Fallback: simple keyword matching if embeddings not available
            self.embedding_model = None
            self.has_embeddings = False
    
    def _simple_similarity(self, query1: str, query2: str) -> float:
        """
        Simple keyword-based similarity (when embeddings unavailable).
        
        Returns:
            Similarity score 0.0-1.0
        """
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text (with caching)."""
        if not self.has_embeddings:
            return None
        
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            embedding = self.embedding_model.encode(text).tolist()
            self.embeddings_cache[text] = embedding
            return embedding
        except Exception:
            return None
    
    def _cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        import math
        
        if not emb1 or not emb2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = math.sqrt(sum(a * a for a in emb1))
        norm2 = math.sqrt(sum(b * b for b in emb2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def check(
        self,
        query: str,
        is_ambiguous: bool,
        previous_queries: List[str] = None,
        session_memory: Optional[SessionMemory] = None
    ) -> Dict[str, Any]:
        """
        Check if a query is answerable.
        
        Args:
            query: User query
            is_ambiguous: Whether query was flagged as ambiguous
            previous_queries: List of previously answered queries
            session_memory: Session memory summary
            
        Returns:
            {
                "is_answerable": bool,
                "reason": str,
                "confidence": float (0.0-1.0),
                "similar_previous_queries": List[str]
            }
        """
        reasons = []
        is_answerable = True
        confidence = 0.9
        similar_queries = []
        
        # RULE 1: Unresolved ambiguity means not answerable
        if is_ambiguous:
            is_answerable = False
            reasons.append("Query is ambiguous - cannot answer without clarification")
            confidence = 0.0
            return {
                "is_answerable": is_answerable,
                "reason": reasons[0],
                "confidence": confidence,
                "similar_previous_queries": similar_queries
            }
        
        # RULE 2: Check if similar to previous answerable queries
        if previous_queries:
            query_embedding = self._get_embedding(query) if self.has_embeddings else None
            similarities = []
            
            for prev_query in previous_queries:
                if self.has_embeddings and query_embedding:
                    prev_embedding = self._get_embedding(prev_query)
                    if prev_embedding:
                        sim = self._cosine_similarity(query_embedding, prev_embedding)
                        similarities.append((prev_query, sim))
                else:
                    # Fallback to simple keyword similarity
                    sim = self._simple_similarity(query, prev_query)
                    similarities.append((prev_query, sim))
            
            # Get top similar queries with score > 0.75
            similarities.sort(key=lambda x: x[1], reverse=True)
            similar_queries = [q for q, sim in similarities if sim > 0.75]
            
            if similar_queries:
                confidence = min(0.95, 0.7 + len(similar_queries) * 0.1)
            else:
                # Even if not similar to previous, might still be answerable
                if similarities and similarities[0][1] > 0.5:
                    confidence = 0.75
                    reasons.append("Query somewhat similar to previous questions")
        
        # RULE 3: Check session memory for related facts
        if session_memory and session_memory.session_summary:
            summary = session_memory.session_summary
            
            # Check if key facts or decisions are relevant
            query_lower = query.lower()
            fact_keywords = []
            
            for fact in summary.key_facts:
                fact_lower = fact.lower()
                if any(word in query_lower for word in fact_lower.split()):
                    fact_keywords.append(fact)
            
            if fact_keywords:
                confidence = min(1.0, confidence + 0.1)
                reasons.append(f"Found {len(fact_keywords)} related session facts")
        
        # Final determination
        result_reason = (
            "; ".join(reasons) 
            if reasons 
            else "Query appears answerable based on clarity and context"
        )
        
        return {
            "is_answerable": is_answerable,
            "reason": result_reason,
            "confidence": confidence,
            "similar_previous_queries": similar_queries
        }
    
if __name__ == "__main__":
    # Simple test
    checker = AnswerabilityChecker()
    test_query = "How do I implement a chatbot using FastAPI?"
    previous = [
        "How to build a chatbot?",
        "What is FastAPI?",
        "Steps to create a web application with FastAPI"
    ]
    result = checker.check(test_query, is_ambiguous=False, previous_queries=previous)
    print(result)
