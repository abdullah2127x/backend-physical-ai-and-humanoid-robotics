"""
Chat Models - Data models for chat session management.

Contains session and message models for conversation tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """
    Individual message in a conversation.

    Represents a single exchange (user question or system answer).
    """

    id: UUID = Field(default_factory=uuid4, description="Message identifier")
    role: MessageRole = Field(..., description="Sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    citations: list[str] = Field(
        default_factory=list,
        description="Citation source IDs used in this message",
    )
    is_from_book: bool = Field(
        default=True,
        description="Whether message is based on book content",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "Machine learning is a subset of AI...",
                "timestamp": "2025-12-31T10:00:00Z",
                "citations": ["chapter-3"],
                "is_from_book": True,
            }
        }


class SessionStatus(str, Enum):
    """Status of the chat session."""

    ACTIVE = "active"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class Session(BaseModel):
    """
    Chat session for conversation continuity.

    Tracks a single user conversation with message history.
    """

    id: UUID = Field(default_factory=uuid4, description="Session identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(..., description="Session expiration time")
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Session status",
    )
    messages: list[Message] = Field(
        default_factory=list,
        description="Conversation messages",
    )
    total_messages: int = Field(default=0, description="Total message count")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-12-31T10:00:00Z",
                "updated_at": "2025-12-31T10:05:00Z",
                "expires_at": "2025-12-31T10:05:00Z",
                "status": "active",
                "messages": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "role": "user",
                        "content": "What is machine learning?",
                        "timestamp": "2025-12-31T10:00:00Z",
                    }
                ],
                "total_messages": 1,
            }
        }

    def add_message(self, message: Message) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self.total_messages = len(self.messages)

    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

    def to_history(self) -> list[dict]:
        """Convert messages to chat history format."""
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in self.messages
        ]


class SessionCreateResponse(BaseModel):
    """Response when creating a new session."""

    session_id: UUID = Field(..., description="New session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-12-31T10:00:00Z",
                "expires_at": "2025-12-31T10:00:00Z",
            }
        }


class SessionHistoryResponse(BaseModel):
    """Response containing session history."""

    session_id: UUID = Field(..., description="Session identifier")
    messages: list[dict] = Field(..., description="Conversation history")
    total_messages: int = Field(..., description="Total message count")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is machine learning?",
                        "timestamp": "2025-12-31T10:00:00Z",
                    }
                ],
                "total_messages": 1,
            }
        }
