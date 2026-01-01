---
id: 0006
title: fix-ingestion-path-report-issues
stage: refactor
date: 2025-12-31
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-rag-chatbot
branch: 001-rag-chatbot(ingestion-service)
user: Abdullah Qureshi
command: continue
labels: [ingestion,bugfix,qdrant,path-resolution]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/abdullah2127x/backend-physical-ai-and-humanoid-robotics/pull/4
files:
  - src/api/ingestion.py
  - src/ingestion/service.py
  - src/core/vector.py
  - src/utils/chunking.py
tests:
  - Ingestion API tested with chapter-1.md
  - Status endpoint returns completed report
  - Chat retrieval works with ingested content
---

## Prompt

Please continue the conversation from where we left it off without asking the user any further questions. Continue with the last task that you were asked to work on.

The context shows we were implementing User Story 2 (Ingestion Service) and encountered issues where:
1. Search returned 0 chunks despite data existing in Qdrant (similarity score 0.5069 < threshold 0.7)
2. Ingestion returned "Path not found: chapter-1.md" and "Report not found" errors

We need to fix these issues to complete the ingestion service.

## Response snapshot

Fixed critical issues in the ingestion service:

1. **Similarity threshold fix** (src/core/config.py): Changed `RAG_SIMILARITY_THRESHOLD=0.7` to `0.35` since Qdrant cosine similarity of 0.5069 was being filtered out

2. **Path resolution fix** (src/api/ingestion.py): Added content root path resolution so `chapter-1.md` resolves to `./content/chapter-1.md`

3. **Report tracking fix** (src/ingestion/service.py): Fixed timestamp type mismatch by using `datetime.utcnow()` instead of `time.time()`, and added `report_id` parameter to `ingest()` for consistent report access

4. **Test results verified**:
   - Ingestion: 1 file processed, 1 chunk stored
   - Chat: Retrieved chunk and answered "What is robotics?" correctly

## Outcome

- ✅ Impact: Complete ingestion flow working - files can be ingested and chat can retrieve content
- 🧪 Tests: Manual testing via curl commands verified all endpoints
- 📁 Files: 4 files modified (57 insertions, 19 deletions)
- 🔁 Next prompts: PR created, ready for review and merge
- 🧠 Reflection: Key learnings - cosine similarity scores of 0.35-0.5 are typical for semantic search; background tasks need proper report sharing between API and service instances

## Evaluation notes (flywheel)

- Failure modes observed: Threshold too strict filtered valid results; path not relative to content root; datetime vs float type mismatch in reports
- Graders run and results (PASS/FAIL): Manual integration tests PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add unit tests for ingestion service
