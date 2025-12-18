"""Session subsystem module.

This module provides session lifecycle management for Aeon, including
session creation, state tracking, and TTL management.
"""

from aeon.session.interface import SessionSubsystemInterface
from aeon.session.manager import SessionManager
from aeon.session.models import (
    Session,
    SessionCloseResult,
    SessionMetadata,
    SessionState,
)

__all__ = [
    "SessionSubsystemInterface",
    "SessionManager",
    "Session",
    "SessionState",
    "SessionMetadata",
    "SessionCloseResult",
]
