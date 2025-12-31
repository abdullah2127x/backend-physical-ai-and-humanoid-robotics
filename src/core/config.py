"""
Pydantic Settings - Environment configuration for RAG Chatbot Backend.
Loads configuration from .env file with environment variable overrides.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Settings
    app_host: str = Field(default="0.0.0.0", description="Host to bind the server to")
    app_port: int = Field(default=8000, ge=1, le=65535, description="Port to bind the server to")
    app_debug: bool = Field(default=False, description="Enable debug mode")
    app_log_level: str = Field(default="info", description="Logging level")

    # Qdrant Vector Database
    qdrant_url: str = Field(description="Qdrant Cloud URL")
    qdrant_api_key: str = Field(default="", description="Qdrant API key")
    qdrant_collection_name: str = Field(default="book_content", description="Collection name for embeddings")

    # Cohere Embeddings
    cohere_api_key: str = Field(default="", description="Cohere API key")
    cohere_embedding_model: str = Field(default="embed-english-v3.0", description="Embedding model name")
    cohere_embedding_batch_size: int = Field(default=96, ge=1, le=500, description="Batch size for embedding calls")

    # LiteLLM / OpenRouter
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    litellm_model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    litellm_api_base: str = Field(default="https://openrouter.ai/api/v1", description="API base URL")
    litellm_timeout: float = Field(default=30.0, ge=1.0, description="Timeout for LLM calls in seconds")
    litellm_max_tokens: int = Field(default=1000, ge=1, description="Maximum tokens in generated response")

    # RAG Configuration
    rag_similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score for retrieval"
    )
    rag_max_chunks: int = Field(default=10, ge=1, description="Maximum number of chunks to retrieve")
    rag_chunk_size: int = Field(default=500, ge=50, description="Target size of text chunks in tokens")
    rag_chunk_overlap: int = Field(default=50, ge=0, description="Overlap between chunks in tokens")
    rag_response_cache_ttl: int = Field(
        default=3600, ge=0, description="Cache TTL for responses in seconds"
    )

    # Session Configuration
    session_timeout_hours: int = Field(default=24, ge=1, description="Session timeout in hours")
    session_max_messages: int = Field(default=100, ge=1, description="Maximum messages per session")

    # Content Paths
    content_root_path: str = Field(default="./content", description="Root path for content files")
    ingestion_chunk_size: str = Field(default="200-500", description="Chunk size range for ingestion")

    # Performance & Limits
    max_concurrent_requests: int = Field(default=100, ge=1, description="Maximum concurrent requests")
    max_request_body_size: int = Field(
        default=10 * 1024 * 1024, ge=1, description="Maximum request body size in bytes"
    )

    @field_validator("ingestion_chunk_size")
    @classmethod
    def parse_chunk_size_range(cls, v: str) -> str:
        """Validate chunk size range format (e.g., '200-500')."""
        try:
            parts = v.split("-")
            if len(parts) != 2:
                raise ValueError("Must be in format 'min-max'")
            min_size, max_size = int(parts[0]), int(parts[1])
            if min_size < 50 or max_size > 2000:
                raise ValueError("Chunk size must be between 50-2000 tokens")
            if min_size >= max_size:
                raise ValueError("Min must be less than max")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid chunk size range '{v}': {e}") from e
        return v

    @property
    def content_root(self) -> Path:
        """Get the absolute path to the content root directory."""
        return Path(self.content_root_path).resolve()

    @property
    def chunk_size_tuple(self) -> tuple[int, int]:
        """Parse chunk size range into (min, max) tuple."""
        min_size, max_size = self.ingestion_chunk_size.split("-")
        return int(min_size), int(max_size)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment (useful for testing)."""
    global _settings
    _settings = Settings()
    return _settings
