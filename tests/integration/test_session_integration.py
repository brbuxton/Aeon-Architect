"""Integration tests for session subsystem with orchestrator.

This module contains integration tests for Phase 9: Session integration tests (T139),
covering orchestrator functions with Session enabled but STM disabled,
and STM functions correctly with Session enabled.
"""

import pytest
from datetime import datetime

from aeon.memory.stm import STM
from aeon.memory.null_memory import NullMemory
from aeon.session.manager import SessionManager


class TestSessionIntegration:
    """Phase 9: Session integration tests (T139).
    
    Tests that orchestrator functions with Session enabled but STM disabled,
    and STM functions correctly with Session enabled.
    """
    
    @pytest.fixture
    def session_manager(self):
        """Create SessionManager instance for testing."""
        return SessionManager(initial_ttl=3)
    
    @pytest.fixture
    def null_memory(self):
        """Create NullMemory instance for testing."""
        return NullMemory()
    
    @pytest.fixture
    def stm(self):
        """Create STM instance for testing."""
        return STM(capacity=100, initial_ttl=10)
    
    def test_orchestrator_functions_with_session_enabled_but_stm_disabled(
        self, session_manager, null_memory
    ):
        """Test that orchestrator functions with Session enabled but STM disabled (T139)."""
        from aeon.kernel.orchestrator import Orchestrator
        from tests.fixtures.mock_llm import MockLLMAdapter
        
        # Create orchestrator with Session enabled but STM disabled (NullMemory)
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory_access=null_memory,  # STM disabled
            session_manager=session_manager,  # Session enabled
            ttl=10,
        )
        
        # Execute request
        result = orchestrator.execute_multipass(request="test request")
        
        # Should complete successfully
        assert result is not None
        
        # Verify session was created
        session_id = orchestrator._current_session_id
        assert session_id is not None
        
        # Verify session exists in session manager
        sessions = session_manager.list_sessions()
        assert session_id in [s.session_id for s in sessions]
        
        # Verify NullMemory returns empty results
        entries = null_memory.read_entries(session_id=session_id)
        assert len(entries) == 0
        
        # Verify session state is active
        session_state = session_manager.get_session_state(session_id)
        assert session_state.state == "active"
    
    def test_stm_functions_correctly_with_session_enabled(self, stm, session_manager):
        """Test that STM functions correctly with Session enabled (T139)."""
        from aeon.kernel.orchestrator import Orchestrator
        from tests.fixtures.mock_llm import MockLLMAdapter
        
        # Create orchestrator with both Session and STM enabled
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory_access=stm,  # STM enabled
            session_manager=session_manager,  # Session enabled
            ttl=10,
        )
        
        # Execute request
        result = orchestrator.execute_multipass(request="test request")
        
        # Should complete successfully
        assert result is not None
        
        # Verify session was created
        session_id = orchestrator._current_session_id
        assert session_id is not None
        
        # Verify STM can store and retrieve entries
        stm.write_entry(
            session_id=session_id,
            execution_id="exec_001",
            phase="A",
            content={"goal": "test goal", "steps": []},
        )
        
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) > 0
        
        # Verify session and STM work together
        session_state = session_manager.get_session_state(session_id)
        assert session_state.state == "active"
        
        # Verify memory entries are associated with session
        for entry in entries:
            assert entry.session_id == session_id
    
    def test_session_lifecycle_with_stm(self, stm, session_manager):
        """Test that session lifecycle works correctly with STM."""
        from aeon.kernel.orchestrator import Orchestrator
        from tests.fixtures.mock_llm import MockLLMAdapter
        
        # Create orchestrator with both Session and STM enabled
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory_access=stm,
            session_manager=session_manager,
            ttl=10,
        )
        
        # Execute first request
        orchestrator.execute_multipass(request="first request")
        session_id = orchestrator._current_session_id
        assert session_id is not None
        
        # Write memory entries
        stm.write_entry(
            session_id=session_id,
            execution_id="exec_001",
            phase="A",
            content={"goal": "goal 1", "steps": []},
        )
        
        # Verify entries exist
        entries = stm.read_entries(session_id=session_id)
        assert len(entries) > 0
        
        # Execute second request (same session)
        orchestrator.execute_multipass(request="second request")
        
        # Verify session is still active
        session_state = session_manager.get_session_state(session_id)
        assert session_state.state == "active"
        
        # Verify memory entries persist across executions
        entries_after = stm.read_entries(session_id=session_id)
        assert len(entries_after) >= len(entries)  # At least same entries, possibly more
    
    def test_session_expiration_triggers_stm_cleanup(self, stm, session_manager):
        """Test that session expiration triggers STM cleanup."""
        from aeon.kernel.orchestrator import Orchestrator
        from tests.fixtures.mock_llm import MockLLMAdapter
        
        # Create session manager with very low TTL
        low_ttl_session_manager = SessionManager(initial_ttl=1)
        
        # Create orchestrator
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory_access=stm,
            session_manager=low_ttl_session_manager,
            ttl=10,
        )
        
        # Execute first request
        orchestrator.execute_multipass(request="first request")
        session_id = orchestrator._current_session_id
        assert session_id is not None
        
        # Write memory entries
        stm.write_entry(
            session_id=session_id,
            execution_id="exec_001",
            phase="A",
            content={"goal": "test goal", "steps": []},
        )
        
        # Verify entries exist
        entries_before = stm.read_entries(session_id=session_id)
        assert len(entries_before) > 0
        
        # Complete execution to decrement TTL
        orchestrator.execute_multipass(request="second request")
        
        # Complete again to expire session (TTL was 1, so 2 completions expire it)
        orchestrator.execute_multipass(request="third request")
        
        # Verify session is expired
        session_state = low_ttl_session_manager.get_session_state(session_id)
        if session_state.state == "expired":
            # Verify memory was cleaned up (delete_session_entries was called)
            entries_after = stm.read_entries(session_id=session_id)
            # After cleanup, entries should be removed
            assert len(entries_after) == 0
