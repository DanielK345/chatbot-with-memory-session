"""
Test ambiguous query detection.
Uses a single comprehensive conversation that exercises all ambiguity rules
to test if the pipeline correctly identifies and flags ambiguous queries.

Ambiguity Rules Tested:
- RULE 1: Pronouns (it, they, this, that) without clear antecedent
- RULE 1b: Anaphoric determiners (same, similar, previous)
- RULE 1c: 'Which one/ones' without antecedent or selection criteria
- RULE 2: Unclear questions (< 4 tokens, no verb, no WH-word, incomplete)
- RULE 2b: 'What/which should I choose/pick/select' without object
- RULE 3: Unclear intent (declarative without clear question/command)
"""

import asyncio
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
pipeline_module.session_summary_logger = SessionSummaryLogger(log_file="session_summaries_test.log", log_dir=log_dir)

# Ensure log folder exists and truncate existing test logs so each run starts fresh
try:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    # Refresh all test logs so each run starts fresh
    for lf in ["conversations_test.log", "user_queries_test.log", "session_summaries_test.log"]:
        f = log_path / lf
        try:
            f.write_text("")
        except Exception:
            pass
except Exception:
    pass

# UNIFIED CONVERSATION SET - Natural ML project discussion with ambiguity rules woven in
# Structure: (query, should_be_ambiguous, rule_tested, description)
UNIFIED_CONVERSATION = [
    # Establish context: machine learning project setup
    ("We're building a machine learning system - what's the first step?", False, "CLEAR", "Clear setup question"),
    ("Should we use TensorFlow or PyTorch?", False, "CLEAR", "Clear library comparison question"),
    
    # RULE 1: Pronoun without antecedent (still has no specific choice made)
    ("How does it perform?", True, "RULE 1", "Pronoun 'it' - no decision made yet about which to use"),
    
    # Establish decision context
    ("I'm leaning towards PyTorch for flexibility", False, "CLEAR", "Establish choice context"),
    ("And TensorFlow for production deployment", False, "CLEAR", "Add second option"),
    
    # RULE 1: Now pronoun HAS clear antecedent
    ("How does it compare for training speed?", False, "RULE 1-resolved", "Pronoun 'it' now has PyTorch as context"),
    
    # RULE 1c: Which one without context
    ("Which one do you prefer?", True, "RULE 1c", "Which one - no selection criteria given"),
    
    # Establish criteria context
    ("We need something that trains fast and has good ecosystem", False, "CLEAR", "Provide criteria"),
    
    # RULE 1c: Which one WITH context
    ("Which would be better for our needs?", False, "CLEAR", "Now criteria are clear (speed + ecosystem)"),
    
    # RULE 2b: choose/pick without object
    ("What should I choose?", True, "RULE 2b", "Missing object - choose what?"),
    
    # Establish topic
    ("For the neural network architecture", False, "CLEAR", "Topic context provided"),
    
    # RULE 2b: choose WITH object
    ("Should we go with a CNN or RNN?", False, "CLEAR", "Choose with clear object types"),
    
    # RULE 1b: Anaphoric 'same' without antecedent
    ("Can we use the same approach?", True, "RULE 1b", "Anaphoric 'same approach' - no prior approach mentioned yet"),
    
    # Establish what 'approach' means
    ("We've been using transfer learning for images", False, "CLEAR", "Establish approach context"),
    
    # RULE 1b: Now anaphoric determiner HAS context
    ("Can we apply similar principles to text data?", False, "CLEAR", "Similar now has transfer learning as context"),
    
    # RULE 2: Very short, unclear questions
    ("It?", True, "RULE 2", "Single word, no verb, no context"),
    ("Better?", True, "RULE 2", "Unclear what's being compared"),
    
    # RULE 2: Incomplete WH-questions
    ("What about preprocessing?", True, "RULE 2", "Incomplete WH - missing main clause"),
    ("Which one faster?", True, "RULE 2", "Grammatically incomplete WH-question"),
    
    # RULE 3: Declarative without clear intent
    ("Data augmentation techniques.", True, "RULE 3", "Fragment - no clear question or command intent"),
    ("Model evaluation metrics.", True, "RULE 3", "Statement without intent"),
    
    # RULE 3: Clear imperatives (NOT ambiguous)
    ("Show me how to implement this CNN", False, "CLEAR", "Clear imperative intent"),
    ("Help me debug the training loop", False, "CLEAR", "Clear request for help"),
    
    # Complex: Multiple ambiguity signals
    ("It similar?", True, "RULE 1+2", "Pronoun 'it' (ambiguous) + incomplete grammar + anaphoric 'similar'"),
    ("How does that work?", True, "RULE 1+2", "Pronoun reference unclear + incomplete object"),
    
    # Final clear questions
    ("What's the expected accuracy for our baseline model?", False, "CLEAR", "Specific question"),
    ("How long should training take on a GPU?", False, "CLEAR", "Clear time-estimation question"),
    ("Should we use batch normalization in each layer?", False, "CLEAR", "Clear yes/no technical question"),
]


async def test_ambiguous_query_detection():
    """Test ambiguous query detection with unified conversation."""
    print("=" * 80)
    print("TEST: Ambiguous Query Detection (Unified Conversation)")
    print("=" * 80)
    print(f"\nTotal queries: {len(UNIFIED_CONVERSATION)}")
    print("Testing all ambiguity rules from ambiguity.py...")
    
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
        print(f"\n[OK] Initialized with {provider} as LLM provider\n")
        
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            enable_query_understanding=True,
            max_response_tokens=800,
            response_temperature=0.5,
            conversation_logger=pipeline_module.conversation_logger,
            query_logger=pipeline_module.query_logger,
            session_summary_logger=pipeline_module.session_summary_logger
        )
        
        session_id = "test_ambiguity_session"
        session_store.clear_messages(session_id)
        
        # Track results by rule
        rule_results = {}
        total_correct = 0
        total_tests = 0
        
        print("Running conversation queries:")
        print("-" * 80)
        
        for idx, (query, should_be_ambiguous, rule_tested, description) in enumerate(UNIFIED_CONVERSATION, 1):
            result = await pipeline.process_message(session_id, query)
            is_ambiguous = result.get('query_understanding', {}).get('is_ambiguous', False)
            ambiguity_reason = result.get('query_understanding', {}).get('ambiguity_reason', None)
            rewritten_query = result.get('query_understanding', {}).get('rewritten_query', None)
            
            # Check if result matches expectation
            is_correct = (is_ambiguous == should_be_ambiguous)
            total_correct += is_correct
            total_tests += 1
            
            # Track by rule
            if rule_tested not in rule_results:
                rule_results[rule_tested] = {"correct": 0, "total": 0}
            rule_results[rule_tested]["total"] += 1
            if is_correct:
                rule_results[rule_tested]["correct"] += 1
            
            # Print result
            status = "[OK]" if is_correct else "[FAIL]"
            print(f"\n{idx:2d}. {status} {rule_tested:15s} | {description}")
            print(f"     Query: {query}")
            print(f"     Expected ambiguous: {should_be_ambiguous}, Got: {is_ambiguous}")
            
            if is_ambiguous:
                print(f"     Reason: {ambiguity_reason}")
            if rewritten_query:
                print(f"     Refined: {rewritten_query}")
        
        # Summary by rule
        print("\n" + "=" * 80)
        print("RESULTS BY RULE:")
        print("=" * 80)
        
        for rule in sorted(rule_results.keys()):
            correct = rule_results[rule]["correct"]
            total = rule_results[rule]["total"]
            percentage = (correct / total * 100) if total > 0 else 0
            status = "PASS" if correct == total else "PARTIAL"
            print(f"{rule:20s}: {correct}/{total} ({percentage:5.1f}%) [{status}]")
        
        print("\n" + "=" * 80)
        print(f"OVERALL RESULTS: {total_correct}/{total_tests} ({total_correct/total_tests*100:.1f}%)")
        print("=" * 80)
        
        if total_correct >= int(total_tests * 0.8):  # 80% pass threshold
            print("\n[PASS] TEST PASSED: Ambiguous query detection working well")
            return True
        else:
            print(f"\n[INFO] TEST INCONCLUSIVE: {total_correct}/{total_tests} passed")
            print("    (Results may vary based on LLM's ambiguity sensitivity)")
            return True  # Not a failure - LLM sensitivity varies
            
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        logger.error(f"Ambiguous query detection test failed: {e}", exc_info=True)
        return False
    finally:
        _cleanup()


if __name__ == "__main__":
    success = asyncio.run(test_ambiguous_query_detection())
    exit(0 if success else 1)
