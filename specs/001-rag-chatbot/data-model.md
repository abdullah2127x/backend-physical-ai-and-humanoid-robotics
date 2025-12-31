# Data Model: RAG Chatbot Backend

**Feature**: RAG Chatbot Backend
**Date**: 2025-12-30
**Status**: Phase 1 Complete

## Entity Overview

This document describes core entities for RAG Chatbot Backend system, including their fields, relationships, and validation rules derived from feature specification and constitution.

---

## Entity 1: Document

Represents a piece of content from the book that is processed for search capability.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| document_id | UUID | Required, auto-generated | Unique identifier for the document |
| source_id | string | Required, max 255 chars | Reference to source file (e.g., filename) |
| file_path | string | Required | Absolute path to original file |
| file_type | enum | Required, values: `pdf`, `txt`, `md` | File type |
| file_size | integer | Required, max 10,485,760 bytes (10MB) | File size in bytes |
| content_hash | string | Required, SHA256, max 64 chars | Hash of raw text content |
| status | enum | Required, values: `pending`, `processing`, `completed`, `failed` | Processing status |
| chunk_count | integer | Required, >= 0 | Number of chunks created |
| created_at | datetime | Required, auto-generated | Timestamp when document was ingested |
| updated_at | datetime | Required, auto-updated | Timestamp of last update |

### Validation Rules
- `file_size` must not exceed 10MB (constitution requirement)
- `file_type` must be one of: `pdf`, `txt`, `md` (constitution requirement)
- `content_hash` must be valid SHA256 format
- `chunk_count` must be >= 0

### Relationships
- One Document has many Chunks

---

## Entity 2: Chunk

Represents a semantic unit of content from a document, stored as a vector embedding.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| chunk_id | UUID | Required, auto-generated | Unique identifier for the chunk |
| document_id | UUID | Required, FK to Document | Parent document |
| chunk_index | integer | Required, >= 0 | Sequential index within document |
| content | string | Required | Text content of the chunk |
| content_hash | string | Required, SHA256, max 64 chars | Hash of chunk content |
| embedding | list[float] | Required, size: 1024 (Cohere v3) | Vector embedding |
| chapter | string | Optional, max 255 chars | Chapter name if available |
| page_start | integer | Optional, >= 0 | Starting page number |
| page_end | integer | Optional, >= 0, >= page_start | Ending page number |
| timestamp | datetime | Required, auto-generated | When chunk was created |

### Validation Rules
- `chunk_index` must be >= 0
- `embedding` must be exactly 1024 dimensions (Cohere embed-english-v3.0)
- `content_hash` must be valid SHA256 format
- `page_end` must be >= `page_start` if both present

### Relationships
- Many Chunks belong to one Document
- One Chunk appears in many ConversationMessage (as citation)

### Note on Storage
Chunks are stored in Qdrant with embedding as vector. Metadata stored as payload:
- `document_id`, `chunk_index`, `timestamp`, `content_hash`, `chapter`, `page_start`, `page_end`

---

## Entity 3: ConversationSession

Represents a continuous dialogue between user and system within a single browsing session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| session_id | UUID | Required, auto-generated | Unique session identifier |
| messages | list[ConversationMessage] | Required | Conversation history |
| created_at | datetime | Required, auto-generated | Session start time |
| last_activity | datetime | Required, auto-updated | Last message timestamp |

### Validation Rules
- `messages` list must be in chronological order
- Session expires after 30 minutes of inactivity (configurable)

### Relationships
- One ConversationSession has many ConversationMessage

---

## Entity 4: ConversationMessage

Represents an individual exchange (user question or system answer) within a conversation session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| message_id | UUID | Required, auto-generated | Unique message identifier |
| session_id | UUID | Required, FK to ConversationSession | Parent session |
| role | enum | Required, values: `user`, `assistant` | Who sent the message |
| content | string | Required, max 10,000 chars | Message content |
| content_selection | ContentSelection | Optional | User's selected content scope |
| sources | list[Source] | Optional, for assistant messages only | Cited chunks |
| disclaimer | string | Optional | Disclaimer if answer not from book |
| timestamp | datetime | Required, auto-generated | When message was created |

### Validation Rules
- `content` max 10,000 characters (configurable)
- `sources` only allowed when `role` = `assistant`
- `disclaimer` only allowed when `role` = `assistant`

### Relationships
- Many ConversationMessage belong to one ConversationSession

---

## Entity 5: ContentSelection

Defines user-defined scope for search (specific page range, entire chapter, or no selection).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| selection_type | enum | Required, values: `none`, `page_range`, `chapter` | Type of selection |
| chapter | string | Optional, max 255 chars | Chapter name if selection_type=chapter |
| page_start | integer | Optional, >= 0 | Starting page if selection_type=page_range |
| page_end | integer | Optional, >= 0, >= page_start | Ending page if selection_type=page_range |

### Validation Rules
- If `selection_type` = `chapter`, then `chapter` is required
- If `selection_type` = `page_range`, then `page_start` and `page_end` are required
- If `selection_type` = `none`, no other fields required
- `page_end` must be >= `page_start`

---

## Entity 6: Source

Represents a cited chunk in an answer.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| source_id | string | Required | Document source identifier |
| chunk_index | integer | Required, >= 0 | Chunk index within document |
| chapter | string | Optional | Chapter name if available |
| relevance_score | float | Required, 0.0 to 1.0 | Similarity score from retrieval |

### Validation Rules
- `relevance_score` must be between 0.0 and 1.0
- `chunk_index` must be >= 0

---

## Entity 7: IngestionReport

Summary of document processing results.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| report_id | UUID | Required, auto-generated | Unique report identifier |
| folder_path | string | Required | Path to ingested folder |
| files_processed | integer | Required, >= 0 | Number of files processed |
| files_skipped | integer | Required, >= 0 | Number of unsupported files skipped |
| files_failed | integer | Required, >= 0 | Number of files that failed processing |
| chunks_created | integer | Required, >= 0 | Total chunks created |
| errors | list[IngestionError] | Required | List of errors encountered |
| started_at | datetime | Required | Start timestamp |
| completed_at | datetime | Required | Completion timestamp |

### Validation Rules
- All count fields must be >= 0
- `completed_at` must be >= `started_at`

---

## Entity 8: IngestionError

Error details from document processing.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| file_name | string | Required | Name of file that caused error |
| error_type | string | Required | Type of error (e.g., "invalid_format", "size_exceeded") |
| error_message | string | Required | Detailed error message |

---

## Entity Relationship Diagram

```
Document (1) ----< (*) Chunk

ConversationSession (1) ----< (*) ConversationMessage

ConversationMessage (optional) ----> ContentSelection

ConversationMessage (assistant) ----> (*) Source

IngestionReport (1) ----> (*) IngestionError
```

---

## State Transitions

### Document Status

```
pending -> processing -> completed
pending -> processing -> failed
completed -> processing (re-processing)
```

---

## Indexes and Query Patterns

### Qdrant Collection (chunks)
- Primary: Vector HNSW index for similarity search
- Payload indexes:
  - `source_id` (exact match filtering)
  - `chapter` (exact match filtering)
  - `page_start` (range filtering)
  - `page_end` (range filtering)
  - `content_hash` (deduplication checks)

### Query Patterns
1. **Search all content**: No payload filter
2. **Search specific chapter**: `must_match({"chapter": "Chapter 3"})`
3. **Search page range**: `range_filters({"page_start": 10, "page_end": 20})`
4. **Check for duplicates**: `must_match({"content_hash": "..."})`

---

## Validation Summary

| Constraint | Constitution Reference | Entity |
|------------|----------------------|---------|
| Max 10MB per document | Data Management | Document |
| PDF/TXT/MD only | Data Management | Document |
| 200-500 token chunks | RAG Guidelines | Chunk (via chunking logic) |
| Metadata required | Data Management | Chunk |
| Hash-based deduplication | Data Management | Document, Chunk |
| Soft delete (90 days) | Data Management | Document (via status field) |
| Max 1000 chars query | Security First | ConversationMessage |

---

## Next Steps

Proceed to generate API contracts based on these data models.
