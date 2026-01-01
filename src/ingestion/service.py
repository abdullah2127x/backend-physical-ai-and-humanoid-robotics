"""
Ingestion Service - Main orchestration for document ingestion.

Coordinates file discovery, processing, chunking, embedding, and storage.
"""

import asyncio
import hashlib
import time
from datetime import datetime
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
    IngestionSourceType,
)
from src.crawler.sitemap import fetch_sitemap_urls
from src.crawler.scraper import scrape_batch
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
        source_type: IngestionSourceType = IngestionSourceType.DIRECTORY,
        recursive: bool = True,
        clear_existing: bool = False,
        report_id: Optional[UUID] = None,
    ) -> IngestionReport:
        """
        Run the full ingestion pipeline.

        Args:
            source_path: Path to file or directory OR URL to sitemap
            source_type: Type of source (directory or sitemap)
            recursive: Scan subdirectories (directory mode only)
            clear_existing: Clear Qdrant collection first
            report_id: Optional existing report ID to use/update

        Returns:
            IngestionReport with summary
        """
        # Use existing report or create new one
        if report_id and report_id in self._reports:
            report = self._reports[report_id]
            report.started_at = datetime.utcnow()
            report.status = DocumentStatus.PROCESSING
        else:
            report = IngestionReport(
                id=report_id or uuid4(),
                source_path=source_path,
                started_at=datetime.utcnow(),
                status=DocumentStatus.PROCESSING,
            )
            self._reports[report.id] = report

        start_time = time.time()

        try:
            # Clear existing if requested
            if clear_existing:
                logger.info("Clearing existing collection")
                try:
                    await self._qdrant.delete_collection()
                except Exception as e:
                    logger.warning("Failed to clear collection", error=str(e))

            # Ensure collection exists
            await self._qdrant.ensure_collection()

            if source_type == IngestionSourceType.SITEMAP:
                await self._ingest_sitemap(source_path, report)
            else:
                await self._ingest_directory(source_path, recursive, report)

            # Finalize report
            report.status = DocumentStatus.COMPLETED

        except Exception as e:
            report.status = DocumentStatus.FAILED
            logger.error("Ingestion failed", error=str(e))
            raise

        finally:
            report.completed_at = datetime.utcnow()

        start_ts = report.started_at
        if hasattr(start_ts, "timestamp"):
            start_ts = start_ts.timestamp()

        duration = report.completed_at.timestamp() - start_ts
        logger.info(
            "Ingestion complete",
            files_processed=report.processed_files,
            chunks=report.total_chunks,
            duration_sec=round(duration, 2),
            errors=len(report.errors),
        )

        return report

    async def _ingest_directory(self, source_path: str, recursive: bool, report: IngestionReport) -> None:
        """Process files from a local directory."""
        path = Path(source_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {source_path}")

        files = scan_directory(path, recursive=recursive)
        report.total_files = len(files)
        logger.info("found_files_to_ingest", count=len(files))

        for i, file_path in enumerate(files):
            try:
                document = self._process_file(file_path, path)
                if document is None:
                    report.skipped_files += 1
                    continue

                content = self._processor.process(document)
                chunks = self._create_chunks(document, content)

                if chunks:
                    await self._embed_and_store(chunks)

                report.processed_files += 1
                report.total_chunks += len(chunks)

                if (i + 1) % 5 == 0:
                    logger.info("ingestion_progress", processed=i+1, total=len(files), chunks=report.total_chunks)
            except Exception as e:
                report.add_error(IngestionError(file_path=str(file_path), error_type=self._map_error_type(e), message=str(e)))

    async def _ingest_sitemap(self, sitemap_url: str, report: IngestionReport) -> None:
        """Process content from a sitemap.xml."""
        logger.info("fetching_sitemap", url=sitemap_url)
        urls = await fetch_sitemap_urls(sitemap_url)
        report.total_files = len(urls)
        logger.info("found_urls_to_scrape", count=len(urls))

        # Process in batches of 5 to avoid overloading
        for i in range(0, len(urls), 5):
            batch_urls = urls[i:i+5]
            scraped_data = await scrape_batch(batch_urls)

            for url, content in scraped_data.items():
                try:
                    # Create a virtual document for the URL
                    source_id = url.split("/")[-1] or "index"
                    doc_id = uuid4()

                    # Create chunks directly for the scraped text
                    chunk_texts = list(self._chunker.chunk_text(content))
                    chunks = []
                    for idx, text in enumerate(chunk_texts):
                        chunks.append(Chunk(
                            id=uuid4(), document_id=doc_id, source_id=source_id,
                            text=text, chunk_index=idx, total_chunks=len(chunk_texts),
                            metadata={"url": url, "source_type": "sitemap"}
                        ))

                    if chunks:
                        await self._embed_and_store(chunks)

                    report.processed_files += 1
                    report.total_chunks += len(chunks)
                except Exception as e:
                    report.add_error(IngestionError(file_path=url, error_type=self._map_error_type(e), message=str(e)))

            logger.info("sitemap_progress", processed=min(i+5, len(urls)), total=len(urls), chunks=report.total_chunks)

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

        # Ensure we are connected to Qdrant
        if self._qdrant._client is None:
            await self._qdrant.connect()

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
