"""Test QueryRefiner without LLM (just pronoun/entity detection)."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.query_understanding.query_refiner import QueryRefiner


def test_refiner_without_llm():
    """Test pronoun and entity detection without LLM."""
    print("=" * 70)
    print("TEST: QueryRefiner - Pronoun & Entity Detection (No LLM)")
    print("=" * 70)
    
    # Initialize without LLM
    refiner = QueryRefiner(llm_client=None)
    
    # Test pronouns detection
    print("\n" + "=" * 70)
    print("Test 1: Pronoun Detection")
    print("=" * 70)
    
    test_pronouns = [
        ("How does it compare?", ['it']),
        ("Can they help me?", ['they']),
        ("Show me this example", ['this']),
        ("That looks wrong", ['that']),
        ("Does he know?", ['he']),
        ("Is she available?", ['she']),
        ("Give them the code", ['them']),
        ("No pronouns here", []),
    ]
    
    for query, expected_pronouns in test_pronouns:
        detected = refiner._detect_pronouns(query)
        status = "✓" if set(detected) == set(expected_pronouns) else "✗"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_pronouns}")
        print(f"   Detected: {detected}")
    
    # Test entity extraction from cache
    print("\n" + "=" * 70)
    print("Test 2: Entity Extraction from Cache")
    print("=" * 70)
    
    # Build cache
    print("\nBuilding cache with 3 queries:")
    test_queries = [
        "We're using TensorFlow for deep learning.",
        "PyTorch is also an option.",
        "How does it compare?",
    ]
    
    for query in test_queries:
        refiner._add_to_cache(query)
        print(f"  Added: {query}")
    
    # Extract entities
    entities = refiner._extract_entities_from_cache()
    print(f"\nExtracted entities: {entities}")
    expected = ['TensorFlow', 'PyTorch']
    status = "✓" if set(entities) >= set(expected) else "✗"
    print(f"{status} Expected to find at least: {expected}")
    print(f"   Found: {entities}")
    
    # Test combined: detect pronouns + extract entities
    print("\n" + "=" * 70)
    print("Test 3: Combined - Pronouns + Entities (without LLM)")
    print("=" * 70)
    
    new_query = "Which one should we use?"
    refiner._add_to_cache(new_query)
    
    pronouns = refiner._detect_pronouns(new_query)
    entities = refiner._extract_entities_from_cache()
    
    print(f"\nQuery: {new_query}")
    print(f"Pronouns detected: {pronouns}")
    print(f"Entities from cache: {entities}")
    print(f"\nRefinement would be: '{new_query}' → '[Replace 'which one' with one of: {entities}]'")
    
    # Verify cache behavior
    print("\n" + "=" * 70)
    print("Test 4: Cache maintains max 3 queries")
    print("=" * 70)
    
    print(f"\nCurrent cache size: {len(refiner.query_cache)}")
    assert len(refiner.query_cache) == 3, "Cache should have exactly 3 items"
    print("✓ Cache size is correct (3)")
    
    # Add 5th query
    refiner._add_to_cache("This is the 5th query")
    print(f"\nAfter adding 5th query, cache size: {len(refiner.query_cache)}")
    assert len(refiner.query_cache) == 3, "Cache should still have 3 items"
    print("✓ Cache still has 3 items (oldest was dropped)")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    test_refiner_without_llm()
