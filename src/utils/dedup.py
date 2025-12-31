"""
Content Hash Deduplication Utility - Detect duplicate content.

Uses SHA-256 hashing to detect identical or near-identical content
before embedding to prevent redundant storage.
"""

import hashlib
from typing import Callable


def compute_content_hash(content: str) -> str:
    """
    Compute SHA-256 hash of content.

    Args:
        content: Text content to hash

    Returns:
        Hexadecimal hash string
    """
    # Normalize whitespace for consistent hashing
    normalized = " ".join(content.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DeduplicationSet:
    """
    Set-like container for tracking seen content hashes.

    Provides O(1) duplicate detection for content ingestion.
    """

    def __init__(self, hash_func: Callable[[str], str] | None = None):
        """
        Initialize the deduplication set.

        Args:
            hash_func: Optional custom hash function
        """
        self._seen: dict[str, str] = {}  # hash -> original content (truncated)
        self._hash_func = hash_func or compute_content_hash

    def is_duplicate(self, content: str) -> bool:
        """
        Check if content has been seen before.

        Args:
            content: Content to check

        Returns:
            True if content is a duplicate
        """
        content_hash = self._hash_func(content)
        return content_hash in self._seen

    def add(self, content: str) -> str:
        """
        Add content to the set and return its hash.

        Args:
            content: Content to add

        Returns:
            Hash of the content
        """
        content_hash = self._hash_func(content)
        self._seen[content_hash] = content[:100]  # Store truncated for debugging
        return content_hash

    def add_if_new(self, content: str) -> tuple[bool, str]:
        """
        Add content only if it's not a duplicate.

        Args:
            content: Content to potentially add

        Returns:
            (is_new, hash) tuple
        """
        content_hash = self._hash_func(content)
        if content_hash in self._seen:
            return False, content_hash
        self._seen[content_hash] = content[:100]
        return True, content_hash

    def clear(self) -> None:
        """Clear all tracked content."""
        self._seen.clear()

    def __len__(self) -> int:
        """Return number of unique items tracked."""
        return len(self._seen)

    def __contains__(self, content: str) -> bool:
        """Check if content is in the set."""
        return self.is_duplicate(content)


def create_deduplication_set() -> DeduplicationSet:
    """Factory function to create a new deduplication set."""
    return DeduplicationSet()
