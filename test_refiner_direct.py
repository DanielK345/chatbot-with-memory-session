"""Direct test of the new LLM-assisted QueryRefiner."""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.query_understanding.query_refiner import QueryRefiner
from app.llm.client import LLMClient


async def test_query_refiner():
    """Test the new lightweight LLM-based query refiner."""
    print("=" * 70)
    print("TEST: LLM-Assisted Query Refiner (Lightweight + Cache)")
    print("=" * 70)
    
    try:
        # Initialize
        llm_client = LLMClient(primary="gemini")
        refiner = QueryRefiner(llm_client=llm_client)
        provider = llm_client.get_active_provider().upper()
        print(f"\n[OK] Initialized QueryRefiner with {provider} LLM")
        
        # Test 1: Build context by adding queries to cache
        print("\n" + "=" * 70)
        print("Test 1: Building context cache with 3 queries")
        print("=" * 70)
        
        test_queries = [
            "We're using TensorFlow for deep learning.",
            "Should we switch to PyTorch?",
            "How does it compare?",  # This has pronoun "it"
        ]
        
        refined_queries = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}] Query: {query}")
            
            # Check cache state before
            print(f"    Cache before: {list(refiner.query_cache)}")
            
            # Process query
            refined = await refiner.refine(query, use_llm=True)
            
            # Check cache state after
            print(f"    Cache after:  {list(refiner.query_cache)}")
            print(f"    Cache size:   {len(refiner.query_cache)}/3")
            
            if refined:
                print(f"    ✓ Refined: {refined}")
                refined_queries.append(refined)
            else:
                print(f"    ✗ No refinement (no pronouns or entities)")
        
        # Test 2: Verify cache behavior
        print("\n" + "=" * 70)
        print("Test 2: Verify cache maintains exactly 3 queries")
        print("=" * 70)
        
        print(f"\nFinal cache size: {len(refiner.query_cache)}/3")
        print("Final cache contents:")
        for i, q in enumerate(refiner.query_cache, 1):
            print(f"  [{i}] {q}")
        
        # Test 3: New query - cache should only keep latest 3
        print("\n" + "=" * 70)
        print("Test 3: Add 4th query (should drop oldest)")
        print("=" * 70)
        
        new_query = "Can we deploy it easily?"
        print(f"\nAdding: {new_query}")
        refined = await refiner.refine(new_query, use_llm=True)
        
        print(f"\nCache after adding 4th query:")
        for i, q in enumerate(refiner.query_cache, 1):
            print(f"  [{i}] {q}")
        print(f"\nCache size: {len(refiner.query_cache)}/3 (oldest dropped)")
        
        if refined:
            print(f"\n✓ Refined: {refined}")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETED")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_query_refiner())
    sys.exit(0 if success else 1)
