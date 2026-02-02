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

### Deployment ✅

- **Multi-Platform Ready**:
  - Railway (via Dockerfile + start.sh)
  - Render (FastAPI + Streamlit as separate services)
  - Heroku (via Procfile)
- **Production Server**: Gunicorn with Uvicorn workers
- **Environment Variables**: Port and concurrency auto-configuration
- **Docker Optimization**: Minimal images with build-time dependencies only

### Future Roadmap 🚀

1. **[CI/CD Pipeline Enhancement]**
   - GitHub Actions workflows for Docker image builds and pushes
   - Multi-platform deployment automation
   - Smoke tests and performance benchmarks
   - Branch protection and secrets scanning

2. **[User Authentication]**
   - JWT-based authentication
   - User registration/login endpoints
   - Role-based access control (RBAC)
   - Optional OAuth2 (Google, GitHub) and Auth0 integration
   - Per-user conversation isolation

3. **[PDF Upload & Document Storage]**
   - PDF upload endpoint with validation
   - Text extraction from PDFs
   - S3/MinIO storage integration
   - Similarity search in documents
   - Vector embeddings (optional: Pinecone)
   - Document-based RAG (Retrieval Augmented Generation)

4. **[Agentic Web Search]**
   - LangChain agent integration
   - DuckDuckGo/SerpAPI web search
   - Uncertainty-based search triggering
   - Factual query detection
   - Search result caching
   - Source attribution

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

**Option C: FastAPI Backend**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## Deployment Guides

### Railway
1. Push repo to GitHub
2. Create new project on https://railway.app
3. Connect GitHub repo
4. Choose Docker deployment
5. Set environment variables (API keys)
6. Deploy — Railway auto-builds and runs start.sh

### Render
1. Create two Web Services:
   - **Service A (API)**: 
     - Connect repo, choose Docker
     - Set Dockerfile Path: `Dockerfile`
     - Set Start Command: `/app/start.sh`
   - **Service B (UI)**: 
     - Connect repo, choose Docker
     - Set Dockerfile Path: `Dockerfile.streamlit`
2. Set environment variables on each service
3. Deploy

### Heroku
```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku-cli
# or on Windows: choco install heroku-cli

# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set GOOGLE_API_KEY=your-key

# Push to Heroku
git push heroku main
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
├── docs/                    # Implementation guides
│   ├── 01_CI_CD_PIPELINE.md
│   ├── 02_AUTHENTICATION.md
│   ├── 03_MONITORING.md
│   ├── 04_PDF_UPLOAD_S3.md
│   ├── 05_AGENTIC_WEB_SEARCH.md
│   └── CONVERSATION_LOGGING.md
├── data/                    # Persistent data
│   ├── sessions/            # Session summaries (JSON)
│   └── conversations/       # Conversation logs (JSONL)
├── logs/                    # Application logs
├── cli_demo.py              # CLI interface
├── streamlit_app.py         # Streamlit web UI
├── Dockerfile               # API service container
├── Dockerfile.streamlit     # Streamlit UI container
├── start.sh                 # Production entrypoint (Gunicorn)
├── start_streamlit.sh       # Streamlit entrypoint
├── Procfile                 # Heroku process definition
├── runtime.txt              # Python runtime version (Heroku)
├── docker-compose.yml       # Development orchestration
├── requirements.txt         # Python dependencies
├── .dockerignore            # Docker build optimization
├── .env.example             # Environment template
├── .github/workflows/
│   └── tests.yml            # GitHub Actions CI/CD
└── README.md                # This file
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

# API
PORT=8000
WEB_CONCURRENCY=1                    # Gunicorn workers

# Future Features
ENABLE_AUTHENTICATION=false          # Enable auth (docs/02)
ENABLE_WEB_SEARCH=false              # Enable web search (docs/05)
ENABLE_DOCUMENT_UPLOAD=false         # Enable PDF upload (docs/04)

# Monitoring (docs/03)
ENABLE_PROMETHEUS=false
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
```

## API Endpoints

### Chat
```
POST /chat
Body: {
  "message": "Your question",
  "session_id": "session-123"
}

Response: {
  "response": "Assistant's answer",
  "session_id": "session-123",
  "token_count": 1234,
  "context_used": true
}
```

## Testing

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

## Security Checklist

- [ ] Store API keys securely (environment variables, not in code)
- [ ] Use HTTPS in production (Railway/Render provide this)
- [ ] Implement rate limiting on API endpoints (future)
- [ ] Validate and sanitize all user inputs
- [ ] Log access to sensitive operations
- [ ] Regularly update dependencies: `pip list --outdated`
- [ ] Enable authentication before production deployment
- [ ] Configure CORS appropriately
- [ ] Use private S3/MinIO buckets for documents

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>
```

### Gemini API Errors
- Verify `GOOGLE_API_KEY` is set correctly
- Check API quota on Google Cloud Console
- Ensure billing is enabled

### Streamlit Not Loading
- Verify `streamlit_app.py` exists
- Check port 8501 is accessible
- Review Streamlit logs: `streamlit run streamlit_app.py --logger.level=debug`

### Docker Build Failures
- Clear cache: `docker system prune -a`
- Check `requirements.txt` for invalid packages
- Verify `start.sh` has execute permissions

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test: `python tests/run_tests.py`
3. Commit: `git commit -am "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open PR on GitHub

## Implementation Roadmap Priority

1. **High Priority** (Next Sprint):
   - Authentication (enable multi-user support)
   - CI/CD automation (faster deployments)

2. **Medium Priority** (Following Sprint):
   - PDF upload & document storage
   - Web search for current information

## License

MIT

## Support

For issues, questions, or feature requests, open a GitHub issue.

---

**Last Updated**: February 2026
**Current Version**: 1.0.0
**Status**: Production Ready (Core Features)
