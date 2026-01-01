"""
File Validators - Validate files before ingestion.

Checks file type, size, and accessibility.
"""

import os
from pathlib import Path
from typing import Optional

import structlog

from src.core.config import get_settings
from src.ingestion.models import Document, DocumentStatus, FileType

logger = structlog.get_logger(__name__)

# Maximum file size (10MB as per constitution)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported file extensions
SUPPORTED_EXTENSIONS = {ext.value for ext in FileType}


class ValidationResult:
    """Result of file validation."""

    def __init__(
        self,
        is_valid: bool,
        file_type: Optional[FileType] = None,
        error_message: Optional[str] = None,
    ):
        self.is_valid = is_valid
        self.file_type = file_type
        self.error_message = error_message

    @classmethod
    def valid(cls, file_type: FileType) -> "ValidationResult":
        """Create a valid result."""
        return cls(is_valid=True, file_type=file_type)

    @classmethod
    def invalid(cls, message: str) -> "ValidationResult":
        """Create an invalid result."""
        return cls(is_valid=False, error_message=message)


def validate_file(file_path: Path) -> ValidationResult:
    """
    Validate a single file for ingestion.

    Args:
        file_path: Path to the file

    Returns:
        ValidationResult with success/failure info
    """
    # Check if file exists
    if not file_path.exists():
        return ValidationResult.invalid(f"File not found: {file_path}")

    # Check if it's a file (not a directory)
    if not file_path.is_file():
        return ValidationResult.invalid(f"Path is not a file: {file_path}")

    # Check file extension
    extension = file_path.suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        return ValidationResult.invalid(
            f"Unsupported file format: '.{extension}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Map extension to FileType
    file_type_map = {
        "md": FileType.MARKDOWN,
        "mdx": FileType.MARKDOWNX,
        "txt": FileType.TEXT,
    }
    file_type = file_type_map.get(extension, FileType.TEXT)

    # Check file size
    try:
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            return ValidationResult.invalid(
                f"File exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit: "
                f"{file_path.name} ({size_mb:.1f}MB)"
            )
    except OSError as e:
        return ValidationResult.invalid(f"Cannot read file size: {e}")

    # Check read permission
    if not os.access(file_path, os.R_OK):
        return ValidationResult.invalid(f"File is not readable: {file_path}")

    return ValidationResult.valid(file_type)


def create_document(file_path: Path, content_root: Path) -> Optional[Document]:
    """
    Create a Document from a validated file path.

    Args:
        file_path: Path to the file
        content_root: Root path for calculating relative paths

    Returns:
        Document if validation passes, None otherwise
    """
    from src.utils.dedup import compute_content_hash

    validation = validate_file(file_path)
    if not validation.is_valid:
        logger.warning("File validation failed", path=str(file_path), error=validation.error_message)
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
    except Exception as e:
        logger.error("Failed to read file for hashing", path=str(file_path), error=str(e))
        content_hash = ""

    return Document(
        file_path=file_path,
        relative_path=relative_path,
        file_type=validation.file_type,  # type: ignore
        file_size=file_path.stat().st_size,
        content_hash=content_hash,
        status=DocumentStatus.PENDING,
    )


def scan_directory(
    path: Path,
    recursive: bool = True,
    file_types: Optional[list[FileType]] = None,
) -> list[Path]:
    """
    Scan a directory for files to ingest.

    Args:
        path: Root directory to scan
        recursive: Whether to scan subdirectories
        file_types: Optional list of file types to include

    Returns:
        List of valid file paths
    """
    settings = get_settings()
    valid_files: list[Path] = []

    if not path.exists():
        logger.warning("Path does not exist", path=str(path))
        return valid_files

    if not path.is_dir():
        # Single file
        validation = validate_file(path)
        if validation.is_valid:
            valid_files.append(path)
        return valid_files

    # Determine which extensions to include
    if file_types is None:
        file_types = list(FileType)
    extensions = {ft.value for ft in file_types}

    # Walk directory
    for root, dirs, files in os.walk(path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for filename in files:
            file_path = Path(root) / filename
            validation = validate_file(file_path)

            if validation.is_valid and validation.file_type in file_types:  # type: ignore
                valid_files.append(file_path)

        # Stop if not recursive
        if not recursive:
            break

    logger.info(
        "Scanned directory",
        path=str(path),
        recursive=recursive,
        files_found=len(valid_files),
    )

    return valid_files
