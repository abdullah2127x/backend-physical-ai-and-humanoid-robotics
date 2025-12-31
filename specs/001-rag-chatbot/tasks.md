# Implementation Tasks: RAG Chatbot Backend

**Feature**: RAG Chatbot Backend
**Branch**: `001-rag-chatbot`
**Date**: 2025-12-30
**Source**: Generated from plan.md, spec.md, data-model.md

## Dependency Graph

```
Phase 1: Setup ───────────────────────────────────────────────────────────────┐
  └─ T001-T007                                                                     │
                                                                                    │
Phase 2: Foundational ────────────────────────────────────────────────────────────┤
  └─ T008-T015                                                                     │
    │                                                                              │
    ▼                                                                              │
Phase 3: User Story 1 (P1) ─ Ask Question About Book Content ────────────────────┤
  └─ T016-T029                                                                     │
    │         │                                                                     │
    ▼         ▼                                                                     │
  (US1)    (US1)                                                                   │
    │                                                                              │
    ▼                                                                              │
Phase 4: User Story 2 (P1) ─ Ingest Book Content for Search ─────────────────────┤
  └─ T030-T046                                                                     │
    │                                                                              │
    ▼                                                                              │
Phase 5: User Story 3 (P2) ─ Receive Answer Not in Book ─────────────────────────┤
  └─ T047-T055                                                                     │
    │                                                                              │
    ▼                                                                              │
Phase 6: Polish & Cross-Cutting Concerns ─────────────────────────────────────────┘
  └─ T056-T060
```

## Parallel Execution Opportunities

| Story | Parallel Tasks | Can Run Together |
|-------|----------------|------------------|
| Setup (T001-T007) | T002, T003, T004 | All setup tasks except T001 (must create structure first) |
| Foundational (T008-T015) | T009, T010, T011 | Can run in parallel after T008 |
| US1 (T016-T029) | T017-T020 | Models can be created in parallel |
| US2 (T030-T046) | T032-T037 | Ingestion services can run in parallel |
| US3 (T047-T055) | T048-T051 | All US3 tasks can run after T047 |

## MVP Scope

**Recommended MVP**: User Story 1 only (T016-T029)

- Focus on core Q&A functionality first
- Skip ingestion (US2) and disclaimer handling (US3) for initial release
- US1 provides the core value proposition

---

## Phase 1: Setup

**Goal**: Initialize project structure and configuration

- [ ] T001 Initialize Python 3.12+ project with uv in pyproject.toml
- [ ] T002 Create .env.example with all required environment variables in .env.example
- [ ] T003 Create src/__init__.py in src/__init__.py
- [ ] T004 Create app/__init__.py in app/__init__.py
- [ ] T005 Create src/core/__init__.py in src/core/__init__.py
- [ ] T006 Create src/utils/__init__.py in src/utils/__init__.py
- [ ] T007 Create requirements.txt from uv.lock for compatibility

---

## Phase 2: Foundational

**Goal**: Create shared infrastructure that all user stories depend on

- [ ] T008 Create Pydantic settings in src/core/config.py
- [ ] T009 Implement Qdrant client wrapper in src/core/vector.py
- [ ] T010 Implement Cohere embedding client in src/core/embeddings.py
- [ ] T011 Implement LiteLLM/OpenRouter client in src/core/generation.py
- [ ] T012 Create text chunking utility in src/utils/chunking.py
- [ ] T013 Create content hash deduplication utility in src/utils/dedup.py
- [ ] T014 Create structured logging setup in src/utils/logging.py
- [ ] T015 Create FastAPI app factory in app/main.py

---

## Phase 3: User Story 1 (P1) - Ask Question About Book Content

**Goal**: Enable users to ask questions about book content and receive contextual answers with conversation history

**Independent Test Criteria**:
- User can select a chapter/page range and ask a question
- System returns answer based only on selected content area
- Conversation history is visible during session
- System responds within 5 seconds

### Models

- [ ] T016 [P] [US1] Create ContentSelection model in src/rag/models.py
- [ ] T017 [P] [US1] Create Source model in src/rag/models.py
- [ ] T018 [P] [US1] Create Session model in src/chat/models.py
- [ ] T019 [P] [US1] Create Message model in src/chat/models.py
- [ ] T020 [P] [US1] Create ChatRequest model in src/rag/models.py
- [ ] T021 [P] [US1] Create ChatResponse model in src/rag/models.py

### Services

- [ ] T022 [US1] Implement vector retrieval in src/rag/retrieval.py
- [ ] T023 [US1] Implement session management in src/chat/service.py
- [ ] T024 [US1] Implement RAG pipeline in src/rag/generation.py
- [ ] T025 [US1] Implement citation extraction in src/rag/generation.py
- [ ] T026 [US1] Implement fallback response for no matches in src/rag/fallback.py

### API Endpoints

- [ ] T027 [US1] Create POST /chat/start endpoint in src/api/chat.py
- [ ] T028 [US1] Create POST /chat/send/{session_id} endpoint in src/api/chat.py
- [ ] T029 [US1] Create GET /chat/history/{session_id} endpoint in src/api/chat.py

---

## Phase 4: User Story 2 (P1) - Ingest Book Content for Search

**Goal**: Process documentation folders and make content searchable

**Independent Test Criteria**:
- User provides folder path, system processes all supported files
- Unsupported files are skipped with summary report
- Errors are reported clearly
- Ingestion completes within 2 minutes for 1000 files

### Models

- [ ] T030 [P] [US2] Create Document model in src/ingestion/models.py
- [ ] T031 [P] [US2] Create IngestionReport model in src/ingestion/models.py
- [ ] T032 [P] [US2] Create IngestionError model in src/ingestion/models.py
- [ ] T033 [P] [US2] Create IngestionRequest model in src/ingestion/models.py
- [ ] T034 [P] [US2] Create Chunk model in src/ingestion/models.py

### Services

- [ ] T035 [US2] Implement file validation in src/ingestion/validators.py
- [ ] T036 [US2] Implement PDF text extraction in src/ingestion/service.py
- [ ] T037 [US2] Implement Markdown/Text processing in src/ingestion/service.py
- [ ] T038 [US2] Implement chunk creation with metadata in src/ingestion/service.py
- [ ] T039 [US2] Implement embedding generation in src/ingestion/service.py
- [ ] T040 [US2] Implement Qdrant upsert for chunks in src/ingestion/service.py
- [ ] T041 [US2] Implement deduplication check in src/ingestion/service.py

### API Endpoints

- [ ] T042 [US2] Create POST /ingestion/start endpoint in src/api/ingestion.py
- [ ] T043 [US2] Create GET /ingestion/status/{report_id} endpoint in src/api/ingestion.py

---

## Phase 5: User Story 3 (P2) - Receive Answer Not in Book

**Goal**: Handle out-of-scope questions with appropriate disclaimers

**Independent Test Criteria**:
- User asks question with no matching content
- System provides disclaimer: "This information is not available in the book"
- System distinguishes book-based answers from general knowledge

### Implementation

- [ ] T047 [US3] Update system prompt template in src/core/generation.py
- [ ] T048 [P] [US3] Add similarity threshold check in src/rag/retrieval.py
- [ ] T049 [P] [US3] Implement disclaimer injection in src/rag/generation.py
- [ ] T050 [P] [US3] Implement partial answer handling in src/rag/fallback.py
- [ ] T051 [P] [US3] Add source tracking for answer attribution in src/rag/generation.py
- [ ] T052 [US3] Update ChatResponse to include is_from_book flag in src/rag/models.py
- [ ] T053 [US3] Update conversation history to include disclaimer in src/chat/service.py
- [ ] T054 [US3] Add PII detection utility in src/utils/pii_detection.py
- [ ] T055 [US3] Implement response filtering in src/rag/generation.py

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Improve reliability, performance, and developer experience

### Infrastructure

- [ ] T056 Create GET /health endpoint in src/api/health.py
- [ ] T057 Implement response caching in src/core/generation.py
- [ ] T058 Add circuit breaker pattern in src/utils/resilience.py
- [ ] T059 Implement retry with exponential backoff in src/utils/resilience.py
- [ ] T060 Create Docker configuration in Dockerfile

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 60 |
| Setup Phase | 7 tasks |
| Foundational Phase | 8 tasks |
| User Story 1 (P1) | 14 tasks |
| User Story 2 (P1) | 14 tasks |
| User Story 3 (P2) | 9 tasks |
| Polish Phase | 5 tasks |
| Parallelizable Tasks | 23 |
| Independent Test Criteria | 4 (one per phase) |

## Recommended Execution Order

1. **Week 1**: Phase 1 + Phase 2 (infrastructure)
2. **Week 2**: Phase 3 (US1 - core Q&A)
3. **Week 3**: Phase 4 (US2 - ingestion)
4. **Week 4**: Phase 5 (US3 - disclaimers) + Phase 6 (polish)

## Implementation Strategy

**MVP (Minimum Viable Product)**:
- Complete Phase 1 (Setup)
- Complete Phase 2 (Foundational)
- Complete Phase 3 (US1 only)

**V1.0 Release** includes:
- Ask questions about book content
- Conversation history during session
- Context-aware answers with citations

**V1.1 Release** adds:
- Document ingestion pipeline
- Content processing for search

**V1.2 Release** adds:
- Disclaimer handling for out-of-scope questions
- PII detection and filtering
