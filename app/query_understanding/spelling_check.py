"""Spelling check for user queries - rule-based, NO LLM."""

import re
from typing import Dict, Any


class SpellingChecker:
    """Corrects spelling errors using rule-based heuristics only."""
    
    # Common typos and their corrections (edit distance ≤ 1)
    COMMON_TYPOS = {
        'teh': 'the',
        'abd': 'and',
        'recieve': 'receive',
        'occured': 'occurred',
        'definately': 'definitely',
        'seperate': 'separate',
        'your': 'you\'re',  # common confusion
        'their': 'there',   # common confusion (context-dependent)
        'hwat': 'what',
        'whcih': 'which',
        'taht': 'that',
        'wich': 'which',
        'doesnt': 'doesn\'t',
        'cant': 'can\'t',
        'wont': 'won\'t',
    }
    
    # Domain terms to NEVER modify
    DOMAIN_TERMS = {
        'llm', 'fastapi', 'ollama', 'gemini', 'ollama', 'redis', 'langchain',
        'vectordb', 'embeddings', 'tokenizer', 'encoder', 'llama', 'qwen',
        'mistral', 'neural', 'lstm', 'transformer', 'huggingface', 'pytorch',
        'tensorflow', 'sklearn', 'scikit', 'keras', 'jax', 'numpy', 'pandas',
        'streamlit', 'gradio', 'uvicorn', 'gunicorn', 'postgresql', 'mongodb',
        'elasticsearch', 'pinecone', 'weaviate', 'milvus', 'faiss'
    }
    
    def __init__(self):
        """Initialize spelling checker."""
        pass
    
    def check(self, query: str) -> Dict[str, Any]:
        """
        Check and fix spelling errors in query.
        
        Returns:
            {
                "original_query": str,
                "has_spelling_error": bool,
                "rewritten_query": str (if errors found)
            }
        """
        original = query
        fixed = query
        has_error = False
        
        # Step 1: Fix repeated words (e.g., "the the" -> "the")
        fixed = re.sub(r'\b(\w+)\s+\1\b', r'\1', fixed, flags=re.IGNORECASE)
        if fixed != original:
            has_error = True
        
        # Step 2: Fix missing spaces (e.g., "thecat" -> "the cat" - conservative)
        # Only for very obvious cases to avoid breaking domain terms
        words = fixed.split()
        
        # Step 3: Fix common typos (but NOT domain terms)
        words_lower = [w.lower() for w in words]
        fixed_words = []
        for word in words:
            word_clean = word.rstrip('.,!?;:')
            word_lower = word_clean.lower()
            punctuation = word[len(word_clean):]
            
            # Check if it's a domain term - skip if it is
            if word_lower in self.DOMAIN_TERMS:
                fixed_words.append(word)
                continue
            
            # Check for typo match
            if word_lower in self.COMMON_TYPOS:
                corrected = self.COMMON_TYPOS[word_lower]
                fixed_words.append(corrected + punctuation)
                has_error = True
            else:
                fixed_words.append(word)
        
        fixed = ' '.join(fixed_words)
        
        return {
            "original_query": original,
            "has_spelling_error": has_error,
            "rewritten_query": fixed if has_error else None
        }
    
if __name__ == "__main__":
    checker = SpellingChecker()
    test_queries = [
        "Teh cat sat on teh mat.",
        "I cant beleive it happend!",
        "Using LLMs is fun.",
        "This is definately a test.",
        "The the quick brown fox.",
        "Hwat is the capital of France?"
    ]
    
    for q in test_queries:
        result = checker.check(q)
        print(f"Original: {result['original_query']}")
        if result['has_spelling_error']:
            print(f"Corrected: {result['rewritten_query']}\n")
        else:
            print("No spelling errors found.\n")
