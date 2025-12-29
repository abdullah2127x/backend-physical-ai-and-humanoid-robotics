---
id: 0001
title: Create RAG system constitution
stage: constitution
date: 2025-12-25
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: main
user: unknown
command: /sp.constitution
labels: ["governance", "principles", "technical-stack", "rag-system", "initial-setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - None (governance artifact)
---

## Prompt

```text
## Core Principles
- **Simplicity and Maintainability**: Favor clear, readable code over clever solutions. Follow KISS, DRY, and YAGNI. Prioritize explicit over implicit.
- **Type Safety**: Use Python type hints everywhere (including | union syntax in Python 3.12+). All functions, classes, and Pydantic models must be fully typed.
- **Async-First**: FastAPI is async-capable—prefer async routes, async database/vector clients, and async dependencies unless sync is explicitly justified.
- **Modular Design**: Organize code by domain/feature (e.g., ingestion/, rag/, api/, utils/). Use dependency injection for services.
- **Security First**: Validate all inputs (Pydantic + custom validators). Implement rate limiting, CORS restrictions, and protect API keys via environment variables. Never expose secrets in code.
- **Cost Awareness**: Minimize API calls to paid services (OpenAI, Cohere). Cache embeddings where possible. Use free tiers efficiently.

## Technical Stack (Non-Negotiable)
- **Language & Manager**: Python 3.12+ managed with uv (virtualenv, dependencies, scripts).
- **Framework**: FastAPI with Uvicorn server.
- **Embeddings**: Cohere (free tier models like embed-english-v3.0).
- **Vector Database**: Qdrant Cloud Free Tier (qdrant-client).
- **Generation**: OpenAI SDK (ChatCompletion or Agents if needed).
- **Database (Optional)**: Neon Serverless Postgres (psycopg2-binary or async driver) for metadata/chat history.
- **Other**: Pydantic for models/validation, no heavy frameworks like LangChain unless justified.

## Quality & Testing Standards
- **Test-Driven Development**: Write tests first where feasible. Use pytest with async support.
- **Coverage**: Aim for 80%+ coverage on core logic (RAG pipeline, ingestion, API endpoints).
- **Error Handling**: Graceful errors with proper HTTP status codes and logging.
- **Logging & Monitoring**: Structured logging; prepare for future observability.
- **Documentation**: Docstrings on public functions/endpoints. OpenAPI/Swagger auto-generated.

## RAG-Specific Guidelines
- **Chunking**: 200-500 tokens per chunk with overlap for better retrieval.
- **Retrieval**: Hybrid if needed (vector + metadata filters via Qdrant payloads/Postgres).
- **Context Management**: Augment prompts with retrieved chunks + user-selected text. Guard against prompt injection.
- **Fallbacks**: If no relevant retrievals, respond honestly without hallucinating.

## Governance
- All plans, tasks, and implementations must explicitly reference and adhere to this constitution.
- Architectural decisions requiring deviation must be justified and approved by human review.
- Keep the project lightweight: MVP-first, add complexity only when required.
```

## Response snapshot

Created constitution v1.0.0 for Backend Physical AI and Humanoid Robotics RAG System with:
- 6 core principles (Simplicity, Type Safety, Async-First, Modular Design, Security First, Cost Awareness)
- Non-negotiable technical stack (Python 3.12+, FastAPI, Cohere, Qdrant, OpenAI, uv)
- Quality standards (TDD, 80%+ coverage, error handling, logging, documentation)
- RAG-specific guidelines (chunking 200-500 tokens, hybrid retrieval, prompt injection guards, honest fallbacks)
- Governance rules (adherence required, deviations need approval, MVP-first approach)

Validated consistency with plan-template.md, spec-template.md, and tasks-template.md. All templates align with constitutional principles.

## Outcome

- ✅ Impact: Established governance foundation for all future development. All features must now reference and adhere to these principles.
- 🧪 Tests: No tests applicable (governance artifact)
- 📁 Files: Created .specify/memory/constitution.md (v1.0.0)
- 🔁 Next prompts: Ready for feature specification (/sp.specify) or direct implementation planning (/sp.plan) for first RAG feature
- 🧠 Reflection: Constitution establishes clear technical and quality boundaries. RATIFICATION_DATE needs to be set when formally adopted. Templates already align with principles, minimizing propagation work.

## Evaluation notes (flywheel)

- Failure modes observed: None. Template structure followed correctly with all placeholders replaced.
- Graders run and results (PASS/FAIL): PASS - No unresolved placeholders, version semantics correct (1.0.0 for initial), dates in ISO format, principles declarative and testable.
- Prompt variant (if applicable): Standard constitution creation workflow
- Next experiment (smallest change to try): Monitor first feature implementation to validate whether constitution principles are practical and complete, or require PATCH/MINOR amendments.
