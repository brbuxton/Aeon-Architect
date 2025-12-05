# Quickstart: Phase Transition Stabilization & Deterministic Context Propagation

**Date**: 2025-12-05  
**Feature**: Phase Transition Stabilization & Deterministic Context Propagation  
**Phase**: 1 - Design

## Overview

This guide provides examples and patterns for using explicit phase transition contracts, deterministic context propagation, TTL boundary behavior, ExecutionPass consistency, and phase boundary logging. All examples extend the existing orchestration and observability infrastructure.

## Basic Usage

### Phase Transition with Contract Validation

```python
from aeon.orchestration.phases import (
    PhaseOrchestrator,
    get_phase_transition_contract,
    validate_phase_transition_contract,
    enforce_phase_transition_contract
)
from aeon.exceptions import PhaseTransitionError
from aeon.observability.logger import JSONLLogger

# Initialize components
orchestrator = PhaseOrchestrator()
logger = JSONLLogger(file_path=Path("execution.jsonl"))

# Get contract for A→B transition
contract = get_phase_transition_contract("A→B")

# Prepare inputs
inputs = {
    "task_profile": task_profile,
    "initial_plan": initial_plan,
    "ttl": ttl_remaining
}

# Validate inputs before transition
is_valid, error_message = validate_phase_transition_contract(
    transition_name="A→B",
    inputs=inputs,
    contract=contract
)

if not is_valid:
    # Handle validation error (non-retryable)
    error = PhaseTransitionError(
        transition_name="A→B",
        failure_condition=error_message,
        retryable=False
    )
    logger.log_phase_transition_error(
        correlation_id=correlation_id,
        phase="A",
        pass_number=pass_number,
        error_code=error.ERROR_CODE,
        severity=error.SEVERITY.value,
        affected_component="phase_transition",
        failure_condition=error_message,
        retryable=False
    )
    raise error

# Execute phase transition
refined_plan = orchestrator.phase_b_initial_plan_refinement(
    request=request,
    plan=initial_plan,
    task_profile=task_profile,
    ...
)

# Enforce contract (validate outputs)
outputs = {"refined_plan": refined_plan}
success, error_message, phase_error = enforce_phase_transition_contract(
    transition_name="A→B",
    inputs=inputs,
    outputs=outputs,
    contract=contract
)

if not success:
    # Handle contract violation
    logger.log_phase_transition_error(
        correlation_id=correlation_id,
        phase="B",
        pass_number=pass_number,
        error_code=phase_error.ERROR_CODE,
        severity=phase_error.SEVERITY.value,
        affected_component="phase_transition",
        failure_condition=error_message,
        retryable=phase_error.retryable
    )
    
    # Retry if retryable
    if phase_error.retryable:
        # Retry once
        refined_plan = orchestrator.phase_b_initial_plan_refinement(...)
        # Re-validate
        success, error_message, phase_error = enforce_phase_transition_contract(...)
        if not success:
            raise phase_error
    else:
        raise phase_error
```

### Context Propagation with Validation

```python
from aeon.orchestration.phases import (
    get_context_propagation_specification,
    validate_context_propagation,
    build_llm_context
)
from aeon.exceptions import ContextPropagationError

# Get specification for Phase B
spec = get_context_propagation_specification("B")

# Prepare full context
full_context = {
    "request": request,
    "task_profile": task_profile,
    "initial_plan": initial_plan,
    "pass_number": 0,
    "phase": "B",
    "ttl_remaining": ttl_remaining,
    "correlation_id": correlation_id,
    "execution_start_timestamp": execution_start_timestamp
}

# Validate context before LLM call
is_valid, error_message, missing_fields = validate_context_propagation(
    phase="B",
    context=full_context,
    specification=spec
)

if not is_valid:
    # Handle validation error (non-retryable)
    error = ContextPropagationError(
        phase="B",
        missing_fields=missing_fields
    )
    raise error

# Build minimal LLM context
llm_context = build_llm_context(
    phase="B",
    context=full_context,
    specification=spec
)

# Make LLM call with validated context
llm_response = llm_adapter.call(
    prompt=build_prompt(llm_context),
    ...
)
```

### TTL Boundary Checking

```python
from aeon.orchestration.ttl import (
    check_ttl_before_phase_entry,
    check_ttl_after_llm_call,
    decrement_ttl_per_cycle
)
from aeon.exceptions import TTLExpiredError
from aeon.kernel.state import TTLExpirationResponse

# Check TTL before phase entry
can_proceed, expiration_response = check_ttl_before_phase_entry(
    ttl_remaining=ttl_remaining,
    phase="B",
    execution_pass=execution_pass
)

if not can_proceed:
    # Handle TTL expiration at phase boundary (non-retryable)
    logger.log_phase_transition_error(
        correlation_id=correlation_id,
        phase="B",
        pass_number=pass_number,
        error_code="AEON.PHASE_TRANSITION.TTL_EXPIRED",
        severity="CRITICAL",
        affected_component="ttl",
        failure_condition="TTL expired at phase boundary",
        retryable=False
    )
    raise TTLExpiredError(f"TTL expired at phase boundary: {expiration_response}")

# Execute phase
result = orchestrator.phase_b_initial_plan_refinement(...)

# Check TTL after LLM call
can_proceed, expiration_response = check_ttl_after_llm_call(
    ttl_remaining=ttl_remaining,
    phase="B",
    execution_pass=execution_pass
)

if not can_proceed:
    # Handle TTL expiration mid-phase (non-retryable)
    logger.log_phase_transition_error(
        correlation_id=correlation_id,
        phase="B",
        pass_number=pass_number,
        error_code="AEON.PHASE_TRANSITION.TTL_EXPIRED",
        severity="CRITICAL",
        affected_component="ttl",
        failure_condition="TTL expired mid-phase",
        retryable=False
    )
    raise TTLExpiredError(f"TTL expired mid-phase: {expiration_response}")

# Decrement TTL once per cycle (after complete cycle A→B→C→D)
if phase == "D" and cycle_complete:
    ttl_remaining = decrement_ttl_per_cycle(ttl_remaining)
```

### Phase Boundary Logging

```python
from aeon.observability.logger import JSONLLogger
from datetime import datetime

# Initialize logger
logger = JSONLLogger(file_path=Path("execution.jsonl"))

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
    ttl_remaining=ttl_remaining,
    phase_state=phase_state,
    snapshot_type="before_transition"
)

# Log TTL snapshot
logger.log_ttl_snapshot(
    correlation_id=correlation_id,
    phase="B",
    pass_number=pass_number,
    ttl_before=ttl_before,
    ttl_after=ttl_after,
    ttl_at_boundary=ttl_at_boundary
)

# Execute phase
start_time = datetime.now()
result = orchestrator.phase_b_initial_plan_refinement(...)
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

# Log state snapshot after transition
logger.log_state_snapshot(
    correlation_id=correlation_id,
    phase="B",
    pass_number=pass_number,
    plan_state=plan.model_dump(),
    ttl_remaining=ttl_remaining,
    phase_state=phase_state,
    snapshot_type="after_transition"
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

### ExecutionPass Consistency

```python
from aeon.kernel.state import ExecutionPass, validate_execution_pass_before_phase, validate_execution_pass_after_phase
from datetime import datetime

# Create ExecutionPass before phase entry
execution_pass = ExecutionPass(
    pass_number=0,
    phase="A",
    plan_state=plan.model_dump(),
    ttl_remaining=10,
    timing_information={"start_time": datetime.now().isoformat()}
)

# Validate before phase entry
is_valid, error_message = validate_execution_pass_before_phase(
    execution_pass=execution_pass,
    phase="A"
)

if not is_valid:
    raise ValueError(f"Invalid ExecutionPass before phase entry: {error_message}")

# Execute phase
result = orchestrator.phase_a_taskprofile_ttl(...)

# Update ExecutionPass after phase exit
execution_pass.timing_information["end_time"] = datetime.now().isoformat()
execution_pass.timing_information["duration"] = (
    datetime.fromisoformat(execution_pass.timing_information["end_time"])
    - datetime.fromisoformat(execution_pass.timing_information["start_time"])
).total_seconds()

# For Phase C, add execution_results and evaluation_results
if phase == "C":
    execution_pass.execution_results = execution_results
    execution_pass.evaluation_results = evaluation_results
    if refinement_changes:
        execution_pass.refinement_changes = refinement_changes

# Validate after phase exit
is_valid, error_message = validate_execution_pass_after_phase(
    execution_pass=execution_pass,
    phase="A"
)

if not is_valid:
    raise ValueError(f"Invalid ExecutionPass after phase exit: {error_message}")
```

## Advanced Patterns

### Retryable Error Handling

```python
from aeon.exceptions import PhaseTransitionError

def execute_phase_with_retry(
    transition_name: str,
    inputs: Dict[str, Any],
    phase_func: Callable,
    max_retries: int = 1
):
    """Execute phase with retry logic for retryable errors."""
    contract = get_phase_transition_contract(transition_name)
    
    # Validate inputs
    is_valid, error_message = validate_phase_transition_contract(
        transition_name=transition_name,
        inputs=inputs,
        contract=contract
    )
    
    if not is_valid:
        # Non-retryable validation error
        raise PhaseTransitionError(
            transition_name=transition_name,
            failure_condition=error_message,
            retryable=False
        )
    
    # Execute phase with retry
    for attempt in range(max_retries + 1):
        try:
            # Execute phase
            outputs = phase_func(**inputs)
            
            # Enforce contract
            success, error_message, phase_error = enforce_phase_transition_contract(
                transition_name=transition_name,
                inputs=inputs,
                outputs=outputs,
                contract=contract
            )
            
            if success:
                return outputs
            
            # Contract violation
            if not phase_error.retryable:
                # Non-retryable error
                raise phase_error
            
            # Retryable error - retry if attempts remaining
            if attempt < max_retries:
                continue
            else:
                # Max retries exceeded
                raise phase_error
                
        except PhaseTransitionError as e:
            if not e.retryable:
                # Non-retryable error
                raise
            # Retryable error - retry if attempts remaining
            if attempt < max_retries:
                continue
            else:
                # Max retries exceeded
                raise
```

### Complete Phase Transition Flow

```python
def execute_phase_transition(
    transition_name: str,
    phase: str,
    correlation_id: str,
    pass_number: int,
    context: Dict[str, Any],
    phase_func: Callable
):
    """Execute complete phase transition with all validations and logging."""
    logger = JSONLLogger(file_path=Path("execution.jsonl"))
    
    # Log phase entry
    logger.log_phase_entry(
        phase=phase,
        correlation_id=correlation_id,
        pass_number=pass_number
    )
    
    # Log state snapshot before transition
    logger.log_state_snapshot(
        correlation_id=correlation_id,
        phase=phase,
        pass_number=pass_number,
        plan_state=context.get("plan_state", {}),
        ttl_remaining=context.get("ttl_remaining", 0),
        phase_state=context.get("phase_state", {}),
        snapshot_type="before_transition"
    )
    
    # Check TTL before phase entry
    can_proceed, expiration_response = check_ttl_before_phase_entry(
        ttl_remaining=context.get("ttl_remaining", 0),
        phase=phase,
        execution_pass=context.get("execution_pass")
    )
    
    if not can_proceed:
        logger.log_phase_transition_error(
            correlation_id=correlation_id,
            phase=phase,
            pass_number=pass_number,
            error_code="AEON.PHASE_TRANSITION.TTL_EXPIRED",
            severity="CRITICAL",
            affected_component="ttl",
            failure_condition="TTL expired at phase boundary",
            retryable=False
        )
        raise TTLExpiredError(f"TTL expired at phase boundary: {expiration_response}")
    
    # Validate context propagation
    spec = get_context_propagation_specification(phase)
    is_valid, error_message, missing_fields = validate_context_propagation(
        phase=phase,
        context=context,
        specification=spec
    )
    
    if not is_valid:
        logger.log_phase_transition_error(
            correlation_id=correlation_id,
            phase=phase,
            pass_number=pass_number,
            error_code="AEON.CONTEXT_PROPAGATION.000",
            severity="ERROR",
            affected_component="context_propagation",
            failure_condition=f"Missing fields: {missing_fields}",
            retryable=False
        )
        raise ContextPropagationError(phase=phase, missing_fields=missing_fields)
    
    # Build LLM context
    llm_context = build_llm_context(
        phase=phase,
        context=context,
        specification=spec
    )
    
    # Execute phase with retry
    start_time = datetime.now()
    try:
        outputs = execute_phase_with_retry(
            transition_name=transition_name,
            inputs=context,
            phase_func=phase_func
        )
        outcome = "success"
    except Exception as e:
        outcome = "failure"
        raise
    finally:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Log state snapshot after transition
        logger.log_state_snapshot(
            correlation_id=correlation_id,
            phase=phase,
            pass_number=pass_number,
            plan_state=context.get("plan_state", {}),
            ttl_remaining=context.get("ttl_remaining", 0),
            phase_state=context.get("phase_state", {}),
            snapshot_type="after_transition"
        )
        
        # Log phase exit
        logger.log_phase_exit(
            phase=phase,
            correlation_id=correlation_id,
            pass_number=pass_number,
            duration=duration,
            outcome=outcome
        )
    
    return outputs
```

## Testing Examples

### Phase Transition Contract Tests

```python
import pytest
from aeon.orchestration.phases import (
    get_phase_transition_contract,
    validate_phase_transition_contract,
    enforce_phase_transition_contract
)

def test_phase_transition_contract_a_b_valid():
    """Test A→B transition with valid inputs."""
    contract = get_phase_transition_contract("A→B")
    
    inputs = {
        "task_profile": TaskProfile.default(),
        "initial_plan": Plan(goal="test", steps=[]),
        "ttl": 10
    }
    
    is_valid, error_message = validate_phase_transition_contract(
        transition_name="A→B",
        inputs=inputs,
        contract=contract
    )
    
    assert is_valid
    assert error_message is None

def test_phase_transition_contract_a_b_invalid_ttl():
    """Test A→B transition with invalid TTL."""
    contract = get_phase_transition_contract("A→B")
    
    inputs = {
        "task_profile": TaskProfile.default(),
        "initial_plan": Plan(goal="test", steps=[]),
        "ttl": 0  # Invalid: TTL must be > 0
    }
    
    is_valid, error_message = validate_phase_transition_contract(
        transition_name="A→B",
        inputs=inputs,
        contract=contract
    )
    
    assert not is_valid
    assert "ttl" in error_message.lower()
```

### Context Propagation Tests

```python
import pytest
from aeon.orchestration.phases import (
    get_context_propagation_specification,
    validate_context_propagation,
    build_llm_context
)

def test_context_propagation_phase_b_valid():
    """Test Phase B context propagation with valid context."""
    spec = get_context_propagation_specification("B")
    
    context = {
        "request": "test request",
        "task_profile": TaskProfile.default(),
        "initial_plan": Plan(goal="test", steps=[]),
        "pass_number": 0,
        "phase": "B",
        "ttl_remaining": 10,
        "correlation_id": "test-correlation-id",
        "execution_start_timestamp": "2025-01-27T00:00:00"
    }
    
    is_valid, error_message, missing_fields = validate_context_propagation(
        phase="B",
        context=context,
        specification=spec
    )
    
    assert is_valid
    assert error_message is None
    assert missing_fields == []

def test_context_propagation_phase_b_missing_fields():
    """Test Phase B context propagation with missing fields."""
    spec = get_context_propagation_specification("B")
    
    context = {
        "request": "test request",
        # Missing task_profile, initial_plan, etc.
    }
    
    is_valid, error_message, missing_fields = validate_context_propagation(
        phase="B",
        context=context,
        specification=spec
    )
    
    assert not is_valid
    assert len(missing_fields) > 0
```

### TTL Boundary Tests

```python
import pytest
from aeon.orchestration.ttl import (
    check_ttl_before_phase_entry,
    check_ttl_after_llm_call,
    decrement_ttl_per_cycle
)

def test_ttl_before_phase_entry_valid():
    """Test TTL check before phase entry with valid TTL."""
    can_proceed, expiration_response = check_ttl_before_phase_entry(
        ttl_remaining=10,
        phase="B",
        execution_pass=execution_pass
    )
    
    assert can_proceed
    assert expiration_response is None

def test_ttl_before_phase_entry_expired():
    """Test TTL check before phase entry with expired TTL."""
    can_proceed, expiration_response = check_ttl_before_phase_entry(
        ttl_remaining=0,
        phase="B",
        execution_pass=execution_pass
    )
    
    assert not can_proceed
    assert expiration_response is not None
    assert expiration_response.expiration_type == "phase_boundary"

def test_ttl_decrement_per_cycle():
    """Test TTL decrement exactly once per cycle."""
    ttl_remaining = 10
    
    # Decrement once per cycle
    ttl_remaining = decrement_ttl_per_cycle(ttl_remaining)
    
    assert ttl_remaining == 9
    
    # Decrement again
    ttl_remaining = decrement_ttl_per_cycle(ttl_remaining)
    
    assert ttl_remaining == 8
```

## Best Practices

1. **Always validate phase transition contracts** before and after phase transitions
2. **Always validate context propagation** before LLM calls
3. **Always check TTL** before phase entry and after each LLM call
4. **Always log phase boundaries** (entry, exit, state snapshots, TTL snapshots)
5. **Always validate ExecutionPass** before and after phase transitions
6. **Handle retryable errors** with exactly one retry attempt
7. **Handle non-retryable errors** by aborting immediately
8. **Use structured error logging** for all phase transition errors
9. **Ensure deterministic behavior** for identical inputs
10. **Test all phase transitions** with valid and invalid inputs

