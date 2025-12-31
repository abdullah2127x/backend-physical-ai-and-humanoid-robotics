"""
Fallback Response Handler - Generate responses when no context is found.

Provides helpful responses when RAG retrieval returns no relevant chunks.
"""

from typing import Optional

from src.rag.models import ChatResponse


class FallbackHandler:
    """Handles responses when no book content matches the query."""

    FALLBACK_MESSAGE = (
        "I couldn't find specific information about that in the book. "
        "Would you like me to provide a general answer based on common knowledge, "
        "or would you like to rephrase your question?"
    )

    GENERAL_ANSWER_PREFIX = (
        "Note: This information is not available in the book.\n\n"
    )

    def get_fallback_response(
        self,
        question: str,
        general_answer: Optional[str] = None,
    ) -> ChatResponse:
        """
        Generate a fallback response when no context is found.

        Args:
            question: User's original question
            general_answer: Optional general knowledge answer

        Returns:
            ChatResponse with fallback message
        """
        if general_answer:
            answer = self.GENERAL_ANSWER_PREFIX + general_answer
        else:
            answer = self.FALLBACK_MESSAGE

        return ChatResponse(
            answer=answer,
            citations=[],
            is_from_book=False,
            has_disclaimer=True,
        )

    def get_no_results_message(self, question: str) -> str:
        """Get a message when search returns no results."""
        return (
            f"I couldn't find any content related to '{question[:100]}' in the book. "
            "This could mean:\n"
            "1. The topic isn't covered in the book\n"
            "2. Try using different keywords\n"
            "3. Check if you have the right content selected"
        )

    def get_out_of_scope_message(self, question: str) -> str:
        """Get a message for out-of-scope questions."""
        return (
            "That's outside the scope of the book's content. "
            "I can only answer questions about what's covered in the book. "
            "Would you like me to rephrase my answer using general knowledge instead?"
        )


# Global fallback handler instance
_fallback_handler: Optional[FallbackHandler] = None


def get_fallback_handler() -> FallbackHandler:
    """Get the global fallback handler instance."""
    global _fallback_handler
    if _fallback_handler is None:
        _fallback_handler = FallbackHandler()
    return _fallback_handler
