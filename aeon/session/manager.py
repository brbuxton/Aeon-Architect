"""Session subsystem implementation.

This module implements the SessionManager class that manages session lifecycle,
including session creation, state tracking, and TTL management.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from aeon.session.interface import SessionSubsystemInterface
from aeon.session.models import (
    Session,
    SessionCloseResult,
    SessionMetadata,
    SessionState,
)

logger = logging.getLogger(__name__)


class SessionManager(SessionSubsystemInterface):
    """Implementation of Session Subsystem Interface.

    Manages session lifecycle autonomously, including session creation,
    state tracking, TTL management, and expiration detection.
    """

    def __init__(self, initial_ttl: int = 3) -> None:
        """
        Initialize SessionManager.

        Args:
            initial_ttl: Initial Session TTL value (default: 3).
                        TTL decrements on execution completion notification.
        """
        self._sessions: Dict[str, Session] = {}
        self._initial_ttl: int = initial_ttl

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
        try:
            # Generate unique session_id using UUID
            session_id = str(uuid4())

            # Create new session with initial state
            session = Session(
                session_id=session_id,
                state="active",
                ttl=self._initial_ttl,
                created_at=datetime.now(),
            )

            # Store session in-memory
            self._sessions[session_id] = session

            logger.debug(
                f"Created session: {session_id}, TTL: {self._initial_ttl}"
            )
            return session_id
        except Exception as e:
            # Graceful degradation: log error and return empty string
            logger.error(f"Failed to create session: {e}", exc_info=True)
            return ""

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
        try:
            # Check if session exists
            if session_id not in self._sessions:
                # Session does not exist, return expired state
                return SessionState(
                    session_id=session_id,
                    state="expired",
                    ttl=None,
                )

            session = self._sessions[session_id]

            # Only decrement TTL if session is active
            if session.state == "active":
                # Decrement TTL
                session.ttl -= 1

                # Check if TTL is exhausted
                if session.ttl <= 0:
                    # Mark session as expired and clean up
                    session.state = "expired"
                    session.ttl = 0
                    logger.debug(
                        f"Session expired: {session_id}, TTL exhausted"
                    )

                    # Return expired state
                    return SessionState(
                        session_id=session_id,
                        state="expired",
                        ttl=None,
                    )
                else:
                    # Session still active, return current state
                    logger.debug(
                        f"Session TTL decremented: {session_id}, TTL: {session.ttl}"
                    )
                    return SessionState(
                        session_id=session_id,
                        state="active",
                        ttl=session.ttl,
                    )
            else:
                # Session is not active (expired or closed), return current state
                return SessionState(
                    session_id=session_id,
                    state=session.state,
                    ttl=None,
                )
        except Exception as e:
            # Graceful degradation: log error and return expired state
            logger.error(
                f"Failed to notify execution complete for session {session_id}: {e}",
                exc_info=True,
            )
            return SessionState(
                session_id=session_id,
                state="expired",
                ttl=None,
            )

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
        try:
            # Check if session exists
            if session_id not in self._sessions:
                # Session does not exist, return expired state
                return SessionState(
                    session_id=session_id,
                    state="expired",
                    ttl=None,
                )

            session = self._sessions[session_id]

            # Return current state
            return SessionState(
                session_id=session_id,
                state=session.state,
                ttl=session.ttl if session.state == "active" else None,
            )
        except Exception as e:
            # Graceful degradation: log error and return expired state
            logger.error(
                f"Failed to get session state for {session_id}: {e}",
                exc_info=True,
            )
            return SessionState(
                session_id=session_id,
                state="expired",
                ttl=None,
            )

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
        try:
            # Convert sessions to metadata
            metadata_list = []
            for session in self._sessions.values():
                metadata = SessionMetadata(
                    session_id=session.session_id,
                    state=session.state,
                    created_at=session.created_at,
                )
                metadata_list.append(metadata)

            return metadata_list
        except Exception as e:
            # Graceful degradation: log error and return empty list
            logger.error(f"Failed to list sessions: {e}", exc_info=True)
            return []

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
        try:
            # Check if session exists
            if session_id not in self._sessions:
                # Session does not exist, return failure
                return SessionCloseResult(
                    success=False,
                    error=f"Session {session_id} does not exist",
                )

            session = self._sessions[session_id]

            # Check if session is already closed
            if session.state == "closed":
                # Session already closed, return success
                return SessionCloseResult(success=True)

            # Mark session as closed
            session.state = "closed"
            logger.debug(f"Session closed: {session_id}")

            # Note: We keep the session in _sessions for audit purposes
            # (list_sessions() can still return it). If needed, we could remove it,
            # but keeping it allows tracking of closed sessions.

            return SessionCloseResult(success=True)
        except Exception as e:
            # Graceful degradation: log error and return failure
            logger.error(
                f"Failed to close session {session_id}: {e}", exc_info=True
            )
            return SessionCloseResult(
                success=False,
                error=str(e),
            )
