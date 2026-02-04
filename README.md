# Chat Bot with Memory

A production-ready conversational AI assistant with advanced memory management, session persistence, query understanding, and real-time deployment capability.

## Features

### Current Features ✅

- **Conversation Memory**: Persistent session storage with automatic context retrieval
- **Session Summarization**: Token-aware summarization when conversations exceed threshold (default 10K tokens)
- **Query Understanding**: 
  - Ambiguous query detection
  - Query rewriting for clarity
  - Context augmentation
  - Clarifying question generation
- **Multi-LLM Support**: 
  - Google Gemini (primary)
  - Ollama (local/self-hosted fallback)
- **Conversation Logging**: Automatic JSON Lines logging with metadata (timestamps, token counts, ambiguity flags)
- **Rich UI**: Streamlit-based web interface with markdown rendering, styled chat bubbles, orange theme
- **Comprehensive Testing**: 6 test suites covering core functionality
- **CI/CD Pipeline**: GitHub Actions with automated testing and deployment hooks

## App Interface

![Chat Bot UI](assets/UI.png)

*Streamlit-based web interface with rich markdown support, styled chat bubbles, and orange theme for an intuitive conversational experience.*

### Deployment ✅

- **Multi-Platform Ready**:
  - Railway (via Dockerfile + start.sh)
  - Render (FastAPI + Streamlit as separate services)
  - Heroku (via Procfile)
- **Production Server**: Gunicorn with Uvicorn workers
- **Environment Variables**: Port and concurrency auto-configuration
- **Docker Optimization**: Minimal images with build-time dependencies only

## Architecture

```
┌─────────────────────┐
│   Streamlit UI      │ ← Rich markdown, styled bubbles
│  (Optional Render)  │
└──────────┬──────────┘
           │
           │ HTTP/JSON
           ↓
┌──────────────────────┐
│   FastAPI Backend    │ ← Gunicorn + Uvicorn
│  (Railway/Render)    │
│                      │
│ ┌──────────────────┐ │
│ │  Chat Pipeline   │ │ ← Orchestrator
│ │  - Query Understand│
│ │  - Memory Manage │
│ │  - LLM Call      │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ LLM Clients      │ │ ← Gemini, Ollama
│ │ Token Counter    │ │
│ │ Summarizer       │ │
│ └──────────────────┘ │
└──────────┬───────────┘
           │
    ┌──────┴──────────────┬────────────┐
    ↓                     ↓            ↓
┌─────────────┐  ┌────────────────┐  ┌──────────────┐
│Session Store│  │LLM APIs        │  │Logging       │
│ (JSON Files)│  │(Gemini/Ollama) │  │ (JSON Lines) │
└─────────────┘  └────────────────┘  └──────────────┘
```

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (for containerized deployment)
- API Keys: Google Generative AI (Gemini)

### Installation

1. **Clone and Setup**
```bash
git clone <repo-url>
cd chat-bot-with-memory
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_API_KEY
# - OLLAMA_HOST (optional, for fallback)
```

3. **Run Locally**

**Option A: CLI Demo**
```bash
python cli_demo.py
```

**Option B: Streamlit UI**
```bash
streamlit run streamlit_app.py
```

### Docker Deployment (Local)

**API Service**
```bash
docker build -t chat-bot-api .
docker run -e PORT=8000 -e GOOGLE_API_KEY=your-key -p 8000:8000 chat-bot-api
```

**Streamlit UI**
```bash
docker build -f Dockerfile.streamlit -t chat-bot-ui .
docker run -e PORT=8501 -p 8501:8501 chat-bot-ui
```

## File Structure

```
chat-bot-with-memory/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # API endpoints
│   │   ├── chat.py
│   │   ├── docs.py          # Document upload (future)
│   │   └── auth.py          # Authentication (future)
│   ├── core/
│   │   ├── pipeline.py      # Main orchestrator
│   │   ├── config.py        # Configuration
│   │   ├── prompt_builder.py
│   │   └── token_counter.py
│   ├── llm/
│   │   ├── client.py        # Base LLM client
│   │   ├── gemini_client.py
│   │   ├── ollama_client.py
│   │   └── json_guard.py    # JSON parsing utilities
│   ├── memory/
│   │   ├── session_store.py # Session persistence
│   │   ├── schemas.py       # Data models
│   │   ├── summarizer.py    # Token-aware summarization
│   │   └── schemas.py
│   ├── query_understanding/
│   │   ├── ambiguity.py     # Detect ambiguous queries
│   │   ├── clarifier.py     # Generate clarifying questions
│   │   ├── context.py       # Context augmentation
│   │   ├── rewrite.py       # Query rewriting
│   │   └── schemas.py
│   ├── utils/
│   │   ├── logging.py       # ConversationLogger
│   │   └── __init__.py
│   └── __init__.py
├── tests/
│   ├── test_session_summarization.py
│   ├── test_ambiguous_query_detection.py
│   ├── test_query_refinement.py
│   ├── test_conversation_logging.py
│   ├── test_cli_demo.py
│   ├── test_streamlit_app.py
│   └── run_tests.py
├── logs/                    # Application logs
├── cli_demo.py              # CLI interface
├── streamlit_app.py         # Streamlit web UI
├── Dockerfile               # API service container
├── Dockerfile.streamlit     # Streamlit UI container
```

## Environment Variables

```bash
# LLM Configuration
GOOGLE_API_KEY=your-gemini-api-key
OLLAMA_HOST=http://localhost:11434  # For fallback

# Session Management
SESSION_TOKEN_THRESHOLD=10000        # Summarize at this token count
SESSION_STORAGE_TYPE=file            # or 'redis'
REDIS_URL=redis://localhost:6379     # If using Redis

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

## Testing
Run the test files
Run full test suite:
```bash
python tests/run_tests.py
```

Run specific test:
```bash
pytest tests/test_session_summarization.py -v
```

Test with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

**Session Management**
```bash
# View session info
python session_manager.py -i default_session

# Delete session
python session_manager.py -d default_session

# Delete all sessions
python session_manager.py -d
```

## License

MIT

## Support

For issues, questions, or feature requests, open a GitHub issue.

---

**Last Updated**: February 2026
**Current Version**: 1.0.0
**Status**: Production Ready (Core Features)
