"""Unified LLM client with Gemini (default) and Ollama (fallback)."""

import json
import os
from typing import Dict, Any, Optional, List, Union
from app.llm.ollama_client import OllamaClient
from app.utils.logging import get_logger

# Try importing Gemini
try:
    from app.llm.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiClient = None

logger = get_logger(__name__)


class LLMClient:
    """
    Unified LLM client with automatic fallback.
    Tries Gemini first, falls back to Ollama if Gemini fails.
    """
    
    def __init__(
        self,
        primary: str = "gemini",
        gemini_api_key: Optional[str] = None,
        gemini_model: str = "gemini-pro",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.1"
    ):
        """
        Initialize unified LLM client.
        
        Args:
            primary: Primary model to use ("gemini" or "ollama")
            gemini_api_key: Gemini API key (defaults to GOOGLE_API_KEY env var)
            gemini_model: Gemini model name
            ollama_base_url: Ollama API base URL
            ollama_model: Ollama model name
        """
        self.primary = primary.lower()
        self.gemini_client = None
        self.ollama_client = None
        self.active_client = None
        self.active_provider = None
        
        # Initialize Gemini if requested
        if self.primary == "gemini" or primary is None:
            if GEMINI_AVAILABLE and GeminiClient:
                try:
                    self.gemini_client = GeminiClient(
                        api_key=gemini_api_key,
                        model=gemini_model
                    )
                    # Test connection
                    self.gemini_client._ensure_configured()
                    self.active_client = self.gemini_client
                    self.active_provider = "gemini"
                    logger.info("✓ Gemini client initialized successfully")
                except Exception as e:
                    logger.warning(f"⚠ Gemini initialization failed: {e}")
                    logger.info("Falling back to Ollama...")
                    self.gemini_client = None
            else:
                logger.warning("⚠ Gemini not available (google-generativeai not installed)")
                logger.info("Falling back to Ollama...")
        
        # Initialize Ollama (as primary or fallback)
        if self.primary == "ollama" or self.active_client is None:
            try:
                self.ollama_client = OllamaClient(
                    base_url=ollama_base_url,
                    model=ollama_model
                )
                # Test connection (async, so we'll test on first use)
                self.active_client = self.ollama_client
                self.active_provider = "ollama"
                logger.info("✓ Ollama client initialized")
            except Exception as e:
                logger.error(f"✗ Ollama initialization failed: {e}")
                if self.active_client is None:
                    raise RuntimeError(
                        "Both Gemini and Ollama failed to initialize.\n"
                        "For Gemini: Set GOOGLE_API_KEY environment variable\n"
                        "For Ollama: Ensure Ollama is running (ollama serve) and model is pulled (ollama pull llama3.1)"
                    )
        
        if self.active_client is None:
            raise RuntimeError("No LLM client available")
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """
        Generate text using active LLM, with automatic fallback.
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            json_mode: Whether to force JSON output
            
        Returns:
            Generated text
        """
        # Try primary client first
        if self.active_client:
            try:
                return await self.active_client.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    json_mode=json_mode
                )
            except Exception as e:
                logger.warning(f"⚠ {self.active_provider} generation failed: {e}")
                
                # Try fallback
                if self.active_provider == "gemini" and self.ollama_client:
                    logger.info("Falling back to Ollama...")
                    try:
                        result = await self.ollama_client.generate(
                            prompt=prompt,
                            system=system,
                            temperature=temperature,
                            json_mode=json_mode
                        )
                        self.active_client = self.ollama_client
                        self.active_provider = "ollama"
                        logger.info("✓ Switched to Ollama")
                        return result
                    except Exception as fallback_error:
                        raise RuntimeError(
                            f"Both Gemini and Ollama failed.\n"
                            f"Gemini error: {e}\n"
                            f"Ollama error: {fallback_error}\n"
                            "Please check your configuration."
                        )
                elif self.active_provider == "ollama" and self.gemini_client:
                    logger.info("Falling back to Gemini...")
                    try:
                        result = await self.gemini_client.generate(
                            prompt=prompt,
                            system=system,
                            temperature=temperature,
                            json_mode=json_mode
                        )
                        self.active_client = self.gemini_client
                        self.active_provider = "gemini"
                        logger.info("✓ Switched to Gemini")
                        return result
                    except Exception as fallback_error:
                        raise RuntimeError(
                            f"Both Ollama and Gemini failed.\n"
                            f"Ollama error: {e}\n"
                            f"Gemini error: {fallback_error}\n"
                            "Please check your configuration."
                        )
                else:
                    raise
        
        raise RuntimeError("No LLM client available")
    
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
                json_text = self.active_client.json_guard.extract_json(response)
                parsed = json.loads(json_text)
                
                # Validate against schema
                return schema.model_validate(parsed)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate valid structured output after {max_retries} attempts: {e}")
                continue
        
        raise ValueError("Unexpected error in generate_structured")
    
    def get_active_provider(self) -> str:
        """Get the currently active LLM provider."""
        return self.active_provider or "unknown"
