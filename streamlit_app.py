"""Streamlit interface for Chat Assistant with Session Memory."""

import asyncio
import re
import html as _html
import streamlit as st
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import configure_logging_from_env, get_logger

# Try to import the `markdown` package for robust conversion. If unavailable,
# we'll use a small fallback converter below.
try:
    import markdown as _md
    _HAS_MARKDOWN = True
except Exception:
    _HAS_MARKDOWN = False


def _markdown_to_html(text: str) -> str:
    """Convert a Markdown-like string to HTML.

    Attempts to use the `markdown` package if available; otherwise a small
    conservative fallback that handles headers, bold, italics, lists and
    simple tables.
    """
    if not text:
        return ""

    if _HAS_MARKDOWN:
        try:
            return _md.markdown(text, extensions=["extra", "tables"]) or ""
        except Exception:
            pass

    # Fallback conversion (simple and safe-ish)
    safe = _html.escape(text)

    # Headers: lines starting with #
    def _hdr(m):
        level = len(m.group(1))
        return f"<h{level}>{m.group(2).strip()}</h{level}>"
    safe = re.sub(r'^(#{1,6})\s+(.*)$', _hdr, safe, flags=re.MULTILINE)

    # Bold **text**
    safe = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', safe)
    # Italic *text* or _text_
    safe = re.sub(r'\*(.*?)\*', r'<em>\1</em>', safe)
    safe = re.sub(r'_(.*?)_', r'<em>\1</em>', safe)

    # Code fences ``` ``` -> <pre><code>
    safe = re.sub(r'```\s*\n(.*?)\n```', lambda m: f"<pre><code>{m.group(1)}</code></pre>", safe, flags=re.S)

    # Unordered lists
    lines = safe.splitlines()
    out_lines = []
    in_ul = False
    for ln in lines:
        if re.match(r'^[\-\*]\s+', ln):
            if not in_ul:
                out_lines.append('<ul>')
                in_ul = True
            li_content = re.sub(r'^[\-\*]\s+', '', ln)
            out_lines.append(f"<li>{li_content}</li>")
        else:
            if in_ul:
                out_lines.append('</ul>')
                in_ul = False
            out_lines.append(ln)
    if in_ul:
        out_lines.append('</ul>')

    safe = '\n'.join(out_lines)

    # Simple table detection: lines containing | with header separator
    if '|' in safe:
        parts = [p for p in safe.split('\n') if '|' in p]
        if len(parts) >= 2 and re.match(r'^\s*\|?\s*[:\-]+', parts[1]):
            # crude table builder
            rows = [row.strip() for row in parts if row.strip()]
            cols = [c.strip() for c in rows[0].strip('|').split('|')]
            html_tbl = ['<table>']
            # header
            html_tbl.append('<thead><tr>' + ''.join([f'<th>{_html.escape(c)}</th>' for c in cols]) + '</tr></thead>')
            # body
            html_tbl.append('<tbody>')
            for r in rows[2:]:
                cells = [c.strip() for c in r.strip('|').split('|')]
                html_tbl.append('<tr>' + ''.join([f'<td>{_html.escape(c)}</td>' for c in cells]) + '</tr>')
            html_tbl.append('</tbody></table>')
            safe = '\n'.join([l for l in lines if '|' not in l]) + '\n' + '\n'.join(html_tbl)

    # Paragraphs
    paragraphs = [p for p in safe.split('\n\n') if p.strip()]
    safe = ''.join([f'<p>{p}</p>' for p in paragraphs])

    return safe

# Configure logging
configure_logging_from_env()
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Chat Assistant with Session Memory",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    /* Top banner */
    .top-banner {
        background: linear-gradient(90deg, #ff8a00 0%, #ff6a00 100%);
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 18px;
        color: white;
    }
    .banner-inner { max-width: 1100px; margin: 0 auto; }
    .banner-title {
        font-size: 1.8rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .banner-sub { font-size: 0.95rem; opacity: 0.95; margin-top: 6px; }

    /* Chat area */
    .chat-row { display: flex; margin: 8px 4px; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }

    .chat-bubble {
        max-width: 72%;
        padding: 12px 16px;
        border-radius: 18px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        line-height: 1.4;
        font-size: 0.98rem;
    }

    .assistant-bubble {
        background: #f3f4f6; /* light gray */
        color: #0f172a;
        border: 1px solid rgba(15,23,42,0.04);
        border-top-left-radius: 6px;
    }
    
    /* Headers in responses - muted colors for readability */
    .assistant-bubble h1, 
    .assistant-bubble h2, 
    .assistant-bubble h3,
    .assistant-bubble h4,
    .assistant-bubble h5,
    .assistant-bubble h6 {
        color: #1e293b !important;
        font-weight: 600;
        margin: 12px 0 8px 0;
        line-height: 1.3;
    }
    
    .assistant-bubble h1 { font-size: 1.4rem; }
    .assistant-bubble h2 { font-size: 1.2rem; }
    .assistant-bubble h3 { font-size: 1.05rem; }
    .assistant-bubble h4, 
    .assistant-bubble h5, 
    .assistant-bubble h6 { font-size: 0.95rem; }

    .user-bubble {
        background: #ff8a00; /* orange */
        color: white;
        border-top-right-radius: 6px;
    }

    /* Small orange pill for user short messages */
    .user-bubble.small { padding: 8px 12px; border-radius: 14px; }

    /* Info / status boxes */
    .info-box { background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; }
    .success-box { background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; }

    /* Input area adjustments */
    .stButton>button {
        background: #ff8a00 !important;
        border-radius: 8px !important;
        color: white !important;
        border: none !important;
    }

    .stTextInput>div>div>input {
        border: 2px solid #ff8a00 !important;
        border-radius: 14px !important;
        padding: 12px !important;
    }

    /* Footer caption alignment */
    .streamlit-expanderHeader { }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_pipeline():
    """Initialize the chat pipeline (cached for performance)."""
    try:
        session_store = SessionStore(storage_type="file")
        llm_client = LLMClient(primary="gemini")
        pipeline = ChatPipeline(
            session_store,
            llm_client,
            max_context_tokens=st.session_state.get('max_context_tokens', 10000),
            max_response_tokens=1500,
            response_temperature=0.6
        )
        return pipeline, llm_client.get_active_provider()
    except Exception as e:
        st.error(f"Failed to initialize pipeline: {e}")
        return None, None


def process_message_async(pipeline, session_id, user_query):
    """Wrapper to run async pipeline processing."""
    return asyncio.run(pipeline.process_message(session_id, user_query))


def main():
    """Main Streamlit application."""
    # Header / top banner
    st.markdown(
            '''
            <div class="top-banner">
                <div class="banner-inner">
                    <div class="banner-title">🤖 AI Chatbot</div>
                    <div class="banner-sub">Your reliable AI assistant</div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
    )

    # ---- SESSION STATE INITIALIZATION ----
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None

    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = None

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'session_id' not in st.session_state:
        st.session_state.session_id = "default_session"

    if 'max_context_tokens' not in st.session_state:
        st.session_state.max_context_tokens = 10000
    
    # Initialize pipeline
    if not st.session_state.pipeline or not st.session_state.llm_provider:
        with st.spinner("Initializing LLM client (Gemini default, Ollama fallback)..."):
            pipeline, provider = initialize_pipeline()
            if pipeline:
                st.session_state.pipeline = pipeline
                st.session_state.llm_provider = provider
                st.success(f"✓ Initialized with {provider.upper()} as LLM provider")
            else:
                st.stop()
    
    # Load persisted messages from session store (restores chat history after refresh)
    if st.session_state.pipeline and not st.session_state.messages:
        persisted_messages = st.session_state.pipeline.session_store.get_messages(st.session_state.session_id)
        if persisted_messages:
            st.session_state.messages = persisted_messages
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Session ID
        session_id = st.text_input(
            "Session ID",
            value=st.session_state.get('session_id', 'default_session'),
            help="Unique identifier for this conversation session"
        )
        
        # Load messages from new session if ID changed
        if session_id != st.session_state.session_id:
            st.session_state.session_id = session_id
            persisted_messages = st.session_state.pipeline.session_store.get_messages(session_id)
            st.session_state.messages = persisted_messages if persisted_messages else []
            st.rerun()
        else:
            st.session_state.session_id = session_id
        
        # Max context tokens
        max_tokens = st.slider(
            "Max Context Tokens",
            min_value=1000,
            max_value=20000,
            value=st.session_state.get('max_context_tokens', 10000),
            step=1000,
            help="Threshold for triggering session summarization"
        )
        if max_tokens != st.session_state.get('max_context_tokens', 10000):
            st.session_state.max_context_tokens = max_tokens
            st.session_state.pipeline.max_context_tokens = max_tokens
        
        st.divider()
        
        # Session info
        st.subheader("📊 Session Info")
        if st.session_state.pipeline:
            messages = st.session_state.pipeline.session_store.get_messages(session_id)
            st.metric("Messages", len(messages))
            
            if messages:
                token_count = st.session_state.pipeline.token_counter.count_messages(messages)
                st.metric("Token Count", f"{token_count:,}")
                st.metric("Threshold", f"{max_tokens:,}")
                
                # Progress bar
                progress = min(token_count / max_tokens, 1.0)
                st.progress(progress)
                if token_count > max_tokens * 0.8:
                    st.warning("⚠️ Approaching summarization threshold")
        
        st.divider()
        
        # Actions
        st.subheader("🔧 Actions")
        if st.button("🗑️ Clear Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pipeline.session_store.clear_messages(session_id)
            st.rerun()
        
        if st.button("📥 Load Conversation", use_container_width=True):
            st.info("Use the file uploader below to load a conversation log")
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💭 Chat")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message['role'] == 'user':
                    # Right-aligned user bubble
                                        user_text = _html.escape(message['content'] or "")
                                        st.markdown(
                                                f"""
                                                <div class="chat-row user">
                                                    <div class="chat-bubble user-bubble">{user_text}</div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True
                                        )
                else:
                    # Left-aligned assistant bubble
                    content = message['content'] or ""
                    # Detect markdown-like content (headers, bold, lists, tables, code fences)
                    md_markers = ['\n#', '\n-', '\n*', '**', '```', '|', '# ']
                    looks_like_md = any(m in content for m in md_markers) or (len(content) > 300)

                    if looks_like_md:
                        html_content = _markdown_to_html(content)
                    else:
                        # Escape and preserve simple newlines
                        html_content = _html.escape(content).replace('\n', '<br/>')

                    st.markdown(
                        f"""
                        <div class="chat-row assistant">
                          <div class="chat-bubble assistant-bubble">{html_content}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Show query understanding if available (preserve existing behavior)
                    if 'query_understanding' in message:
                        q_understanding = message['query_understanding']
                        if q_understanding.get('is_ambiguous'):
                            with st.expander("🔍 Query Understanding", expanded=False):
                                st.info(f"**Ambiguous Query Detected**\n\n{q_understanding.get('ambiguity_reason', 'Query was ambiguous')}")
                                if q_understanding.get('rewritten_query'):
                                    st.success(f"**Rewritten:** {q_understanding['rewritten_query']}")
                                if q_understanding.get('clarifying_questions'):
                                    st.warning("**Clarifying Questions:**")
                                    for q in q_understanding['clarifying_questions']:
                                        st.write(f"- {q}")

                    # Show summarization info if triggered (preserve existing behavior)
                    if 'pipeline_metadata' in message:
                        metadata = message['pipeline_metadata']
                        if metadata.get('summarization_triggered'):
                            st.markdown(
                                """
                                <div class="success-box">
                                    <strong>✅ Session Summarization Triggered!</strong><br>
                                    Context exceeded threshold and was summarized.
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to history
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input
            })
            
            # Process message
            with st.spinner("Processing..."):
                try:
                    result = process_message_async(
                        st.session_state.pipeline,
                        session_id,
                        user_input
                    )
                    
                    # Add assistant response to history
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': result['response'],
                        'query_understanding': result.get('query_understanding'),
                        'pipeline_metadata': result.get('pipeline_metadata'),
                        'session_memory': result.get('session_memory')
                    })
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing message: {e}")
                    logger.error(f"Error in Streamlit app: {e}", exc_info=True)
    
    with col2:
        st.subheader("📋 Session Memory")
        
        # Get session summary if available
        if st.session_state.pipeline:
            summary = st.session_state.pipeline.session_store.get_summary(session_id)
            
            if summary:
                st.markdown("### Summary")
                
                # User Profile
                if summary.session_summary.user_profile.prefs or summary.session_summary.user_profile.constraints:
                    with st.expander("👤 User Profile", expanded=True):
                        if summary.session_summary.user_profile.prefs:
                            st.write("**Preferences:**")
                            for pref in summary.session_summary.user_profile.prefs:
                                st.write(f"- {pref}")
                        if summary.session_summary.user_profile.constraints:
                            st.write("**Constraints:**")
                            for constraint in summary.session_summary.user_profile.constraints:
                                st.write(f"- {constraint}")
                
                # Key Facts
                if summary.session_summary.key_facts:
                    with st.expander("🔑 Key Facts", expanded=False):
                        for fact in summary.session_summary.key_facts:
                            st.write(f"- {fact}")
                
                # Decisions
                if summary.session_summary.decisions:
                    with st.expander("✅ Decisions", expanded=False):
                        for decision in summary.session_summary.decisions:
                            st.write(f"- {decision}")
                
                # Open Questions
                if summary.session_summary.open_questions:
                    with st.expander("❓ Open Questions", expanded=False):
                        for question in summary.session_summary.open_questions:
                            st.write(f"- {question}")
                
                # Todos
                if summary.session_summary.todos:
                    with st.expander("📝 Todos", expanded=False):
                        for todo in summary.session_summary.todos:
                            st.write(f"- {todo}")
                
                st.caption(f"Summarized messages: {summary.message_range_summarized.from_index} to {summary.message_range_summarized.to_index}")
            else:
                st.info("No session summary available yet. Continue the conversation to trigger summarization.")
        
        st.divider()
        
        # Pipeline metadata from last message
        if st.session_state.messages:
            last_message = st.session_state.messages[-1]
            if last_message.get('role') == 'assistant' and 'pipeline_metadata' in last_message:
                metadata = last_message['pipeline_metadata']
                st.subheader("🔧 Pipeline Metadata")
                
                st.metric("Token Count", f"{metadata.get('token_count', 0):,}")
                st.metric("Summarization", "✅ Triggered" if metadata.get('summarization_triggered') else "❌ Not triggered")
                
                if metadata.get('fields_used_from_memory'):
                    st.write("**Memory Fields Used:**")
                    for field in metadata['fields_used_from_memory']:
                        st.code(field)
    
    # Footer
    st.divider()
    st.caption(f"Powered by {st.session_state.get('llm_provider', 'Unknown').upper()} | Session: {session_id}")


if __name__ == "__main__":
    main()
