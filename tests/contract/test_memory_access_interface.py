"""Contract tests for MemoryAccessInterface (MAI)."""

import pytest

from aeon.memory.interface import MemoryAccessInterface
from aeon.memory.models import (
    MemoryDeleteResult,
    MemoryEntry,
    MemoryEntryMetadata,
    MemoryUsageStats,
    MemoryWriteResult,
)
from aeon.memory.null_memory import NullMemory
from aeon.memory.stm import STM


class TestMemoryAccessInterface:
    """Contract tests verifying MemoryAccessInterface compliance."""

    @pytest.fixture(params=[STM, NullMemory])
    def memory(self, request):
        """Create memory instance for testing (both STM and NullMemory)."""
        if request.param == STM:
            return STM(capacity=100, initial_ttl=10)
        return NullMemory()

    def test_memory_implements_memory_access_interface(self, memory):
        """Test that memory implementation implements MemoryAccessInterface."""
        assert isinstance(memory, MemoryAccessInterface)

    def test_memory_has_write_entry_method(self, memory):
        """Test that MemoryAccessInterface implementation has write_entry() method."""
        assert hasattr(memory, "write_entry")
        assert callable(memory.write_entry)

    def test_memory_has_read_entries_method(self, memory):
        """Test that MemoryAccessInterface implementation has read_entries() method."""
        assert hasattr(memory, "read_entries")
        assert callable(memory.read_entries)

    def test_memory_has_select_for_injection_method(self, memory):
        """Test that MemoryAccessInterface implementation has select_for_injection() method."""
        assert hasattr(memory, "select_for_injection")
        assert callable(memory.select_for_injection)

    def test_memory_has_get_usage_stats_method(self, memory):
        """Test that MemoryAccessInterface implementation has get_usage_stats() method."""
        assert hasattr(memory, "get_usage_stats")
        assert callable(memory.get_usage_stats)

    def test_memory_has_list_entries_method(self, memory):
        """Test that MemoryAccessInterface implementation has list_entries() method."""
        assert hasattr(memory, "list_entries")
        assert callable(memory.list_entries)

    def test_memory_has_delete_session_entries_method(self, memory):
        """Test that MemoryAccessInterface implementation has delete_session_entries() method."""
        assert hasattr(memory, "delete_session_entries")
        assert callable(memory.delete_session_entries)

    def test_write_entry_returns_memory_write_result(self, memory):
        """Test that write_entry() returns MemoryWriteResult."""
        result = memory.write_entry(
            session_id="session_123",
            execution_id="exec_001",
            phase="A",
            content={"test": "data"},
        )
        assert isinstance(result, MemoryWriteResult)
        assert hasattr(result, "success")
        assert hasattr(result, "entry_id")
        assert hasattr(result, "evicted_count")
        assert hasattr(result, "error")

    def test_write_entry_never_raises_exceptions(self, memory):
        """Test that write_entry() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return result, not raise
        result = memory.write_entry(
            session_id="",
            execution_id="",
            phase="X",
            content={"invalid": "data"},
        )
        assert isinstance(result, MemoryWriteResult)
        # Should return a result, never raise

    def test_read_entries_returns_list_of_memory_entries(self, memory):
        """Test that read_entries() returns List[MemoryEntry]."""
        result = memory.read_entries(session_id="session_123")
        assert isinstance(result, list)
        # All items should be MemoryEntry (if any)
        for entry in result:
            assert isinstance(entry, MemoryEntry)

    def test_read_entries_never_raises_exceptions(self, memory):
        """Test that read_entries() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return list, not raise
        result = memory.read_entries(session_id=None)  # type: ignore
        assert isinstance(result, list)

    def test_select_for_injection_returns_dict_with_required_keys(self, memory):
        """Test that select_for_injection() returns dict with context_blocks and non_authoritative_marker."""
        context = {
            "current_phase": "B",
            "current_execution_id": "exec_001",
            "injection_point": "memory_context",
        }
        result = memory.select_for_injection(
            session_id="session_123",
            context=context,
            budget=1000,
        )
        assert isinstance(result, dict)
        assert "context_blocks" in result
        assert "non_authoritative_marker" in result
        assert isinstance(result["context_blocks"], list)
        assert isinstance(result["non_authoritative_marker"], str)

    def test_select_for_injection_never_raises_exceptions(self, memory):
        """Test that select_for_injection() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return dict, not raise
        result = memory.select_for_injection(
            session_id="",
            context={},
            budget=-1,
        )
        assert isinstance(result, dict)
        assert "context_blocks" in result

    def test_get_usage_stats_returns_memory_usage_stats(self, memory):
        """Test that get_usage_stats() returns MemoryUsageStats."""
        result = memory.get_usage_stats(session_id="session_123")
        assert isinstance(result, MemoryUsageStats)
        assert hasattr(result, "memory_used")
        assert hasattr(result, "memory_entries_considered")
        assert hasattr(result, "memory_entries_injected")
        assert hasattr(result, "memory_failures")
        assert hasattr(result, "total_entries")
        assert hasattr(result, "expired_entries")

    def test_get_usage_stats_never_raises_exceptions(self, memory):
        """Test that get_usage_stats() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return stats, not raise
        result = memory.get_usage_stats(session_id="")
        assert isinstance(result, MemoryUsageStats)

    def test_list_entries_returns_list_of_metadata(self, memory):
        """Test that list_entries() returns List[MemoryEntryMetadata]."""
        result = memory.list_entries(session_id="session_123")
        assert isinstance(result, list)
        # All items should be MemoryEntryMetadata (if any)
        for metadata in result:
            assert isinstance(metadata, MemoryEntryMetadata)
            # Verify metadata does NOT have content field
            assert not hasattr(metadata, "content")

    def test_list_entries_never_raises_exceptions(self, memory):
        """Test that list_entries() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return list, not raise
        result = memory.list_entries(session_id=None)  # type: ignore
        assert isinstance(result, list)

    def test_delete_session_entries_returns_memory_delete_result(self, memory):
        """Test that delete_session_entries() returns MemoryDeleteResult."""
        result = memory.delete_session_entries(session_id="session_123")
        assert isinstance(result, MemoryDeleteResult)
        assert hasattr(result, "success")
        assert hasattr(result, "entries_removed")
        assert hasattr(result, "error")

    def test_delete_session_entries_never_raises_exceptions(self, memory):
        """Test that delete_session_entries() never raises exceptions (graceful degradation)."""
        # Even with invalid inputs, should return result, not raise
        result = memory.delete_session_entries(session_id="")
        assert isinstance(result, MemoryDeleteResult)

    def test_all_methods_require_session_id(self, memory):
        """Test that all methods require session_id parameter."""
        # All methods should accept session_id as first parameter
        # (This is verified by the method signatures, but we test they work)
        result1 = memory.write_entry(
            session_id="test",
            execution_id="exec",
            phase="A",
            content={},
        )
        assert isinstance(result1, MemoryWriteResult)

        result2 = memory.read_entries(session_id="test")
        assert isinstance(result2, list)

        result3 = memory.select_for_injection(
            session_id="test",
            context={"current_phase": "B"},
            budget=1000,
        )
        assert isinstance(result3, dict)

        result4 = memory.get_usage_stats(session_id="test")
        assert isinstance(result4, MemoryUsageStats)

        result5 = memory.list_entries(session_id="test")
        assert isinstance(result5, list)

        result6 = memory.delete_session_entries(session_id="test")
        assert isinstance(result6, MemoryDeleteResult)

    def test_graceful_degradation_on_all_operations(self, memory):
        """Test that all operations degrade gracefully (never raise, always return structured results)."""
        # Test with various invalid inputs
        invalid_inputs = [
            ("", "exec", "A", {}),
            ("session", "", "A", {}),
            ("session", "exec", "X", {}),
            ("session", "exec", "A", None),  # type: ignore
        ]

        for session_id, execution_id, phase, content in invalid_inputs:
            try:
                result = memory.write_entry(
                    session_id=session_id,
                    execution_id=execution_id,
                    phase=phase,
                    content=content if content is not None else {},
                )
                assert isinstance(result, MemoryWriteResult)
            except Exception as e:
                pytest.fail(f"write_entry raised exception: {e}")

        # Test read operations with invalid inputs
        try:
            result = memory.read_entries(session_id="")
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"read_entries raised exception: {e}")

        # Test other operations similarly
        try:
            result = memory.select_for_injection(
                session_id="",
                context={},
                budget=-1,
            )
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"select_for_injection raised exception: {e}")

        try:
            result = memory.get_usage_stats(session_id="")
            assert isinstance(result, MemoryUsageStats)
        except Exception as e:
            pytest.fail(f"get_usage_stats raised exception: {e}")

        try:
            result = memory.list_entries(session_id="")
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"list_entries raised exception: {e}")

        try:
            result = memory.delete_session_entries(session_id="")
            assert isinstance(result, MemoryDeleteResult)
        except Exception as e:
            pytest.fail(f"delete_session_entries raised exception: {e}")
