"""
Ingestion Models - Data models for document ingestion.

Contains request/response models and domain objects for the ingestion pipeline.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported file types for ingestion."""

    MARKDOWN = "md"
    MARKDOWNX = "mdx"
    TEXT = "txt"


class DocumentStatus(str, Enum):
    """Status of a document during ingestion."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Document(BaseModel):
    """
    Document to be ingested.

    Represents a single file with its metadata and processing state.
    """

    id: UUID = Field(default_factory=uuid4, description="Document identifier")
    file_path: Path = Field(..., description="Absolute path to the file")
    relative_path: str = Field(..., description="Relative path from content root")
    file_type: FileType = Field(..., description="File type extension")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash of content")
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Processing status",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error if processing failed",
    )
    chunk_count: int = Field(default=0, description="Number of chunks created")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "file_path": "/path/to/content/chapter-1.md",
                "relative_path": "chapter-1.md",
                "file_type": "md",
                "file_size": 1024,
                "content_hash": "abc123...",
                "status": "completed",
                "chunk_count": 5,
            }
        }


class Chunk(BaseModel):
    """
    Text chunk for embedding and storage.

    Represents a chunk of text with metadata for vector storage.
    """

    id: UUID = Field(default_factory=uuid4, description="Chunk identifier")
    document_id: UUID = Field(..., description="Source document ID")
    source_id: str = Field(..., description="Human-readable source identifier")
    text: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., ge=0, description="Index within document")
    total_chunks: int = Field(..., ge=1, description="Total chunks in document")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (title, headers, etc.)",
    )

    def to_point_payload(self) -> dict:
        """Convert to Qdrant point payload."""
        return {
            "source_id": self.source_id,
            "document_id": str(self.document_id),
            "text": self.text,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "metadata": self.metadata,
            "content_hash": self.metadata.get("content_hash", ""),
        }


class IngestionErrorType(str, Enum):
    """Types of ingestion errors."""

    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    UNSUPPORTED_FORMAT = "unsupported_format"
    FILE_TOO_LARGE = "file_too_large"
    PARSE_ERROR = "parse_error"
    EMBEDDING_ERROR = "embedding_error"
    STORAGE_ERROR = "storage_error"
    UNKNOWN = "unknown"


class IngestionError(BaseModel):
    """
    Individual ingestion error.

    Represents a single error that occurred during ingestion.
    """

    file_path: str = Field(..., description="Path to the file that failed")
    error_type: IngestionErrorType = Field(..., description="Error category")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "/path/to/file.md",
                "error_type": "unsupported_format",
                "message": "File extension .pdf is not supported",
            }
        }


class IngestionReport(BaseModel):
    """
    Ingestion process report.

    Summary of the entire ingestion process.
    """

    id: UUID = Field(default_factory=uuid4, description="Report identifier")
    source_path: str = Field(..., description="Root path that was ingested")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    total_files: int = Field(default=0, description="Total files found")
    processed_files: int = Field(default=0, description="Files successfully processed")
    skipped_files: int = Field(default=0, description="Files skipped (unsupported type)")
    failed_files: int = Field(default=0, description="Files that failed")
    total_chunks: int = Field(default=0, description="Total chunks created")
    errors: list[IngestionError] = Field(
        default_factory=list,
        description="List of errors encountered",
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.PROCESSING,
        description="Overall status",
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def add_error(self, error: IngestionError) -> None:
        """Add an error to the report."""
        self.errors.append(error)
        self.failed_files += 1

    def to_summary(self) -> dict:
        """Generate a summary dictionary."""
        return {
            "report_id": str(self.id),
            "source_path": self.source_path,
            "status": self.status.value,
            "files": {
                "total": self.total_files,
                "processed": self.processed_files,
                "skipped": self.skipped_files,
                "failed": self.failed_files,
            },
            "chunks": self.total_chunks,
            "duration_seconds": self.duration_seconds,
            "error_count": len(self.errors),
        }

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "source_path": "./content",
                "total_files": 100,
                "processed_files": 95,
                "skipped_files": 3,
                "failed_files": 2,
                "total_chunks": 450,
                "status": "completed",
            }
        }


class IngestionSourceType(str, Enum):
    """Supported source types for ingestion."""

    DIRECTORY = "directory"
    SITEMAP = "sitemap"


class IngestionRequest(BaseModel):
    """
    Request to start ingestion.

    Specifies the source to ingest.
    """

    source_type: IngestionSourceType = Field(
        default=IngestionSourceType.DIRECTORY,
        description="Type of source to ingest (directory or sitemap)",
    )
    path: str = Field(
        ...,
        description="Path to file/directory OR URL to sitemap.xml",
        json_schema_extra={"example": "./content/chapters"},
    )
    recursive: bool = Field(
        default=True,
        description="Recursively process subdirectories (for directory source only)",
    )
    file_types: list[FileType] = Field(
        default=[FileType.MARKDOWN, FileType.MARKDOWNX, FileType.TEXT],
        description="File types to process",
    )
    clear_existing: bool = Field(
        default=False,
        description="Clear existing collection before ingesting",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "path": "./content",
                "recursive": True,
                "file_types": ["md", "mdx", "txt"],
                "clear_existing": False,
            }
        }


class IngestionStatusResponse(BaseModel):
    """
    Response for ingestion status check.

    Returns current status of an ongoing or completed ingestion.
    """

    report_id: UUID = Field(..., description="Report identifier")
    status: DocumentStatus = Field(..., description="Current status")
    progress: dict = Field(..., description="Progress details")
    message: str = Field(default="", description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": {
                    "total": 100,
                    "processed": 45,
                    "percentage": 45.0,
                },
                "message": "Processing file 45 of 100...",
            }
        }
