# API Contracts

This directory contains the OpenAPI 3.0 specification for the RAG Chatbot Backend API.

## Files

- `openapi.yaml` - Complete OpenAPI 3.0 specification

## Overview

The API provides three main functional areas:

### Health Check
- `GET /health` - Check system health (Qdrant, Cohere, OpenAI connectivity)

### Document Ingestion
- `POST /ingestion/start` - Start processing a folder of documents
- `GET /ingestion/status/{report_id}` - Check ingestion progress/results

### Chat & Conversations
- `POST /chat/start` - Create a new conversation session
- `POST /chat/send/{session_id}` - Ask a question with optional content selection
- `GET /chat/history/{session_id}` - Retrieve conversation history

## Authentication

All endpoints except `/health` require API key authentication via the `X-API-Key` header.

## API Versioning

Current version: `/v1/`
Breaking changes will result in a new major version (e.g., `/v2/`)

## Documentation

- Interactive Swagger UI available at: `http://localhost:8000/docs` (when server is running)
- ReDoc documentation available at: `http://localhost:8000/redoc`

## Validating the Contract

```bash
# Install openapi-spec-validator
pip install openapi-spec-validator

# Validate
openapi-spec-validator openapi.yaml
```

## Generating Client SDKs

```bash
# OpenAPI Generator
docker run --rm -v "${PWD}:/local" \
  openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g python \
  -o /local/client

# Or generate TypeScript client
docker run --rm -v "${PWD}:/local" \
  openapitools/openapi-generator-cli generate \
  -i /local/openapi.yaml \
  -g typescript-axios \
  -o /local/client-ts
```
