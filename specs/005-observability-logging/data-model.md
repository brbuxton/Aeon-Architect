# Data Model: Observability, Logging, and Test Coverage

**Date**: 2025-01-27  
**Feature**: Observability, Logging, and Test Coverage  
**Phase**: 1 - Design

## Overview

This document defines the data models and entities for phase-aware structured logging, actionable error logging, and enhanced debug visibility. These entities extend the existing observability infrastructure established in Sprint 1.

## Observability Entities

### CorrelationID

A unique identifier that links all log entries for a single execution cycle, enabling trace reconstruction across phases and passes.

**Fields**:
- `value` (string, required): UUIDv5 string representation of the correlation ID

**Validation Rules**:
- Must be a valid UUIDv5 format
- Must be deterministic (same inputs produce same UUID)
- Must be unique across executions (timestamp component ensures uniqueness)
- Must persist across all phases and passes for a single execution

**Generation**:
- Generated once at execution start using deterministic UUIDv5
- Namespace: Fixed UUID constant (e.g., `6ba7b810-9dad-11d1-80b4-00c04fd430c8`)
- Name: `f"{execution_start_timestamp}:{request_hash}"` where request_hash is SHA256 hash of request string
- Fallback: If UUIDv5 generation fails, use `f"aeon-{execution_start_timestamp}-{request_hash[:8]}"`

**Usage Pattern**:
```python
correlation_id = generate_correlation_id(execution_start_timestamp, request)
logger.log_phase_entry(phase="A", correlation_id=correlation_id, ...)
```

**Relationships**:
- Included in all LogEntry instances for a single execution
- Enables correlation of events across phases and passes

### ErrorRecord

A structured error record containing error code, severity level, message, affected component, and optional context.

**Fields**:
- `code` (string, required): Error code in format "AEON.<COMPONENT>.<CODE>" (e.g., "AEON.REFINEMENT.001")
- `severity` (enum, required): Severity level (CRITICAL, ERROR, WARNING, INFO)
- `message` (string, required): Human-readable error message
- `affected_component` (string, required): Component where error occurred (e.g., "refinement", "execution", "validation")
- `context` (dict, optional): Additional context for diagnosis (step_id, tool_name, attempted_action, etc.)
- `stack_trace` (string, optional): Stack trace if available (for debugging)

**Validation Rules**:
- code must match pattern "AEON.<COMPONENT>.<CODE>"
- severity must be one of: CRITICAL, ERROR, WARNING, INFO
- message must be non-empty string
- affected_component must be non-empty string
- context is optional but recommended for diagnosis

**Error Code Format**:
- Component names: REFINEMENT, EXECUTION, VALIDATION, PHASE, PLAN, TOOL, MEMORY, LLM, SUPERVISOR
- Code numbers: 001, 002, 003, ... (sequential within component)
- Examples:
  - `AEON.REFINEMENT.001`: Refinement action application failed
  - `AEON.EXECUTION.002`: Step execution failed
  - `AEON.VALIDATION.003`: Validation check failed
  - `AEON.PHASE.004`: Phase transition failed

**Usage Pattern**:
```python
error_record = ErrorRecord(
    code="AEON.REFINEMENT.001",
    severity="ERROR",
    message="Failed to apply refinement action: invalid step_id",
    affected_component="refinement",
    context={"step_id": "step_1", "attempted_action": "modify_step"},
)
logger.log_error(correlation_id=correlation_id, error=error_record)
```

**Relationships**:
- Created from exception instances via `exception.to_error_record()`
- Included in LogEntry instances when errors occur
- Referenced in error_recovery events

### LogEntry (Extended)

A JSONL record of an orchestration event (extended from Sprint 1 LogEntry with phase-aware fields).

**Fields** (existing from Sprint 1):
- `step_number` (integer, optional): Sequential cycle identifier (for cycle events)
- `plan_state` (dict, optional): Snapshot of plan at cycle start (for cycle events)
- `llm_output` (dict, optional): Raw LLM response (for cycle events)
- `supervisor_actions` (array, optional): Supervisor repairs in this cycle (for cycle events)
- `tool_calls` (array, optional): Tool invocations in this cycle (for cycle events)
- `ttl_remaining` (integer, optional): Cycles left before expiration (for cycle events)
- `errors` (array, optional): Errors in this cycle (for cycle events)
- `timestamp` (string, required): ISO 8601 timestamp of the event

**Fields** (new for phase-aware logging):
- `event` (enum, required): Event type (phase_entry, phase_exit, state_transition, refinement_outcome, evaluation_outcome, error_recovery, cycle)
- `correlation_id` (string, required): Correlation ID linking events for a single execution
- `phase` (enum, optional): Current phase (A, B, C, D) - required for phase events
- `pass_number` (integer, optional): Pass number in multi-pass execution
- `duration` (float, optional): Duration in seconds (for phase_exit events)
- `outcome` (enum, optional): Outcome (success, failure) - for phase_exit events
- `component` (string, optional): Component name (for state_transition events)
- `before_state` (dict, optional): State snapshot before transition (for state_transition events)
- `after_state` (dict, optional): State snapshot after transition (for state_transition events)
- `transition_reason` (string, optional): Reason for state transition (for state_transition events)
- `evaluation_signals` (dict, optional): Evaluation signals summary (for refinement_outcome, evaluation_outcome events)
- `refinement_actions` (list, optional): Refinement actions applied (for refinement_outcome events)
- `before_plan_fragment` (PlanFragment, optional): Plan fragment before refinement (for refinement_outcome events)
- `after_plan_fragment` (PlanFragment, optional): Plan fragment after refinement (for refinement_outcome events)
- `convergence_assessment` (dict, optional): Convergence assessment summary (for evaluation_outcome events)
- `validation_report` (dict, optional): Validation report summary (for evaluation_outcome events)
- `original_error` (ErrorRecord, optional): Original error (for error_recovery events)
- `recovery_action` (string, optional): Recovery action attempted (for error_recovery events)
- `recovery_outcome` (enum, optional): Recovery outcome (success, failure) - for error_recovery events

**Validation Rules**:
- event must be one of the enum values
- correlation_id must be present for all events
- phase must be present for phase_entry, phase_exit events
- duration and outcome must be present for phase_exit events
- component, before_state, after_state, transition_reason must be present for state_transition events
- evaluation_signals, refinement_actions, before_plan_fragment, after_plan_fragment must be present for refinement_outcome events
- convergence_assessment, validation_report must be present for evaluation_outcome events
- original_error, recovery_action, recovery_outcome must be present for error_recovery events
- timestamp must be valid ISO 8601 format

**Event Types**:
- `phase_entry`: Phase A/B/C/D entry event
- `phase_exit`: Phase A/B/C/D exit event
- `state_transition`: State change event (plan state, execution state, etc.)
- `refinement_outcome`: Plan refinement result event
- `evaluation_outcome`: Evaluation result event (convergence, validation)
- `error_recovery`: Error recovery attempt event
- `cycle`: Legacy cycle event (backward compatibility)

**Usage Pattern**:
```python
# Phase entry
logger.log_phase_entry(
    phase="A",
    correlation_id=correlation_id,
    timestamp=datetime.now().isoformat(),
)

# Phase exit
logger.log_phase_exit(
    phase="A",
    correlation_id=correlation_id,
    duration=1.23,
    outcome="success",
    timestamp=datetime.now().isoformat(),
)

# State transition
logger.log_state_transition(
    correlation_id=correlation_id,
    component="plan",
    before_state=plan_state_slice_before,
    after_state=plan_state_slice_after,
    transition_reason="refinement_applied",
    timestamp=datetime.now().isoformat(),
)
```

**Relationships**:
- Contains CorrelationID
- Contains ErrorRecord instances (for error events)
- Contains PlanFragment instances (for refinement events)
- Contains state slice instances (for state_transition events)

### PlanFragment

A plan fragment containing only changed steps (modified/added/removed) with step IDs, referencing unchanged steps by ID only.

**Fields**:
- `changed_steps` (array of PlanStep, required): Steps that were modified, added, or removed (full step data)
- `unchanged_step_ids` (array of string, required): Step IDs of unchanged steps (ID only, no full data)

**Validation Rules**:
- changed_steps must be array of valid PlanStep objects
- unchanged_step_ids must be array of valid step IDs
- Step IDs in changed_steps and unchanged_step_ids must not overlap
- All step IDs must reference valid steps in the plan

**Usage Pattern**:
```python
plan_fragment = PlanFragment(
    changed_steps=[
        PlanStep(step_id="step_1", description="Updated step", status="complete", ...),
        PlanStep(step_id="step_3", description="New step", status="pending", ...),
    ],
    unchanged_step_ids=["step_2", "step_4"],
)
logger.log_refinement_outcome(
    correlation_id=correlation_id,
    before_plan_fragment=before_fragment,
    after_plan_fragment=after_fragment,
    ...
)
```

**Relationships**:
- Used in refinement_outcome events
- Used in error logging (FR-013)
- References PlanStep objects (for changed steps)

### ConvergenceAssessmentSummary

A summary of convergence assessment results containing reason codes, scores, and converged boolean.

**Fields**:
- `converged` (boolean, required): Whether convergence was achieved
- `reason_codes` (array of string, required): Reason codes explaining convergence decision
- `scores` (dict, optional): Convergence scores (completeness, coherence, consistency)
- `pass_number` (integer, required): Pass number when assessment was made

**Validation Rules**:
- reason_codes must be non-empty array
- scores is optional but recommended
- pass_number must be >= 0

**Usage Pattern**:
```python
convergence_summary = ConvergenceAssessmentSummary(
    converged=True,
    reason_codes=["all_steps_complete", "validation_passed"],
    scores={"completeness": 1.0, "coherence": 0.95, "consistency": 1.0},
    pass_number=2,
)
```

**Relationships**:
- Included in evaluation_signals for refinement_outcome and evaluation_outcome events
- Referenced in convergence assessment logging (FR-022)

### ValidationIssuesSummary

A summary of validation issues containing issue counts by severity level and type.

**Fields**:
- `total_issues` (integer, required): Total number of validation issues
- `critical_count` (integer, required): Number of critical issues
- `error_count` (integer, required): Number of error-level issues
- `warning_count` (integer, required): Number of warning-level issues
- `info_count` (integer, required): Number of info-level issues
- `issues_by_type` (dict, optional): Issues grouped by type (e.g., {"missing_tool": 2, "invalid_schema": 1})

**Validation Rules**:
- total_issues must equal sum of critical_count + error_count + warning_count + info_count
- All counts must be >= 0
- issues_by_type is optional but recommended

**Usage Pattern**:
```python
validation_summary = ValidationIssuesSummary(
    total_issues=3,
    critical_count=0,
    error_count=2,
    warning_count=1,
    info_count=0,
    issues_by_type={"missing_tool": 2, "invalid_schema": 1},
)
```

**Relationships**:
- Included in evaluation_signals for refinement_outcome and evaluation_outcome events
- Referenced in validation error logging (FR-015)

### StateSlice

A minimal structured state slice relevant to a specific component, containing only fields needed for debugging that component's transitions.

**Base Fields** (all state slices):
- `component` (string, required): Component name (e.g., "plan", "execution", "refinement")
- `timestamp` (string, required): ISO 8601 timestamp of the state snapshot

**Component-Specific Slices**:

#### PlanStateSlice
- `plan_id` (string, optional): Plan identifier
- `current_step_id` (string, optional): Currently executing step ID
- `step_count` (integer, required): Total number of steps
- `steps_status_summary` (dict, required): Summary of step statuses (e.g., {"pending": 2, "running": 1, "complete": 3})

#### ExecutionStateSlice
- `current_step_id` (string, optional): Currently executing step ID
- `step_status` (enum, required): Current step status (pending, running, complete, failed)
- `tool_calls_count` (integer, required): Number of tool calls made
- `errors_count` (integer, required): Number of errors encountered

#### RefinementStateSlice
- `refinement_type` (string, required): Type of refinement (add_step, modify_step, remove_step)
- `changed_steps_count` (integer, required): Number of changed steps
- `added_steps_count` (integer, required): Number of added steps
- `removed_steps_count` (integer, required): Number of removed steps

**Validation Rules**:
- component must be non-empty string
- timestamp must be valid ISO 8601 format
- Component-specific fields must be present for that component type

**Usage Pattern**:
```python
plan_slice = PlanStateSlice(
    component="plan",
    timestamp=datetime.now().isoformat(),
    plan_id="plan_123",
    current_step_id="step_2",
    step_count=5,
    steps_status_summary={"pending": 2, "running": 1, "complete": 2},
)
logger.log_state_transition(
    correlation_id=correlation_id,
    component="plan",
    before_state=before_slice.model_dump(),
    after_state=after_slice.model_dump(),
    transition_reason="refinement_applied",
    ...
)
```

**Relationships**:
- Used in state_transition events
- Referenced in state transition logging (FR-005)

## Entity Relationships Diagram

```
CorrelationID
└── included in → LogEntry (all events for a single execution)

ErrorRecord
├── created from → Exception (via to_error_record())
└── included in → LogEntry (error events, error_recovery events)

LogEntry
├── contains → CorrelationID
├── contains → ErrorRecord (for error events)
├── contains → PlanFragment (for refinement events)
├── contains → StateSlice (for state_transition events)
└── contains → ConvergenceAssessmentSummary, ValidationIssuesSummary (for evaluation events)

PlanFragment
└── references → PlanStep (changed steps only)

ConvergenceAssessmentSummary
└── included in → LogEntry.evaluation_signals

ValidationIssuesSummary
└── included in → LogEntry.evaluation_signals

StateSlice
└── included in → LogEntry (before_state, after_state for state_transition events)
```

## Data Flow

1. **Correlation ID Generation**: Execution start → generate_correlation_id() → CorrelationID
2. **Phase Entry Logging**: Phase transition → logger.log_phase_entry() → LogEntry (event=phase_entry)
3. **State Transition Logging**: State change → create StateSlice → logger.log_state_transition() → LogEntry (event=state_transition)
4. **Error Logging**: Exception → exception.to_error_record() → ErrorRecord → logger.log_error() → LogEntry (with ErrorRecord)
5. **Refinement Logging**: Refinement outcome → create PlanFragment → logger.log_refinement_outcome() → LogEntry (event=refinement_outcome)
6. **Evaluation Logging**: Evaluation result → create ConvergenceAssessmentSummary, ValidationIssuesSummary → logger.log_evaluation_outcome() → LogEntry (event=evaluation_outcome)
7. **Error Recovery Logging**: Recovery attempt → logger.log_error_recovery() → LogEntry (event=error_recovery)
8. **Phase Exit Logging**: Phase completion → logger.log_phase_exit() → LogEntry (event=phase_exit)

## Backward Compatibility

The extended LogEntry model maintains backward compatibility with existing Sprint 1 log entries:

- Existing `format_entry()` method continues to work, creates entries with `event="cycle"`
- New phase-aware methods create entries with specific event types
- Optional fields allow gradual migration
- Existing log parsers can ignore new fields
- Schema remains valid JSONL format

