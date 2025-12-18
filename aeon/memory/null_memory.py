"""NullMemory implementation.

This module implements the NullMemory class that provides no-op behavior
for memory operations, enabling execution with memory fully disabled.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from aeon.memory.interface import MemoryAccessInterface
from aeon.memory.models import (
    MemoryDeleteResult,
    MemoryEntry,
    MemoryEntryMetadata,
    MemoryUsageStats,
    MemoryWriteResult,
)

if TYPE_CHECKING:
    from aeon.observability.logger import JSONLLogger


class NullMemory(MemoryAccessInterface):
    """NullMemory implementation.

    Provides no-op behavior for all memory operations.
    All operations succeed but store/retrieve nothing.
    """

    def __init__(self, logger: Optional["JSONLLogger"] = None) -> None:
        """
        Initialize NullMemory.

        Args:
            logger: Optional JSONLLogger for observability (default: None for no-op logging)
        """
        self._logger: Optional["JSONLLogger"] = logger

    def _log_memory_operation(
        self,
        operation_type: str,
        session_id: str,
        execution_id: Optional[str] = None,
        phase: Optional[str] = None,
        entry_count: Optional[int] = None,
        success: Optional[bool] = None,
        error_type: Optional[str] = None,
    ) -> None:
        """Log a memory operation using JSONLLogger (for consistency with STM)."""
        if self._logger:
            self._logger.log_memory_operation(
                operation_type=operation_type,
                session_id=session_id,
                correlation_id=None,
                execution_id=execution_id,
                phase=phase,
                entry_count=entry_count,
                success=success,
                error_type=error_type,
            )

    def write_entry(
        self,
        session_id: str,
        execution_id: str,
        phase: str,
        content: Dict[str, Any],
    ) -> MemoryWriteResult:
        """
        Store a memory entry (no-op).

        Args:
            session_id: Session owning the entry (required)
            execution_id: Execution (turn) that created the entry (required)
            phase: Phase (A, B, C, D, E) that created the entry (required)
            content: Phase-native, raw execution artifacts (JSON-compatible, required)

        Returns:
            MemoryWriteResult with success=True, empty entry_id, evicted_count=0
        """
        # No-op: succeed but store nothing
        self._log_memory_operation(
            operation_type="write_entry",
            session_id=session_id,
            execution_id=execution_id,
            phase=phase,
            entry_count=0,
            success=True,
        )
        return MemoryWriteResult(
            success=True,
            entry_id=None,
            evicted_count=0,
        )

    def read_entries(
        self,
        session_id: str,
        execution_id: str | None = None,
        phase: str | None = None,
    ) -> List[MemoryEntry]:
        """
        Retrieve memory entries (no-op).

        Args:
            session_id: Session to query (required)
            execution_id: Filter by execution_id (optional)
            phase: Filter by phase (optional)

        Returns:
            Empty list (no entries stored)
        """
        # No-op: return empty list
        self._log_memory_operation(
            operation_type="read_entries",
            session_id=session_id,
            execution_id=execution_id,
            phase=phase,
            entry_count=0,
            success=True,
        )
        return []

    def select_for_injection(
        self,
        session_id: str,
        context: Dict[str, Any],
        budget: int,
    ) -> Dict[str, Any]:
        """
        Select relevant entries for injection (no-op).

        Args:
            session_id: Session to query (required)
            context: Selection context (required)
            budget: Injection budget (hard upper bound)

        Returns:
            Dict with empty context_blocks and non_authoritative_marker
        """
        # No-op: return empty structure
        self._log_memory_operation(
            operation_type="select_for_injection",
            session_id=session_id,
            entry_count=0,
            success=True,
        )
        return {
            "context_blocks": [],
            "non_authoritative_marker": "Non-authoritative context from this session (for reference only)",
        }

    def get_usage_stats(self, session_id: str) -> MemoryUsageStats:
        """
        Get memory usage statistics (no-op).

        Args:
            session_id: Session to query (required)

        Returns:
            MemoryUsageStats with zero counts
        """
        # No-op: return zero stats
        self._log_memory_operation(
            operation_type="get_usage_stats",
            session_id=session_id,
            entry_count=0,
            success=True,
        )
        return MemoryUsageStats(
            memory_used=False,
            memory_entries_considered=0,
            memory_entries_injected=0,
            memory_failures=0,
            total_entries=0,
            expired_entries=0,
        )

    def list_entries(self, session_id: str) -> List[MemoryEntryMetadata]:
        """
        List all memory entries (no-op).

        Args:
            session_id: Session to query (required)

        Returns:
            Empty list (no entries stored)
        """
        # No-op: return empty list
        self._log_memory_operation(
            operation_type="list_entries",
            session_id=session_id,
            entry_count=0,
            success=True,
        )
        return []

    def delete_session_entries(self, session_id: str) -> MemoryDeleteResult:
        """
        Delete/remove all memory entries (no-op).

        Args:
            session_id: Session to delete entries for (required)

        Returns:
            MemoryDeleteResult with success=True, entries_removed=0
        """
        # No-op: succeed but remove nothing
        self._log_memory_operation(
            operation_type="delete_session_entries",
            session_id=session_id,
            entry_count=0,
            success=True,
        )
        return MemoryDeleteResult(
            success=True,
            entries_removed=0,
        )
