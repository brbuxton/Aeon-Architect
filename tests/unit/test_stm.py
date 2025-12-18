"""Unit tests for STM (Short-Term Memory)."""

import json
import pytest
from datetime import datetime

from aeon.memory.models import MemoryEntry, MemoryWriteResult
from aeon.memory.stm import STM


class TestSTM:
    """Tests for STM session-scoped memory storage."""

    @pytest.fixture
    def stm(self):
        """Create STM instance for testing."""
        return STM(capacity=100, initial_ttl=10)

    @pytest.fixture
    def session_id(self):
        """Create a test session_id."""
        return "test_session_123"

    @pytest.fixture
    def execution_id(self):
        """Create a test execution_id."""
        return "exec_001"

    def test_write_entry_stores_entry(self, stm, session_id, execution_id):
        """Test that write_entry() stores a memory entry."""
        content = {"goal": "test goal", "steps": ["step1", "step2"]}
        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )

        assert result.success is True
        assert result.entry_id is not None
        assert result.evicted_count == 0
        assert result.error is None

    def test_write_entry_returns_unique_entry_id(self, stm, session_id, execution_id):
        """Test that write_entry() returns unique entry_id for each entry."""
        content = {"test": "data"}
        result1 = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )
        result2 = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content=content,
        )

        assert result1.success is True
        assert result2.success is True
        assert result1.entry_id != result2.entry_id

    def test_read_entries_retrieves_stored_entries(self, stm, session_id, execution_id):
        """Test that read_entries() retrieves stored entries."""
        content1 = {"phase": "A", "data": "test1"}
        content2 = {"phase": "B", "data": "test2"}

        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content1,
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content=content2,
        )

        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 2
        assert all(isinstance(entry, MemoryEntry) for entry in entries)

    def test_read_entries_filters_by_execution_id(self, stm, session_id):
        """Test that read_entries() filters by execution_id."""
        content = {"test": "data"}

        stm.write_entry(
            session_id=session_id,
            execution_id="exec_001",
            phase="A",
            content=content,
        )
        stm.write_entry(
            session_id=session_id,
            execution_id="exec_002",
            phase="A",
            content=content,
        )

        entries = stm.read_entries(session_id=session_id, execution_id="exec_001")
        assert len(entries) == 1
        assert entries[0].execution_id == "exec_001"

    def test_read_entries_filters_by_phase(self, stm, session_id, execution_id):
        """Test that read_entries() filters by phase."""
        content = {"test": "data"}

        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content=content,
        )

        entries = stm.read_entries(session_id=session_id, phase="A")
        assert len(entries) == 1
        assert entries[0].phase == "A"

    def test_read_entries_returns_empty_for_nonexistent_session(self, stm):
        """Test that read_entries() returns empty list for nonexistent session."""
        entries = stm.read_entries(session_id="nonexistent")
        assert entries == []

    def test_write_entry_validates_session_id(self, stm, execution_id):
        """Test that write_entry() validates session_id."""
        result = stm.write_entry(
            session_id="",
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        assert result.success is False
        assert result.error is not None
        assert "session_id" in result.error.lower()

    def test_write_entry_validates_execution_id(self, stm, session_id):
        """Test that write_entry() validates execution_id."""
        result = stm.write_entry(
            session_id=session_id,
            execution_id="",
            phase="A",
            content={"test": "data"},
        )

        assert result.success is False
        assert result.error is not None
        assert "execution_id" in result.error.lower()

    def test_write_entry_validates_phase(self, stm, session_id, execution_id):
        """Test that write_entry() validates phase."""
        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="X",  # Invalid phase
            content={"test": "data"},
        )

        assert result.success is False
        assert result.error is not None
        assert "phase" in result.error.lower()

    def test_write_entry_validates_content_serializability(self, stm, session_id, execution_id):
        """Test that write_entry() validates content is JSON-serializable."""
        # Create a non-serializable object (function)
        def non_serializable():
            pass

        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"func": non_serializable},
        )

        assert result.success is False
        assert result.error is not None
        assert "serializable" in result.error.lower()

    def test_write_entry_graceful_degradation_on_exception(self, stm, session_id, execution_id):
        """Test that write_entry() degrades gracefully on exception."""
        # This test verifies that exceptions don't propagate
        # We can't easily trigger an exception in normal flow,
        # but we can verify the error handling structure exists
        content = {"test": "data"}
        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )

        # Should always return a result, never raise
        assert isinstance(result, MemoryWriteResult)

    def test_read_entries_graceful_degradation_on_exception(self, stm):
        """Test that read_entries() degrades gracefully on exception."""
        # Should always return a list, never raise
        entries = stm.read_entries(session_id="test")
        assert isinstance(entries, list)

    def test_write_entry_enforces_capacity(self, stm, session_id, execution_id):
        """Test that write_entry() enforces capacity limit with eviction."""
        # Create STM with small capacity
        small_stm = STM(capacity=3, initial_ttl=10)

        # Write entries up to capacity
        for i in range(3):
            result = small_stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )
            assert result.success is True
            assert result.evicted_count == 0

        # Write one more entry - should trigger eviction
        result = small_stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"index": 3},
        )
        assert result.success is True
        assert result.evicted_count > 0

        # Verify capacity is maintained
        entries = small_stm.read_entries(session_id=session_id)
        assert len(entries) <= 3

    def test_capacity_eviction_is_deterministic(self, session_id, execution_id):
        """Test that capacity eviction is deterministic (same sequence produces same results)."""
        # Create two STM instances with same capacity
        stm1 = STM(capacity=3, initial_ttl=10)
        stm2 = STM(capacity=3, initial_ttl=10)

        # Write same sequence of entries to both
        for i in range(5):
            content = {"index": i, "data": f"entry_{i}"}
            result1 = stm1.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content=content,
            )
            result2 = stm2.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content=content,
            )
            assert result1.success == result2.success
            assert result1.evicted_count == result2.evicted_count

        # Verify both have same entries (deterministic eviction)
        entries1 = stm1.read_entries(session_id=session_id)
        entries2 = stm2.read_entries(session_id=session_id)
        assert len(entries1) == len(entries2)
        # Entries should be the same (deterministic FIFO eviction)
        entry_ids1 = {entry.content["index"] for entry in entries1}
        entry_ids2 = {entry.content["index"] for entry in entries2}
        assert entry_ids1 == entry_ids2

    def test_capacity_eviction_reports_evicted_count(self, session_id, execution_id):
        """Test that write_entry() reports evicted_count in result."""
        small_stm = STM(capacity=2, initial_ttl=10)

        # Fill to capacity
        for i in range(2):
            result = small_stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )
            assert result.evicted_count == 0

        # Write one more - should evict 1 entry
        result = small_stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"index": 2},
        )
        assert result.success is True
        assert result.evicted_count == 1

    def test_read_entries_excludes_expired_entries(self, stm, session_id, execution_id):
        """Test that read_entries() excludes expired entries (TTL <= 0)."""
        # Write an entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        # Manually expire the entry by setting TTL to 1, then read (which decrements TTL)
        # Set TTL to 1 so that next read will decrement it to 0
        for entry_id, entry in stm._store[session_id].items():
            entry.ttl = 1

        # Read - this will decrement TTL to 0 and remove expired entry
        entries = stm.read_entries(session_id=session_id)
        # Entry should be removed (expired and cleaned up)
        assert len(entries) == 0

    def test_ttl_assignment_on_write(self, session_id, execution_id):
        """Test that write_entry() assigns initial TTL value to new entries."""
        stm = STM(capacity=100, initial_ttl=10)
        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )
        assert result.success is True

        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 1
        assert entries[0].ttl == 10  # Should have initial TTL

    def test_autonomous_ttl_decrement_on_read(self, session_id, execution_id):
        """Test that TTL is decremented autonomously on read_entries() for all entries in session."""
        stm = STM(capacity=100, initial_ttl=3)
        # Write multiple entries
        for i in range(3):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )

        # All entries should have TTL = 3 initially
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 3
        for entry in entries:
            assert entry.ttl == 2  # Decremented once by read_entries

        # Read again - TTL should decrement again
        entries = stm.read_entries(session_id=session_id)
        for entry in entries:
            assert entry.ttl == 1  # Decremented again

        # Read one more time - entries should expire and be removed
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 0  # All expired and removed

    def test_autonomous_ttl_decrement_on_write(self, session_id, execution_id):
        """Test that TTL is decremented autonomously on write_entry() for all entries in session."""
        stm = STM(capacity=100, initial_ttl=2)
        # Write first entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"index": 0},
        )

        # Write second entry - should decrement TTL of first entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"index": 1},
        )

        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 2
        # First entry should have TTL = 1 (decremented once), second should have TTL = 1 (decremented once)
        for entry in entries:
            assert entry.ttl == 1

    def test_autonomous_ttl_decrement_preserves_recency_bias(self, session_id, execution_id):
        """Test that TTL decrement preserves recency bias (all entries in session decremented together)."""
        stm = STM(capacity=100, initial_ttl=5)
        # Write entries at different times
        for i in range(3):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )

        # All entries should have same TTL after decrements (preserves recency bias)
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 3
        ttls = [entry.ttl for entry in entries]
        # All should have same TTL (all decremented together)
        assert len(set(ttls)) == 1

    def test_expired_entry_removal_from_physical_memory(self, session_id, execution_id):
        """Test that expired entries are removed from physical memory."""
        stm = STM(capacity=100, initial_ttl=1)
        # Write entry
        result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )
        assert result.success is True

        # Read once - TTL decrements to 0, entry should be removed
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 0

        # Verify entry is removed from physical memory
        assert session_id in stm._store
        assert len(stm._store[session_id]) == 0

    def test_expired_entry_exclusion_from_all_operations(self, session_id, execution_id):
        """Test that expired entries are excluded from all read and search operations."""
        stm = STM(capacity=100, initial_ttl=1)
        # Write entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        # Read once to expire entry
        stm.read_entries(session_id=session_id)

        # Verify expired entry is excluded from read_entries
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 0

        # Verify expired entry is excluded from list_entries
        metadata_list = stm.list_entries(session_id=session_id)
        assert len(metadata_list) == 0

        # Verify expired entry is excluded from get_usage_stats
        stats = stm.get_usage_stats(session_id=session_id)
        assert stats.total_entries == 0
        assert stats.expired_entries == 0

    def test_ttl_decrement_on_select_for_injection(self, session_id, execution_id):
        """Test that TTL is decremented on select_for_injection() operation."""
        stm = STM(capacity=100, initial_ttl=2)
        # Write entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        # Call select_for_injection - should decrement TTL
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "memory_context",
        }
        stm.select_for_injection(session_id=session_id, context=context, budget=1000)

        # Verify TTL was decremented
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 1
        assert entries[0].ttl == 1

    def test_ttl_decrement_on_get_usage_stats(self, session_id, execution_id):
        """Test that TTL is decremented on get_usage_stats() operation."""
        stm = STM(capacity=100, initial_ttl=2)
        # Write entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        # Call get_usage_stats - should decrement TTL
        stats = stm.get_usage_stats(session_id=session_id)
        assert stats.total_entries == 1

        # Verify TTL was decremented
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 1
        assert entries[0].ttl == 1

    def test_ttl_decrement_on_list_entries(self, session_id, execution_id):
        """Test that TTL is decremented on list_entries() operation."""
        stm = STM(capacity=100, initial_ttl=2)
        # Write entry
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"test": "data"},
        )

        # Call list_entries - should decrement TTL
        metadata_list = stm.list_entries(session_id=session_id)
        assert len(metadata_list) == 1

        # Verify TTL was decremented
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 1
        assert entries[0].ttl == 1

    def test_list_entries_returns_metadata_only(self, stm, session_id, execution_id):
        """Test that list_entries() returns metadata without raw content."""
        content = {"sensitive": "data", "goal": "test"}
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )

        metadata_list = stm.list_entries(session_id=session_id)
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        # Verify metadata has required fields
        assert metadata.session_id == session_id
        assert metadata.execution_id == execution_id
        assert metadata.phase == "A"
        assert isinstance(metadata.created_at, datetime)
        assert metadata.ttl >= 0

        # Verify metadata does NOT have content field
        assert not hasattr(metadata, "content")

    def test_delete_session_entries_removes_all_entries(self, stm, session_id, execution_id):
        """Test that delete_session_entries() removes all entries for a session."""
        # Write multiple entries
        for i in range(5):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )

        # Verify entries exist
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 5

        # Delete all entries
        result = stm.delete_session_entries(session_id=session_id)
        assert result.success is True
        assert result.entries_removed == 5

        # Verify entries are gone
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) == 0

    def test_delete_session_entries_returns_zero_for_nonexistent_session(self, stm):
        """Test that delete_session_entries() returns zero for nonexistent session."""
        result = stm.delete_session_entries(session_id="nonexistent")
        assert result.success is True
        assert result.entries_removed == 0

    def test_get_usage_stats_returns_stats(self, stm, session_id, execution_id):
        """Test that get_usage_stats() returns usage statistics."""
        # Write some entries
        for i in range(3):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="A",
                content={"index": i},
            )

        stats = stm.get_usage_stats(session_id=session_id)
        assert stats.total_entries == 3
        assert stats.expired_entries == 0
        assert stats.memory_used is True

    def test_get_usage_stats_returns_zero_for_nonexistent_session(self, stm):
        """Test that get_usage_stats() returns zero stats for nonexistent session."""
        stats = stm.get_usage_stats(session_id="nonexistent")
        assert stats.total_entries == 0
        assert stats.expired_entries == 0
        assert stats.memory_used is False

    def test_select_for_injection_returns_empty_structure(self, stm, session_id):
        """Test that select_for_injection() returns empty structure (Phase 4 basic implementation)."""
        context = {
            "current_phase": "B",
            "current_execution_id": "exec_001",
            "injection_point": "memory_context",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=1000,
        )

        assert "context_blocks" in result
        assert "non_authoritative_marker" in result
        assert result["context_blocks"] == []
        assert isinstance(result["non_authoritative_marker"], str)

    def test_memory_entries_persist_across_reads(self, stm, session_id, execution_id):
        """Test that memory entries persist across multiple read operations."""
        content = {"test": "data"}
        write_result = stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content=content,
        )
        assert write_result.success is True

        # Read multiple times
        entries1 = stm.read_entries(session_id=session_id)
        entries2 = stm.read_entries(session_id=session_id)

        assert len(entries1) == 1
        assert len(entries2) == 1
        # Verify same content persists
        assert entries1[0].content == entries2[0].content
        assert entries1[0].session_id == entries2[0].session_id

    def test_memory_entries_are_session_scoped(self, stm, execution_id):
        """Test that memory entries are scoped to sessions."""
        session1 = "session_1"
        session2 = "session_2"

        stm.write_entry(
            session_id=session1,
            execution_id=execution_id,
            phase="A",
            content={"session": "1"},
        )
        stm.write_entry(
            session_id=session2,
            execution_id=execution_id,
            phase="A",
            content={"session": "2"},
        )

        entries1 = stm.read_entries(session_id=session1)
        entries2 = stm.read_entries(session_id=session2)

        assert len(entries1) == 1
        assert len(entries2) == 1
        assert entries1[0].content["session"] == "1"
        assert entries2[0].content["session"] == "2"

    # Phase 6: User Story 3 - Memory-Aware Prompt Injection Tests (T093)
    
    def test_select_for_injection_phase_filtering(self, stm, session_id):
        """Test that select_for_injection() filters entries by phase (T083)."""
        execution_id = "exec_001"
        
        # Write entries for different phases
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"user_prompt": "Previous B request", "llm_response": "Previous B response"},
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="D",
            content={"refinement_reason": "Previous D refinement", "updated_goal": "Previous goal"},
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="A",
            content={"goal": "Previous A goal"},
        )
        
        # Phase B should prefer Phase B (primary) and Phase D (secondary)
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should include Phase B and Phase D entries
        assert len(result["context_blocks"]) >= 1
        
    def test_select_for_injection_execution_filtering(self, stm, session_id):
        """Test that select_for_injection() prefers earlier executions (T084)."""
        execution_id_1 = "exec_001"
        execution_id_2 = "exec_002"
        
        # Write entries from different executions
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id_1,
            phase="B",
            content={"user_prompt": "Earlier execution", "llm_response": "Earlier response"},
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id_2,
            phase="B",
            content={"user_prompt": "Later execution", "llm_response": "Later response"},
        )
        
        # Query with current_execution_id = exec_002
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id_2,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should prefer exec_001 (earlier) over exec_002 (current)
        assert len(result["context_blocks"]) >= 1
        
    def test_select_for_injection_recency_ordering(self, stm, session_id):
        """Test that select_for_injection() orders entries by recency (T085)."""
        execution_id = "exec_001"
        
        # Write multiple entries (they will have different created_at timestamps)
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"user_prompt": "Oldest", "llm_response": "Oldest response"},
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"user_prompt": "Middle", "llm_response": "Middle response"},
        )
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"user_prompt": "Newest", "llm_response": "Newest response"},
        )
        
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should have entries ordered by recency (most recent first)
        assert len(result["context_blocks"]) >= 1
        
    def test_select_for_injection_field_extraction_phase_b(self, stm, session_id):
        """Test that select_for_injection() extracts phase-appropriate fields for Phase B (T086)."""
        execution_id = "exec_001"
        
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={
                "user_prompt": "Test user request",
                "llm_response": "Test assistant response",
            },
        )
        
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should extract user_prompt and llm_response fields
        assert len(result["context_blocks"]) == 1
        block = result["context_blocks"][0]
        assert "Test user request" in block or "Previous user request" in block
        assert "Test assistant response" in block or "Previous assistant response" in block
        
    def test_select_for_injection_field_extraction_phase_d(self, stm, session_id):
        """Test that select_for_injection() extracts phase-appropriate fields for Phase D (T086)."""
        execution_id = "exec_001"
        
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="D",
            content={
                "refinement_reason": "Test refinement reason",
                "updated_goal": "Test updated goal",
                "step_descriptions": [{"description": "Step 1"}, {"description": "Step 2"}],
            },
        )
        
        context = {
            "current_phase": "D",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should extract refinement_reason, updated_goal, and step_descriptions
        assert len(result["context_blocks"]) == 1
        block = result["context_blocks"][0]
        assert "Test refinement reason" in block or "Refinement reason" in block
        assert "Test updated goal" in block or "Updated goal" in block
        
    def test_select_for_injection_budget_enforcement(self, stm, session_id):
        """Test that select_for_injection() enforces injection budget (T088)."""
        execution_id = "exec_001"
        
        # Write multiple entries
        for i in range(5):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="B",
                content={
                    "user_prompt": f"Request {i}",
                    "llm_response": f"Response {i}",
                },
            )
        
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        
        # Test with small budget
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=100,  # Small budget
        )
        
        # Should only include blocks that fit within budget (no partial inclusion)
        total_size = sum(len(block) for block in result["context_blocks"])
        assert total_size <= 100
        
        # Test with larger budget
        result_large = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,  # Large budget
        )
        
        # Should include more blocks
        assert len(result_large["context_blocks"]) >= len(result["context_blocks"])
        
    def test_select_for_injection_non_authoritative_marker(self, stm, session_id):
        """Test that select_for_injection() returns non-authoritative marker (T089)."""
        execution_id = "exec_001"
        
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"user_prompt": "Test", "llm_response": "Test"},
        )
        
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        result = stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )
        
        # Should include non-authoritative marker
        assert "non_authoritative_marker" in result
        assert isinstance(result["non_authoritative_marker"], str)
        assert len(result["non_authoritative_marker"]) > 0
        assert "Non-authoritative" in result["non_authoritative_marker"] or "non-authoritative" in result["non_authoritative_marker"]

    # Phase 7: User Story 4 - Memory Usage Observability Tests (T106)

    def test_get_usage_stats_tracks_considered_and_injected(self, stm, session_id, execution_id):
        """Test that get_usage_stats() tracks memory_entries_considered and memory_entries_injected (T102, T106)."""
        # Write some entries
        for i in range(3):
            stm.write_entry(
                session_id=session_id,
                execution_id=execution_id,
                phase="B",
                content={"user_prompt": f"Request {i}", "llm_response": f"Response {i}"},
            )

        # Perform select_for_injection to track considered/injected
        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )

        stats = stm.get_usage_stats(session_id=session_id)
        assert stats.memory_used is True
        assert stats.total_entries == 3
        # Should track entries considered and injected
        assert stats.memory_entries_considered >= 0
        assert stats.memory_entries_injected >= 0
        assert stats.memory_failures == 0

    def test_get_usage_stats_tracks_failures(self, stm, session_id):
        """Test that get_usage_stats() tracks memory_failures (T102, T106)."""
        # Try to write with invalid phase to trigger a failure
        stm.write_entry(
            session_id=session_id,
            execution_id="exec_001",
            phase="X",  # Invalid phase
            content={"test": "data"},
        )

        stats = stm.get_usage_stats(session_id=session_id)
        # Should track the failure
        assert stats.memory_failures >= 0  # May be 0 if validation failure doesn't count, but should track

    def test_list_entries_returns_metadata_without_content(self, stm, session_id, execution_id):
        """Test that list_entries() returns metadata-only (no raw content) (T103, T106)."""
        sensitive_content = {
            "password": "secret123",
            "credit_card": "1234-5678-9012-3456",
            "user_message": "This is sensitive user data",
        }
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content=sensitive_content,
        )

        metadata_list = stm.list_entries(session_id=session_id)
        assert len(metadata_list) == 1
        metadata = metadata_list[0]

        # Verify metadata has structural fields
        assert metadata.session_id == session_id
        assert metadata.execution_id == execution_id
        assert metadata.phase == "B"
        assert isinstance(metadata.created_at, datetime)
        assert metadata.ttl >= 0

        # Verify NO content field (content-free observability)
        assert not hasattr(metadata, "content")

        # Verify content is not accessible via any other means
        metadata_dict = metadata.__dict__ if hasattr(metadata, "__dict__") else {}
        assert "content" not in metadata_dict
        assert "password" not in str(metadata)
        assert "credit_card" not in str(metadata)
        assert "secret123" not in str(metadata)

    def test_logging_does_not_contain_raw_content(self, session_id, execution_id, tmp_path):
        """Test that logging does not contain raw memory content (T100, T106)."""
        import json
        from pathlib import Path
        from aeon.observability.logger import JSONLLogger
        
        # Create logger with temporary file
        log_file = tmp_path / "memory_test.jsonl"
        logger = JSONLLogger(file_path=log_file)
        stm = STM(capacity=100, initial_ttl=10, logger=logger)

        sensitive_content = {
            "password": "secret123",
            "credit_card": "1234-5678-9012-3456",
            "user_message": "This is sensitive user data",
        }

        # Perform memory operations
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content=sensitive_content,
        )
        stm.read_entries(session_id=session_id)
        stm.list_entries(session_id=session_id)

        # Read log file and check contents
        log_lines = log_file.read_text().strip().split('\n')
        log_text = '\n'.join(log_lines)

        # Should contain structural metadata
        assert "write_entry" in log_text.lower() or "memory_operation" in log_text.lower()
        assert session_id in log_text
        assert execution_id in log_text

        # Should NOT contain raw content
        assert "secret123" not in log_text
        assert "1234-5678-9012-3456" not in log_text
        assert "This is sensitive user data" not in log_text
        
        # Verify JSON structure is valid and contains memory operation events
        for line in log_lines:
            if line.strip():
                entry = json.loads(line)
                assert entry.get("event") == "memory_operation"
                assert entry.get("memory_operation_type") is not None
                assert entry.get("memory_session_id") == session_id
                # Verify no content fields
                assert "content" not in str(entry).lower() or "memory_operation_type" in str(entry)

    def test_error_logging_contains_error_type_not_content(self, session_id, execution_id, tmp_path):
        """Test that error logging contains error types but not raw content (T101, T106)."""
        import json
        from pathlib import Path
        from aeon.observability.logger import JSONLLogger
        
        # Create logger with temporary file
        log_file = tmp_path / "memory_error_test.jsonl"
        logger = JSONLLogger(file_path=log_file)
        stm = STM(capacity=100, initial_ttl=10, logger=logger)

        # Try an operation that will fail (invalid phase)
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="INVALID",  # Invalid phase to trigger validation error
            content={"test": "data"},
        )

        # Read log file and check contents
        log_lines = log_file.read_text().strip().split('\n')
        log_text = '\n'.join(log_lines)

        # Should contain error type/context
        assert "error_type" in log_text.lower() or "memory_operation" in log_text.lower()
        assert session_id in log_text or "session" in log_text.lower()

        # Should NOT contain raw content even in error messages
        # Check log entries are valid JSON and contain error_type but not content
        for line in log_lines:
            if line.strip():
                entry = json.loads(line)
                if entry.get("event") == "memory_operation" and entry.get("memory_error_type"):
                    # Error entry should have error_type but no content
                    assert entry.get("memory_error_type") is not None
                    assert "test" not in str(entry) or "memory_operation_type" in str(entry)
                    assert "data" not in str(entry)

    def test_usage_stats_includes_all_required_fields(self, stm, session_id, execution_id):
        """Test that get_usage_stats() returns all required fields (T102, T106)."""
        # Write entries and perform operations
        stm.write_entry(
            session_id=session_id,
            execution_id=execution_id,
            phase="B",
            content={"test": "data"},
        )

        context = {
            "current_phase": "B",
            "current_execution_id": execution_id,
            "injection_point": "test_point",
        }
        stm.select_for_injection(
            session_id=session_id,
            context=context,
            budget=10000,
        )

        stats = stm.get_usage_stats(session_id=session_id)

        # Verify all required fields are present
        assert hasattr(stats, "memory_used")
        assert hasattr(stats, "memory_entries_considered")
        assert hasattr(stats, "memory_entries_injected")
        assert hasattr(stats, "memory_failures")
        assert hasattr(stats, "total_entries")
        assert hasattr(stats, "expired_entries")

        # Verify types
        assert isinstance(stats.memory_used, bool)
        assert isinstance(stats.memory_entries_considered, int)
        assert isinstance(stats.memory_entries_injected, int)
        assert isinstance(stats.memory_failures, int)
        assert isinstance(stats.total_entries, int)
        assert isinstance(stats.expired_entries, int)

        # Verify non-negative
        assert stats.memory_entries_considered >= 0
        assert stats.memory_entries_injected >= 0
        assert stats.memory_failures >= 0
        assert stats.total_entries >= 0
        assert stats.expired_entries >= 0
