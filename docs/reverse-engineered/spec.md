# RAG Chatbot Backend Specification

**Version**: 1.0 (Reverse Engineered)
**Date**: 2026-01-01
**Source**: D:\AbdullahQureshi\workspace\Hackathon-2025\backend-physical-ai-and-humanoid-robotics

## Problem Statement

The RAG Chatbot Backend provides an API for question-answering over book content and other documents using Retrieval-Augmented Generation (RAG). It allows users to upload documents, index them in a vector database, and then ask questions that are answered based on the content of those documents. The system addresses the need for domain-specific AI assistance where general LLMs lack the specific knowledge contained in particular documents.

## System Intent

**Target Users**: Developers, researchers, and organizations that need to build AI-powered Q&A systems over their own documents.

**Core Value Proposition**: Enables users to ask natural language questions about their documents and receive accurate, cited answers based on the content, without needing to read through entire documents manually.

**Key Capabilities**:
- Document ingestion and indexing in vector database
- Natural language question-answering with citations
- Session-based conversation management
- Health and monitoring endpoints

## Functional Requirements

### Requirement 1: Document Ingestion
- **What**: Upload and process documents from various sources (files, URLs, sitemaps) and store them in vector format
- **Why**: To enable the system to answer questions based on specific document content
- **Inputs**: File paths, URLs, source types, ingestion configuration
- **Outputs**: Ingestion report with processing statistics
- **Side Effects**: Creates vector embeddings in Qdrant database
- **Success Criteria**: Documents are successfully parsed, chunked, and stored as embeddings

### Requirement 2: Question-Answering
- **What**: Accept user questions and generate answers based on ingested document content
- **Why**: To provide AI-powered assistance for understanding document content
- **Inputs**: User question, session ID, optional content selection
- **Outputs**: Answer with citations to source documents
- **Side Effects**: Saves conversation history, creates new session if needed
- **Success Criteria**: Accurate answers with proper citations and context

### Requirement 3: Session Management
- **What**: Create, manage, and delete conversation sessions
- **Why**: To maintain conversation context and history
- **Inputs**: Session creation requests, session IDs
- **Outputs**: Session IDs, conversation history
- **Side Effects**: Stores conversation history in memory
- **Success Criteria**: Sessions persist conversation state and can be retrieved

### Requirement 4: System Health Monitoring
- **What**: Provide health and readiness endpoints for monitoring
- **Why**: To enable system monitoring and orchestration
- **Inputs**: Health check requests
- **Outputs**: Health status and component readiness
- **Side Effects**: None
- **Success Criteria**: Returns accurate system status information

## Non-Functional Requirements

### Performance
- Response time < 3-5 seconds for question-answering (with proper vector database connection)
- Support for 100+ concurrent requests
- Efficient retrieval from vector database
- Target: Handle 10-100 QPS depending on query complexity

### Security
- API key authentication for external services (Cohere, OpenRouter)
- Input validation for all endpoints
- No direct exposure of sensitive credentials
- Standards: Environment-based configuration for secrets

### Reliability
- Graceful degradation when vector database unavailable
- Error handling for external service failures
- Session timeout management
- Circuit breaker patterns for external API calls

### Scalability
- Stateless API design for horizontal scaling
- Session management can be externalized
- Vector database as external dependency

### Observability
- Structured logging with correlation IDs using structlog
- Error logging for debugging
- Monitoring: Health and readiness endpoints available

## System Constraints

### External Dependencies
- Qdrant Vector Database: Cloud or self-hosted vector database
- Cohere API: For generating document embeddings
- OpenRouter/LiteLLM: For LLM responses
- Python 3.11+ runtime

### Data Formats
- JSON for API requests/responses
- PDF, TXT, HTML, DOCX for document ingestion (via external libraries)

### Deployment Context
- FastAPI application running with uvicorn
- Environment: Can be deployed on various platforms
- Configuration via .env files

### Compliance Requirements
- Data privacy: No storage of user questions beyond session lifetime
- API rate limiting through external services

## Non-Goals & Out of Scope

**Explicitly excluded** (inferred from missing implementation):
- Real-time collaborative editing
- Advanced document format support (only basic formats via external libraries)
- Multi-tenant isolation beyond basic session management
- Advanced analytics or usage tracking

## Known Gaps & Technical Debt

### Gap 1: Production Readiness of Health Checks
- **Issue**: Health checks are basic and don't actually verify external service connectivity
- **Evidence**: [src/api/health.py, lines 63-76]
- **Impact**: False readiness reports in production
- **Recommendation**: Implement actual connectivity checks for external services

### Gap 2: Session Persistence
- **Issue**: Sessions appear to be in-memory only, not persistent across restarts
- **Evidence**: [src/chat/service.py] likely uses in-memory storage
- **Impact**: Conversation loss on service restart
- **Recommendation**: Implement persistent session storage

### Gap 3: Rate Limiting
- **Issue**: No apparent rate limiting implementation
- **Evidence**: No rate limiting middleware found
- **Impact**: Potential abuse of external APIs and service degradation
- **Recommendation**: Add rate limiting middleware

## Success Criteria

### Functional Success
- [ ] All API endpoints return correct responses for valid inputs
- [ ] All error cases handled gracefully with appropriate HTTP status codes
- [ ] Document ingestion processes various file types successfully
- [ ] Question-answering provides relevant responses with citations

### Non-Functional Success
- [ ] Response time < 5 seconds for typical queries
- [ ] System handles 100+ concurrent users
- [ ] 95%+ test coverage achieved
- [ ] Zero critical security vulnerabilities

## Acceptance Tests

### Test 1: Document Ingestion Flow
**Given**: Valid document file path
**When**: POST /ingestion/start with ingestion request
**Then**: Document is processed and stored in vector database

### Test 2: Question-Answering Flow
**Given**: Documents have been ingested and user has a session
**When**: POST /chat/send/{session_id} with question
**Then**: Returns answer based on document content with citations

### Test 3: Session Management
**Given**: No existing session
**When**: POST /chat/start
**Then**: Returns new session ID that can be used for conversation