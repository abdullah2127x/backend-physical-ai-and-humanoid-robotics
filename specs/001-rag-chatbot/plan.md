  # Implementation Plan: RAG Chatbot Backend

  **Branch**: `001-rag-chatbot` | **Date**: 2025-12-30 | **Spec**: [spec.md](./spec.md)
  **Input**: Feature specification from `/specs/001-rag-chatbot/spec.md`

  ## Summary

  Implement a RAG (Retrieval-Augmented Generation) chatbot backend that enables users to ask questions about book content. The system ingests documentation folders, creates searchable vector embeddings, and provides contextual answers with conversation history management. Answers must distinguish between book-based content and general knowledge with explicit disclaimers when applicable.

  ## Technical Context

  **Language/Version**: Python 3.12+ (managed with uv)
  **Primary Dependencies**: FastAPI, Uvicorn, qdrant-client, cohere, litellm (for LiteLLM/OpenRouter), Pydantic
  **Storage**:
      - Vector Database: Qdrant Cloud Free Tier (embeddings)
      - Optional: Neon Serverless Postgres (chat history, metadata)
  **Testing**: pytest with async support, test fixtures, contract tests
  **Target Platform**: Linux server (containerizable)
  **Project Type**: web (FastAPI backend)
  **Performance Goals**:
      - API response: <200ms p95 (excluding LLM generation)
      - Ingestion: <2 minutes for 1000 files
      - Handle 100 concurrent requests
  **Constraints**:
      - Max 10MB per document, PDF/TXT/MD only
      - 200-500 token chunks with 50-token overlap
      - Max 1000 characters per query
      - Memory <100MB per request
  **Scale/Scope**:
      - Support 50+ concurrent users
      - 20+ message exchanges per session
      - Process 1000+ documents

  ## Constitution Check

  *GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

  ### Core Principles Compliance

  | Principle | Status | Notes |
  |-----------|--------|-------|
  | I. Simplicity & Maintainability | ✅ PASS | Using standard FastAPI patterns, avoiding complex abstractions |
  | II. Type Safety | ✅ PASS | All functions/models will use Pydantic with full type hints |
  | III. Async-First | ✅ PASS | FastAPI async routes, async Qdrant/Cohere clients |
  | IV. Modular Design | ✅ PASS | Organized by domain: ingestion/, rag/, chat/, api/, utils/ |
  | V. Security First | ✅ PASS | Pydantic validation, prompt injection defenses |
  | VI. Cost Awareness | ✅ PASS | Caching embeddings, using free tiers (Cohere, Qdrant, OpenRouter) |
  | VII. Performance Standards | ✅ PASS | 200ms p95 target, connection pooling, response caching |
  | VIII. Error Recovery & Resilience | ✅ PASS | Retries with backoff, circuit breakers, degraded mode, timeouts |

  ### Technical Stack Compliance

  | Component | Requirement | Status |
  |-----------|-------------|--------|
  | Python 3.12+ with uv | Python 3.12+ (non-negotiable) | ✅ PASS |
  | FastAPI + Uvicorn | Framework | ✅ PASS |
  | Cohere embeddings | embed-english-v3.0 or equivalent | ✅ PASS |
  | Qdrant Cloud Free Tier | Vector database | ✅ PASS |
  | LiteLLM/OpenRouter | Generation (via LiteLLM unified interface) | ✅ PASS |
  | Pydantic | Models/validation | ✅ PASS |
  | No LangChain | Unless justified | ✅ PASS (not needed) |

  ### Data Management Compliance

  | Requirement | Status | Notes |
  |-------------|--------|-------|
  | Max 10MB docs | ✅ PASS | Enforced in ingestion validation |
  | PDF/TXT/MD only | ✅ PASS | File type filtering |
  | 200-500 token chunks | ✅ PASS | Configurable chunking with 50-token overlap |
  | Metadata requirements | ✅ PASS | source_id, chunk_index, timestamp, content_hash |
  | Hash-based deduplication | ✅ PASS | Before embedding to prevent waste |
  | Soft delete (90 days) | ✅ PASS | Retain metadata for audit trail |

  ### Quality & Testing Compliance

  | Requirement | Status | Notes |
  |-------------|--------|-------|
  | TDD with pytest async | ✅ PASS | Test-first approach, async support |
  | Test pyramid (80% unit) | ✅ PASS | Unit, integration, contract tests |
  | 80%+ coverage on core logic | ✅ PASS | RAG pipeline, ingestion, API endpoints |
  | CI/CD gates | ✅ PASS | All tests pass before merge |

  ### RAG-Specific Compliance

  | Requirement | Status | Notes |
  |-------------|--------|-------|
  | Chunk 200-500 tokens, 50 overlap | ✅ PASS | Configurable via environment |
  | Fallback similarity <0.7 | ✅ PASS | Honest response when no matches |
  | Track MRR, NDCG@10 | ✅ PASS | Retrieval quality metrics |
  | Citations required | ✅ PASS | Every answer cites sources |

  ### Performance Standards Compliance

  | Requirement | Status | Notes |
  |-------------|--------|-------|
  | 200ms p95 API response | ✅ PASS | Excluding LLM generation time |
  | 100 concurrent requests | ✅ PASS | Connection pooling, async I/O |
  | Memory <100MB per request | ✅ PASS | Efficient chunk handling |
  | Response caching (1hr TTL) | ✅ PASS | Configurable via environment |

  ### Error Recovery & Resilience Compliance

  | Requirement | Status | Notes |
  |-------------|--------|-------|
  | Exponential backoff (3 retries) | ✅ PASS | 1s→10s with jitter |
  | Circuit breakers (5 failures) | ✅ PASS | 60s cooldown |
  | Degraded mode | ✅ PASS | 503 if vector DB unavailable |
  | Explicit timeouts (5s/30s) | ✅ PASS | 5s default, 30s for LLM |

  **GATE STATUS: ✅ ALL PASSES** - No violations to justify. Proceeding to Phase 0 research.

  ## Project Structure

  ### Documentation (this feature)

  specs/001-rag-chatbot/
  ├── spec.md              # Feature specification (user stories, requirements)
  ├── plan.md              # This file (implementation plan)
  ├── research.md          # Phase 0 output (technology research)
  ├── data-model.md        # Phase 1 output (entities and schema)
  ├── quickstart.md        # Phase 1 output (developer setup)
  ├── contracts/           # Phase 1 output (API specifications)
  │   ├── openapi.yaml     # OpenAPI 3.0 spec
  │   └── README.md        # Contract documentation
  └── tasks.md             # Phase 2 output (/sp.tasks command - not created yet)

  ### Source Code (repository root)

  src/
  ├── ingestion/           # Document ingestion module
  │   ├── init.py
  │   ├── models.py        # Ingestion request/response models
  │   ├── service.py       # Core ingestion logic
  │   └── validators.py    # File validation, size limits
  │
  ├── rag/                 # RAG pipeline module
  │   ├── init.py
  │   ├── models.py        # Query/answer models, selection scope
  │   ├── retrieval.py     # Vector search from Qdrant
  │   ├── generation.py    # LiteLLM generation with context
  │   └── fallback.py      # Fallback when no matches
  │
  ├── chat/                # Conversation session management
  │   ├── init.py
  │   ├── models.py        # Session, message models
  │   └── service.py       # Session CRUD operations
  │
  ├── api/                 # FastAPI route handlers
  │   ├── init.py
  │   ├── deps.py          # FastAPI dependencies (DB clients)
  │   ├── ingestion.py     # Ingestion endpoints
  │   ├── chat.py          # Chat/query endpoints
  │   └── health.py        # Health check endpoint
  │
  ├── core/                # Shared core functionality
  │   ├── init.py
  │   ├── config.py        # Pydantic settings, environment variables
  │   ├── embeddings.py    # Cohere embedding client wrapper
  │   └── vector.py        # Qdrant client wrapper
  │
  └── utils/               # Utilities
      ├── init.py
      ├── chunking.py      # Text chunking logic
      ├── dedup.py         # Content hash deduplication
      └── logging.py       # Structured logging setup

  tests/
  ├── unit/                # Unit tests (80%+ coverage target)
  │   ├── test_chunking.py
  │   ├── test_dedup.py
  │   ├── test_embeddings.py
  │   ├── test_retrieval.py
  │   └── test_generation.py
  │
  ├── integration/         # Integration tests (API + DB/vector store)
  │   ├── test_ingestion.py
  │   ├── test_chat_flow.py
  │   └── test_health.py
  │
  ├── contract/            # Contract tests (external APIs)
  │   ├── test_cohere_api.py
  │   ├── test_openrouter_api.py
  │   └── test_qdrant_api.py
  │
  └── fixtures/            # Reusable test fixtures
      ├── embeddings.py
      ├── qdrant.py
      └── mock_llm.py

  app/                     # FastAPI application entry
  ├── init.py
  └── main.py              # FastAPI app factory, middleware setup

  pyproject.toml           # uv-managed dependencies
  uv.lock                  # Locked dependency versions
  .env.example             # Environment variable template
  Dockerfile               # Container configuration
  requirements.txt         # Generated from uv (for compatibility)

  **Structure Decision**: Single web backend project using FastAPI. Domain-driven module organization (ingestion/, rag/, chat/, api/) ensures separation of concerns. Shared core functionality in core/ avoids duplication. Test pyramid structure follows pytest best practices with unit, integration, and contract tests.

  ## Complexity Tracking

  > **Fill ONLY if Constitution Check has violations that must be justified**

  No violations detected - all constitution requirements are met. This section remains empty.

  ---
  Explanations You Requested:

  1. Document Filtering & Content Ingestion

  The ingestion module will handle all three file types (PDF, TXT, MD):

  How it works:
  # src/ingestion/validators.py

  def validate_file(file_path: str) -> tuple[bool, str]:
      \"\"\"Validate file type and size.\"\"\"
      # Check file extension
      ext = Path(file_path).suffix.lower()
      if ext == '.pdf':
          return True, 'pdf'
      elif ext in ['.txt', '.md']:
          return True, ext[1:]  # Remove the dot
      else:
          return False, f'Unsupported format: {ext}'

      # Check file size (constitution: max 10MB)
      size = os.path.getsize(file_path)
      MAX_SIZE = 10 * 1024 * 1024  # 10MB in bytes
      if size > MAX_SIZE:
          return False, f'File exceeds 10MB limit: {size} bytes'

      return True, 'valid'

  File Routing in Ingestion Service:
  # src/ingestion/service.py

  async def ingest_folder(folder_path: str):
      for root, _, files in os.walk(folder_path):
          for file in files:
              valid, ext = validate_file(file)
              if not valid:
                  continue  # Skip unsupported files

              if ext == 'pdf':
                  await process_pdf(file)
              elif ext == 'md':
                  await process_markdown(file)
              elif ext == 'txt':
                  await process_text(file)

  2. Why LiteLLM Instead of Direct OpenAI SDK

  | Aspect            | Direct OpenAI SDK               | LiteLLM + OpenRouter                         |
  |-------------------|---------------------------------|----------------------------------------------|
  | Lock-in           | Tied to single provider         | Access to 100+ models via one API key        |
  | Cost Optimization | Cannot switch providers         | Compare pricing across providers dynamically |
  | Unified Interface | Different API for each provider | Same completion() function for all           |
  | Reliability       | Single point of failure         | Failover to alternative providers            |
  | Maintenance       | Provider-specific code          | Provider-agnostic, easier updates            |

  References:
  - LiteLLM Docs: https://docs.litellm.ai/
  - OpenRouter: https://openrouter.ai/

  ---