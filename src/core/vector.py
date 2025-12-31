"""
Qdrant Client Wrapper - Async vector database operations for RAG.

Provides async wrapper around qdrant-client for vector storage and retrieval.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import structlog
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.models import (
    Batch,
    Distance,
    PointStruct,
    VectorParams,
)

from .config import get_settings

logger = structlog.get_logger(__name__)


class QdrantWrapper:
    """Async wrapper for Qdrant vector database operations."""

    def __init__(self):
        self._client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None
        self._settings = get_settings()
        self._collection_name = self._settings.qdrant_collection_name

    async def connect(self) -> None:
        """Establish connection to Qdrant Cloud."""
        try:
            self._client = AsyncQdrantClient(
                url=self._settings.qdrant_url,
                api_key=self._settings.qdrant_api_key,
            )
            self._sync_client = QdrantClient(
                url=self._settings.qdrant_url,
                api_key=self._settings.qdrant_api_key,
            )
            logger.info("Connected to Qdrant", collection=self._collection_name)
        except Exception as e:
            logger.error("Failed to connect to Qdrant", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close connection to Qdrant."""
        if self._client:
            await self._client.close()
        if self._sync_client:
            self._sync_client.close()
        self._client = None
        self._sync_client = None
        logger.info("Disconnected from Qdrant")

    async def ensure_collection(self, vector_size: int = 1024) -> None:
        """Ensure the collection exists with proper configuration."""
        if self._client is None:
            raise RuntimeError("Not connected to Qdrant")

        # Check if collection exists
        collections = await self._client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if self._collection_name not in collection_names:
            # Create collection with vector configuration
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created collection", collection=self._collection_name)
        else:
            logger.info("Collection already exists", collection=self._collection_name)

    async def upsert_points(
        self,
        points: list[PointStruct],
        batch_size: int = 100,
    ) -> None:
        """Upsert points into the collection."""
        if self._client is None:
            raise RuntimeError("Not connected to Qdrant")

        # Process in batches
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await self._client.upsert(
                collection_name=self._collection_name,
                points=batch,
            )
            logger.debug("Upserted batch", batch_size=len(batch))

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        if self._client is None:
            raise RuntimeError("Not connected to Qdrant")

        try:
            results = await self._client.query_points(
                collection_name=self._collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )

            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results.points
            ]
        except Exception as e:
            # Collection doesn't exist or other error - return empty results
            logger.warning("Search failed, returning empty results", error=str(e))
            return []

    async def delete_collection(self) -> None:
        """Delete the collection (use with caution)."""
        if self._client is None:
            raise RuntimeError("Not connected to Qdrant")

        await self._client.delete_collection(collection_name=self._collection_name)
        logger.info("Deleted collection", collection=self._collection_name)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator["QdrantWrapper", None]:
        """Context manager for connection lifecycle."""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()


# Global wrapper instance
_qdrant_wrapper: Optional[QdrantWrapper] = None


def get_qdrant() -> QdrantWrapper:
    """Get the global Qdrant wrapper instance (singleton pattern)."""
    global _qdrant_wrapper
    if _qdrant_wrapper is None:
        _qdrant_wrapper = QdrantWrapper()
    return _qdrant_wrapper


async def init_qdrant() -> QdrantWrapper:
    """Initialize Qdrant connection and ensure collection exists."""
    qdrant = get_qdrant()
    await qdrant.connect()
    await qdrant.ensure_collection()
    return qdrant
