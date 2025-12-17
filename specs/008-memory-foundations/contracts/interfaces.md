# Interface Contracts: Memory Foundations

**Date**: 2025-12-17  
**Feature**: Memory Foundations  
**Phase**: 1 - Design

## Overview

Memory Foundations introduces two new interface contracts: Memory Access Interface (MAI) for memory operations and Session Subsystem Interface for session lifecycle management. These interfaces enforce separation of concerns and enable graceful degradation.

## Memory Access Interface (MAI)

**Purpose**: Abstract all memory operations behind a replaceable interface with graceful degradation.

**Interface**: `aeon.memory.interface.MemoryAccessInterface`

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

class MemoryAccessInterface(ABC):
    """Abstract interface for memory storage and retrieval."""
    
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
        Select relevant entries and emit a deterministic, field-extracted contextual projection for prompt injection.
        
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
            - STM performs field extraction, ordering, and light formatting only - NO semantic summarization, inference, or rewriting
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
            List of MemoryEntryMetadata objects (metadata only, no raw content). Empty list on failure.
            
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
```

**Contract Requirements**:
- All methods MUST never raise exceptions (graceful degradation per FR-005, FR-006)
- All methods MUST return structured results indicating success/failure
- session_id is required for all operations (FR-007, FR-079)
- Memory entries MUST be annotated with execution_id and phase (FR-008, FR-012)
- STM MUST autonomously manage TTL (decrement on access, exclude expired entries) (FR-021, FR-022, FR-024)
- STM MUST perform field extraction, ordering, and light formatting only - NO semantic processing (FR-131, FR-131A)
- Content MUST be phase-native, raw execution artifacts (no pre-summarization) (FR-126, FR-128)
- Operations MUST degrade silently on failure (FR-005, FR-006)

**Implementations**:
- `aeon.memory.stm.STM` (Short-Term Memory)
- `aeon.memory.null_memory.NullMemory` (No-op implementation)

## Session Subsystem Interface

**Purpose**: Abstract session lifecycle management behind a replaceable interface.

**Interface**: `aeon.session.interface.SessionSubsystemInterface`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

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
    def notify_execution_complete(self, session_id: str) -> "SessionState":
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
            - When Session TTL is exhausted, session subsystem marks session as expired, cleans up session_id internally, and returns expired status
            - Orchestrator has no knowledge of Session TTL values, decrement logic, or expiration detection
            - Never raises exceptions (graceful degradation)
        """
        pass
    
    @abstractmethod
    def get_session_state(self, session_id: str) -> "SessionState":
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
    def list_sessions(self) -> List["SessionMetadata"]:
        """
        List all current sessions (active, expired, and closed) for audit purposes.
        
        Returns:
            List of SessionMetadata objects (session_id, state, created_at). Empty list if no sessions.
            
        Note:
            - Returns metadata only (no internal implementation details)
            - Never raises exceptions (graceful degradation)
        """
        pass
    
    @abstractmethod
    def close_session(self, session_id: str) -> "SessionCloseResult":
        """
        Gracefully close/terminate a session when triggered by presentation/client requests or host-defined termination policies (before TTL expiration).
        
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
```

**Contract Requirements**:
- All methods MUST never raise exceptions (graceful degradation)
- All methods MUST return structured results indicating success/failure
- session_id MUST be unique across all sessions (FR-068)
- Session subsystem MUST autonomously manage Session TTL (decrement on execution completion, detect expiration) (FR-121, FR-122)
- Session subsystem MUST NOT store memory (FR-072)
- Session subsystem MUST NOT own STM (FR-073)
- Session subsystem MUST NOT depend on kernel internals (FR-074)
- Session subsystem MUST be in-memory only (no persistence) (FR-075)
- Orchestrator has no knowledge of Session TTL values, decrement logic, or expiration detection (FR-125)

**Implementations**:
- `aeon.session.manager.SessionManager` (Session subsystem implementation)

## Data Models

### MemoryEntry

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

@dataclass
class MemoryEntry:
    """Structured data representing a single memory entry."""
    session_id: str  # Session owning the entry (required)
    execution_id: str  # Execution (turn) that created the entry (required)
    phase: str  # Phase (A, B, C, D, E) that created the entry (required)
    content: Dict[str, Any]  # Phase-native, raw execution artifacts (required)
    ttl: int  # Time-to-live (session-relative, decrements on STM access) (required)
    created_at: datetime  # Entry creation timestamp (required)
```

### MemoryWriteResult

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryWriteResult:
    """Result of a memory write operation."""
    success: bool  # Whether write succeeded (required)
    entry_id: Optional[str]  # Identifier of stored entry (if successful)
    evicted_count: int  # Number of entries evicted (if capacity exceeded) (required)
    error: Optional[str]  # Error message (if failed, for logging only)
```

### MemoryUsageStats

```python
from dataclasses import dataclass

@dataclass
class MemoryUsageStats:
    """Statistics about memory usage for observability."""
    memory_used: bool  # Whether memory was used in this execution (required)
    memory_entries_considered: int  # Number of entries considered for injection (required)
    memory_entries_injected: int  # Number of entries actually injected (required)
    memory_failures: int  # Number of memory operation failures (required)
    total_entries: int  # Total entries in session (for debugging) (required)
    expired_entries: int  # Number of expired entries (for debugging) (required)
```

### MemoryEntryMetadata

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemoryEntryMetadata:
    """Metadata about a memory entry for audit purposes (no raw content)."""
    session_id: str  # Session owning the entry (required)
    execution_id: str  # Execution (turn) that created the entry (required)
    phase: str  # Phase (A, B, C, D, E) that created the entry (required)
    created_at: datetime  # Entry creation timestamp (required)
    ttl: int  # Current TTL value (required)
```

### MemoryDeleteResult

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryDeleteResult:
    """Result of a memory delete operation."""
    success: bool  # Whether delete succeeded (required)
    entries_removed: int  # Number of entries removed (required)
    error: Optional[str]  # Error message (if failed, for logging only)
```

### SessionState

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SessionState:
    """Result of session state query operations."""
    session_id: str  # Session identifier (required)
    state: str  # Current session state ("active", "expired", "closed") (required)
    ttl: Optional[int]  # Current Session TTL value (if state is "active")
```

### SessionMetadata

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SessionMetadata:
    """Metadata about a session for audit purposes."""
    session_id: str  # Session identifier (required)
    state: str  # Current session state ("active", "expired", "closed") (required)
    created_at: datetime  # Session creation timestamp (required)
```

### SessionCloseResult

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SessionCloseResult:
    """Result of session close operation."""
    success: bool  # Whether close succeeded (required)
    error: Optional[str]  # Error message (if failed, for logging only)
```

## Integration Points

### Orchestrator Integration

The orchestrator integrates with memory and session subsystems through their interfaces:

1. **Session Creation**: Orchestrator calls `create_session()` at session start
2. **Memory Writing**: Orchestrator calls `write_entry()` after LLM response for Phase A (Plan Generation, TaskProfile Inference), Phase B (Reasoning Steps), and Phase D (Recursive Planning/Refinement). For Phase C, orchestrator calls `write_entry()` with metadata only after each response.
3. **Memory Injection**: Orchestrator calls `select_for_injection()` when rendering prompts that have memory injection enabled (Phase B, Phase D, optionally Phase A). Memory injection is disabled for Phase C and Phase E.
4. **Execution Completion**: Orchestrator calls `notify_execution_complete()` at Phase E to notify session subsystem of execution completion
5. **Session Cleanup**: When orchestrator receives expired session status, it calls `delete_session_entries()` to clean up memory entries

### Prompt Registry Integration

The prompt registry integrates with memory through the MAI interface:

1. **Memory Injection Configuration**: Prompt registry supports `memory_injection_enabled: bool` flag per prompt
2. **Memory Selection**: When memory injection is enabled, prompt registry calls `select_for_injection()` with appropriate context
3. **Context Insertion**: Prompt registry formats and inserts returned context blocks into prompt templates at defined injection points
4. **Non-Authoritative Marker**: Prompt registry applies the non-authoritative marker when inserting STM context

## Error Handling

All interface methods implement graceful degradation:

- **Never raise exceptions**: All methods return structured results indicating success/failure
- **Silent degradation**: Failures are logged but do not block execution
- **Structured results**: Result objects contain success flags and optional error messages
- **Empty results**: Read/list operations return empty lists on failure
- **Zero counts**: Statistics return zero counts on failure

This ensures that memory and session operations never block kernel execution, even in failure scenarios.

