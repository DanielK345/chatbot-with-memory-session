"""Token counting utilities for context size monitoring."""

import tiktoken
from typing import List, Dict, Any


class TokenCounter:
    """Counts tokens in messages using tiktoken."""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize token counter.
        
        Args:
            model: Model name for tokenizer (default: gpt-3.5-turbo)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.encoding.encode(text))
    
    def count_messages(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count total tokens in a list of messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Count role + content + formatting overhead (~4 tokens per message)
            role_text = msg.get("role", "")
            content_text = msg.get("content", "")
            total += self.count_tokens(role_text) + self.count_tokens(content_text) + 4
        return total
    
    def estimate_tokens(self, text: str) -> int:
        """
        Heuristic estimation (characters / 4) as fallback.
        More conservative than actual token count.
        """
        return len(text) // 4
