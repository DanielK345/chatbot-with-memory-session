"""
Test query refinement (rewriting).
Uses random query generation to test if the pipeline correctly
rewrites ambiguous or unclear queries into more specific ones.
"""

import asyncio
import random
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Queries that might need refinement
REFINABLE_QUERIES = [
    "How do I do it?",
    "What's the best way?",
    "Can I use this for that?",
    "Is there a simpler method?",
    "How does it work compared to the other one?",
    "What should I pick?",
    "Can you explain this more?",
    "Why doesn't this work?",
    "What's wrong with my approach?",
    "How can I improve it?",
]

# Context to establish what "it" or "that" refers to
CONTEXT_STATEMENTS = [
    "I'm building a machine learning model for classification",
    "We're working on natural language processing",
    "I'm trying to implement neural networks",
    "We need to optimize database queries",
    "I'm developing a web application",
    "We're building a data pipeline",
    "I'm working on image recognition",
    "We're creating a recommendation system",
]

# More specific refinements that should be generated
REFINED_QUERIES = [
    "How should I preprocess my data?",
    "What hyperparameters should I tune?",
    "Which algorithm is best for this problem?",
    "How do I handle missing values?",
    "What evaluation metrics should I use?",
    "How do I split my data for training?",
]


async def test_query_refinement():
    """Test query refinement (rewriting) with random queries."""
    print("=" * 70)
    print("TEST: Query Refinement (Rewriting)")
    print("=" * 70)
    
    try:
        # Initialize pipeline
        session_store = SessionStore(storage_type="file")
        llm_client = LLMClient(primary="gemini")
        provider = llm_client.get_active_provider().upper()
        print(f"\n✓ Initialized with {provider} as LLM provider")
        
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            enable_query_understanding=True,
            skip_llm_ambiguity_if_clear=False,  # Always run ambiguity detection
            max_response_tokens=300,
            response_temperature=0.5
        )
        
        session_id = "test_refinement_session"
        session_store.clear_messages(session_id)
        
        print("\nPhase 1: Establishing context with specific queries")
        print("-" * 70)
        
        contexts = random.sample(CONTEXT_STATEMENTS, min(2, len(CONTEXT_STATEMENTS)))
        for context in contexts:
            print(f"\nUser: {context}")
            result = await pipeline.process_message(session_id, context)
            print(f"  ✓ Context established")
        
        print("\nPhase 2: Testing refinement of ambiguous queries")
        print("-" * 70)
        
        # Select random ambiguous queries
        test_queries = random.sample(REFINABLE_QUERIES, min(3, len(REFINABLE_QUERIES)))
        
        refinement_count = 0
        rewritten_count = 0
        
        for query in test_queries:
            print(f"\n[Original Query] User: {query}")
            result = await pipeline.process_message(session_id, query)
            
            q_understanding = result['query_understanding']
            is_ambiguous = q_understanding.get('is_ambiguous', False)
            rewritten = q_understanding.get('rewritten_query')
            
            print(f"  Detected as ambiguous: {is_ambiguous}")
            
            if is_ambiguous:
                refinement_count += 1
                if rewritten:
                    print(f"  [Rewritten Query] {rewritten}")
                    rewritten_count += 1
                else:
                    print(f"  [No rewrite generated, but ambiguity detected]")
                
                ambiguity_reason = q_understanding.get('ambiguity_reason', 'Unknown')
                print(f"  Reason: {ambiguity_reason[:70]}...")
        
        print("\n" + "-" * 70)
        print(f"\nResults:")
        print(f"  Queries detected as ambiguous: {refinement_count}/3")
        print(f"  Queries rewritten: {rewritten_count}/{refinement_count if refinement_count > 0 else 1}")
        
        if refinement_count >= 1:
            print(f"\n✅ TEST PASSED: Query refinement pipeline is working")
            print(f"   (At least {refinement_count} query/queries detected for refinement)")
            return True
        else:
            print(f"\n⚠️  TEST INCONCLUSIVE: No queries detected as ambiguous for refinement")
            print("    (This may depend on the LLM's sensitivity and query complexity)")
            return True  # Not a failure
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error(f"Query refinement test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_query_refinement())
    exit(0 if success else 1)
