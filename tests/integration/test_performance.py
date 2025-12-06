"""Integration tests for performance verification after kernel refactoring.

Verifies that the refactored kernel maintains performance characteristics
and does not introduce performance degradation.
"""

import time
from pathlib import Path

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from tests.fixtures.mock_llm import MockLLMAdapter


@pytest.fixture
def orchestrator():
    """Create orchestrator with mock LLM for performance testing."""
    llm = MockLLMAdapter()
    memory = InMemoryKVStore()
    return Orchestrator(
        llm=llm,
        memory=memory,
        ttl=20,
    )






def test_memory_operations_performance(orchestrator):
    """Verify memory operations do not introduce performance degradation."""
    # Store values
    orchestrator.memory.write("test_key", "test_value")
    orchestrator.memory.write("another_key", 42)
    
    start_time = time.time()
    # Read multiple times
    for _ in range(100):
        orchestrator.memory.read("test_key")
        orchestrator.memory.read("another_key")
    elapsed_time = time.time() - start_time
    
    # Memory operations should be fast (<1s for 100 reads)
    assert elapsed_time < 1.0, f"Memory operations took {elapsed_time:.2f}s, expected <1s"





