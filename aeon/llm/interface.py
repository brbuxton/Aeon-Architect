"""LLM adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from aeon.exceptions import LLMError


class LLMAdapter(ABC):
    """Abstract interface for LLM inference adapters."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate LLM response.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with keys:
                - "text": Generated text (str)
                - "usage": Token usage dict (optional)
                - "model": Model identifier (str, optional)

        Raises:
            LLMError: On API failure, timeout, or other errors
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return True if adapter supports streaming responses."""
        pass








