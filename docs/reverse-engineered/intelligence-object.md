# RAG Chatbot Backend Reusable Intelligence

**Version**: 1.0 (Extracted from Codebase)
**Date**: 2026-01-01

## Overview

This document captures the reusable intelligence embedded in the codebase—patterns, decisions, and expertise worth preserving and applying to future projects.

---

## Extracted Skills

### Skill 1: FastAPI Application Factory Pattern

**Persona**: You are a backend engineer designing scalable FastAPI applications with proper lifecycle management.

**Questions to ask before implementing FastAPI application**:
- What startup/shutdown tasks are needed?
- How will configuration be loaded and managed?
- What middleware is required for the application?
- How should routes be organized and registered?

**Principles**:
- **Lifespan management**: Use async lifespan for startup/shutdown events
- **Configuration loading**: Load settings once at startup, use singleton pattern
- **Middleware configuration**: Set up CORS, logging, and error handling early
- **Route registration**: Organize routes in separate modules and register in factory
- **Global exception handling**: Implement centralized error handling

**Implementation Pattern** (observed in codebase):
```python
# Extracted from: [src/app/main.py, lines 21-89]
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager - startup and shutdown events."""
    settings = get_settings()

    logger.info("Starting RAG Chatbot Backend", version="0.1.0")

    # Initialize Qdrant connection
    try:
        await init_qdrant()
        logger.info("Qdrant connection established")
    except Exception as e:
        logger.warning("Failed to connect to Qdrant - running in degraded mode", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down RAG Chatbot Backend")
    qdrant = get_qdrant()
    await qdrant.disconnect()

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    settings = get_settings()

    app = FastAPI(
        title="RAG Chatbot API",
        description="Backend API for RAG-powered book content Q&A",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.app_debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from src.api.chat import router as chat_router
    from src.api.health import router as health_router
    from src.api.ingestion import router as ingestion_router

    app.include_router(health_router, prefix="/health", tags=["Health"])
    app.include_router(chat_router, prefix="/chat", tags=["Chat"])
    app.include_router(ingestion_router, prefix="/ingestion", tags=["Ingestion"])

    return app
```

**When to apply**:
- All FastAPI-based services
- Applications requiring startup/shutdown tasks
- Projects needing centralized configuration

### Skill 2: Pydantic Settings Configuration Pattern

**Persona**: You are a configuration management engineer ensuring consistent and validated application configuration.

**Questions to ask before implementing configuration**:
- What configuration values are needed for the application?
- How should configuration be loaded (environment variables, files, etc.)?
- What validation is required for configuration values?
- How should sensitive configuration be handled?

**Principles**:
- **Environment loading**: Load from .env files with environment variable overrides
- **Validation**: Use Pydantic field validators for configuration validation
- **Type safety**: Define specific types for configuration values
- **Singleton access**: Provide singleton access to configuration instance
- **Default values**: Provide sensible defaults for development

**Implementation Pattern** (observed in codebase):
```python
# Extracted from: [src/core/config.py, lines 13-117]
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Settings
    app_host: str = Field(default="0.0.0.0", description="Host to bind the server to")
    app_port: int = Field(default=8000, ge=1, le=65535, description="Port to bind the server to")
    app_debug: bool = Field(default=False, description="Enable debug mode")

    # External service configurations
    qdrant_url: str = Field(description="Qdrant Cloud URL")
    cohere_api_key: str = Field(default="", description="Cohere API key")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")

    @field_validator("ingestion_chunk_size")
    @classmethod
    def parse_chunk_size_range(cls, v: str) -> str:
        """Validate chunk size range format (e.g., '200-500')."""
        try:
            parts = v.split("-")
            if len(parts) != 2:
                raise ValueError("Must be in format 'min-max'")
            min_size, max_size = int(parts[0]), int(parts[1])
            if min_size < 50 or max_size > 2000:
                raise ValueError("Chunk size must be between 50-2000 tokens")
            if min_size >= max_size:
                raise ValueError("Min must be less than max")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid chunk size range '{v}': {e}") from e
        return v

def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**When to apply**:
- All Python applications requiring configuration
- Projects with multiple environment deployments
- Services with sensitive configuration values

### Skill 3: Async Service Locator Pattern

**Persona**: You are a service architect designing dependency management for async applications.

**Questions to ask before implementing service management**:
- What services need to be shared across the application?
- Should services be singletons or created per request?
- How should service initialization be handled?
- What lifecycle management is needed for services?

**Principles**:
- **Lazy initialization**: Initialize services only when first accessed
- **Thread safety**: Ensure singleton access is thread-safe
- **Async compatibility**: Support async initialization when needed
- **Global access**: Provide simple global access to service instances
- **Clear interfaces**: Use abstract base classes or clear contracts

**Implementation Pattern** (observed in codebase):
```python
# Extracted from: [src/chat/service.py, lines 100-117] (pattern example)
from typing import Optional

_session_service: Optional[SessionService] = None

def get_session_service() -> SessionService:
    """Get the global session service instance (singleton pattern)."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service

# Similar pattern in other service modules:
# - get_ingestion_service() in src/ingestion/service.py
# - get_retriever() in src/rag/retrieval.py
# - get_qdrant() in src/core/vector.py
```

**When to apply**:
- Applications with shared service instances
- Async applications requiring singleton services
- Projects with multiple service dependencies

### Skill 4: RAG (Retrieval-Augmented Generation) Architecture

**Persona**: You are an AI engineer implementing RAG systems for domain-specific question-answering.

**Questions to ask before implementing RAG**:
- What vector database is appropriate for the use case?
- How should documents be chunked and indexed?
- What similarity threshold is appropriate?
- How should citations be generated and returned?
- What fallback strategies are needed when no relevant context is found?

**Principles**:
- **Chunking strategy**: Balance between context size and relevance
- **Similarity matching**: Use appropriate threshold for retrieval
- **Citation tracking**: Maintain links to original sources
- **Fallback handling**: Provide responses when no context is available
- **Context formatting**: Format retrieved context for optimal LLM performance

**Implementation Pattern** (observed in codebase):
```python
# Extracted from: [src/api/chat.py, lines 88-136] and [src/rag/retrieval.py]
async def send_message(session_id: UUID4, request: ChatRequest) -> ChatResponse:
    # Retrieve relevant context
    retriever = get_retriever()
    context, chunks = await retriever.retrieve_with_citations(
        query=request.question,
        selection=request.content_selection,
    )

    # Generate response
    if chunks:
        # Use RAG with context
        generator = get_rag_generator()
        response = await generator.generate_response(
            question=request.question,
            context=context,
            chunks=chunks,
        )
    else:
        # No context found - use fallback
        llm = get_llm_client()
        fallback = get_fallback_handler()

        # Try to provide a general answer
        try:
            general_answer = await llm.generate(
                system_prompt="You are a helpful assistant. Answer the question helpfully.",
                user_message=request.question,
                temperature=0.3,
            )
            response = fallback.get_fallback_response(
                question=request.question,
                general_answer=general_answer,
            )
        except Exception:
            # LLM also failed - return simple fallback
            response = fallback.get_fallback_response(question=request.question)
```

**When to apply**:
- Document question-answering systems
- Domain-specific AI applications
- Applications requiring source citations

---

## Architecture Decision Records (Inferred)

### ADR-001: Choice of FastAPI over Flask/Django for API Framework

**Status**: Accepted (inferred from implementation)

**Context**:
The system requires:
- Async request handling for I/O operations
- Automatic API documentation
- Type validation with Pydantic
- High performance for AI/ML workloads

**Decision**: Use FastAPI as the primary web framework

**Rationale** (inferred from code patterns):
1. **Evidence 1**: Heavy use of async/await patterns throughout the codebase
   - Location: [src/api/chat.py, src/ingestion/service.py, src/core/vector.py]
   - Pattern: All external API calls and database operations use async

2. **Evidence 2**: Pydantic model integration for request/response validation
   - Location: [src/rag/models.py, src/ingestion/models.py, src/chat/models.py]
   - Pattern: All API models use Pydantic BaseModels with field validation

3. **Evidence 3**: Built-in documentation and type hints
   - Location: All API route definitions
   - Pattern: Automatic OpenAPI documentation generation

**Consequences**:

**Positive**:
- Excellent async support for I/O operations
- Automatic API documentation with Swagger UI
- Strong type validation and IDE support
- High performance with Starlette ASGI foundation

**Negative**:
- Smaller ecosystem compared to Flask
- Newer framework with potential breaking changes
- Requires async programming knowledge

**Alternatives Considered** (inferred):
- **Flask**: Rejected because of sync-first design, less native async support
- **Django**: Rejected because of monolithic nature, overkill for API-only service

### ADR-002: Qdrant Vector Database for Embedding Storage

**Status**: Accepted (inferred from implementation)

**Context**:
The system needs:
- High-performance vector similarity search
- Support for embedding metadata
- Python client library
- Scalability for document collections

**Decision**: Use Qdrant as the vector database

**Rationale** (inferred from code patterns):
1. **Evidence 1**: Dedicated Qdrant client implementation
   - Location: [src/core/vector.py]
   - Pattern: Full-featured QdrantClient with connection management

2. **Evidence 2**: Vector search operations tailored for RAG
   - Location: [src/rag/retrieval.py]
   - Pattern: Similarity search with metadata filtering

3. **Evidence 3**: Collection management features
   - Location: [src/core/vector.py]
   - Pattern: Create, delete, and manage vector collections

**Consequences**:

**Positive**:
- High-performance vector similarity search
- Rich filtering capabilities
- Good Python client library
- Can run in cloud or self-hosted

**Negative**:
- Additional infrastructure dependency
- Learning curve for vector database concepts
- Potential cost implications for cloud usage

**Alternatives Considered** (inferred):
- **Pinecone**: Could have worked but likely costlier
- **Chroma**: Simpler but potentially less scalable
- **Weaviate**: Similar capabilities, possible alternative

---

## Code Patterns & Conventions

### Pattern 1: API Router Organization

**Observed in**: All API modules (chat.py, ingestion.py, health.py)

**Structure**:
```python
# Standard structure for API modules
from fastapi import APIRouter

router = APIRouter()

@router.post("/endpoint", response_model=ResponseModel, summary="Summary")
async def endpoint_function(request: RequestModel) -> ResponseModel:
    """
    Detailed function documentation.

    Args:
        request: Input parameters

    Returns:
        Response with expected format
    """
    # Implementation here
    pass
```

**Benefits**:
- Clean separation of API endpoints
- Easy route registration in main application
- Consistent documentation format
- Type safety with Pydantic models

**When to apply**: All FastAPI route definitions

### Pattern 2: Background Task Processing

**Observed in**: Ingestion API for long-running operations

**Structure**:
```python
# Extracted from: [src/api/ingestion.py, lines 28-49]
async def run_ingestion_task(report_id: UUID, request: IngestionRequest) -> None:
    """Background task for ingestion."""
    # Task implementation
    pass

@router.post("/start", ...)
async def start_ingestion(request: IngestionRequest, background_tasks: BackgroundTasks) -> StatusResponse:
    # Create report first
    report = IngestionReport(...)

    # Start background task
    task = asyncio.create_task(
        run_ingestion_task(report.id, request),
        name=f"ingestion-{report.id}",
    )
    _running_ingestions[report.id] = task

    return StatusResponse(...)
```

**Benefits**:
- Non-blocking API responses
- Progress tracking for long operations
- Proper task management
- Error handling for background operations

**When to apply**: Long-running operations that shouldn't block API responses

---

## Lessons Learned

### What Worked Well

1. **Clean architecture separation**
   - Clear boundaries between API, service, and data layers
   - Easy to test individual components
   - **Benefit**: Maintainable and extensible codebase

2. **Comprehensive configuration management**
   - Pydantic Settings with validation
   - Environment-based configuration
   - **Benefit**: Easy deployment across different environments

3. **Async-first design**
   - Proper async/await usage throughout
   - Non-blocking I/O operations
   - **Benefit**: Better performance for I/O-bound operations

### What Could Be Improved

1. **Session persistence**
   - Sessions appear to be in-memory only
   - **Impact**: Conversation loss on restart
   - **Recommendation**: Implement Redis or database-backed sessions

2. **Production health checks**
   - Health checks don't verify external service connectivity
   - **Impact**: False positive health status
   - **Recommendation**: Add actual connectivity checks

3. **Rate limiting**
   - No apparent rate limiting implementation
   - **Impact**: Potential API abuse and costs
   - **Recommendation**: Add rate limiting middleware

### What to Avoid in Future Projects

1. **In-memory session storage**
   - Hard to scale and maintain
   - **Why bad**: Data loss on restarts, difficult horizontal scaling
   - **Alternative**: External storage (Redis, database)

2. **Basic error fallbacks**
   - Limited graceful degradation strategies
   - **Why bad**: Poor user experience when services fail
   - **Alternative**: More robust fallback mechanisms

3. **Missing observability**
   - Limited metrics and monitoring
   - **Why bad**: Difficult to debug production issues
   - **Alternative**: Metrics + tracing + structured logs from day 1

---

## Reusability Assessment

### Components Reusable As-Is

1. **FastAPI application factory** → Portable to any FastAPI project
2. **Configuration management system** → Portable to any Python service
3. **Service locator pattern** → Portable to any Python application
4. **RAG architecture pattern** → Patterns reusable, specifics adaptable

### Patterns Worth Generalizing

1. **Async service management** → Create template for any async service
2. **Background task processing** → Create pattern for long-running operations
3. **API router organization** → Create template for consistent API structure

### Domain-Specific (Not Reusable)

1. **Document ingestion logic** → Specific to RAG domain
2. **Book content processing** → Specific to document Q&A
3. **Qdrant vector operations** → Specific to vector databases