# Data Model: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Date**: 2025-12-07  
**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Phase**: 1 - Design

## Entities

### PromptId

Enumeration of all unique prompt identifiers used throughout the system. Each identifier maps to exactly one PromptDefinition.

**Values** (from spec FR-005):
- `PLAN_GENERATION_SYSTEM` - System prompt for plan generation
- `PLAN_GENERATION_USER` - User prompt for plan generation
- `REASONING_STEP_SYSTEM` - System prompt for reasoning steps
- `REASONING_STEP_USER` - User prompt for reasoning steps
- `VALIDATION_SEMANTIC_SYSTEM` - System prompt for semantic validation
- `VALIDATION_SEMANTIC_USER` - User prompt for semantic validation
- `CONVERGENCE_ASSESSMENT_SYSTEM` - System prompt for convergence assessment
- `CONVERGENCE_ASSESSMENT_USER` - User prompt for convergence assessment
- `TASKPROFILE_INFERENCE_SYSTEM` - System prompt for task profile inference
- `TASKPROFILE_INFERENCE_USER` - User prompt for task profile inference
- `TASKPROFILE_UPDATE_SYSTEM` - System prompt for task profile update
- `TASKPROFILE_UPDATE_USER` - User prompt for task profile update
- `RECURSIVE_PLAN_GENERATION_USER` - User prompt for recursive plan generation
- `RECURSIVE_SUBPLAN_GENERATION_USER` - User prompt for recursive subplan generation
- `RECURSIVE_REFINEMENT_SYSTEM` - System prompt for recursive refinement
- `RECURSIVE_REFINEMENT_USER` - User prompt for recursive refinement
- `SUPERVISOR_REPAIR_SYSTEM` - System prompt for supervisor repair
- `SUPERVISOR_REPAIR_JSON_USER` - User prompt for supervisor JSON repair
- `SUPERVISOR_REPAIR_TOOLCALL_USER` - User prompt for supervisor tool call repair
- `SUPERVISOR_REPAIR_PLAN_USER` - User prompt for supervisor plan repair
- `SUPERVISOR_REPAIR_MISSINGTOOL_USER` - User prompt for supervisor missing tool repair
- `ANSWER_SYNTHESIS_SYSTEM` - System prompt for answer synthesis
- `ANSWER_SYNTHESIS_USER` - User prompt for answer synthesis

**Validation Rules**:
- Each PromptId must have exactly one corresponding PromptDefinition in PromptRegistry
- PromptId values are immutable (enum constants)

**Relationships**:
- Maps to PromptDefinition (1:1)

### PromptDefinition

Object containing a prompt's template, input model (required), output model (optional for non-JSON prompts), and rendering function. Defines the contract for prompt usage.

**Fields**:
- `prompt_id` (PromptId, required): Unique identifier for this prompt
- `template` (str, required): Prompt template string (may contain f-string placeholders)
- `input_model` (Type[BaseModel], required): Pydantic model class for input validation
- `output_model` (Optional[Type[BaseModel]], optional): Pydantic model class for output validation (only for JSON-producing prompts)
- `render_fn` (Callable, required): Function that renders template with input data (uses f-strings with Pydantic model field access)

**Validation Rules**:
- `input_model` must be a Pydantic BaseModel subclass
- `output_model` must be a Pydantic BaseModel subclass if present (None for non-JSON prompts)
- `template` must be a valid Python f-string (if placeholders are used)
- `render_fn` must accept input_model instance and return str

**State Transitions**:
- Created: PromptDefinition registered in PromptRegistry
- Updated: Template, input_model, or output_model modified (changes apply immediately)
- Retrieved: PromptDefinition accessed via PromptRegistry.get_prompt()

**Relationships**:
- Referenced by PromptId (1:1)
- Contains input_model (1:1)
- Contains output_model (0:1, optional)

### PromptRegistry

Central repository containing all prompt definitions, accessible by PromptId. Contains PromptDefinition objects with input/output models and rendering utilities.

**Fields**:
- `_definitions` (Dict[PromptId, PromptDefinition], private): Internal dictionary mapping PromptId to PromptDefinition

**Methods**:
- `get_prompt(prompt_id: PromptId, input_data: BaseModel) -> str`: Retrieve and render prompt with input data
- `validate_output(prompt_id: PromptId, llm_response: Union[str, Dict[str, Any]], output_model: Optional[Type[BaseModel]]) -> BaseModel`: Extract JSON from LLM response and validate against output model

**Validation Rules**:
- Every PromptId must have a corresponding PromptDefinition (Registration Invariant)
- Input data must validate against prompt's input_model before rendering
- Output data (for JSON prompts) must validate against prompt's output_model after extraction

**State Transitions**:
- Initialized: PromptRegistry created with all PromptDefinitions registered
- Retrieved: Prompt accessed via get_prompt()
- Validated: Output validated via validate_output()

**Relationships**:
- Contains PromptDefinition objects (1:N, one per PromptId)

### PromptInput (Base Class)

Base class for all prompt input models. Each prompt defines its own input model extending this base, specifying required fields and validation rules.

**Fields**:
- Base class only; concrete subclasses define specific fields

**Validation Rules**:
- All concrete PromptInput subclasses must be Pydantic BaseModel subclasses
- Required fields must be specified with non-Optional type hints
- Optional fields must use Optional[] type hints

**Relationships**:
- Extended by concrete input models (e.g., PlanGenerationInput, AnswerSynthesisInput)

### PromptOutput (Base Class)

Base class for all prompt output models. Only JSON-producing prompts define output models extending this base.

**Fields**:
- Base class only; concrete subclasses define specific fields

**Validation Rules**:
- All concrete PromptOutput subclasses must be Pydantic BaseModel subclasses
- Only JSON-producing prompts define output models (per spec FR-010, FR-011)

**Relationships**:
- Extended by concrete output models (e.g., PlanGenerationOutput, FinalAnswerOutput)

### JSONExtractionError

Domain-specific exception raised by `validate_output()` when no valid JSON can be extracted from an LLM response.

**Fields**:
- `message` (str, required): Error message describing the extraction failure
- `extraction_methods_attempted` (List[str], required): List of extraction methods that were tried (e.g., ["dictionary_text_key", "markdown_code_blocks", "embedded_json", "direct_parsing"])
- `prompt_id` (PromptId, optional): PromptId that was being validated (if available)

**Validation Rules**:
- Must be raised when all extraction methods fail (dictionary "text" key, markdown code blocks, embedded JSON, direct parsing)
- Must NOT be raised when JSON extraction succeeds but validation fails (ValidationError is raised instead)

**Relationships**:
- Raised by PromptRegistry.validate_output() when extraction fails

### PhaseEInput

Input model for Phase E synthesis, defined in `aeon/orchestration/phases.py` using Pydantic BaseModel with explicit Optional[] type hints.

**Fields**:
- `request` (str, required): Original user request that initiated execution
- `correlation_id` (str, required): Correlation ID for execution tracking
- `execution_start_timestamp` (datetime, required): Timestamp when execution started
- `convergence_status` (str, required): Convergence status ("converged", "not_converged", "ttl_expired")
- `total_passes` (int, required): Total number of execution passes (must be >= 0, must accept 0)
- `total_refinements` (int, required): Total number of plan refinements (must be >= 0, must accept 0)
- `ttl_remaining` (int, required): TTL remaining at execution end (must be >= 0)
- `plan_state` (Optional[Dict[str, Any]], optional): Plan state at execution end (may be None)
- `execution_results` (Optional[Dict[str, Any]], optional): Execution results (may be None)
- `convergence_assessment` (Optional[Dict[str, Any]], optional): Convergence assessment (may be None)
- `execution_passes` (Optional[List[Dict[str, Any]]], optional): List of execution passes (may be None)
- `semantic_validation` (Optional[Dict[str, Any]], optional): Semantic validation results (may be None)
- `task_profile` (Optional[Dict[str, Any]], optional): Task profile (may be None)

**Validation Rules**:
- Required fields must not be None
- Optional fields must use Optional[] type hints and may be None
- `total_passes` and `total_refinements` must be >= 0 (must accept 0 for zero passes scenario)
- `ttl_remaining` must be >= 0
- PhaseEInput MUST accept None values for optional fields and MUST NOT raise validation errors when optional fields are missing

**State Transitions**:
- Created: PhaseEInput built from execution state in OrchestrationEngine.run_multipass()
- Passed: PhaseEInput passed to execute_phase_e()
- Processed: PhaseEInput used to generate synthesis prompt

**Relationships**:
- Converted to AnswerSynthesisInput for prompt registry
- Used by execute_phase_e() to produce FinalAnswer

### FinalAnswer

Output model for Phase E synthesis, defined in `aeon/orchestration/phases.py` using Pydantic BaseModel with explicit Optional[] type hints.

**Fields**:
- `answer_text` (str, required): Synthesized answer text (must never be None or empty, minimum length 1, must explain the situation even in degraded mode)
- `confidence` (Optional[float], optional): Confidence level (range 0.0-1.0 if present)
- `used_step_ids` (Optional[List[str]], optional): List of step IDs used in synthesis (may be empty list)
- `notes` (Optional[str], optional): Additional notes (may be empty string)
- `ttl_exhausted` (Optional[bool], optional): Whether TTL was exhausted
- `metadata` (Dict[str, Any], required): Metadata dictionary (must never be None, may be empty dict, used to indicate missing/incomplete fields in degraded mode with structure: {"missing_fields": List[str], "degraded": bool, "reason": str, ...})

**Validation Rules**:
- `answer_text` must never be None or empty (minimum length 1)
- `answer_text` must explain the situation even in degraded mode
- `confidence` must be in range 0.0-1.0 if present
- `metadata` must never be None (may be empty dict)
- Degraded FinalAnswer MUST use metadata to indicate which PhaseEInput fields were missing or incomplete (e.g., {"missing_fields": ["execution_results"], "degraded": True, "reason": "incomplete_state"})
- Degraded FinalAnswer MUST always pass Pydantic validation regardless of state completeness
- FinalAnswer MUST NOT contain fields beyond the defined schema (no speculative fields allowed)

**State Transitions**:
- Created: FinalAnswer produced by execute_phase_e()
- Serialized: FinalAnswer serialized to dict for attachment to execution result
- Attached: FinalAnswer attached to execution result under key "final_answer"

**Relationships**:
- Produced by execute_phase_e() from PhaseEInput
- Attached to execution result in OrchestrationEngine.run_multipass()
- Displayed by CLI command `aeon execute`

### AnswerSynthesisInput

Input model for answer synthesis prompts (ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER), derived from PhaseEInput.

**Fields**:
- Same fields as PhaseEInput (all fields from PhaseEInput are included)

**Validation Rules**:
- Same validation rules as PhaseEInput
- Used specifically for prompt registry rendering

**Relationships**:
- Derived from PhaseEInput
- Used by PromptRegistry.get_prompt() for ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER

### FinalAnswerOutput

Output model for answer synthesis prompts, maps to FinalAnswer.

**Fields**:
- Same fields as FinalAnswer (all fields from FinalAnswer are included)

**Validation Rules**:
- Same validation rules as FinalAnswer
- Used specifically for prompt registry output validation

**Relationships**:
- Maps to FinalAnswer (1:1)
- Used by PromptRegistry.validate_output() for ANSWER_SYNTHESIS_USER

## Entity Relationships Diagram

```
PromptId (enum)
└── maps to → PromptDefinition (1:1)

PromptDefinition
├── contains → input_model (PromptInput subclass, 1:1)
├── contains → output_model (PromptOutput subclass, 0:1, optional)
└── stored in → PromptRegistry (1:1)

PromptRegistry
├── contains → PromptDefinition objects (1:N)
├── uses → PromptInput (for input validation)
└── uses → PromptOutput (for output validation, optional)

PhaseEInput
├── converted to → AnswerSynthesisInput (for prompt rendering)
└── used by → execute_phase_e() → FinalAnswer

FinalAnswer
├── maps to → FinalAnswerOutput (for prompt validation)
└── attached to → execution result (under key "final_answer")

JSONExtractionError
└── raised by → PromptRegistry.validate_output() (when extraction fails)
```

## Validation Rules Summary

### Location Invariant
- No inline prompts exist outside the registry (verified by automated search)

### Schema Invariant
- Every prompt has a typed input model (required)
- JSON-producing prompts have typed output models (required)
- Non-JSON prompts do not have output models (optional)

### Registration Invariant
- Every PromptId has a corresponding entry in PromptRegistry (verified by automated tests)
