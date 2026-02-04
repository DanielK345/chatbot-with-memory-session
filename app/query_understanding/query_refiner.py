"""Query refinement using rule-based entity replacement (fix.txt section 5)."""

from pathlib import Path
import re
import sys
from typing import List, Dict, Any, Optional
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.memory.schemas import SessionMemory


class QueryRefiner:
    """
    Refines queries using rule-based entity replacement and template filling.
    
    Example:
    "Why is it faster?" → "Why is Llama 3.1 faster than Qwen for local inference?"
    
    Uses LLM ONLY if complex paraphrasing required.
    """
    
    def __init__(self):
        """Initialize query refiner."""
        pass
    
    def _extract_entities_from_context(
        self,
        context: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Extract entities from conversation context.
        
        Returns:
            Dict mapping entity types to identified values
        """
        entities = {
            "models": [],
            "tools": [],
            "concepts": [],
            "subjects": []
        }
        
        # Simple pattern matching for common entities
        if context:
            context_text = " ".join([m.get('content', '') for m in context[-5:]])
            context_lower = context_text.lower()
            
            # Model names
            model_names = ['llama', 'qwen', 'mistral', 'gemini', 'gpt', 'claude', 'phi']
            entities["models"] = [m for m in model_names if m in context_lower]
            
            # Tool names
            tools = ['fastapi', 'ollama', 'redis', 'streamlit', 'gradio', 'pytorch', 'tensorflow']
            entities["tools"] = [t for t in tools if t in context_lower]
            
        return entities
    
    def _resolve_pronouns(
        self,
        query: str,
        session_memory: Optional[SessionMemory] = None,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Resolve pronouns like 'it', 'that', 'they' using context.
        
        Example:
        Query: "Why is it faster?"
        Context mentions: "Llama 3.1"
        Result: "Why is Llama 3.1 faster?"
        """
        refined = query
        
        # Simple pronoun resolution (replace 'it' with most recent entity)
        pronouns_to_resolve = ['it', 'it\'s', 'it is', 'that', 'this', 'they', 'them']
        
        # Extract recent entities from context
        if context and len(context) >= 2:
            # Get last user message before current query
            recent_entities = []
            for msg in context[-5:]:  # Last 5 messages (includes most recent)
                if msg.get('role') == 'assistant':
                    # Extract capitalized words (likely entity names)
                    words = msg.get('content', '').split()
                    caps_words = [w for w in words if w and w[0].isupper() and len(w) > 2]
                    recent_entities.extend(caps_words[:3])  # Top 3
            
            if recent_entities:
                main_entity = recent_entities[0]
                # Replace 'it' at start of sentence
                refined = re.sub(r'^[Ii]t\s+', f"{main_entity} ", refined)
                # Replace 'it' in middle
                refined = re.sub(r'\s+[Ii]t\s+', f" {main_entity} ", refined)
        
        return refined
    
    def _apply_template_filling(
        self,
        query: str,
        session_memory: Optional[SessionMemory] = None
    ) -> str:
        """
        Fill in template patterns based on session memory.
        
        Example:
        Query: "How do I implement [task] with [tool]?"
        Memory has: user building chatbot with FastAPI
        Result: "How do I implement chatbot with FastAPI?"
        """
        refined = query
        
        if not session_memory:
            return refined
        
        summary = session_memory.session_summary
        
        # Extract key terms from memory
        key_facts = summary.key_facts or []
        decisions = summary.decisions or []
        prefs = summary.user_profile.prefs or []
        
        # Build a dictionary of common replacements
        replacements = {}
        
        if key_facts:
            # Example: "User is building a chatbot" → replace [project] with "chatbot"
            for fact in key_facts:
                if 'building' in fact.lower() or 'creating' in fact.lower():
                    # Extract project name
                    words = fact.split()
                    if len(words) > 2:
                        project = words[-1].rstrip('.,')
                        replacements['[project]'] = project
                        replacements['[task]'] = project
        
        if decisions:
            for decision in decisions:
                # Extract tool/tech from decisions
                if 'use' in decision.lower() or 'using' in decision.lower():
                    words = decision.split()
                    for i, word in enumerate(words):
                        if word.lower() in ['use', 'using'] and i + 1 < len(words):
                            tool = words[i + 1].rstrip('.,')
                            replacements['[tool]'] = tool
                            replacements['[backend]'] = tool
        
        # Apply replacements
        for placeholder, value in replacements.items():
            refined = refined.replace(placeholder, value)
        
        return refined
    
    def refine(
        self,
        query: str,
        session_memory: Optional[SessionMemory] = None,
        context: Optional[List[Dict[str, Any]]] = None,
        use_llm_for_complex: bool = False
    ) -> str:
        """
        Refine query using rule-based entity replacement and template filling.
        
        Args:
            query: Original query
            session_memory: Session memory for context
            context: Conversation context
            use_llm_for_complex: Use LLM if simple rules fail (not yet implemented)
            
        Returns:
            Refined query string
        """
        refined = query
        
        # Step 1: Resolve pronouns
        refined = self._resolve_pronouns(refined, session_memory, context)
        
        # Step 2: Apply template filling
        refined = self._apply_template_filling(refined, session_memory)
        
        # Step 3: Clean up
        refined = re.sub(r'\s+', ' ', refined).strip()
        
        return refined
    
if __name__ == "__main__":
    # Example usage
    refiner = QueryRefiner()
    sample_query = "Why is it beautiful?"
    sample_context = [
        {"role": "user", "content": "Can you tell me about Paris?"},
        {"role": "assistant", "content": "Paris is the capital of France. It is a beautiful city"},
    ]
    refined_query = refiner.refine(sample_query, context=sample_context)
    print(f"Original Query: {sample_query}")
    print(f"Refined Query: {refined_query}")
