# Research: Memory Foundations

**Date**: 2025-12-17  
**Feature**: Memory Foundations  
**Phase**: 0 - Research

## Overview

This document consolidates research findings and design decisions for Sprint 8: Memory Foundations. All technical clarifications from the specification have been resolved, and key architectural decisions are documented below.

## Decision 1: Memory Access Interface (MAI) Design

**Decision**: Abstract `MemoryAccessInterface` (MAI) with methods: `write_entry()`, `read_entries()`, `select_for_injection()`, `get_usage_stats()`, `list_entries()`, `delete_session_entries()`. Implementations include `STM` (Short-Term Memory) and `NullMemory` (no-op).

**Rationale**:
- Interface abstraction enables replacement of memory implementations without kernel changes
- NullMemory enables execution with memory fully disabled (testing, fallback scenarios)
- Structured result types (MemoryWriteResult, MemoryDeleteResult) enable graceful degradation without exceptions
- Session-scoped operations ensure memory is properly isolated per session

**Alternatives Considered**:
- Extend existing `Memory` interface (write/read/search): Rejected - existing interface is too simple (key/value), new interface needs session/execution/phase annotations and injection semantics
- Direct STM implementation without interface: Rejected - violates interface abstraction, prevents NullMemory and future implementations
- Exception-based error handling: Rejected - violates graceful degradation requirement (FR-005, FR-006)

**Implementation Approach**:
```python
class MemoryAccessInterface(ABC):
    @abstractmethod
    def write_entry(self, session_id: str, execution_id: str, phase: str, content: Dict[str, Any]) -> MemoryWriteResult:
        """Store memory entry with annotations. Returns result, never raises exceptions."""
        pass
    
    @abstractmethod
    def select_for_injection(self, session_id: str, context: Dict[str, Any], budget: int) -> Dict[str, Any]:
        """Select relevant entries and emit contextual projection. Returns structured JSON."""
        pass
    
    # ... other methods
```

## Decision 2: Short-Term Memory (STM) Storage Design

**Decision**: In-memory dict-based storage with capacity limits and TTL-based eviction. Entries stored with session_id, execution_id, phase, content, ttl, created_at. TTL decrements autonomously on STM access (read/write/select operations) for all entries in session to preserve recency bias.

**Rationale**:
- In-memory dict is fast, requires no external dependencies, and satisfies no-disk guarantee
- Capacity limits prevent unbounded growth
- TTL-based eviction provides temporal relevance filtering
- Autonomous TTL decrement preserves recency bias (newer entries have higher TTLs)
- Access-based TTL decrement (not execution-based) aligns with STM's lack of execution boundary knowledge

**Alternatives Considered**:
- SQLite or file-based storage: Rejected - violates no-disk guarantee (FR-059, FR-060)
- Vector store or embeddings: Rejected - out of scope (explicitly excluded in spec)
- Execution-boundary TTL decrement: Rejected - STM has no concept of execution boundaries, operates on access patterns only
- Wall-clock time TTL: Rejected - STM does not observe wall-clock time, manages TTL based on access patterns

**Implementation Approach**:
- Dict structure: `{session_id: {entry_id: MemoryEntry}}`
- Capacity limit: Configurable (e.g., 100-1000 entries per session)
- TTL initial value: 10 (configurable static variable)
- TTL decrement: On any STM operation (read_entries, write_entry, select_for_injection) for session_id, decrement all entries' TTLs
- Eviction: Deterministic soft eviction when capacity exceeded (LRU or creation-order based)
- Expired entry removal: Autonomously exclude from queries and remove from physical memory when TTL ≤ 0

## Decision 3: Memory Ingest/Emit Asymmetry

**Decision**: `write_entry()` ingests raw, phase-native execution artifacts without pre-summarization. `select_for_injection()` emits deterministic, field-extracted contextual projection suitable for prompt injection. STM performs field extraction, ordering, and light formatting only - NO semantic summarization, inference, or rewriting.

**Rationale**:
- Ingest raw artifacts preserves fidelity and avoids information loss
- Emit contextual projection enables phase-appropriate context crafting
- Field extraction and ordering are deterministic and transparent
- No semantic processing keeps STM simple and predictable
- Asymmetry allows STM to decide what to extract during selection, not at ingest time

**Alternatives Considered**:
- Summarize at ingest time: Rejected - loses information, violates ingest/emit asymmetry requirement (FR-126)
- Semantic analysis for relevance: Rejected - out of scope, explicitly excluded (no semantic summarization)
- Raw entry injection: Rejected - violates requirement for field-extracted projection (FR-037, FR-131)

**Implementation Approach**:
- Ingest: Store raw content as-is (phase-native structure)
- Emit: Extract phase-appropriate fields deterministically:
  - Phase B: Extract prior user statements, prior assistant response text, optional recent refinement reason
  - Phase D: Extract refinement reason, updated goal, updated step descriptions
  - Phase A: Extract goal, task profile posture fields (rare, optional)
- Formatting: Light formatting only (string concatenation, punctuation, line breaks) - no semantic transformation

## Decision 4: Session Subsystem Architecture

**Decision**: Autonomous Session subsystem that manages session lifecycle independently of STM. Issues unique session_ids, tracks session state (active/expired/closed), manages Session TTL autonomously. Session TTL initial value: 3, decrements when orchestrator notifies execution completion. Session subsystem has no knowledge of STM, and STM has no knowledge of Session subsystem.

**Rationale**:
- Autonomous subsystem aligns with architectural principle of separation of concerns
- Session TTL managed independently from Memory Entry TTL (different scopes, purposes, decrement triggers)
- Orchestrator mediates between Session and STM but has no knowledge of TTL internals
- Session subsystem is in-memory only, no persistence

**Alternatives Considered**:
- STM manages sessions: Rejected - violates separation of concerns, STM should not own session lifecycle (FR-077, FR-078)
- Orchestrator manages Session TTL: Rejected - violates autonomous subsystem principle, orchestrator should not know TTL internals (FR-125)
- Shared TTL between Session and Memory Entry: Rejected - different scopes and purposes (Session TTL controls session lifetime, Memory Entry TTL controls entry relevance)

**Implementation Approach**:
- Session subsystem interface: `create_session() -> str`, `notify_execution_complete(session_id) -> SessionState`, `get_session_state(session_id) -> SessionState`, `list_sessions() -> List[SessionMetadata]`, `close_session(session_id) -> SessionCloseResult`
- Session TTL: Initial value 3, decrements on execution completion notification
- Session state: active, expired (TTL exhausted), closed/terminated (graceful shutdown)
- Orchestrator wiring: Call `create_session()` at session start, `notify_execution_complete()` at Phase E, check session state before memory operations

## Decision 5: Memory Injection Integration

**Decision**: Memory injection flows through explicit, named, opt-in injection points in prompt registry. Prompt registry calls `select_for_injection()` and formats/inserts returned context blocks into prompt templates. Injection is bounded by explicit budget (hard upper bound, no truncation of individual entries). Memory injection disabled for Phase C and Phase E.

**Rationale**:
- Explicit injection points ensure memory only enters prompts where intended
- Opt-in behavior maintains safety and predictability
- Budget bounds prevent unbounded context growth
- Prompt registry owns formatting and insertion logic, STM only provides render-ready content
- Phase restrictions (C and E) align with spec requirements (FR-133)

**Alternatives Considered**:
- Automatic injection into all prompts: Rejected - violates explicit opt-in requirement (FR-040, FR-045)
- STM-aware prompt templates: Rejected - STM should not be aware of prompt structure (FR-132)
- Unbounded injection: Rejected - violates bounded injection requirement (FR-041)

**Implementation Approach**:
- Prompt registry extension: Add `memory_injection_enabled: bool` flag per prompt
- Injection points: Named markers in prompt templates (e.g., `{memory_context}`)
- Budget enforcement: Hard upper bound, entries included in order until budget exhausted
- Non-authoritative marker: Applied by prompt registry when inserting STM context
- Phase restrictions: Memory injection disabled for Phase C and Phase E prompts

## Decision 6: Graceful Degradation Strategy

**Decision**: All memory operations return structured results (success/failure indicators) and never raise exceptions. Memory failures are logged but do not block execution. NullMemory provides no-op fallback. STM validation failures degrade silently (entry not stored, failure logged).

**Rationale**:
- Graceful degradation ensures execution continues even if memory fails
- Structured results enable observability without exceptions
- NullMemory enables execution with memory fully disabled
- Silent degradation aligns with non-blocking requirement (FR-005, FR-006)

**Alternatives Considered**:
- Exception-based error handling: Rejected - violates graceful degradation requirement
- Blocking on memory failures: Rejected - violates non-blocking requirement
- Retry logic for memory failures: Rejected - adds complexity, silent degradation is sufficient

**Implementation Approach**:
- Result types: MemoryWriteResult, MemoryDeleteResult, MemoryUsageStats (all with success flags and optional error messages)
- Error handling: Try-catch around all memory operations, log errors, return failure results
- NullMemory: All operations return success with empty/zero results
- Validation failures: Log error, return failure result, continue execution

## Decision 7: Observability Design

**Decision**: Memory operations logged with structural metadata (operation type, entry count, session_id, execution_id, phase) but NO raw content. Phase E metadata includes memory usage statistics (memory_used, memory_entries_considered, memory_entries_injected, memory_failures). Logs are content-free.

**Rationale**:
- Content-free logging maintains privacy and prevents log bloat
- Structural metadata enables debugging and monitoring
- Phase E metadata provides execution-level memory usage visibility
- No content exposure aligns with no-disk guarantee and privacy requirements

**Alternatives Considered**:
- Full content logging: Rejected - violates content-free logging requirement (FR-062)
- No logging: Rejected - observability is essential for debugging
- Semantic analysis logging: Rejected - out of scope, adds complexity

**Implementation Approach**:
- Log format: `{"operation": "write_entry", "session_id": "...", "execution_id": "...", "phase": "B", "entry_count": 1, "success": true}`
- Phase E metadata: `{"memory_used": true, "memory_entries_considered": 5, "memory_entries_injected": 3, "memory_failures": 0}`
- Content exclusion: Never log raw memory content, step_output, stored user text

## Summary

All technical clarifications have been resolved. Key decisions:
1. MAI interface abstraction with structured results (no exceptions)
2. In-memory STM with capacity and TTL-based eviction
3. Ingest/emit asymmetry (raw ingest, field-extracted emit)
4. Autonomous Session subsystem with independent TTL management
5. Explicit, opt-in memory injection through prompt registry
6. Graceful degradation with structured results
7. Content-free observability with structural metadata

No further research needed. Ready for Phase 1 design.

