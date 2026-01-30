"""CLI demo for chat assistant."""

import asyncio
import json
import sys
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient


async def interactive_demo():
    """Run interactive CLI demo."""
    print("=" * 60)
    print("Chat Assistant with Session Memory - CLI Demo")
    print("=" * 60)
    print("\nThis demo shows:")
    print("1. Session memory via automatic summarization")
    print("2. Query understanding (ambiguity detection, rewrite, context augmentation)")
    print("\nType 'exit' to quit, 'load <file>' to load a conversation log")
    print("=" * 60)
    
    # Initialize pipeline with unified LLM client (Gemini default, Ollama fallback)
    print("\nInitializing LLM client (Gemini default, Ollama fallback)...")
    try:
        session_store = SessionStore(storage_type="file")
        llm_client = LLMClient(primary="gemini")
        print(f"✓ Using {llm_client.get_active_provider().upper()} as LLM provider")
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            max_context_tokens=5000  # Lower threshold for demo
        )
    except Exception as e:
        print(f"\n✗ Failed to initialize LLM client: {e}")
        sys.exit(1)
    
    session_id = "demo_session"
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            if user_input.lower().startswith("load "):
                filepath = user_input[5:].strip()
                await load_conversation(filepath, pipeline, session_id)
                continue
            
            # Process message
            print("\n[Processing...]")
            result = await pipeline.process_message(session_id, user_input)
            
            # Display response
            print(f"\nAssistant: {result['response']}")
            
            # Display query understanding if ambiguous
            q_understanding = result['query_understanding']
            if q_understanding['is_ambiguous']:
                print("\n[Query Understanding]")
                print(f"  Ambiguous: Yes")
                if q_understanding.get('rewritten_query'):
                    print(f"  Rewritten: {q_understanding['rewritten_query']}")
                if q_understanding.get('clarifying_questions'):
                    print(f"  Clarifying questions:")
                    for q in q_understanding['clarifying_questions']:
                        print(f"    - {q}")
            
            # Display pipeline metadata
            metadata = result['pipeline_metadata']
            if metadata.get('summarization_triggered'):
                print(f"\n[Pipeline] Summarization triggered! (tokens: {metadata['token_count']})")
                if result.get('session_memory'):
                    print("  Session summary created.")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


async def load_conversation(filepath: str, pipeline: ChatPipeline, session_id: str):
    """Load a conversation from JSONL file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            messages = []
            for line in f:
                entry = json.loads(line.strip())
                if 'message' in entry:
                    msg = entry['message']
                    pipeline.session_store.add_message(
                        session_id,
                        msg.get('role', 'user'),
                        msg.get('content', '')
                    )
                    messages.append(msg)
            
            print(f"\nLoaded {len(messages)} messages from {filepath}")
            print("You can now continue the conversation or trigger summarization with more messages.")
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except Exception as e:
        print(f"Error loading conversation: {e}")


async def demo_flows():
    """Demonstrate the two required flows."""
    print("=" * 60)
    print("Demo Flow 1: Session Memory Trigger")
    print("=" * 60)
    
    print("\nInitializing LLM client (Gemini default, Ollama fallback)...")
    try:
        session_store = SessionStore(storage_type="file")
        llm_client = LLMClient(primary="gemini")
        print(f"✓ Using {llm_client.get_active_provider().upper()} as LLM provider")
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            max_context_tokens=3000  # Low threshold for demo
        )
    except Exception as e:
        print(f"\n✗ Failed to initialize LLM client: {e}")
        sys.exit(1)
    
    session_id = "demo_flow1"
    
    # Simulate a long conversation
    print("\nSimulating a long conversation to trigger summarization...")
    messages = [
        "I'm interested in learning about machine learning.",
        "What are the main types of machine learning?",
        "Can you explain supervised learning in detail?",
        "What about unsupervised learning?",
        "I prefer Python for ML projects.",
        "What libraries would you recommend?",
        "I'm working on a classification problem.",
        "My dataset has 10,000 samples.",
        "I want to use neural networks.",
        "What architecture would work best?",
        "I'm concerned about overfitting.",
        "How can I prevent that?",
        "I'll use cross-validation.",
        "What's a good learning rate?",
        "I'll start with 0.001.",
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n[{i}/{len(messages)}] User: {msg}")
        result = await pipeline.process_message(session_id, msg)
        print(f"Assistant: {result['response'][:100]}...")
        
        if result['pipeline_metadata'].get('summarization_triggered'):
            print("\n✅ SUMMARIZATION TRIGGERED!")
            if result.get('session_memory'):
                summary = result['session_memory']['session_summary']
                print(f"  Key facts: {summary.get('key_facts', [])[:3]}")
                print(f"  Decisions: {summary.get('decisions', [])[:3]}")
            break
    
    print("\n" + "=" * 60)
    print("Demo Flow 2: Ambiguous Query Handling")
    print("=" * 60)
    
    session_id2 = "demo_flow2"
    
    # Set up some context
    await pipeline.process_message(session_id2, "I'm comparing different LLM models for my project.")
    await pipeline.process_message(session_id2, "I need something that's cost-effective and fast.")
    
    # Ambiguous query
    ambiguous_query = "Which one should I use?"
    print(f"\nUser: {ambiguous_query}")
    result = await pipeline.process_message(session_id2, ambiguous_query)
    
    print(f"\nAssistant: {result['response']}")
    q_understanding = result['query_understanding']
    print(f"\n✅ Query Understanding:")
    print(f"  Is ambiguous: {q_understanding['is_ambiguous']}")
    if q_understanding.get('rewritten_query'):
        print(f"  Rewritten: {q_understanding['rewritten_query']}")
    if q_understanding.get('clarifying_questions'):
        print(f"  Clarifying questions:")
        for q in q_understanding['clarifying_questions']:
            print(f"    - {q}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "flows":
        asyncio.run(demo_flows())
    else:
        asyncio.run(interactive_demo())
