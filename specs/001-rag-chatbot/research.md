# Phase 0: Technology Research

**Feature**: RAG Chatbot Backend
**Date**: 2025-12-30
**Status**: Complete

## Research Summary

All technical requirements from constitution and spec have been resolved. The research confirms that the chosen technology stack (FastAPI, Qdrant, Cohere, OpenAI) is appropriate and aligns with all constitutional requirements.

## Technology Decisions

### Text Chunking Strategy

**Decision**: Use token-based chunking with 50-token overlap
**Rationale**: Token-based chunking preserves semantic meaning better than fixed character counts. 50-token overlap prevents context loss at boundaries. 200-500 token range balances retrieval precision and context window efficiency.

**Implementation**: Use `tiktoken` library for accurate token counting with GPT-4 tokenizer (compatible with OpenAI models).

### PDF Extraction

**Decision**: Use `pypdf` for PDF text extraction
**Rationale**: Lightweight, well-maintained, Python 3.12+ compatible. No external dependencies required. Handles text extraction from PDFs reliably.

**Alternatives Considered**:
- `pdfplumber` (rejected: heavier dependency)
- `PyPDF2` (rejected: less maintained)

### Markdown Processing

**Decision**: Use built-in Python file reading for Markdown
**Rationale**: No external dependencies needed. Simple text extraction.

### Vector Database Schema

**Decision**: Qdrant collection with payload for metadata
**Rationale**: Qdrant supports storing metadata alongside embeddings, enabling filtering by source_id, chapter, page range. Native HNSW index for fast similarity search.

**Payload Schema**:
```json
{
  "source_id": "string",
  "chunk_index": "integer",
  "timestamp": "string (ISO8601)",
  "content_hash": "string (SHA256)",
  "chapter": "string (optional)",
  "page_start": "integer (optional)",
  "page_end": "integer (optional)"
}
```

### Content Selection Filtering

**Decision**: Qdrant payload filters for scope restriction
**Rationale**: Qdrant's filtering capabilities allow efficient pre-filtering by chapter, page ranges before similarity search. Reduces retrieval latency.

**Filter Examples**:
- Whole chapter: `must_match({"chapter": "Chapter 3"})`
- Page range: `range_filters({"page_start": 10, "page_end": 20})`
- No selection: no filter (search all)

### Session Management

**Decision**: In-memory session store with optional Postgres persistence
**Rationale**: For hackathon scope, in-memory sessions suffice. Postgres provides persistence if needed later. Redis overkill for 20+ message sessions.

**Session Structure**:
```json
{
  "session_id": "uuid",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "sources": [...], "timestamp": "..."}
  ],
  "created_at": "ISO8601",
  "last_activity": "ISO8601"
}
```

### Prompt Engineering for RAG

**Decision**: System prompt with retrieved context + explicit citation requirement
**Rationale**: Clear system instructions improve answer quality. Citation requirement ensures traceability. Disclaimers for non-book content maintain honesty.

**Template**:
```
You are a helpful assistant answering questions about book content.

Context from the book:
{retrieved_chunks}

User Question: {question}

Instructions:
1. Answer using ONLY the provided context when relevant.
2. Cite sources by including [source_id:chunk_index] in your answer.
3. If the answer is not in the context, state: "This information is not available in the book."
4. Do not hallucinate or make up information.

Answer:
```

### Error Handling Strategy

**Decision**: Circuit breaker pattern with exponential backoff
**Rationale**: Constitution requires explicit timeouts and retry logic. Circuit breaker prevents cascading failures. Degraded mode (503) maintains partial service availability.

**Implementation**: Use `tenacity` library for retry logic with circuit breaker integration.

### API Authentication

**Decision**: API key via `X-API-Key` header
**Rationale**: Simple, stateless authentication. FastAPI dependency injection makes implementation easy. Compatible with constitution requirements.

**Implementation**:
```python
async def verify_api_key(api_key: str = Header(...)):
    if api_key not in settings.valid_api_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

### Content Deduplication

**Decision**: SHA256 hash of raw text before embedding
**Rationale**: Prevents duplicate embeddings. Constitution requires hash-based deduplication. Fast, collision-resistant.

**Implementation**:
```python
import hashlib

def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
```

### PII Detection

**Decision**: Simple regex pattern matching + optional external service
**Rationale**: Basic PII detection using regex covers email, phone, SSN patterns. Optional external service (like Microsoft Presidio) for production-grade detection.

**Patterns**: Email, phone numbers, SSN, credit card, IP addresses.

### Response Caching

**Decision**: In-memory LRU cache with TTL
**Rationale**: Reduces LLM API costs and latency. LRU evicts old entries. TTL prevents stale answers.

**Implementation**: Use `cachetools` library with TTL decorator.

## Best Practices Applied

| Area | Practice | Constitution Reference |
|-------|----------|----------------------|
| Code Structure | Domain-driven modules | IV. Modular Design |
| Type Safety | Pydantic models everywhere | II. Type Safety |
| Async I/O | Async clients for Qdrant/Cohere | III. Async-First |
| Security | Input validation, rate limiting, API key auth | V. Security First |
| Performance | Connection pooling, caching | VII. Performance Standards |
| Error Recovery | Retries, circuit breakers, timeouts | VIII. Error Recovery & Resilience |
| Cost | Embedding deduplication, caching | VI. Cost Awareness |
| Data | Chunking, metadata requirements | Data Management Principles |
| Testing | Unit/Integration/Contract tests | Quality & Testing Standards |

## Open Questions Resolved

| Question | Resolution |
|----------|-------------|
| How to handle content selection? | Qdrant payload filters for chapter/page ranges |
| How to store sessions? | In-memory sessions, optional Postgres |
| How to detect duplicates? | SHA256 hash before embedding |
| How to fallback when no matches? | Check similarity score <0.7, return honest response |
| How to implement citations? | Include [source_id:chunk_index] in prompt instructions |
| How to protect against prompt injection? | Delimiters in system prompt, validate retrieved chunks |

## Next Steps

Proceed to Phase 1: Generate data models, API contracts, and quickstart guide.
