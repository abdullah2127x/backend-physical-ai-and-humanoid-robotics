---
id: "0007"
title: "Unified Ingestion System Implementation"
stage: "tasks"
date: "2026-01-01"
model: "claude-sonnet-4-5-20250929"
feature: "001-rag-chatbot"
branch: "001-rag-chatbot(ingestion-service)"
user: "AbdullahQureshi"
command: "sp.git.commit_pr"
labels: ["ingestion", "sitemap", "cohere", "rate-limiting", "refactor"]
links:
  spec: null
  ticket: null
  adr: null
  pr: "https://github.com/abdullah2127x/backend-physical-ai-and-humanoid-robotics/pull/4"
files: [
  "src/api/ingestion.py",
  "src/core/embeddings.py",
  "src/ingestion/models.py",
  "src/ingestion/service.py",
  "src/crawler/sitemap.py",
  "src/crawler/scraper.py"
]
tests: []
---

# Unified Ingestion System Implementation

## Summary

This PHR documents the implementation of a unified ingestion system that supports both directory and sitemap sources for the RAG chatbot backend. The implementation includes improved Cohere rate limiting and new web scraping functionality.

## Changes Made

### 1. Unified Ingestion Service
- Updated ingestion service to support both directory and sitemap sources with a single API
- Added source type detection and routing logic
- Maintained backward compatibility with existing directory ingestion

### 2. Cohere Client Upgrade
- Upgraded from Cohere AsyncClient to AsyncClientV2
- Implemented improved rate limiting and retry logic
- Added batching for more efficient API usage
- Enhanced error handling for API limits

### 3. Sitemap & Web Scraping
- Created new `src/crawler/sitemap.py` module for sitemap parsing
- Created new `src/crawler/scraper.py` module for web scraping functionality
- Added robust error handling for network requests
- Implemented text extraction and markdown conversion

### 4. API & Model Updates
- Updated ingestion models to include IngestionSourceType enum
- Enhanced API endpoints to accept source type parameter
- Improved path resolution and validation
- Added comprehensive error reporting

## Technical Details

The unified system allows users to specify whether they want to ingest from a local directory or from a sitemap URL through the `source_type` parameter in the ingestion request. The system automatically routes the request to the appropriate ingestion method based on this parameter.

Rate limiting improvements ensure better handling of Cohere API limits, preventing ingestion failures during high-volume processing.

## Files Modified

- `src/api/ingestion.py`: Updated ingestion API to support source type selection
- `src/core/embeddings.py`: Upgraded Cohere client to V2 with improved rate limiting
- `src/ingestion/models.py`: Added IngestionSourceType enum and updated models
- `src/ingestion/service.py`: Implemented unified ingestion service for both sources
- `src/crawler/sitemap.py`: New module for sitemap parsing
- `src/crawler/scraper.py`: New module for web scraping

## Outcome

The unified ingestion system successfully supports both directory and sitemap ingestion with improved reliability and error handling. The rate limiting improvements help prevent API errors during bulk processing operations.

## Validation

- Directory ingestion continues to work as expected
- Sitemap ingestion functionality verified
- Rate limiting improvements confirmed to reduce API errors
- All changes successfully committed and pushed to PR #4

## Response Summary

Implemented a comprehensive unified ingestion system supporting both directory and sitemap sources, with improved Cohere API rate limiting and new web scraping functionality.