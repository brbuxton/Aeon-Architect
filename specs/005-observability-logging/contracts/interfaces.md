# Interface Contracts: Observability, Logging, and Test Coverage

**Date**: 2025-01-27  
**Feature**: Observability, Logging, and Test Coverage  
**Phase**: 1 - Design

## Overview

This document defines the interface contracts for phase-aware structured logging, actionable error logging, and enhanced debug visibility. These interfaces extend the existing JSONLLogger interface from Sprint 1 with phase-aware capabilities.

## Interface Design Principles

1. **Non-Blocking**: All logging methods are non-blocking and fail silently on errors
2. **Structured Data**: All log entries use structured Pydantic models
3. **Correlation IDs**: All log entries include correlation_id for trace reconstruction
4. **Backward Compatibility**: Existing logging methods remain functional
5. **Deterministic**: Logging operations do not affect kernel determinism

## JSONLLogger Interface

**Module**: `aeon.observability.logger`

**Purpose**: Provide phase-aware structured logging with correlation IDs, error logging, and debug visibility.

### generate_correlation_id

**Signature**:
```python
def generate_correlation_id(
    execution_start_timestamp: str,
    request: str
) -> str:
    """
    Generate a deterministic correlation ID for an execution cycle.
    
    Args:
        execution_start_timestamp: ISO 8601 timestamp of execution start
        request: Natural language request string
    
    Returns:
        Correlation ID string (UUIDv5 or fallback format)
    
    Behavior:
        - Uses UUIDv5 with fixed namespace and timestamp+request hash
        - Falls back to deterministic timestamp-based ID if UUID generation fails
        - Returns same ID for same inputs (deterministic)
    """
```

**Error Handling**:
- If UUIDv5 generation fails, returns fallback format: `f"aeon-{execution_start_timestamp}-{request_hash[:8]}"`
- Never raises exceptions (ensures logging continues)

### log_phase_entry

**Signature**:
```python
def log_phase_entry(
    phase: Literal["A", "B", "C", "D"],
    correlation_id: str,
    timestamp: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a phase entry event.
    
    Args:
        phase: Phase identifier (A, B, C, or D)
        correlation_id: Correlation ID for this execution
        timestamp: ISO 8601 timestamp (defaults to now if None)
        context: Optional context data
    
    Behavior:
        - Creates LogEntry with event="phase_entry"
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
    duration: float,
    outcome: Literal["success", "failure"],
    timestamp: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a phase exit event.
    
    Args:
        phase: Phase identifier (A, B, C, or D)
        correlation_id: Correlation ID for this execution
        duration: Phase duration in seconds
        outcome: Phase outcome (success or failure)
        timestamp: ISO 8601 timestamp (defaults to now if None)
        context: Optional context data
    
    Behavior:
        - Creates LogEntry with event="phase_exit"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_state_transition

**Signature**:
```python
def log_state_transition(
    correlation_id: str,
    component: str,
    before_state: Dict[str, Any],
    after_state: Dict[str, Any],
    transition_reason: str,
    timestamp: Optional[str] = None
) -> None:
    """
    Log a state transition event.
    
    Args:
        correlation_id: Correlation ID for this execution
        component: Component name (e.g., "plan", "execution", "refinement")
        before_state: State snapshot before transition (StateSlice model_dump())
        after_state: State snapshot after transition (StateSlice model_dump())
        transition_reason: Reason for state transition
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates LogEntry with event="state_transition"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_refinement_outcome

**Signature**:
```python
def log_refinement_outcome(
    correlation_id: str,
    pass_number: int,
    phase: Literal["A", "B", "C", "D"],
    evaluation_signals: Dict[str, Any],
    refinement_actions: List[Dict[str, Any]],
    before_plan_fragment: Dict[str, Any],
    after_plan_fragment: Dict[str, Any],
    timestamp: Optional[str] = None
) -> None:
    """
    Log a refinement outcome event.
    
    Args:
        correlation_id: Correlation ID for this execution
        pass_number: Pass number in multi-pass execution
        phase: Current phase (A, B, C, or D)
        evaluation_signals: Evaluation signals summary (convergence assessment, validation issues)
        refinement_actions: List of refinement actions applied
        before_plan_fragment: Plan fragment before refinement (PlanFragment model_dump())
        after_plan_fragment: Plan fragment after refinement (PlanFragment model_dump())
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates LogEntry with event="refinement_outcome"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_evaluation_outcome

**Signature**:
```python
def log_evaluation_outcome(
    correlation_id: str,
    pass_number: int,
    phase: Literal["A", "B", "C", "D"],
    convergence_assessment: Dict[str, Any],
    validation_report: Dict[str, Any],
    timestamp: Optional[str] = None
) -> None:
    """
    Log an evaluation outcome event.
    
    Args:
        correlation_id: Correlation ID for this execution
        pass_number: Pass number in multi-pass execution
        phase: Current phase (A, B, C, or D)
        convergence_assessment: Convergence assessment summary (ConvergenceAssessmentSummary model_dump())
        validation_report: Validation report summary (ValidationIssuesSummary model_dump())
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates LogEntry with event="evaluation_outcome"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### log_error

**Signature**:
```python
def log_error(
    correlation_id: str,
    error: ErrorRecord,
    timestamp: Optional[str] = None
) -> None:
    """
    Log an error event.
    
    Args:
        correlation_id: Correlation ID for this execution
        error: ErrorRecord instance
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates LogEntry with error information
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions
- Error logging itself never raises exceptions (prevents cascading failures)

### log_error_recovery

**Signature**:
```python
def log_error_recovery(
    correlation_id: str,
    original_error: ErrorRecord,
    recovery_action: str,
    recovery_outcome: Literal["success", "failure"],
    timestamp: Optional[str] = None
) -> None:
    """
    Log an error recovery attempt.
    
    Args:
        correlation_id: Correlation ID for this execution
        original_error: Original error that triggered recovery
        recovery_action: Recovery action attempted
        recovery_outcome: Recovery outcome (success or failure)
        timestamp: ISO 8601 timestamp (defaults to now if None)
    
    Behavior:
        - Creates LogEntry with event="error_recovery"
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

### format_entry (Existing - Backward Compatible)

**Signature**:
```python
def format_entry(
    step_number: int,
    plan_state: dict,
    llm_output: dict,
    supervisor_actions: list = None,
    tool_calls: list = None,
    ttl_remaining: int = 0,
    errors: list = None,
    pass_number: Optional[int] = None,
    phase: Optional[str] = None,
) -> LogEntry:
    """
    Format a log entry from orchestration cycle data (backward compatible).
    
    Args:
        step_number: Sequential cycle identifier
        plan_state: Snapshot of plan at cycle start
        llm_output: Raw LLM response
        supervisor_actions: Supervisor repairs in this cycle (optional)
        tool_calls: Tool invocations in this cycle (optional)
        ttl_remaining: Cycles left before expiration
        errors: Errors in this cycle (optional)
        pass_number: Pass number in multi-pass execution (optional)
        phase: Current phase in multi-pass execution (optional)
    
    Returns:
        LogEntry instance with event="cycle" (backward compatible)
    """
```

**Behavior**:
- Maintains backward compatibility with Sprint 1 logging
- Creates LogEntry with event="cycle"
- Includes correlation_id if provided (optional for backward compatibility)

### log_entry (Existing - Backward Compatible)

**Signature**:
```python
def log_entry(self, entry: LogEntry) -> None:
    """
    Write a log entry to the JSONL file (backward compatible).
    
    Args:
        entry: LogEntry to write
    
    Behavior:
        - Writes to JSONL file (non-blocking)
        - Silently fails on write errors
    """
```

**Error Handling**:
- Silently fails on file write errors (non-blocking)
- Never raises exceptions

## ErrorRecord Interface

**Module**: `aeon.observability.models`

**Purpose**: Structured error record with error code, severity, and context.

### ErrorRecord Model

**Fields**:
- `code` (string, required): Error code in format "AEON.<COMPONENT>.<CODE>"
- `severity` (enum, required): Severity level (CRITICAL, ERROR, WARNING, INFO)
- `message` (string, required): Human-readable error message
- `affected_component` (string, required): Component where error occurred
- `context` (dict, optional): Additional context for diagnosis
- `stack_trace` (string, optional): Stack trace if available

**Validation**:
- code must match pattern "AEON.<COMPONENT>.<CODE>"
- severity must be one of: CRITICAL, ERROR, WARNING, INFO
- message must be non-empty string
- affected_component must be non-empty string

## Exception Interface Extensions

**Module**: `aeon.exceptions`

**Purpose**: Extend exception classes with structured error record conversion.

### to_error_record (Method on Exception Classes)

**Signature**:
```python
def to_error_record(self) -> ErrorRecord:
    """
    Convert exception to ErrorRecord.
    
    Returns:
        ErrorRecord instance with error code, severity, message, and context
    
    Behavior:
        - Extracts error code from exception class constant
        - Maps exception type to severity level
        - Includes exception message and context
        - Includes stack trace if available
    """
```

**Implementation**:
- Each exception class defines `ERROR_CODE` constant (e.g., `"AEON.REFINEMENT.001"`)
- Each exception class defines `SEVERITY` constant (e.g., `"ERROR"`)
- `to_error_record()` method creates ErrorRecord from exception instance

## Correlation ID Helper Interface

**Module**: `aeon.observability.helpers`

**Purpose**: Provide correlation ID generation utilities.

### generate_correlation_id

**Signature**:
```python
def generate_correlation_id(
    execution_start_timestamp: str,
    request: str
) -> str:
    """
    Generate a deterministic correlation ID.
    
    Args:
        execution_start_timestamp: ISO 8601 timestamp of execution start
        request: Natural language request string
    
    Returns:
        Correlation ID string (UUIDv5 or fallback format)
    
    Behavior:
        - Uses UUIDv5 with fixed namespace UUID
        - Name component: f"{execution_start_timestamp}:{request_hash}"
        - Falls back to deterministic format if UUID generation fails
    """
```

**Error Handling**:
- If UUIDv5 generation fails, returns fallback: `f"aeon-{execution_start_timestamp}-{request_hash[:8]}"`
- Never raises exceptions

## Interface Usage Patterns

### Phase-Aware Logging Pattern

```python
# Generate correlation ID at execution start
correlation_id = generate_correlation_id(execution_start_timestamp, request)

# Log phase entry
logger.log_phase_entry(phase="A", correlation_id=correlation_id)

# ... phase execution ...

# Log phase exit
logger.log_phase_exit(
    phase="A",
    correlation_id=correlation_id,
    duration=1.23,
    outcome="success"
)
```

### Error Logging Pattern

```python
try:
    # ... operation ...
except RefinementError as e:
    # Convert exception to ErrorRecord
    error_record = e.to_error_record()
    
    # Log error
    logger.log_error(correlation_id=correlation_id, error=error_record)
    
    # Kernel decides recovery
    recovery_action = "fallback_to_default"
    try:
        # ... recovery attempt ...
        logger.log_error_recovery(
            correlation_id=correlation_id,
            original_error=error_record,
            recovery_action=recovery_action,
            recovery_outcome="success"
        )
    except Exception:
        logger.log_error_recovery(
            correlation_id=correlation_id,
            original_error=error_record,
            recovery_action=recovery_action,
            recovery_outcome="failure"
        )
```

### State Transition Logging Pattern

```python
# Create state slices
before_slice = PlanStateSlice(
    component="plan",
    plan_id=plan.id,
    current_step_id=plan.current_step_id,
    step_count=len(plan.steps),
    steps_status_summary=summarize_step_statuses(plan.steps),
    timestamp=datetime.now().isoformat(),
)

# ... state transition ...

after_slice = PlanStateSlice(
    component="plan",
    plan_id=plan.id,
    current_step_id=plan.current_step_id,
    step_count=len(plan.steps),
    steps_status_summary=summarize_step_statuses(plan.steps),
    timestamp=datetime.now().isoformat(),
)

# Log state transition
logger.log_state_transition(
    correlation_id=correlation_id,
    component="plan",
    before_state=before_slice.model_dump(),
    after_state=after_slice.model_dump(),
    transition_reason="refinement_applied"
)
```

## Contract Guarantees

1. **Non-Blocking**: All logging methods are non-blocking and never block execution
2. **Silent Failure**: Logging errors never raise exceptions or cascade failures
3. **Deterministic**: Correlation ID generation is deterministic (same inputs produce same ID)
4. **Structured**: All log entries use structured Pydantic models
5. **Backward Compatible**: Existing logging methods remain functional
6. **Performance**: Logging latency <10ms per entry (validated by profiling)

## Testing Requirements

All interfaces must be tested for:
- Non-blocking behavior (logging errors don't block execution)
- Silent failure (logging errors don't raise exceptions)
- Deterministic correlation ID generation
- Structured data validation (Pydantic models)
- Backward compatibility (existing methods work)
- Performance (logging latency <10ms)

