#!/usr/bin/env python3
"""Debug test to see what the LLM is actually returning."""

import json
from typing import Any, Dict, Optional

import requests

from aeon.kernel.orchestrator import Orchestrator


class LiveLlamaCppAdapter:
    """Minimal adapter for testing."""

    def __init__(self, api_url: str = "http://localhost:8000/v1/chat/completions", model: str = "llama-cpp"):
        self.api_url = api_url
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate response from llama-cpp server."""
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

        response = requests.post(
            self.api_url, headers=headers, json=payload, timeout=120
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("choices"):
            raise Exception("No choices in LLM response")

        text = data["choices"][0]["message"]["content"]
        return {
            "text": text,
            "usage": data.get("usage"),
            "model": self.model,
        }

    def supports_streaming(self) -> bool:
        return False


def main():
    """Debug what the LLM returns for plan generation."""
    print("=" * 60)
    print("Debug: Testing Plan Generation Prompt")
    print("=" * 60)
    
    llm = LiveLlamaCppAdapter()
    orchestrator = Orchestrator(llm=llm, ttl=10)
    
    # Get the prompt that would be sent
    request = "calculate the sum of 5 and 10"
    system_prompt = orchestrator._get_plan_generation_system_prompt()
    prompt = orchestrator._construct_plan_generation_prompt(request)
    
    print("\nSystem Prompt:")
    print("-" * 60)
    print(system_prompt)
    print("-" * 60)
    
    print("\nUser Prompt:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    
    print("\nSending to LLM...")
    response = llm.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=500, temperature=0.1)
    
    print("\nRaw LLM Response:")
    print("-" * 60)
    print(repr(response['text']))
    print("-" * 60)
    
    print("\nResponse length:", len(response['text']))
    print("\nFirst 500 chars:")
    print(response['text'][:500])
    
    # Try to extract JSON
    print("\n" + "=" * 60)
    print("Attempting JSON extraction...")
    print("=" * 60)
    try:
        plan_json = orchestrator._extract_plan_from_response(response)
        print("✓ Successfully extracted JSON:")
        print(json.dumps(plan_json, indent=2))
    except Exception as e:
        print(f"✗ Failed to extract JSON: {e}")
        print("\nTrying to find JSON in response...")
        text = response['text']
        # Look for JSON code blocks
        if "```json" in text:
            print("Found ```json block")
        elif "```" in text:
            print("Found ``` block (might be JSON)")
        # Look for { at start
        if text.strip().startswith("{"):
            print("Response starts with {")
        else:
            print("Response does NOT start with {")
            # Try to find first {
            idx = text.find("{")
            if idx >= 0:
                print(f"Found {{ at position {idx}")
                print(f"Text before: {repr(text[:idx])}")
                print(f"Text from {{: {text[idx:idx+200]}")


if __name__ == "__main__":
    main()

