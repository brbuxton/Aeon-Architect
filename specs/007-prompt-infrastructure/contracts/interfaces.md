# API Contracts: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Date**: 2025-12-07  
**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Phase**: 1 - Design

## Prompt Registry Interface

### PromptRegistry Class

**Location**: `aeon/prompts/registry.py`

**Purpose**: Central repository for all prompt definitions with schema-backed contracts.

#### Method: `get_prompt(prompt_id: PromptId, input_data: BaseModel) -> str`

Retrieve and render a prompt with input data.

**Parameters**:
- `prompt_id` (PromptId, required): Unique identifier for the prompt
- `input_data` (BaseModel, required): Input data instance that validates against the prompt's input model

**Returns**:
- `str`: Rendered prompt string with input data populated

**Raises**:
- `PromptNotFoundError`: If prompt_id does not exist in registry
- `ValidationError`: If input_data does not validate against prompt's input model
- `RenderingError`: If prompt template rendering fails (e.g., missing field in template)

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId, PlanGenerationInput

registry = PromptRegistry()
input_data = PlanGenerationInput(request="Build a web app", goal="Create a simple web application")
prompt = registry.get_prompt(PromptId.PLAN_GENERATION_USER, input_data)
```

#### Method: `validate_output(prompt_id: PromptId, llm_response: Union[str, Dict[str, Any]], output_model: Optional[Type[BaseModel]]) -> BaseModel`

Extract JSON from LLM response and validate against output model.

**Parameters**:
- `prompt_id` (PromptId, required): Unique identifier for the prompt
- `llm_response` (Union[str, Dict[str, Any]], required): LLM response (raw string or dictionary with "text" key)
- `output_model` (Optional[Type[BaseModel]], optional): Output model class (None for non-JSON prompts)

**Returns**:
- `BaseModel`: Validated output model instance

**Raises**:
- `JSONExtractionError`: If no valid JSON can be extracted from response (includes context about which extraction methods were attempted)
- `ValidationError`: If JSON extraction succeeds but validation against output model fails (includes Pydantic validation error messages)

**Extraction Priority Order**:
1. Dictionary "text" key extraction (if llm_response is dict, extract value from "text" key)
2. Markdown code block extraction (extract JSON from first complete ```json ... ``` or ``` ... ``` block)
3. Embedded JSON extraction (use brace matching to find first complete JSON object)
4. Direct JSON parsing (attempt to parse entire response as JSON)

**Example**:
```python
from aeon.prompts.registry import PromptRegistry, PromptId, PlanGenerationOutput

registry = PromptRegistry()
llm_response = '{"plan": {"goal": "Build web app", "steps": []}}'
output = registry.validate_output(
    PromptId.PLAN_GENERATION_USER,
    llm_response,
    PlanGenerationOutput
)
```

### PromptId Enum

**Location**: `aeon/prompts/registry.py`

**Purpose**: Enumeration of all unique prompt identifiers.

**Values**: See data-model.md for complete list of PromptId values.

**Usage**:
```python
from aeon.prompts.registry import PromptId

# Use PromptId enum values
prompt_id = PromptId.PLAN_GENERATION_USER
```

### Exceptions

#### PromptNotFoundError

Raised when a prompt_id does not exist in the registry.

**Fields**:
- `message` (str): Error message
- `prompt_id` (PromptId): PromptId that was not found

#### RenderingError

Raised when prompt template rendering fails.

**Fields**:
- `message` (str): Error message
- `prompt_id` (PromptId): PromptId that failed to render
- `error` (Exception): Underlying error

#### JSONExtractionError

Raised when no valid JSON can be extracted from LLM response.

**Fields**:
- `message` (str): Error message describing the extraction failure
- `extraction_methods_attempted` (List[str]): List of extraction methods that were tried
- `prompt_id` (PromptId, optional): PromptId that was being validated

#### NoOutputModelError

Raised when validate_output() is called for a prompt that has no output model (non-JSON prompt).

**Fields**:
- `message` (str): Error message
- `prompt_id` (PromptId): PromptId that has no output model

## Phase E Interface

### Function: `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer`

Execute Phase E (Answer Synthesis) to produce a final answer from execution state.

**Location**: `aeon/orchestration/phases.py`

**Parameters**:
- `phase_e_input` (PhaseEInput, required): Input model containing execution state (required and optional fields)
- `llm_adapter` (LLMAdapter, required): LLM adapter for synthesis LLM calls
- `prompt_registry` (PromptRegistry, required): Prompt registry for synthesis prompts

**Returns**:
- `FinalAnswer`: Synthesized final answer (always valid, may be degraded if state is incomplete)

**Raises**:
- `PromptNotFoundError`: If synthesis prompts are not found in registry (handled gracefully, produces degraded answer)
- `RenderingError`: If prompt rendering fails (handled gracefully, produces degraded answer)
- `LLMError`: If LLM call fails (handled gracefully, produces degraded answer with error indication)

**Behavior**:
- MUST execute unconditionally even when execution state is missing or incomplete
- MUST NOT raise exceptions for missing or incomplete upstream artifacts
- MUST produce a degraded FinalAnswer using available data when state is incomplete
- MUST indicate missing fields in metadata["missing_fields"]
- MUST ensure answer_text is never None or empty (explains situation even in degraded mode)

**Example**:
```python
from aeon.orchestration.phases import execute_phase_e, PhaseEInput
from aeon.prompts.registry import PromptRegistry
from aeon.llm.interface import LLMAdapter

phase_e_input = PhaseEInput(
    request="Build a web app",
    correlation_id="abc123",
    execution_start_timestamp=datetime.now(),
    convergence_status="converged",
    total_passes=3,
    total_refinements=1,
    ttl_remaining=10,
    plan_state={"goal": "Build web app", "steps": [...]},
    execution_results={"step_1": "completed", ...},
    # ... other optional fields
)

final_answer = execute_phase_e(phase_e_input, llm_adapter, prompt_registry)
```

### PhaseEInput Model

**Location**: `aeon/orchestration/phases.py`

**Purpose**: Input model for Phase E synthesis.

**Fields**: See data-model.md for complete field list.

**Validation**:
- Required fields must not be None
- Optional fields may be None (must use Optional[] type hints)
- total_passes and total_refinements must be >= 0 (must accept 0)

### FinalAnswer Model

**Location**: `aeon/orchestration/phases.py`

**Purpose**: Output model for Phase E synthesis.

**Fields**: See data-model.md for complete field list.

**Validation**:
- answer_text must never be None or empty (minimum length 1)
- metadata must never be None (may be empty dict)
- Degraded FinalAnswer must conform exactly to FinalAnswer schema

## Integration Points

### OrchestrationEngine.run_multipass() Integration

**Location**: `aeon/orchestration/engine.py`

**Integration Point**: After `_execute_phase_c_loop` returns, before building final execution result.

**Code Pattern**:
```python
# After _execute_phase_c_loop returns
converged, task_profile = self._execute_phase_c_loop(...)

# Build PhaseEInput from execution state
phase_e_input = PhaseEInput(
    request=request,
    correlation_id=execution_context.correlation_id,
    execution_start_timestamp=execution_context.execution_start_timestamp,
    convergence_status="converged" if converged else "not_converged",
    total_passes=len(execution_passes),
    total_refinements=sum(1 for p in execution_passes if p.refinement_changes),
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

### CLI Integration

**Location**: `aeon/cli/main.py` (or equivalent CLI module)

**Integration Point**: Display FinalAnswer when available in execution result.

**Code Pattern**:
```python
# In CLI command handler
if "final_answer" in execution_result:
    final_answer = FinalAnswer(**execution_result["final_answer"])
    
    if json_output:
        # JSON format
        print(json.dumps({"final_answer": final_answer.model_dump()}, indent=2))
    else:
        # Human-readable format
        print(f"Answer: {final_answer.answer_text}")
        if final_answer.confidence is not None:
            print(f"Confidence: {final_answer.confidence}")
        if final_answer.ttl_exhausted:
            print("⚠️  Time limit reached")
        if final_answer.notes:
            print(f"Note: {final_answer.notes}")
        if final_answer.metadata:
            print(f"Metadata: {final_answer.metadata}")
```

## Contract Invariants

### Location Invariant
- No inline prompts exist outside the registry (verified by automated search)

### Schema Invariant
- Every prompt has a typed input model (required)
- JSON-producing prompts have typed output models (required)

### Registration Invariant
- Every PromptId has a corresponding entry in PromptRegistry (verified by automated tests)

### Phase E Invariant
- Phase E executes unconditionally after C-loop terminates
- Phase E never raises exceptions for missing/incomplete state
- FinalAnswer always conforms to FinalAnswer schema (even when degraded)

