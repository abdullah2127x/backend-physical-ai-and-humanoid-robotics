"""
Ingestion Service - Main orchestration for document ingestion.

Coordinates file discovery, processing, chunking, embedding, and storage.
"""

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import structlog

from src.core.config import get_settings
from src.core.embeddings import get_embeddings
from src.core.vector import get_qdrant
from src.ingestion.models import (
    Chunk,
    Document,
    DocumentStatus,
    IngestionError,
    IngestionErrorType,
    IngestionReport,
)
from src.ingestion.processors import get_processor
from src.ingestion.validators import scan_directory
from src.utils.chunking import get_chunker

logger = structlog.get_logger(__name__)


class IngestionService:
    """
    Main ingestion service.

    Orchestrates the entire ingestion pipeline:
    1. Scan directory for files
    2. Validate files
    3. Extract text content
    4. Chunk text
    5. Generate embeddings
    6. Store in Qdrant
    """

    def __init__(self):
        self._settings = get_settings()
        self._qdrant = get_qdrant()
        self._embeddings = get_embeddings()
        self._processor = get_processor()
        self._chunker = get_chunker()
        self._reports: dict[UUID, IngestionReport] = {}

    async def ingest(
        self,
        source_path: str,
        recursive: bool = True,
        clear_existing: bool = False,
    ) -> IngestionReport:
        """
        Run the full ingestion pipeline.

        Args:
            source_path: Path to file or directory
            recursive: Scan subdirectories
            clear_existing: Clear Qdrant collection first

        Returns:
            IngestionReport with summary
        """
        report = IngestionReport(
            id=uuid4(),
            source_path=source_path,
            started_at=time.time(),
            status=DocumentStatus.PROCESSING,
        )
        self._reports[report.id] = report

        start_time = time.time()

        try:
            # Convert to Path
            path = Path(source_path).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Path not found: {source_path}")

            # Clear existing if requested
            if clear_existing:
                logger.info("Clearing existing collection")
                try:
                    await self._qdrant.delete_collection()
                    await self._qdrant.ensure_collection()
                except Exception as e:
                    logger.warning("Failed to clear collection", error=str(e))

            # Scan for files
            files = scan_directory(path, recursive=recursive)
            report.total_files = len(files)
            logger.info("Found files to ingest", count=len(files))

            # Process files
            all_chunks: list[Chunk] = []

            for i, file_path in enumerate(files):
                try:
                    # Create document
                    document = self._process_file(file_path, path)
                    if document is None:
                        report.skipped_files += 1
                        continue

                    # Extract content
                    content = self._processor.process(document)

                    # Create chunks
                    chunks = self._create_chunks(document, content)
                    all_chunks.extend(chunks)

                    # Update report
                    report.processed_files += 1
                    report.total_chunks += len(chunks)

                    # Log progress
                    if (i + 1) % 10 == 0:
                        logger.info(
                            "Ingestion progress",
                            processed=i + 1,
                            total=len(files),
                            chunks=len(all_chunks),
                        )

                except Exception as e:
                    error = IngestionError(
                        file_path=str(file_path),
                        error_type=self._map_error_type(e),
                        message=str(e),
                    )
                    report.add_error(error)
                    logger.error("Failed to process file", path=str(file_path), error=str(e))

            # Generate embeddings and store
            if all_chunks:
                logger.info("Generating embeddings", chunks=len(all_chunks))
                await self._embed_and_store(all_chunks)

            # Finalize report
            report.status = DocumentStatus.COMPLETED

        except Exception as e:
            report.status = DocumentStatus.FAILED
            logger.error("Ingestion failed", error=str(e))
            raise

        finally:
            report.completed_at = time.time()

        duration = report.completed_at - report.started_at
        logger.info(
            "Ingestion complete",
            files_processed=report.processed_files,
            chunks=report.total_chunks,
            duration_sec=round(duration, 2),
            errors=len(report.errors),
        )

        return report

    def _process_file(self, file_path: Path, content_root: Path) -> Optional[Document]:
        """Process a single file into a Document."""
        from src.ingestion.validators import create_document, validate_file
        from src.utils.dedup import compute_content_hash

        validation = validate_file(file_path)
        if not validation.is_valid:
            return None

        # Calculate relative path
        try:
            relative_path = str(file_path.relative_to(content_root))
        except ValueError:
            relative_path = str(file_path)

        # Read content for hash
        try:
            content = file_path.read_text(encoding="utf-8")
            content_hash = compute_content_hash(content)
        except Exception:
            content_hash = hashlib.sha256(str(file_path).encode()).hexdigest()

        return Document(
            file_path=file_path,
            relative_path=relative_path,
            file_type=validation.file_type,  # type: ignore
            file_size=file_path.stat().st_size,
            content_hash=content_hash,
            status=DocumentStatus.PENDING,
        )

    def _create_chunks(self, document: Document, content: str) -> list[Chunk]:
        """Create chunks from document content."""
        chunks = []

        # Get source ID from relative path
        source_id = Path(document.relative_path).stem

        # Chunk the content
        chunk_texts = list(self._chunker.chunk_text(content))

        for index, text in enumerate(chunk_texts):
            chunk = Chunk(
                id=uuid4(),
                document_id=document.id,
                source_id=source_id,
                text=text,
                chunk_index=index,
                total_chunks=len(chunk_texts),
                metadata={
                    "file_path": str(document.file_path),
                    "relative_path": document.relative_path,
                    "file_type": document.file_type.value,
                    "content_hash": document.content_hash,
                },
            )
            chunks.append(chunk)

        logger.debug(
            "Created chunks",
            file=document.relative_path,
            chunks=len(chunks),
        )

        return chunks

    async def _embed_and_store(self, chunks: list[Chunk]) -> None:
        """Generate embeddings and store in Qdrant."""
        from qdrant_client.models import PointStruct

        # Extract texts for embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings in batches
        embeddings = await self._embeddings.embed_texts(texts)

        # Create points
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point = PointStruct(
                id=str(chunk.id),
                vector=embedding,
                payload=chunk.to_point_payload(),
            )
            points.append(point)

        # Upsert to Qdrant
        await self._qdrant.upsert_points(points)

        logger.info("Stored chunks in Qdrant", count=len(points))

    def _map_error_type(self, error: Exception) -> IngestionErrorType:
        """Map exception to error type."""
        error_msg = str(error).lower()

        if "not found" in error_msg:
            return IngestionErrorType.FILE_NOT_FOUND
        elif "permission" in error_msg:
            return IngestionErrorType.PERMISSION_DENIED
        elif "unsupported" in error_msg or "format" in error_msg:
            return IngestionErrorType.UNSUPPORTED_FORMAT
        elif "too large" in error_msg or "size" in error_msg:
            return IngestionErrorType.FILE_TOO_LARGE
        elif "parse" in error_msg or "read" in error_msg:
            return IngestionErrorType.PARSE_ERROR
        elif "embedding" in error_msg:
            return IngestionErrorType.EMBEDDING_ERROR
        elif "storage" in error_msg or "qdrant" in error_msg:
            return IngestionErrorType.STORAGE_ERROR

        return IngestionErrorType.UNKNOWN

    def get_report(self, report_id: UUID) -> Optional[IngestionReport]:
        """Get a report by ID."""
        return self._reports.get(report_id)


# Global service instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """Get the global ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service
