# Data Model: Phase Transition Stabilization & Deterministic Context Propagation

**Date**: 2025-12-05  
**Feature**: Phase Transition Stabilization & Deterministic Context Propagation  
**Phase**: 1 - Design

## Overview

This document defines the data models and entities for explicit phase transition contracts, deterministic context propagation, TTL boundary behavior, ExecutionPass consistency, and phase boundary logging. These entities extend the existing orchestration and observability infrastructure.

## Phase Transition Entities

### PhaseTransitionContract

An explicit contract defining input requirements, output guarantees, invariants, and failure modes for a phase transition (A→B, B→C, C→D, D→A/B).

**Fields**:
- `transition_name` (enum, required): Transition identifier (A→B, B→C, C→D, D→A/B)
- `required_inputs` (dict, required): Field name → validation rule mapping for required inputs
- `guaranteed_outputs` (dict, required): Field name → validation rule mapping for guaranteed outputs
- `invariants` (list of strings, required): Invariant descriptions that must hold during transition
- `failure_conditions` (list of dicts, required): Failure condition → retryability classification mapping

**Validation Rules**:
- transition_name must be one of: "A→B", "B→C", "C→D", "D→A/B"
- required_inputs must be non-empty dict
- guaranteed_outputs must be non-empty dict
- invariants must be non-empty list
- failure_conditions must be non-empty list
- Each failure condition must have: `condition` (string), `retryable` (boolean), `error_code` (string)

**Failure Condition Format**:
- `condition`: Human-readable description of failure condition
- `retryable`: Boolean indicating if condition is retryable
- `error_code`: Error code in format "AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>"

**Contract Examples**:
- A→B: Required inputs: `task_profile` (TaskProfile), `initial_plan` (Plan), `ttl > 0` (int). Guaranteed outputs: `refined_plan` (Plan). Failure conditions: incomplete profile (non-retryable, AEON.PHASE_TRANSITION.A_B.001), malformed plan JSON (retryable, AEON.PHASE_TRANSITION.A_B.002), malformed plan structure (non-retryable, AEON.PHASE_TRANSITION.A_B.003).
- B→C: Required inputs: `refined_plan` (Plan with valid step fragments). Guaranteed outputs: `ExecutionPass` with `execution_results` (list). Failure conditions: missing steps (non-retryable, AEON.PHASE_TRANSITION.B_C.001), invalid plan fragments missing required fields (retryable, AEON.PHASE_TRANSITION.B_C.002), invalid plan fragments structural invalidity (non-retryable, AEON.PHASE_TRANSITION.B_C.003).

**Usage Pattern**:
```python
contract_a_b = PhaseTransitionContract(
    transition_name="A→B",
    required_inputs={
        "task_profile": lambda x: isinstance(x, TaskProfile),
        "initial_plan": lambda x: isinstance(x, Plan),
        "ttl": lambda x: isinstance(x, int) and x > 0,
    },
    guaranteed_outputs={
        "refined_plan": lambda x: isinstance(x, Plan),
    },
    invariants=[
        "correlation_id must be passed unchanged",
        "execution_start_timestamp must be passed unchanged",
    ],
    failure_conditions=[
        {
            "condition": "incomplete profile",
            "retryable": False,
            "error_code": "AEON.PHASE_TRANSITION.A_B.001",
        },
        {
            "condition": "malformed plan JSON",
            "retryable": True,
            "error_code": "AEON.PHASE_TRANSITION.A_B.002",
        },
    ],
)
```

**Relationships**:
- Validated before phase transitions
- Referenced in phase transition error logs
- Used for contract testing

### ContextPropagationSpecification

A structured specification defining, for each phase (A, B, C, D), what fields must be constructed before phase entry (must-have), what fields must be passed unchanged between phases (must-pass-unchanged), and what fields may be produced/modified only by specific phases (may-modify).

**Fields**:
- `phase` (enum, required): Phase identifier (A, B, C, D)
- `must_have_fields` (list of strings, required): Required fields before phase entry
- `must_pass_unchanged_fields` (list of strings, required): Fields that must be identical across phases
- `may_modify_fields` (list of strings, required): Fields that may be produced/modified by this phase

**Validation Rules**:
- phase must be one of: "A", "B", "C", "D"
- must_have_fields must be non-empty list
- must_pass_unchanged_fields must be non-empty list (at minimum: correlation_id, execution_start_timestamp)
- may_modify_fields may be empty list (for Phase A which produces initial context)

**Field Categories**:
- `must_have_fields`: Fields required before phase entry (e.g., request, task_profile, plan state, pass_number, phase, ttl_remaining, correlation_id, execution_start_timestamp)
- `must_pass_unchanged_fields`: Fields that must be identical across all phases (e.g., correlation_id, execution_start_timestamp)
- `may_modify_fields`: Fields that may be produced/modified by this phase (e.g., task_profile, refined_plan, execution_results, evaluation_results, ttl_remaining)

**Specification Examples**:
- Phase A: Must-have: `request`, `pass_number=0`, `phase="A"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`. Must-pass-unchanged: `correlation_id`, `execution_start_timestamp`. May-modify: None (Phase A produces initial context).
- Phase B: Must-have: `request`, `task_profile`, `initial_plan` goal and step metadata, `pass_number=0`, `phase="B"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`. Must-pass-unchanged: `correlation_id`, `execution_start_timestamp`. May-modify: `refined_plan` (Phase B produces refined plan).

**Usage Pattern**:
```python
spec_phase_a = ContextPropagationSpecification(
    phase="A",
    must_have_fields=[
        "request",
        "pass_number",
        "phase",
        "ttl_remaining",
        "correlation_id",
        "execution_start_timestamp",
    ],
    must_pass_unchanged_fields=[
        "correlation_id",
        "execution_start_timestamp",
    ],
    may_modify_fields=[],
)
```

**Relationships**:
- Validated before LLM calls
- Referenced in context propagation error logs
- Used for context validation testing

## TTL Boundary Behavior Specification

A specification defining TTL decrement timing, expiration detection, and boundary conditions.

**Fields**:
- `decrement_timing` (enum, required): When TTL decrements (once_per_cycle)
- `check_timing` (list of enums, required): When TTL is checked (before_phase_entry, after_llm_call)
- `boundary_conditions` (dict, required): Behavior at TTL boundaries (ttl_1, ttl_0_phase_boundary, ttl_0_mid_phase)

**Validation Rules**:
- decrement_timing must be: "once_per_cycle" (TTL decrements once per complete cycle A→B→C→D)
- check_timing must include: "before_phase_entry", "after_llm_call"
- boundary_conditions must define behavior for: ttl_1, ttl_0_phase_boundary, ttl_0_mid_phase

**Boundary Conditions**:
- `ttl_1`: Allow cycle to complete, then decrement to 0
- `ttl_0_phase_boundary`: Generate TTLExpirationResponse with `expiration_type="phase_boundary"`, abort execution
- `ttl_0_mid_phase`: Generate TTLExpirationResponse with `expiration_type="mid_phase"`, abort execution

**Usage Pattern**:
```python
ttl_spec = TTLBoundarySpecification(
    decrement_timing="once_per_cycle",
    check_timing=["before_phase_entry", "after_llm_call"],
    boundary_conditions={
        "ttl_1": "allow_cycle_complete",
        "ttl_0_phase_boundary": "generate_expiration_response_abort",
        "ttl_0_mid_phase": "generate_expiration_response_abort",
    },
)
```

**Relationships**:
- Used by TTLStrategy for expiration detection
- Referenced in TTL boundary tests
- Used for TTL behavior verification

## ExecutionPass Consistency Requirements

Extended requirements for ExecutionPass consistency across the loop (extending existing ExecutionPass model from `aeon/kernel/state.py`).

**Required Fields Before Phase Entry**:
- `pass_number` (int, required): Sequential identifier (0 for initial plan, 1-N for execution passes)
- `phase` (enum, required): Current phase (A, B, C, D)
- `plan_state` (dict, required): Snapshot of plan at pass start (JSON-serializable)
- `ttl_remaining` (int, required): TTL cycles remaining (>= 0)
- `timing_information.start_time` (string, required): ISO 8601 timestamp of pass start

**Required Fields After Phase Exit**:
- `execution_results` (list, required if Phase C): Step outputs and tool results (JSON-serializable)
- `evaluation_results` (dict, required if Phase C): Convergence assessment and semantic validation report (JSON-serializable)
- `refinement_changes` (list, required if Phase C refinement occurred): Plan/step modifications (JSON-serializable)
- `timing_information.end_time` (string, required): ISO 8601 timestamp of pass end
- `timing_information.duration` (float, required): Duration in seconds

**Invariants**:
- `execution_results` contain step outputs and status
- `evaluation_results` contain convergence assessment and validation report
- No conflicts between execution_results and evaluation_results
- Refinement_changes are correctly applied to plan_state
- TTL decrements exactly once per cycle (A→B→C→D)

**Validation Rules**:
- All required fields must be present and non-null before phase entry
- All required fields must be present and non-null after phase exit
- Invariants must hold after phase exit
- ExecutionPass must remain consistent across the loop

**Usage Pattern**:
```python
# Before phase entry
execution_pass = ExecutionPass(
    pass_number=0,
    phase="A",
    plan_state=plan.model_dump(),
    ttl_remaining=10,
    timing_information={"start_time": datetime.now().isoformat()},
)

# After phase exit
execution_pass.timing_information["end_time"] = datetime.now().isoformat()
execution_pass.timing_information["duration"] = (
    datetime.fromisoformat(execution_pass.timing_information["end_time"])
    - datetime.fromisoformat(execution_pass.timing_information["start_time"])
).total_seconds()
```

**Relationships**:
- Extends existing ExecutionPass model from `aeon/kernel/state.py`
- Validated before/after phase transitions
- Referenced in ExecutionPass consistency tests

## Phase Boundary Logging Models

Extended logging models for phase boundary events (extending existing LogEntry model from Sprint 5).

### PhaseEntryLog

A log entry for phase entry events.

**Fields**:
- `event` (enum, required): "phase_entry"
- `phase` (enum, required): Current phase (A, B, C, D)
- `correlation_id` (string, required): Correlation ID linking events
- `pass_number` (int, required): Pass number in multi-pass execution
- `timestamp` (string, required): ISO 8601 timestamp of phase entry

**Validation Rules**:
- event must be "phase_entry"
- phase must be one of: "A", "B", "C", "D"
- correlation_id must be present and non-empty
- pass_number must be >= 0
- timestamp must be valid ISO 8601 format

### PhaseExitLog

A log entry for phase exit events.

**Fields**:
- `event` (enum, required): "phase_exit"
- `phase` (enum, required): Current phase (A, B, C, D)
- `correlation_id` (string, required): Correlation ID linking events
- `pass_number` (int, required): Pass number in multi-pass execution
- `duration` (float, required): Duration in seconds
- `outcome` (enum, required): Outcome (success, failure)
- `timestamp` (string, required): ISO 8601 timestamp of phase exit

**Validation Rules**:
- event must be "phase_exit"
- phase must be one of: "A", "B", "C", "D"
- correlation_id must be present and non-empty
- pass_number must be >= 0
- duration must be >= 0
- outcome must be one of: "success", "failure"
- timestamp must be valid ISO 8601 format

### StateSnapshotLog

A log entry for deterministic state snapshots at phase boundaries.

**Fields**:
- `event` (enum, required): "state_snapshot"
- `correlation_id` (string, required): Correlation ID linking events
- `phase` (enum, required): Current phase (A, B, C, D)
- `pass_number` (int, required): Pass number in multi-pass execution
- `plan_state` (dict, required): Snapshot of plan state (JSON-serializable)
- `ttl_remaining` (int, required): TTL cycles remaining
- `phase_state` (dict, required): Snapshot of phase state (JSON-serializable)
- `snapshot_type` (enum, required): Snapshot type (before_transition, after_transition)
- `timestamp` (string, required): ISO 8601 timestamp of snapshot

**Validation Rules**:
- event must be "state_snapshot"
- correlation_id must be present and non-empty
- phase must be one of: "A", "B", "C", "D"
- pass_number must be >= 0
- plan_state must be JSON-serializable
- ttl_remaining must be >= 0
- phase_state must be JSON-serializable
- snapshot_type must be one of: "before_transition", "after_transition"
- timestamp must be valid ISO 8601 format

### TTLSnapshotLog

A log entry for TTL snapshots at phase boundaries.

**Fields**:
- `event` (enum, required): "ttl_snapshot"
- `correlation_id` (string, required): Correlation ID linking events
- `phase` (enum, required): Current phase (A, B, C, D)
- `pass_number` (int, required): Pass number in multi-pass execution
- `ttl_before` (int, required): TTL before phase entry
- `ttl_after` (int, required): TTL after phase exit
- `ttl_at_boundary` (int, required): TTL at phase boundary
- `timestamp` (string, required): ISO 8601 timestamp of snapshot

**Validation Rules**:
- event must be "ttl_snapshot"
- correlation_id must be present and non-empty
- phase must be one of: "A", "B", "C", "D"
- pass_number must be >= 0
- ttl_before must be >= 0
- ttl_after must be >= 0
- ttl_at_boundary must be >= 0
- timestamp must be valid ISO 8601 format

### PhaseTransitionErrorLog

A log entry for phase transition errors.

**Fields**:
- `event` (enum, required): "phase_transition_error"
- `correlation_id` (string, required): Correlation ID linking events
- `phase` (enum, required): Current phase (A, B, C, D)
- `pass_number` (int, required): Pass number in multi-pass execution
- `error_code` (string, required): Error code in format "AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>"
- `severity` (enum, required): Severity level (CRITICAL, ERROR, WARNING, INFO)
- `affected_component` (string, required): Component where error occurred
- `failure_condition` (string, required): Description of failure condition
- `retryable` (boolean, required): Whether error is retryable
- `timestamp` (string, required): ISO 8601 timestamp of error

**Validation Rules**:
- event must be "phase_transition_error"
- correlation_id must be present and non-empty
- phase must be one of: "A", "B", "C", "D"
- pass_number must be >= 0
- error_code must match pattern "AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>"
- severity must be one of: CRITICAL, ERROR, WARNING, INFO
- affected_component must be non-empty string
- failure_condition must be non-empty string
- timestamp must be valid ISO 8601 format

**Relationships**:
- Extends existing LogEntry model from Sprint 5
- Referenced in phase boundary logging tests
- Used for phase transition debugging

## Entity Relationships Diagram

```
PhaseTransitionContract
├── validated by → Phase transition validation functions
└── referenced by → Phase transition error logs

ContextPropagationSpecification
├── validated by → Context validation functions
└── referenced by → Context propagation error logs

TTLBoundarySpecification
├── used by → TTLStrategy
└── referenced by → TTL boundary tests

ExecutionPass (extended)
├── validated by → ExecutionPass consistency validation
└── referenced by → Phase transition contracts

PhaseEntryLog / PhaseExitLog / StateSnapshotLog / TTLSnapshotLog / PhaseTransitionErrorLog
├── extends → LogEntry (Sprint 5)
└── written by → JSONLLogger (Sprint 5)
```

