# Quickstart Guide: RAG Chatbot Backend

**Feature**: RAG Chatbot Backend
**Date**: 2025-12-30

## Prerequisites

- Python 3.12+
- uv (Python package manager) - [Install uv](https://github.com/astral-sh/uv)
- Qdrant Cloud account (free tier) - [Sign up](https://cloud.qdrant.io/)
- Cohere API key (free tier) - [Get API key](https://console.cohere.com/)
- OpenAI API key - [Get API key](https://platform.openai.com/api-keys)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/backend-physical-ai-and-humanoid-robotics.git
cd backend-physical-ai-and-humanoid-robotics
```

### 2. Install Dependencies with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Or install in development mode with dev dependencies
uv sync --dev
```

### 3. Set Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
API_RATE_LIMIT_REQUESTS=100
API_RATE_LIMIT_BURST=20

# API Keys (comma-separated list)
VALID_API_KEYS=dev-key-123,prod-key-456

# Cohere (Embeddings)
COHERE_API_KEY=your_cohere_api_key_here
COHERE_MODEL=embed-english-v3.0

# OpenAI (Generation)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# Qdrant (Vector Database)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION=rag-chunks

# Optional: Postgres (for persistent sessions)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Cache Settings
CACHE_TTL=3600  # 1 hour in seconds
```

### 4. Create Qdrant Collection

The application will create the collection automatically on startup, but you can also create it manually:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your_qdrant_api_key"
)

client.create_collection(
    collection_name="rag-chunks",
    vectors_config=VectorParams(
        size=1024,  # Cohere v3 dimensions
        distance=Distance.COSINE
    )
)
```

## Running the Application

### Development Mode (with auto-reload)

```bash
# Run with uv
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the provided script
./scripts/dev.sh
```

### Production Mode

```bash
# Run with uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Docker
docker build -t rag-chatbot .
docker run -p 8000:8000 --env-file .env rag-chatbot
```

## Verifying Installation

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "vector_db": "connected",
    "embedding_api": "connected",
    "generation_api": "connected"
  }
}
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Run All Tests

```bash
# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
uv run pytest tests/unit/test_chunking.py

# Run with verbose output
uv run pytest -v
```

### Run Test Category

```bash
# Unit tests only
uv run pytest tests/unit

# Integration tests only
uv run pytest tests/integration

# Contract tests only
uv run pytest tests/contract
```

## Common Workflows

### Ingest Documents

```bash
curl -X POST http://localhost:8000/v1/ingestion/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "folder_path": "/path/to/book/documentation"
  }'
```

Response:
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Ingestion started for folder /path/to/book/documentation"
}
```

Check ingestion status:
```bash
curl http://localhost:8000/v1/ingestion/status/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: dev-key-123"
```

### Start Conversation

```bash
curl -X POST http://localhost:8000/v1/chat/start \
  -H "X-API-Key: dev-key-123"
```

Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "created_at": "2025-12-30T10:30:00Z",
  "last_activity": "2025-12-30T10:30:00Z",
  "message_count": 0
}
```

### Ask Question

Without content selection (search all):
```bash
curl -X POST http://localhost:8000/v1/chat/send/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "question": "What is the main concept explained in Chapter 3?"
  }'
```

With chapter selection:
```bash
curl -X POST http://localhost:8000/v1/chat/send/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "question": "What is explained in Chapter 3?",
    "content_selection": {
      "selection_type": "chapter",
      "chapter": "Chapter 3"
    }
  }'
```

With page range selection:
```bash
curl -X POST http://localhost:8000/v1/chat/send/550e8400-e29b-41d4-a716-446655440001 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "question": "What is discussed on pages 45-60?",
    "content_selection": {
      "selection_type": "page_range",
      "page_start": 45,
      "page_end": 60
    }
  }'
```

## Project Structure

```
src/
├── ingestion/      # Document processing
├── rag/            # RAG pipeline (retrieval, generation)
├── chat/           # Session management
├── api/            # FastAPI routes
├── core/           # Shared utilities (config, embeddings, vector)
└── utils/          # Helpers (chunking, dedup, logging)

tests/
├── unit/          # Unit tests (80%+ coverage)
├── integration/    # API + DB tests
├── contract/       # External API tests
└── fixtures/       # Reusable test fixtures
```

## Development Tips

### Code Style

All code must follow constitution requirements:
- Full type hints (Python 3.12+ | syntax)
- Async-first design
- Pydantic models for validation
- No LangChain (use direct APIs)

### Running in Debug Mode

```bash
export LOG_LEVEL=DEBUG
uv run uvicorn app.main:app --reload
```

### Checking Code Coverage

```bash
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Linting

```bash
# Run ruff for fast linting
uv run ruff check src/

# Run mypy for type checking
uv run mypy src/
```

## Troubleshooting

### Qdrant Connection Failed

1. Verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
2. Check Qdrant cloud status: https://status.qdrant.io/
3. Ensure collection exists or allow auto-creation

### Cohere API Error

1. Verify `COHERE_API_KEY` in `.env`
2. Check API key permissions at: https://console.cohere.com/
3. Verify you're using a valid model: `embed-english-v3.0`

### OpenAI API Error

1. Verify `OPENAI_API_KEY` in `.env`
2. Check API key permissions and billing at: https://platform.openai.com/
3. Verify model name: `gpt-4o-mini`

### Import Errors

```bash
# Ensure dependencies are installed
uv sync

# Or reinstall
uv pip install --force-reinstall qdrant-client cohere openai pydantic
```

## Next Steps

1. Review `data-model.md` for entity definitions
2. Review `contracts/openapi.yaml` for API specification
3. Run `pytest tests/` to verify setup
4. Start development by running the server

## Resources

- [Constitution](../.specify/memory/constitution.md) - Project principles and standards
- [Data Model](data-model.md) - Entity definitions
- [API Contracts](contracts/) - OpenAPI specification
- [Feature Specification](spec.md) - User stories and requirements
