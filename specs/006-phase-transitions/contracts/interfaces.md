# Interface Contracts: Phase Transition Stabilization & Deterministic Context Propagation

**Date**: 2025-12-05  
**Feature**: Phase Transition Stabilization & Deterministic Context Propagation  
**Phase**: 1 - Design

## Overview

This document defines the interface contracts for explicit phase transition contracts, deterministic context propagation, TTL boundary behavior, ExecutionPass consistency, and phase boundary logging. These interfaces extend the existing orchestration and observability infrastructure.

## Interface Design Principles

1. **Explicit Contracts**: All phase transitions use explicit contracts with input requirements, output guarantees, invariants, and failure modes
2. **Deterministic**: All operations are deterministic for identical inputs
3. **Testable**: All contracts are testable and verifiable
4. **Non-Blocking**: Logging operations are non-blocking and fail silently
5. **Backward Compatible**: Existing interfaces remain functional

## Phase Transition Contract Interfaces

**Module**: `aeon.orchestration.phases`

**Purpose**: Provide explicit phase transition contracts with validation and error handling.

### validate_phase_transition_contract

**Signature**:
```python
def validate_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    contract: PhaseTransitionContract
) -> Tuple[bool, Optional[str]]:
    """
    Validate phase transition inputs against contract.
    
    Args:
        transition_name: Transition identifier
        inputs: Input dictionary to validate
        contract: Phase transition contract
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Behavior:
        - Validates all required_inputs are present and match validation rules
        - Returns (True, None) if valid
        - Returns (False, error_message) if invalid
    """
```

**Error Handling**:
- Returns (False, error_message) for invalid inputs
- Never raises exceptions (validation only)

### enforce_phase_transition_contract

**Signature**:
```python
def enforce_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    contract: PhaseTransitionContract
) -> Tuple[bool, Optional[str], Optional[PhaseTransitionError]]:
    """
    Enforce phase transition contract (validate inputs and outputs).
    
    Args:
        transition_name: Transition identifier
        inputs: Input dictionary
        outputs: Output dictionary
        contract: Phase transition contract
    
    Returns:
        Tuple of (success, error_message, phase_transition_error)
    
    Behavior:
        - Validates inputs against required_inputs
        - Validates outputs against guaranteed_outputs
        - Checks invariants
        - Returns (True, None, None) if contract satisfied
        - Returns (False, error_message, PhaseTransitionError) if contract violated
    """
```

**Error Handling**:
- Returns (False, error_message, PhaseTransitionError) for contract violations
- PhaseTransitionError contains error_code, severity, affected_component, failure_condition

### get_phase_transition_contract

**Signature**:
```python
def get_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"]
) -> PhaseTransitionContract:
    """
    Get phase transition contract for a transition.
    
    Args:
        transition_name: Transition identifier
    
    Returns:
        Phase transition contract
    
    Behavior:
        - Returns contract constant for transition
        - Contracts are defined as constants in orchestration/phases.py
    """
```

**Error Handling**:
- Raises ValueError if transition_name is invalid

## Context Propagation Interfaces

**Module**: `aeon.orchestration.phases`

**Purpose**: Provide context propagation validation and specification.

### validate_context_propagation

**Signature**:
```python
def validate_context_propagation(
    phase: Literal["A", "B", "C", "D"],
    context: Dict[str, Any],
    specification: ContextPropagationSpecification
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate context against propagation specification.
    
    Args:
        phase: Phase identifier
        context: Context dictionary to validate
        specification: Context propagation specification
    
    Returns:
        Tuple of (is_valid, error_message, missing_fields)
    
    Behavior:
        - Validates all must_have_fields are present and non-null
        - Validates must_pass_unchanged_fields are present
        - Returns (True, None, []) if valid
        - Returns (False, error_message, missing_fields) if invalid
    """
```

**Error Handling**:
- Returns (False, error_message, missing_fields) for invalid context
- Never raises exceptions (validation only)

### get_context_propagation_specification

**Signature**:
```python
def get_context_propagation_specification(
    phase: Literal["A", "B", "C", "D"]
) -> ContextPropagationSpecification:
    """
    Get context propagation specification for a phase.
    
    Args:
        phase: Phase identifier
    
    Returns:
        Context propagation specification
    
    Behavior:
        - Returns specification constant for phase
        - Specifications are defined as constants in orchestration/phases.py
    """
```

**Error Handling**:
- Raises ValueError if phase is invalid

### build_llm_context

**Signature**:
```python
def build_llm_context(
    phase: Literal["A", "B", "C", "D"],
    context: Dict[str, Any],
    specification: ContextPropagationSpecification
) -> Dict[str, Any]:
    """
    Build LLM context from context dictionary according to specification.
    
    Args:
        phase: Phase identifier
        context: Full context dictionary
        specification: Context propagation specification
    
    Returns:
        LLM context dictionary with only required fields
    
    Behavior:
        - Extracts only must_have_fields from context
        - Ensures all required fields are present and non-null
        - Returns minimal context for LLM calls
    """
```

**Error Handling**:
- Raises ValueError if required fields are missing or null

## TTL Boundary Interfaces

**Module**: `aeon.orchestration.ttl`

**Purpose**: Provide TTL boundary behavior and expiration detection.

### check_ttl_before_phase_entry

**Signature**:
```python
def check_ttl_before_phase_entry(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
    execution_pass: ExecutionPass
) -> Tuple[bool, Optional[TTLExpirationResponse]]:
    """
    Check TTL before phase entry.
    
    Args:
        ttl_remaining: TTL cycles remaining
        phase: Phase identifier
        execution_pass: Current execution pass
    
    Returns:
        Tuple of (can_proceed, ttl_expiration_response)
    
    Behavior:
        - If ttl_remaining > 0, returns (True, None)
        - If ttl_remaining == 0, returns (False, TTLExpirationResponse with expiration_type="phase_boundary")
    """
```

**Error Handling**:
- Returns (False, TTLExpirationResponse) if TTL expired
- Never raises exceptions

### check_ttl_after_llm_call

**Signature**:
```python
def check_ttl_after_llm_call(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
    execution_pass: ExecutionPass
) -> Tuple[bool, Optional[TTLExpirationResponse]]:
    """
    Check TTL after LLM call within phase.
    
    Args:
        ttl_remaining: TTL cycles remaining
        phase: Phase identifier
        execution_pass: Current execution pass
    
    Returns:
        Tuple of (can_proceed, ttl_expiration_response)
    
    Behavior:
        - If ttl_remaining > 0, returns (True, None)
        - If ttl_remaining == 0, returns (False, TTLExpirationResponse with expiration_type="mid_phase")
    """
```

**Error Handling**:
- Returns (False, TTLExpirationResponse) if TTL expired
- Never raises exceptions

### decrement_ttl_per_cycle

**Signature**:
```python
def decrement_ttl_per_cycle(
    ttl_remaining: int
) -> int:
    """
    Decrement TTL exactly once per cycle.
    
    Args:
        ttl_remaining: Current TTL cycles remaining
    
    Returns:
        Decremented TTL (ttl_remaining - 1)
    
    Behavior:
        - Decrements TTL by exactly 1
        - Called once per complete cycle (A→B→C→D)
        - Returns max(0, ttl_remaining - 1) to prevent negative values
    """
```

**Error Handling**:
- Returns 0 if ttl_remaining <= 0 (prevents negative values)
- Never raises exceptions

## Phase Boundary Logging Interfaces

**Module**: `aeon.observability.logger`

**Purpose**: Provide phase boundary logging (extending existing JSONLLogger interface).

### log_phase_entry

**Signature**:
```python
def log_phase_entry(
    phase: Literal["A", "B", "C", "D"],
    correlation_id: str,
    pass_number: int,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a phase entry event.
    
    Args:
        phase: Phase identifier
        correlation_id: Correlation ID for this execution
        pass_number: Pass number in multi-pass execution
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates PhaseEntryLog with event="phase_entry"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_phase_exit

**Signature**:
```python
def log_phase_exit(
    phase: Literal["A", "B", "C", "D"],
    correlation_id: str,
    pass_number: int,
    duration: float,
    outcome: Literal["success", "failure"],
    timestamp: Optional[str] = None
) -> None:
    """
    Log a phase exit event.
    
    Args:
        phase: Phase identifier
        correlation_id: Correlation ID for this execution
        pass_number: Pass number in multi-pass execution
        duration: Phase duration in seconds
        outcome: Phase outcome (success or failure)
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates PhaseExitLog with event="phase_exit"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_state_snapshot

**Signature**:
```python
def log_state_snapshot(
    correlation_id: str,
    phase: Literal["A", "B", "C", "D"],
    pass_number: int,
    plan_state: Dict[str, Any],
    ttl_remaining: int,
    phase_state: Dict[str, Any],
    snapshot_type: Literal["before_transition", "after_transition"],
    timestamp: Optional[str] = None
) -> None:
    """
    Log a deterministic state snapshot at phase boundary.
    
    Args:
        correlation_id: Correlation ID for this execution
        phase: Phase identifier
        pass_number: Pass number in multi-pass execution
        plan_state: Snapshot of plan state (JSON-serializable)
        ttl_remaining: TTL cycles remaining
        phase_state: Snapshot of phase state (JSON-serializable)
        snapshot_type: Snapshot type (before_transition or after_transition)
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates StateSnapshotLog with event="state_snapshot"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_ttl_snapshot

**Signature**:
```python
def log_ttl_snapshot(
    correlation_id: str,
    phase: Literal["A", "B", "C", "D"],
    pass_number: int,
    ttl_before: int,
    ttl_after: int,
    ttl_at_boundary: int,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a TTL snapshot at phase boundary.
    
    Args:
        correlation_id: Correlation ID for this execution
        phase: Phase identifier
        pass_number: Pass number in multi-pass execution
        ttl_before: TTL before phase entry
        ttl_after: TTL after phase exit
        ttl_at_boundary: TTL at phase boundary
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates TTLSnapshotLog with event="ttl_snapshot"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_phase_transition_error

**Signature**:
```python
def log_phase_transition_error(
    correlation_id: str,
    phase: Literal["A", "B", "C", "D"],
    pass_number: int,
    error_code: str,
    severity: Literal["CRITICAL", "ERROR", "WARNING", "INFO"],
    affected_component: str,
    failure_condition: str,
    retryable: bool,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a phase transition error.
    
    Args:
        correlation_id: Correlation ID for this execution
        phase: Phase identifier
        pass_number: Pass number in multi-pass execution
        error_code: Error code in format "AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>"
        severity: Severity level
        affected_component: Component where error occurred
        failure_condition: Description of failure condition
        retryable: Whether error is retryable
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates PhaseTransitionErrorLog with event="phase_transition_error"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

## Error Interfaces

**Module**: `aeon.exceptions`

**Purpose**: Provide phase transition error classes (extending existing exception hierarchy).

### PhaseTransitionError

**Signature**:
```python
class PhaseTransitionError(AeonError):
    """Raised when phase transition fails."""
    
    ERROR_CODE: str = "AEON.PHASE_TRANSITION.000"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR
    
    def __init__(
        self,
        transition_name: str,
        failure_condition: str,
        retryable: bool,
        message: Optional[str] = None
    ):
        """
        Initialize phase transition error.
        
        Args:
            transition_name: Transition identifier (A→B, B→C, C→D, D→A/B)
            failure_condition: Description of failure condition
            retryable: Whether error is retryable
            message: Optional error message
        """
```

**Error Handling**:
- Extends AeonError with phase transition-specific error codes
- Error codes follow format: "AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>"
- Retryable flag indicates if error can be retried

### ContextPropagationError

**Signature**:
```python
class ContextPropagationError(AeonError):
    """Raised when context propagation fails."""
    
    ERROR_CODE: str = "AEON.CONTEXT_PROPAGATION.000"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR
    
    def __init__(
        self,
        phase: str,
        missing_fields: List[str],
        message: Optional[str] = None
    ):
        """
        Initialize context propagation error.
        
        Args:
            phase: Phase identifier (A, B, C, D)
            missing_fields: List of missing required fields
            message: Optional error message
        """
```

**Error Handling**:
- Extends AeonError with context propagation-specific error codes
- Error codes follow format: "AEON.CONTEXT_PROPAGATION.<PHASE>.<CODE>"
- Always non-retryable (context propagation failure is permanent)

## ExecutionPass Consistency Interfaces

**Module**: `aeon.kernel.state`

**Purpose**: Provide ExecutionPass consistency validation (extending existing ExecutionPass model).

### validate_execution_pass_before_phase

**Signature**:
```python
def validate_execution_pass_before_phase(
    execution_pass: ExecutionPass,
    phase: Literal["A", "B", "C", "D"]
) -> Tuple[bool, Optional[str]]:
    """
    Validate ExecutionPass required fields before phase entry.
    
    Args:
        execution_pass: Execution pass to validate
        phase: Phase identifier
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Behavior:
        - Validates required fields: pass_number, phase, plan_state, ttl_remaining, timing_information.start_time
        - Returns (True, None) if valid
        - Returns (False, error_message) if invalid
    """
```

**Error Handling**:
- Returns (False, error_message) for invalid ExecutionPass
- Never raises exceptions (validation only)

### validate_execution_pass_after_phase

**Signature**:
```python
def validate_execution_pass_after_phase(
    execution_pass: ExecutionPass,
    phase: Literal["A", "B", "C", "D"]
) -> Tuple[bool, Optional[str]]:
    """
    Validate ExecutionPass required fields after phase exit.
    
    Args:
        execution_pass: Execution pass to validate
        phase: Phase identifier
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Behavior:
        - Validates required fields: execution_results (if Phase C), evaluation_results (if Phase C), refinement_changes (if Phase C refinement occurred), timing_information.end_time, timing_information.duration
        - Validates invariants: execution_results contain step outputs, evaluation_results contain convergence assessment and validation report, no conflicts between results
        - Returns (True, None) if valid
        - Returns (False, error_message) if invalid
    """
```

**Error Handling**:
- Returns (False, error_message) for invalid ExecutionPass
- Never raises exceptions (validation only)

## Interface Usage Patterns

### Phase Transition with Contract Validation

```python
# Get contract
contract = get_phase_transition_contract("A→B")

# Validate inputs
is_valid, error_message = validate_phase_transition_contract(
    transition_name="A→B",
    inputs={"task_profile": task_profile, "initial_plan": plan, "ttl": ttl},
    contract=contract
)

if not is_valid:
    # Handle validation error
    error = PhaseTransitionError(
        transition_name="A→B",
        failure_condition=error_message,
        retryable=False
    )
    raise error

# Execute phase transition
outputs = phase_b_initial_plan_refinement(...)

# Enforce contract
success, error_message, phase_error = enforce_phase_transition_contract(
    transition_name="A→B",
    inputs={"task_profile": task_profile, "initial_plan": plan, "ttl": ttl},
    outputs={"refined_plan": outputs},
    contract=contract
)

if not success:
    # Handle contract violation
    raise phase_error
```

### Context Propagation with Validation

```python
# Get specification
spec = get_context_propagation_specification("B")

# Validate context
is_valid, error_message, missing_fields = validate_context_propagation(
    phase="B",
    context=full_context,
    specification=spec
)

if not is_valid:
    # Handle validation error
    error = ContextPropagationError(
        phase="B",
        missing_fields=missing_fields
    )
    raise error

# Build LLM context
llm_context = build_llm_context(
    phase="B",
    context=full_context,
    specification=spec
)

# Make LLM call with validated context
llm_response = llm_adapter.call(llm_context)
```

### TTL Boundary Checking

```python
# Check TTL before phase entry
can_proceed, expiration_response = check_ttl_before_phase_entry(
    ttl_remaining=ttl,
    phase="B",
    execution_pass=execution_pass
)

if not can_proceed:
    # Handle TTL expiration
    raise TTLExpiredError(f"TTL expired at phase boundary: {expiration_response}")

# Execute phase
result = phase_b_initial_plan_refinement(...)

# Check TTL after LLM call
can_proceed, expiration_response = check_ttl_after_llm_call(
    ttl_remaining=ttl,
    phase="B",
    execution_pass=execution_pass
)

if not can_proceed:
    # Handle TTL expiration
    raise TTLExpiredError(f"TTL expired mid-phase: {expiration_response}")
```

### Phase Boundary Logging

```python
# Log phase entry
logger.log_phase_entry(
    phase="B",
    correlation_id=correlation_id,
    pass_number=pass_number
)

# Log state snapshot before transition
logger.log_state_snapshot(
    correlation_id=correlation_id,
    phase="B",
    pass_number=pass_number,
    plan_state=plan.model_dump(),
    ttl_remaining=ttl,
    phase_state=phase_state,
    snapshot_type="before_transition"
)

# Execute phase
result = phase_b_initial_plan_refinement(...)

# Log TTL snapshot
logger.log_ttl_snapshot(
    correlation_id=correlation_id,
    phase="B",
    pass_number=pass_number,
    ttl_before=ttl_before,
    ttl_after=ttl_after,
    ttl_at_boundary=ttl_at_boundary
)

# Log phase exit
logger.log_phase_exit(
    phase="B",
    correlation_id=correlation_id,
    pass_number=pass_number,
    duration=duration,
    outcome="success"
)
```

