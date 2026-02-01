"""
Test script demonstrating conversation logging functionality.
Shows how the ConversationLogger records user-assistant exchanges.
"""

import json
from pathlib import Path
from app.utils.logging import ConversationLogger

def test_conversation_logging():
    """Test the conversation logging functionality."""
    
    # Create conversation logger
    logger = ConversationLogger(log_file="conversations.log", log_dir="logs")
    
    print("=" * 60)
    print("Testing Conversation Logger")
    print("=" * 60)
    
    # Test 1: Log a complete exchange
    print("\n[Test 1] Logging a complete conversation exchange...")
    logger.log_exchange(
        session_id="session_001",
        user_message="What is the capital of France?",
        assistant_response="The capital of France is Paris.",
        metadata={
            "is_ambiguous": False,
            "token_count": 45,
            "summarization_triggered": False,
            "memory_fields_used": []
        }
    )
    print("✓ Exchange logged successfully")
    
    # Test 2: Log another exchange with different metadata
    print("\n[Test 2] Logging another exchange with metadata...")
    logger.log_exchange(
        session_id="session_001",
        user_message="What about Germany?",
        assistant_response="The capital of Germany is Berlin.",
        metadata={
            "is_ambiguous": False,
            "token_count": 52,
            "summarization_triggered": False,
            "memory_fields_used": ["previous_query"]
        }
    )
    print("✓ Exchange logged successfully")
    
    # Test 3: Log user message only
    print("\n[Test 3] Logging user message only...")
    logger.log_user_message(
        session_id="session_002",
        user_message="Tell me about Python programming"
    )
    print("✓ User message logged successfully")
    
    # Test 4: Log assistant response only
    print("\n[Test 4] Logging assistant response only...")
    logger.log_assistant_response(
        session_id="session_002",
        response="Python is a versatile programming language known for its simplicity and readability."
    )
    print("✓ Assistant response logged successfully")
    
    # Test 5: Display the logged conversations
    print("\n[Test 5] Reading logged conversations from file...")
    log_file = Path("logs/conversations.log")
    
    if log_file.exists():
        print(f"\n✓ Log file exists at: {log_file}")
        print(f"\nContents of {log_file.name}:")
        print("-" * 60)
        
        with open(log_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                entry = json.loads(line)
                print(f"\nEntry {i}:")
                print(json.dumps(entry, indent=2, ensure_ascii=False))
        
        print("\n" + "-" * 60)
        print("✓ All entries displayed successfully")
    else:
        print(f"✗ Log file not found at {log_file}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_conversation_logging()
