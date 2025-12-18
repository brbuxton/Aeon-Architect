"""Memory interface.

This module defines both the legacy Memory interface (for backward compatibility)
and the new MemoryAccessInterface (MAI) for session-scoped memory operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from aeon.exceptions import MemoryError

if TYPE_CHECKING:
    from aeon.memory.models import (
        MemoryDeleteResult,
        MemoryEntry,
        MemoryEntryMetadata,
        MemoryUsageStats,
        MemoryWriteResult,
    )


class Memory(ABC):
    """Abstract interface for memory storage (legacy interface, kept for backward compatibility)."""

    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.

        Args:
            key: Unique identifier (non-empty string)
            value: Value to store (must be serializable)

        Raises:
            MemoryError: On storage failure
        """
        pass

    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.

        Args:
            key: Identifier to look up

        Returns:
            Stored value or None if key not found

        Raises:
            MemoryError: On read failure
        """
        pass

    @abstractmethod
    def search(self, prefix: str) -> List[Tuple[str, Any]]:
        """
        Find all keys starting with the given prefix.

        Args:
            prefix: Prefix to match

        Returns:
            List of (key, value) tuples for matching keys

        Raises:
            MemoryError: On search failure
        """
        pass


class MemoryAccessInterface(ABC):
    """Abstract interface for memory storage and retrieval (new MAI interface).

    This interface provides session-scoped memory operations with graceful degradation.
    All methods never raise exceptions and return structured results.
    """

    @abstractmethod
    def write_entry(
        self,
        session_id: str,
        execution_id: str,
        phase: str,
        content: Dict[str, Any],
    ) -> "MemoryWriteResult":
        """
        Store a memory entry with annotations.

        Args:
            session_id: Session owning the entry (required)
            execution_id: Execution (turn) that created the entry (required)
            phase: Phase (A, B, C, D, E) that created the entry (required)
            content: Phase-native, raw execution artifacts (JSON-compatible, required)

        Returns:
            MemoryWriteResult with:
                - success: bool - Whether write succeeded
                - entry_id: Optional[str] - Identifier of stored entry (if successful)
                - evicted_count: int - Number of entries evicted (if capacity exceeded)
                - error: Optional[str] - Error message (if failed, for logging only)

        Note:
            - Content MUST be phase-native, raw execution artifacts (no pre-summarization)
            - STM assigns TTL using deterministic default from configuration
            - Never raises exceptions (graceful degradation)
            - Validation failures degrade silently (entry not stored, failure logged)
        """
        pass

    @abstractmethod
    def read_entries(
        self,
        session_id: str,
        execution_id: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> List["MemoryEntry"]:
        """
        Retrieve memory entries matching filters.

        Args:
            session_id: Session to query (required)
            execution_id: Filter by execution_id (optional)
            phase: Filter by phase (optional)

        Returns:
            List of MemoryEntry objects matching filters. Empty list if no matches or on failure.

        Note:
            - Never raises exceptions (graceful degradation)
            - STM autonomously excludes expired entries (TTL ≤ 0) from results
            - Returns empty list on failure
        """
        pass

    @abstractmethod
    def select_for_injection(
        self,
        session_id: str,
        context: Dict[str, Any],
        budget: int,
    ) -> Dict[str, Any]:
        """
        Select relevant entries and emit a deterministic, field-extracted contextual
        projection for prompt injection.

        Args:
            session_id: Session to query (required)
            context: Selection context (required). MUST include:
                - current_phase: str (required) - Current phase (A, B, C, D, E)
                - current_execution_id: Optional[str] - Current execution ID (for excluding current execution)
                - injection_point: str (required) - Injection point identifier
            budget: Injection budget (hard upper bound, no truncation of individual entries)

        Returns:
            Dict with keys:
                - context_blocks: List[str] - List of formatted context strings/blocks ready for prompt injection
                - non_authoritative_marker: str - Single header/footer wrapper text marking context as non-authoritative

        Note:
            - STM performs field extraction, ordering, and light formatting only -
              NO semantic summarization, inference, or rewriting
            - STM excludes expired entries (TTL ≤ 0) before selection
            - STM filters by session_id and phase matching
            - STM prefers entries from earlier executions over current execution
            - STM orders selected entries by recency (created_at, most recent first)
            - STM applies injection budget as hard upper bound
            - Never raises exceptions (graceful degradation)
            - Returns empty structure on failure
        """
        pass

    @abstractmethod
    def get_usage_stats(self, session_id: str) -> "MemoryUsageStats":
        """
        Get memory usage statistics for observability.

        Args:
            session_id: Session to query (required)

        Returns:
            MemoryUsageStats with:
                - memory_used: bool - Whether memory was used in this execution
                - memory_entries_considered: int - Number of entries considered for injection
                - memory_entries_injected: int - Number of entries actually injected
                - memory_failures: int - Number of memory operation failures
                - total_entries: int - Total entries in session (for debugging)
                - expired_entries: int - Number of expired entries (for debugging)

        Note:
            - Returns stats with counts only, never content
            - Never raises exceptions (graceful degradation)
        """
        pass

    @abstractmethod
    def list_entries(self, session_id: str) -> List["MemoryEntryMetadata"]:
        """
        List all memory entries for a session for audit purposes.

        Args:
            session_id: Session to query (required)

        Returns:
            List of MemoryEntryMetadata objects (metadata only, no raw content).
            Empty list on failure.

        Note:
            - Returns metadata only (no raw content)
            - Never raises exceptions (graceful degradation)
        """
        pass

    @abstractmethod
    def delete_session_entries(self, session_id: str) -> "MemoryDeleteResult":
        """
        Delete/remove all memory entries associated with a session.

        Args:
            session_id: Session to delete entries for (required)

        Returns:
            MemoryDeleteResult with:
                - success: bool - Whether delete succeeded
                - entries_removed: int - Number of entries removed
                - error: Optional[str] - Error message (if failed, for logging only)

        Note:
            - Never raises exceptions (graceful degradation)
            - Used for session cleanup (expired or closed sessions)
        """
        pass




