# Research: Observability, Logging, and Test Coverage

**Date**: 2025-01-27  
**Feature**: Observability, Logging, and Test Coverage  
**Phase**: 0 - Research

## Overview

This document consolidates research findings and technical decisions for implementing phase-aware structured logging, actionable error logging, enhanced debug visibility, and expanded test coverage. All decisions are based on requirements from `spec.md` and constitutional constraints.

## Research Decisions

### Decision 1: Correlation ID Generation Strategy

**Decision**: Use deterministic UUIDv5 with namespace UUID and timestamp-based name for correlation ID generation.

**Rationale**:
- UUIDv5 provides deterministic generation (same inputs produce same UUID)
- Determinism preserves kernel determinism (constitutional requirement)
- Timestamp component ensures uniqueness across executions
- Standard library `uuid` module provides UUIDv5 support (no external dependencies)
- Namespace UUID can be a fixed constant (e.g., UUID for "aeon-correlation")
- Name component combines execution start timestamp and request hash for uniqueness

**Alternatives Considered**:
- UUIDv4 (random): Rejected - non-deterministic, violates kernel determinism requirement
- Sequential integers: Rejected - not unique across restarts, requires state management
- Timestamp-only: Rejected - not unique enough for concurrent executions
- External correlation ID service: Rejected - adds complexity, violates simplicity constraints

**Implementation Approach**:
- Use `uuid.uuid5()` with fixed namespace UUID (e.g., `uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')`)
- Name component: `f"{execution_start_timestamp}:{request_hash}"` where request_hash is SHA256 hash of request string
- Generate correlation ID once at execution start, persist through all phases and passes
- Store correlation ID in execution context, pass to all logging calls

**Error Handling**:
- If UUIDv5 generation fails, fall back to deterministic timestamp-based ID: `f"aeon-{execution_start_timestamp}-{request_hash[:8]}"`
- Fallback ensures logging continues even if UUID generation fails

### Decision 2: Structured Error Model Design

**Decision**: Extend existing exception hierarchy with structured error classes containing error codes, severity levels, and context fields.

**Rationale**:
- Error codes enable filtering and categorization (FR-012)
- Severity levels enable prioritization and filtering (FR-012)
- Structured context enables diagnosis without code inspection (FR-018)
- Extends existing `aeon/exceptions.py` hierarchy (maintains consistency)
- Error codes use "AEON.<COMPONENT>.<CODE>" format for clarity and filtering

**Alternatives Considered**:
- Separate error model outside exception hierarchy: Rejected - exceptions provide stack traces and Pythonic error handling
- Error codes only (no structured classes): Rejected - insufficient context for diagnosis
- External error tracking service: Rejected - violates simplicity constraints, adds dependencies

**Implementation Approach**:
- Add `ErrorRecord` Pydantic model with fields: `code`, `severity`, `message`, `affected_component`, `context` (dict), `stack_trace` (optional)
- Extend exception classes with `to_error_record()` method that returns ErrorRecord
- Error codes follow format: `AEON.<COMPONENT>.<CODE>` where COMPONENT is REFINEMENT, EXECUTION, VALIDATION, etc.
- Severity levels: CRITICAL, ERROR, WARNING, INFO (enum)
- Error codes are constants defined in each exception class (e.g., `RefinementError.ERROR_CODE = "AEON.REFINEMENT.001"`)

**Error Code Examples**:
- `AEON.REFINEMENT.001`: Refinement action application failed
- `AEON.EXECUTION.002`: Step execution failed
- `AEON.VALIDATION.003`: Validation check failed
- `AEON.PHASE.004`: Phase transition failed

### Decision 3: Phase-Aware Logging Event Schema

**Decision**: Extend LogEntry model with phase event types (phase_entry, phase_exit, state_transition, refinement_outcome, evaluation_outcome, error_recovery) and correlation_id field.

**Rationale**:
- Phase events enable trace reconstruction through multi-pass execution (FR-001, FR-002)
- Correlation ID links all events for a single execution (FR-003, FR-004)
- Structured event types enable filtering and analysis
- Backward compatible with existing LogEntry schema (adds optional fields)

**Alternatives Considered**:
- Separate log files per phase: Rejected - breaks correlation, complicates analysis
- Single event type with phase field: Rejected - insufficient structure for filtering
- External event streaming: Rejected - violates simplicity constraints

**Implementation Approach**:
- Add `event` field to LogEntry: `Literal["phase_entry", "phase_exit", "state_transition", "refinement_outcome", "evaluation_outcome", "error_recovery", "cycle"]`
- Add `correlation_id` field (required for all entries)
- Add `phase` field (required for phase events, optional for cycle events)
- Add event-specific data fields (e.g., `before_state`, `after_state` for state_transition)
- Maintain backward compatibility: existing `format_entry()` method continues to work, creates `event="cycle"` entries

**Event Schema**:
- `phase_entry`: phase, correlation_id, timestamp, optional context
- `phase_exit`: phase, correlation_id, timestamp, duration, outcome (success/failure)
- `state_transition`: correlation_id, component, before_state (snapshot), after_state (snapshot), transition_reason, timestamp
- `refinement_outcome`: correlation_id, pass_number, phase, evaluation_signals, refinement_actions, before_plan_fragment, after_plan_fragment, timestamp
- `evaluation_outcome`: correlation_id, pass_number, phase, convergence_assessment, validation_report, timestamp
- `error_recovery`: correlation_id, original_error, recovery_action, recovery_outcome, timestamp

### Decision 4: State Snapshot Design

**Decision**: Log only minimal structured state slices relevant to the transitioning component, including transition reason.

**Rationale**:
- Full state snapshots are too large and contain irrelevant data (FR-005)
- Minimal slices reduce log size and improve readability
- Component-specific slices enable targeted debugging
- Transition reason explains why state changed

**Alternatives Considered**:
- Full state snapshots: Rejected - too large, contains irrelevant data
- No state snapshots: Rejected - insufficient context for debugging
- Diff-based snapshots: Rejected - complex to implement, harder to parse

**Implementation Approach**:
- Define state slice schemas per component (e.g., `PlanStateSlice`, `ExecutionStateSlice`, `RefinementStateSlice`)
- State slices contain only fields relevant to component transitions
- Include `transition_reason` field explaining why state changed
- Use Pydantic models for state slices to ensure structure and validation
- Log before_state and after_state as separate fields in state_transition events

**State Slice Examples**:
- PlanStateSlice: `{plan_id, current_step_id, step_count, steps_status_summary}`
- ExecutionStateSlice: `{current_step_id, step_status, tool_calls_count, errors_count}`
- RefinementStateSlice: `{refinement_type, changed_steps_count, added_steps_count, removed_steps_count}`

### Decision 5: Plan Fragment Logging Pattern

**Decision**: Log only changed steps (modified/added/removed) with step IDs, referencing unchanged steps by ID only.

**Rationale**:
- Full plan logging is redundant and large (FR-006, FR-013)
- Changed steps provide sufficient context for debugging refinement
- Step ID references enable reconstruction of full plan context if needed
- Reduces log size and improves readability

**Alternatives Considered**:
- Full plan logging: Rejected - too large, redundant
- No plan logging: Rejected - insufficient context for refinement debugging
- Diff format: Rejected - complex to implement, harder to parse

**Implementation Approach**:
- Define `PlanFragment` model with fields: `changed_steps` (list of changed PlanStep), `unchanged_step_ids` (list of step IDs)
- Changed steps include full step data (step_id, description, status, tool, etc.)
- Unchanged steps referenced by ID only
- Log before_plan_fragment and after_plan_fragment in refinement_outcome events
- Use same pattern for error logging (FR-013)

### Decision 6: Evaluation Signal Logging Pattern

**Decision**: Log convergence assessment summary (reason codes, scores, converged boolean) and validation issues summary (issue counts, severity levels).

**Rationale**:
- Full evaluation signals are too large and contain redundant data (FR-006, FR-013, FR-019)
- Summaries provide sufficient context for debugging without log bloat
- Reason codes and scores explain convergence decisions
- Issue counts and severity levels explain validation outcomes

**Alternatives Considered**:
- Full evaluation signals: Rejected - too large, contains redundant data
- No evaluation signals: Rejected - insufficient context for debugging
- Aggregated metrics only: Rejected - loses important detail (reason codes, severity levels)

**Implementation Approach**:
- Define `ConvergenceAssessmentSummary` model: `{converged, reason_codes, scores, pass_number}`
- Define `ValidationIssuesSummary` model: `{total_issues, critical_count, error_count, warning_count, info_count, issues_by_type}`
- Log summaries in refinement_outcome and evaluation_outcome events
- Include full details only when explicitly requested (debug mode)

### Decision 7: Test Coverage Expansion Strategy

**Decision**: Expand test coverage to ≥80% by adding phase transition tests, error-path tests, TTL boundary tests, context propagation tests, and deterministic convergence tests.

**Rationale**:
- Current coverage (~55%) is insufficient for safe refactoring (FR-024)
- Phase transition tests validate phase entry/exit behavior (FR-025)
- Error-path tests validate error handling and logging (FR-026)
- TTL boundary tests validate expiration behavior (FR-027)
- Context propagation tests validate phase context handoffs (FR-028)
- Deterministic convergence tests validate convergence behavior (FR-029)

**Alternatives Considered**:
- Focus only on new code coverage: Rejected - insufficient for regression prevention
- Mock-based testing only: Rejected - tests must be deterministic and avoid mocking future features (FR-030, FR-031)
- Integration tests only: Rejected - unit tests are needed for isolated component testing

**Implementation Approach**:
- Use pytest-cov for coverage measurement and reporting
- Add phase transition tests in `tests/integration/test_phase_transitions.py`
- Add error-path tests in `tests/integration/test_error_paths.py`
- Add TTL boundary tests in `tests/integration/test_ttl_boundaries.py` (single-pass only, no adaptive depth)
- Add context propagation tests in `tests/integration/test_context_propagation.py` (phase context, not memory)
- Add deterministic convergence tests in `tests/integration/test_deterministic_convergence.py` (simple, repeatable tasks)
- Expand unit test coverage for observability modules, error models, and logging interfaces
- Ensure all tests are deterministic (no flaky tests)

### Decision 8: Logging Performance Optimization

**Decision**: Keep logging synchronous and lightweight, with <10ms latency per log entry, unless profiling proves otherwise.

**Rationale**:
- Synchronous logging preserves determinism (FR-033, FR-035)
- Lightweight logging prevents performance regressions (FR-036)
- <10ms latency target ensures logging doesn't block execution (SC-005)
- Profiling will validate actual performance (FR-033)

**Alternatives Considered**:
- Async logging: Rejected - adds complexity, may affect determinism
- Buffered logging: Rejected - adds complexity, may lose logs on crash
- External logging service: Rejected - violates simplicity constraints, adds dependencies

**Implementation Approach**:
- Keep existing synchronous file-based JSONL logging
- Optimize JSON serialization (use `model_dump_json()` for Pydantic models)
- Minimize state snapshot size (use minimal slices)
- Profile logging operations and optimize hot paths if needed
- Measure logging latency in integration tests
- If profiling shows >10ms latency, optimize serialization or reduce snapshot size

### Decision 9: Backward Compatibility Strategy

**Decision**: Maintain backward compatibility with existing log schema by adding optional fields and supporting both old and new log entry formats.

**Rationale**:
- Existing logs must remain parseable (FR-009)
- Gradual migration enables safe rollout
- Optional fields don't break existing log parsers
- Schema versioning enables future migrations

**Alternatives Considered**:
- Breaking change with schema version: Rejected - breaks existing log analysis tools
- Separate log files for new format: Rejected - complicates correlation and analysis
- No backward compatibility: Rejected - breaks existing infrastructure

**Implementation Approach**:
- Add new fields as optional (correlation_id, event, phase-specific fields)
- Existing `format_entry()` method continues to work, creates entries with `event="cycle"`
- New phase-aware methods create entries with `event="phase_entry"`, etc.
- Log schema remains valid JSONL, existing parsers can ignore new fields
- Document schema evolution in quickstart.md

### Decision 10: Error Recovery Logging Pattern

**Decision**: Log error recovery attempts with original error, recovery action, and recovery outcome.

**Rationale**:
- Error recovery logging enables debugging of recovery logic (FR-017)
- Original error context is preserved for diagnosis
- Recovery action and outcome explain recovery behavior
- Enables analysis of recovery success rates

**Alternatives Considered**:
- No recovery logging: Rejected - insufficient visibility into recovery behavior
- Log only recovery failures: Rejected - need to track recovery success for analysis
- Full error stack traces in recovery logs: Rejected - too verbose, stack traces in original error

**Implementation Approach**:
- Add `error_recovery` event type to LogEntry
- Log recovery attempts with fields: `correlation_id`, `original_error` (ErrorRecord), `recovery_action` (string), `recovery_outcome` (success/failure), `timestamp`
- Recovery logging happens in kernel when recovery decisions are made (FR-016)
- Original error is logged separately before recovery attempt

## Technical Dependencies

### Python Standard Library
- `uuid`: UUIDv5 generation for correlation IDs
- `json`: JSON serialization (already used)
- `datetime`: Timestamp generation (already used)

### Existing Dependencies
- `pydantic>=2.0.0`: Data models for LogEntry, ErrorRecord, state slices
- `pytest`: Test framework (already used)
- `pytest-cov`: Coverage reporting (already used)

### No New Dependencies
- All requirements can be met with existing dependencies and standard library
- No external monitoring services or logging libraries required

## Integration Points

### Kernel Integration
- Kernel invokes logging through `JSONLLogger` interface (no changes to kernel)
- Correlation ID generated at execution start, passed to all logging calls
- Phase transitions logged by orchestration modules, not kernel

### Orchestration Integration
- `aeon/orchestration/phases.py` logs phase entry/exit events
- `aeon/orchestration/refinement.py` logs refinement outcomes
- `aeon/orchestration/step_prep.py` logs step preparation events (if needed)

### Error Handling Integration
- Exception classes extended with `to_error_record()` method
- Error logging happens at exception catch sites
- Recovery logging happens in kernel when recovery decisions are made

## Performance Considerations

### Logging Latency
- Target: <10ms per log entry (SC-005)
- Measurement: Profile logging operations in integration tests
- Optimization: Minimize state snapshot size, optimize JSON serialization

### Log File Size
- Minimal state slices reduce log size
- Changed steps only in plan fragments reduce log size
- Evaluation signal summaries reduce log size
- Compression can be added later if needed (out of scope)

### Determinism
- Correlation ID generation is deterministic (UUIDv5)
- Logging operations are synchronous (no async complexity)
- No non-deterministic behavior introduced

## Testing Strategy

### Unit Tests
- Test correlation ID generation (deterministic, unique)
- Test error record creation from exceptions
- Test phase event logging
- Test state snapshot creation (minimal slices)
- Test plan fragment creation (changed steps only)
- Test evaluation signal summarization

### Integration Tests
- Test phase transition logging (entry/exit events, correlation IDs)
- Test error logging (structured error records, error codes)
- Test refinement outcome logging (plan fragments, evaluation signals)
- Test state transition logging (before/after snapshots)
- Test correlation ID persistence across phases and passes
- Test logging performance (<10ms latency)

### Coverage Goals
- Overall coverage: ≥80% (FR-024, SC-003)
- Observability modules: ≥90% (critical infrastructure)
- Error models: ≥90% (critical for debugging)
- Integration tests: Cover all phase transitions, error paths, TTL boundaries, context propagation, deterministic convergence

## Open Questions Resolved

All technical questions from the feature spec have been resolved:

1. ✅ **Correlation ID generation**: Deterministic UUIDv5 with timestamp component
2. ✅ **Plan fragment detail level**: Changed steps only with step IDs
3. ✅ **Evaluation signal structure**: Convergence assessment summary + validation issues summary
4. ✅ **Error code format**: AEON.<COMPONENT>.<CODE> format
5. ✅ **State snapshot detail level**: Minimal structured state slices with transition reason

## Next Steps

1. **Phase 1 Design**: Create data-model.md with LogEntry extensions, ErrorRecord model, state slice models
2. **Phase 1 Contracts**: Create contracts/interfaces.md with logging interface contracts
3. **Phase 1 Quickstart**: Create quickstart.md with usage examples
4. **Phase 2 Tasks**: Generate tasks.md with implementation breakdown

