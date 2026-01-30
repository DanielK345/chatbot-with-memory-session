"""JSON extraction and validation utilities."""

import json
import re
from typing import Optional


class JSONGuard:
    """Utilities for extracting and validating JSON from LLM responses."""
    
    def extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks.
        
        Args:
            text: Text that may contain JSON
            
        Returns:
            Extracted JSON string
        """
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Try to find JSON object boundaries
        # Look for first { and last }
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_text = text[start:end+1]
            # Validate it's parseable
            try:
                json.loads(json_text)
                return json_text
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, try parsing the whole text
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            raise ValueError(f"Could not extract valid JSON from text: {text[:200]}")
    
    def validate_json(self, text: str) -> bool:
        """Check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False
