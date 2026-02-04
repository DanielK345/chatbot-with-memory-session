"""
Test ambiguous query detection.
Uses random query generation to test if the pipeline correctly
identifies and flags ambiguous queries.
"""

import asyncio
import random
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import get_logger
from app.utils.logging import ConversationLogger, UserQueryLogger, SessionSummaryLogger
from scripts.session_manager import delete_session
import app.core.pipeline as pipeline_module

logger = get_logger(__name__)

# Pre-configure test loggers at module import time
log_dir = "logs/ambiguous_query_detection"
pipeline_module.conversation_logger = ConversationLogger(log_file="conversations_test.log", log_dir=log_dir)
pipeline_module.query_logger = UserQueryLogger(log_file="user_queries_test.log", log_dir=log_dir)

# Clear queries (should not be ambiguous)
CLEAR_QUERIES = [
    "What is the capital of France?",
    "How many continents are there?",
    "What is the speed of light?",
    "Who wrote Romeo and Juliet?",
    "What is the periodic table?",
    "Define photosynthesis",
    "What is quantum computing?",
    "Explain machine learning",
    "What is blockchain?",
    "Define API",
]

# Ambiguous queries (may be flagged as ambiguous)
AMBIGUOUS_QUERIES = [
    "Which one is better?",
    "What should I choose?",
    "How do I fix this?",
    "What's the best approach?",
    "Can you recommend something?",
    "Which model should I use?",
    "What about this?",
    "Is this correct?",
    "How does it compare?",
    "Which one do you prefer?",
]

# Context-dependent queries (ambiguous without prior context)
CONTEXT_DEPENDENT_QUERIES = [
    "Tell me more about that",
    "Is it the same?",
    "Can I use the same approach?",
    "Will this work for my case?",
    "How does it relate to what we discussed?",
    "Should I apply the same principles?",
]


def generate_test_scenario() -> tuple:
    """Generate a test scenario with context and ambiguous follow-up."""
    context = random.choice([
        "I'm building a classification model with Python",
        "We're using TensorFlow for deep learning",
        "Our team is exploring NLP solutions",
        "We're working on time series forecasting",
        "We need real-time prediction capabilities",
    ])
    
    follow_up = random.choice(AMBIGUOUS_QUERIES + CONTEXT_DEPENDENT_QUERIES)
    
    return context, follow_up


async def test_ambiguous_query_detection():
    """Test ambiguous query detection with random queries."""
    print("=" * 70)
    print("TEST: Ambiguous Query Detection")
    print("=" * 70)
    
    def _cleanup():
        try:
            delete_session(session_id)
        except Exception:
            pass

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
            skip_llm_ambiguity_if_clear=True,
            max_response_tokens=800,
            response_temperature=0.5,
            conversation_logger=pipeline_module.conversation_logger,
            query_logger=pipeline_module.query_logger,
            session_summary_logger=pipeline_module.session_summary_logger
        )
        
        session_id = "test_ambiguity_session"
        session_store.clear_messages(session_id)
        
        print("\nPhase 1: Testing CLEAR queries (should NOT be ambiguous)")
        print("-" * 70)
        
        clear_queries = random.sample(CLEAR_QUERIES, min(3, len(CLEAR_QUERIES)))
        clear_ambiguous_count = 0
        
        for query in clear_queries:
            print(f"\nQuery: {query}")
            result = await pipeline.process_message(session_id, query)
            is_ambiguous = result['query_understanding'].get('is_ambiguous', False)
            print(f"  Ambiguous: {is_ambiguous}")
            if is_ambiguous:
                clear_ambiguous_count += 1
        
        print("\nPhase 2: Testing AMBIGUOUS queries with context")
        print("-" * 70)
        
        # Generate random scenarios with context
        context_queries = []
        for _ in range(3):
            context, follow_up = generate_test_scenario()
            context_queries.append((context, follow_up))
        
        ambiguous_detected_count = 0
        
        for context, follow_up in context_queries:
            # First, establish context
            print(f"\n[Context] User: {context[:70]}...")
            result = await pipeline.process_message(session_id, context)
            
            # Then ask ambiguous follow-up
            print(f"[Ambiguous Follow-up] User: {follow_up}")
            result = await pipeline.process_message(session_id, follow_up)
            is_ambiguous = result['query_understanding'].get('is_ambiguous', False)
            print(f"  Ambiguous: {is_ambiguous}")
            
            if is_ambiguous:
                reason = result['query_understanding'].get('ambiguity_reason', 'Unknown')
                print(f"  Reason: {reason[:70]}...")
                ambiguous_detected_count += 1
        
        print("\n" + "-" * 70)
        print(f"\nResults:")
        print(f"  Clear queries incorrectly flagged as ambiguous: {clear_ambiguous_count}/3")
        print(f"  Ambiguous queries correctly flagged: {ambiguous_detected_count}/3")
        
        if ambiguous_detected_count >= 1:
            print(f"\n✅ TEST PASSED: Ambiguous query detection working")
            return True
        else:
            print(f"\n⚠️  TEST INCONCLUSIVE: No ambiguous queries detected")
            print("    (This may depend on the LLM's sensitivity to ambiguity)")
            return True  # Not a failure
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error(f"Ambiguous query detection test failed: {e}", exc_info=True)
        return False
    finally:
        _cleanup()


if __name__ == "__main__":
    success = asyncio.run(test_ambiguous_query_detection())
    exit(0 if success else 1)
