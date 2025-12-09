# Quickstart Guide: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Date**: 2025-12-07  
**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Phase**: 1 - Design

## Overview

This guide provides a quick introduction to using the prompt infrastructure and Phase E synthesis in Aeon. It demonstrates how to use the prompt registry, validate prompt outputs, and integrate Phase E into the orchestration flow.

## Prerequisites

- Python 3.11+
- pydantic>=2.0.0
- Existing Aeon codebase with orchestration engine

## Basic Usage

### 1. Using the Prompt Registry

```python
from aeon.prompts.registry import PromptRegistry, PromptId, PlanGenerationInput

# Initialize prompt registry (typically done once at startup)
registry = PromptRegistry()

# Create input data for a prompt
input_data = PlanGenerationInput(
    request="Build a web application",
    goal="Create a simple web app with user authentication",
    context={}
)

# Retrieve and render the prompt
prompt = registry.get_prompt(PromptId.PLAN_GENERATION_USER, input_data)
print(prompt)
```

### 2. Validating Prompt Outputs

```python
from aeon.prompts.registry import PromptRegistry, PromptId, PlanGenerationOutput

registry = PromptRegistry()

# LLM response (could be string, dict with "text" key, markdown code block, etc.)
llm_response = '{"plan": {"goal": "Build web app", "steps": [{"step_id": "1", "description": "Setup project"}]}}'

# Validate output against output model
try:
    output = registry.validate_output(
        PromptId.PLAN_GENERATION_USER,
        llm_response,
        PlanGenerationOutput
    )
    print(f"Validated plan: {output.plan.goal}")
except JSONExtractionError as e:
    print(f"Failed to extract JSON: {e.message}")
    print(f"Methods attempted: {e.extraction_methods_attempted}")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### 3. Handling Different LLM Response Formats

The `validate_output()` method handles multiple response formats automatically:

```python
# Format 1: Dictionary with "text" key
response1 = {"text": '{"plan": {"goal": "Build app"}}'}

# Format 2: Markdown code block
response2 = "Here's the plan:\n```json\n{\"plan\": {\"goal\": \"Build app\"}}\n```"

# Format 3: Embedded JSON in text
response3 = "The plan is: {\"plan\": {\"goal\": \"Build app\"}}"

# Format 4: Raw JSON string
response4 = '{"plan": {"goal": "Build app"}}'

# All formats work the same way
output = registry.validate_output(
    PromptId.PLAN_GENERATION_USER,
    response1,  # or response2, response3, response4
    PlanGenerationOutput
)
```

### 4. Using Phase E Synthesis

```python
from aeon.orchestration.phases import execute_phase_e, PhaseEInput
from aeon.prompts.registry import PromptRegistry
from aeon.llm.interface import LLMAdapter
from datetime import datetime

# Initialize components
llm_adapter = LLMAdapter(...)  # Your LLM adapter
prompt_registry = PromptRegistry()

# Build PhaseEInput from execution state
phase_e_input = PhaseEInput(
    request="Build a web application",
    correlation_id="abc123",
    execution_start_timestamp=datetime.now(),
    convergence_status="converged",
    total_passes=3,
    total_refinements=1,
    ttl_remaining=10,
    plan_state={"goal": "Build web app", "steps": [...]},
    execution_results={"step_1": "completed", "step_2": "completed"},
    convergence_assessment={"converged": True, "confidence": 0.95},
    execution_passes=[...],  # List of execution passes
    semantic_validation={"valid": True},
    task_profile={"complexity": "medium"}
)

# Execute Phase E
final_answer = execute_phase_e(phase_e_input, llm_adapter, prompt_registry)

# Access final answer
print(f"Answer: {final_answer.answer_text}")
print(f"Confidence: {final_answer.confidence}")
if final_answer.ttl_exhausted:
    print("⚠️  Time limit reached")
```

### 5. Handling Degraded FinalAnswer

Phase E produces degraded answers when execution state is incomplete:

```python
# PhaseEInput with missing optional fields
phase_e_input = PhaseEInput(
    request="Build a web application",
    correlation_id="abc123",
    execution_start_timestamp=datetime.now(),
    convergence_status="not_converged",
    total_passes=0,  # Zero passes scenario
    total_refinements=0,
    ttl_remaining=0,
    # Optional fields are None
    plan_state=None,
    execution_results=None,
    convergence_assessment=None,
    execution_passes=None,
    semantic_validation=None,
    task_profile=None,
)

# Phase E still executes and produces degraded answer
final_answer = execute_phase_e(phase_e_input, llm_adapter, prompt_registry)

# Check for degradation
if final_answer.metadata.get("degraded"):
    print(f"Degraded answer: {final_answer.answer_text}")
    print(f"Missing fields: {final_answer.metadata.get('missing_fields', [])}")
    print(f"Reason: {final_answer.metadata.get('reason')}")
```

### 6. Integrating Phase E in OrchestrationEngine

```python
# In OrchestrationEngine.run_multipass(), after _execute_phase_c_loop returns
converged, task_profile = self._execute_phase_c_loop(...)

# Build PhaseEInput from execution state
phase_e_input = PhaseEInput(
    request=request,
    correlation_id=execution_context.correlation_id,
    execution_start_timestamp=execution_context.execution_start_timestamp,
    convergence_status="converged" if converged else "not_converged",
    total_passes=len(execution_passes),
    total_refinements=sum(1 for p in execution_passes if hasattr(p, 'refinement_changes') and p.refinement_changes),
    ttl_remaining=state.ttl_remaining,
    plan_state=state.plan.model_dump() if state.plan else None,
    execution_results=get_execution_results_from_passes(execution_passes),
    convergence_assessment=get_convergence_assessment_from_passes(execution_passes),
    execution_passes=[p.model_dump() for p in execution_passes] if execution_passes else None,
    semantic_validation=get_semantic_validation_from_passes(execution_passes),
    task_profile=task_profile.model_dump() if task_profile else None,
)

# Execute Phase E
from aeon.orchestration.phases import execute_phase_e
final_answer = execute_phase_e(phase_e_input, self.llm, prompt_registry)

# Attach to execution result
execution_result = build_execution_result(...)
execution_result["final_answer"] = final_answer.model_dump()
```

## Testing Scenarios

### Level 1 Prompt Tests (Unit Tests)

Test prompt infrastructure components in isolation:

```python
# Test 1: Model instantiation
def test_plan_generation_input_validation():
    input_data = PlanGenerationInput(
        request="Build app",
        goal="Create web app",
        context={}
    )
    assert input_data.request == "Build app"

# Test 2: Prompt rendering
def test_prompt_rendering():
    registry = PromptRegistry()
    input_data = PlanGenerationInput(request="Build app", goal="Create app", context={})
    prompt = registry.get_prompt(PromptId.PLAN_GENERATION_USER, input_data)
    assert "Build app" in prompt
    assert "Create app" in prompt

# Test 3: Output model validation
def test_output_validation():
    registry = PromptRegistry()
    valid_json = '{"plan": {"goal": "Build app", "steps": []}}'
    output = registry.validate_output(
        PromptId.PLAN_GENERATION_USER,
        valid_json,
        PlanGenerationOutput
    )
    assert output.plan.goal == "Build app"

# Test 4: Invariant enforcement
def test_location_invariant():
    # Automated search for inline prompts should return zero matches
    assert search_inline_prompts() == 0

def test_schema_invariant():
    # Every PromptId should have an input model
    for prompt_id in PromptId:
        assert has_input_model(prompt_id)

def test_registration_invariant():
    # Every PromptId should have a registry entry
    registry = PromptRegistry()
    for prompt_id in PromptId:
        assert registry.has_prompt(prompt_id)
```

### Phase E Integration Tests

Test Phase E with mocked LLM adapter:

```python
# Test 1: Successful synthesis with complete data
def test_phase_e_complete_data():
    phase_e_input = PhaseEInput(
        request="Build app",
        correlation_id="test123",
        execution_start_timestamp=datetime.now(),
        convergence_status="converged",
        total_passes=3,
        total_refinements=1,
        ttl_remaining=10,
        plan_state={"goal": "Build app"},
        execution_results={"step_1": "completed"},
        convergence_assessment={"converged": True},
        execution_passes=[{"pass_number": 1}],
        semantic_validation={"valid": True},
        task_profile={"complexity": "medium"}
    )
    
    # Mock LLM adapter to return valid FinalAnswer JSON
    mock_llm = MockLLMAdapter(return_value='{"answer_text": "Successfully built app", "confidence": 0.95}')
    registry = PromptRegistry()
    
    final_answer = execute_phase_e(phase_e_input, mock_llm, registry)
    assert final_answer.answer_text == "Successfully built app"
    assert final_answer.confidence == 0.95
    assert not final_answer.metadata.get("degraded")

# Test 2: TTL expiration scenario
def test_phase_e_ttl_expiration():
    phase_e_input = PhaseEInput(
        request="Build app",
        correlation_id="test123",
        execution_start_timestamp=datetime.now(),
        convergence_status="not_converged",
        total_passes=2,
        total_refinements=0,
        ttl_remaining=0,  # TTL exhausted
        # ... other fields
    )
    
    # Mock LLM adapter to return degraded FinalAnswer
    mock_llm = MockLLMAdapter(return_value='{"answer_text": "TTL expired", "ttl_exhausted": true, "confidence": 0.5}')
    registry = PromptRegistry()
    
    final_answer = execute_phase_e(phase_e_input, mock_llm, registry)
    assert final_answer.ttl_exhausted is True
    assert "TTL" in final_answer.answer_text or "time limit" in final_answer.answer_text.lower()

# Test 3: Incomplete data scenario
def test_phase_e_incomplete_data():
    phase_e_input = PhaseEInput(
        request="Build app",
        correlation_id="test123",
        execution_start_timestamp=datetime.now(),
        convergence_status="not_converged",
        total_passes=1,
        total_refinements=0,
        ttl_remaining=5,
        # Missing optional fields
        plan_state=None,
        execution_results=None,
        convergence_assessment=None,
        execution_passes=None,
        semantic_validation=None,
        task_profile=None,
    )
    
    # Mock LLM adapter to return degraded FinalAnswer
    mock_llm = MockLLMAdapter(return_value='{"answer_text": "Insufficient data", "metadata": {"degraded": true, "missing_fields": ["execution_results"]}}')
    registry = PromptRegistry()
    
    final_answer = execute_phase_e(phase_e_input, mock_llm, registry)
    assert final_answer.metadata.get("degraded") is True
    assert "execution_results" in final_answer.metadata.get("missing_fields", [])
    assert len(final_answer.answer_text) > 0  # Must explain situation
```

## Common Patterns

### Pattern 1: Extracting Prompts from Existing Code

When migrating inline prompts to the registry:

1. Identify the prompt string in the code
2. Determine the PromptId (or create new one if needed)
3. Define input/output models (if JSON-producing)
4. Add PromptDefinition to registry
5. Replace inline prompt with `registry.get_prompt(PromptId.X, input_data)`

### Pattern 2: Handling JSON Extraction Errors

```python
try:
    output = registry.validate_output(prompt_id, llm_response, output_model)
except JSONExtractionError as e:
    # JSON extraction failed - cannot proceed
    logger.error(f"Failed to extract JSON: {e.message}")
    logger.error(f"Methods attempted: {e.extraction_methods_attempted}")
    # Do not attempt supervisor repair (per spec)
    raise
except ValidationError as e:
    # JSON extracted but validation failed - may attempt repair
    logger.warning(f"Validation failed: {e}")
    # May route to supervisor for repair
```

### Pattern 3: Degraded FinalAnswer Handling

Always check for degradation when displaying FinalAnswer:

```python
final_answer = execute_phase_e(phase_e_input, llm_adapter, registry)

if final_answer.metadata.get("degraded"):
    # Show degradation warning
    print("⚠️  Answer may be incomplete due to missing execution data")
    if final_answer.metadata.get("missing_fields"):
        print(f"Missing: {', '.join(final_answer.metadata['missing_fields'])}")

# Always display answer_text (it explains the situation)
print(f"Answer: {final_answer.answer_text}")
```

## Next Steps

- Review the [data model](./data-model.md) for complete entity definitions
- Review the [API contracts](./contracts/interfaces.md) for detailed interface specifications
- Review the [research decisions](./research.md) for technology choices
- See the [implementation plan](./plan.md) for architecture details
