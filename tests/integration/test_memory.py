"""Integration tests for memory operations in orchestration."""

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from tests.fixtures.mock_llm import MockLLMAdapter


class TestMemoryOperations:
    """Integration tests for memory operations in orchestration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def memory(self):
        """Create memory instance."""
        return InMemoryKVStore()

    @pytest.fixture
    def orchestrator(self, mock_llm, memory):
        """Create orchestrator with memory."""
        return Orchestrator(
            llm=mock_llm,
            memory=memory,
            ttl=10
        )

    def test_memory_is_accessible_in_orchestrator(self, orchestrator, memory):
        """Test that memory is accessible through orchestrator."""
        assert orchestrator.memory is not None
        assert orchestrator.memory == memory




    def test_memory_without_orchestrator(self):
        """Test that memory works independently of orchestrator."""
        memory = InMemoryKVStore()
        memory.write("independent_key", "independent_value")
        assert memory.read("independent_key") == "independent_value"
        
        results = memory.search("independent")
        assert len(results) == 1
        assert ("independent_key", "independent_value") in results

