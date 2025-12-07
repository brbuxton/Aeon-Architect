# Phase E (Answer Synthesis) Interface Contract

**Feature**: Phase E Synthesis  
**Date**: 2025-12-07  
**Type**: Python Module Interface

## Overview

This contract defines the interface for Phase E answer synthesis, which consolidates execution results into a coherent final answer.

## Interface: execute_phase_e

### Function Definition

```python
def execute_phase_e(
    phase_e_input: PhaseEInput,
    llm_adapter: LLMAdapter,
    prompt_registry: PromptRegistry
) -> FinalAnswer:
    """
    Execute Phase E: Answer Synthesis.
    
    Synthesizes a final answer from execution results, plan state, and
    convergence assessment. This phase completes the A→B→C→D→E reasoning
    loop by producing a coherent response for the user.
    
    Args:
        phase_e_input: Complete final execution state
        llm_adapter: LLM adapter for synthesis calls
        prompt_registry: Prompt registry for synthesis prompts
        
    Returns:
        FinalAnswer containing synthesized answer text and metadata
        
    Raises:
        ValidationError: If phase_e_input does not conform to PhaseEInput model
        SynthesisError: If synthesis fails (LLM error, invalid response, etc.)
    """
    pass
```

## Interface: PhaseEInput

### Model Definition

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class PhaseEInput(BaseModel):
    """Input model for Phase E answer synthesis."""
    
    # Core request
    request: str
    
    # Execution results
    execution_results: List[Dict[str, Any]]
    
    # Plan state
    plan_state: Dict[str, Any]  # Serialized Plan
    
    # Convergence assessment
    convergence_assessment: Dict[str, Any]  # Serialized ConvergenceAssessment
    
    # Optional execution metadata
    execution_passes: Optional[List[Dict[str, Any]]] = None
    semantic_validation: Optional[Dict[str, Any]] = None
    task_profile: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    correlation_id: str
    execution_start_timestamp: str  # ISO format timestamp
    convergence_status: bool
    total_passes: int
    total_refinements: int
    ttl_remaining: int
```

### Field Descriptions

- **request**: Original user request that initiated execution
- **execution_results**: List of step execution results from all passes
- **plan_state**: Current plan state (serialized Plan object)
- **convergence_assessment**: Convergence assessment results (serialized ConvergenceAssessment)
- **execution_passes**: Optional list of execution pass metadata
- **semantic_validation**: Optional semantic validation report
- **task_profile**: Optional task profile information
- **correlation_id**: Execution correlation identifier
- **execution_start_timestamp**: ISO format timestamp of execution start
- **convergence_status**: Whether execution converged
- **total_passes**: Total number of execution passes
- **total_refinements**: Total number of plan refinements
- **ttl_remaining**: Remaining TTL tokens

## Interface: FinalAnswer

### Model Definition

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class FinalAnswer(BaseModel):
    """Output model for Phase E answer synthesis."""
    
    # Required fields
    answer_text: str  # Synthesized answer text
    
    # Optional fields
    confidence: Optional[float] = None  # Confidence score (0.0-1.0)
    used_step_ids: Optional[List[str]] = None  # Step IDs that contributed to answer
    notes: Optional[str] = None  # Additional notes or context
    ttl_exhausted: Optional[bool] = None  # Whether TTL was exhausted
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
```

### Field Descriptions

- **answer_text**: Synthesized answer text (required, non-empty)
- **confidence**: Confidence score between 0.0 and 1.0 (optional)
- **used_step_ids**: List of step IDs that contributed to the answer (optional)
- **notes**: Additional notes or context (optional)
- **ttl_exhausted**: Whether TTL was exhausted during execution (optional)
- **metadata**: Additional metadata dictionary (optional)

## Integration Point

### Engine Integration

Phase E is integrated at the exit of the C-loop in `OrchestrationEngine.run_multipass()`:

```python
# After _execute_phase_c_loop returns
converged, task_profile = self._execute_phase_c_loop(...)

# Build PhaseEInput from final state
phase_e_input = PhaseEInput(
    request=request,
    execution_results=execution_results,
    plan_state=serialize_plan(state.plan),
    convergence_assessment=serialize_convergence(convergence_assessment),
    execution_passes=serialize_passes(execution_passes),
    semantic_validation=serialize_validation(semantic_validation),
    task_profile=serialize_task_profile(task_profile),
    correlation_id=execution_context.correlation_id,
    execution_start_timestamp=execution_start_timestamp.isoformat(),
    convergence_status=converged,
    total_passes=len(execution_passes),
    total_refinements=state.total_refinements,
    ttl_remaining=state.ttl_remaining
)

# Execute Phase E
final_answer = execute_phase_e(
    phase_e_input=phase_e_input,
    llm_adapter=self.llm_adapter,
    prompt_registry=prompt_registry
)

# Attach to execution result
execution_result["final_answer"] = final_answer.model_dump()
```

## Error Types

### SynthesisError

```python
class SynthesisError(Exception):
    """Raised when Phase E synthesis fails."""
    pass
```

## Usage Examples

### Example 1: Basic Phase E Execution

```python
from aeon.orchestration.phases import execute_phase_e, PhaseEInput
from aeon.prompts.registry import PromptRegistry

# Build PhaseEInput from execution state
phase_e_input = PhaseEInput(
    request="Deploy a web application",
    execution_results=[...],
    plan_state={...},
    convergence_assessment={...},
    correlation_id="abc123",
    execution_start_timestamp="2025-01-27T10:00:00Z",
    convergence_status=True,
    total_passes=3,
    total_refinements=1,
    ttl_remaining=5000
)

# Execute Phase E
final_answer = execute_phase_e(
    phase_e_input=phase_e_input,
    llm_adapter=llm_adapter,
    prompt_registry=prompt_registry
)

# Use final answer
print(final_answer.answer_text)
print(f"Confidence: {final_answer.confidence}")
```

### Example 2: Degraded Mode (TTL Expired)

```python
# Phase E handles degraded conditions gracefully
phase_e_input = PhaseEInput(
    request="Complex task",
    execution_results=[...],  # Partial results
    plan_state={...},
    convergence_assessment={...},
    convergence_status=False,  # Did not converge
    ttl_remaining=0,  # TTL exhausted
    ...
)

final_answer = execute_phase_e(...)

# Final answer indicates TTL exhaustion
assert final_answer.ttl_exhausted == True
assert "TTL exhausted" in final_answer.answer_text or final_answer.notes
```

## Contract Guarantees

### Input Validation
- PhaseEInput is validated against its Pydantic model before synthesis
- Required fields must be present
- Field types must match model definitions
- Timestamps must be valid ISO format

### Output Guarantees
- FinalAnswer is always produced, even in degraded conditions
- answer_text is always non-empty
- If synthesis fails, degraded answer is produced with error indication
- Output is validated against FinalAnswer model before returning

### Degraded Mode Handling
- Phase E produces final_answer even when:
  - TTL is exhausted
  - Execution did not converge
  - Execution results are incomplete
  - Errors occurred during execution
- Degraded answers include appropriate metadata indicating conditions

### Integration Guarantees
- Phase E is invoked after C-loop completes, regardless of Phase D execution
- Phase E receives complete final state from execution
- FinalAnswer is attached to execution result returned by engine
- Phase E does not modify execution state (read-only operation)

## Implementation Notes

- Phase E uses ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER prompts from registry
- Synthesis prompts are registered with PhaseEInput as input model and FinalAnswer as output model
- LLM response is validated against FinalAnswer model before returning
- If validation fails, degraded answer is produced with available data and error indication
- Phase E does not perform presentation-layer work (Layer 2/3 concerns are out of scope)
