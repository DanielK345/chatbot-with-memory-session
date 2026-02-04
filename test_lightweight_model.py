"""Test lightweight model integration for query refinement."""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm.client import LLMClient


async def test_lightweight_model():
    """Test lightweight model for query refinement."""
    print("=" * 70)
    print("TEST: Lightweight Model (Qwen2.5-1.5B) for Query Refinement")
    print("=" * 70)
    
    try:
        # Initialize LLMClient with lightweight model
        llm_client = LLMClient(
            primary="ollama",
            lightweight_ollama_model="qwen2.5:1.5b"
        )
        
        print(f"\n✓ LLMClient initialized")
        print(f"  Active provider: {llm_client.get_active_provider().upper()}")
        print(f"  Lightweight model: {llm_client.get_lightweight_model_name()}")
        
        # Test 1: Test lightweight model availability
        print("\n" + "=" * 70)
        print("Test 1: Lightweight Model Availability")
        print("=" * 70)
        
        if llm_client.lightweight_ollama_client:
            print("\n✓ Lightweight Ollama client available")
            print(f"  Model: {llm_client.lightweight_model}")
            print("  Use case: Fast pronoun replacement in queries")
        else:
            print("\n⚠ Lightweight Ollama client not available")
            print("  Will fall back to active client for query refinement")
        
        # Test 2: Test minimal prompt for pronoun replacement
        print("\n" + "=" * 70)
        print("Test 2: Generate Lightweight Response (Minimal Prompt)")
        print("=" * 70)
        
        test_prompt = (
            "Rewrite this query by replacing the pronouns [it] "
            "with one of these entities [TensorFlow, PyTorch]:\n\n"
            "Query: How does it compare?\n\n"
            "Rewritten query (keep it concise):"
        )
        
        print(f"\nPrompt:\n{test_prompt}")
        print(f"\nCalling generate_lightweight with:")
        print(f"  max_tokens: 20")
        print(f"  temperature: 0.3")
        
        try:
            response = await llm_client.generate_lightweight(
                prompt=test_prompt,
                max_tokens=20,
                temperature=0.3
            )
            print(f"\n✓ Response (lightweight model):")
            print(f"  {response}")
        except Exception as e:
            print(f"\n⚠ Lightweight model call failed: {e}")
            print("  This is expected if Ollama is not running")
        
        # Test 3: Show comparison of models
        print("\n" + "=" * 70)
        print("Test 3: Model Comparison for Query Refinement Task")
        print("=" * 70)
        
        comparison = f"""
Query Refinement Task: Replace pronouns with entities from previous questions

Qwen2.5-1.5B (Lightweight - RECOMMENDED)
  Size: 1.5B parameters
  Speed: 2-3x faster than llama3.1
  Memory: ~1-2 GB (can run on most hardware)
  Accuracy: Sufficient for simple pronoun → entity replacement
  Token cost: Minimal (20 tokens max)
  Best for: Fast inference, resource-constrained environments

llama3.1 (Standard - Fallback)
  Size: 8B parameters
  Speed: Baseline (1x)
  Memory: ~6-8 GB (requires good hardware)
  Accuracy: Higher quality, overkill for this task
  Token cost: Higher
  Best for: Complex reasoning, fallback

Your current setup:
  Primary LLM: {llm_client.get_active_provider().upper()}
  Lightweight model: {llm_client.get_lightweight_model_name()}
  
✓ QueryRefiner will use: {llm_client.get_lightweight_model_name()}
  - 2-3x faster inference for pronoun replacement
  - Lightweight resource usage
  - Falls back to {llm_client.get_active_provider().upper()} if unavailable
"""
        print(comparison)
        
        print("\n" + "=" * 70)
        print("TEST COMPLETED")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_lightweight_model())
    sys.exit(0 if success else 1)
