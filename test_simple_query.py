"""Quick test of query understanding pipeline with simple queries."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.memory.session_store import SessionStore
from app.core.pipeline import ChatPipeline
from app.llm.gemini_client import GeminiClient
from app.utils.logging import ConversationLogger, UserQueryLogger, SessionSummaryLogger


async def test_simple():
    """Test a few simple ambiguous queries to verify logging."""
    # Setup
    session_store = SessionStore(storage_type="file")
    llm_client = GeminiClient()
    conversation_logger = ConversationLogger()
    query_logger = UserQueryLogger()
    session_summary_logger = SessionSummaryLogger()
    
    pipeline = ChatPipeline(
        session_store=session_store,
        llm_client=llm_client,
        max_context_tokens=10000,
        keep_recent_messages=5,
        enable_query_understanding=True,
        conversation_logger=conversation_logger,
        query_logger=query_logger,
        session_summary_logger=session_summary_logger
    )
    
    session_id = "test_simple"
    
    # Test 1: Simple unambiguous query
    print("\n[Test 1] Simple clear query:")
    result1 = await pipeline.process_message(session_id, "What is Python?")
    print(f"  Response length: {len(result1['response'])}")
    
    # Test 2: Ambiguous query (vague pronoun)
    print("\n[Test 2] Ambiguous query with 'it':")
    result2 = await pipeline.process_message(session_id, "How do I use it?")
    print(f"  Response length: {len(result2['response'])}")
    
    # Test 3: Query with context setup then pronoun
    print("\n[Test 3] Context setup then pronoun:")
    result3a = await pipeline.process_message(session_id, "I'm building a web API with FastAPI.")
    result3b = await pipeline.process_message(session_id, "How do I optimize it for performance?")
    print(f"  First response length: {len(result3a['response'])}")
    print(f"  Second response length: {len(result3b['response'])}")
    
    # Read logs to verify
    print("\n[Checking query_logger output]")
    with open(query_logger.log_file, "r") as f:
        lines = f.readlines()
        # Show last few entries
        for i, line in enumerate(lines[-20:]):
            if line.strip():
                print(f"  {line.strip()[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_simple())
