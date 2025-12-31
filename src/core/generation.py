"""
LiteLLM/OpenRouter Client - LLM generation for RAG responses.

Provides unified interface for LLM calls via LiteLLM with OpenRouter.
"""

import time
from typing import Optional

import structlog
from litellm import acompletion

from .config import get_settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """LiteLLM wrapper for LLM generation with OpenRouter."""

    def __init__(self):
        self._settings = get_settings()
        self._model = self._settings.litellm_model
        self._api_base = self._settings.litellm_api_base
        self._timeout = self._settings.litellm_timeout
        self._max_tokens = self._settings.litellm_max_tokens

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        context: Optional[str] = None,
    ) -> str:
        """
        Generate a response using the LLM.

        Args:
            system_prompt: System prompt defining the AI's behavior
            user_message: User's message/question
            temperature: Response creativity (0.0-1.0)
            context: Optional context from RAG retrieval

        Returns:
            Generated response text
        """
        start_time = time.time()

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {user_message}",
            })
        else:
            messages.append({"role": "user", "content": user_message})

        try:
            response = await acompletion(
                model=self._model,
                messages=messages,
                api_base=self._api_base,
                api_key=self._settings.openrouter_api_key,
                temperature=temperature,
                max_tokens=self._max_tokens,
                timeout=self._timeout,
            )

            latency = time.time() - start_time
            logger.info(
                "LLM generation complete",
                model=self._model,
                latency_ms=round(latency * 1000, 2),
            )

            # Extract content from response
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            else:
                raise ValueError("Empty response from LLM")

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            raise


# Global LLM client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance (singleton pattern)."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
