"""
RAG Generation - Generate answers using LLM with retrieved context.

Implements the core RAG pipeline with citation extraction.
"""

import re
import time
from typing import Optional

import structlog

from src.core.config import get_settings
from src.core.generation import get_llm_client
from src.rag.models import ChatResponse, Citation
from src.rag.retrieval import get_retriever

logger = structlog.get_logger(__name__)

# System prompt template
SYSTEM_PROMPT = """You are a helpful assistant answering questions about book content.
Answer the user's question based ONLY on the provided context when available.
Always cite your sources using the format [source_id].

If the context does not contain relevant information, you may use general knowledge
but you MUST explicitly state that the information is not from the book.

Keep answers concise, helpful, and accurate."""


class RAGGenerator:
    """Generates answers using RAG with context from retrieved chunks."""

    def __init__(self):
        self._llm = get_llm_client()
        self._retriever = get_retriever()

    async def generate_response(
        self,
        question: str,
        context: str,
        chunks: list[dict],
    ) -> ChatResponse:
        """
        Generate a response to the user's question.

        Args:
            question: User's question
            context: Formatted context from retrieval
            chunks: Retrieved chunks with metadata

        Returns:
            ChatResponse with answer and citations
        """
        start_time = time.time()

        # Determine if we have relevant context
        has_relevant_context = len(context) > 100  # Arbitrary threshold
        is_from_book = has_relevant_context

        if has_relevant_context:
            # Generate with context
            answer = await self._llm.generate(
                system_prompt=SYSTEM_PROMPT,
                user_message=question,
                context=context,
                temperature=0.3,
            )
        else:
            # No relevant context - use general knowledge with disclaimer
            disclaimer = "Note: This information is not available in the book.\n\n"
            general_answer = await self._llm.generate(
                system_prompt=SYSTEM_PROMPT,
                user_message=question,
                temperature=0.3,
            )
            answer = disclaimer + general_answer

        # Extract citations from chunks
        citations = self._extract_citations(chunks)

        latency = time.time() - start_time
        logger.info(
            "Generated response",
            has_context=has_relevant_context,
            citations_count=len(citations),
            latency_ms=round(latency * 1000, 2),
        )

        return ChatResponse(
            answer=answer,
            citations=citations,
            is_from_book=is_from_book,
            has_disclaimer=not is_from_book,
        )

    def _extract_citations(self, chunks: list[dict]) -> list[Citation]:
        """Extract citation information from retrieved chunks."""
        citations = []
        seen_sources = set()

        for chunk in chunks:
            payload = chunk.get("payload", {})
            source_id = payload.get("source_id", "unknown")

            # Avoid duplicate citations
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)

            text = payload.get("text", "")[:500]  # Truncate for citation
            location = payload.get("title", "") or payload.get("chapter", "")

            citations.append(Citation(
                source_id=source_id,
                text=text,
                location=location,
            ))

        return citations


# Global generator instance
_generator: Optional[RAGGenerator] = None


def get_rag_generator() -> RAGGenerator:
    """Get the global RAG generator instance."""
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator
