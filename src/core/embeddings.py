"""
Cohere Embedding Client - Text to vector conversion.

Provides async wrapper for Cohere embeddings API.
"""

import asyncio
import time
from typing import Literal

import structlog
import cohere
from cohere import AsyncClientV2
from cohere.errors import TooManyRequestsError

from .config import get_settings

logger = structlog.get_logger(__name__)

# Rate limit retry settings
DEFAULT_MAX_RETRIES = 5
DEFAULT_INITIAL_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_BATCH_DELAY = 0.5  # delay between batches


class CohereEmbeddings:
    """Async wrapper for Cohere embedding generation V2."""

    def __init__(self):
        self._client: AsyncClientV2 | None = None
        self._settings = get_settings()
        self._model = self._settings.cohere_embedding_model
        # Optimal batch size for current key
        self._batch_size = 20

    def _get_client(self) -> AsyncClientV2:
        """Get or create Cohere client V2."""
        if self._client is None:
            self._client = AsyncClientV2(
                api_key=self._settings.cohere_api_key,
            )
        return self._client

    async def embed_texts(
        self,
        texts: list[str],
        input_type: Literal["search_document", "search_query"] = "search_document",
    ) -> list[list[float]]:
        """Embed texts using Cohere API with retry logic and batching."""
        if not texts:
            return []

        client = self._get_client()
        all_embeddings = []

        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]

            # Retry mechanism
            delay = DEFAULT_INITIAL_DELAY
            for attempt in range(DEFAULT_MAX_RETRIES + 1):
                try:
                    response = await client.embed(
                        texts=batch,
                        model=self._model,
                        input_type=input_type,
                        embedding_types=["float"],
                    )

                    # V2 API uses response.embeddings.float_
                    batch_embeddings = response.embeddings.float_ if response.embeddings.float_ else []
                    all_embeddings.extend(batch_embeddings)
                    break

                except TooManyRequestsError:
                    if attempt < DEFAULT_MAX_RETRIES:
                        logger.warning("rate_limit_hit", attempt=attempt + 1, delay=delay)
                        await asyncio.sleep(delay)
                        delay = min(delay * 2, DEFAULT_MAX_DELAY)
                    else:
                        raise
                except Exception as e:
                    logger.error("embedding_failed", error=str(e))
                    raise

            # Small inter-batch delay to stay under the radar
            if i + self._batch_size < len(texts):
                await asyncio.sleep(DEFAULT_BATCH_DELAY)

        return all_embeddings

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single search query."""
        results = await self.embed_texts([query], input_type="search_query")
        return results[0] if results else []

    async def close(self) -> None:
        """Close the client."""
        if self._client:
            # AsyncClientV2 uses aclose
            await self._client.close()
            self._client = None


# Global embeddings instance
_embeddings_instance: CohereEmbeddings | None = None


def get_embeddings() -> CohereEmbeddings:
    """Get the global embeddings instance (singleton pattern)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = CohereEmbeddings()
    return _embeddings_instance
