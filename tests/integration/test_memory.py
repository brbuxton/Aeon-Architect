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

    def test_memory_write_and_read_during_execution(self, orchestrator, memory):
        """Test that memory can be written to and read from during execution."""
        # Write to memory before execution
        memory.write("pre_execution_key", "pre_execution_value")
        
        # Verify it's accessible
        assert memory.read("pre_execution_key") == "pre_execution_value"
        
        # Execute a plan
        result = orchestrator.execute("test request")
        
        # Memory should still be accessible after execution
        assert memory.read("pre_execution_key") == "pre_execution_value"
        
        # Write new value during/after execution
        memory.write("post_execution_key", "post_execution_value")
        assert memory.read("post_execution_key") == "post_execution_value"

    def test_memory_search_during_execution(self, orchestrator, memory):
        """Test that memory search works during execution."""
        # Write multiple keys with prefix
        memory.write("user_name", "Alice")
        memory.write("user_age", 30)
        memory.write("other_key", "value")
        
        # Execute plan
        result = orchestrator.execute("test request")
        
        # Search should still work
        results = memory.search("user_")
        assert len(results) == 2
        keys = [key for key, _ in results]
        assert "user_name" in keys
        assert "user_age" in keys

    def test_memory_persists_across_steps(self, orchestrator, memory):
        """Test that memory persists across plan steps."""
        # Write value before execution
        memory.write("step_data", "initial_value")
        
        # Execute plan with multiple steps
        result = orchestrator.execute("complex multi-step request")
        
        # Memory should persist
        assert memory.read("step_data") == "initial_value"
        
        # Update value
        memory.write("step_data", "updated_value")
        assert memory.read("step_data") == "updated_value"

    def test_memory_without_orchestrator(self):
        """Test that memory works independently of orchestrator."""
        memory = InMemoryKVStore()
        memory.write("independent_key", "independent_value")
        assert memory.read("independent_key") == "independent_value"
        
        results = memory.search("independent")
        assert len(results) == 1
        assert ("independent_key", "independent_value") in results

