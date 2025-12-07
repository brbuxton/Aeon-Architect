# Data Model: Prompt Infrastructure & Phase E

**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Date**: 2025-12-07

## Overview

This document defines the data models for the prompt infrastructure system, including prompt registry entities, prompt contracts, and Phase E synthesis models.

## Core Entities

### PromptRegistry

**Purpose**: Central repository containing all prompt definitions, accessible by PromptId.

**Location**: `aeon/prompts/registry.py`

**Structure**:
```python
class PromptRegistry:
    """Central registry for all system prompts."""
    
    _registry: Dict[PromptId, PromptDefinition]
    
    def get_prompt(
        self, 
        prompt_id: PromptId, 
        input_data: PromptInput
    ) -> str:
        """Retrieve and render a prompt by identifier."""
        # 1. Validate input_data against prompt's input model
        # 2. Render prompt template with input_data
        # 3. Return rendered prompt string
```

**Relationships**:
- Contains: `Dict[PromptId, PromptDefinition]`
- Used by: All modules that need prompts (kernel, supervisor, phases, validation, convergence, adaptive)

**Validation Rules**:
- Every PromptId must have a corresponding PromptDefinition (Registration Invariant)
- Input data must validate against prompt's input model before rendering
- Registry must be initialized with all prompts at module load time

### PromptId

**Purpose**: Enumeration of all unique prompt identifiers used throughout the system.

**Location**: `aeon/prompts/registry.py`

**Structure**:
```python
from enum import Enum

class PromptId(Enum):

    # -----------------------------
    # Plan Generation
    # -----------------------------
    PLAN_GENERATION_SYSTEM = "plan_generation_system"
    PLAN_GENERATION_USER = "plan_generation_user"

    # -----------------------------
    # Execution Reasoning
    # -----------------------------
    REASONING_STEP_SYSTEM = "reasoning_step_system"
    REASONING_STEP_USER = "reasoning_step_user"

    # -----------------------------
    # Semantic Validation
    # -----------------------------
    VALIDATION_SEMANTIC_SYSTEM = "validation_semantic_system"
    VALIDATION_SEMANTIC_USER = "validation_semantic_user"

    # -----------------------------
    # Convergence Assessment
    # -----------------------------
    CONVERGENCE_ASSESSMENT_SYSTEM = "convergence_assessment_system"
    CONVERGENCE_ASSSESSMENT_USER = "convergence_assessment_user"

    # -----------------------------
    # Task Profile Inference / Update
    # -----------------------------
    TASKPROFILE_INFERENCE_SYSTEM = "taskprofile_inference_system"
    TASKPROFILE_INFERENCE_USER = "taskprofile_inference_user"
    TASKPROFILE_UPDATE_SYSTEM = "taskprofile_update_system"
    TASKPROFILE_UPDATE_USER = "taskprofile_update_user"

    # -----------------------------
    # Recursive Planning / Refinement
    # -----------------------------
    RECURSIVE_PLAN_GENERATION_USER = "recursive_plan_generation_user"
    RECURSIVE_SUBPLAN_GENERATION_USER = "recursive_subplan_generation_user"
    RECURSIVE_REFINEMENT_SYSTEM = "recursive_refinement_system"
    RECURSIVE_REFINEMENT_USER = "recursive_refinement_user"

    # -----------------------------
    # Supervisor Repair
    # -----------------------------
    SUPERVISOR_REPAIR_SYSTEM = "supervisor_repair_system"
    SUPERVISOR_REPAIR_JSON_USER = "supervisor_repair_json_user"
    SUPERVISOR_REPAIR_TOOLCALL_USER = "supervisor_repair_toolcall_user"
    SUPERVISOR_REPAIR_PLAN_USER = "supervisor_repair_plan_user"
    SUPERVISOR_REPAIR_MISSINGTOOL_USER = "supervisor_repair_missingtool_user"

    # -----------------------------
    # Phase E — Answer Synthesis
    # -----------------------------
    ANSWER_SYNTHESIS_SYSTEM = "answer_synthesis_system"
    ANSWER_SYNTHESIS_USER = "answer_synthesis_user"

```

**Relationships**:
- Maps to: `PromptDefinition` (one-to-one)
- Used by: All modules that retrieve prompts from registry

**Validation Rules**:
- Each PromptId must be unique
- Each PromptId must have a corresponding PromptDefinition in registry
- PromptId values are string enums for JSON serialization compatibility

### PromptDefinition

**Purpose**: Object containing a prompt's template, input model (required), output model (optional), and rendering function.

**Location**: `aeon/prompts/registry.py`

**Structure**:
```python
from typing import Type, Optional, Callable
from pydantic import BaseModel

class PromptDefinition:
    """Definition of a prompt with its contract."""
    
    prompt_id: PromptId
    template: str  # Prompt template string (f-string compatible)
    input_model: Type[PromptInput]  # Required: Pydantic model for input validation
    output_model: Optional[Type[PromptOutput]] = None  # Optional: Pydantic model for output validation
    render_fn: Callable[[PromptInput], str]  # Rendering function
    
    def render(self, input_data: PromptInput) -> str:
        """Render prompt template with input data."""
        # Validate input_data against input_model
        # Execute render_fn with validated input
        # Return rendered prompt string
```

**Relationships**:
- Contains: `input_model`, `output_model` (optional), `template`, `render_fn`
- Belongs to: `PromptRegistry` (many-to-one)

**Validation Rules**:
- `input_model` is required (Schema Invariant)
- `output_model` is optional (only for JSON-producing prompts)
- `template` must be a valid f-string template
- `render_fn` must accept `PromptInput` and return `str`
- Template must not reference fields not in `input_model`

### PromptInput

**Purpose**: Base class for all prompt input models. Each prompt defines its own input model extending this base.

**Location**: `aeon/prompts/registry.py`

**Structure**:
```python
from pydantic import BaseModel

class PromptInput(BaseModel):
    """Base class for prompt input models."""
    pass

# Example: Plan generation input
class PlanGenerationInput(PromptInput):
    """Input model for plan generation prompts."""
    request: str
    tool_registry: Optional[Dict[str, Any]] = None  # Serialized tool registry

# Example: Reasoning input
class ReasoningInput(PromptInput):
    """Input model for reasoning prompts."""
    step_description: str
    request: str
    plan_goal: Optional[str] = None
    pass_number: int
    phase: str
    ttl_remaining: int
    correlation_id: str
    step_index: Optional[int] = None
    total_steps: Optional[int] = None
    incoming_context: Optional[str] = None
    memory_context: Optional[Dict[str, Any]] = None
```

**Relationships**:
- Extended by: Specific input models for each prompt type
- Used by: `PromptDefinition.render()`

**Validation Rules**:
- All fields must be typed
- Required fields must not have default values
- Optional fields use `Optional[Type]` or `Type | None`
- Field descriptions should be provided for clarity

### PromptOutput

**Purpose**: Base class for all prompt output models. Only JSON-producing prompts define output models extending this base.

**Location**: `aeon/prompts/registry.py`

**Structure**:
```python
from pydantic import BaseModel
from typing import Optional

class PromptOutput(BaseModel):
    """Base class for prompt output models."""
    pass

# Example: Convergence assessment output
class ConvergenceAssessmentOutput(PromptOutput):
    """Output model for convergence assessment prompts."""
    converged: bool
    completeness_score: float
    coherence_score: float
    consistency_alignment: Dict[str, bool]
    reasoning: str
    confidence: float

# Example: TaskProfile inference output
class TaskProfileInferenceOutput(PromptOutput):
    """Output model for TaskProfile inference prompts."""
    reasoning_depth: int
    information_sufficiency: float
    expected_tool_usage: str
    output_breadth: str
    confidence_requirement: float
```

**Relationships**:
- Extended by: Specific output models for JSON-producing prompts
- Used by: `PromptDefinition` (optional field)

**Validation Rules**:
- Only required for prompts that produce structured JSON
- All fields must be typed
- Output models validate LLM responses after generation
- Validation failures should provide clear error messages

## Phase E Entities

### PhaseEInput

**Purpose**: Input model for Phase E synthesis, containing complete final execution state.

**Location**: `aeon/orchestration/phases.py`

**Structure**:
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

**Relationships**:
- Used by: `execute_phase_e()` method
- Contains: All final execution state needed for synthesis

**Validation Rules**:
- `request` is required
- `execution_results` is required (may be empty list)
- `plan_state` is required
- `convergence_assessment` is required
- `correlation_id` is required
- `execution_start_timestamp` must be valid ISO format
- `convergence_status` is required boolean
- `total_passes` must be >= 0
- `total_refinements` must be >= 0
- `ttl_remaining` must be >= 0

### FinalAnswer

**Purpose**: Output model for Phase E synthesis, containing the synthesized final answer.

**Location**: `aeon/orchestration/phases.py`

**Structure**:
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

**Relationships**:
- Produced by: `execute_phase_e()` method
- Attached to: Execution result returned by engine

**Validation Rules**:
- `answer_text` is required (non-empty string)
- `confidence` must be between 0.0 and 1.0 if provided
- `used_step_ids` must contain valid step IDs if provided
- `metadata` can contain arbitrary key-value pairs

## State Transitions

### Prompt Registry Lifecycle

1. **Initialization**: Registry is populated with all PromptDefinitions at module load time
2. **Lookup**: Module requests prompt by PromptId with input data
3. **Validation**: Input data validated against prompt's input model
4. **Rendering**: Prompt template rendered with validated input data
5. **Usage**: Rendered prompt sent to LLM
6. **Output Validation** (if output_model exists): LLM response validated against output model

### Phase E Execution Flow

1. **C-Loop Completion**: `_execute_phase_c_loop()` returns convergence status and task_profile
2. **State Collection**: Final execution state collected into PhaseEInput model
3. **Phase E Invocation**: `execute_phase_e(phase_e_input)` called
4. **Prompt Retrieval**: ANSWER_SYNTHESIS prompts retrieved from registry
5. **Synthesis**: LLM called with synthesis prompts and execution state
6. **Output Validation**: LLM response validated against FinalAnswer model
7. **Result Attachment**: FinalAnswer attached to execution result

## Invariants

### Location Invariant
- **Rule**: No inline prompt strings exist outside the registry
- **Enforcement**: Automated search for prompt strings in codebase (zero matches expected)
- **Scope**: All modules (kernel, supervisor, phases, tools, validation, convergence, adaptive)

### Schema Invariant
- **Rule**: Every prompt has a typed input model; JSON-producing prompts must have typed output models
- **Enforcement**: PromptRegistry initialization validates all prompts have input models
- **Scope**: All PromptDefinitions in registry

### Registration Invariant
- **Rule**: Every PromptId has a corresponding entry in PromptRegistry
- **Enforcement**: PromptRegistry.get_prompt() raises error if PromptId not found
- **Scope**: All PromptId enum values

## Validation Rules Summary

### Prompt Input Validation
- Input data must be instance of prompt's input model type
- Required fields must be present
- Field types must match model definitions
- Validation occurs before prompt rendering

### Prompt Output Validation
- Only applies to prompts with output_model defined
- LLM response must be valid JSON
- JSON must parse to prompt's output model
- Validation occurs after LLM response received

### Phase E Input Validation
- PhaseEInput must contain all required fields
- Field types must match model definitions
- Timestamps must be valid ISO format
- Numeric fields must be non-negative

### FinalAnswer Validation
- answer_text must be non-empty string
- confidence must be in range [0.0, 1.0] if provided
- used_step_ids must contain valid step IDs if provided
