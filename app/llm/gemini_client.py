"""Gemini LLM client wrapper."""

import json
import os
from typing import Optional, Any

try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False
    genai = None

from app.llm.json_guard import JSONGuard
from app.core.config import GOOGLE_API_KEY


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-flash-latest"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model: Model name (e.g., "gemini-pro", "gemini-1.5-pro")
        """
        if not GEMINI_SDK_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed.\n"
                "Install with: pip install google-generativeai"
            )
        self.api_key = api_key or GOOGLE_API_KEY
        self.model_name = model
        self.json_guard = JSONGuard()
        self._client = None
        self._configured = False
    
    def _ensure_configured(self):
        """Ensure Gemini is configured and test connection."""
        if self._configured:
            return
        
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Please set GOOGLE_API_KEY environment variable.\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        
        try:
            genai.configure(api_key=self.api_key)
            # Test connection by listing models
            list(genai.list_models())
            self._configured = True
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Gemini API: {str(e)}\n"
                "Please check:\n"
                "1. Your API key is valid\n"
                "2. You have internet connection\n"
                "3. The Gemini API is accessible"
            )

    def _extract_text(self, response) -> str:
        if not response.candidates:
            return ""

        parts = response.candidates[0].content.parts

        texts = []
        for part in parts:
            if hasattr(part, "text") and part.text:
                texts.append(part.text)

        return "\n".join(texts).strip()
        
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        max_tokens: Optional[int] = None,
        add_suggestions: bool = True
    ) -> str:
        """
        Generate text using Gemini with rich, friendly tone and end-of-line suggestions.
        
        Args:
            prompt: User prompt
            system: System prompt (optional, will be prepended)
            temperature: Sampling temperature
            json_mode: Whether to force JSON output
            max_tokens: Maximum tokens to generate (None = no limit)
            add_suggestions: Whether to add follow-up suggestions at the end
            
        Returns:
            Generated text with optional follow-up suggestions
        """
        self._ensure_configured()
        
        try:
            # Enhanced system prompt for richer, friendlier responses
            enhanced_system = system or """You are a warm, engaging, and knowledgeable assistant. 
Your responses should be:
- **Friendly and conversational**: Write as if chatting with a colleague
- **Rich and detailed**: Provide thoughtful examples and explanations
- **Well-structured**: Use formatting (bold, lists, code blocks) for clarity
- **Encouraging**: Show enthusiasm for the topic
- **Practical**: Include actionable insights and tips when relevant

Format your response with clear sections if covering multiple points."""
            
            # Combine system and user prompt
            full_prompt = f"{enhanced_system}\n\nUser query: {prompt}"
            
            # Add suggestions guidance if enabled
            if add_suggestions and not json_mode:
                full_prompt += """\n\n**IMPORTANT**: After your main response, suggest 2-3 follow-up questions 
the user might find helpful. Format them as:

---
**You might also want to know:**
- Question 1?
- Question 2?
- Question 3?"""
            
            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            else:
                # Default to a richer response length if not specified
                generation_config["max_output_tokens"] = 1500
            
            # Note: response_mime_type is not supported in current Gemini SDK
            # JSON mode is handled via prompt engineering instead
            
            # Generate response
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            text = self._extract_text(response)
            
            # Add closing encouragement if suggestions were generated
            if add_suggestions and not json_mode and "You might also want to know" not in text:
                text += "\n\n---\n💡 *Feel free to ask me anything else you'd like to explore!*"
            
            return text
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {str(e)}")
    
    async def generate_structured(
        self,
        prompt: str,
        schema: type,
        system: Optional[str] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Generate structured output matching a Pydantic schema.
        
        Args:
            prompt: User prompt
            schema: Pydantic model class
            system: System prompt (optional)
            max_retries: Maximum retry attempts
            
        Returns:
            Validated Pydantic model instance
        """
        schema_json = schema.model_json_schema()
        enhanced_prompt = f"""{prompt}

You MUST respond with valid JSON matching this schema:
{json.dumps(schema_json, indent=2)}

Do not include any text outside the JSON. Do not use markdown code blocks."""
        
        for attempt in range(max_retries):
            try:
                response = await self.generate(
                    prompt=enhanced_prompt,
                    system=system or "You are a helpful assistant that outputs valid JSON.",
                    json_mode=True,
                    temperature=0.3
                )
                
                # Extract JSON from response
                json_text = self.json_guard.extract_json(response)
                parsed = json.loads(json_text)
                
                # Validate against schema
                return schema.model_validate(parsed)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate valid structured output after {max_retries} attempts: {e}")
                continue
        
        raise ValueError("Unexpected error in generate_structured")
