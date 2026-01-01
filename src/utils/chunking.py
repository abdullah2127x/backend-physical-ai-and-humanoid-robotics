"""
Text Chunking Utility - Split text into overlapping chunks.

Implements token-based chunking with configurable size and overlap
for optimal RAG retrieval performance.
"""

import re
from collections.abc import Iterator


class TextChunker:
    """
    Token-based text chunker with overlap support.

    Uses a simple whitespace-based tokenizer for estimating token counts.
    """

    # Approximate characters per token (English text)
    CHARS_PER_TOKEN = 4

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100,
    ):
        """
        Initialize the chunker.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            min_chunk_size: Minimum chunk size in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words (whitespace-based)."""
        # Split on whitespace and filter empty strings
        return re.findall(r'\b\w+\b', text.lower())

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimate: ~4 characters per token
        return len(text) // self.CHARS_PER_TOKEN

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences while preserving structure."""
        # Split on common sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> Iterator[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Yields:
            Text chunks
        """
        if not text or not text.strip():
            return

        # Handle very short texts
        estimated_tokens = self._estimate_tokens(text)
        if estimated_tokens <= self.chunk_size:
            yield text.strip()
            return

        sentences = self._split_into_sentences(text)
        if not sentences:
            # Fallback: split by whitespace
            sentences = text.split()

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_size = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If adding this sentence exceeds chunk size
            if current_size + sentence_tokens > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk).strip()
                    if self._estimate_tokens(chunk_text) >= self.min_chunk_size:
                        chunks.append(chunk_text)

                # Start new chunk with overlap
                if self.chunk_overlap > 0 and chunks:
                    # Get last overlap_size sentences from previous chunk
                    overlap_text = chunks[-1]
                    overlap_sentences = self._split_into_sentences(overlap_text)
                    current_chunk = overlap_sentences[-self.chunk_overlap:] if self.chunk_overlap > 0 else []
                    current_size = sum(self._estimate_tokens(s) for s in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_tokens

        # Yield remaining chunks
        for i, chunk in enumerate(chunks):
            yield chunk

        # Final chunk
        if current_chunk:
            final_chunk = " ".join(current_chunk).strip()
            if final_chunk and final_chunk != chunks[-1] if chunks else True:
                if self._estimate_tokens(final_chunk) >= self.min_chunk_size:
                    yield final_chunk

    def chunk_documents(
        self,
        documents: list[tuple[str, dict]],
    ) -> Iterator[tuple[str, dict]]:
        """
        Chunk multiple documents with metadata.

        Args:
            documents: List of (text, metadata) tuples

        Yields:
            (chunk_text, metadata) tuples with chunk_index added to metadata
        """
        for doc_text, metadata in documents:
            source_id = metadata.get("source_id", "unknown")
            chunks = list(self.chunk_text(doc_text))

            for chunk_index, chunk in enumerate(chunks):
                chunk_metadata = {
                    **metadata,
                    "chunk_index": chunk_index,
                    "total_chunks": len(chunks),
                }
                yield chunk, chunk_metadata


# Global chunker instance
_chunker: TextChunker | None = None


def get_chunker(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> TextChunker:
    """Get the global chunker instance with optional overrides."""
    global _chunker
    if _chunker is None:
        from src.core.config import get_settings

        settings = get_settings()
        _chunker = TextChunker(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )

    if chunk_size is not None:
        _chunker.chunk_size = chunk_size
    if chunk_overlap is not None:
        _chunker.chunk_overlap = chunk_overlap

    return _chunker
