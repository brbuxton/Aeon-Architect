"""Session subsystem interface.

This module defines the abstract interface for session lifecycle management,
including session creation, state tracking, and TTL management.
"""

from abc import ABC, abstractmethod
from typing import List

from aeon.session.models import SessionCloseResult, SessionMetadata, SessionState


class SessionSubsystemInterface(ABC):
    """Abstract interface for session lifecycle management."""

    @abstractmethod
    def create_session(self) -> str:
        """
        Issue a unique session_id for a new session.

        Returns:
            Unique session_id string

        Note:
            - Session_id must be unique across all sessions
            - Session subsystem assigns initial Session TTL value (configurable, default: 3)
            - Never raises exceptions (graceful degradation)
        """
        pass

    @abstractmethod
    def notify_execution_complete(self, session_id: str) -> SessionState:
        """
        Notify session subsystem that an execution completed (Phase E).
        Session subsystem autonomously decrements Session TTL and detects expiration.

        Args:
            session_id: Session to notify (required)

        Returns:
            SessionState with:
                - session_id: str - Session identifier
                - state: str - Current session state ("active", "expired", "closed")
                - ttl: Optional[int] - Current Session TTL value (if state is "active")

        Note:
            - Session subsystem autonomously decrements Session TTL for that session_id
            - Session subsystem autonomously detects when Session TTL is exhausted
            - When Session TTL is exhausted, session subsystem marks session as expired,
              cleans up session_id internally, and returns expired status
            - Orchestrator has no knowledge of Session TTL values, decrement logic, or expiration detection
            - Never raises exceptions (graceful degradation)
        """
        pass

    @abstractmethod
    def get_session_state(self, session_id: str) -> SessionState:
        """
        Get current session state.

        Args:
            session_id: Session to query (required)

        Returns:
            SessionState with session_id, state, and optional ttl

        Note:
            - Never raises exceptions (graceful degradation)
            - Returns expired/closed state if session does not exist
        """
        pass

    @abstractmethod
    def list_sessions(self) -> List[SessionMetadata]:
        """
        List all current sessions (active, expired, and closed) for audit purposes.

        Returns:
            List of SessionMetadata objects (session_id, state, created_at).
            Empty list if no sessions.

        Note:
            - Returns metadata only (no internal implementation details)
            - Never raises exceptions (graceful degradation)
        """
        pass

    @abstractmethod
    def close_session(self, session_id: str) -> SessionCloseResult:
        """
        Gracefully close/terminate a session when triggered by presentation/client
        requests or host-defined termination policies (before TTL expiration).

        Args:
            session_id: Session to close (required)

        Returns:
            SessionCloseResult with:
                - success: bool - Whether close succeeded
                - error: Optional[str] - Error message (if failed, for logging only)

        Note:
            - Session subsystem releases all associated resources and marks session as no longer accessible
            - Never raises exceptions (graceful degradation)
            - Used for graceful shutdown (distinct from TTL expiration)
        """
        pass
