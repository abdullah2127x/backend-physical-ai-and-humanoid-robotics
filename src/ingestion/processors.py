"""
Content Processors - Extract text from files.

Handles Markdown and plain text file processing.
"""

import re
from pathlib import Path
from typing import Optional

import structlog

from src.ingestion.models import Document, FileType

logger = structlog.get_logger(__name__)


class ContentProcessor:
    """Base class for content processors."""

    def can_process(self, file_type: FileType) -> bool:
        """Check if processor can handle the file type."""
        raise NotImplementedError

    def process(self, document: Document) -> str:
        """
        Extract text content from a document.

        Args:
            document: Document to process

        Returns:
            Extracted text content
        """
        raise NotImplementedError


class MarkdownProcessor(ContentProcessor):
    """Processor for Markdown files."""

    def can_process(self, file_type: FileType) -> bool:
        return file_type in (FileType.MARKDOWN, FileType.MARKDOWNX)

    def process(self, document: Document) -> str:
        """
        Extract text from Markdown file.

        Preserves structure for better chunking.
        """
        try:
            content = document.file_path.read_text(encoding="utf-8")

            # Remove frontmatter (YAML/TOML)
            content = self._strip_frontmatter(content)

            # Normalize line endings
            content = content.replace("\r\n", "\n")

            # Remove excessive whitespace
            lines = content.split("\n")
            cleaned_lines = []
            for line in lines:
                # Keep headers as they provide structure
                if line.strip():
                    cleaned_lines.append(line.rstrip())

            return "\n".join(cleaned_lines)

        except Exception as e:
            logger.error(
                "Failed to process markdown file",
                path=str(document.file_path),
                error=str(e),
            )
            raise

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from markdown."""
        # Match --- at start of file
        if content.startswith("---"):
            # Find the closing ---
            match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                return content[match.end() :]
        return content


class TextProcessor(ContentProcessor):
    """Processor for plain text files."""

    def can_process(self, file_type: FileType) -> bool:
        return file_type == FileType.TEXT

    def process(self, document: Document) -> str:
        """Extract text from plain text file."""
        try:
            return document.file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(
                "Failed to process text file",
                path=str(document.file_path),
                error=str(e),
            )
            raise


class ContentProcessorFactory:
    """Factory for creating content processors."""

    def __init__(self):
        self._processors: list[ContentProcessor] = [
            MarkdownProcessor(),
            TextProcessor(),
        ]

    def get_processor(self, file_type: FileType) -> Optional[ContentProcessor]:
        """Get processor for file type."""
        for processor in self._processors:
            if processor.can_process(file_type):
                return processor
        return None

    def process(self, document: Document) -> str:
        """
        Process a document and extract text.

        Args:
            document: Document to process

        Returns:
            Extracted text content

        Raises:
            ValueError: If no processor found for file type
        """
        processor = self.get_processor(document.file_type)
        if processor is None:
            raise ValueError(f"No processor for file type: {document.file_type}")

        return processor.process(document)


# Global factory instance
_processor_factory: Optional[ContentProcessorFactory] = None


def get_processor() -> ContentProcessorFactory:
    """Get the global processor factory."""
    global _processor_factory
    if _processor_factory is None:
        _processor_factory = ContentProcessorFactory()
    return _processor_factory
