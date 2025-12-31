"""
Chat API Endpoints - REST API for chat operations.

Provides endpoints for session management and question answering.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import UUID4

from src.chat.models import (
    MessageRole,
    SessionCreateResponse,
    SessionHistoryResponse,
)
from src.chat.service import get_session_service
from src.core.generation import get_llm_client
from src.rag.fallback import get_fallback_handler
from src.rag.models import ChatRequest, ChatResponse
from src.rag.retrieval import get_retriever

router = APIRouter()


@router.post(
    "/start",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new chat session",
    description="Creates a new conversation session and returns the session ID.",
)
async def start_session() -> SessionCreateResponse:
    """
    Start a new chat session.

    Returns:
        SessionCreateResponse with session ID and timestamps
    """
    session_service = get_session_service()
    session = session_service.create_session()

    return SessionCreateResponse(
        session_id=session.id,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


@router.post(
    "/send/{session_id}",
    response_model=ChatResponse,
    summary="Send a message to a session",
    description="Ask a question and receive an answer based on book content.",
)
async def send_message(
    session_id: UUID4,
    request: ChatRequest,
) -> ChatResponse:
    """
    Send a question to an existing session.

    Args:
        session_id: Session to send message to
        request: Chat request with question and optional content selection

    Returns:
        ChatResponse with answer and citations
    """
    session_service = get_session_service()

    # Verify session exists
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Save user message
    session_service.add_message(
        session_id=session_id,
        role=MessageRole.USER,
        content=request.question,
    )

    # Retrieve relevant context
    retriever = get_retriever()
    context, chunks = await retriever.retrieve_with_citations(
        query=request.question,
        selection=request.content_selection,
    )

    # Generate response
    if chunks:
        # Use RAG with context
        from src.rag.generation import get_rag_generator

        generator = get_rag_generator()
        response = await generator.generate_response(
            question=request.question,
            context=context,
            chunks=chunks,
        )
    else:
        # No context found - use fallback
        llm = get_llm_client()
        fallback = get_fallback_handler()

        # Try to provide a general answer
        try:
            general_answer = await llm.generate(
                system_prompt="You are a helpful assistant. Answer the question helpfully.",
                user_message=request.question,
                temperature=0.3,
            )
            response = fallback.get_fallback_response(
                question=request.question,
                general_answer=general_answer,
            )
        except Exception:
            # LLM also failed - return simple fallback
            response = fallback.get_fallback_response(question=request.question)

    # Save assistant message
    citation_ids = [c.source_id for c in response.citations]
    session_service.add_message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=response.answer,
        citations=citation_ids,
        is_from_book=response.is_from_book,
    )

    return response


@router.get(
    "/history/{session_id}",
    response_model=SessionHistoryResponse,
    summary="Get conversation history",
    description="Retrieve the full conversation history for a session.",
)
async def get_history(session_id: UUID4) -> SessionHistoryResponse:
    """
    Get the conversation history for a session.

    Args:
        session_id: Session to get history for

    Returns:
        SessionHistoryResponse with messages
    """
    session_service = get_session_service()

    # Verify session exists
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    history = session_service.get_history(session_id)

    return SessionHistoryResponse(
        session_id=session_id,
        messages=history,
        total_messages=len(history),
    )


@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a session",
    description="Permanently delete a chat session and its history.",
)
async def delete_session(session_id: UUID4) -> None:
    """
    Delete a chat session.

    Args:
        session_id: Session to delete
    """
    session_service = get_session_service()
    deleted = session_service.delete_session(session_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )
