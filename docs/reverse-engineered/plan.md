# RAG Chatbot Backend Implementation Plan

**Version**: 1.0 (Reverse Engineered)
**Date**: 2026-01-01

## Architecture Overview

**Architectural Style**: Clean Architecture with layered design (API, Service, Data/Infrastructure)

**Reasoning**: The system separates concerns clearly between presentation (API), business logic (services), and data infrastructure (vector DB, external APIs), making it maintainable and testable.

**Diagram** (ASCII):
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Layer     │───▶│  Service Layer   │───▶│ Infrastructure  │
│ (FastAPI)       │    │ (Business Logic) │    │ (Qdrant, APIs)  │
│ - Route defs    │    │ - Session mgmt   │    │ - Vector DB     │
│ - Input val.    │    │ - Ingestion      │    │ - Cohere API    │
│ - Response fmt  │    │ - RAG logic      │    │ - OpenRouter    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Layer Structure

### Layer 1: API Layer (src/api/)
- **Responsibility**: Handle HTTP requests, input validation, response formatting
- **Components**:
  - [chat.py]: Chat conversation endpoints
  - [ingestion.py]: Document ingestion endpoints
  - [health.py]: Health monitoring endpoints
- **Dependencies**: → Service Layer
- **Technology**: FastAPI with Pydantic models

### Layer 2: Service/Business Logic Layer (src/chat/, src/ingestion/, src/core/)
- **Responsibility**: Core business rules, orchestration, session management
- **Components**:
  - [chat/service.py]: Session management and conversation logic
  - [ingestion/service.py]: Document processing and ingestion workflow
  - [core/generation.py]: LLM interaction logic
  - [rag/retrieval.py]: Vector retrieval and RAG logic
- **Dependencies**: → Data Layer, → External Services
- **Technology**: Python services with async/await patterns

### Layer 3: Data/Persistence Layer (src/core/vector.py, external APIs)
- **Responsibility**: Data access, vector storage, external API integration
- **Components**:
  - [core/vector.py]: Qdrant vector database client
  - [core/embeddings.py]: Cohere embedding integration
  - External API clients for Cohere and OpenRouter
- **Dependencies**: → Vector Database, → External APIs
- **Technology**: Qdrant client, HTTP clients for external APIs

## Design Patterns Applied

### Pattern 1: Service Locator Pattern
- **Location**: [src/chat/service.py, src/ingestion/service.py, src/core/vector.py]
- **Purpose**: Provide singleton access to service instances
- **Implementation**:
```python
def get_session_service() -> SessionService:
    # Returns singleton session service instance
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
```

### Pattern 2: Configuration Singleton
- **Location**: [src/core/config.py]
- **Purpose**: Centralized application configuration with environment loading
- **Implementation**: Pydantic Settings with singleton pattern

### Pattern 3: Factory Pattern
- **Location**: [app/main.py#create_app()]
- **Purpose**: Create and configure the FastAPI application
- **Implementation**: Function that creates and configures FastAPI instance with middleware and routes

## Data Flow

### Question-Answering Flow (Synchronous)
1. **API Layer** receives POST /chat/send/{session_id} request
2. **Validation Middleware** validates ChatRequest schema
3. **Chat Router** calls send_message function
4. **Session Service** verifies session exists and saves user message
5. **Retriever** performs vector search in Qdrant for relevant chunks
6. **RAG Generator** creates context and generates response using LLM
7. **Session Service** saves assistant response with citations
8. **API Layer** returns ChatResponse to client

### Document Ingestion Flow (Asynchronous)
1. **API Layer** receives POST /ingestion/start request
2. **Validation** ensures valid IngestionRequest
3. **Background Task** starts ingestion using asyncio.create_task
4. **Ingestion Service** processes documents, creates embeddings
5. **Vector Client** stores embeddings in Qdrant
6. **Status Updates** reported through IngestionReport
7. **API Layer** provides status endpoints for monitoring

## Technology Stack

### Language & Runtime
- **Primary**: Python 3.11
- **Rationale**: Rich ecosystem for AI/ML, async support, good for web APIs

### Web Framework
- **Choice**: FastAPI
- **Rationale**: Automatic API documentation, async support, Pydantic integration, excellent for AI APIs

### Vector Database
- **Choice**: Qdrant
- **Rationale**: High-performance vector search, Python client, good similarity matching for RAG

### Embeddings
- **Choice**: Cohere API
- **Rationale**: High-quality embeddings, good for document similarity

### LLM
- **Choice**: OpenRouter with LiteLLM
- **Rationale**: Flexible LLM provider access, supports multiple models

### Testing
- **Choice**: pytest
- **Rationale**: Rich ecosystem, async support with pytest-asyncio

### Deployment
- **Choice**: uvicorn ASGI server
- **Rationale**: Production-ready ASGI server for FastAPI

## Module Breakdown

### Module: core
- **Purpose**: Core infrastructure services (config, embeddings, generation, vector DB)
- **Key Classes**: [Settings, QdrantClient, CohereEmbeddings, LLMClient]
- **Dependencies**: [qdrant-client, cohere, litellm, pydantic]
- **Complexity**: Medium

### Module: chat
- **Purpose**: Conversation management, session handling
- **Key Classes**: [SessionService, Message models]
- **Dependencies**: [core services, API models]
- **Complexity**: Medium

### Module: ingestion
- **Purpose**: Document processing and vector database population
- **Key Classes**: [IngestionService, Document models]
- **Dependencies**: [core services, crawler, external libraries]
- **Complexity**: High

### Module: rag
- **Purpose**: Retrieval-Augmented Generation logic
- **Key Classes**: [Retriever, RAGGenerator]
- **Dependencies**: [core services, vector DB]
- **Complexity**: High

### Module: api
- **Purpose**: API endpoints and request/response handling
- **Key Classes**: [Route handlers, API models]
- **Dependencies**: [chat, ingestion, health services]
- **Complexity**: Low

## Regeneration Strategy

### Option 1: Specification-First Rebuild
1. Start with spec.md (intent and requirements)
2. Apply extracted skills (error handling, API patterns)
3. Implement with modern best practices (fill gaps)
4. Test-driven development using acceptance criteria

**Timeline**: 3-4 weeks for full rebuild with improvements

### Option 2: Incremental Refactoring
1. **Strangler Pattern**: New implementation shadows old
2. **Feature Flags**: Gradual traffic shift
3. **Parallel Run**: Validate equivalence
4. **Cutover**: Complete migration

**Timeline**: 6-8 weeks with gradual migration

## Improvement Opportunities

### Technical Improvements
- [ ] **Add Redis for session persistence** instead of in-memory
  - **Rationale**: Session data survives restarts, horizontal scaling
  - **Effort**: Medium

- [ ] **Implement proper rate limiting**
  - **Addresses Gap**: Security and API cost management
  - **Effort**: Low

### Architectural Improvements
- [ ] **Event Sourcing for conversation history**
  - **Enables**: Audit trail, temporal queries, better debugging
  - **Effort**: High

- [ ] **CQRS pattern for read/write separation**
  - **Separates**: Query performance from ingestion performance
  - **Effort**: Medium

### Operational Improvements
- [ ] **Production-ready health checks** with actual service verification
- [ ] **Structured monitoring** with Prometheus metrics
- [ ] **Distributed tracing** with OpenTelemetry
- [ ] **Comprehensive logging** with structured error tracking