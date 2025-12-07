# Quickstart: Prompt Infrastructure & Phase E

**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Date**: 2025-12-07

## Overview

This document provides quickstart examples and test scenarios for the prompt infrastructure system and Phase E answer synthesis.

## Test Scenarios

### Scenario 1: Prompt Registry Lookup

**Goal**: Verify prompt registry can retrieve and render prompts with input validation.

**Steps**:
1. Import prompt registry and prompt identifiers
2. Create input data conforming to prompt's input model
3. Retrieve and render prompt
4. Verify rendered prompt contains expected content

**Example**:
```python
from aeon.prompts.registry import get_prompt, PromptId
from aeon.prompts.registry import PlanGenerationInput

# Create input data
input_data = PlanGenerationInput(
    request="Create a plan to deploy a web application",
    tool_registry={
        "calculator": {
            "name": "calculator",
            "description": "Perform calculations"
        }
    }
)

# Retrieve and render prompt
prompt = get_prompt(PromptId.PLAN_GENERATION_USER, input_data)

# Verify prompt contains request
assert "deploy a web application" in prompt.lower()
assert "calculator" in prompt.lower()
```

**Expected Result**: Prompt is successfully retrieved and rendered with input data.

### Scenario 2: Input Validation Failure

**Goal**: Verify prompt registry rejects invalid input data.

**Steps**:
1. Create input data with missing required fields
2. Attempt to retrieve prompt
3. Verify ValidationError is raised

**Example**:
```python
from aeon.prompts.registry import get_prompt, PromptId
from aeon.prompts.registry import PlanGenerationInput
from pydantic import ValidationError

# Create invalid input (missing required field)
try:
    input_data = PlanGenerationInput(
        # request field missing
        tool_registry={}
    )
    prompt = get_prompt(PromptId.PLAN_GENERATION_USER, input_data)
    assert False, "Should have raised ValidationError"
except ValidationError as e:
    # Verify error message indicates missing field
    assert "request" in str(e).lower()
```

**Expected Result**: ValidationError is raised with clear message about missing required field.

### Scenario 3: Output Validation for JSON Prompts

**Goal**: Verify output validation works for prompts with output models.

**Steps**:
1. Retrieve prompt with output model
2. Get LLM response
3. Validate response against output model
4. Verify validated output can be used

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId
from aeon.prompts.registry import ConvergenceAssessmentInput

registry = PromptRegistry()

# Create input and get prompt
input_data = ConvergenceAssessmentInput(...)
prompt = registry.get_prompt(PromptId.CONVERGENCE_ASSESSMENT_USER, input_data)

# Get LLM response (simulated)
llm_response = '{"converged": true, "completeness_score": 0.9, ...}'

# Validate output
output = registry.validate_output(
    PromptId.CONVERGENCE_ASSESSMENT_USER,
    llm_response
)

# Use validated output
assert output.converged == True
assert 0.0 <= output.completeness_score <= 1.0
```

**Expected Result**: LLM response is validated against output model and can be used type-safely.

### Scenario 4: Output Validation Failure

**Goal**: Verify output validation rejects malformed LLM responses.

**Steps**:
1. Retrieve prompt with output model
2. Get malformed LLM response
3. Attempt to validate response
4. Verify ValidationError is raised

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId
from pydantic import ValidationError

registry = PromptRegistry()

# Get malformed LLM response
llm_response = '{"converged": "yes"}'  # Wrong type (should be boolean)

# Attempt to validate
try:
    output = registry.validate_output(
        PromptId.CONVERGENCE_ASSESSMENT_USER,
        llm_response
    )
    assert False, "Should have raised ValidationError"
except ValidationError as e:
    # Verify error message indicates type mismatch
    assert "converged" in str(e).lower()
```

**Expected Result**: ValidationError is raised with clear message about invalid field type.

### Scenario 5: Phase E Successful Synthesis

**Goal**: Verify Phase E produces final answer from successful execution.

**Steps**:
1. Execute request through A→B→C→D cycle
2. Collect final execution state
3. Invoke Phase E
4. Verify FinalAnswer is produced with synthesized text

**Example**:
```python
from aeon.orchestration.engine import OrchestrationEngine
from aeon.orchestration.phases import execute_phase_e, PhaseEInput

# Execute request (simplified)
engine = OrchestrationEngine(...)
execution_result = engine.run_multipass(
    request="Calculate 2 + 2",
    plan=None,
    execution_context=context,
    state=state,
    ttl=10000,
    execute_step_fn=execute_step
)

# Phase E is automatically invoked and final_answer is attached
assert "final_answer" in execution_result
final_answer = execution_result["final_answer"]

# Verify final answer structure
assert "answer_text" in final_answer
assert len(final_answer["answer_text"]) > 0
assert final_answer.get("confidence") is not None
```

**Expected Result**: FinalAnswer is produced with synthesized answer text and metadata.

### Scenario 6: Phase E with TTL Expiration

**Goal**: Verify Phase E produces final answer even when TTL is exhausted.

**Steps**:
1. Execute request that exhausts TTL
2. Verify execution terminates due to TTL expiration
3. Verify Phase E still produces final answer
4. Verify final answer indicates TTL exhaustion

**Example**:
```python
from aeon.orchestration.engine import OrchestrationEngine
from aeon.exceptions import TTLExpiredError

# Execute with low TTL
engine = OrchestrationEngine(...)
try:
    execution_result = engine.run_multipass(
        request="Complex multi-step task",
        plan=None,
        execution_context=context,
        state=state,
        ttl=100,  # Very low TTL
        execute_step_fn=execute_step
    )
except TTLExpiredError:
    # TTL expired, but Phase E should still produce answer
    pass

# Verify final answer indicates TTL exhaustion
assert execution_result.get("final_answer") is not None
final_answer = execution_result["final_answer"]
assert final_answer.get("ttl_exhausted") == True
assert "ttl" in final_answer["answer_text"].lower() or "timeout" in final_answer["answer_text"].lower()
```

**Expected Result**: FinalAnswer is produced indicating TTL exhaustion while synthesizing available results.

### Scenario 7: Phase E with Incomplete Data

**Goal**: Verify Phase E handles incomplete execution state gracefully.

**Steps**:
1. Create PhaseEInput with missing optional fields
2. Invoke Phase E
3. Verify FinalAnswer is still produced
4. Verify metadata indicates missing fields

**Example**:
```python
from aeon.orchestration.phases import execute_phase_e, PhaseEInput

# Create PhaseEInput with missing optional fields
phase_e_input = PhaseEInput(
    request="Test request",
    execution_results=[],
    plan_state={},
    convergence_assessment={},
    # execution_passes=None (optional)
    # semantic_validation=None (optional)
    correlation_id="test123",
    execution_start_timestamp="2025-01-27T10:00:00Z",
    convergence_status=False,
    total_passes=0,
    total_refinements=0,
    ttl_remaining=0
)

# Execute Phase E
final_answer = execute_phase_e(
    phase_e_input=phase_e_input,
    llm_adapter=llm_adapter,
    prompt_registry=prompt_registry
)

# Verify answer is produced
assert final_answer.answer_text is not None
assert len(final_answer.answer_text) > 0

# Verify metadata indicates incomplete data
if final_answer.metadata:
    assert "incomplete" in final_answer.metadata or "partial" in final_answer.metadata
```

**Expected Result**: FinalAnswer is produced with available data, metadata indicates missing fields.

### Scenario 8: Invariant Enforcement - Location Invariant

**Goal**: Verify no inline prompts exist outside the registry.

**Steps**:
1. Search codebase for inline prompt strings
2. Verify zero matches found
3. Verify all prompts are retrieved from registry

**Example**:
```python
import re
import os

# Search for common prompt patterns
prompt_patterns = [
    r'prompt\s*=\s*["\']',
    r'f["\'].*Generate.*plan',
    r'You are.*assistant',
]

inline_prompts_found = []
for root, dirs, files in os.walk('aeon'):
    # Skip prompts directory (registry is allowed)
    if 'prompts' in root:
        continue
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                for pattern in prompt_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        inline_prompts_found.append((filepath, pattern))

# Verify no inline prompts found
assert len(inline_prompts_found) == 0, f"Found inline prompts: {inline_prompts_found}"
```

**Expected Result**: Zero inline prompts found outside the registry.

### Scenario 9: Invariant Enforcement - Schema Invariant

**Goal**: Verify all prompts have typed input models.

**Steps**:
1. List all prompts in registry
2. Verify each prompt has an input model
3. Verify JSON-producing prompts have output models

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId

registry = PromptRegistry()

# List all prompts
all_prompts = registry.list_prompts()

# Verify each prompt has input model
for prompt_id in all_prompts:
    prompt_def = registry._get_definition(prompt_id)
    assert prompt_def.input_model is not None, f"{prompt_id} missing input model"
    
    # Verify JSON-producing prompts have output models
    if prompt_id in JSON_PRODUCING_PROMPTS:
        assert prompt_def.output_model is not None, f"{prompt_id} missing output model"
```

**Expected Result**: All prompts have input models; JSON-producing prompts have output models.

### Scenario 10: Invariant Enforcement - Registration Invariant

**Goal**: Verify every PromptId has a corresponding registry entry.

**Steps**:
1. List all PromptId enum values
2. Verify each PromptId has a registry entry
3. Verify registry lookup succeeds for all PromptIds

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId

registry = PromptRegistry()

# Get all PromptId enum values
all_prompt_ids = list(PromptId)

# Verify each has registry entry
for prompt_id in all_prompt_ids:
    try:
        # Attempt to get prompt (will raise if not found)
        # Use minimal input for testing
        test_input = create_minimal_input(prompt_id)
        prompt = registry.get_prompt(prompt_id, test_input)
        assert prompt is not None
    except PromptNotFoundError:
        assert False, f"{prompt_id} not found in registry"
```

**Expected Result**: All PromptId values have corresponding registry entries.

## Integration Test Scenarios

### Integration Test 1: End-to-End Prompt Usage

**Goal**: Verify prompts work correctly in actual execution flow.

**Steps**:
1. Execute a request through the full orchestration flow
2. Verify prompts are retrieved from registry (not inline)
3. Verify prompts render correctly with execution state
4. Verify execution completes successfully

**Expected Result**: Execution completes using prompts from registry.

### Integration Test 2: Phase E Integration

**Goal**: Verify Phase E integrates correctly with execution flow.

**Steps**:
1. Execute a request through A→B→C→D cycle
2. Verify Phase E is invoked at C-loop exit
3. Verify FinalAnswer is attached to execution result
4. Verify FinalAnswer contains synthesized text

**Expected Result**: Phase E produces FinalAnswer and attaches it to execution result.

### Integration Test 3: Prompt Contract Changes

**Goal**: Verify prompt contract changes propagate correctly.

**Steps**:
1. Update a prompt's input model (add optional field)
2. Verify existing code still works (backward compatible)
3. Update code to use new field
4. Verify new field is used correctly

**Expected Result**: Contract changes apply immediately to all usages.

## Performance Test Scenarios

### Performance Test 1: Prompt Registry Lookup

**Goal**: Verify prompt registry lookups are fast (O(1)).

**Steps**:
1. Measure time for prompt registry lookup
2. Verify lookup time is < 1ms
3. Verify lookup time does not increase with registry size

**Expected Result**: Prompt registry lookups are fast and constant-time.

### Performance Test 2: Prompt Rendering

**Goal**: Verify prompt rendering does not add significant latency.

**Steps**:
1. Measure time for prompt rendering
2. Verify rendering time is < 10ms
3. Compare with LLM call time (rendering should be negligible)

**Expected Result**: Prompt rendering adds minimal overhead compared to LLM calls.

## Error Handling Test Scenarios

### Error Test 1: Missing Prompt

**Goal**: Verify error handling when prompt is not found.

**Steps**:
1. Attempt to retrieve non-existent prompt
2. Verify PromptNotFoundError is raised
3. Verify error message is clear

**Expected Result**: Clear error message when prompt not found.

### Error Test 2: Invalid Input

**Goal**: Verify error handling when input is invalid.

**Steps**:
1. Attempt to retrieve prompt with invalid input
2. Verify ValidationError is raised
3. Verify error message indicates which fields are invalid

**Expected Result**: Clear validation error messages.

### Error Test 3: Synthesis Failure

**Goal**: Verify Phase E handles synthesis failures gracefully.

**Steps**:
1. Simulate LLM error during synthesis
2. Verify degraded FinalAnswer is produced
3. Verify error indication in metadata

**Expected Result**: Degraded answer produced with error indication.

## Usage Examples

### Example 1: Using Prompt Registry in New Module

```python
from aeon.prompts.registry import get_prompt, PromptId
from aeon.prompts.registry import MyPromptInput

def my_function(request: str, context: dict):
    # Create input data
    input_data = MyPromptInput(
        request=request,
        context=context,
        additional_field="value"
    )
    
    # Get prompt from registry
    prompt = get_prompt(PromptId.MY_PROMPT, input_data)
    
    # Use with LLM
    response = llm_adapter.generate(prompt=prompt)
    return response
```

### Example 2: Adding New Prompt to Registry

```python
from aeon.prompts.registry import PromptId, PromptDefinition, PromptRegistry
from aeon.prompts.registry import PromptInput, PromptOutput
from pydantic import BaseModel

# Define input model
class MyNewPromptInput(PromptInput):
    request: str
    context: dict

# Define output model (if JSON-producing)
class MyNewPromptOutput(PromptOutput):
    result: str
    confidence: float

# Define prompt template
def render_my_prompt(input_data: MyNewPromptInput) -> str:
    return f"""
    Process this request: {input_data.request}
    
    Context: {input_data.context}
    """

# Register prompt
registry = PromptRegistry()
registry.register(
    PromptDefinition(
        prompt_id=PromptId.MY_NEW_PROMPT,
        template="...",
        input_model=MyNewPromptInput,
        output_model=MyNewPromptOutput,  # Optional
        render_fn=render_my_prompt
    )
)
```

### Example 3: Using Phase E Directly

```python
from aeon.orchestration.phases import execute_phase_e, PhaseEInput
from aeon.prompts.registry import PromptRegistry

# Build PhaseEInput from execution state
phase_e_input = PhaseEInput(
    request="User's original request",
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
    prompt_registry=PromptRegistry()
)

# Use final answer
print(f"Answer: {final_answer.answer_text}")
print(f"Confidence: {final_answer.confidence}")
if final_answer.used_step_ids:
    print(f"Used steps: {final_answer.used_step_ids}")
```

## Next Steps

1. **Implementation**: Follow tasks.md to implement prompt infrastructure
2. **Testing**: Run test scenarios to verify implementation
3. **Integration**: Integrate prompt registry into existing modules
4. **Phase E**: Implement and integrate Phase E synthesis
5. **Validation**: Run invariant tests to ensure compliance
