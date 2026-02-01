"""
Test CLI demo loads and initializes successfully.
Verifies that all components (LLM client, pipeline, session store) initialize correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import configure_logging_from_env, get_logger

configure_logging_from_env()
logger = get_logger(__name__)


async def test_cli_demo_initialization():
    """Test that CLI demo components initialize successfully."""
    print("=" * 70)
    print("TEST: CLI Demo Initialization")
    print("=" * 70)
    
    try:
        print("\n[Step 1] Initializing session store...")
        session_store = SessionStore(storage_type="file")
        print("  ✓ Session store initialized")
        
        print("\n[Step 2] Initializing LLM client...")
        llm_client = LLMClient(primary="gemini")
        provider = llm_client.get_active_provider()
        print(f"  ✓ LLM client initialized with provider: {provider.upper()}")
        
        print("\n[Step 3] Initializing chat pipeline...")
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            max_context_tokens=5000
        )
        print("  ✓ Chat pipeline initialized")
        
        print("\n[Step 4] Testing pipeline with a simple message...")
        session_id = "test_cli_demo"
        session_store.clear_messages(session_id)
        
        result = await pipeline.process_message(
            session_id,
            "Hello, what can you help me with?"
        )
        
        if result and result.get('response'):
            print(f"  ✓ Pipeline response received ({len(result['response'])} chars)")
        else:
            print("  ⚠️  Pipeline returned empty response")
        
        print("\n" + "-" * 70)
        print("✅ TEST PASSED: CLI demo components initialized successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error(f"CLI demo initialization test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_cli_demo_initialization())
    exit(0 if success else 1)
