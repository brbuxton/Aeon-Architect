"""Llama-cpp-python LLM adapter for local instances."""

import json
import time
from typing import Any, Dict, Optional

import requests

from aeon.exceptions import LLMError
from aeon.llm.interface import LLMAdapter


class LlamaCppAdapter(LLMAdapter):
    """Llama-cpp-python LLM adapter for local instances."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000/v1/chat/completions",
        model: str = "llama-cpp-model",
        max_retries: int = 3,
    ) -> None:
        """
        Initialize Llama-cpp-python adapter.

        Args:
            api_url: URL of the llama-cpp-python OpenAI-compatible API endpoint.
            model: Model identifier.
            max_retries: Maximum retry attempts (default 3).
        """
        self.api_url = api_url
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
        Generate LLM response from llama-cpp-python API with retry logic.

        Args:
            prompt: User prompt.
            system_prompt: System prompt (optional).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Dict with keys: "text", "usage" (optional), "model" (optional).

        Raises:
            LLMError: On API failure after retries exhausted.
        """
        headers = {"Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=120
                )
                response.raise_for_status()  # Raise an exception for HTTP errors
                response_data = response.json()

                if not response_data.get("choices"):
                    raise LLMError("No choices in LLM response.")

                generated_text = response_data["choices"][0]["message"]["content"]
                return {
                    "text": generated_text,
                    "usage": response_data.get("usage"),
                    "model": self.model,
                }
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    raise LLMError(
                        f"Llama-cpp API call failed after {self.max_retries} attempts: {str(e)}"
                    ) from e
            except (json.JSONDecodeError, KeyError) as e:
                raise LLMError(f"Failed to parse LLM response: {str(e)}") from e
            except Exception as e:
                raise LLMError(f"An unexpected error occurred: {str(e)}") from e
        
        raise LLMError(f"Llama-cpp API call failed after {self.max_retries} attempts")

    def supports_streaming(self) -> bool:
        """Return True if adapter supports streaming responses."""
        return False

