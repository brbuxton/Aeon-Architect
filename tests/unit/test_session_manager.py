"""Unit tests for SessionManager."""

import pytest
from datetime import datetime

from aeon.session.manager import SessionManager
from aeon.session.models import SessionState


class TestSessionManager:
    """Tests for SessionManager session lifecycle management."""

    def test_create_session_returns_unique_session_id(self):
        """Test that create_session() returns unique session_id."""
        manager = SessionManager()
        session_id1 = manager.create_session()
        session_id2 = manager.create_session()

        # Session IDs should be unique
        assert session_id1 != session_id2
        assert isinstance(session_id1, str)
        assert isinstance(session_id2, str)
        assert len(session_id1) > 0
        assert len(session_id2) > 0

    def test_create_session_initializes_session_with_active_state(self):
        """Test that create_session() initializes session with active state and initial TTL."""
        manager = SessionManager(initial_ttl=5)
        session_id = manager.create_session()

        state = manager.get_session_state(session_id)
        assert state.state == "active"
        assert state.ttl == 5
        assert state.session_id == session_id

    def test_get_session_state_returns_active_state(self):
        """Test that get_session_state() returns correct state for active session."""
        manager = SessionManager(initial_ttl=3)
        session_id = manager.create_session()

        state = manager.get_session_state(session_id)
        assert state.session_id == session_id
        assert state.state == "active"
        assert state.ttl == 3

    def test_get_session_state_returns_expired_for_nonexistent_session(self):
        """Test that get_session_state() returns expired state for nonexistent session."""
        manager = SessionManager()
        state = manager.get_session_state("nonexistent_session_id")

        assert state.session_id == "nonexistent_session_id"
        assert state.state == "expired"
        assert state.ttl is None

    def test_notify_execution_complete_decrements_ttl(self):
        """Test that notify_execution_complete() decrements Session TTL."""
        manager = SessionManager(initial_ttl=3)
        session_id = manager.create_session()

        # First notification
        state1 = manager.notify_execution_complete(session_id)
        assert state1.state == "active"
        assert state1.ttl == 2

        # Second notification
        state2 = manager.notify_execution_complete(session_id)
        assert state2.state == "active"
        assert state2.ttl == 1

        # Third notification (TTL reaches 0, should expire)
        state3 = manager.notify_execution_complete(session_id)
        assert state3.state == "expired"
        assert state3.ttl is None

    def test_notify_execution_complete_detects_expiration(self):
        """Test that notify_execution_complete() detects expiration when TTL reaches zero."""
        manager = SessionManager(initial_ttl=2)
        session_id = manager.create_session()

        # First notification (TTL: 2 -> 1)
        state1 = manager.notify_execution_complete(session_id)
        assert state1.state == "active"
        assert state1.ttl == 1

        # Second notification (TTL: 1 -> 0, should expire)
        state2 = manager.notify_execution_complete(session_id)
        assert state2.state == "expired"
        assert state2.ttl is None

        # Third notification (already expired)
        state3 = manager.notify_execution_complete(session_id)
        assert state3.state == "expired"
        assert state3.ttl is None

    def test_notify_execution_complete_handles_nonexistent_session(self):
        """Test that notify_execution_complete() handles nonexistent session gracefully."""
        manager = SessionManager()
        state = manager.notify_execution_complete("nonexistent_session_id")

        assert state.session_id == "nonexistent_session_id"
        assert state.state == "expired"
        assert state.ttl is None

    def test_notify_execution_complete_does_not_decrement_expired_session(self):
        """Test that notify_execution_complete() does not decrement TTL for expired session."""
        manager = SessionManager(initial_ttl=1)
        session_id = manager.create_session()

        # Expire the session
        manager.notify_execution_complete(session_id)
        state1 = manager.get_session_state(session_id)
        assert state1.state == "expired"

        # Try to notify again - should remain expired
        state2 = manager.notify_execution_complete(session_id)
        assert state2.state == "expired"
        assert state2.ttl is None

    def test_list_sessions_returns_all_sessions(self):
        """Test that list_sessions() returns all current sessions."""
        manager = SessionManager()
        session_id1 = manager.create_session()
        session_id2 = manager.create_session()

        sessions = manager.list_sessions()
        assert len(sessions) == 2

        session_ids = {s.session_id for s in sessions}
        assert session_id1 in session_ids
        assert session_id2 in session_ids

        # Verify metadata structure
        for session in sessions:
            assert hasattr(session, "session_id")
            assert hasattr(session, "state")
            assert hasattr(session, "created_at")
            assert isinstance(session.created_at, datetime)

    def test_list_sessions_returns_empty_list_when_no_sessions(self):
        """Test that list_sessions() returns empty list when no sessions exist."""
        manager = SessionManager()
        sessions = manager.list_sessions()
        assert sessions == []

    def test_list_sessions_includes_expired_sessions(self):
        """Test that list_sessions() includes expired sessions."""
        manager = SessionManager(initial_ttl=1)
        session_id = manager.create_session()

        # Expire the session
        manager.notify_execution_complete(session_id)

        sessions = manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == session_id
        assert sessions[0].state == "expired"

    def test_close_session_marks_session_as_closed(self):
        """Test that close_session() marks session as closed."""
        manager = SessionManager()
        session_id = manager.create_session()

        result = manager.close_session(session_id)
        assert result.success is True

        state = manager.get_session_state(session_id)
        assert state.state == "closed"
        assert state.ttl is None

    def test_close_session_handles_nonexistent_session(self):
        """Test that close_session() handles nonexistent session gracefully."""
        manager = SessionManager()
        result = manager.close_session("nonexistent_session_id")

        assert result.success is False
        assert result.error is not None
        assert "does not exist" in result.error

    def test_close_session_handles_already_closed_session(self):
        """Test that close_session() handles already closed session gracefully."""
        manager = SessionManager()
        session_id = manager.create_session()

        # Close once
        result1 = manager.close_session(session_id)
        assert result1.success is True

        # Close again
        result2 = manager.close_session(session_id)
        assert result2.success is True

        state = manager.get_session_state(session_id)
        assert state.state == "closed"

    def test_close_session_handles_already_expired_session(self):
        """Test that close_session() handles already expired session."""
        manager = SessionManager(initial_ttl=1)
        session_id = manager.create_session()

        # Expire the session
        manager.notify_execution_complete(session_id)

        # Try to close expired session
        result = manager.close_session(session_id)
        assert result.success is True

        state = manager.get_session_state(session_id)
        assert state.state == "closed"

    def test_session_state_tracking_works_correctly(self):
        """Test that session state tracking works correctly (active -> expired -> closed)."""
        manager = SessionManager(initial_ttl=2)
        session_id = manager.create_session()

        # Initial state: active
        state1 = manager.get_session_state(session_id)
        assert state1.state == "active"
        assert state1.ttl == 2

        # After one execution: still active
        manager.notify_execution_complete(session_id)
        state2 = manager.get_session_state(session_id)
        assert state2.state == "active"
        assert state2.ttl == 1

        # After two executions: expired
        manager.notify_execution_complete(session_id)
        state3 = manager.get_session_state(session_id)
        assert state3.state == "expired"
        assert state3.ttl is None

        # Close expired session: closed
        manager.close_session(session_id)
        state4 = manager.get_session_state(session_id)
        assert state4.state == "closed"
        assert state4.ttl is None

    def test_session_ttl_decrements_on_execution_completion(self):
        """Test that Session TTL decrements on execution completion notification."""
        manager = SessionManager(initial_ttl=5)
        session_id = manager.create_session()

        # Verify initial TTL
        state = manager.get_session_state(session_id)
        assert state.ttl == 5

        # Notify execution completion multiple times
        for expected_ttl in [4, 3, 2, 1]:
            state = manager.notify_execution_complete(session_id)
            assert state.ttl == expected_ttl
            assert state.state == "active"

        # Final notification (TTL reaches 0, should expire)
        state = manager.notify_execution_complete(session_id)
        assert state.state == "expired"
        assert state.ttl is None

        # After TTL reaches 0, session should be expired
        state = manager.get_session_state(session_id)
        assert state.state == "expired"

    def test_session_subsystem_autonomously_detects_expiration(self):
        """Test that Session subsystem autonomously detects expiration and marks session as expired."""
        manager = SessionManager(initial_ttl=1)
        session_id = manager.create_session()

        # Notify execution completion (should expire)
        state = manager.notify_execution_complete(session_id)
        assert state.state == "expired"

        # Verify session is marked as expired internally
        state2 = manager.get_session_state(session_id)
        assert state2.state == "expired"
        assert state2.ttl is None

    def test_session_validity_checks_return_accurate_state(self):
        """Test that session validity checks return accurate state information."""
        manager = SessionManager(initial_ttl=3)
        session_id = manager.create_session()

        # Active session
        state = manager.get_session_state(session_id)
        assert state.state == "active"
        assert state.ttl == 3

        # After expiration
        manager.notify_execution_complete(session_id)
        manager.notify_execution_complete(session_id)
        manager.notify_execution_complete(session_id)

        state = manager.get_session_state(session_id)
        assert state.state == "expired"
        assert state.ttl is None

        # After closure
        manager.close_session(session_id)
        state = manager.get_session_state(session_id)
        assert state.state == "closed"
        assert state.ttl is None

    def test_graceful_degradation_all_methods_return_structured_results(self):
        """Test that all methods return structured results and never raise exceptions."""
        manager = SessionManager()

        # create_session() should never raise
        session_id = manager.create_session()
        assert isinstance(session_id, str)

        # get_session_state() should never raise
        state = manager.get_session_state(session_id)
        assert isinstance(state, SessionState)

        # notify_execution_complete() should never raise
        state = manager.notify_execution_complete(session_id)
        assert isinstance(state, SessionState)

        # list_sessions() should never raise
        sessions = manager.list_sessions()
        assert isinstance(sessions, list)

        # close_session() should never raise
        result = manager.close_session(session_id)
        assert hasattr(result, "success")
        assert hasattr(result, "error")

    def test_graceful_degradation_handles_invalid_inputs(self):
        """Test that graceful degradation handles invalid inputs."""
        manager = SessionManager()

        # Invalid session_id should return expired state
        state = manager.get_session_state("")
        assert state.state == "expired"

        state = manager.get_session_state(None)  # type: ignore
        assert state.state == "expired"

        # Invalid session_id in notify_execution_complete
        state = manager.notify_execution_complete("")
        assert state.state == "expired"

        # Invalid session_id in close_session
        result = manager.close_session("")
        assert result.success is False

    def test_multiple_sessions_independent_ttl_management(self):
        """Test that multiple sessions have independent TTL management."""
        manager = SessionManager(initial_ttl=3)
        session_id1 = manager.create_session()
        session_id2 = manager.create_session()

        # Decrement TTL for session1 only
        state1 = manager.notify_execution_complete(session_id1)
        assert state1.ttl == 2

        # Session2 should still have initial TTL
        state2 = manager.get_session_state(session_id2)
        assert state2.ttl == 3

        # Decrement TTL for session2
        state2 = manager.notify_execution_complete(session_id2)
        assert state2.ttl == 2

        # Session1 should still be at TTL 2
        state1 = manager.get_session_state(session_id1)
        assert state1.ttl == 2

    def test_custom_initial_ttl(self):
        """Test that SessionManager accepts custom initial TTL."""
        manager = SessionManager(initial_ttl=10)
        session_id = manager.create_session()

        state = manager.get_session_state(session_id)
        assert state.ttl == 10

        # Decrement multiple times
        for expected_ttl in [9, 8, 7, 6, 5]:
            state = manager.notify_execution_complete(session_id)
            assert state.ttl == expected_ttl
