"""
Vector Retrieval - Search for relevant document chunks.

Handles similarity search against the vector database with filtering.
"""

import time
from typing import Optional

import structlog

from src.core.config import get_settings
from src.core.embeddings import get_embeddings
from src.core.vector import get_qdrant
from src.rag.models import ContentSelection

logger = structlog.get_logger(__name__)


class VectorRetriever:
    """Retrieves relevant document chunks from vector database."""

    def __init__(self):
        self._settings = get_settings()
        self._qdrant = get_qdrant()
        self._embeddings = get_embeddings()

    async def retrieve(
        self,
        query: str,
        selection: Optional[ContentSelection] = None,
        limit: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: User's question
            selection: Optional content scope filter
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of retrieved chunks with metadata
        """
        start_time = time.time()

        # Generate query embedding
        query_embedding = await self._embeddings.embed_query(query)
        logger.debug("Generated query embedding", query_len=len(query_embedding))

        # Use configured limits
        max_chunks = limit or self._settings.rag_max_chunks
        threshold = score_threshold or self._settings.rag_similarity_threshold

        # Search vector database
        results = await self._qdrant.search(
            query_vector=query_embedding,
            limit=max_chunks,
            score_threshold=threshold if threshold > 0 else None,
        )

        latency = time.time() - start_time
        logger.info(
            "Retrieved chunks",
            count=len(results),
            threshold=threshold,
            latency_ms=round(latency * 1000, 2),
        )

        return results

    async def retrieve_with_citations(
        self,
        query: str,
        selection: Optional[ContentSelection] = None,
    ) -> tuple[str, list[dict]]:
        """
        Retrieve chunks and format as context for LLM.

        Args:
            query: User's question
            selection: Optional content scope filter

        Returns:
            Tuple of (formatted_context, chunks)
        """
        chunks = await self.retrieve(query, selection)

        if not chunks:
            return "", []

        # Format chunks for LLM context
        context_parts = []
        for chunk in chunks:
            source_id = chunk.get("payload", {}).get("source_id", "unknown")
            title = chunk.get("payload", {}).get("title", "Untitled")
            text = chunk.get("payload", {}).get("text", "")
            score = chunk.get("score", 0)

            context_parts.append(
                f"[Source: {source_id} | Score: {score:.2f}]\n{text}"
            )

        context = "\n\n".join(context_parts)
        return context, chunks


# Global retriever instance
_retriever: Optional[VectorRetriever] = None


def get_retriever() -> VectorRetriever:
    """Get the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever
