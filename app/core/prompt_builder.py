"""Builds final prompts for LLM with augmented context."""

from typing import List, Dict, Any, Optional


class PromptBuilder:
    """Constructs final prompts for LLM generation with universal compatibility."""
    
    def build(
        self,
        query: str,
        augmented_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_name: str = "generic"
    ) -> tuple[str, str]:
        """
        Build system and user prompts compatible across all LLM providers.
        
        Args:
            query: User query (possibly rewritten)
            augmented_context: Augmented context from memory
            system_prompt: Custom system prompt (optional)
            model_name: Model identifier ("gemini", "ollama", "claude", "generic")
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Universal system prompt compatible across all models
        default_system = """You are a knowledgeable and helpful assistant.
Characteristics:
- Provide accurate, thoughtful responses
- Be clear and well-organized
- Use examples when helpful
- Acknowledge limitations if you're unsure
- Maintain a respectful, professional tone
- Format responses for readability (use lists, sections when appropriate)"""
        
        system = system_prompt or default_system
        
        # Build user prompt with context if available
        user_parts = []
        
        if augmented_context:
            user_parts.append("CONTEXT:")
            user_parts.append(augmented_context)
            user_parts.append("")  # Blank line separator
        
        user_parts.append("QUESTION:")
        user_parts.append(query)
        
        user_prompt = "\n".join(user_parts)
        
        return system, user_prompt
    
    def build_with_instructions(
        self,
        query: str,
        augmented_context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        instructions: Optional[List[str]] = None
    ) -> tuple[str, str]:
        """
        Build prompts with explicit instructions section (more explicit for varied models).
        
        Args:
            query: User query
            augmented_context: Augmented context from memory
            system_prompt: Custom system prompt
            instructions: List of specific instructions to follow
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        default_system = """You are a helpful, accurate, and professional assistant."""
        system = system_prompt or default_system
        
        user_parts = []
        
        if instructions:
            user_parts.append("INSTRUCTIONS:")
            for i, instruction in enumerate(instructions, 1):
                user_parts.append(f"{i}. {instruction}")
            user_parts.append("")
        
        if augmented_context:
            user_parts.append("CONTEXT:")
            user_parts.append(augmented_context)
            user_parts.append("")
        
        user_parts.append("QUESTION:")
        user_parts.append(query)
        
        user_prompt = "\n".join(user_parts)
        
        return system, user_prompt
    
    def build_for_structured_output(
        self,
        query: str,
        output_format: str,
        augmented_context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build prompts for structured output (JSON, key-value pairs, etc.).
        
        Args:
            query: User query
            output_format: Description of desired output format (e.g., "JSON object", "bullet points", "CSV")
            augmented_context: Augmented context from memory
            system_prompt: Custom system prompt
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        default_system = """You are a precise assistant that formats responses exactly as requested.
Always follow the specified output format exactly."""
        
        system = system_prompt or default_system
        
        user_parts = []
        
        if augmented_context:
            user_parts.append("CONTEXT:")
            user_parts.append(augmented_context)
            user_parts.append("")
        
        user_parts.append("QUESTION:")
        user_parts.append(query)
        user_parts.append("")
        user_parts.append(f"OUTPUT FORMAT:")
        user_parts.append(output_format)
        
        user_prompt = "\n".join(user_parts)
        
        return system, user_prompt

