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

## Query Understanding Pipeline

### 🔄 New Workflow (v1.0+)

The query understanding pipeline processes every user query through 6 sequential steps to ensure clarity before LLM response generation:

```
┌─────────────────────────────────────────────────────────────────┐
│                    INCOMING USER QUERY                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
         ┌───────────────────────────────────────┐
         │  STEP 1: SPELLING CHECK               │
         │  ✓ Rule-based (NO LLM)               │
         │  ✓ Corrects typos & grammar          │
         │  ✓ Fast, deterministic               │
         └────────────┬────────────────────────┘
                      │
                      ↓
         ┌───────────────────────────────────────┐
         │  STEP 2: AMBIGUITY DETECTION          │
         │  ✓ Rule-first (heuristics)           │
         │  ✓ 6 ambiguity rules:               │
         │    - RULE 1: Pronouns (it, they)    │
         │    - RULE 1b: Anaphoric (same, like)│
         │    - RULE 1c: Which-one patterns    │
         │    - RULE 2: Very short questions   │
         │    - RULE 2b: Choose without object│
         │    - RULE 3: Unclear intent         │
         │  ✓ LLM fallback if uncertain        │
         │  ✓ Logs confidence score            │
         └────────────┬────────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
        CLEAR            AMBIGUOUS
           │                     │
           ↓                     ↓
      CONTINUE         ┌──────────────────────┐
                       │ RULE 3b: Is it still │
                       │ fixable with context?│
                       └──┬──────────────┬────┘
                          │              │
                       YES│              │NO
                          ↓              ↓
                      CONTINUE       UNCLEAR
                                         │
                                         ↓
                      ┌──────────────────────────┐
                      │ STEP 6b: Generate        │
                      │ Clarifying Questions     │
                      │ + Return instead of LLM  │
                      └──────────────────────────┘
           │
           ↓
         ┌───────────────────────────────────────┐
         │  STEP 3: ANSWERABILITY CHECK          │
         │  ✓ Similarity-based (NO LLM)         │
         │  ✓ Compares to known patterns       │
         │  ✓ Checks if answerable by system   │
         │  ✓ Falls back to clarifying Qs      │
         └────────────┬────────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
       ANSWERABLE         NOT ANSWERABLE
           │                     │
           ↓                     ↓
       CONTINUE          (Clarifying Qs)
                                 │
           │
           ↓
         ┌───────────────────────────────────────┐
         │  STEP 4: CONTEXT RETRIEVAL            │
         │  ✓ Selective memory augmentation     │
         │  ✓ Detects pronouns → get history   │
         │  ✓ Extracts key facts, decisions    │
         │  ✓ Aggressive filtering (no bloat)  │
         │  ✓ Max 3-turn lookback              │
         └────────────┬────────────────────────┘
                      │
                      ↓
         ┌───────────────────────────────────────┐
         │  STEP 5: QUERY REFINEMENT             │
         │  ✓ Pronoun detection (regex)         │
         │  ✓ Entity extraction from cache:     │
         │    - Last 3 queries (lightweight)    │
         │    - Capitalized word extraction    │
         │  ✓ LLM rewriting (Qwen2.5-1.5B):    │
         │    - "Replace [pronouns] with       │
         │      [entities] in query"           │
         │    - Max 20 tokens response         │
         │    - 2-3x faster than llama3.1      │
         └────────────┬────────────────────────┘
                      │
                      ↓
         ┌───────────────────────────────────────┐
         │  STEP 6: LLM RESPONSE GENERATION      │
         │  ✓ Build system + user prompt       │
         │  ✓ Include augmented context        │
         │  ✓ Generate response               │
         │  ✓ Log everything                   │
         └────────────┬────────────────────────┘
                      │
                      ↓
         ┌───────────────────────────────────────┐
         │        RESPONSE + METADATA            │
         │  ✓ Answer text                       │
         │  ✓ Query understanding results       │
         │  ✓ Token usage statistics            │
         │  ✓ Refinement details                │
         └───────────────────────────────────────┘
```

### Key Design Principles

| Principle | Implementation |
|-----------|-----------------|
| **Prefer Early Exits** | Spelling corrected → Fast success path |
| **Rule-First** | 6 heuristic rules before LLM for ambiguity |
| **Minimal LLM Usage** | Only use LLM when necessary (target <30%) |
| **Aggressive Filtering** | Context limited to recent messages + memory |
| **Lightweight Models** | Qwen2.5-1.5B for refinement (2-3x faster) |
| **Never Guess** | Clarifying questions instead of assumptions |
| **Fast Processing** | <500ms per query (without LLM delays) |

### Components

#### 1. **Spelling Checker** (`app/query_understanding/spelling_check.py`)
```python
# Corrects typos automatically
checker = SpellingChecker()
result = checker.check("whats the best libary for ML?")
# → "what's the best library for ML?"
```

#### 2. **Ambiguity Detector** (`app/query_understanding/ambiguity.py`)
```python
# Detects 6 types of ambiguous queries
detector = AmbiguityDetector(llm_client)
analysis = await detector.detect("How does it compare?", messages)
# → is_ambiguous=True, rule="RULE 1", reason="Pronoun 'it' without clear antecedent"
```

#### 3. **Query Refiner** (`app/query_understanding/query_refiner.py`)
```python
# Replaces pronouns with entities using lightweight LLM
refiner = QueryRefiner(llm_client)  # Uses Qwen2.5-1.5B by default
refined = await refiner.refine("How does it perform?")
# Cache: ["TensorFlow is fast", "PyTorch is flexible"]
# → "How does TensorFlow perform?" or "How does PyTorch perform?"
```

**Query Refinement Details:**
- **Pronoun Detection**: it, they, them, this, that, he, she
- **Entity Extraction**: From last 3 queries (lightweight cache)
- **LLM Rewriting**: Qwen2.5-1.5B model (1.5B params vs 8B for llama3.1)
- **Performance**: 2-3x faster than standard models
- **Fallback**: Auto-fallback to active LLM if Qwen unavailable

#### 4. **Context Augmenter** (`app/query_understanding/context.py`)
```python
# Intelligently retrieves session memory
augmenter = ContextAugmenter()
context, fields = augmenter.augment(
    query="How does it compare?",
    messages=messages,
    session_memory=memory,
    needed_fields=["key_facts", "decisions"]
)
```

#### 5. **Clarifying Question Generator** (`app/query_understanding/clarifier.py`)
```python
# Generates clarifying questions if query still unclear
clarifier = ClarifyingQuestionGenerator(llm_client)
questions = await clarifier.generate(
    "What should I choose?",  # Missing object
    messages=messages
)
# → ["Choose what? (library, algorithm, etc.)",
#    "What's your main priority? (speed, accuracy, etc.)",
#    "What's your use case?"]
```

---

## Logging System

The system generates **three types of detailed logs** for analysis:

### 📊 Log Types

| Log Type | File | Contents | Use Case |
|----------|------|----------|----------|
| **Conversation** | `conversations_*.log` | User-assistant pairs + metadata | Analyze conversations, user behavior |
| **User Query** | `user_queries_*.log` | Original → refined query + context | Debug ambiguity detection, refinement |
| **Session Summary** | `session_summaries_*.log` | Session facts, decisions, summary | Understand session evolution |

### 🔍 Log Structure

#### **Conversation Log** (`conversations_*.log`)
```json
{
  "timestamp": "2026-02-04T11:38:06.123456",
  "session_id": "session-123",
  "user": "How does it perform?",
  "assistant": "TensorFlow performs well for...",
  "metadata": {
    "is_answerable": true,
    "token_count": 1234,
    "summarization_triggered": false,
    "pipeline_metadata": {
      "spelling_check_used": false,
      "ambiguity_llm_used": true,
      "answerability_check_passed": true,
      "context_expanded": true,
      "refinement_applied": true,
      "llm_call_made": true
    },
    "llm_usage_percentage": "45.2%"
  }
}
```

#### **User Query Log** (`user_queries_*.log`)
```json
{
  "timestamp": "2026-02-04T11:38:06.123456",
  "session_id": "session-123",
  "original_query": "How does it perform?",
  "is_ambiguous": true,
  "rewritten_query": "How does TensorFlow perform?",
  "needed_context_from_memory": [
    "user_profile.prefs: [wants speed, flexibility]",
    "key_facts: [using TensorFlow in project]",
    "decisions: [chose TensorFlow over PyTorch]"
  ],
  "clarifying_questions": [],
  "final_augmented_context": "Recent discussion: TensorFlow chosen for project..."
}
```

#### **Session Summary Log** (`session_summaries_*.log`)
```json
{
  "timestamp": "2026-02-04T11:38:06.123456",
  "session_id": "session-123",
  "session_summary": {
    "user_profile": {
      "prefs": ["speed", "flexibility"],
      "constraints": ["budget: limited", "team: 2 engineers"]
    },
    "key_facts": [
      "Building ML system for production",
      "Team has PyTorch experience"
    ],
    "decisions": [
      "Chose TensorFlow for deployment",
      "Using transfer learning approach"
    ],
    "open_questions": [
      "How to optimize training speed?"
    ]
  },
  "message_range_summarized": {
    "from": 0,
    "to": 42
  }
}
```

---

## Running Tests & Generating Logs

### 📝 Test Scripts Location
```
tests/
├── test_ambiguous_query_detection.py    ← Ambiguity detection + all 6 rules
├── test_query_refinement.py              ← Query refinement with LLM
├── test_session_summarization.py         ← Session memory & summarization
├── test_conversation_logging.py          ← Conversation persistence
├── test_cli_demo.py                      ← CLI interface testing
├── test_streamlit_app.py                 ← Streamlit UI testing
└── run_tests.py                          ← Run all tests
```

### 🚀 Running Tests & Generating Logs

#### **1. Test Ambiguity Detection (All 6 Rules)**
```bash
# Run: Tests all 6 ambiguity rules with natural conversation
python tests/test_ambiguous_query_detection.py

# Generates logs:
# logs/ambiguous_query_detection/
# ├── conversations_test.log      (user-assistant pairs with metadata)
# ├── user_queries_test.log        (original + rewritten queries, ambiguity flags)
# └── session_summaries_test.log   (session memory evolution)

# Example output:
# [✓] Test: Ambiguous query detection
# [✓] Query 1: "We're building a machine learning system" → CLEAR (100% confidence)
# [✓] Query 3: "How does it perform?" → AMBIGUOUS (RULE 1: pronoun without antecedent)
# [✓] Query 7: "Which one do you prefer?" → AMBIGUOUS (RULE 1c: which-one without context)
# [✓] Query 23: "It?" → AMBIGUOUS (RULE 2: very short question)
# [✓] Overall: 24/28 queries correctly classified (85.7% accuracy)
```

#### **2. Test Query Refinement (Lightweight Model)**
```bash
# Run: Tests pronoun replacement with Qwen2.5-1.5B model
python tests/test_query_refinement.py

# Prerequisites: Ollama running with qwen2.5:1.5b pulled
# ollama pull qwen2.5:1.5b
# ollama serve

# Generates logs:
# logs/query_refinement/
# ├── conversations_test.log
# ├── user_queries_test.log        (shows rewritten_query field populated)
# └── session_summaries_test.log

# Example output:
# [Original] "How does it perform?"
# [Refined]  "How does TensorFlow perform?" ✓
# [Cache]    ["TensorFlow is fast", "PyTorch is flexible"]
```

#### **3. Test Session Summarization**
```bash
# Run: Tests token-aware summarization when context exceeds threshold
python tests/test_session_summarization.py

# Generates logs:
# logs/session_summarization/
# ├── conversations_test.log
# ├── user_queries_test.log
# └── session_summaries_test.log  (shows summarization_triggered + summary content)

# Example output:
# Token count: 2500
# [✓] Summarization triggered at 10000 tokens
# [✓] Extracted 5 key facts
# [✓] Tracked 3 decisions
# [✓] Found 2 open questions
```

#### **4. Run All Tests**
```bash
# Run entire test suite
python tests/run_tests.py

# Generates all logs across test directories:
logs/
├── ambiguous_query_detection/
│   ├── conversations_test.log
│   ├── user_queries_test.log
│   └── session_summaries_test.log
├── query_refinement/
│   ├── conversations_test.log
│   ├── user_queries_test.log
│   └── session_summaries_test.log
├── session_summarization/
│   ├── conversations_test.log
│   ├── user_queries_test.log
│   └── session_summaries_test.log
└── ...
```

### 📂 Analyzing Generated Logs

#### **View Conversation Logs**
```bash
# Pretty-print conversation log
python -c "
import json
with open('logs/ambiguous_query_detection/conversations_test.log') as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            print(f\"User: {data['user']}\")
            print(f\"Assistant: {data['assistant'][:100]}...\")
            print(f\"Ambiguity: {data['metadata']['pipeline_metadata']['ambiguity_llm_used']}\")
            print()
"
```

#### **View User Query Logs** 
```bash
# Show original → refined queries
python -c "
import json
with open('logs/ambiguous_query_detection/user_queries_test.log') as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            orig = data['original_query']
            refined = data['rewritten_query']
            if refined and refined != orig:
                print(f\"Original: {orig}\")
                print(f\"Refined:  {refined}\")
                print()
"
```

#### **View Session Summaries**
```bash
# Show session evolution
python -c "
import json
with open('logs/ambiguous_query_detection/session_summaries_test.log') as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            summary = data['session_summary']
            print(f\"Facts: {summary.get('key_facts', [])}\")
            print(f\"Decisions: {summary.get('decisions', [])}\")
            print(f\"Open Qs: {summary.get('open_questions', [])}\")
            print()
"
```

### 🔧 Log Directory Structure

```
logs/
├── ambiguous_query_detection/
│   ├── conversations_test.log       ← User-assistant conversations
│   ├── user_queries_test.log        ← Query analysis (ambiguity, refinement)
│   └── session_summaries_test.log   ← Memory & summaries
├── query_refinement/
│   ├── conversations_test.log
│   ├── user_queries_test.log        ← Shows rewritten_query field
│   └── session_summaries_test.log
├── session_summarization/
│   ├── conversations_test.log
│   ├── user_queries_test.log
│   └── session_summaries_test.log   ← Shows summarization triggers
├── app.log                          ← Application debug logs
└── [others]/
```

### 📊 Log Insights

**From Conversation Logs:**
- Track LLM call frequency (target: <30%)
- Monitor token usage per query
- Analyze response quality

**From User Query Logs:**
- See which queries are being refined
- Validate ambiguity detection accuracy
- Track context augmentation effectiveness

**From Session Summary Logs:**
- Monitor session memory evolution
- Identify when summarization triggers
- Validate fact extraction quality



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
