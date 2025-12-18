"""Unit tests for NullMemory."""

import pytest

from aeon.memory.models import MemoryDeleteResult, MemoryWriteResult
from aeon.memory.null_memory import NullMemory


class TestNullMemory:
    """Tests for NullMemory no-op implementation."""

    @pytest.fixture
    def null_memory(self):
        """Create NullMemory instance for testing."""
        return NullMemory()

    def test_write_entry_returns_success_but_stores_nothing(self, null_memory):
        """Test that write_entry() returns success but stores nothing."""
        result = null_memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"test": "data"},
        )

        assert result.success is True
        assert result.entry_id is None
        assert result.evicted_count == 0
        assert result.error is None

        # Verify nothing was stored
        entries = null_memory.read_entries(session_id="session_123")
        assert entries == []

    def test_read_entries_returns_empty_list(self, null_memory):
        """Test that read_entries() always returns empty list."""
        # Write something (no-op)
        null_memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"test": "data"},
        )

        # Read should return empty
        entries = null_memory.read_entries(session_id="session_123")
        assert entries == []

        # Read with filters should also return empty
        entries = null_memory.read_entries(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
        )
        assert entries == []

    def test_select_for_injection_returns_empty_structure(self, null_memory):
        """Test that select_for_injection() returns empty structure."""
        context = {
            "current_phase": "B",
            "current_execution_id": "exec_001",
            "injection_point": "memory_context",
        }
        result = null_memory.select_for_injection(
            session_id="session_123",
            context=context,
            budget=1000,
        )

        assert "context_blocks" in result
        assert "non_authoritative_marker" in result
        assert result["context_blocks"] == []
        assert isinstance(result["non_authoritative_marker"], str)

    def test_get_usage_stats_returns_zero_counts(self, null_memory):
        """Test that get_usage_stats() returns zero counts."""
        stats = null_memory.get_usage_stats(session_id="session_123")

        assert stats.memory_used is False
        assert stats.memory_entries_considered == 0
        assert stats.memory_entries_injected == 0
        assert stats.memory_failures == 0
        assert stats.total_entries == 0
        assert stats.expired_entries == 0

    def test_list_entries_returns_empty_list(self, null_memory):
        """Test that list_entries() returns empty list."""
        # Write something (no-op)
        null_memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"test": "data"},
        )

        # List should return empty
        metadata_list = null_memory.list_entries(session_id="session_123")
        assert metadata_list == []

    def test_delete_session_entries_returns_success_with_zero_removed(self, null_memory):
        """Test that delete_session_entries() returns success with zero removed."""
        # Write something (no-op)
        null_memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"test": "data"},
        )

        # Delete should succeed but remove nothing
        result = null_memory.delete_session_entries(session_id="session_123")
        assert result.success is True
        assert result.entries_removed == 0
        assert result.error is None

    def test_all_operations_never_raise_exceptions(self, null_memory):
        """Test that all operations never raise exceptions (graceful degradation)."""
        # All operations should return results, never raise
        result1 = null_memory.write_entry(
            session_id="",
            execution_id="",
            phase="X",
            content={"invalid": "data"},
        )
        assert isinstance(result1, MemoryWriteResult)

        result2 = null_memory.read_entries(session_id=None)  # type: ignore
        assert isinstance(result2, list)

        result3 = null_memory.select_for_injection(
            session_id="",
            context={},
            budget=-1,
        )
        assert isinstance(result3, dict)

        result4 = null_memory.get_usage_stats(session_id="")
        assert hasattr(result4, "total_entries")

        result5 = null_memory.list_entries(session_id="")
        assert isinstance(result5, list)

        result6 = null_memory.delete_session_entries(session_id="")
        assert isinstance(result6, MemoryDeleteResult)

    def test_null_memory_enables_execution_with_memory_disabled(self, null_memory):
        """Test that NullMemory enables execution with memory fully disabled."""
        # All operations should succeed but do nothing
        # This allows orchestrator to function with memory disabled

        # Write operations succeed
        write_result = null_memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"goal": "test"},
        )
        assert write_result.success is True

        # Read operations return empty
        entries = null_memory.read_entries(session_id="session_123")
        assert entries == []

        # Selection returns empty
        injection_result = null_memory.select_for_injection(
            session_id="session_123",
            context={"current_phase": "B"},
            budget=1000,
        )
        assert injection_result["context_blocks"] == []

        # Stats are zero
        stats = null_memory.get_usage_stats(session_id="session_123")
        assert stats.total_entries == 0

        # Delete succeeds
        delete_result = null_memory.delete_session_entries(session_id="session_123")
        assert delete_result.success is True
