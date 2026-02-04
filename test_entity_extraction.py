"""Test entity extraction from cache."""

import sys
import re
from pathlib import Path
from collections import deque

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_entity_extraction():
    """Test the entity extraction from cache."""
    
    # Simulate cache
    query_cache = deque(maxlen=3)
    
    test_queries = [
        "We're using TensorFlow for deep learning.",
        "Should we switch to PyTorch?",
        "How does it compare?",
    ]
    
    for query in test_queries:
        query_cache.append(query)
    
    # Extract entities
    entities = []
    bad_words = {'I', 'The', 'This', 'That', 'What', 'Which', 'How', 'Are', 'Is', 'So', 'We', 'You', 'They', 'Can', 'Should', 'Would', 'Could', 'Do', 'Did', 'Have', 'Has', 'Will', 'A', 'Or'}
    
    print("Cache contents:")
    for i, q in enumerate(query_cache, 1):
        print(f"  [{i}] {q}")
    
    print("\nExtracting entities:")
    for query_text in query_cache:
        print(f"\nQuery: {query_text}")
        words = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', query_text)
        print(f"  Capitalized words: {words}")
        
        for word in words:
            print(f"    - {word}")
            print(f"      len >= 3: {len(word) >= 3}")
            print(f"      not in bad_words: {word not in bad_words}")
            print(f"      not in entities: {word not in entities}")
            
            if len(word) >= 3 and word not in bad_words and word not in entities:
                print(f"      ✓ Added")
                entities.append(word)
            else:
                print(f"      ✗ Filtered")
    
    print(f"\nFinal entities: {entities}")
    print(f"Entities with 'it' pronoun in queries: {entities}")


if __name__ == "__main__":
    test_entity_extraction()
