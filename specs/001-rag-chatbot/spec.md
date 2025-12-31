# Feature Specification: RAG Chatbot Backend

**Feature Branch**: `001-rag-chatbot`
**Created**: 2025-12-30
**Status**: Draft
**Input**: User description: "create a specification with upper level detail we discuss and do not mention to techincal detail"

## Clarifications

### Session 2025-12-31

- Q: LLM provider for general knowledge answers → A: LiteLLM with OpenRouter (unified multi-model interface, cost optimization, provider failover)
- Q: Supported file types for ingestion → A: MD, MDX only (constitution: MD-focused, no PDF needed for current docs)
- Q: Session persistence approach → A: Backend UUID sessions with 24-hour timeout; frontend stores session ID in localStorage for continuity
- Q: Ingestion folder scanning approach → A: Recursive folder scan with relative paths from configured content root
- Q: Embedding model and vector database → A: Cohere embed-english-v3.0 + Qdrant Cloud Free Tier

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask Question About Book Content (Priority: P1)

User reads a published book online and wants to ask a specific question about the content they are currently viewing. The system provides an answer based only on the content from the book, and displays the conversation history during their session.

**Why this priority**: This is the core value proposition - enabling users to get contextual answers about book content without navigating away.

**Independent Test**: Can be tested by opening the book interface, selecting any page/chapter/section, and asking a question. The system should return an answer that references only the selected content area.

**Acceptance Scenarios**:

1. **Given** User has the book interface open, **When** User selects a chapter and asks "What is the main concept explained here?", **Then** System returns an answer that uses only information from that chapter
2. **Given** User selects a specific page range and asks a question, **When** User submits their query, **Then** System filters search to only that page range and provides an accurate answer
3. **Given** User does not select any specific content area and asks a question, **When** User submits their query, **Then** System searches across all available book content and provides the best answer
4. **Given** User refreshes their browser page, **When** User returns to ask a new question, **Then** System treats this as a new conversation session (no previous messages visible)
5. **Given** User has an ongoing conversation with multiple questions, **When** User asks a follow-up question, **Then** System shows complete conversation history from the current session

---

### User Story 2 - Ingest Book Content for Search (Priority: P1)

Content authors or maintainers need to upload new or updated book documentation so that it becomes available for users to ask questions about. The system accepts a relative folder path from a configured content root, recursively scans all subdirectories, and processes MD/MDX files for search capability.

**Why this priority**: Without this capability, users cannot ask questions about content. This is foundational to the entire feature.

**Independent Test**: Can be tested by providing a documentation folder with various file types and verifying that the system processes them correctly and makes the content searchable.

**Acceptance Scenarios**:

1. **Given** A documentation folder contains supported file types, **When** Content manager initiates ingestion of the folder, **Then** System processes all valid documents and confirms successful ingestion with count of files processed
2. **Given** Folder contains a mix of supported and unsupported file types, **When** Ingestion is triggered, **Then** System automatically filters and processes only supported file types, skipping unsupported ones with a summary report
3. **Given** Folder path is invalid or not accessible, **When** Ingestion is attempted, **Then** System returns a clear error message indicating the specific issue
4. **Given** Ingestion has previously been completed for a folder, **When** Ingestion is triggered again, **Then** System either updates existing content or handles duplicates appropriately based on configured behavior

---

### User Story 3 - Receive Answer Not in Book (Priority: P2)

User asks a question about the book content, but the specific information is not covered in any of the available book sections. The system provides a helpful response while clearly distinguishing between book-based answers and general knowledge answers.

**Why this priority**: Users often ask questions beyond scope. Without clear disclaimers, they may incorrectly attribute general information to book content, leading to misunderstandings.

**Independent Test**: Can be tested by asking questions clearly outside the book's scope (e.g., "What is tomorrow's weather?" or "Who won the 2025 World Cup?") and verifying that the response includes appropriate disclaimers.

**Acceptance Scenarios**:

1. **Given** User asks a question with no matching content in the book, **When** System finds no relevant information, **Then** System responds with a general knowledge answer AND explicitly states "This information is not available in the book" or similar disclaimer
2. **Given** User asks a question partially covered in the book, **When** System finds some relevant but insufficient information, **Then** System provides answer based on available book content and clearly indicates what parts are from book versus general knowledge
3. **Given** User asks a question within book scope, **When** System finds relevant content, **Then** System provides answer without disclaimer (since it's book-based)

---

### Edge Cases

- What happens when selected content area contains no searchable text?
- How does system handle concurrent users asking questions about the same content?
- What happens when ingestion folder is empty?
- How does system handle very long selected text ranges?
- What happens when user asks question in unsupported language?
- How does system handle malformed or invalid folder paths during ingestion?
- What happens when session identifier is corrupted or lost during conversation?
- How does system handle extremely long queries from users?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept user questions via a chat interface and provide answers
- **FR-002**: System MUST accept an optional content selection parameter to limit search scope to specific pages, chapters, or ranges
- **FR-003**: System MUST retrieve and search only from ingested book content when answering questions
- **FR-004**: System MUST process documentation folders and make content searchable
- **FR-005**: System MUST automatically identify and process only supported file types (MD, MDX) from provided folders
- **FR-006**: System MUST maintain conversation history within a single user session
- **FR-007**: System MUST distinguish between answers derived from book content versus general knowledge
- **FR-008**: System MUST provide explicit disclaimer when answer uses information not found in the book
- **FR-009**: System MUST handle cases where no book content matches the user question
- **FR-010**: System MUST provide user with summary of ingestion results (number of files processed, any errors encountered)
- **FR-011**: System MUST support flexible content selection (whole page, whole chapter, custom range, or none)
- **FR-012**: System MUST append new conversation messages to existing session without replacing full history

### Key Entities

- **Document**: A piece of content from the book (can be a page, chapter, or section) that is processed for search capability
- **Content Selection**: User-defined scope for search, which can be specific page range, entire chapter, or no selection (search all)
- **Question**: User's inquiry or request for information
- **Answer**: System's response to a question, which may be based on book content or general knowledge
- **Conversation Session**: A continuous dialogue between user and system within a single browsing session
- **Conversation Message**: An individual exchange (either user question or system answer) within a conversation session
- **Ingestion Report**: Summary of document processing results including counts and any issues encountered

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask questions about book content and receive answers within 5 seconds
- **SC-002**: 95% of questions asked within selected content scope return relevant book-based answers
- **SC-003**: System processes documentation folders with up to 1000 files within 2 minutes
- **SC-004**: Users can maintain conversation history for at least 20 message exchanges without loss
- **SC-005**: 100% of answers derived from general knowledge (not book content) include explicit disclaimer
- **SC-006**: Users can select content scope at any level (specific page, chapter, or all content) with equal responsiveness
- **SC-007**: Ingestion process provides clear success/failure feedback within 10 seconds for folders up to 100 files

### External Services

- **LLM Provider**: LiteLLM with OpenRouter for general knowledge answers (enables multi-model access, cost optimization, and provider failover)
- **Embedding Model**: Cohere embed-english-v3.0 for text-to-vector conversion
- **Vector Database**: Qdrant Cloud Free Tier for storing and searching embeddings

### Non-Functional Requirements

- **NFR-001**: System must handle at least 50 concurrent users asking questions without degradation in response quality
- **NFR-002**: Search results must be relevant and accurate when content exists within selected scope
- **NFR-003**: Conversation session must remain active and accessible during continuous user interaction
- **NFR-004**: System must be resilient to temporary unavailability of external search services
- **NFR-005**: Ingestion process must not affect ongoing question answering for other users

## Assumptions

- Content selection is optional; if not provided, system searches all available content
- Conversation history uses backend UUID sessions with 24-hour timeout; frontend stores session ID in localStorage to maintain continuity across page refreshes
- Ingestion processes files as they exist at the time of ingestion
- System will automatically filter supported file types (MD, MDX) during ingestion
- Content scope selection can be any granularity from single page to entire book
- General knowledge answers may be provided when book content is insufficient, with appropriate disclaimers
- Session identifiers are generated and managed by the user interface for conversation continuity
