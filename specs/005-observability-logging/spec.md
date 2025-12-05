# Feature Specification: Observability, Logging, and Test Coverage

**Feature Branch**: `005-observability-logging`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Sprint 5 establishes the diagnostic substrate for all subsequent work. Produce a specification defining: structured, consistent, phase-aware observability across the reasoning loop, actionable error logging and error models, improved debug visibility for plan/refinement failures, expanded test coverage to ≥80%, and clear boundaries preventing performance regressions and scope creep."

## Clarifications

### Session 2025-01-27

- Q: How should correlation IDs be generated? → A: Deterministic UUIDv5 with timestamp
- Q: What level of detail should plan fragments contain in logs? → A: Changed steps only with step IDs
- Q: What structure should evaluation signals have in logs? → A: Convergence assessment summary + validation issues summary
- Q: What format should error codes use? → A: AEON.<COMPONENT>.<CODE> format (e.g., "AEON.REFINEMENT.001", "AEON.EXECUTION.002")
- Q: What level of detail should state snapshots contain? → A: Log only the minimal structured state slice relevant to the transitioning component, including a transition reason

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phase-Aware Structured Logging (Priority: P1)

As a developer debugging the reasoning loop, I can review structured logs that clearly show phase transitions (A→B→C→D), state changes, and correlation IDs that link related events across the entire execution cycle.

**Why this priority**: Without phase-aware logging, developers cannot trace failures through the multi-pass reasoning loop. This is foundational for all debugging work in subsequent sprints. Correlation IDs enable tracking a single request through all phases and passes.

**Independent Test**: Can be fully tested by executing a multi-pass reasoning task and verifying that logs contain phase entry/exit markers, state transition records, and a consistent correlation ID that appears in all log entries for that execution. The test delivers value by proving developers can trace execution flow and identify where failures occur.

**Acceptance Scenarios**:

1. **Given** a multi-pass execution starts, **When** Phase A begins, **Then** a log entry is generated with phase="A", event="phase_entry", correlation_id, and timestamp
2. **Given** Phase A completes successfully, **When** Phase B begins, **Then** log entries show phase="A" event="phase_exit" followed by phase="B" event="phase_entry", both sharing the same correlation_id
3. **Given** execution spans multiple passes, **When** reviewing logs, **Then** all entries for the same execution share the same correlation_id, enabling trace reconstruction
4. **Given** state transitions occur during execution, **When** reviewing logs, **Then** state change events are logged with before/after snapshots and correlation_id
5. **Given** logs are written in JSONL format, **When** parsing log files, **Then** each line is valid JSON with stable schema fields (phase, event, correlation_id, timestamp, data)

---

### User Story 2 - Actionable Error Logging (Priority: P1)

As a developer investigating failures, I can review error logs that contain structured error information including error codes, severity levels, affected components, step IDs, attempted actions, and context that enables rapid diagnosis.

**Why this priority**: Current error logging is shallow and inconsistent. Developers need structured error information to diagnose refinement failures, execution errors, and plan validation issues. This blocks effective debugging of issues in subsequent sprints.

**Independent Test**: Can be fully tested by triggering various error conditions (refinement failures, execution errors, validation failures) and verifying that error logs contain all required fields (code, severity, message, component, step_id, context) in a structured format. The test delivers value by proving developers can quickly identify root causes and affected components.

**Evaluation Signals Structure**:
evaluation_signals MUST be a dict with the following keys:
   - convergence_assessment: the ConvergenceAssessmentSummary model serialized to a dict (e.g., model_dump()),
   - validation_issues: the ValidationIssuesSummary model serialized to a dict.
    - No additional keys are required in this sprint.

**Acceptance Scenarios**:

1. **Given** a refinement operation fails, **When** the error is logged, **Then** the log entry contains error_code, severity, affected_component="refinement", step_id (if applicable), attempted_action, before_plan_fragment, after_plan_fragment, and evaluation_signals
2. **Given** an execution step fails, **When** the error is logged, **Then** the log entry contains error_code, severity, affected_component="execution", step_id, attempted_action, tool_name (if tool-based), and error_context
3. **Given** a validation error occurs, **When** the error is logged, **Then** the log entry contains error_code, severity, affected_component="validation", validation_type, and validation_details
4. **Given** errors occur at different severity levels, **When** reviewing logs, **Then** severity levels (CRITICAL, ERROR, WARNING, INFO) are clearly indicated and filterable
5. **Given** an error occurs, **When** the error is logged, **Then** the error is never silently recovered inside modules; recovery decisions are made by the kernel and logged separately

---

### User Story 3 - Refinement and Execution Debug Visibility (Priority: P2)

As a developer debugging plan refinement or execution failures, I can review detailed logs showing refinement outcomes, evaluation signals, plan state changes, and execution results that explain why refinements were applied or why execution failed.

**Why this priority**: Refinement and execution failures are currently difficult to debug because logs don't capture the decision context. Developers need visibility into why refinements were triggered, what changes were made, and why execution steps failed. This is secondary to basic error logging (P1) but critical for complex debugging scenarios.

**Independent Test**: Can be fully tested by executing a plan that requires refinement and verifying that logs capture refinement triggers (evaluation signals, validation issues), refinement actions applied, before/after plan fragments, and execution results with sufficient detail to understand failures. The test delivers value by proving developers can understand refinement and execution behavior.

**Acceptance Scenarios**:

1. **Given** a refinement is triggered, **When** reviewing logs, **Then** logs show the evaluation signals that triggered refinement (convergence assessment, validation issues), the refinement actions applied, and before/after plan fragments
2. **Given** execution results are generated, **When** reviewing logs, **Then** logs show step execution outcomes, tool invocation results (if applicable), step status changes, and any errors encountered
3. **Given** a plan fails to converge, **When** reviewing logs, **Then** logs show the convergence assessment results, reason codes, and evaluation signals that explain why convergence was not achieved
4. **Given** refinement changes are applied, **When** reviewing logs, **Then** logs show which steps were modified, added, or removed, with sufficient context to understand the changes

---

### User Story 4 - Comprehensive Test Coverage (Priority: P1)

As a developer maintaining the codebase, I can run a test suite with ≥80% coverage that includes phase transition tests, error-path tests, TTL boundary tests, context propagation tests, and deterministic convergence tests that validate system behavior without relying on future features.

**Why this priority**: Current test coverage (~55%) is insufficient for safe refactoring and regression prevention. Without adequate test coverage, changes in subsequent sprints risk introducing bugs. Tests must be deterministic and avoid mocking future features to remain reliable.

**Independent Test**: Can be fully tested by running the test suite with coverage reporting and verifying that coverage is ≥80%, that phase transition tests exist, that error-path tests cover refinement and execution failures, that TTL boundary tests exist, and that context propagation tests validate phase context (not memory). The test delivers value by proving the codebase is well-tested and safe to refactor.

**Acceptance Scenarios**:

1. **Given** the test suite is executed with coverage reporting, **When** coverage is calculated, **Then** overall coverage is ≥80%
2. **Given** phase transitions occur during execution, **When** running phase transition tests, **Then** tests verify correct phase entry/exit behavior, state handoffs, and error handling at phase boundaries
3. **Given** error conditions are triggered, **When** running error-path tests, **Then** tests verify that refinement errors, execution errors, and validation errors are properly handled and logged
4. **Given** TTL expiration scenarios, **When** running TTL boundary tests, **Then** tests verify correct behavior at TTL boundaries (single-pass only; no adaptive depth)
5. **Given** context propagation occurs, **When** running context propagation tests, **Then** tests verify that phase context (not memory) is correctly propagated between phases
6. **Given** simple tasks are executed, **When** running deterministic convergence tests, **Then** tests verify that convergence behaves deterministically for simple, repeatable tasks

---

### Edge Cases

- What happens when logging fails (file write errors, disk full)? System must continue execution without blocking
- What happens when correlation ID generation fails? System must fall back to a timestamp-based deterministic ID if UUIDv5 generation fails
- What happens when error logging itself raises an exception? System must catch and ignore logging errors to prevent cascading failures
- What happens when test coverage calculation is inaccurate due to dynamic code paths? Coverage reporting must account for conditional execution paths
- What happens when phase transitions occur rapidly? Logs must capture all transitions without losing events
- What happens when multiple errors occur simultaneously? All errors must be logged with proper correlation IDs
- What happens when refinement produces no changes? Logs must indicate refinement was attempted but no changes were needed
- What happens when execution completes with partial failures? Logs must clearly distinguish between successful steps and failed steps

## Requirements *(mandatory)*

### Functional Requirements

#### Structured Logging

- **FR-001**: The system MUST log phase entry events with fields: phase (A/B/C/D), event="phase_entry", correlation_id, timestamp, and optional context data
- **FR-002**: The system MUST log phase exit events with fields: phase (A/B/C/D), event="phase_exit", correlation_id, timestamp, duration, and outcome (success/failure)
- **FR-003**: The system MUST generate a unique correlation ID for each execution cycle that persists across all phases and passes. Correlation IDs MUST be generated using deterministic UUIDv5 (namespace + name) with timestamp component to ensure uniqueness and determinism
- **FR-004**: The system MUST include correlation_id in all log entries for a given execution cycle
- **FR-005**: The system MUST log state transitions with fields: event="state_transition", correlation_id, component, before_state (snapshot), after_state (snapshot), transition_reason, and timestamp. State snapshots MUST contain only the minimal structured state slice relevant to the transitioning component, not full orchestration state
- **FR-006**: The system MUST log refinement outcomes with fields: event="refinement_outcome", correlation_id, pass_number, phase, evaluation_signals, refinement_actions, before_plan_fragment, after_plan_fragment, and timestamp. Plan fragments MUST contain only changed steps (modified/added/removed) with step IDs, referencing unchanged steps by ID only. Evaluation signals MUST include convergence assessment summary (reason codes, scores, converged boolean) and validation issues summary (issue counts, severity levels)
- **FR-007**: The system MUST log evaluation outcomes with fields: event="evaluation_outcome", correlation_id, pass_number, phase, convergence_assessment, validation_report, and timestamp
- **FR-008**: The system MUST output logs in JSONL format (one JSON object per line)
- **FR-009**: The system MUST ensure log schemas are stable and backward-compatible within the same major version
- **FR-010**: Logging MUST be synchronous and lightweight. Async logging is not permitted in this architecture because log determinism and phase-order fidelity are required for debugging and reasoning stability.
- **FR-011**: The system MUST ensure logging does not reduce kernel determinism

#### Error Logging and Error Models

- **FR-012**: The system MUST define error classes with required fields: code (string), severity (CRITICAL/ERROR/WARNING/INFO), message (string), affected_component (string), and optional fields: stack_trace, context (dict). Error codes MUST use the format "AEON.<COMPONENT>.<CODE>" (e.g., "AEON.REFINEMENT.001", "AEON.EXECUTION.002", "AEON.VALIDATION.003") to enable filtering and categorization
- **FR-013**: The system MUST log refinement errors with fields: error_code, severity, affected_component="refinement", step_id (if applicable), attempted_action, before_plan_fragment, after_plan_fragment, evaluation_signals, and correlation_id. Plan fragments MUST contain only changed steps (modified/added/removed) with step IDs, referencing unchanged steps by ID only. Evaluation signals MUST include convergence assessment summary (reason codes, scores, converged boolean) and validation issues summary (issue counts, severity levels)
- **FR-014**: The system MUST log execution errors with fields: error_code, severity, affected_component="execution", step_id, attempted_action, tool_name (if tool-based), error_context, and correlation_id
- **FR-015**: The system MUST log validation errors with fields: error_code, severity, affected_component="validation", validation_type, validation_details, and correlation_id
- **FR-016**: The system MUST ensure errors are never silently recovered inside modules; recovery decisions MUST be made by the kernel and logged separately
- **FR-017**: The system MUST log error recovery attempts with fields: event="error_recovery", correlation_id, original_error, recovery_action, recovery_outcome, and timestamp
- **FR-018**: The system MUST ensure error logging captures sufficient context to enable diagnosis without requiring code inspection

#### Debug Visibility

- **FR-019**: The system MUST log refinement triggers showing evaluation signals (convergence assessment, validation issues) that caused refinement to be triggered. Evaluation signals MUST include convergence assessment summary (reason codes, scores, converged boolean) and validation issues summary (issue counts, severity levels)
- **FR-020**: The system MUST log refinement actions showing which steps were modified, added, or removed during refinement
- **FR-021**: The system MUST log execution results showing step execution outcomes, tool invocation results (if applicable), and step status changes
- **FR-022**: The system MUST log convergence assessment results showing reason codes and evaluation signals that explain convergence decisions
- **FR-023**: Refinement logs MUST include: (1) the refinement trigger context (reason_code and trigger_type), (2) mutated step fragments with step_id and change_type, (3) convergence and validation summaries (status, issue counts, highest severity), (4) error context when applicable, and (5) correlation_id, pass_number, and phase. Only minimal before/after fragments for changed fields are required; full plan snapshots MUST NOT be logged.

#### Test Coverage

- **FR-024**: The system MUST achieve ≥80% overall test coverage as measured by standard coverage tools
- **FR-025**: The system MUST include phase transition tests that verify correct phase entry/exit behavior, state handoffs, and error handling at phase boundaries
- **FR-026**: The system MUST include error-path tests that verify refinement errors, execution errors, and validation errors are properly handled and logged
- **FR-027**: The system MUST include TTL boundary tests that verify correct behavior at TTL boundaries (single-pass only; no adaptive depth)
- **FR-028**: The system MUST include context propagation tests that verify phase context (not memory) is correctly propagated between phases
- **FR-029**: The system MUST include deterministic convergence tests that verify convergence behaves deterministically for simple, repeatable tasks
- **FR-030**: The system MUST ensure tests remain deterministic (no flaky tests)
- **FR-031**: The system MUST ensure tests avoid mocking future features (memory, advanced validation)
- **FR-032**: The system MUST ensure tests validate logging schema and error model behaviors

#### Performance and Simplicity Constraints

- **FR-033**: The system MUST ensure logging remains synchronous and lightweight
- **FR-034**: The system MUST NOT introduce new async complexity, queues, or external monitoring integrations
- **FR-035**: The system MUST ensure observability does not reduce kernel determinism
- **FR-036**: The logging system MUST be designed so that under normal conditions, logging I/O does not visibly dominate end-to-end task runtime. Logging MUST be synchronous and use buffered, minimal formatting to keep overhead small.

### Key Entities

- **LogEntry**: A structured log record containing phase, event, correlation_id, timestamp, and event-specific data. LogEntries are written in JSONL format with stable schemas.
- **ErrorRecord**: A structured error record containing error_code, severity, message, affected_component, and optional context. ErrorRecords are included in LogEntries when errors occur.
- **CorrelationID**: A unique identifier that links all log entries for a single execution cycle, enabling trace reconstruction across phases and passes. Generated using deterministic UUIDv5 with timestamp component to ensure uniqueness and determinism.
- **PhaseContext**: Contextual information that is propagated between phases (not memory-related). PhaseContext includes phase state, evaluation signals, and refinement history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can trace a single execution through all phases using correlation IDs, with 100% of log entries for an execution containing the same correlation_id
- **SC-002**: Error logs contain all required structured fields (code, severity, component, context) in 100% of error cases, enabling diagnosis without code inspection
- **SC-003**: Test coverage increases from ~55% to ≥80% as measured by standard coverage tools
- **SC-004**: Phase transition tests, error-path tests, TTL boundary tests, context propagation tests, and deterministic convergence tests are all present and passing
- **SC-005**: During manual verification on a small set of representative tasks, end-to-end runtime remains clearly dominated by LLM calls and reasoning work, not logging I/O.
- **SC-006**: Kernel determinism is preserved, with no non-deterministic behavior introduced by observability improvements
- **SC-007**: All log entries conform to stable JSONL schemas, with 100% of log entries being valid JSON and parseable by standard JSON parsers
- **SC-008**: Developers can diagnose refinement and execution failures using log data alone in ≥90% of failure cases, without requiring code inspection or additional debugging tools

## Out of Scope

To prevent scope creep and maintain focus, the following are explicitly excluded from this sprint:

- **Prompt consolidation or template work** (deferred to Sprint 7)
- **Memory semantics, scoring, or propagation logic** (deferred to Sprint 8+)
- **Convergence algorithm tuning** (deferred to Sprint 9)
- **Semantic Validator improvements** (deferred to Sprint 10)
- **Planner or adaptive-depth changes** (deferred to Sprint 11)
- **Kernel refactors or structural reorganization** (not in scope)
- **Planning, validation, memory logic, or prompt structure changes** (only observability, logging, and test coverage are in scope)

## Assumptions

- Logging will use the existing JSONL format established in Sprint 1, extended with new fields for phase awareness and correlation IDs
- Error models will extend the existing exception hierarchy in `aeon/exceptions.py` with structured error records
- Test coverage measurement will use standard Python coverage tools (pytest-cov)
- Logging will remain file-based (JSONL files) as established in Sprint 1; no external monitoring integrations
- Phase context propagation refers to orchestration state between phases, not memory subsystem integration
- TTL boundary tests will focus on single-pass execution only; adaptive depth testing is deferred to Sprint 11
- Deterministic convergence tests will use simple, repeatable tasks that don't require memory or advanced validation features

## Dependencies

- **Existing observability infrastructure**: Sprint 1 established JSONL logging and basic log entry structure
- **Existing exception hierarchy**: `aeon/exceptions.py` provides base exception classes
- **Existing phase orchestration**: `aeon/orchestration/phases.py` provides phase transition logic
- **Existing test infrastructure**: pytest and coverage tools are already configured

## Notes

- This sprint establishes the diagnostic substrate for all subsequent work. Observability improvements must not alter core reasoning logic.
- Error logging must capture sufficient context to enable diagnosis without requiring code inspection or additional debugging tools.
- Test coverage expansion must focus on deterministic tests that validate system behavior without relying on future features.
- Performance constraints ensure that observability improvements do not introduce regressions or reduce system determinism.

