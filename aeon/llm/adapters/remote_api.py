"""Remote API LLM adapter with retry logic."""

import time
from typing import Any, Dict, Optional

from aeon.exceptions import LLMError
from aeon.llm.interface import LLMAdapter


class RemoteAPIAdapter(LLMAdapter):
    """Remote API LLM adapter with retry logic (3 attempts, exponential backoff)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
    ) -> None:
        """
        Initialize remote API adapter.

        Args:
            api_key: API key for authentication
            api_url: API endpoint URL
            model: Model identifier
            max_retries: Maximum retry attempts (default 3)
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.max_retries = max_retries

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate LLM response with retry logic.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with keys: text, usage (optional), model (optional)

        Raises:
            LLMError: On API failure after retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                # Attempt API call
                response = self._call_api(prompt, system_prompt, max_tokens, temperature)
                return response
            except (ConnectionError, TimeoutError, OSError) as e:
                # Network errors - retry with exponential backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(wait_time)
                    continue
                else:
                    raise LLMError(
                        f"API call failed after {self.max_retries} attempts: {str(e)}"
                    ) from e
            except Exception as e:
                # Other errors - don't retry
                raise LLMError(f"API call failed: {str(e)}") from e
        
        # Should never reach here, but just in case
        raise LLMError(f"API call failed after {self.max_retries} attempts")

    def _call_api(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Dict[str, Any]:
        """
        Make actual API call (to be implemented based on specific API).

        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            API response dict

        Raises:
            Exception: On API failure
        """
        # Placeholder implementation - should be replaced with actual API call
        # For now, raise NotImplementedError to indicate this needs implementation
        raise NotImplementedError(
            "Remote API adapter requires actual API implementation. "
            "Use a mock adapter for testing or implement the API call here."
        )

    def supports_streaming(self) -> bool:
        """Return True if adapter supports streaming responses."""
        return False








