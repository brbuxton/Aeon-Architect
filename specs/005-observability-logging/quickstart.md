# Quickstart: Observability, Logging, and Test Coverage

**Date**: 2025-12-05  
**Feature**: Observability, Logging, and Test Coverage  
**Phase**: 1 - Design

## Overview

This guide provides examples and patterns for using phase-aware structured logging, actionable error logging, and enhanced debug visibility. All examples extend the existing JSONL logging infrastructure from Sprint 1.

## Basic Usage

### Initialization

```python
from aeon.observability.logger import JSONLLogger
from aeon.observability.helpers import generate_correlation_id
from datetime import datetime

# Initialize logger
logger = JSONLLogger(file_path=Path("execution.jsonl"))

# Generate correlation ID at execution start
execution_start_timestamp = datetime.now().isoformat()
request = "Create a plan to process user data"
correlation_id = generate_correlation_id(execution_start_timestamp, request)
```

### Phase-Aware Logging

```python
# Log phase entry
logger.log_phase_entry(
    phase="A",
    correlation_id=correlation_id,
    context={"request": request}
)

# ... Phase A execution ...

# Log phase exit
logger.log_phase_exit(
    phase="A",
    correlation_id=correlation_id,
    duration=1.23,
    outcome="success"
)

# Log phase B entry
logger.log_phase_entry(
    phase="B",
    correlation_id=correlation_id
)
```

### Error Logging

```python
from aeon.observability.models import ErrorRecord
from aeon.exceptions import RefinementError

try:
    # ... refinement operation ...
    apply_refinement_actions(plan, actions)
except RefinementError as e:
    # Convert exception to ErrorRecord
    error_record = e.to_error_record()
    
    # Log error
    logger.log_error(
        correlation_id=correlation_id,
        error=error_record
    )
    
    # Kernel decides recovery
    try:
        # ... recovery attempt ...
        logger.log_error_recovery(
            correlation_id=correlation_id,
            original_error=error_record,
            recovery_action="fallback_to_default_plan",
            recovery_outcome="success"
        )
    except Exception as recovery_error:
        logger.log_error_recovery(
            correlation_id=correlation_id,
            original_error=error_record,
            recovery_action="fallback_to_default_plan",
            recovery_outcome="failure"
        )
```

### State Transition Logging

```python
from aeon.observability.models import PlanStateSlice

# Create state slice before transition
before_slice = PlanStateSlice(
    component="plan",
    timestamp=datetime.now().isoformat(),
    plan_id="plan_123",
    current_step_id="step_2",
    step_count=5,
    steps_status_summary={
        "pending": 2,
        "running": 1,
        "complete": 2
    }
)

# ... state transition (e.g., refinement applied) ...

# Create state slice after transition
after_slice = PlanStateSlice(
    component="plan",
    timestamp=datetime.now().isoformat(),
    plan_id="plan_123",
    current_step_id="step_3",
    step_count=6,  # Step added
    steps_status_summary={
        "pending": 2,
        "running": 1,
        "complete": 3
    }
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

### Refinement Outcome Logging

```python
from aeon.observability.models import PlanFragment, ConvergenceAssessmentSummary, ValidationIssuesSummary

# Create plan fragments (changed steps only)
before_fragment = PlanFragment(
    changed_steps=[
        PlanStep(step_id="step_1", description="Original step", status="pending", ...)
    ],
    unchanged_step_ids=["step_2", "step_3"]
)

after_fragment = PlanFragment(
    changed_steps=[
        PlanStep(step_id="step_1", description="Updated step", status="complete", ...),
        PlanStep(step_id="step_4", description="New step", status="pending", ...)
    ],
    unchanged_step_ids=["step_2", "step_3"]
)

# Create evaluation signals summary
convergence_summary = ConvergenceAssessmentSummary(
    converged=False,
    reason_codes=["validation_issues", "incomplete_steps"],
    scores={"completeness": 0.8, "coherence": 0.9, "consistency": 0.95},
    pass_number=2
)

validation_summary = ValidationIssuesSummary(
    total_issues=2,
    critical_count=0,
    error_count=1,
    warning_count=1,
    info_count=0,
    issues_by_type={"missing_tool": 1, "invalid_schema": 1}
)

# Log refinement outcome
logger.log_refinement_outcome(
    correlation_id=correlation_id,
    pass_number=2,
    phase="C",
    evaluation_signals={
        "convergence_assessment": convergence_summary.model_dump(),
        "validation_issues": validation_summary.model_dump()
    },
    refinement_actions=[
        {"type": "modify_step", "step_id": "step_1"},
        {"type": "add_step", "step_id": "step_4"}
    ],
    before_plan_fragment=before_fragment.model_dump(),
    after_plan_fragment=after_fragment.model_dump()
)
```

### Evaluation Outcome Logging

```python
# Log evaluation outcome
logger.log_evaluation_outcome(
    correlation_id=correlation_id,
    pass_number=2,
    phase="C",
    convergence_assessment=convergence_summary.model_dump(),
    validation_report=validation_summary.model_dump()
)
```

## Error Model Usage

### Defining Error Codes

```python
from aeon.exceptions import AeonError
from aeon.observability.models import ErrorRecord

class RefinementError(AeonError):
    """Raised when refinement operations fail."""
    
    ERROR_CODE = "AEON.REFINEMENT.001"
    SEVERITY = "ERROR"
    
    def __init__(self, message: str, step_id: Optional[str] = None, attempted_action: Optional[str] = None):
        super().__init__(message)
        self.step_id = step_id
        self.attempted_action = attempted_action
    
    def to_error_record(self) -> ErrorRecord:
        """Convert exception to ErrorRecord."""
        return ErrorRecord(
            code=self.ERROR_CODE,
            severity=self.SEVERITY,
            message=str(self),
            affected_component="refinement",
            context={
                "step_id": self.step_id,
                "attempted_action": self.attempted_action
            },
            stack_trace=self.__traceback__ if self.__traceback__ else None
        )
```

### Using Error Records

```python
# Create error record from exception
try:
    # ... operation ...
except RefinementError as e:
    error_record = e.to_error_record()
    logger.log_error(correlation_id=correlation_id, error=error_record)

# Create error record manually
error_record = ErrorRecord(
    code="AEON.EXECUTION.002",
    severity="ERROR",
    message="Step execution failed: tool not found",
    affected_component="execution",
    context={
        "step_id": "step_1",
        "tool_name": "missing_tool",
        "attempted_action": "invoke_tool"
    }
)
logger.log_error(correlation_id=correlation_id, error=error_record)
```

## Backward Compatibility

### Existing Logging (Still Works)

```python
# Existing format_entry() method still works
entry = logger.format_entry(
    step_number=1,
    plan_state={"goal": "Process data", "steps": [...]},
    llm_output={"response": "..."},
    supervisor_actions=[],
    tool_calls=[],
    ttl_remaining=10,
    errors=[],
    pass_number=1,
    phase="A"
)

# Log entry (creates event="cycle" for backward compatibility)
logger.log_entry(entry)
```

### Migration Pattern

```python
# Old pattern (still works)
logger.log_entry(logger.format_entry(...))

# New pattern (phase-aware)
logger.log_phase_entry(phase="A", correlation_id=correlation_id)
# ... phase execution ...
logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.23, outcome="success")
```

## Log Entry Examples

### Phase Entry Event

```json
{
  "event": "phase_entry",
  "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "phase": "A",
  "timestamp": "2025-01-27T10:00:00.000000",
  "context": {
    "request": "Create a plan to process user data"
  }
}
```

### Phase Exit Event

```json
{
  "event": "phase_exit",
  "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "phase": "A",
  "duration": 1.23,
  "outcome": "success",
  "timestamp": "2025-01-27T10:00:01.230000"
}
```

### State Transition Event

```json
{
  "event": "state_transition",
  "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "component": "plan",
  "before_state": {
    "component": "plan",
    "plan_id": "plan_123",
    "current_step_id": "step_2",
    "step_count": 5,
    "steps_status_summary": {
      "pending": 2,
      "running": 1,
      "complete": 2
    },
    "timestamp": "2025-01-27T10:00:02.000000"
  },
  "after_state": {
    "component": "plan",
    "plan_id": "plan_123",
    "current_step_id": "step_3",
    "step_count": 6,
    "steps_status_summary": {
      "pending": 2,
      "running": 1,
      "complete": 3
    },
    "timestamp": "2025-01-27T10:00:02.100000"
  },
  "transition_reason": "refinement_applied",
  "timestamp": "2025-01-27T10:00:02.100000"
}
```

### Error Event

```json
{
  "event": "cycle",
  "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "step_number": 1,
  "errors": [
    {
      "code": "AEON.REFINEMENT.001",
      "severity": "ERROR",
      "message": "Failed to apply refinement action: invalid step_id",
      "affected_component": "refinement",
      "context": {
        "step_id": "step_1",
        "attempted_action": "modify_step"
      }
    }
  ],
  "timestamp": "2025-01-27T10:00:03.000000"
}
```

### Refinement Outcome Event

```json
{
  "event": "refinement_outcome",
  "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "pass_number": 2,
  "phase": "C",
  "evaluation_signals": {
    "convergence_assessment": {
      "converged": false,
      "reason_codes": ["validation_issues", "incomplete_steps"],
      "scores": {
        "completeness": 0.8,
        "coherence": 0.9,
        "consistency": 0.95
      },
      "pass_number": 2
    },
    "validation_issues": {
      "total_issues": 2,
      "critical_count": 0,
      "error_count": 1,
      "warning_count": 1,
      "info_count": 0,
      "issues_by_type": {
        "missing_tool": 1,
        "invalid_schema": 1
      }
    }
  },
  "refinement_actions": [
    {"type": "modify_step", "step_id": "step_1"},
    {"type": "add_step", "step_id": "step_4"}
  ],
  "before_plan_fragment": {
    "changed_steps": [
      {
        "step_id": "step_1",
        "description": "Original step",
        "status": "pending"
      }
    ],
    "unchanged_step_ids": ["step_2", "step_3"]
  },
  "after_plan_fragment": {
    "changed_steps": [
      {
        "step_id": "step_1",
        "description": "Updated step",
        "status": "complete"
      },
      {
        "step_id": "step_4",
        "description": "New step",
        "status": "pending"
      }
    ],
    "unchanged_step_ids": ["step_2", "step_3"]
  },
  "timestamp": "2025-01-27T10:00:04.000000"
}
```

## Testing Examples

### Testing Correlation ID Generation

```python
def test_correlation_id_deterministic():
    """Test that correlation IDs are deterministic."""
    timestamp = "2025-01-27T10:00:00.000000"
    request = "Test request"
    
    id1 = generate_correlation_id(timestamp, request)
    id2 = generate_correlation_id(timestamp, request)
    
    assert id1 == id2  # Deterministic
    assert id1.startswith("6ba7b810") or id1.startswith("aeon-")  # UUIDv5 or fallback
```

### Testing Phase Logging

```python
def test_phase_logging():
    """Test phase entry/exit logging."""
    logger = JSONLLogger(file_path=Path("test.jsonl"))
    correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
    
    logger.log_phase_entry(phase="A", correlation_id=correlation_id)
    logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
    
    # Read log file and verify entries
    with open("test.jsonl") as f:
        entries = [json.loads(line) for line in f]
    
    assert entries[0]["event"] == "phase_entry"
    assert entries[0]["phase"] == "A"
    assert entries[0]["correlation_id"] == correlation_id
    assert entries[1]["event"] == "phase_exit"
    assert entries[1]["outcome"] == "success"
```

### Testing Error Logging

```python
def test_error_logging():
    """Test error logging with ErrorRecord."""
    logger = JSONLLogger(file_path=Path("test.jsonl"))
    correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
    
    error = RefinementError("Test error", step_id="step_1", attempted_action="modify")
    error_record = error.to_error_record()
    
    logger.log_error(correlation_id=correlation_id, error=error_record)
    
    # Read log file and verify error entry
    with open("test.jsonl") as f:
        entry = json.loads(f.readline())
    
    assert entry["errors"][0]["code"] == "AEON.REFINEMENT.001"
    assert entry["errors"][0]["severity"] == "ERROR"
    assert entry["errors"][0]["affected_component"] == "refinement"
```

## Performance Considerations

### Logging Latency

```python
import time

def test_logging_latency():
    """Test that logging latency is <10ms."""
    logger = JSONLLogger(file_path=Path("test.jsonl"))
    correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
    
    start = time.time()
    logger.log_phase_entry(phase="A", correlation_id=correlation_id)
    latency = (time.time() - start) * 1000  # Convert to ms
    
    assert latency < 10.0  # SC-005: Logging latency <10ms
```

### Non-Blocking Behavior

```python
def test_logging_non_blocking():
    """Test that logging errors don't block execution."""
    # Use invalid file path to trigger write error
    logger = JSONLLogger(file_path=Path("/invalid/path/file.jsonl"))
    correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
    
    # Should not raise exception
    logger.log_phase_entry(phase="A", correlation_id=correlation_id)
    
    # Execution continues
    assert True  # No exception raised
```

## Schema Validation

All log entries conform to stable JSONL schemas with 100% valid JSON. Each event type has a well-defined schema:

### Schema Requirements

- **All entries must be valid JSON**: Every line in the JSONL file is parseable JSON
- **Required fields**: All entries have `event`, `timestamp`, and optionally `correlation_id`
- **Type safety**: Event types are validated against known literals
- **Backward compatibility**: Old format entries (event="cycle") remain valid

### Schema Validation Example

```python
import json

def validate_log_schema(log_file: Path):
    """Validate that all log entries conform to schema."""
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                # Verify required fields
                assert "event" in entry
                assert "timestamp" in entry
                # Verify event type is valid
                assert entry["event"] in [
                    "phase_entry", "phase_exit", "state_transition",
                    "refinement_outcome", "evaluation_outcome",
                    "error", "error_recovery", "cycle"
                ]
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
```

## Determinism Validation

Logging operations preserve kernel determinism. Correlation IDs are deterministic and logging does not introduce non-deterministic behavior.

### Correlation ID Determinism

Correlation IDs are generated deterministically using UUIDv5:

```python
def test_correlation_id_deterministic():
    """Test that correlation IDs are deterministic."""
    timestamp = "2025-01-27T10:00:00.000000"
    request = "Test request"
    
    id1 = generate_correlation_id(timestamp, request)
    id2 = generate_correlation_id(timestamp, request)
    
    assert id1 == id2  # Same inputs produce same ID
```

### Kernel Determinism

Logging operations do not affect kernel determinism:

- **No side effects**: Logging failures are silent and do not affect execution
- **Deterministic correlation IDs**: Same execution inputs produce same correlation ID
- **No non-deterministic behavior**: Logging does not introduce randomness or timing dependencies

## Diagnostic Capability

≥90% of failures are diagnosable from logs (SC-008). Each error log entry contains:

1. **Error code**: Structured error code (e.g., "AEON.REFINEMENT.001")
2. **Severity level**: CRITICAL, ERROR, WARNING, or INFO
3. **Error message**: Human-readable error message
4. **Affected component**: Component where error occurred
5. **Context**: Additional context for diagnosis (step_id, tool_name, etc.)
6. **Correlation ID**: Links error to execution trace

### Diagnostic Information Example

```python
# Error log entry contains all diagnostic information
error_entry = {
    "event": "error",
    "correlation_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "original_error": {
        "code": "AEON.EXECUTION.001",
        "severity": "ERROR",
        "message": "Step execution failed: tool not found",
        "affected_component": "execution",
        "context": {
            "step_id": "step_1",
            "tool_name": "missing_tool",
            "attempted_action": "invoke_tool"
        }
    },
    "timestamp": "2025-01-27T10:00:03.000000"
}

# Can diagnose failure from:
# 1. Error code: AEON.EXECUTION.001
# 2. Component: execution
# 3. Context: step_id, tool_name, attempted_action
# 4. Correlation ID: Links to full execution trace
```

## Error Code Conventions

Error codes follow the format: `AEON.<COMPONENT>.<CODE>`

### Component Names

- `REFINEMENT`: Refinement operations
- `EXECUTION`: Step execution
- `VALIDATION`: Validation operations
- `PHASE`: Phase transitions
- `PLAN`: Plan operations
- `TOOL`: Tool invocations
- `MEMORY`: Memory operations
- `LLM`: LLM adapter operations
- `SUPERVISOR`: Supervisor operations

### Error Code Examples

```python
# Refinement errors
"AEON.REFINEMENT.001"  # Invalid step_id
"AEON.REFINEMENT.002"  # Refinement action failed

# Execution errors
"AEON.EXECUTION.001"   # Tool not found
"AEON.EXECUTION.002"   # Step execution timeout

# Validation errors
"AEON.VALIDATION.001"  # Semantic validation failed
"AEON.VALIDATION.002"  # Schema validation failed
```

## Best Practices

1. **Generate correlation ID once** at execution start and pass to all logging calls
2. **Use structured error records** instead of string error messages
3. **Log state transitions** with minimal state slices (not full state)
4. **Log plan fragments** with changed steps only (not full plan)
5. **Log evaluation signals** as summaries (not full evaluation data)
6. **Handle logging errors gracefully** (logging should never raise exceptions)
7. **Use phase-aware logging** for multi-pass execution (phase_entry, phase_exit)
8. **Log error recovery attempts** to track recovery success rates
9. **Maintain backward compatibility** with existing logging methods
10. **Profile logging performance** to ensure <10ms latency
11. **Validate log schemas** to ensure 100% valid JSON
12. **Preserve determinism** by using deterministic correlation IDs
13. **Include diagnostic context** in all error logs for ≥90% diagnosability

