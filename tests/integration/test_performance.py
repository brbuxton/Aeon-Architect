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


def test_plan_generation_performance(orchestrator):
    """Verify plan generation completes within acceptable time."""
    request = "calculate the sum of 5 and 10"
    
    start_time = time.time()
    result = orchestrator.execute(request)
    elapsed_time = time.time() - start_time
    
    # Plan generation should complete in reasonable time (<10s for mock)
    assert elapsed_time < 10.0, f"Plan generation took {elapsed_time:.2f}s, expected <10s"
    assert result is not None
    assert "plan" in result or "status" in result


def test_multi_step_execution_performance(orchestrator):
    """Verify multi-step execution maintains performance."""
    request = "step 1: calculate 5+10, step 2: multiply by 2, step 3: add 5"
    
    start_time = time.time()
    result = orchestrator.execute(request)
    elapsed_time = time.time() - start_time
    
    # Multi-step execution should complete in reasonable time (<30s for mock)
    assert elapsed_time < 30.0, f"Multi-step execution took {elapsed_time:.2f}s, expected <30s"
    assert result is not None


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


def test_orchestration_module_invocation_performance(orchestrator):
    """Verify orchestration module invocations do not add significant overhead."""
    request = "process data and generate report"
    
    start_time = time.time()
    result = orchestrator.execute(request)
    elapsed_time = time.time() - start_time
    
    # Orchestration module invocations should not add significant overhead
    # Baseline: similar performance to pre-refactor (<15s for mock)
    assert elapsed_time < 15.0, f"Orchestration took {elapsed_time:.2f}s, expected <15s"
    assert result is not None


def test_no_performance_regression(orchestrator):
    """Verify no performance regression compared to baseline expectations.
    
    This test ensures that the refactored kernel with orchestration modules
    maintains similar performance characteristics to the pre-refactor kernel.
    """
    request = "execute a multi-step task with validation and refinement"
    
    start_time = time.time()
    result = orchestrator.execute(request)
    elapsed_time = time.time() - start_time
    
    # Performance should be within acceptable range
    # For mock LLM, complex execution should complete in reasonable time
    assert elapsed_time < 20.0, f"Execution took {elapsed_time:.2f}s, expected <20s"
    assert result is not None
    
    # Verify result structure is correct
    assert isinstance(result, dict)
    assert "status" in result or "plan" in result

