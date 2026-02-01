"""
Session Manager utility for chat assistant.
Provides commands to view and manage session information.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.memory.session_store import SessionStore
from app.utils.logging import get_logger

logger = get_logger(__name__)


def get_session_info(session_id: str):
    """
    Display comprehensive session information.
    
    Args:
        session_id: Session identifier
    """
    try:
        session_store = SessionStore(storage_type="file")
        messages = session_store.get_messages(session_id)
        summary = session_store.get_summary(session_id)
        
        print("=" * 70)
        print(f"SESSION INFORMATION: {session_id}")
        print("=" * 70)
        
        if not messages:
            print("\nℹ️  Session is empty - no messages found")
            print("=" * 70)
            return True
        
        # Message count
        print(f"\n📊 Message Count: {len(messages)}")
        
        # Token count
        from app.core.token_counter import TokenCounter
        token_counter = TokenCounter()
        token_count = token_counter.count_messages(messages)
        print(f"📈 Total Tokens: {token_count:,}")
        
        # Session summary
        if summary:
            print(f"\n📝 Session Summary:")
            print(f"   ✓ Summary exists (created at {summary.created_at})")
            print(f"   ✓ Summarized messages: {summary.message_range_summarized.from_index} to {summary.message_range_summarized.to_index}")
            
            session_summary = summary.session_summary
            
            if session_summary.user_profile.prefs or session_summary.user_profile.constraints:
                print(f"\n   👤 User Profile:")
                if session_summary.user_profile.prefs:
                    print(f"      Preferences:")
                    for pref in session_summary.user_profile.prefs[:3]:
                        print(f"        - {pref}")
                if session_summary.user_profile.constraints:
                    print(f"      Constraints:")
                    for constraint in session_summary.user_profile.constraints[:3]:
                        print(f"        - {constraint}")
            
            if session_summary.key_facts:
                print(f"\n   🔑 Key Facts:")
                for fact in session_summary.key_facts[:3]:
                    print(f"      - {fact}")
            
            if session_summary.decisions:
                print(f"\n   ✅ Decisions:")
                for decision in session_summary.decisions[:3]:
                    print(f"      - {decision}")
        else:
            print(f"\n📝 Session Summary: None (no summarization yet)")
        
        # Latest query and response
        print(f"\n💬 Latest Exchange:")
        
        # Find last user query and assistant response
        last_user_idx = None
        last_assistant_idx = None
        
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]['role'] == 'user' and last_user_idx is None:
                last_user_idx = i
            if messages[i]['role'] == 'assistant' and last_assistant_idx is None:
                last_assistant_idx = i
            if last_user_idx is not None and last_assistant_idx is not None:
                break
        
        if last_user_idx is not None:
            user_msg = messages[last_user_idx]['content']
            print(f"   User: {user_msg[:100]}{'...' if len(user_msg) > 100 else ''}")
        
        if last_assistant_idx is not None:
            assistant_msg = messages[last_assistant_idx]['content']
            print(f"   Assistant: {assistant_msg[:100]}{'...' if len(assistant_msg) > 100 else ''}")
        
        print("\n" + "=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error retrieving session info: {e}")
        logger.error(f"Failed to get session info: {e}", exc_info=True)
        return False


def delete_session(session_id: str = None):
    """
    Delete session information.
    
    Args:
        session_id: Specific session to delete, or None to delete all sessions
    """
    try:
        import shutil
        
        if session_id:
            # Delete specific session
            # 1. Delete summary file
            summary_path = Path("data/sessions") / f"{session_id}_summary.json"
            if summary_path.exists():
                summary_path.unlink()
            
            # 2. Remove session entries from JSONL
            jsonl_path = Path("data/conversations/session_log.jsonl")
            if jsonl_path.exists():
                lines = []
                with open(jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        if entry.get("session_id") != session_id:
                            lines.append(line)
                
                with open(jsonl_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            print(f"✓ Deleted session: {session_id}")
            logger.info(f"Session {session_id} deleted")
        else:
            # Delete all sessions
            storage_path = Path("data/sessions")
            if storage_path.exists():
                shutil.rmtree(storage_path)
                storage_path.mkdir(parents=True, exist_ok=True)
            
            # Clear JSONL file
            jsonl_path = Path("data/conversations/session_log.jsonl")
            if jsonl_path.exists():
                jsonl_path.unlink()
            
            print(f"✓ Deleted all sessions")
            logger.info(f"All sessions deleted")
        
        return True
    except Exception as e:
        print(f"❌ Error deleting session: {e}")
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        return False


def print_usage():
    """Print script usage information."""
    print("=" * 70)
    print("Session Manager - Chat Assistant Session Management")
    print("=" * 70)
    print("\nUsage: python session_manager.py [command] [options]")
    print("\nCommands:")
    print("  --info, -i [session_id]     Show session information")
    print("                              Shows: message count, token count,")
    print("                              summary (if available), latest query")
    print("  --delete, -d [session_id]   Delete session(s)")
    print("                              If session_id provided, delete that session")
    print("                              If no session_id, delete all sessions")
    print("  --help, -h                  Show this help message")
    print("\nExamples:")
    print("  python session_manager.py --info demo_session")
    print("  python session_manager.py -i default_session")
    print("  python session_manager.py --delete demo_session")
    print("  python session_manager.py -d")
    print("  python session_manager.py --help")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage chat assistant sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python session_manager.py --info demo_session
  python session_manager.py -i default_session
  python session_manager.py --delete demo_session
  python session_manager.py -d
        """
    )
    
    parser.add_argument(
        "--info", "-i",
        type=str,
        nargs="?",
        const="default_session",
        metavar="SESSION_ID",
        help="Show session information (default: 'default_session')"
    )
    parser.add_argument(
        "--delete", "-d",
        type=str,
        nargs="*",
        metavar="SESSION_ID",
        help="Delete session(s) (if no session_id, delete all)"
    )
    
    args = parser.parse_args()
    
    # Check if any command was provided
    has_command = (args.info is not None) or (args.delete is not None)
    
    if not has_command:
        print_usage()
        sys.exit(0)
    
    success = True
    
    if args.info is not None:
        success = get_session_info(args.info) and success
    
    if args.delete is not None:
        # args.delete is a list (due to nargs="*")
        if len(args.delete) == 0:
            # Delete all sessions
            print("\n⚠️  WARNING: This will delete ALL stored sessions!")
            confirm = input("Continue? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Cancelled.")
                sys.exit(1)
            success = delete_session(None) and success
        elif len(args.delete) == 1:
            # Delete specific session
            success = delete_session(args.delete[0]) and success
        else:
            print(f"❌ Error: Too many arguments for --delete command")
            print(f"Usage: python session_manager.py --delete [session_id]")
            sys.exit(1)
    
    sys.exit(0 if success else 1)
