"""Memory subsystem module.

This module provides memory storage and retrieval interfaces for Aeon.
It includes both the legacy Memory interface (for backward compatibility)
and the new MemoryAccessInterface (MAI) for session-scoped memory.
"""

from aeon.memory.interface import Memory, MemoryAccessInterface
from aeon.memory.models import (
    MemoryDeleteResult,
    MemoryEntry,
    MemoryEntryMetadata,
    MemoryInjectionResult,
    MemoryUsageStats,
    MemoryWriteResult,
)
from aeon.memory.null_memory import NullMemory
from aeon.memory.stm import STM

__all__ = [
    # Legacy interface (backward compatibility)
    "Memory",
    # New MAI interface
    "MemoryAccessInterface",
    # MAI implementations
    "STM",
    "NullMemory",
    # Data models
    "MemoryEntry",
    "MemoryWriteResult",
    "MemoryUsageStats",
    "MemoryEntryMetadata",
    "MemoryDeleteResult",
    "MemoryInjectionResult",
]








