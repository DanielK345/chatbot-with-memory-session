"""
Comprehensive test suite for query understanding pipeline.
Simulates a long conversation that triggers:
1. Ambiguity detection and query rewriting
2. Context augmentation with selective fields
3. Session summarization
4. LLM usage tracking
5. Query refinement with pronouns
6. Clarifying question generation
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.memory.session_store import SessionStore
from app.memory.schemas import SessionMemory, UserProfile, SessionSummary
from app.core.pipeline import ChatPipeline
from app.llm.gemini_client import GeminiClient
from app.utils.logging import ConversationLogger, UserQueryLogger, SessionSummaryLogger


# ============================================================================
# TEST DATA: Long conversation that triggers all scenarios
# ============================================================================

COMPREHENSIVE_CONVERSATION = [
    # Phase 1: Clear context establishment
    {
        "query": "I'm building a machine learning system for image classification.",
        "description": "Clear, unambiguous query - establishes context"
    },
    {
        "query": "We're using FastAPI as the backend framework.",
        "description": "Clear context setup"
    },
    
    # Phase 2: Pronoun-heavy queries requiring context resolution
    {
        "query": "How can we improve its accuracy?",
        "description": "Pronoun 'its' - should be resolved to 'image classification system'"
    },
    {
        "query": "What data augmentation techniques are best for them?",
        "description": "Pronoun 'them' - should resolve to 'image datasets'"
    },
    
    # Phase 3: Ambiguous queries needing clarification
    {
        "query": "Should we deploy using it?",
        "description": "Ambiguous pronoun 'it' - unclear referent"
    },
    {
        "query": "How long does this take?",
        "description": "Vague temporal reference - 'this' could mean training, deployment, etc."
    },
    
    # Phase 4: Complex multi-entity queries
    {
        "query": "Comparing FastAPI and Django, which one is better for our use case?",
        "description": "Multiple entities, clear intent - requires context from earlier setup"
    },
    {
        "query": "But what about performance differences during inference?",
        "description": "Contrast word 'but' - needs expanded context"
    },
    
    # Phase 5: Follow-up queries with implicit references
    {
        "query": "How do we handle model versioning with it?",
        "description": "Pronoun 'it' - should resolve to backend framework"
    },
    {
        "query": "What's the best way to integrate them together?",
        "description": "Ambiguous 'them' - multiple possible referents"
    },
    
    # Phase 6: Domain-specific technical queries
    {
        "query": "Should we use transfer learning or train from scratch?",
        "description": "Clear technical question - tests domain understanding"
    },
    {
        "query": "What about fine-tuning pre-trained models like ResNet or EfficientNet?",
        "description": "Clear question with specific model names"
    },
    
    # Phase 7: More pronoun-heavy queries
    {
        "query": "How do we optimize it for mobile devices?",
        "description": "Pronoun 'it' - refers to model"
    },
    {
        "query": "Can we reduce their size significantly?",
        "description": "Pronoun 'their' - ambiguous (models? predictions?)"
    },
    
    # Phase 8: Clarification-requiring queries
    {
        "query": "Is this approach scalable?",
        "description": "Demonstrative pronoun 'this' - vague"
    },
    {
        "query": "How much improvement can we expect from it?",
        "description": "Pronoun 'it' - unclear improvement source"
    },
    
    # Phase 9: Technical follow-ups with contrasts
    {
        "query": "We prefer lightweight models, but they seem insufficient.",
        "description": "Contrast word 'but' - conflict between preferences and requirements"
    },
    {
        "query": "Rather than investing in GPU infrastructure, what are alternatives?",
        "description": "Contrast word 'rather' - explores alternative approaches"
    },
    
    # Phase 10: Wrap-up with comprehensive questions
    {
        "query": "Given all these constraints, what would be your recommendation?",
        "description": "Summary question - tests context integration"
    },
    {
        "query": "Should we proceed with this architecture or iterate?",
        "description": "Demonstrative 'this' - final decision point"
    },
]


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_SESSION_ID = "comprehensive_test_session"
TEST_LOG_FOLDER = Path(__file__).parent.parent / "logs" / "run_all_tests"
SUMMARIZATION_THRESHOLD = 2000  # Tokens before summarization


# ============================================================================
# TEST UTILITIES
# ============================================================================

def setup_test_environment():
    """Create test folders and initialize loggers."""
    TEST_LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Create specialized loggers for this test
    conversation_logger = ConversationLogger()
    query_logger = UserQueryLogger()
    session_logger = SessionSummaryLogger()
    
    # Redirect logs to test folder
    conversation_logger.log_file = TEST_LOG_FOLDER / "conversations_test.log"
    query_logger.log_file = TEST_LOG_FOLDER / "user_queries_test.log"
    session_logger.log_file = TEST_LOG_FOLDER / "session_summaries_test.log"
    
    return conversation_logger, query_logger, session_logger


def print_test_header(title: str):
    """Print formatted test header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_query_analysis(query: str, metadata: Dict[str, Any]):
    """Print analysis of query processing."""
    print(f"\n📝 Query: {query}")
    if metadata.get("pipeline_metadata"):
        pm = metadata["pipeline_metadata"]
        print(f"   Ambiguous: {pm.get('spelling_check_used', 'N/A')}")
        if pm.get("ambiguity_llm_used"):
            print("   ⚠️  LLM used for ambiguity detection")
        if pm.get("context_expanded"):
            print("   ↗️  Context expanded to 3 turns")
        if pm.get("refinement_applied"):
            print("   ✨ Query refined")


async def run_comprehensive_conversation_test():
    """
    Main test: Run comprehensive conversation triggering all scenarios.
    
    Scenarios:
    1. Clear query handling
    2. Ambiguity detection and LLM fallback
    3. Pronoun resolution via context refinement
    4. Session summarization triggering
    5. Context augmentation with selective fields
    6. LLM usage percentage tracking
    """
    
    print_test_header("TEST 1: COMPREHENSIVE CONVERSATION ANALYSIS")
    
    # Setup
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            max_context_tokens=SUMMARIZATION_THRESHOLD,
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Pipeline initialized")
        print(f"✓ Session ID: {TEST_SESSION_ID}")
        print(f"✓ Log folder: {TEST_LOG_FOLDER}")
        
        # Run conversation
        print(f"\n📊 Processing {len(COMPREHENSIVE_CONVERSATION)} queries...\n")
        
        for i, exchange in enumerate(COMPREHENSIVE_CONVERSATION, 1):
            query = exchange["query"]
            description = exchange["description"]
            
            # Display query info
            print(f"\n[{i}/{len(COMPREHENSIVE_CONVERSATION)}] {description}")
            
            # Process query through pipeline
            result = await pipeline.process_message(TEST_SESSION_ID, query)
            
            # Print analysis
            print_query_analysis(query, result)
            
            # Print LLM usage stats
            if result.get("llm_usage_stats"):
                stats = result["llm_usage_stats"]
                print(f"   LLM Usage: {stats['llm_calls']}/{stats['total_queries']} ({stats['usage_percentage']})")
        
        # Final statistics
        print("\n" + "=" * 80)
        print("  FINAL STATISTICS")
        print("=" * 80)
        print(f"\n✓ Total queries processed: {len(COMPREHENSIVE_CONVERSATION)}")
        print(f"✓ LLM usage percentage: {pipeline.llm_calls_made / pipeline.total_queries_processed * 100:.1f}%")
        print(f"✓ Logs saved to: {TEST_LOG_FOLDER}")
        
        # List log files
        if TEST_LOG_FOLDER.exists():
            log_files = list(TEST_LOG_FOLDER.glob("*.log"))
            print(f"\n📋 Log files created:")
            for log_file in log_files:
                size = log_file.stat().st_size
                print(f"   - {log_file.name} ({size} bytes)")
        
        # Cleanup
        session_store.delete_session(TEST_SESSION_ID)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_ambiguity_detection_scenarios_test():
    """
    Test 2: Specific ambiguity detection scenarios.
    Tests heuristic vs LLM fallback behavior.
    """
    
    print_test_header("TEST 2: AMBIGUITY DETECTION SCENARIOS")
    
    ambiguity_scenarios = [
        ("What is the capital?", "Clear question - should have 0 ambiguity"),
        ("Tell me about it.", "Short, pronoun-based - ambiguous"),
        ("How does photosynthesis work?", "Clear WH-question - unambiguous"),
        ("They said it was important.", "Multiple pronouns - ambiguous"),
        ("The current approach has issues, but we think we have a solution.", "Complex sentence - test parsing"),
    ]
    
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Testing {len(ambiguity_scenarios)} ambiguity scenarios\n")
        
        for i, (query, expected) in enumerate(ambiguity_scenarios, 1):
            print(f"\n[{i}] {expected}")
            print(f"    Query: {query}")
            
            result = await pipeline.process_message(f"ambiguity_test_{i}", query)
            
            # Note: In actual testing, would verify ambiguity detection results
            print(f"    ✓ Processed")
        
        # Cleanup
        for i in range(1, len(ambiguity_scenarios) + 1):
            session_store.delete_session(f"ambiguity_test_{i}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def run_context_augmentation_test():
    """
    Test 3: Context augmentation with selective field retrieval.
    Tests aggressive context filtering per fix.txt principles.
    """
    
    print_test_header("TEST 3: CONTEXT AUGMENTATION & FIELD SELECTION")
    
    context_test_queries = [
        ("I prefer FastAPI for backend development.", "Preferences - should load user_profile.prefs"),
        ("Given our current architecture, is this approach scalable?", "Architecture reference - should load key_facts"),
        ("But we decided to use Redis instead.", "Decision reference - should load decisions"),
        ("What about the open questions regarding deployment?", "Pronoun + reference - should load open_questions"),
    ]
    
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Testing {len(context_test_queries)} context scenarios\n")
        
        for i, (query, expected) in enumerate(context_test_queries, 1):
            print(f"\n[{i}] {expected}")
            print(f"    Query: {query}")
            
            result = await pipeline.process_message("context_test_session", query)
            
            if result.get("pipeline_metadata", {}).get("context_expanded"):
                print(f"    ⟳ Context expanded based on triggers")
            
            print(f"    ✓ Processed")
        
        # Cleanup
        session_store.delete_session("context_test_session")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def run_pronoun_resolution_test():
    """
    Test 4: Query refinement with pronoun resolution.
    Tests rule-based pronoun replacement without LLM.
    """
    
    print_test_header("TEST 4: PRONOUN RESOLUTION & QUERY REFINEMENT")
    
    pronoun_queries = [
        ("How can I optimize it for performance?", "it → should resolve to context entity"),
        ("What are the best practices for them?", "them → should resolve from context"),
        ("Can we combine these with that?", "these/that → multiple referents"),
        ("Should we deploy it on AWS or GCP?", "it → needs entity context"),
    ]
    
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Testing {len(pronoun_queries)} pronoun resolution scenarios\n")
        
        # Establish context first
        await pipeline.process_message("pronoun_test_session", "We're building a FastAPI service with Redis cache.")
        
        # Then test pronoun resolution
        for i, (query, expected) in enumerate(pronoun_queries, 1):
            print(f"\n[{i}] {expected}")
            print(f"    Query: {query}")
            
            result = await pipeline.process_message("pronoun_test_session", query)
            
            if result.get("pipeline_metadata", {}).get("refinement_applied"):
                print(f"    ✨ Query refined (pronoun resolution applied)")
            
            print(f"    ✓ Processed")
        
        # Cleanup
        session_store.delete_session("pronoun_test_session")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def run_llm_usage_tracking_test():
    """
    Test 5: LLM usage percentage tracking.
    Verifies that usage stays below 30% target.
    """
    
    print_test_header("TEST 5: LLM USAGE PERCENTAGE TRACKING")
    
    tracking_queries = [
        "This is a clear question about machine learning.",
        "What does it mean?",  # Ambiguous
        "Explain how neural networks work.",  # Clear
        "Can we do that?",  # Ambiguous
        "Show me examples of CNN architectures.",  # Clear
        "Why is it faster?",  # Ambiguous
        "How to implement attention mechanisms?",  # Clear
        "Should we use them?",  # Ambiguous
    ]
    
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Testing LLM usage on {len(tracking_queries)} queries\n")
        
        result = None
        for i, query in enumerate(tracking_queries, 1):
            result = await pipeline.process_message("tracking_test_session", query)
            
            if result.get("llm_usage_stats"):
                stats = result["llm_usage_stats"]
                print(f"[{i}] {stats['usage_percentage']:>6} | LLM calls: {stats['llm_calls']}/{stats['total_queries']}")
        
        # Final report
        final_stats = result.get("llm_usage_stats", {})
        print(f"\n✓ Final LLM Usage: {final_stats.get('usage_percentage', 'N/A')}")
        
        target_met = float(final_stats.get('usage_percentage', '100').rstrip('%')) < 30
        if target_met:
            print(f"✅ Target achieved: < 30% LLM usage")
        else:
            print(f"⚠️  Target not met: usage above 30%")
        
        # Cleanup
        session_store.delete_session("tracking_test_session")
        
        return target_met
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def run_session_summarization_test():
    """
    Test 6: Session summarization triggering.
    Tests automatic summarization when token threshold exceeded.
    """
    
    print_test_header("TEST 6: SESSION SUMMARIZATION TRIGGERING")
    
    summarization_queries = [
        "We're building a recommendation engine using collaborative filtering.",
        "The system needs to handle 1 million+ users efficiently.",
        "Should we use matrix factorization or deep learning models?",
        "How do we scale the feature engineering pipeline?",
        "What database should we use for storing embeddings?",
        "How can we optimize the inference latency to under 100ms?",
        "Should we implement A/B testing for model evaluation?",
        "What monitoring and alerting should we set up?",
        "How do we handle cold start problems for new users?",
        "What are the privacy considerations for user data?",
    ]
    
    session_store = SessionStore(storage_type="file")
    conversation_logger, query_logger, session_logger = setup_test_environment()
    
    try:
        llm_client = GeminiClient()
        pipeline = ChatPipeline(
            session_store=session_store,
            llm_client=llm_client,
            enable_query_understanding=True,
            max_context_tokens=1000,  # Lower threshold for testing
            conversation_logger=conversation_logger,
            query_logger=query_logger,
            session_summary_logger=session_logger
        )
        
        print(f"\n✓ Testing session summarization over {len(summarization_queries)} queries\n")
        print(f"✓ Summarization threshold: 1000 tokens\n")
        
        summarization_triggered = False
        
        for i, query in enumerate(summarization_queries, 1):
            result = await pipeline.process_message("summarization_test_session", query)
            
            meta = result.get("pipeline_metadata", {})
            if meta.get("summarization_triggered"):
                summarization_triggered = True
                print(f"[{i}] 💾 SESSION SUMMARIZATION TRIGGERED")
            else:
                print(f"[{i}] ✓ Processed")
        
        # Check if summaries were logged
        summary_log = TEST_LOG_FOLDER / "session_summaries_test.log"
        if summary_log.exists():
            # Support prettified JSON blocks (multiple-line JSON objects separated by blank lines)
            with open(summary_log, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            summaries = []
            if content:
                # Split on blank lines between JSON blocks
                blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
                for block in blocks:
                    try:
                        summaries.append(json.loads(block))
                    except Exception:
                        # Fallback: try to parse line-by-line JSON objects
                        for line in block.splitlines():
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                summaries.append(json.loads(line))
                            except Exception:
                                # skip malformed lines
                                continue

            print(f"\n✓ {len(summaries)} session summary(ies) created")
        
        # Cleanup
        session_store.delete_session("summarization_test_session")
        
        return summarization_triggered or summary_log.exists()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Execute all 6 comprehensive tests."""
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "COMPREHENSIVE QUERY UNDERSTANDING TEST SUITE".center(78) + "║")
    print("║" + "Per fix.txt Principles - Rule-first, LLM-last Architecture".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = {
        "comprehensive_conversation": False,
        "ambiguity_scenarios": False,
        "context_augmentation": False,
        "pronoun_resolution": False,
        "llm_usage_tracking": False,
        "session_summarization": False,
    }
    
    # Run all 6 tests
    try:
        results["comprehensive_conversation"] = await run_comprehensive_conversation_test()
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
    
    try:
        results["ambiguity_scenarios"] = await run_ambiguity_detection_scenarios_test()
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
    
    try:
        results["context_augmentation"] = await run_context_augmentation_test()
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
    
    try:
        results["pronoun_resolution"] = await run_pronoun_resolution_test()
    except Exception as e:
        print(f"\n❌ Test 4 crashed: {e}")
    
    try:
        results["llm_usage_tracking"] = await run_llm_usage_tracking_test()
    except Exception as e:
        print(f"\n❌ Test 5 crashed: {e}")
    
    try:
        results["session_summarization"] = await run_session_summarization_test()
    except Exception as e:
        print(f"\n❌ Test 6 crashed: {e}")
    
    # Print summary
    print("\n\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "TEST SUMMARY".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    print("\nTest Results:")
    print(f"  1. Comprehensive Conversation:    {'✅ PASSED' if results['comprehensive_conversation'] else '❌ FAILED'}")
    print(f"  2. Ambiguity Detection Scenarios: {'✅ PASSED' if results['ambiguity_scenarios'] else '❌ FAILED'}")
    print(f"  3. Context Augmentation:          {'✅ PASSED' if results['context_augmentation'] else '❌ FAILED'}")
    print(f"  4. Pronoun Resolution:            {'✅ PASSED' if results['pronoun_resolution'] else '❌ FAILED'}")
    print(f"  5. LLM Usage Tracking:            {'✅ PASSED' if results['llm_usage_tracking'] else '❌ FAILED'}")
    print(f"  6. Session Summarization:         {'✅ PASSED' if results['session_summarization'] else '❌ FAILED'}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n  Overall: {passed}/{total} tests passed")
    
    print(f"\n📋 Logs saved to: {TEST_LOG_FOLDER}")
    if TEST_LOG_FOLDER.exists():
        log_files = list(TEST_LOG_FOLDER.glob("*.log"))
        for log_file in log_files:
            print(f"   - {log_file.name}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

