"""
Cohere Embedding Client - Text to vector conversion.

Provides async wrapper for Cohere embeddings API.
"""

import time

import structlog
from cohere import AsyncClient
from cohere.types import EmbedResponse

from .config import get_settings

logger = structlog.get_logger(__name__)


class CohereEmbeddings:
    """Async wrapper for Cohere embedding generation."""

    def __init__(self):
        self._client: AsyncClient | None = None
        self._settings = get_settings()
        self._model = self._settings.cohere_embedding_model
        self._batch_size = self._settings.cohere_embedding_batch_size

    def _get_client(self) -> AsyncClient:
        """Get or create Cohere client."""
        if self._client is None:
            self._client = AsyncClient(
                api_key=self._settings.cohere_api_key,
            )
        return self._client

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        client = self._get_client()
        all_embeddings: list[list[float]] = []

        # Process in batches to respect rate limits
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            start_time = time.time()

            try:
                response: EmbedResponse = await client.embed(
                    texts=batch,
                    model=self._model,
                    input_type="search_document",
                )

                all_embeddings.extend(response.embeddings)

                latency = time.time() - start_time
                logger.debug(
                    "Embedded batch",
                    batch_size=len(batch),
                    latency_ms=round(latency * 1000, 2),
                )

            except Exception as e:
                logger.error("Failed to embed batch", error=str(e))
                raise

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Query text to embed

        Returns:
            Query embedding vector
        """
        client = self._get_client()

        response: EmbedResponse = await client.embed(
            texts=[query],
            model=self._model,
            input_type="search_query",
        )

        return response.embeddings[0]

    async def close(self) -> None:
        """Close the Cohere client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global embeddings instance
_embeddings_instance: CohereEmbeddings | None = None


def get_embeddings() -> CohereEmbeddings:
    """Get the global embeddings instance (singleton pattern)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = CohereEmbeddings()
    return _embeddings_instance
