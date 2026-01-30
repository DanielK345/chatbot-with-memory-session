# Chat Assistant with Session Memory

A production-ready chat assistant backend that implements automatic session summarization and intelligent query understanding. Built for the Vulcan Labs AI Engineer Intern take-home test.

## Features

### Core Functionality

1. **Session Memory via Summarization**
   - Automatically triggers when conversation context exceeds configurable threshold (~10k tokens)
   - Uses tokenizer-based token counting (tiktoken) for accurate measurement
   - Generates structured summaries with:
     - User profile (preferences, constraints)
     - Key facts
     - Decisions made
     - Open questions
     - Todos/action items
   - Sliding window approach: summarizes old messages while keeping recent context

2. **Query Understanding Pipeline**
   - **Ambiguity Detection**: Hybrid approach using heuristics + LLM classification
   - **Query Rewriting**: Clarifies ambiguous queries using conversation context
   - **Context Augmentation**: Selectively injects relevant session memory fields
   - **Clarifying Questions**: Generates 1-3 actionable questions when queries remain unclear

3. **Structured Outputs**
   - All outputs follow Pydantic v2 schemas
   - Schema-validated LLM responses with automatic retry
   - JSON extraction and validation utilities

## Architecture

```
User Input
   ↓
Session Store (messages + summaries)
   ↓
Context Size Monitor
   ↓ (if exceeded)
Session Summarizer → Structured Memory
   ↓
Query Understanding Pipeline
   ├─ Ambiguity Detection
   ├─ Query Rewrite
   ├─ Context Augmentation (memory + recent msgs)
   └─ Clarifying Question Generator
   ↓
Final Prompt Constructor
   ↓
LLM Response
```

## Tech Stack

- **Backend**: FastAPI (async, typed, clean API)
- **LLM**: **Gemini (default)** with **Ollama (fallback)**
  - Primary: Google Gemini (requires API key)
  - Fallback: Ollama (local/hosted, cost-free)
- **Models**: 
  - Gemini: gemini-pro, gemini-1.5-pro (configurable)
  - Ollama: llama3.1, qwen2.5, mistral (configurable)
- **Data Models**: Pydantic v2 (schema-first)
- **Token Counting**: tiktoken (accurate token counting)
- **Session Store**: Redis (optional) or file-based (default)
- **Persistence**: JSONL files for auditability
- **Containerization**: Docker + docker-compose

## Project Structure

```
chat-bot-with-memory/
│
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── api/
│   │   └── chat.py            # /chat endpoint
│   │
│   ├── core/
│   │   ├── pipeline.py        # Main orchestrator
│   │   ├── token_counter.py   # Token counting utilities
│   │   └── prompt_builder.py  # Prompt construction
│   │
│   ├── memory/
│   │   ├── session_store.py   # Redis/file abstraction
│   │   ├── summarizer.py      # Session summarization
│   │   └── schemas.py         # SessionSummary schema
│   │
│   ├── query_understanding/
│   │   ├── ambiguity.py       # Ambiguity detection
│   │   ├── rewrite.py         # Query rewriting
│   │   ├── context.py         # Context augmentation
│   │   ├── clarifier.py       # Clarifying questions
│   │   └── schemas.py         # QueryUnderstanding schema
│   │
│   └── llm/
│       ├── client.py          # Unified LLM client (Gemini + Ollama)
│       ├── gemini_client.py   # Gemini client wrapper
│       └── json_guard.py       # JSON validation/retry
│
├── data/
│   └── conversations/
│       ├── long_session.jsonl      # Demo: memory trigger
│       ├── ambiguous_queries.jsonl # Demo: ambiguous queries
│       └── mixed_flow.jsonl        # Demo: mixed scenarios
│
├── cli_demo.py                # CLI demo script
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites

1. **Python 3.11+**
2. **Ollama** installed and running
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull a model:
   ollama pull llama3.1
   # Or: ollama pull qwen2.5
   ```

3. **Redis** (optional, for Redis-based session storage)
   ```bash
   # Using Docker:
   docker run -d -p 6379:6379 redis:7-alpine
   ```

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd chat-bot-with-memory
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure LLM (choose one or both):**
   
   **Option A: Gemini (recommended)**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```
   
   **Option B: Ollama (fallback)**
   ```bash
   # Verify Ollama is running:
   curl http://localhost:11434/api/tags
   # Pull a model if needed:
   ollama pull llama3.1
   ```
   
   **Note**: The system will try Gemini first, then automatically fall back to Ollama if Gemini fails.

## How to Run

### Option 1: CLI Demo (Recommended for Testing)

Run the interactive CLI demo:

```bash
python cli_demo.py
```

This starts an interactive session where you can:
- Chat with the assistant
- See query understanding in action
- Trigger summarization with long conversations
- Load conversation logs: `load data/conversations/long_session.jsonl`

**Demo Flows:**

To see the two required demo flows:

```bash
python cli_demo.py flows
```

This demonstrates:
1. **Flow 1**: Session memory trigger (long conversation → summarization)
2. **Flow 2**: Ambiguous query handling (rewrite → context augmentation → clarifying questions)

### Option 2: FastAPI Server

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

**Endpoints:**
- `POST /api/chat` - Send a chat message
- `GET /api/sessions/{session_id}/messages` - Get session messages
- `GET /api/sessions/{session_id}/summary` - Get session summary
- `GET /docs` - Interactive API documentation

**Example request:**
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session",
    "message": "I need help with machine learning"
  }'
```

### Option 3: Docker Compose

```bash
docker-compose up --build
```

This starts:
- Chat assistant API on port 8000
- Redis on port 6379

**Note**: Ensure Ollama is running on your host machine (accessible at `host.docker.internal:11434`)

## Test Data

Three conversation logs are provided in `data/conversations/`:

1. **`long_session.jsonl`**: Long conversation that triggers summarization
   - 20+ messages about building a recommendation system
   - Demonstrates session memory extraction

2. **`ambiguous_queries.jsonl`**: Conversations with ambiguous queries
   - Examples: "Which one should I use?", "What should I do?", "It"
   - Shows query understanding pipeline in action

3. **`mixed_flow.jsonl`**: Mixed scenarios
   - Combination of normal and ambiguous queries
   - Tests both flows together

**Load a conversation:**
```bash
# In CLI demo:
load data/conversations/long_session.jsonl
```

## Configuration

### Environment Variables

Create a `.env` file (optional):

```env
# Gemini (primary, recommended)
GOOGLE_API_KEY=your_api_key_here

# Ollama (fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Session storage
REDIS_URL=redis://localhost:6379
SESSION_STORAGE_TYPE=file  # or "redis"
MAX_CONTEXT_TOKENS=10000
```

### Pipeline Parameters

In `app/core/pipeline.py`, you can configure:

- `max_context_tokens`: Threshold for triggering summarization (default: 10000)
- `keep_recent_messages`: Messages to keep after summarization (default: 5)

## High-Level Design Explanation

### Session Memory

When the conversation context exceeds the token threshold:

1. **Token Counting**: Uses tiktoken to accurately count tokens
2. **Range Selection**: Determines which messages to summarize (sliding window)
3. **Structured Summarization**: LLM extracts structured information into Pydantic schema
4. **Storage**: Saves summary to session store (Redis or file)
5. **Context Pruning**: Removes old messages, keeps recent ones for continuity

### Query Understanding

For each user query:

1. **Ambiguity Detection**:
   - Heuristic checks (short queries, pronouns, incomplete questions)
   - LLM-based classification with confidence scores

2. **Query Rewriting** (if ambiguous):
   - Uses conversation context to clarify intent
   - Maintains original query for debugging

3. **Context Augmentation**:
   - Selectively extracts relevant memory fields
   - Combines with recent messages
   - Avoids RAG-style dumping

4. **Clarifying Questions** (if still unclear):
   - Generates 1-3 actionable questions
   - Only if ambiguity persists after rewrite

### Schema-First Approach

All outputs are validated against Pydantic schemas:
- `SessionSummary`: Structured memory extraction
- `QueryUnderstanding`: Complete query analysis
- Automatic retry on schema violations
- JSON extraction from LLM responses

## Assumptions and Limitations

### Assumptions

1. **Gemini API key** is set (recommended) OR **Ollama is running locally** on port 11434 (fallback)
2. **Ollama model is pre-downloaded** if using Ollama (e.g., `ollama pull llama3.1`)
3. **File-based storage** is used by default (Redis optional)
4. **Single-threaded processing** per session (no concurrent requests)

### Limitations

1. **Token counting** uses GPT-3.5 tokenizer (may differ slightly for other models)
2. **Summarization** is triggered only on message send (not real-time)
3. **Context augmentation** uses simple keyword matching for field selection
4. **No conversation history** beyond session boundaries
5. **File-based storage** doesn't handle concurrent writes efficiently (use Redis for production)

### Future Improvements

- [x] Multi-model support with automatic fallback (Gemini + Ollama)
- [ ] Vector-based memory retrieval for better context selection
- [ ] Streaming responses for better UX
- [ ] Conversation history across sessions
- [ ] Metrics and observability (OpenTelemetry)
- [ ] LangGraph integration for state machine pipeline

## Testing the Demo Flows

### Flow 1: Session Memory Trigger

```bash
python cli_demo.py flows
```

Or manually:
1. Load `data/conversations/long_session.jsonl`
2. Continue conversation until token threshold is exceeded
3. Observe summarization trigger and structured summary output

### Flow 2: Ambiguous Query Handling

```bash
python cli_demo.py flows
```

Or manually:
1. Start a conversation with some context
2. Send an ambiguous query like "Which one should I use?"
3. Observe:
   - Ambiguity detection
   - Query rewriting
   - Context augmentation
   - Clarifying questions (if applicable)

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Model Not Found

```bash
# Pull a model
ollama pull llama3.1
# Or
ollama pull qwen2.5
```

### Redis Connection Issues

If using Redis, ensure it's running:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Or use file-based storage (default):
```python
session_store = SessionStore(storage_type="file")
```

## License

This project is created for the Vulcan Labs AI Engineer Intern take-home test.

## Author

Built with attention to:
- Clear pipeline design
- Structured, schema-first outputs
- Clean code organization
- Comprehensive documentation
- Test data for validation
