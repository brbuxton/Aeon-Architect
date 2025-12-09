"""Prompt Registry - Centralized prompt management with schema-backed contracts."""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from aeon.exceptions import AeonError, ErrorSeverity


# ============================================================================
# Base Exception Classes (T004)
# ============================================================================

class PromptNotFoundError(AeonError):
    """Raised when a prompt identifier is not found in the registry."""

    ERROR_CODE: str = "AEON.PROMPT.001"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def __init__(self, prompt_id: str, message: Optional[str] = None):
        """Initialize PromptNotFoundError."""
        self.prompt_id = prompt_id
        error_message = message or f"Prompt not found: {prompt_id}"
        super().__init__(error_message)


class NoOutputModelError(AeonError):
    """Raised when attempting to validate output for a prompt without an output model."""

    ERROR_CODE: str = "AEON.PROMPT.002"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def __init__(self, prompt_id: str, message: Optional[str] = None):
        """Initialize NoOutputModelError."""
        self.prompt_id = prompt_id
        error_message = message or f"Prompt {prompt_id} does not have an output model"
        super().__init__(error_message)


class RenderingError(AeonError):
    """Raised when prompt rendering fails."""

    ERROR_CODE: str = "AEON.PROMPT.003"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def __init__(self, prompt_id: str, reason: str, message: Optional[str] = None):
        """Initialize RenderingError."""
        self.prompt_id = prompt_id
        self.reason = reason
        error_message = message or f"Failed to render prompt {prompt_id}: {reason}"
        super().__init__(error_message)


class JSONExtractionError(AeonError):
    """Raised when JSON extraction from LLM response fails."""

    ERROR_CODE: str = "AEON.PROMPT.004"
    SEVERITY: ErrorSeverity = ErrorSeverity.ERROR

    def __init__(
        self,
        message: str,
        extraction_methods_attempted: List[str],
        prompt_id: Optional[str] = None,
    ):
        """
        Initialize JSONExtractionError.

        Args:
            message: Error message describing the extraction failure
            extraction_methods_attempted: List of extraction methods that were tried
            prompt_id: Optional prompt identifier that was being validated
        """
        self.extraction_methods_attempted = extraction_methods_attempted
        self.prompt_id = prompt_id
        super().__init__(message)


# ============================================================================
# Base Input/Output Models (T005, T006)
# ============================================================================

class PromptInput(BaseModel):
    """Base class for all prompt input models."""

    model_config = {"frozen": False}


class PromptOutput(BaseModel):
    """Base class for all prompt output models."""

    model_config = {"frozen": False}


# ============================================================================
# PromptId Enum (T011)
# ============================================================================

class PromptId(str, Enum):
    """Enumeration of all unique prompt identifiers."""

    # Plan Generation
    PLAN_GENERATION_SYSTEM = "PLAN_GENERATION_SYSTEM"
    PLAN_GENERATION_USER = "PLAN_GENERATION_USER"
    REASONING_STEP_SYSTEM = "REASONING_STEP_SYSTEM"
    REASONING_STEP_USER = "REASONING_STEP_USER"
    
    # Validation
    VALIDATION_SEMANTIC_SYSTEM = "VALIDATION_SEMANTIC_SYSTEM"
    VALIDATION_SEMANTIC_USER = "VALIDATION_SEMANTIC_USER"
    
    # Convergence Assessment
    CONVERGENCE_ASSESSMENT_SYSTEM = "CONVERGENCE_ASSESSMENT_SYSTEM"
    CONVERGENCE_ASSESSMENT_USER = "CONVERGENCE_ASSESSMENT_USER"
    
    # TaskProfile
    TASKPROFILE_INFERENCE_SYSTEM = "TASKPROFILE_INFERENCE_SYSTEM"
    TASKPROFILE_INFERENCE_USER = "TASKPROFILE_INFERENCE_USER"
    TASKPROFILE_UPDATE_SYSTEM = "TASKPROFILE_UPDATE_SYSTEM"
    TASKPROFILE_UPDATE_USER = "TASKPROFILE_UPDATE_USER"
    
    # Recursive Planning
    RECURSIVE_PLAN_GENERATION_USER = "RECURSIVE_PLAN_GENERATION_USER"
    RECURSIVE_SUBPLAN_GENERATION_USER = "RECURSIVE_SUBPLAN_GENERATION_USER"
    RECURSIVE_REFINEMENT_SYSTEM = "RECURSIVE_REFINEMENT_SYSTEM"
    RECURSIVE_REFINEMENT_USER = "RECURSIVE_REFINEMENT_USER"
    
    # Supervisor Repair
    SUPERVISOR_REPAIR_SYSTEM = "SUPERVISOR_REPAIR_SYSTEM"
    SUPERVISOR_REPAIR_JSON_USER = "SUPERVISOR_REPAIR_JSON_USER"
    SUPERVISOR_REPAIR_TOOLCALL_USER = "SUPERVISOR_REPAIR_TOOLCALL_USER"
    SUPERVISOR_REPAIR_PLAN_USER = "SUPERVISOR_REPAIR_PLAN_USER"
    SUPERVISOR_REPAIR_MISSINGTOOL_USER = "SUPERVISOR_REPAIR_MISSINGTOOL_USER"
    
    # Answer Synthesis (Phase E)
    ANSWER_SYNTHESIS_SYSTEM = "ANSWER_SYNTHESIS_SYSTEM"
    ANSWER_SYNTHESIS_USER = "ANSWER_SYNTHESIS_USER"


# ============================================================================
# PromptDefinition Class (T012)
# ============================================================================

class PromptDefinition:
    """Definition of a prompt with its contract."""

    def __init__(
        self,
        prompt_id: PromptId,
        template: str,
        input_model: Type[PromptInput],
        output_model: Optional[Type[PromptOutput]] = None,
        render_fn: Optional[Callable[[PromptInput], str]] = None,
    ):
        """
        Initialize PromptDefinition.

        Args:
            prompt_id: Unique prompt identifier
            template: Prompt template string (may contain f-string placeholders)
            input_model: Pydantic model class for input validation
            output_model: Optional Pydantic model class for output validation
            render_fn: Optional custom rendering function. If None, uses default f-string rendering.
        """
        self.prompt_id = prompt_id
        self.template = template
        self.input_model = input_model
        self.output_model = output_model
        self.render_fn = render_fn or self._default_render

    def _default_render(self, input_data: PromptInput) -> str:
        """
        Default rendering function using f-string with Pydantic model field access.

        Templates should use format string syntax like: "Goal: {goal}" or "Goal: {input.goal}".
        The function supports both {field} and {input.field} syntax.

        Args:
            input_data: Input data conforming to input_model

        Returns:
            Rendered prompt string
        """
        try:
            # Validate input_data against input_model
            if isinstance(input_data, BaseModel):
                validated_input = self.input_model.model_validate(input_data.model_dump())
            else:
                validated_input = self.input_model.model_validate(input_data)
            
            # Get model fields as dict
            input_dict = validated_input.model_dump()
            
            # Support both {field} and {input.field} syntax
            # First, replace {input.field} with {field} for .format() compatibility
            template = self.template
            for key in input_dict.keys():
                template = template.replace(f"{{input.{key}}}", f"{{{key}}}")
            
            # Render using .format() with model fields
            result = template.format(**input_dict)
            
            return result
        except PydanticValidationError as e:
            raise RenderingError(
                prompt_id=self.prompt_id.value,
                reason=f"Input validation failed: {e}",
            ) from e
        except (KeyError, AttributeError) as e:
            raise RenderingError(
                prompt_id=self.prompt_id.value,
                reason=f"Template rendering failed: {e}. Missing field in template or input data.",
            ) from e

    def render(self, input_data: PromptInput) -> str:
        """
        Render prompt template with input data.

        Args:
            input_data: Input data conforming to input_model

        Returns:
            Rendered prompt string

        Raises:
            RenderingError: If template rendering fails
        """
        return self.render_fn(input_data)


# ============================================================================
# PromptRegistry Class (T013-T015)
# ============================================================================

class PromptRegistry:
    """Central registry for all system prompts."""

    def __init__(self):
        """Initialize registry with empty definitions."""
        self._registry: Dict[PromptId, PromptDefinition] = {}

    def register(self, definition: PromptDefinition) -> None:
        """
        Register a prompt definition.

        Args:
            definition: PromptDefinition to register
        """
        self._registry[definition.prompt_id] = definition

    def get_prompt(
        self,
        prompt_id: PromptId,
        input_data: PromptInput,
    ) -> str:
        """
        Retrieve and render a prompt by identifier (T014).

        Args:
            prompt_id: Unique prompt identifier
            input_data: Input data conforming to prompt's input model

        Returns:
            Rendered prompt string ready for LLM consumption

        Raises:
            PromptNotFoundError: If prompt_id not found in registry
            RenderingError: If prompt rendering fails
        """
        if prompt_id not in self._registry:
            raise PromptNotFoundError(prompt_id.value)
        
        definition = self._registry[prompt_id]
        return definition.render(input_data)

    def list_prompts(self) -> List[PromptId]:
        """
        List all registered prompt identifiers (T015).

        Returns:
            List of all PromptId values in registry
        """
        return list(self._registry.keys())

    def validate_output(
        self,
        prompt_id: PromptId,
        llm_response: Union[str, Dict[str, Any]],
        output_model: Optional[Type[PromptOutput]] = None,
    ) -> PromptOutput:
        """
        Validate LLM response against prompt's output model (T054-T061).

        Implements unified JSON extraction that handles multiple LLM response formats:
        - Dictionary with "text" key (FR-013C)
        - Markdown code blocks (FR-013D)
        - Embedded JSON using brace matching (FR-013E)
        - Raw JSON string (FR-013F)

        Args:
            prompt_id: Unique prompt identifier
            llm_response: LLM response (string or dict with "text" key) (FR-013B)
            output_model: Optional output model (if None, uses prompt's output_model)

        Returns:
            Validated output model instance

        Raises:
            PromptNotFoundError: If prompt_id not found in registry
            NoOutputModelError: If prompt has no output model defined
            JSONExtractionError: If JSON extraction fails (FR-013G)
            PydanticValidationError: If validation fails (FR-013J)
        """
        import json
        import re
        
        # Check if prompt exists
        if prompt_id not in self._registry:
            raise PromptNotFoundError(prompt_id.value)
        
        definition = self._registry[prompt_id]
        
        # Determine output model
        if output_model is None:
            output_model = definition.output_model
        
        if output_model is None:
            raise NoOutputModelError(prompt_id.value)
        
        # Track extraction methods attempted (FR-013G)
        extraction_methods_attempted = []
        
        # Step 1: Extract candidate JSON string from llm_response (FR-013C)
        candidate_json_str = None
        
        if isinstance(llm_response, dict):
            extraction_methods_attempted.append("dictionary_text_key")
            if "text" not in llm_response:
                raise JSONExtractionError(
                    message="Dictionary response must contain 'text' key",
                    extraction_methods_attempted=extraction_methods_attempted,
                    prompt_id=prompt_id.value,
                )
            if not isinstance(llm_response["text"], str):
                raise JSONExtractionError(
                    message="'text' key value must be a string",
                    extraction_methods_attempted=extraction_methods_attempted,
                    prompt_id=prompt_id.value,
                )
            candidate_json_str = llm_response["text"]
        elif isinstance(llm_response, str):
            candidate_json_str = llm_response
        else:
            raise JSONExtractionError(
                message=f"llm_response must be str or dict, got {type(llm_response).__name__}",
                extraction_methods_attempted=extraction_methods_attempted,
                prompt_id=prompt_id.value,
            )
        
        # Step 2: Extract JSON from candidate string using multiple methods
        extracted_json = None
        
        # Method 1: Markdown code blocks (FR-013D)
        extraction_methods_attempted.append("markdown_code_blocks")
        code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        code_block_matches = re.findall(code_block_pattern, candidate_json_str, re.DOTALL)
        if code_block_matches:
            # Extract from first complete code block
            code_block_content = code_block_matches[0].strip()
            try:
                extracted_json = json.loads(code_block_content)
            except json.JSONDecodeError:
                pass  # Try next method
        
        # Method 2: Embedded JSON using brace matching (FR-013E)
        if extracted_json is None:
            extraction_methods_attempted.append("embedded_json")
            # Find first complete JSON object with balanced braces
            brace_count = 0
            json_start = -1
            json_end = -1
            
            for i, char in enumerate(candidate_json_str):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start >= 0:
                        json_end = i + 1
                        break
            
            if json_start >= 0 and json_end > json_start:
                json_candidate = candidate_json_str[json_start:json_end]
                try:
                    extracted_json = json.loads(json_candidate)
                except json.JSONDecodeError:
                    pass  # Try next method
        
        # Method 3: Direct JSON parsing fallback (FR-013F)
        if extracted_json is None:
            extraction_methods_attempted.append("direct_parsing")
            try:
                extracted_json = json.loads(candidate_json_str)
            except json.JSONDecodeError:
                pass  # All methods failed
        
        # Step 3: Raise JSONExtractionError if no valid JSON found (FR-013G)
        if extracted_json is None:
            raise JSONExtractionError(
                message=f"Could not extract valid JSON from LLM response. Attempted methods: {', '.join(extraction_methods_attempted)}",
                extraction_methods_attempted=extraction_methods_attempted,
                prompt_id=prompt_id.value,
            )
        
        # Step 4: Validate against output model (FR-013J)
        try:
            validated_output = output_model.model_validate(extracted_json)
            return validated_output
        except PydanticValidationError as e:
            # Raise ValidationError (not JSONExtractionError) when validation fails (FR-013J)
            # Re-raise the original error to preserve all validation error details
            # The original error already contains all validation error information
            raise


# ============================================================================
# Module-Level Convenience Function (T016)
# ============================================================================

# Global registry instance (T032) - will be initialized after all prompts are registered
_registry_instance: Optional[PromptRegistry] = None


def get_prompt(
    prompt_id: PromptId,
    input_data: PromptInput,
) -> str:
    """
    Convenience function to retrieve and render a prompt using global registry.

    Args:
        prompt_id: Unique prompt identifier
        input_data: Input data conforming to prompt's input model

    Returns:
        Rendered prompt string ready for LLM consumption

    Raises:
        PromptNotFoundError: If prompt_id not found in registry
        RenderingError: If prompt rendering fails
    """
    global _registry_instance
    if _registry_instance is None:
        _initialize_registry()
    return _registry_instance.get_prompt(prompt_id, input_data)


def get_prompt_registry() -> PromptRegistry:
    """
    Get the global prompt registry instance.
    
    Returns:
        The global PromptRegistry instance
    """
    global _registry_instance
    if _registry_instance is None:
        _initialize_registry()
    return _registry_instance


# ============================================================================
# Input Models (Basic - will be enhanced in User Story 2)
# ============================================================================

class PlanGenerationSystemInput(PromptInput):
    """Input model for plan generation system prompt (no inputs needed)."""
    pass


class PlanGenerationUserInput(PromptInput):
    """Input model for plan generation user prompt."""
    request: str = Field(..., description="Natural language request")
    tool_registry_export: Optional[str] = Field(default=None, description="Formatted tool registry export")


class ReasoningStepSystemInput(PromptInput):
    """Input model for reasoning step system prompt (no inputs needed)."""
    pass


class ReasoningStepUserInput(PromptInput):
    """Input model for reasoning step user prompt."""
    step_description: str = Field(..., description="Step description")
    phase_context: Optional[Dict[str, Any]] = Field(default=None, description="Phase context dict")
    step_index: Optional[int] = Field(default=None, description="Step index")
    total_steps: Optional[int] = Field(default=None, description="Total steps")
    incoming_context: Optional[str] = Field(default=None, description="Context from previous steps")
    memory_context: Optional[str] = Field(default=None, description="Memory context")


# Additional Input Models for other prompts

class SemanticValidationSystemInput(PromptInput):
    """Input model for semantic validation system prompt (no inputs needed)."""
    pass


class SemanticValidationUserInput(PromptInput):
    """Input model for semantic validation user prompt."""
    artifact: Dict[str, Any] = Field(..., description="Artifact to validate")
    artifact_type: str = Field(..., description="Type of artifact: plan, step, execution_artifact, cross_phase")
    tool_registry_info: Optional[str] = Field(default=None, description="Available tools info")


class ConvergenceAssessmentSystemInput(PromptInput):
    """Input model for convergence assessment system prompt (no inputs needed)."""
    pass


class ConvergenceAssessmentUserInput(PromptInput):
    """Input model for convergence assessment user prompt."""
    plan_state: Dict[str, Any] = Field(..., description="Plan state")
    execution_results: List[Dict[str, Any]] = Field(..., description="Execution results")
    semantic_validation_summary: str = Field(..., description="Semantic validation summary")
    completeness_threshold: float = Field(..., description="Completeness threshold")
    coherence_threshold: float = Field(..., description="Coherence threshold")


class TaskProfileInferenceSystemInput(PromptInput):
    """Input model for task profile inference system prompt (no inputs needed)."""
    pass


class TaskProfileInferenceUserInput(PromptInput):
    """Input model for task profile inference user prompt."""
    request: str = Field(..., description="User request")
    tool_registry_info: Optional[str] = Field(default=None, description="Available tools info")


class TaskProfileUpdateSystemInput(PromptInput):
    """Input model for task profile update system prompt (no inputs needed)."""
    pass


class TaskProfileUpdateUserInput(PromptInput):
    """Input model for task profile update user prompt."""
    current_profile: Dict[str, Any] = Field(..., description="Current task profile")
    convergence_assessment: Dict[str, Any] = Field(..., description="Convergence assessment")
    semantic_validation_issues: List[Dict[str, Any]] = Field(..., description="Semantic validation issues")
    clarity_states: List[str] = Field(..., description="Clarity states")


class RecursivePlanGenerationUserInput(PromptInput):
    """Input model for recursive plan generation user prompt."""
    task_description: str = Field(..., description="Task description")
    task_profile_context: str = Field(..., description="Task profile context")
    tool_registry_export: Optional[str] = Field(default=None, description="Tool registry export")


class RecursiveSubplanGenerationUserInput(PromptInput):
    """Input model for recursive subplan generation user prompt."""
    fragment_description: str = Field(..., description="Fragment description")
    parent_plan_context: str = Field(..., description="Parent plan context")
    tool_registry_export: Optional[str] = Field(default=None, description="Tool registry export")


class RecursiveRefinementSystemInput(PromptInput):
    """Input model for recursive refinement system prompt (no inputs needed)."""
    pass


class RecursiveRefinementUserInput(PromptInput):
    """Input model for recursive refinement user prompt."""
    current_plan: Dict[str, Any] = Field(..., description="Current plan")
    validation_issues: List[Dict[str, Any]] = Field(..., description="Validation issues")
    refinement_triggers: List[Dict[str, Any]] = Field(..., description="Refinement triggers")
    target_fragments: List[str] = Field(..., description="Target fragments")


class SupervisorRepairSystemInput(PromptInput):
    """Input model for supervisor repair system prompt (no inputs needed)."""
    pass


class SupervisorRepairJSONUserInput(PromptInput):
    """Input model for supervisor JSON repair user prompt."""
    malformed_json: str = Field(..., description="Malformed JSON string")
    expected_schema: Optional[Dict[str, Any]] = Field(default=None, description="Expected schema")


class SupervisorRepairToolCallUserInput(PromptInput):
    """Input model for supervisor tool call repair user prompt."""
    malformed_call: Dict[str, Any] = Field(..., description="Malformed tool call")
    tool_schema: Dict[str, Any] = Field(..., description="Tool schema")


class SupervisorRepairPlanUserInput(PromptInput):
    """Input model for supervisor plan repair user prompt."""
    malformed_plan: Dict[str, Any] = Field(..., description="Malformed plan")


class SupervisorRepairMissingToolUserInput(PromptInput):
    """Input model for supervisor missing tool repair user prompt."""
    step: Dict[str, Any] = Field(..., description="Step with missing tool")
    available_tools: List[Dict[str, Any]] = Field(..., description="Available tools")
    plan_goal: str = Field(..., description="Plan goal")


class AnswerSynthesisInput(PromptInput):
    """Input model for answer synthesis prompts (Phase E).
    
    Derived from PhaseEInput, contains all fields needed for synthesis.
    """
    request: str = Field(..., description="Original user request that initiated execution")
    correlation_id: str = Field(..., description="Execution correlation identifier")
    execution_start_timestamp: str = Field(..., description="ISO format timestamp of execution start")
    convergence_status: Union[bool, str] = Field(..., description="Whether execution converged (bool or string)")
    total_passes: int = Field(..., ge=0, description="Total number of execution passes (must be >= 0)")
    total_refinements: int = Field(..., ge=0, description="Total number of plan refinements (must be >= 0)")
    ttl_remaining: int = Field(..., ge=0, description="Remaining TTL tokens (must be >= 0)")
    plan_state: Optional[Dict[str, Any]] = Field(None, description="Current plan state (serialized Plan object)")
    execution_results: Optional[List[Dict[str, Any]]] = Field(None, description="List of step execution results from all passes")
    convergence_assessment: Optional[Dict[str, Any]] = Field(None, description="Convergence assessment results")
    execution_passes: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of execution pass metadata")
    semantic_validation: Optional[Dict[str, Any]] = Field(None, description="Optional semantic validation report")
    task_profile: Optional[Dict[str, Any]] = Field(None, description="Optional task profile information")


# ============================================================================
# Output Models for JSON-Producing Prompts (T046-T052)
# ============================================================================

class PlanStepOutput(PromptOutput):
    """Output model for plan step in plan generation."""
    step_id: str = Field(..., description="Unique identifier for the step")
    description: str = Field(..., description="Human-readable description")
    status: str = Field(default="pending", description="Step status")
    tool: Optional[str] = Field(default=None, description="Tool name")
    agent: Optional[str] = Field(default=None, description="Agent type")


class PlanGenerationOutput(PromptOutput):
    """Output model for plan generation prompts (T046)."""
    goal: str = Field(..., description="Plan goal")
    steps: List[PlanStepOutput] = Field(..., description="List of plan steps")


class ConvergenceAssessmentOutput(PromptOutput):
    """Output model for convergence assessment prompts (T047)."""
    converged: bool = Field(..., description="Whether convergence was achieved")
    reason_codes: List[str] = Field(default_factory=list, description="Reason codes")
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Completeness score")
    coherence_score: float = Field(..., ge=0.0, le=1.0, description="Coherence score")
    consistency_status: Dict[str, Any] = Field(default_factory=dict, description="Consistency status")
    detected_issues: List[str] = Field(default_factory=list, description="Detected issues")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskProfileInferenceOutput(PromptOutput):
    """Output model for task profile inference prompts (T048)."""
    profile_version: int = Field(default=1, ge=1, description="Profile version")
    reasoning_depth: int = Field(..., ge=1, le=5, description="Reasoning depth (1-5)")
    information_sufficiency: float = Field(..., ge=0.0, le=1.0, description="Information sufficiency")
    expected_tool_usage: str = Field(..., description="Expected tool usage level")
    output_breadth: str = Field(..., description="Output breadth")
    confidence_requirement: str = Field(..., description="Confidence requirement")
    raw_inference: str = Field(..., min_length=1, description="Raw inference explanation")


class TaskProfileUpdateOutput(PromptOutput):
    """Output model for task profile update prompts (T049)."""
    profile_version: int = Field(default=1, ge=1, description="Profile version")
    reasoning_depth: int = Field(..., ge=1, le=5, description="Reasoning depth (1-5)")
    information_sufficiency: float = Field(..., ge=0.0, le=1.0, description="Information sufficiency")
    expected_tool_usage: str = Field(..., description="Expected tool usage level")
    output_breadth: str = Field(..., description="Output breadth")
    confidence_requirement: str = Field(..., description="Confidence requirement")
    raw_inference: str = Field(..., min_length=1, description="Raw inference explanation")


class RecursiveSubplanGenerationOutput(PromptOutput):
    """Output model for recursive subplan generation prompts (T050)."""
    goal: str = Field(..., description="Subplan goal")
    steps: List[PlanStepOutput] = Field(..., description="List of subplan steps")


class RefinementActionOutput(PromptOutput):
    """Output model for refinement action in recursive refinement."""
    action_type: str = Field(..., description="Action type")
    target_step_id: Optional[str] = Field(default=None, description="Target step ID")
    target_plan_section: Optional[str] = Field(default=None, description="Target plan section")
    new_step: Optional[Dict[str, Any]] = Field(default=None, description="New step content")
    changes: Dict[str, Any] = Field(..., description="Modified content")
    reason: str = Field(..., description="Refinement reason")
    semantic_validation_input: List[Dict[str, Any]] = Field(default_factory=list, description="Validation issues")
    inconsistency_detected: bool = Field(default=False, description="Inconsistency flag")


class RecursiveRefinementOutput(PromptOutput):
    """Output model for recursive refinement prompts (T051)."""
    refinements: List[RefinementActionOutput] = Field(..., description="List of refinement actions")


class SupervisorRepairJSONOutput(PromptOutput):
    """Output model for supervisor JSON repair prompts (T052)."""
    # Generic JSON output - structure depends on what was being repaired
    # Use Dict[str, Any] to allow flexible structure
    repaired_json: Dict[str, Any] = Field(..., description="Repaired JSON structure")


class FinalAnswerOutput(PromptOutput):
    """Output model for answer synthesis prompts (Phase E).
    
    Maps to FinalAnswer model, contains synthesized answer with metadata.
    """
    answer_text: str = Field(..., min_length=1, description="Synthesized answer text (must never be None or empty)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (must never be None)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    used_step_ids: Optional[List[str]] = Field(None, description="List of step IDs that contributed to the answer")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    ttl_exhausted: Optional[bool] = Field(None, description="Whether TTL was exhausted during execution")


# ============================================================================
# Prompt Registration (T017-T023, T032)
# ============================================================================

def _initialize_registry() -> None:
    """Initialize global registry with all prompt definitions."""
    global _registry_instance
    if _registry_instance is not None:
        return
    
    _registry_instance = PromptRegistry()
    
    # Plan Generation Prompts (T017, T063)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.PLAN_GENERATION_SYSTEM,
        template="""You are a planning assistant. Generate declarative plans in JSON format.
A plan must have:
- "goal": string describing the objective
- "steps": array of step objects, each with:
  - "step_id": unique identifier (string)
  - "description": what the step does (string)
  - "status": "pending" (always pending for new plans)
  - "tool": (optional) name of registered tool for tool-based execution
  - "agent": (optional) "llm" for explicit LLM reasoning steps

IMPORTANT: Only reference tools that exist in the available tools list. Do not invent tools.
If a step requires a tool, use the "tool" field with the exact tool name from the available list.
If a step requires reasoning without a tool, use "agent": "llm".

Return only valid JSON.""",
        input_model=PlanGenerationSystemInput,
        output_model=PlanGenerationOutput,  # T063
    ))
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.PLAN_GENERATION_USER,
        template="""Generate a plan to accomplish the following request:

{request}

{tool_registry_export}Return a JSON plan with goal and steps.""",
        input_model=PlanGenerationUserInput,
        output_model=PlanGenerationOutput,  # T063
    ))
    
    # Reasoning Step Prompts (T023)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.REASONING_STEP_SYSTEM,
        template="You are a reasoning assistant. Provide clear, structured responses. Include clarity_state and handoff_to_next in your response.",
        input_model=ReasoningStepSystemInput,
    ))
    
    # Note: REASONING_STEP_USER is constructed dynamically in build_reasoning_prompt()
    # It will be handled via a custom render function when we update the code
    
    # Semantic Validation Prompts (T019)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.VALIDATION_SEMANTIC_SYSTEM,
        template="""You are a semantic validation assistant. Analyze plans, steps, and execution artifacts for quality issues.
Identify specificity problems, relevance issues, do/say mismatches, hallucinated tools, and consistency violations.
Classify issues by type and assign severity scores. Propose semantic repairs when possible.
Return structured JSON with detected issues.""",
        input_model=SemanticValidationSystemInput,
    ))
    
    # Note: VALIDATION_SEMANTIC_USER is constructed dynamically in _construct_validation_prompt()
    # It will be handled via a custom render function
    
    # Convergence Assessment Prompts (T020, T063)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.CONVERGENCE_ASSESSMENT_SYSTEM,
        template="""You are a convergence assessment assistant. Evaluate task execution for completeness, coherence, and consistency.
Assess whether the execution has converged on a complete, coherent, consistent solution.
Provide numeric scores (0.0-1.0) for completeness and coherence, and alignment status for consistency.
Return structured JSON with scores, status, and explanations.""",
        input_model=ConvergenceAssessmentSystemInput,
        output_model=ConvergenceAssessmentOutput,  # T063
    ))
    
    # Note: CONVERGENCE_ASSESSMENT_USER is constructed dynamically in _construct_convergence_prompt()
    # It will be handled via a custom render function
    
    # TaskProfile Prompts (T021, T063)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.TASKPROFILE_INFERENCE_SYSTEM,
        template="""You are a task complexity analyzer. Analyze tasks and infer their complexity characteristics.
Return only valid JSON with the required fields: reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference.""",
        input_model=TaskProfileInferenceSystemInput,
        output_model=TaskProfileInferenceOutput,  # T063
    ))
    
    # Note: TASKPROFILE_INFERENCE_USER is constructed dynamically in _construct_task_profile_prompt()
    # It will be handled via a custom render function
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.TASKPROFILE_UPDATE_SYSTEM,
        template="""You are a task complexity analyzer. Based on execution feedback (convergence failure, validation issues, blocked steps), update the TaskProfile to better reflect the actual task complexity.
Return only valid JSON with the required fields: reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference.
Adjust dimensions based on whether complexity was underestimated (increase) or overestimated (decrease).""",
        input_model=TaskProfileUpdateSystemInput,
        output_model=TaskProfileUpdateOutput,  # T063
    ))
    
    # Note: TASKPROFILE_UPDATE_USER is constructed dynamically in _construct_update_task_profile_prompt()
    # It will be handled via a custom render function
    
    # Recursive Planning Prompts (T018)
    # Note: RECURSIVE_PLAN_GENERATION_USER uses PLAN_GENERATION_USER with additional context
    # RECURSIVE_SUBPLAN_GENERATION_USER and RECURSIVE_REFINEMENT prompts are constructed dynamically
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.RECURSIVE_REFINEMENT_SYSTEM,
        template="You are a plan refinement assistant. Generate refinement actions as JSON array.",
        input_model=RecursiveRefinementSystemInput,
        output_model=RecursiveRefinementOutput,  # T063
    ))
    
    # Note: RECURSIVE_REFINEMENT_USER is constructed dynamically in refine_plan()
    # It will be handled via a custom render function
    
    # Supervisor Repair Prompts (T022)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.SUPERVISOR_REPAIR_SYSTEM,
        template="""You are a JSON repair assistant. Fix malformed JSON, tool calls, or plan structures.
Return only the corrected JSON. Do not add new fields, tools, or semantic meaning.
Your job is to correct syntax and structure only.""",
        input_model=SupervisorRepairSystemInput,
    ))
    
    def _render_json_repair_prompt(input_data: SupervisorRepairJSONUserInput) -> str:
        """Custom render function for JSON repair prompt."""
        prompt = f"Fix this malformed JSON: {input_data.malformed_json}"
        if input_data.expected_schema:
            import json
            prompt += f"\n\nExpected schema: {json.dumps(input_data.expected_schema, indent=2)}"
        prompt += "\n\nReturn only the corrected JSON, no explanation."
        return prompt
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.SUPERVISOR_REPAIR_JSON_USER,
        template="",  # Not used, custom render function handles it
        input_model=SupervisorRepairJSONUserInput,
        output_model=SupervisorRepairJSONOutput,  # T063
        render_fn=_render_json_repair_prompt,
    ))
    
    def _render_toolcall_repair_prompt(input_data: SupervisorRepairToolCallUserInput) -> str:
        """Custom render function for tool call repair prompt."""
        import json
        return f"""Fix this malformed tool call: {json.dumps(input_data.malformed_call, indent=2)}

Tool schema: {json.dumps(input_data.tool_schema, indent=2)}

Return only the corrected tool call JSON, no explanation."""
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.SUPERVISOR_REPAIR_TOOLCALL_USER,
        template="",  # Not used, custom render function handles it
        input_model=SupervisorRepairToolCallUserInput,
        render_fn=_render_toolcall_repair_prompt,
    ))
    
    def _render_plan_repair_prompt(input_data: SupervisorRepairPlanUserInput) -> str:
        """Custom render function for plan repair prompt."""
        import json
        return f"""Fix this malformed plan: {json.dumps(input_data.malformed_plan, indent=2)}

A valid plan must have:
- "goal": string
- "steps": array of step objects with "step_id", "description", "status"

Return only the corrected plan JSON, no explanation."""
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.SUPERVISOR_REPAIR_PLAN_USER,
        template="",  # Not used, custom render function handles it
        input_model=SupervisorRepairPlanUserInput,
        render_fn=_render_plan_repair_prompt,
    ))
    
    # Note: SUPERVISOR_REPAIR_MISSINGTOOL_USER is constructed dynamically in _construct_missing_tool_repair_prompt()
    # It will be handled via a custom render function
    
    # Answer Synthesis Prompts (Phase E - T074)
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.ANSWER_SYNTHESIS_SYSTEM,
        template="""You are an answer synthesis assistant. Synthesize execution results, plan state, and convergence information into a coherent final answer.

Your task is to consolidate all available execution data into a clear, structured response that addresses the original user request.

Return a JSON object with the following structure:
- answer_text (string, required): The synthesized answer text explaining the execution results
- confidence (float, optional): Confidence score between 0.0 and 1.0
- used_step_ids (array of strings, optional): List of step IDs that contributed to the answer
- notes (string, optional): Additional notes or context
- ttl_exhausted (boolean, optional): Whether TTL was exhausted during execution
- metadata (object, required): Additional metadata about the execution

If execution data is incomplete or TTL expired, indicate this in the answer_text and metadata.""",
        input_model=AnswerSynthesisInput,
    ))
    
    _registry_instance.register(PromptDefinition(
        prompt_id=PromptId.ANSWER_SYNTHESIS_USER,
        template="""Synthesize the execution results into a final answer.

Request: {request}
Correlation ID: {correlation_id}
Execution Start: {execution_start_timestamp}
Convergence Status: {convergence_status}
Total Passes: {total_passes}
Total Refinements: {total_refinements}
TTL Remaining: {ttl_remaining}

Plan State: {plan_state}
Execution Results: {execution_results}
Convergence Assessment: {convergence_assessment}
Execution Passes: {execution_passes}
Semantic Validation: {semantic_validation}
Task Profile: {task_profile}

Return a JSON object with answer_text, confidence (optional), used_step_ids (optional), notes (optional), ttl_exhausted (optional), and metadata (required).""",
        input_model=AnswerSynthesisInput,
        output_model=FinalAnswerOutput,
    ))
