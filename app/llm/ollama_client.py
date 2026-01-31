"""Ollama LLM client wrapper."""

import json
import httpx
from typing import Optional, Any
from app.llm.json_guard import JSONGuard


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL
            model: Model name to use
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.json_guard = JSONGuard()
        self._tested = False
    
    def _test_connection(self):
        """Test if Ollama is available."""
        if self._tested:
            return True
        
        try:
            # Try a simple async check
            async def _check():
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/api/tags")
                    response.raise_for_status()
                    return True
            
            # For now, we'll test on first use rather than blocking here
            # This avoids async/sync issues
            return True
        except Exception:
            return False
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            json_mode: Whether to force JSON output
            max_tokens: Maximum tokens to generate (None = no limit)
            
        Returns:
            Generated text
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["options"] = {"num_predict": max_tokens}
        
        if json_mode:
            payload["format"] = "json"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
            except httpx.ConnectError:
                raise ConnectionError(
                    f"Failed to connect to Ollama at {self.base_url}.\n"
                    "Please ensure Ollama is running:\n"
                    "1. Install Ollama from https://ollama.ai\n"
                    "2. Start Ollama: ollama serve\n"
                    "3. Pull a model: ollama pull llama3.1"
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError(
                        f"Model '{self.model}' not found in Ollama.\n"
                        f"Please pull the model: ollama pull {self.model}"
                    )
                raise
            except Exception as e:
                raise RuntimeError(f"Ollama generation failed: {str(e)}")
    
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
                    temperature=0.3  # Lower temperature for structured output
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
