"""Memory subsystem data models.

This module defines the data models for memory operations,
including MemoryEntry, MemoryWriteResult, MemoryUsageStats,
MemoryEntryMetadata, MemoryDeleteResult, and MemoryInjectionResult.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """Structured data representing a single memory entry."""

    session_id: str  # Session owning the entry (required)
    execution_id: str  # Execution (turn) that created the entry (required)
    phase: str  # Phase (A, B, C, D, E) that created the entry (required)
    content: Dict[str, Any]  # Phase-native, raw execution artifacts (required)
    ttl: int  # Time-to-live (session-relative, decrements on STM access) (required)
    created_at: datetime  # Entry creation timestamp (required)


@dataclass
class MemoryWriteResult:
    """Result of a memory write operation."""

    success: bool  # Whether write succeeded (required)
    entry_id: Optional[str] = None  # Identifier of stored entry (if successful)
    evicted_count: int = 0  # Number of entries evicted (if capacity exceeded) (required)
    error: Optional[str] = None  # Error message (if failed, for logging only)


@dataclass
class MemoryUsageStats:
    """Statistics about memory usage for observability."""

    memory_used: bool  # Whether memory was used in this execution (required)
    memory_entries_considered: int  # Number of entries considered for injection (required)
    memory_entries_injected: int  # Number of entries actually injected (required)
    memory_failures: int  # Number of memory operation failures (required)
    total_entries: int  # Total entries in session (for debugging) (required)
    expired_entries: int  # Number of expired entries (for debugging) (required)


@dataclass
class MemoryEntryMetadata:
    """Metadata about a memory entry for audit purposes (no raw content)."""

    session_id: str  # Session owning the entry (required)
    execution_id: str  # Execution (turn) that created the entry (required)
    phase: str  # Phase (A, B, C, D, E) that created the entry (required)
    created_at: datetime  # Entry creation timestamp (required)
    ttl: int  # Current TTL value (required)


@dataclass
class MemoryDeleteResult:
    """Result of a memory delete operation."""

    success: bool  # Whether delete succeeded (required)
    entries_removed: int  # Number of entries removed (required)
    error: Optional[str] = None  # Error message (if failed, for logging only)


@dataclass
class MemoryInjectionResult:
    """Result of select_for_injection() operation."""

    context_blocks: List[str]  # List of formatted context strings/blocks ready for prompt injection (required)
    non_authoritative_marker: str  # Single header/footer wrapper text marking context as non-authoritative (required)
