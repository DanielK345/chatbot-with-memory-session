"""Streamlit interface for Chat Assistant with Session Memory."""

import asyncio
import streamlit as st
from app.core.pipeline import ChatPipeline
from app.memory.session_store import SessionStore
from app.llm.client import LLMClient
from app.utils.logging import configure_logging_from_env, get_logger

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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f1f8e9;
        border-left: 4px solid #8bc34a;
    }
    .info-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
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
            max_context_tokens=st.session_state.get('max_context_tokens', 10000)
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
    # Header
    st.markdown('<h1 class="main-header">💬 Chat Assistant with Session Memory</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent chat with automatic session summarization and query understanding</p>', unsafe_allow_html=True)
    
    # Initialize pipeline
    if 'pipeline' not in st.session_state or 'llm_provider' not in st.session_state:
        with st.spinner("Initializing LLM client (Gemini default, Ollama fallback)..."):
            pipeline, provider = initialize_pipeline()
            if pipeline:
                st.session_state.pipeline = pipeline
                st.session_state.llm_provider = provider
                st.success(f"✓ Initialized with {provider.upper()} as LLM provider")
            else:
                st.stop()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Session ID
        session_id = st.text_input(
            "Session ID",
            value=st.session_state.get('session_id', 'default_session'),
            help="Unique identifier for this conversation session"
        )
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
        
        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message['role'] == 'user':
                    st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>You:</strong> {message['content']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="chat-message assistant-message">
                            <strong>Assistant:</strong> {message['content']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show query understanding if available
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
                    
                    # Show summarization info if triggered
                    if 'pipeline_metadata' in message:
                        metadata = message['pipeline_metadata']
                        if metadata.get('summarization_triggered'):
                            st.markdown("""
                                <div class="success-box">
                                    <strong>✅ Session Summarization Triggered!</strong><br>
                                    Context exceeded threshold and was summarized.
                                </div>
                            """, unsafe_allow_html=True)
        
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
