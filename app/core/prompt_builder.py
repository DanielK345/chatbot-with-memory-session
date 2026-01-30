"""Builds final prompts for LLM with augmented context."""

from typing import List, Dict, Any, Optional


class PromptBuilder:
    """Constructs final prompts for LLM generation."""
    
    def build(
        self,
        query: str,
        augmented_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build system and user prompts.
        
        Args:
            query: User query (possibly rewritten)
            augmented_context: Augmented context from memory
            system_prompt: Custom system prompt (optional)
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        default_system = "You are a helpful, knowledgeable assistant. Provide clear, accurate responses."
        system = system_prompt or default_system
        
        user_parts = []
        
        if augmented_context:
            user_parts.append(augmented_context)
            user_parts.append("")  # Blank line separator
        
        user_parts.append(f"User query: {query}")
        
        user_prompt = "\n".join(user_parts)
        
        return system, user_prompt
