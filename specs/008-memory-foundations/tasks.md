# Implementation Tasks: Memory Foundations

**Feature**: Memory Foundations  
**Branch**: `008-memory-foundations`  
**Date**: 2025-12-17  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Summary

This document provides an actionable, dependency-ordered task list for implementing Memory Foundations (Sprint 8). Tasks are organized by phase, with user stories implemented in priority order (P1, then P2). Each task is independently executable and includes specific file paths.

**Total Tasks**: 102  
**Phase 1 (Setup)**: 5 tasks  
**Phase 2 (Foundational)**: 4 tasks  
**User Story 0 (Session Lifecycle)**: 12 tasks  
**User Story 1 (Session-Scoped Memory Storage)**: 16 tasks  
**User Story 2 (Bounded Memory with Eviction)**: 12 tasks  
**User Story 3 (Memory-Aware Prompt Injection)**: 15 tasks  
**User Story 4 (Memory Usage Observability)**: 10 tasks  
**Phase 8 (Integration & Kernel Wiring)**: 13 tasks  
**Phase 9 (Polish & Cross-Cutting)**: 15 tasks

## Dependencies

**User Story Completion Order**:
1. **User Story 0** (Session Lifecycle Management) - **MUST complete first** - Provides session_id infrastructure required by all memory operations
2. **User Story 1** (Session-Scoped Memory Storage) - **Depends on User Story 0** - Requires session_id from Session subsystem
3. **User Story 2** (Bounded Memory with Eviction) - **Depends on User Story 1** - Extends STM with capacity and TTL eviction
4. **User Story 3** (Memory-Aware Prompt Injection) - **Depends on User Story 2** - Requires working STM with selection capabilities
5. **User Story 4** (Memory Usage Observability) - **Depends on User Story 3** - Requires memory operations to be observable

**Parallel Execution Opportunities**:
- Within Phase 2: Session interface (T010) and Session models (T011) can be developed in parallel; MAI interface (T012) and Memory models (T013) can be developed in parallel
- Within User Story 1: STM core implementation (T040-T045) and NullMemory implementation (T046-T052) can be developed in parallel
- Within User Story 2: Capacity configuration/eviction (T060-T062) and TTL configuration/eviction (T063-T067) can be developed in parallel
- Within User Story 3: Prompt registry extension (T080-T081) and STM selection logic (T082-T089) can be developed in parallel
- Within User Story 4: Logging implementation (T100-T101) and usage stats implementation (T102-T103) can be developed in parallel

## Implementation Strategy

**MVP Scope**: User Story 0 + User Story 1 (Session subsystem + basic STM storage)  
**Incremental Delivery**: Each user story phase is independently testable and delivers value

---

## Phase 1: Setup

**Goal**: Initialize project structure and dependencies for Memory Foundations feature.

**Independent Test**: Project structure exists, dependencies are installed, no import errors.

- [ ] T001 Create session subsystem directory structure at `aeon/session/`
- [ ] T002 Create `aeon/session/__init__.py` with module exports
- [ ] T003 Update `aeon/memory/__init__.py` to prepare for new MAI interface (keep existing Memory interface for backward compatibility)
- [ ] T004 Verify pydantic>=2.0.0 is installed and compatible
- [ ] T005 Verify pytest>=7.4.0 is installed for testing

---

## Phase 2: Foundational

**Goal**: Implement core interfaces and data models that are prerequisites for all user stories.

**Independent Test**: Interfaces are defined, data models are validated, no implementation logic yet.

- [ ] T010 [P] Create Session Subsystem Interface at `aeon/session/interface.py` with abstract methods: `create_session()`, `notify_execution_complete()`, `get_session_state()`, `list_sessions()`, `close_session()`
- [ ] T011 [P] Create Session data models at `aeon/session/models.py`: `Session`, `SessionState`, `SessionMetadata`, `SessionCloseResult`
- [ ] T012 Create Memory Access Interface (MAI) at `aeon/memory/interface.py` with abstract methods: `write_entry()`, `read_entries()`, `select_for_injection()`, `get_usage_stats()`, `list_entries()`, `delete_session_entries()`
- [ ] T013 Create Memory data models at `aeon/memory/models.py`: `MemoryEntry`, `MemoryWriteResult`, `MemoryUsageStats`, `MemoryEntryMetadata`, `MemoryDeleteResult`, `MemoryInjectionResult`

---

## Phase 3: User Story 0 - Session Lifecycle Management (P1)

**Goal**: Implement Session subsystem that issues unique session_ids and manages session lifecycle independently of STM.

**Independent Test**: Can create sessions, receive unique session_ids, track session state (active/expired/closed), enforce termination policies, and expose session validity checks. Session subsystem operates independently of STM with no memory storage operations.

**Test Criteria**:
- Session creation returns unique session_id
- Session state tracking works correctly (active → expired → closed)
- Session TTL decrements on execution completion notification
- Session subsystem autonomously detects expiration and marks session as expired
- Session validity checks return accurate state information
- Session subsystem performs zero memory storage operations
- Session subsystem has zero dependencies on kernel internals

- [ ] T020 [US0] Implement SessionManager at `aeon/session/manager.py` with in-memory session storage (`_sessions: Dict[str, Session]`)
- [ ] T021 [US0] Implement `create_session()` in SessionManager that issues unique session_id using UUID
- [ ] T022 [US0] Implement session state tracking in SessionManager: `_sessions` dict with Session objects containing `session_id`, `state`, `ttl`, `created_at`
- [ ] T023 [US0] Implement `get_session_state()` in SessionManager that returns SessionState with current state
- [ ] T024 [US0] Implement `notify_execution_complete()` in SessionManager that decrements Session TTL and autonomously detects expiration
- [ ] T025 [US0] Implement session expiration detection in SessionManager: when TTL reaches zero, mark session as expired and clean up internally
- [ ] T026 [US0] Implement `list_sessions()` in SessionManager that returns List[SessionMetadata] with session_id, state, created_at
- [ ] T027 [US0] Implement `close_session()` in SessionManager for graceful session termination (client/presentation request or termination policy)
- [ ] T028 [US0] Add session termination policy enforcement in SessionManager (host-defined policies)
- [ ] T029 [US0] Implement graceful degradation in SessionManager: all methods return structured results, never raise exceptions
- [ ] T030 [US0] Add unit tests for SessionManager at `tests/unit/test_session_manager.py` covering session creation, state tracking, TTL decrement, expiration detection, graceful closure
- [ ] T031 [US0] Add contract tests for Session Subsystem Interface at `tests/contract/test_session_interface.py` verifying interface contract compliance

---

## Phase 4: User Story 1 - Session-Scoped Memory Storage (P1)

**Goal**: Implement STM that stores and retrieves memory entries scoped to sessions, with entries persisting across multiple executions within a session.

**Independent Test**: Can create a session, store memory entries during execution 1, and retrieve those entries during execution 2 within the same session. Memory entries are correctly tagged with session_id, execution_id, and phase annotations.

**Test Criteria**:
- Memory entries written in execution 1 are accessible in execution 2 (same session)
- Memory entries are correctly annotated with session_id, execution_id, phase
- Memory operations degrade gracefully on failure (no exceptions, execution continues)
- Memory entries are garbage-collectable at session termination
- STM performs zero file I/O operations
- NullMemory provides no-op behavior (all operations succeed but store nothing)

- [ ] T040 [US1] Implement STM class at `aeon/memory/stm.py` with in-memory storage structure: `_store: Dict[str, Dict[str, MemoryEntry]]` (nested dict: `{session_id: {entry_id: MemoryEntry}}`)
- [ ] T041 [US1] Implement `write_entry()` in STM that stores MemoryEntry with session_id, execution_id, phase, content annotations
- [ ] T042 [US1] Implement entry validation in STM `write_entry()`: validate required annotations (session_id, execution_id, phase), content serializability, phase-appropriate structure
- [ ] T043 [US1] Implement `read_entries()` in STM that retrieves MemoryEntry objects filtered by session_id, optional execution_id, optional phase
- [ ] T044 [US1] Implement graceful degradation in STM: all methods return structured results (MemoryWriteResult, List[MemoryEntry]), never raise exceptions
- [ ] T045 [US1] Implement validation failure handling in STM: validation failures degrade silently (entry not stored, failure logged, execution continues)
- [ ] T046 [US1] Implement NullMemory class at `aeon/memory/null_memory.py` that implements MAI with no-op behavior (all operations succeed but store/retrieve nothing)
- [ ] T047 [US1] Implement `write_entry()` in NullMemory that returns success result with empty entry_id
- [ ] T048 [US1] Implement `read_entries()` in NullMemory that returns empty list
- [ ] T049 [US1] Implement `select_for_injection()` in NullMemory that returns empty structure (empty context_blocks, non_authoritative_marker)
- [ ] T050 [US1] Implement `get_usage_stats()` in NullMemory that returns zero counts
- [ ] T051 [US1] Implement `list_entries()` in NullMemory that returns empty list
- [ ] T052 [US1] Implement `delete_session_entries()` in NullMemory that returns success with entries_removed=0
- [ ] T053 [US1] Add unit tests for STM at `tests/unit/test_stm.py` covering write_entry, read_entries, session scoping, execution annotations, phase annotations, graceful degradation
- [ ] T054 [US1] Add unit tests for NullMemory at `tests/unit/test_null_memory.py` covering no-op behavior, graceful degradation
- [ ] T055 [US1] Add contract tests for MAI at `tests/contract/test_memory_interface.py` verifying interface contract compliance, graceful degradation

---

## Phase 5: User Story 2 - Bounded Memory with Deterministic Eviction (P1)

**Goal**: Implement capacity limits and TTL-based eviction in STM, ensuring memory remains bounded and predictable.

**Independent Test**: Can write memory entries until capacity is exceeded, then verify deterministic eviction occurs. Can write entries and verify TTL-based eviction occurs when entries expire. Eviction is transparent to execution (no exceptions).

**Test Criteria**:
- Capacity limit is enforced deterministically (same sequence of writes produces same eviction results)
- TTL decrement occurs autonomously by STM on any STM access (read, write, select) for session_id
- All entries in session are decremented to preserve recency bias
- Expired entries (TTL ≤ 0) are excluded from query results
- Expired entries are removed from physical memory
- Both capacity and TTL eviction work simultaneously
- Eviction is transparent to execution (no exceptions, graceful degradation)

- [ ] T060 [US2] Add capacity limit configuration to STM: `_capacity: int` (configurable, e.g., 100-1000 entries per session)
- [ ] T061 [US2] Implement capacity check in STM `write_entry()`: when capacity exceeded, perform deterministic soft eviction
- [ ] T062 [US2] Implement deterministic eviction algorithm in STM: evict entries based on creation order or LRU (must be deterministic, same input produces same output)
- [ ] T063 [US2] Add TTL configuration to STM: `_initial_ttl: int` (configurable static variable, default: 10)
- [ ] T064 [US2] Implement TTL assignment in STM `write_entry()`: assign initial TTL value to new entries
- [ ] T065 [US2] Implement autonomous TTL decrement in STM: on any STM operation (read_entries, write_entry, select_for_injection) for session_id, decrement TTL for all entries in that session
- [ ] T066 [US2] Implement expired entry exclusion in STM: exclude entries with TTL ≤ 0 from all read and search operations
- [ ] T067 [US2] Implement expired entry removal in STM: remove expired entries from physical memory (delete from `_store`) for security and resource management
- [ ] T068 [US2] Update `write_entry()` result to include `evicted_count` in MemoryWriteResult
- [ ] T069 [US2] Add unit tests for capacity eviction at `tests/unit/test_stm.py` covering capacity limit enforcement, deterministic eviction, evicted_count reporting
- [ ] T070 [US2] Add unit tests for TTL eviction at `tests/unit/test_stm.py` covering TTL assignment, autonomous decrement, recency bias preservation, expired entry exclusion, expired entry removal
- [ ] T071 [US2] Add integration tests for combined eviction at `tests/integration/test_memory_integration.py` covering capacity and TTL eviction working simultaneously

---

## Phase 6: User Story 3 - Memory-Aware Prompt Injection (P2)

**Goal**: Implement memory injection into LLM prompts through explicit, opt-in injection points in prompt registry, with bounded injection budget.

**Independent Test**: Can configure a prompt for memory injection, write memory entries, and verify that selected entries are injected into the prompt within the injection budget. Memory injection is disabled for Phase C and Phase E.

**Test Criteria**:
- Memory injection only occurs through explicit, named, opt-in injection points in prompt registry
- Memory injection is bounded by explicit injection budget (hard upper bound, no truncation of individual entries)
- Memory injection is disabled for Phase C and Phase E prompts
- Memory injection failures degrade silently (prompt renders without memory, execution continues)
- STM `select_for_injection()` performs field extraction, ordering, and light formatting only (NO semantic summarization, inference, or rewriting)
- Non-authoritative marker is applied to injected memory context

- [ ] T080 [US3] Extend prompt registry at `aeon/prompts/registry.py` to support `memory_injection_enabled: bool` flag per prompt configuration
- [ ] T081 [US3] Add memory injection point markers to prompt templates in prompt registry (e.g., `{memory_context}` placeholder)
- [ ] T082 [US3] Implement `select_for_injection()` in STM that selects relevant entries based on session_id, context metadata (current_phase, current_execution_id, injection_point), and recency
- [ ] T083 [US3] Implement phase filtering in STM `select_for_injection()`: Phase B prefers Phase B entries (primary), Phase D entries (secondary); Phase D prefers Phase D entries (primary), Phase B entries (secondary); Phase A rarely uses memory; Phase C and E never inject
- [ ] T084 [US3] Implement execution filtering in STM `select_for_injection()`: prefer entries from earlier executions over current execution (if current_execution_id provided)
- [ ] T085 [US3] Implement recency ordering in STM `select_for_injection()`: order selected entries by created_at (most recent first) with insertion order as tie-breaker
- [ ] T086 [US3] Implement field extraction in STM `select_for_injection()`: extract phase-appropriate fields deterministically (Phase B: prior user statements, prior assistant response text; Phase D: refinement reason, updated goal, step descriptions; Phase A: goal, task profile posture fields)
- [ ] T087 [US3] Implement light formatting in STM `select_for_injection()`: string concatenation, basic punctuation, line breaks only (NO semantic transformation, summarization, paraphrasing, inference, rewriting)
- [ ] T088 [US3] Implement injection budget enforcement in STM `select_for_injection()`: include context blocks in order until budget exhausted, skip blocks that would exceed budget (no partial inclusion)
- [ ] T089 [US3] Implement non-authoritative marker in STM `select_for_injection()`: return `non_authoritative_marker` string (e.g., "Non-authoritative context from this session (for reference only)")
- [ ] T090 [US3] Implement prompt registry memory injection logic: when `memory_injection_enabled=True`, call `select_for_injection()` and format/insert context blocks into prompt templates at injection points
- [ ] T091 [US3] Implement non-authoritative marker application in prompt registry: apply marker when inserting STM context
- [ ] T092 [US3] Enforce memory injection disabled for Phase C and Phase E in prompt registry
- [ ] T093 [US3] Add unit tests for STM `select_for_injection()` at `tests/unit/test_stm.py` covering phase filtering, execution filtering, recency ordering, field extraction, light formatting, budget enforcement, non-authoritative marker
- [ ] T094 [US3] Add integration tests for prompt injection at `tests/integration/test_memory_integration.py` covering memory injection into prompts, budget enforcement, phase restrictions, graceful degradation

---

## Phase 7: User Story 4 - Memory Usage Observability (P2)

**Goal**: Implement content-free observability for memory operations through logs and Phase E metadata.

**Independent Test**: Can perform memory operations and verify that logs contain structural metadata (operation type, entry count, session_id, execution_id, phase) but no raw content. Phase E metadata includes memory usage statistics.

**Test Criteria**:
- Logs contain structural metadata (operation type, entry count, session_id, execution_id, phase) but NO raw memory content
- Phase E metadata includes memory usage statistics (memory_used, memory_entries_considered, memory_entries_injected, memory_failures)
- Memory failures are logged with error types and context but NO content
- Memory operation success is indicated with counts and metadata but NO content

- [ ] T100 [US4] Implement content-free logging in STM: log memory operations with structural metadata (operation type, entry count, session_id, execution_id, phase) but NO raw content
- [ ] T101 [US4] Implement memory failure logging in STM: log failures with error types and context but NO content
- [ ] T102 [US4] Implement `get_usage_stats()` in STM that returns MemoryUsageStats with memory_used, memory_entries_considered, memory_entries_injected, memory_failures, total_entries, expired_entries
- [ ] T103 [US4] Implement `list_entries()` in STM that returns List[MemoryEntryMetadata] with session_id, execution_id, phase, created_at, ttl (NO raw content)
- [ ] T104 [US4] Extend Phase E metadata structure to include memory usage statistics (memory_used: bool, memory_entries_considered: int, memory_entries_injected: int, memory_failures: int)
- [ ] T105 [US4] Wire memory usage stats collection in orchestrator: call `get_usage_stats()` at Phase E and include in Phase E metadata
- [ ] T106 [US4] Add unit tests for observability at `tests/unit/test_stm.py` covering content-free logging, memory usage stats, metadata-only list operations
- [ ] T107 [US4] Add integration tests for observability at `tests/integration/test_memory_integration.py` covering Phase E metadata includes memory stats, logs are content-free
- [ ] T108 [US4] Add automated log analysis test at `tests/integration/test_memory_integration.py` verifying logs contain NO raw memory content
- [ ] T109 [US4] Add automated file I/O test at `tests/integration/test_memory_integration.py` verifying STM performs zero file I/O operations

---

## Phase 8: Integration & Kernel Wiring

**Goal**: Wire memory and session subsystems into orchestrator at appropriate phase boundaries, ensuring kernel remains minimal and memory operations never block execution.

**Independent Test**: Can execute full orchestrator flow with memory enabled, verify memory entries are written at phase boundaries (Phase A, B, D), memory injection occurs in prompts (Phase B, D), session TTL decrements on execution completion, and expired sessions trigger memory cleanup.

**Test Criteria**:
- Orchestrator calls `create_session()` at session start
- Orchestrator calls `write_entry()` after LLM response for Phase A (Plan Generation, TaskProfile Inference), Phase B (Reasoning Steps), Phase D (Recursive Planning/Refinement)
- Orchestrator calls `write_entry()` with metadata only for Phase C
- Orchestrator calls `select_for_injection()` when rendering prompts with memory injection enabled
- Orchestrator calls `notify_execution_complete()` at Phase E
- Orchestrator handles expired session status and triggers STM cleanup
- Kernel LOC remains under 800 after memory wiring
- All phases operate correctly with NullMemory (memory fully disabled)

- [ ] T110 Wire session creation in orchestrator at `aeon/kernel/orchestrator.py`: call `create_session()` at session start
- [ ] T111 Wire memory write in orchestrator at `aeon/kernel/orchestrator.py`: call `write_entry()` after LLM response for Phase A (Plan Generation, TaskProfile Inference)
- [ ] T112 Wire memory write in orchestrator at `aeon/kernel/orchestrator.py`: call `write_entry()` after LLM response for Phase B (Reasoning Steps)
- [ ] T113 Wire memory write in orchestrator at `aeon/kernel/orchestrator.py`: call `write_entry()` with metadata only after LLM response for Phase C (Validation/Convergence)
- [ ] T114 Wire memory write in orchestrator at `aeon/kernel/orchestrator.py`: call `write_entry()` after LLM response for Phase D (Recursive Planning/Refinement)
- [ ] T115 Wire memory injection in prompt registry: call `select_for_injection()` when rendering prompts with `memory_injection_enabled=True`
- [ ] T116 Wire execution completion notification in orchestrator at `aeon/kernel/orchestrator.py`: call `notify_execution_complete()` at Phase E
- [ ] T117 Wire expired session handling in orchestrator at `aeon/kernel/orchestrator.py`: when Session subsystem returns expired status, call `delete_session_entries()` to clean up memory
- [ ] T118 Wire graceful session closure in orchestrator at `aeon/kernel/orchestrator.py`: when session is closed (client/presentation request or termination policy), call `close_session()` and `delete_session_entries()`
- [ ] T119 Add dependency injection for memory and session in orchestrator: accept `memory: MemoryAccessInterface` and `session_manager: SessionSubsystemInterface` as constructor parameters
- [ ] T120 Verify kernel LOC remains under 800 after memory wiring (run LOC check)
- [ ] T121 Add integration tests for orchestrator with memory at `tests/integration/test_memory_integration.py` covering full execution flow with memory enabled, phase boundary writes, memory injection, session lifecycle
- [ ] T122 Add integration tests for orchestrator with NullMemory at `tests/integration/test_memory_integration.py` covering all phases operate correctly with memory fully disabled

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Complete remaining integration tasks, add comprehensive tests, verify all safety constraints, and ensure system robustness.

**Independent Test**: All safety constraints are enforced, all integration tests pass, kernel remains minimal, memory operations never block execution, and system operates correctly with memory enabled and disabled.

**Test Criteria**:
- Memory cannot change plan, step, or tool decisions (non-authoritative constraint)
- Memory only enters prompts via explicit injection points (routing protection)
- Phase E reports memory usage metadata (interpretation protection)
- STM performs no file I/O (no-disk guarantee)
- STM eviction obeys both capacity and TTL bounds deterministically
- STM functions correctly across multiple executions within a single session
- All phases operate correctly with NullMemory
- Kernel receives no new business logic except wiring (kernel minimalism maintained)
- STM cannot operate without session_id
- Session termination triggers STM cleanup
- Multiple executions share STM within a session
- Orchestrator functions with Session enabled but STM disabled
- STM functions correctly with Session enabled

- [ ] T130 Add safety constraint tests at `tests/integration/test_memory_integration.py` covering memory cannot change plan/step/tool decisions (non-authoritative constraint)
- [ ] T131 Add routing protection tests at `tests/integration/test_memory_integration.py` covering memory only enters prompts via explicit injection points
- [ ] T132 Add interpretation protection tests at `tests/integration/test_memory_integration.py` covering Phase E reports memory usage metadata
- [ ] T133 Add no-disk guarantee tests at `tests/integration/test_memory_integration.py` covering STM performs no file I/O (verified by automated file system monitoring)
- [ ] T134 Add eviction determinism tests at `tests/integration/test_memory_integration.py` covering STM eviction obeys both capacity and TTL bounds deterministically
- [ ] T135 Add multi-execution tests at `tests/integration/test_memory_integration.py` covering STM functions correctly across multiple executions within a single session
- [ ] T136 Add NullMemory integration tests at `tests/integration/test_memory_integration.py` covering all phases operate correctly with NullMemory
- [ ] T137 Add kernel minimalism verification: verify kernel LOC remains under 800, verify kernel has no new business logic except wiring
- [ ] T138 Add session dependency tests at `tests/integration/test_memory_integration.py` covering STM cannot operate without session_id, session termination triggers STM cleanup
- [ ] T139 Add session integration tests at `tests/integration/test_session_integration.py` covering orchestrator functions with Session enabled but STM disabled, STM functions correctly with Session enabled
- [ ] T140 Add comprehensive error handling tests covering all graceful degradation scenarios (memory failures, session failures, validation failures)
- [ ] T141 Add performance tests verifying memory operations complete in <10ms for typical workloads
- [ ] T142 Add documentation updates: update README with memory usage examples, update API documentation with MAI and Session interfaces
- [ ] T143 Run full test suite and verify all tests pass
- [ ] T144 Verify all acceptance scenarios from spec.md are covered by tests

---

## Notes

- **Kernel Minimalism**: All kernel changes must be wiring only (~50-100 LOC). No domain logic in kernel.
- **Graceful Degradation**: All memory and session operations must never raise exceptions. Use structured results.
- **Content-Free Observability**: Logs and metadata must never contain raw memory content.
- **No Disk I/O**: STM and Session subsystem must never write to disk (verified by automated tests).
- **Autonomous TTL Management**: Session and Memory Entry TTLs are managed autonomously by their respective subsystems. Orchestrator has no knowledge of TTL internals.
- **Ingest/Emit Asymmetry**: `write_entry()` ingests raw artifacts, `select_for_injection()` emits field-extracted projections. NO semantic processing.
- **Phase Restrictions**: Memory injection disabled for Phase C and Phase E.

