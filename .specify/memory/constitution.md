<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0
Modified principles:
  - V. Security First (expanded with comprehensive threat model and RAG-specific defenses)
Expanded sections:
  - Quality & Testing Standards (added test pyramid, fixtures, CI/CD gates)
  - RAG-Specific Guidelines (added evaluation metrics and quality measurements)
Added sections:
  - VII. Performance Standards (NEW)
  - VIII. Error Recovery & Resilience (NEW)
  - Data Management Principles (NEW)
  - Observability & Debugging (expanded from brief mention)
  - API Design & Versioning (NEW)
  - Dependency Hygiene (NEW)
  - Operational Standards (NEW)
Templates requiring updates:
  ✅ plan-template.md (reviewed - performance and operational standards now enforceable in Constitution Check)
  ✅ spec-template.md (reviewed - NFR section should reference performance targets)
  ✅ tasks-template.md (reviewed - test pyramid and operational tasks align)
Follow-up TODOs:
  - RATIFICATION_DATE needs to be set when constitution is formally adopted
  - Consider creating ADR for monitoring/observability stack selection
  - Review existing code/plans against new performance and operational standards
-->

# Backend Physical AI and Humanoid Robotics RAG System Constitution

## Core Principles

### I. Simplicity and Maintainability

Favor clear, readable code over clever solutions. Follow KISS (Keep It Simple, Stupid), DRY (Don't Repeat Yourself), and YAGNI (You Aren't Gonna Need It). Prioritize explicit over implicit.

**Rationale**: Clear code reduces onboarding time, makes debugging faster, and minimizes technical debt. Explicit implementations prevent hidden behavior and make the system predictable.

### II. Type Safety

Use Python type hints everywhere (including | union syntax in Python 3.12+). All functions, classes, and Pydantic models MUST be fully typed.

**Rationale**: Type hints catch errors at development time, improve IDE support, serve as inline documentation, and make refactoring safer. This is non-negotiable for maintaining system reliability.

### III. Async-First

FastAPI is async-capable—prefer async routes, async database/vector clients, and async dependencies unless sync is explicitly justified.

**Rationale**: Async I/O maximizes throughput for I/O-bound operations (database queries, API calls, vector searches). Sync operations block the event loop and degrade performance under load.

### IV. Modular Design

Organize code by domain/feature (e.g., ingestion/, rag/, api/, utils/). Use dependency injection for services.

**Rationale**: Domain-driven structure makes the codebase navigable and scalable. Dependency injection enables testing, mocking, and component reuse without tight coupling.

### V. Security First

Validate all inputs (Pydantic + custom validators). Implement rate limiting, CORS restrictions, and protect API keys via environment variables. Never expose secrets in code.

**Input Validation**:
- Pydantic validators for all request bodies
- Sanitize user queries (strip HTML, limit special chars)
- Max query length: 1000 characters

**Prompt Injection Defense** (RAG-specific):
- Prefix system instructions with delimiters
- Validate retrieved chunks don't contain injection patterns
- Implement output filtering for PII/secrets

**Authentication & Authorization**:
- API key authentication required for all endpoints (except health checks)
- Rate limiting: 100 requests/min per API key (burst: 20)
- CORS: Whitelist only approved origins (no wildcards in production)

**Data Protection**:
- Encrypt embeddings at rest (Qdrant encryption enabled)
- TLS 1.3 for all external communications
- PII detection in ingested documents (log warnings, optional rejection)
- Audit logging for all document ingestion/deletion operations

**Rationale**: Input validation prevents injection attacks and malformed data. Environment-based secrets prevent credential leakage. Rate limiting and CORS protect against abuse and unauthorized access. RAG systems face unique prompt injection risks requiring defense-in-depth. Audit trails enable security incident investigation.

### VI. Cost Awareness

Minimize API calls to paid services (OpenAI, Cohere). Cache embeddings where possible. Use free tiers efficiently.

**Rationale**: Cloud AI services charge per token/request. Caching embeddings eliminates redundant costs. Efficient use of free tiers enables rapid prototyping and testing without budget constraints.

### VII. Performance Standards

- **Latency Targets**: API endpoints MUST respond within 200ms p95 (excluding LLM generation time)
- **Throughput**: System MUST handle 100 concurrent requests without degradation
- **Resource Limits**: Memory usage per request <100MB, database connections pooled
- **Caching Strategy**: Implement response caching for identical queries (TTL: configurable, default 1 hour)

**Rationale**: Performance targets ensure predictable user experience. Connection pooling prevents resource exhaustion. Caching reduces load on expensive embedding/generation services. Measurable targets enable performance regression detection.

### VIII. Error Recovery & Resilience

- **Retry Logic**: Exponential backoff for external API failures (max 3 retries, start 1s, cap 10s)
- **Circuit Breakers**: Fail fast after 5 consecutive failures; recover after 60s cooldown period
- **Degraded Mode**: If vector DB unavailable, return cached results or fail gracefully with 503
- **Timeout Enforcement**: All external calls MUST have explicit timeouts (5s default, 30s max for LLM)

**Rationale**: Transient failures are common in distributed systems. Retries with backoff handle temporary outages. Circuit breakers prevent cascading failures. Explicit timeouts prevent resource leaks. Degraded operation maintains partial service availability.

## Technical Stack (Non-Negotiable)

- **Language & Manager**: Python 3.12+ managed with uv (virtualenv, dependencies, scripts).
- **Framework**: FastAPI with Uvicorn server.
- **Embeddings**: Cohere (free tier models like embed-english-v3.0).
- **Vector Database**: Qdrant Cloud Free Tier (qdrant-client).
- **Generation**: OpenAI SDK (ChatCompletion or Agents if needed).
- **Database (Optional)**: Neon Serverless Postgres (psycopg2-binary or async driver) for metadata/chat history.
- **Other**: Pydantic for models/validation, no heavy frameworks like LangChain unless justified.

**Rationale**: This stack balances cost (free tiers), performance (async-capable), and developer experience (modern tooling). Any deviation MUST be justified in an ADR with cost/performance/complexity trade-offs documented.

## Data Management Principles

- **Ingestion Validation**: Reject documents >10MB, unsupported formats (allow: PDF, TXT, MD only)
- **Chunking Quality**: Monitor chunk size distribution; alert if >10% exceed token limits
- **Embedding Integrity**: Validate embedding dimensions match model spec (1024 for Cohere v3)
- **Metadata Requirements**: Every chunk MUST have: source_id, chunk_index, timestamp, content_hash
- **Deduplication**: Hash-based deduplication before embedding to prevent waste and cost
- **Data Lifecycle**: Implement soft deletion (retain metadata 90 days); hard delete requires audit trail

**Rationale**: Data validation prevents pipeline failures. Metadata enables traceability and debugging. Deduplication reduces embedding costs. Content hashing detects duplicates and enables integrity checks. Soft deletion enables recovery from accidental deletions.

## Quality & Testing Standards

- **Test-Driven Development**: Write tests first where feasible. Use pytest with async support.
- **Test Pyramid**:
  - Unit Tests: 80%+ coverage on services, utilities (fast, no external dependencies, isolated)
  - Integration Tests: API endpoints + database/vector store (use test containers or mocks)
  - Contract Tests: Validate external API responses (Cohere, OpenAI) match expected schemas
- **Test Fixtures**: Reusable fixtures for embeddings, Qdrant collections, mock LLM responses
- **CI/CD Gates**: All tests MUST pass before merge; no skipped tests in main branch
- **Coverage**: Aim for 80%+ coverage on core logic (RAG pipeline, ingestion, API endpoints).
- **Error Handling**: Graceful errors with proper HTTP status codes and logging.
- **Logging & Monitoring**: Structured logging; prepare for future observability.
- **Documentation**: Docstrings on public functions/endpoints. OpenAPI/Swagger auto-generated.

**Rationale**: Test-first ensures testability and prevents regressions. Test pyramid balances speed and coverage. High coverage on core logic protects critical paths. Contract tests detect API breaking changes early. Proper error handling and logging enable debugging in production. Documentation reduces friction for API consumers and future maintainers.

## Observability & Debugging

- **Metrics (MUST track)**:
  - request_count (by endpoint, status code)
  - latency_p50, latency_p95, latency_p99
  - error_rate (5xx errors per minute)
  - cache_hit_ratio
  - embedding_cost (tokens processed)
  - retrieval_result_count (avg chunks returned per query)
- **Tracing**: OpenTelemetry spans for: document ingestion, embedding generation, vector retrieval, LLM generation
- **Log Levels**:
  - ERROR: Unrecoverable failures requiring immediate attention
  - WARN: Retryable failures, degraded mode activation
  - INFO: Lifecycle events (startup, shutdown, document ingested)
  - DEBUG: Development only (never in production due to PII risk)
- **Alert Thresholds**:
  - p95 latency >500ms (sustained 5 minutes)
  - Error rate >5% (any 1-minute window)
  - Embedding API failures >10/min
  - Vector DB connection failures

**Rationale**: Metrics enable performance monitoring and capacity planning. Distributed tracing reveals bottlenecks across service boundaries. Structured logs enable efficient debugging. Alerts ensure rapid incident response. Thresholds balance signal vs noise.

## API Design & Versioning

- **Versioning Scheme**: URI versioning `/v1/`, `/v2/` for breaking changes
- **Deprecation Policy**: 90-day notice before removal; maintain N-1 version support minimum
- **Contract Testing**: All API responses MUST match OpenAPI schema; validate in CI/CD
- **Breaking Changes**: Require MAJOR version bump + ADR documentation + migration guide
- **Backward Compatibility**: Additive changes only within same major version (new optional fields OK, removing/renaming fields NOT OK)

**Rationale**: Explicit versioning prevents breaking existing clients. Deprecation policy provides migration runway. Schema validation prevents accidental contract violations. ADR captures rationale for breaking changes. Backward compatibility reduces coordination overhead.

## Dependency Hygiene

- **Version Pinning**: All dependencies MUST be pinned to exact versions in uv.lock
- **Security Scanning**: Run `uv audit` in CI/CD; block merges on HIGH/CRITICAL vulnerabilities
- **Update Policy**: Review dependencies quarterly; patch security issues within 7 days
- **Forbidden Dependencies**: No GPL-licensed libraries (license conflict), no unmaintained packages (>1 year since last release)
- **Dependency Review**: New dependencies require justification (why not stdlib/existing dep?)

**Rationale**: Version pinning ensures reproducible builds. Security scanning prevents known vulnerabilities. Timely patching reduces attack surface. License restrictions prevent legal issues. Quarterly reviews prevent dependency rot. Justification requirement prevents unnecessary complexity.

## RAG-Specific Guidelines

- **Chunking**: 200-500 tokens per chunk with 50-token overlap for better retrieval
- **Retrieval**: Hybrid if needed (vector + metadata filters via Qdrant payloads/Postgres)
- **Context Management**: Augment prompts with retrieved chunks + user-selected text. Guard against prompt injection.
- **Fallbacks**: If no relevant retrievals (similarity <0.7), respond honestly without hallucinating
- **Retrieval Quality Metrics**:
  - Measure MRR (Mean Reciprocal Rank), NDCG@10 for retrieval relevance
  - Track "no results" rate (target: <5% of queries)
  - Monitor average number of retrieved chunks per query (target: 3-5)
- **Generation Quality**:
  - Human evaluation sample (minimum 10 queries/week) for answer accuracy
  - Automated checks: citation presence (every answer must cite sources), answer length (50-500 words), refusal detection (track when system declines to answer)

**Rationale**: Chunk size balances context granularity and retrieval precision. Overlap prevents context loss at boundaries. Hybrid retrieval combines semantic and structured filtering for better relevance. Prompt injection guards prevent malicious manipulation. Honest fallbacks maintain trust. Retrieval metrics quantify search quality. Generation quality checks ensure output meets standards.

## Operational Standards

- **Deployment**: Blue-green deployment pattern for zero-downtime updates
- **Health Checks**: `/health` endpoint returning 200 only if DB + vector store + embedding API all reachable
- **Graceful Shutdown**: Drain in-flight requests (30s timeout) before termination; new requests get 503
- **Rollback Plan**: Automated rollback on health check failures post-deploy (3 consecutive failures in 2 minutes)
- **Maintenance Windows**: Database migrations during low-traffic windows; require dry-run on staging first
- **Runbooks**: Document common operations (scaling, certificate rotation, data recovery, incident response)

**Rationale**: Blue-green deployments eliminate downtime. Deep health checks prevent routing traffic to degraded instances. Graceful shutdown prevents dropped requests. Automated rollback limits blast radius of bad deploys. Migration dry-runs catch issues before production. Runbooks enable faster incident resolution.

## Governance

- All plans, tasks, and implementations MUST explicitly reference and adhere to this constitution.
- Architectural decisions requiring deviation MUST be justified and approved by human review.
- Keep the project lightweight: MVP-first, add complexity only when required.
- Constitution amendments require:
  1. Documentation of rationale
  2. Impact analysis on existing templates and code
  3. Human approval before adoption
  4. Version increment following semantic versioning (MAJOR.MINOR.PATCH)
- Complexity violations (e.g., introducing non-stack dependencies, adding abstractions without clear need) MUST be documented in the Complexity Tracking section of plan.md with explicit justification.
- Performance/security/operational standard violations MUST be tracked as technical debt with remediation plan and timeline.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE: set when formally adopted) | **Last Amended**: 2025-12-25
