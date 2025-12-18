"""Session subsystem data models.

This module defines the data models for session lifecycle management,
including Session, SessionState, SessionMetadata, and SessionCloseResult.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """Represents a single session with its lifecycle state."""

    session_id: str  # Unique identifier for the session (required)
    state: str  # Current session state: "active", "expired", "closed" (required)
    ttl: int  # Current Session TTL value (decrements on execution completion) (required)
    created_at: datetime  # Session creation timestamp (required)


@dataclass
class SessionState:
    """Result of session state query operations."""

    session_id: str  # Session identifier (required)
    state: str  # Current session state ("active", "expired", "closed") (required)
    ttl: Optional[int] = None  # Current Session TTL value (if state is "active")


@dataclass
class SessionMetadata:
    """Metadata about a session for audit purposes."""

    session_id: str  # Session identifier (required)
    state: str  # Current session state ("active", "expired", "closed") (required)
    created_at: datetime  # Session creation timestamp (required)


@dataclass
class SessionCloseResult:
    """Result of session close operation."""

    success: bool  # Whether close succeeded (required)
    error: Optional[str] = None  # Error message (if failed, for logging only)
