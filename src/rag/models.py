"""
RAG Models - Data models for RAG pipeline.

Contains request/response models and domain objects for the RAG functionality.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ContentSelectionType(str, Enum):
    """Type of content selection scope."""

    PAGE = "page"
    CHAPTER = "chapter"
    RANGE = "range"
    ALL = "all"


class ContentSelection(BaseModel):
    """
    User-defined scope for search queries.

    Defines what portion of the book content should be searched.
    """

    type: ContentSelectionType = Field(
        default=ContentSelectionType.ALL,
        description="Type of content selection",
    )
    source_id: Optional[str] = Field(
        default=None,
        description="Source identifier (page_id, chapter_id, or document_id)",
    )
    start_offset: Optional[int] = Field(
        default=None,
        ge=0,
        description="Start offset for range selection",
    )
    end_offset: Optional[int] = Field(
        default=None,
        ge=0,
        description="End offset for range selection",
    )

    def is_empty(self) -> bool:
        """Check if no specific selection was made."""
        return self.type == ContentSelectionType.ALL and self.source_id is None


class Source(BaseModel):
    """
    Citation source for generated answers.

    Tracks which document chunks were used to generate an answer.
    """

    source_id: str = Field(..., description="Source document identifier")
    chunk_index: int = Field(..., description="Chunk index within the document")
    title: Optional[str] = Field(default=None, description="Source document title")
    excerpt: str = Field(..., description="Relevant excerpt from the source")
    score: float = Field(..., ge=0, le=1, description="Similarity score")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "chapter-1",
                "chunk_index": 3,
                "title": "Introduction to AI",
                "excerpt": "Artificial intelligence (AI) is intelligence...",
                "score": 0.85,
            }
        }


class Citation(BaseModel):
    """Citation with source attribution and text."""

    source_id: str = Field(..., description="Source document ID")
    text: str = Field(..., description="Cited text from source")
    location: str = Field(default="", description="Location hint (page, chapter)")


class ChatRequest(BaseModel):
    """
    Chat request from client.

    Contains the user's question and optional content selection.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question",
        json_schema_extra={"example": "What is the main concept explained here?"},
    )
    content_selection: Optional[ContentSelection] = Field(
        default=None,
        description="Optional content scope for the query",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is machine learning?",
                "content_selection": {
                    "type": "chapter",
                    "source_id": "chapter-3",
                },
            }
        }


class ChatResponse(BaseModel):
    """
    Chat response to client.

    Contains the generated answer and metadata.
    """

    answer: str = Field(..., description="Generated answer to the question")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Sources used to generate the answer",
    )
    is_from_book: bool = Field(
        default=True,
        description="Whether the answer is based on book content",
    )
    has_disclaimer: bool = Field(
        default=False,
        description="Whether a disclaimer was shown for out-of-scope answers",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Machine learning is a subset of AI...",
                "citations": [
                    {
                        "source_id": "chapter-3",
                        "text": "Machine learning is a subset of AI...",
                        "location": "Page 42",
                    }
                ],
                "is_from_book": True,
                "has_disclaimer": False,
            }
        }


class QueryContext(BaseModel):
    """
    Internal context for query processing.

    Contains retrieved chunks and metadata for generation.
    """

    query: str = Field(..., description="Original user query")
    selection: Optional[ContentSelection] = Field(
        default=None,
        description="Applied content selection",
    )
    retrieved_chunks: list[dict] = Field(
        default_factory=list,
        description="Retrieved document chunks",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
