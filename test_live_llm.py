#!/usr/bin/env python3
"""Test Aeon Core against a live llama-cpp-python server.

This script creates a minimal LLM adapter for testing against your local
llama-cpp server running on localhost:8000.

Usage:
    python test_live_llm.py
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from aeon.exceptions import LLMError
from aeon.kernel.orchestrator import Orchestrator
from aeon.llm.interface import LLMAdapter
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger


class LiveLlamaCppAdapter(LLMAdapter):
    """Minimal adapter for testing against live llama-cpp server."""

    def __init__(self, api_url: str = "http://localhost:8000/v1/chat/completions", model: str = "llama-cpp"):
        """Initialize adapter."""
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

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=120
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("choices"):
                raise LLMError("No choices in LLM response")

            text = data["choices"][0]["message"]["content"]
            return {
                "text": text,
                "usage": data.get("usage"),
                "model": self.model,
            }
        except requests.exceptions.RequestException as e:
            raise LLMError(f"API call failed: {str(e)}") from e
        except (json.JSONDecodeError, KeyError) as e:
            raise LLMError(f"Failed to parse response: {str(e)}") from e

    def supports_streaming(self) -> bool:
        """Return False - streaming not supported in this test adapter."""
        return False


def test_basic_generation():
    """Test 1: Basic LLM generation."""
    print("=" * 60)
    print("Test 1: Basic LLM Generation")
    print("=" * 60)
    
    llm = LiveLlamaCppAdapter()
    try:
        response = llm.generate(
            prompt="Say 'hello' in one word.",
            max_tokens=10,
            temperature=0.1,
        )
        print(f"✓ Response: {response['text'].strip()}")
        print(f"✓ Model: {response.get('model', 'unknown')}")
        if response.get('usage'):
            print(f"✓ Usage: {response['usage']}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_plan_generation():
    """Test 2: Plan generation."""
    print("\n" + "=" * 60)
    print("Test 2: Plan Generation")
    print("=" * 60)
    
    llm = LiveLlamaCppAdapter()
    orchestrator = Orchestrator(llm=llm, ttl=10)
    
    try:
        print("Generating plan for: 'calculate the sum of 5 and 10'")
        plan = orchestrator.generate_plan("calculate the sum of 5 and 10")
        print(f"✓ Goal: {plan.goal}")
        print(f"✓ Steps: {len(plan.steps)}")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. [{step.status}] {step.description}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_execution():
    """Test 3: Full plan execution."""
    print("\n" + "=" * 60)
    print("Test 3: Full Plan Execution")
    print("=" * 60)
    
    llm = LiveLlamaCppAdapter()
    memory = InMemoryKVStore()
    logger = JSONLLogger(file_path=Path("test_live_execution.jsonl"))
    
    orchestrator = Orchestrator(
        llm=llm,
        memory=memory,
        logger=logger,
        ttl=10
    )
    
    try:
        print("Executing: 'calculate the sum of 5 and 10'")
        result = orchestrator.execute("calculate the sum of 5 and 10")
        
        print(f"✓ Status: {result['status']}")
        print(f"✓ TTL remaining: {result['ttl_remaining']}")
        
        completed = [s for s in result['plan']['steps'] if s['status'] == 'complete']
        print(f"✓ Steps completed: {len(completed)}/{len(result['plan']['steps'])}")
        
        if result['status'] == 'complete':
            print(f"✓ Final result available in: {result.get('final_state', {})}")
        
        print(f"✓ Log file: test_live_execution.jsonl")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Testing Aeon Core against live llama-cpp server")
    print("Server: http://localhost:8000")
    print()
    
    results = []
    
    # Test 1: Basic generation
    results.append(("Basic Generation", test_basic_generation()))
    
    # Test 2: Plan generation
    results.append(("Plan Generation", test_plan_generation()))
    
    # Test 3: Full execution
    results.append(("Full Execution", test_full_execution()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())

