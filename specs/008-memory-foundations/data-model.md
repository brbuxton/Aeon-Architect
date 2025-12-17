# Data Model: Memory Foundations

**Date**: 2025-12-17  
**Feature**: Memory Foundations  
**Phase**: 1 - Design

## Core Entities

### MemoryAccessInterface

Abstract interface defining all memory operations. Implementations include STM and NullMemory.

**Methods**:
- `write_entry(session_id: str, execution_id: str, phase: str, content: Dict[str, Any]) -> MemoryWriteResult`
- `read_entries(session_id: str, execution_id: Optional[str] = None, phase: Optional[str] = None) -> List[MemoryEntry]`
- `select_for_injection(session_id: str, context: Dict[str, Any], budget: int) -> Dict[str, Any]`
- `get_usage_stats(session_id: str) -> MemoryUsageStats`
- `list_entries(session_id: str) -> List[MemoryEntryMetadata]`
- `delete_session_entries(session_id: str) -> MemoryDeleteResult`

**Validation Rules**:
- All methods must never raise exceptions (graceful degradation)
- All methods must return structured results indicating success/failure
- session_id is required for all operations
- Operations must degrade silently on failure

**State Transitions**:
- N/A (interface, no state)

**Relationships**:
- Implemented by STM and NullMemory
- Used by orchestrator for memory operations

### Short-Term Memory (STM)

In-memory implementation of MemoryAccessInterface that stores structured entries with capacity and TTL bounds.

**Fields** (internal state):
- `_store: Dict[str, Dict[str, MemoryEntry]]` - Nested dict: `{session_id: {entry_id: MemoryEntry}}`
- `_capacity: int` - Maximum entries per session (configurable, e.g., 100-1000)
- `_initial_ttl: int` - Initial TTL value for new entries (configurable, default: 10)

**Behavior**:
- Stores entries in-memory only (never disk)
- Enforces capacity limit with deterministic eviction
- Assigns initial TTL value when creating new entries
- Autonomously decrements TTL for all entries in session_id on any STM access (read/write/select)
- Has no concept of execution boundaries - TTL decrement based solely on access patterns
- Autonomously excludes expired entries (TTL ≤ 0) from all query operations
- Autonomously removes expired entries from physical memory
- Ingests raw, phase-native execution artifacts via `write_entry()` (no pre-summarization)
- Emits deterministic, field-extracted contextual projections via `select_for_injection()` (field extraction, ordering, light formatting only - NO semantic processing)
- Garbage-collectable at session termination

**Validation Rules**:
- Entries must have required annotations (session_id, execution_id, phase)
- Content must be JSON-compatible (serializable)
- Content structure must be phase-appropriate
- Validation failures degrade silently (entry not stored, failure logged)

**State Transitions**:
- Entry created: TTL = initial_ttl, created_at = current time
- Entry accessed: TTL decremented for all entries in session
- Entry expired: TTL ≤ 0, excluded from queries, removed from memory
- Capacity exceeded: Deterministic eviction occurs

**Relationships**:
- Implements MemoryAccessInterface
- Stores MemoryEntry objects
- Used by orchestrator through MAI interface

### NullMemory

No-op implementation of MemoryAccessInterface that provides empty behavior.

**Fields** (internal state):
- None (stateless)

**Behavior**:
- All write operations succeed but store nothing
- All read operations return empty results
- All selection operations return empty results
- Usage stats return zero counts
- Enables execution with memory fully disabled

**Validation Rules**:
- N/A (no-op, always succeeds)

**State Transitions**:
- N/A (stateless)

**Relationships**:
- Implements MemoryAccessInterface
- Used by orchestrator when memory is disabled

### MemoryEntry

Structured data representing a single memory entry.

**Fields**:
- `session_id` (str, required): Session owning the entry
- `execution_id` (str, required): Execution (turn) that created the entry (used for recency ordering across executions)
- `phase` (str, required): Phase (A, B, C, D, E) that created the entry (essential for phase-aware context crafting)
- `content` (Dict[str, Any], required): Phase-native, raw execution artifacts (JSON-compatible, phase-aware structure). Content structure varies by phase but uses uniform JSON-compatible shape. Content MUST contain phase-specific data as defined in FR-128:
  - Phase A - Plan Generation: plan goal and step descriptions only
  - Phase A - TaskProfile Inference: full TaskProfile inference output
  - Phase B - Reasoning Steps: rendered user prompt (or key fields: user request, step description) and full LLM response text (verbatim)
  - Phase C - Validation/Convergence: metadata only (convergence status, detected issues, reason codes, completeness score, coherence score)
  - Phase D - Recursive Planning/Refinement: refinement reason, updated goal, updated step descriptions
  - Phase E - Answer Synthesis: DO NOT ingest by default
- `ttl` (int, required): Time-to-live (session-relative, decrements on STM access). Initial value: 10 (configurable)
- `created_at` (datetime, required): Entry creation timestamp (for eviction ordering and recency)

**Validation Rules**:
- session_id must be non-empty string
- execution_id must be non-empty string
- phase must be one of: "A", "B", "C", "D", "E"
- content must be JSON-compatible (serializable)
- content structure must be phase-appropriate
- ttl must be >= 0
- created_at must be valid datetime

**State Transitions**:
- Created: ttl = initial_ttl, created_at = current time
- Accessed: ttl decremented (along with all other entries in session)
- Expired: ttl ≤ 0, excluded from queries, removed from memory

**Relationships**:
- Belongs to session (via session_id)
- Created by execution (via execution_id)
- Created by phase (via phase)
- Stored by STM

### MemoryInjectionResult

Result of `select_for_injection()` operation.

**Fields**:
- `context_blocks` (List[str], required): List of formatted context strings/blocks ready for prompt injection. Each block contains extracted, phase-appropriate fields from prior execution artifacts.
- `non_authoritative_marker` (str, required): Single header/footer wrapper text marking the context as non-authoritative (e.g., "Non-authoritative context from this session (for reference only)"). Applied by prompt registry when inserting context.

**Validation Rules**:
- context_blocks must be list of strings
- non_authoritative_marker must be non-empty string
- Context blocks must be within injection budget (hard upper bound, no truncation of individual entries)

**State Transitions**:
- N/A (result object, no state)

**Relationships**:
- Returned by STM.select_for_injection()
- Used by prompt registry for injection

### MemoryWriteResult

Result of a memory write operation.

**Fields**:
- `success` (bool, required): Whether write succeeded
- `entry_id` (Optional[str]): Identifier of stored entry (if successful)
- `evicted_count` (int, required): Number of entries evicted (if capacity exceeded)
- `error` (Optional[str]): Error message (if failed, for logging only)

**Validation Rules**:
- success must be bool
- entry_id must be string if success is True, None if False
- evicted_count must be >= 0
- error must be string if success is False, None if True

**State Transitions**:
- N/A (result object, no state)

**Relationships**:
- Returned by MAI.write_entry()
- Used by orchestrator to verify write success

### MemoryUsageStats

Statistics about memory usage for observability.

**Fields**:
- `memory_used` (bool, required): Whether memory was used in this execution
- `memory_entries_considered` (int, required): Number of entries considered for injection
- `memory_entries_injected` (int, required): Number of entries actually injected
- `memory_failures` (int, required): Number of memory operation failures
- `total_entries` (int, required): Total entries in session (for debugging)
- `expired_entries` (int, required): Number of expired entries (for debugging)

**Validation Rules**:
- All fields must be non-negative integers (except memory_used which is bool)
- memory_entries_injected must be <= memory_entries_considered
- expired_entries must be <= total_entries

**State Transitions**:
- N/A (statistics object, no state)

**Relationships**:
- Returned by MAI.get_usage_stats()
- Included in Phase E metadata

### MemoryEntryMetadata

Metadata about a memory entry for audit purposes (no raw content).

**Fields**:
- `session_id` (str, required): Session owning the entry
- `execution_id` (str, required): Execution (turn) that created the entry
- `phase` (str, required): Phase (A, B, C, D, E) that created the entry
- `created_at` (datetime, required): Entry creation timestamp
- `ttl` (int, required): Current TTL value

**Validation Rules**:
- session_id must be non-empty string
- execution_id must be non-empty string
- phase must be one of: "A", "B", "C", "D", "E"
- created_at must be valid datetime
- ttl must be >= 0

**State Transitions**:
- N/A (metadata object, no state)

**Relationships**:
- Returned by MAI.list_entries()
- Represents MemoryEntry without content

### MemoryDeleteResult

Result of a memory delete operation.

**Fields**:
- `success` (bool, required): Whether delete succeeded
- `entries_removed` (int, required): Number of entries removed
- `error` (Optional[str]): Error message (if failed, for logging only)

**Validation Rules**:
- success must be bool
- entries_removed must be >= 0
- error must be string if success is False, None if True

**State Transitions**:
- N/A (result object, no state)

**Relationships**:
- Returned by MAI.delete_session_entries()
- Used by orchestrator to verify delete success

### Session Subsystem Interface

Abstract interface for session lifecycle management.

**Methods**:
- `create_session() -> str`: Issue unique session_id
- `notify_execution_complete(session_id: str) -> SessionState`: Notify execution completion, decrement Session TTL, return session state
- `get_session_state(session_id: str) -> SessionState`: Get current session state
- `list_sessions() -> List[SessionMetadata]`: List all current sessions (active, expired, closed)
- `close_session(session_id: str) -> SessionCloseResult`: Gracefully close/terminate session

**Validation Rules**:
- All methods must never raise exceptions (graceful degradation)
- All methods must return structured results indicating success/failure
- session_id must be unique across all sessions
- Session state must be one of: active, expired, closed

**State Transitions**:
- N/A (interface, no state)

**Relationships**:
- Implemented by SessionManager
- Used by orchestrator for session management

### SessionManager

Implementation of Session Subsystem Interface that manages session lifecycle autonomously.

**Fields** (internal state):
- `_sessions: Dict[str, Session]` - Active sessions: `{session_id: Session}`
- `_initial_ttl: int` - Initial Session TTL value (configurable, default: 3)

**Behavior**:
- Issues unique session_id values for new sessions
- Assigns initial Session TTL value when creating new sessions
- Tracks session state (active / expired / closed)
- Autonomously manages Session TTL - decrements when orchestrator notifies execution completion
- Autonomously detects when Session TTL is exhausted and marks session as expired
- When Session TTL is exhausted, cleans up session_id internally and returns expired status to orchestrator
- Enforces session termination based on host-defined policies
- Supports listing all current sessions for audit purposes
- Supports gracefully closing/terminating sessions
- In-memory only (no persistence)
- Does NOT store memory
- Does NOT own STM
- Does NOT depend on kernel internals

**Validation Rules**:
- session_id must be unique
- Session TTL must be >= 0
- Session state must be one of: active, expired, closed

**State Transitions**:
- Session created: state = active, ttl = initial_ttl
- Execution completed: ttl decremented
- TTL exhausted: state = expired, session_id cleaned up internally
- Graceful closure: state = closed, resources released

**Relationships**:
- Implements Session Subsystem Interface
- Manages Session objects
- Used by orchestrator through Session Subsystem Interface

### Session

Represents a single session with its lifecycle state.

**Fields**:
- `session_id` (str, required): Unique identifier for the session
- `state` (enum, required): Current session state
  - Values: "active", "expired", "closed"
  - Default: "active"
- `ttl` (int, required): Current Session TTL value (decrements on execution completion)
- `created_at` (datetime, required): Session creation timestamp

**Validation Rules**:
- session_id must be non-empty string and unique
- state must be one of: "active", "expired", "closed"
- ttl must be >= 0
- created_at must be valid datetime

**State Transitions**:
- Created: state = "active", ttl = initial_ttl
- Execution completed: ttl decremented (if state is "active")
- TTL exhausted: state = "expired", ttl = 0
- Graceful closure: state = "closed"

**Relationships**:
- Managed by SessionManager
- Referenced by orchestrator via session_id

### SessionState

Result of session state query operations.

**Fields**:
- `session_id` (str, required): Session identifier
- `state` (enum, required): Current session state ("active", "expired", "closed")
- `ttl` (int, optional): Current Session TTL value (if state is "active")

**Validation Rules**:
- session_id must be non-empty string
- state must be one of: "active", "expired", "closed"
- ttl must be >= 0 if present

**State Transitions**:
- N/A (result object, no state)

**Relationships**:
- Returned by SessionManager.notify_execution_complete() and get_session_state()
- Used by orchestrator to check session validity

### SessionMetadata

Metadata about a session for audit purposes.

**Fields**:
- `session_id` (str, required): Session identifier
- `state` (enum, required): Current session state ("active", "expired", "closed")
- `created_at` (datetime, required): Session creation timestamp

**Validation Rules**:
- session_id must be non-empty string
- state must be one of: "active", "expired", "closed"
- created_at must be valid datetime

**State Transitions**:
- N/A (metadata object, no state)

**Relationships**:
- Returned by SessionManager.list_sessions()
- Represents Session without TTL details

### SessionCloseResult

Result of session close operation.

**Fields**:
- `success` (bool, required): Whether close succeeded
- `error` (Optional[str]): Error message (if failed, for logging only)

**Validation Rules**:
- success must be bool
- error must be string if success is False, None if True

**State Transitions**:
- N/A (result object, no state)

**Relationships**:
- Returned by SessionManager.close_session()
- Used by orchestrator to verify close success

## Entity Relationships

```
Orchestrator
  ├── uses MemoryAccessInterface (MAI)
  │     ├── implemented by STM
  │     │     └── stores MemoryEntry objects
  │     └── implemented by NullMemory
  │
  └── uses Session Subsystem Interface
        └── implemented by SessionManager
              └── manages Session objects

MemoryEntry
  ├── belongs to Session (via session_id)
  ├── created by Execution (via execution_id)
  └── created by Phase (via phase)

Session
  └── managed by SessionManager

MemoryInjectionResult
  └── returned by STM.select_for_injection()
      └── used by Prompt Registry for injection
```

## Key Constraints

1. **No Disk I/O**: STM and SessionManager must never write to disk (FR-059, FR-060, FR-075)
2. **Graceful Degradation**: All operations must never raise exceptions (FR-005, FR-006)
3. **Autonomous TTL Management**: Session and Memory Entry TTLs are managed autonomously by their respective subsystems (FR-022, FR-125)
4. **Session Scoping**: All memory entries must be associated with exactly one session_id (FR-007, FR-080)
5. **Phase Annotations**: All memory entries must be annotated with execution_id and phase (FR-008, FR-012)
6. **Content-Free Observability**: Logs and metadata must never contain raw memory content (FR-062, FR-066)

