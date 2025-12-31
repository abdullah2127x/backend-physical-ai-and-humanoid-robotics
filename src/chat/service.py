"""
Chat Session Service - Manage conversation sessions and messages.

Handles session lifecycle, message storage, and history retrieval.
"""

import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

import structlog

from src.core.config import get_settings
from src.chat.models import Message, MessageRole, Session, SessionStatus

logger = structlog.get_logger(__name__)


class SessionService:
    """Service for managing chat sessions."""

    def __init__(self):
        self._settings = get_settings()
        # In-memory session storage (replace with DB for production)
        self._sessions: dict[UUID, Session] = {}

    def create_session(self) -> Session:
        """Create a new chat session."""
        settings = get_settings()
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=settings.session_timeout_hours)

        session = Session(
            id=uuid4(),
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            status=SessionStatus.ACTIVE,
            messages=[],
            total_messages=0,
        )

        self._sessions[session.id] = session
        logger.info("Created session", session_id=str(session.id))
        return session

    def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)

        if session and session.is_expired():
            session.status = SessionStatus.EXPIRED
            logger.info("Session expired", session_id=str(session_id))
            return None

        return session

    def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        citations: Optional[list[str]] = None,
        is_from_book: bool = True,
    ) -> Message:
        """
        Add a message to a session.

        Args:
            session_id: Session to add message to
            role: Message sender role
            content: Message content
            citations: Optional list of source IDs
            is_from_book: Whether message is based on book content

        Returns:
            Created message
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Check message limit
        settings = get_settings()
        if len(session.messages) >= settings.session_max_messages:
            logger.warning(
                "Session message limit reached",
                session_id=str(session_id),
                limit=settings.session_max_messages,
            )
            raise ValueError("Session message limit exceeded")

        message = Message(
            id=uuid4(),
            role=role,
            content=content,
            citations=citations or [],
            is_from_book=is_from_book,
        )

        session.add_message(message)
        logger.info(
            "Added message",
            session_id=str(session_id),
            role=role.value,
            message_id=str(message.id),
        )

        return message

    def get_history(self, session_id: UUID) -> list[dict]:
        """Get conversation history for a session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        return session.to_history()

    def delete_session(self, session_id: UUID) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Deleted session", session_id=str(session_id))
            return True
        return False

    def list_sessions(self) -> list[Session]:
        """List all active sessions."""
        return [
            s for s in self._sessions.values()
            if s.status == SessionStatus.ACTIVE and not s.is_expired()
        ]

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count of cleaned sessions."""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]

        for sid in expired_ids:
            self._sessions[sid].status = SessionStatus.EXPIRED
            del self._sessions[sid]

        if expired_ids:
            logger.info("Cleaned up expired sessions", count=len(expired_ids))

        return len(expired_ids)


# Global service instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Get the global session service instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
