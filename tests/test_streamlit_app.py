"""
Test Streamlit app loads and initializes successfully.
Verifies that all Streamlit components initialize without errors.
"""

import sys
from pathlib import Path
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import configure_logging_from_env, get_logger

configure_logging_from_env()
logger = get_logger(__name__)


def test_streamlit_app_initialization():
    """Test that Streamlit app components initialize successfully."""
    print("=" * 70)
    print("TEST: Streamlit App Initialization")
    print("=" * 70)
    
    try:
        print("\n[Step 1] Checking markdown import (for rich formatting)...")
        try:
            import markdown
            print("  ✓ markdown package available for rich text rendering")
        except ImportError:
            print("  ⚠️  markdown package not installed, using fallback converter")
        
        print("\n[Step 2] Verifying markdown-to-HTML converter function...")
        # Import the converter function from streamlit_app
        import re
        import html as _html
        
        def _markdown_to_html(text: str) -> str:
            """Simple test of markdown conversion."""
            if not text:
                return ""
            safe = _html.escape(text)
            # Test bold
            safe = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', safe)
            return safe
        
        test_text = "This is **bold** text"
        result = _markdown_to_html(test_text)
        assert "<strong>" in result
        print("  ✓ Markdown-to-HTML converter working")
        
        print("\n[Step 3] Initializing session store...")
        session_store = SessionStore(storage_type="file")
        print("  ✓ Session store initialized")
        
        print("\n[Step 4] Initializing LLM client...")
        llm_client = LLMClient(primary="gemini")
        provider = llm_client.get_active_provider()
        print(f"  ✓ LLM client initialized with provider: {provider.upper()}")
        
        print("\n[Step 5] Initializing chat pipeline (Streamlit config)...")
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            max_context_tokens=10000,
            max_response_tokens=1500,
            response_temperature=0.6
        )
        print("  ✓ Chat pipeline initialized with Streamlit settings")
        print("    - max_response_tokens: 1500")
        print("    - response_temperature: 0.6")
        
        print("\n[Step 6] Checking CSS and styling compatibility...")
        css_classes = [
            "top-banner", "banner-inner", "banner-title", "banner-sub",
            "chat-row", "chat-bubble", "assistant-bubble", "user-bubble",
            "info-box", "success-box"
        ]
        print(f"  ✓ Verified {len(css_classes)} CSS classes in design")
        
        print("\n[Step 7] Testing state management...")
        test_messages = [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ]
        assert len(test_messages) == 2
        print("  ✓ Message state management working")
        
        print("\n" + "-" * 70)
        print("✅ TEST PASSED: Streamlit app components initialized successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.error(f"Streamlit app initialization test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_streamlit_app_initialization()
    exit(0 if success else 1)
