"""Contract tests for Session Subsystem Interface."""

import pytest

from aeon.session.interface import SessionSubsystemInterface
from aeon.session.manager import SessionManager
from aeon.session.models import SessionCloseResult, SessionMetadata, SessionState


class TestSessionSubsystemInterface:
    """Contract tests verifying Session Subsystem Interface compliance."""

    @pytest.fixture
    def session_manager(self):
        """Create SessionManager instance for testing."""
        return SessionManager(initial_ttl=3)

    def test_interface_has_create_session_method(self, session_manager):
        """Test that SessionSubsystemInterface implementation has create_session() method."""
        assert hasattr(session_manager, "create_session")
        assert callable(session_manager.create_session)

    def test_interface_has_notify_execution_complete_method(self, session_manager):
        """Test that SessionSubsystemInterface implementation has notify_execution_complete() method."""
        assert hasattr(session_manager, "notify_execution_complete")
        assert callable(session_manager.notify_execution_complete)

    def test_interface_has_get_session_state_method(self, session_manager):
        """Test that SessionSubsystemInterface implementation has get_session_state() method."""
        assert hasattr(session_manager, "get_session_state")
        assert callable(session_manager.get_session_state)

    def test_interface_has_list_sessions_method(self, session_manager):
        """Test that SessionSubsystemInterface implementation has list_sessions() method."""
        assert hasattr(session_manager, "list_sessions")
        assert callable(session_manager.list_sessions)

    def test_interface_has_close_session_method(self, session_manager):
        """Test that SessionSubsystemInterface implementation has close_session() method."""
        assert hasattr(session_manager, "close_session")
        assert callable(session_manager.close_session)

    def test_create_session_returns_string(self, session_manager):
        """Test that create_session() returns a string (session_id)."""
        session_id = session_manager.create_session()
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_create_session_returns_unique_session_ids(self, session_manager):
        """Test that create_session() returns unique session_id values."""
        session_id1 = session_manager.create_session()
        session_id2 = session_manager.create_session()
        assert session_id1 != session_id2

    def test_notify_execution_complete_returns_session_state(self, session_manager):
        """Test that notify_execution_complete() returns SessionState."""
        session_id = session_manager.create_session()
        state = session_manager.notify_execution_complete(session_id)
        assert isinstance(state, SessionState)
        assert state.session_id == session_id
        assert state.state in ["active", "expired", "closed"]
        # TTL should be present if state is active, None otherwise
        if state.state == "active":
            assert state.ttl is not None
            assert isinstance(state.ttl, int)
            assert state.ttl >= 0
        else:
            assert state.ttl is None

    def test_notify_execution_complete_decrements_ttl(self, session_manager):
        """Test that notify_execution_complete() decrements Session TTL."""
        session_id = session_manager.create_session()
        
        # Get initial state
        initial_state = session_manager.get_session_state(session_id)
        initial_ttl = initial_state.ttl
        assert initial_ttl is not None

        # Notify execution complete
        state = session_manager.notify_execution_complete(session_id)
        assert state.ttl is not None
        assert state.ttl == initial_ttl - 1

    def test_notify_execution_complete_detects_expiration(self, session_manager):
        """Test that notify_execution_complete() detects expiration when TTL reaches zero."""
        session_id = session_manager.create_session()
        
        # Decrement TTL until expiration
        for _ in range(3):  # initial_ttl is 3
            state = session_manager.notify_execution_complete(session_id)
        
        # After 3 decrements, session should be expired
        state = session_manager.get_session_state(session_id)
        assert state.state == "expired"
        assert state.ttl is None

    def test_notify_execution_complete_handles_nonexistent_session(self, session_manager):
        """Test that notify_execution_complete() handles nonexistent session gracefully."""
        state = session_manager.notify_execution_complete("nonexistent_session_id")
        assert isinstance(state, SessionState)
        assert state.state == "expired"
        assert state.ttl is None

    def test_get_session_state_returns_session_state(self, session_manager):
        """Test that get_session_state() returns SessionState."""
        session_id = session_manager.create_session()
        state = session_manager.get_session_state(session_id)
        assert isinstance(state, SessionState)
        assert state.session_id == session_id
        assert state.state in ["active", "expired", "closed"]

    def test_get_session_state_returns_expired_for_nonexistent_session(self, session_manager):
        """Test that get_session_state() returns expired state for nonexistent session."""
        state = session_manager.get_session_state("nonexistent_session_id")
        assert isinstance(state, SessionState)
        assert state.state == "expired"
        assert state.ttl is None

    def test_list_sessions_returns_list_of_session_metadata(self, session_manager):
        """Test that list_sessions() returns List[SessionMetadata]."""
        session_id1 = session_manager.create_session()
        session_id2 = session_manager.create_session()
        
        sessions = session_manager.list_sessions()
        assert isinstance(sessions, list)
        assert len(sessions) >= 2

        # Verify all items are SessionMetadata
        for session in sessions:
            assert isinstance(session, SessionMetadata)
            assert hasattr(session, "session_id")
            assert hasattr(session, "state")
            assert hasattr(session, "created_at")
            assert session.state in ["active", "expired", "closed"]

        # Verify created sessions are in the list
        session_ids = {s.session_id for s in sessions}
        assert session_id1 in session_ids
        assert session_id2 in session_ids

    def test_list_sessions_returns_empty_list_when_no_sessions(self):
        """Test that list_sessions() returns empty list when no sessions exist."""
        manager = SessionManager()
        sessions = manager.list_sessions()
        assert isinstance(sessions, list)
        assert sessions == []

    def test_close_session_returns_session_close_result(self, session_manager):
        """Test that close_session() returns SessionCloseResult."""
        session_id = session_manager.create_session()
        result = session_manager.close_session(session_id)
        assert isinstance(result, SessionCloseResult)
        assert hasattr(result, "success")
        assert hasattr(result, "error")
        assert isinstance(result.success, bool)

    def test_close_session_marks_session_as_closed(self, session_manager):
        """Test that close_session() marks session as closed."""
        session_id = session_manager.create_session()
        result = session_manager.close_session(session_id)
        assert result.success is True

        state = session_manager.get_session_state(session_id)
        assert state.state == "closed"

    def test_close_session_handles_nonexistent_session(self, session_manager):
        """Test that close_session() handles nonexistent session gracefully."""
        result = session_manager.close_session("nonexistent_session_id")
        assert isinstance(result, SessionCloseResult)
        assert result.success is False
        assert result.error is not None

    def test_graceful_degradation_no_exceptions_raised(self, session_manager):
        """Test that all methods never raise exceptions (graceful degradation)."""
        # create_session() should never raise
        session_id = session_manager.create_session()
        assert session_id is not None

        # get_session_state() should never raise, even with invalid input
        state1 = session_manager.get_session_state(session_id)
        assert isinstance(state1, SessionState)
        
        state2 = session_manager.get_session_state("invalid")
        assert isinstance(state2, SessionState)

        # notify_execution_complete() should never raise
        state3 = session_manager.notify_execution_complete(session_id)
        assert isinstance(state3, SessionState)

        state4 = session_manager.notify_execution_complete("invalid")
        assert isinstance(state4, SessionState)

        # list_sessions() should never raise
        sessions = session_manager.list_sessions()
        assert isinstance(sessions, list)

        # close_session() should never raise
        result1 = session_manager.close_session(session_id)
        assert isinstance(result1, SessionCloseResult)

        result2 = session_manager.close_session("invalid")
        assert isinstance(result2, SessionCloseResult)

    def test_session_state_transitions_active_to_expired(self, session_manager):
        """Test that session state transitions correctly from active to expired."""
        session_id = session_manager.create_session()
        
        # Initial state: active
        state = session_manager.get_session_state(session_id)
        assert state.state == "active"
        assert state.ttl is not None

        # Decrement TTL until expiration
        for _ in range(3):  # initial_ttl is 3
            state = session_manager.notify_execution_complete(session_id)

        # After expiration: expired
        state = session_manager.get_session_state(session_id)
        assert state.state == "expired"
        assert state.ttl is None

    def test_session_state_transitions_to_closed(self, session_manager):
        """Test that session state transitions correctly to closed."""
        session_id = session_manager.create_session()
        
        # Close active session
        result = session_manager.close_session(session_id)
        assert result.success is True

        state = session_manager.get_session_state(session_id)
        assert state.state == "closed"
        assert state.ttl is None

    def test_session_state_transitions_expired_to_closed(self, session_manager):
        """Test that expired session can be closed."""
        session_id = session_manager.create_session()
        
        # Expire the session
        for _ in range(3):
            session_manager.notify_execution_complete(session_id)

        # Close expired session
        result = session_manager.close_session(session_id)
        assert result.success is True

        state = session_manager.get_session_state(session_id)
        assert state.state == "closed"

    def test_interface_compliance_session_manager_implements_interface(self):
        """Test that SessionManager implements SessionSubsystemInterface."""
        manager = SessionManager()
        assert isinstance(manager, SessionSubsystemInterface)

    def test_contract_session_id_uniqueness(self, session_manager):
        """Test contract: session_id must be unique across all sessions."""
        session_ids = set()
        for _ in range(10):
            session_id = session_manager.create_session()
            assert session_id not in session_ids, "Session IDs must be unique"
            session_ids.add(session_id)

    def test_contract_session_state_values(self, session_manager):
        """Test contract: session state must be one of: active, expired, closed."""
        session_id = session_manager.create_session()
        
        # Active state
        state = session_manager.get_session_state(session_id)
        assert state.state in ["active", "expired", "closed"]

        # Expired state
        for _ in range(3):
            session_manager.notify_execution_complete(session_id)
        state = session_manager.get_session_state(session_id)
        assert state.state in ["active", "expired", "closed"]

        # Closed state
        session_manager.close_session(session_id)
        state = session_manager.get_session_state(session_id)
        assert state.state in ["active", "expired", "closed"]
