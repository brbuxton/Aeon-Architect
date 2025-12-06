"""Phase orchestration logic for multi-pass execution.

This module contains the PhaseOrchestrator class that orchestrates Phase A/B/C/D
logic for multi-pass execution, extracted from the kernel to reduce LOC.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from aeon.adaptive.models import TaskProfile
    from aeon.plan.models import Plan
    from aeon.kernel.state import ExecutionContext, OrchestrationState, ExecutionPass
    from aeon.observability.logger import JSONLLogger

__all__ = [
    "PhaseOrchestrator",
    "PhaseResult",
    "PhaseTransitionContract",
    "ContextPropagationSpecification",
    "get_phase_transition_contract",
    "validate_phase_transition_contract",
    "enforce_phase_transition_contract",
    "validate_and_enforce_phase_transition",
    "get_context_propagation_specification",
    "validate_context_propagation",
    "build_llm_context",
    "execute_with_retry",
    "call_llm_with_provider_error_handling",
]


# Data model: PhaseResult
# Structured result from phase orchestration methods, enabling kernel to handle success/error cases gracefully.
# 
# Fields (as tuple return):
# - success (boolean, required): Whether the phase operation succeeded
# - result (Any, optional): Operation result (type depends on phase method)
# - error (string, optional): Error message if success is False
#
# Validation Rules:
# - If success is True, result must be present
# - If success is False, error must be present
# - Result type depends on phase method (see PhaseOrchestrator interface)

# Type aliases for phase result tuples
PhaseAResult = Tuple[bool, Tuple[Optional["TaskProfile"], int], Optional[str]]
PhaseBResult = Tuple[bool, "Plan", Optional[str]]
PhaseCExecuteResult = List[Dict[str, Any]]  # No error tuple, returns list directly
PhaseCEvaluateResult = Dict[str, Any]  # No error tuple, returns dict directly
PhaseCRefineResult = Tuple[bool, List[Dict[str, Any]], Optional[str], Optional["Plan"]]
PhaseDResult = Tuple[bool, Optional["TaskProfile"], Optional[str]]

# Legacy alias for backwards compatibility
PhaseResult = Any  # Type varies by phase method


# Phase Transition Contract Models
class FailureCondition(BaseModel):
    """A failure condition with retryability classification."""

    condition: str = Field(..., description="Human-readable description of failure condition")
    retryable: bool = Field(..., description="Whether condition is retryable")
    error_code: str = Field(..., description="Error code in format AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>")


class PhaseTransitionContract(BaseModel):
    """Explicit contract defining input requirements, output guarantees, invariants, and failure modes for a phase transition."""

    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"] = Field(..., description="Transition identifier")
    required_inputs: Dict[str, Any] = Field(..., description="Field name → validation rule mapping for required inputs")
    guaranteed_outputs: Dict[str, Any] = Field(..., description="Field name → validation rule mapping for guaranteed outputs")
    invariants: List[str] = Field(..., description="Invariant descriptions that must hold during transition")
    failure_conditions: List[FailureCondition] = Field(..., description="Failure condition → retryability classification mapping")


class ContextPropagationSpecification(BaseModel):
    """Structured specification defining, for each phase, what fields must be constructed before phase entry (must-have), what fields must be passed unchanged between phases (must-pass-unchanged), and what fields may be produced/modified only by specific phases (may-modify)."""

    phase: Literal["A", "B", "C", "D"] = Field(..., description="Phase identifier")
    must_have_fields: List[str] = Field(..., description="Required fields before phase entry")
    must_pass_unchanged_fields: List[str] = Field(..., description="Fields that must be identical across phases")
    may_modify_fields: List[str] = Field(default_factory=list, description="Fields that may be produced/modified by this phase")


# Phase Transition Contract Constants
# These contracts define explicit input requirements, output guarantees, invariants, and failure modes
# for each phase transition (A→B, B→C, C→D, D→A/B).

CONTRACT_A_TO_B = PhaseTransitionContract(
    transition_name="A→B",
    required_inputs={
        "task_profile": lambda x: x is not None,  # TaskProfile must be present
        "initial_plan": lambda x: x is not None,  # Plan must be present
        "ttl": lambda x: isinstance(x, int) and x > 0,  # TTL must be positive integer
    },
    guaranteed_outputs={
        "refined_plan": lambda x: x is not None,  # Plan must be present
    },
    invariants=[
        "correlation_id must be passed unchanged",
        "execution_start_timestamp must be passed unchanged",
    ],
    failure_conditions=[
        FailureCondition(
            condition="incomplete profile",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.A_B.001",
        ),
        FailureCondition(
            condition="malformed plan JSON",
            retryable=True,
            error_code="AEON.PHASE_TRANSITION.A_B.002",
        ),
        FailureCondition(
            condition="malformed plan structure",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.A_B.003",
        ),
    ],
)

CONTRACT_B_TO_C = PhaseTransitionContract(
    transition_name="B→C",
    required_inputs={
        "refined_plan": lambda x: x is not None,  # Plan must be present
        "refined_plan_steps": lambda x: isinstance(x, list) and len(x) > 0,  # Plan must have steps
    },
    guaranteed_outputs={
        "execution_results": lambda x: isinstance(x, list),  # Execution results must be list
    },
    invariants=[
        "correlation_id must be passed unchanged",
        "execution_start_timestamp must be passed unchanged",
    ],
    failure_conditions=[
        FailureCondition(
            condition="missing steps",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.B_C.001",
        ),
        FailureCondition(
            condition="invalid plan fragments missing required fields",
            retryable=True,
            error_code="AEON.PHASE_TRANSITION.B_C.002",
        ),
        FailureCondition(
            condition="invalid plan fragments structural invalidity",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.B_C.003",
        ),
    ],
)

CONTRACT_C_TO_D = PhaseTransitionContract(
    transition_name="C→D",
    required_inputs={
        "execution_results": lambda x: isinstance(x, list),  # Execution results must be list
        "evaluation_results": lambda x: isinstance(x, dict),  # Evaluation results must be dict
    },
    guaranteed_outputs={
        "updated_task_profile": lambda x: x is None or True,  # TaskProfile may be None or updated
    },
    invariants=[
        "correlation_id must be passed unchanged",
        "execution_start_timestamp must be passed unchanged",
    ],
    failure_conditions=[
        FailureCondition(
            condition="execution results incomplete",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.C_D.001",
        ),
        FailureCondition(
            condition="evaluation results malformed",
            retryable=True,
            error_code="AEON.PHASE_TRANSITION.C_D.002",
        ),
    ],
)

CONTRACT_D_TO_A_B = PhaseTransitionContract(
    transition_name="D→A/B",
    required_inputs={
        "task_profile": lambda x: x is not None,  # TaskProfile must be present
        "ttl_remaining": lambda x: isinstance(x, int) and x >= 0,  # TTL must be non-negative
    },
    guaranteed_outputs={
        "next_phase": lambda x: x in ("A", "B"),  # Next phase must be A or B
    },
    invariants=[
        "correlation_id must be passed unchanged",
        "execution_start_timestamp must be passed unchanged",
    ],
    failure_conditions=[
        FailureCondition(
            condition="TTL exhausted",
            retryable=False,
            error_code="AEON.PHASE_TRANSITION.D_AB.001",
        ),
        FailureCondition(
            condition="task profile update failed",
            retryable=True,
            error_code="AEON.PHASE_TRANSITION.D_AB.002",
        ),
    ],
)

# Context Propagation Specification Constants
# These specifications define required fields for each phase (must-have, must-pass-unchanged, may-modify).

CONTEXT_SPEC_PHASE_A = ContextPropagationSpecification(
    phase="A",
    must_have_fields=[
        "request",
        "pass_number",
        "phase",
        "ttl_remaining",
        "correlation_id",
        "execution_start_timestamp",
    ],
    must_pass_unchanged_fields=[
        "correlation_id",
        "execution_start_timestamp",
    ],
    may_modify_fields=[],  # Phase A produces initial context
)

CONTEXT_SPEC_PHASE_B = ContextPropagationSpecification(
    phase="B",
    must_have_fields=[
        "request",
        "task_profile",
        "initial_plan",
        "pass_number",
        "phase",
        "ttl_remaining",
        "correlation_id",
        "execution_start_timestamp",
    ],
    must_pass_unchanged_fields=[
        "correlation_id",
        "execution_start_timestamp",
    ],
    may_modify_fields=["refined_plan"],  # Phase B produces refined plan
)

CONTEXT_SPEC_PHASE_C = ContextPropagationSpecification(
    phase="C",
    must_have_fields=[
        "request",
        "task_profile",
        "refined_plan",
        "pass_number",
        "phase",
        "ttl_remaining",
        "correlation_id",
        "execution_start_timestamp",
    ],
    must_pass_unchanged_fields=[
        "correlation_id",
        "execution_start_timestamp",
    ],
    may_modify_fields=[
        "execution_results",
        "evaluation_results",
        "refinement_changes",
    ],  # Phase C produces execution and evaluation results
)

CONTEXT_SPEC_PHASE_D = ContextPropagationSpecification(
    phase="D",
    must_have_fields=[
        "request",
        "task_profile",
        "evaluation_results",
        "plan_state",
        "pass_number",
        "phase",
        "ttl_remaining",
        "correlation_id",
        "execution_start_timestamp",
    ],
    must_pass_unchanged_fields=[
        "correlation_id",
        "execution_start_timestamp",
    ],
    may_modify_fields=["task_profile"],  # Phase D may update task profile
)


# Phase Transition Contract Functions
def get_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"]
) -> PhaseTransitionContract:
    """
    Get phase transition contract for a transition.

    Args:
        transition_name: Transition identifier

    Returns:
        Phase transition contract

    Raises:
        ValueError: If transition_name is invalid
    """
    contracts = {
        "A→B": CONTRACT_A_TO_B,
        "B→C": CONTRACT_B_TO_C,
        "C→D": CONTRACT_C_TO_D,
        "D→A/B": CONTRACT_D_TO_A_B,
    }
    if transition_name not in contracts:
        raise ValueError(f"Invalid transition name: {transition_name}")
    return contracts[transition_name]


def validate_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    contract: Optional[PhaseTransitionContract] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate phase transition inputs against contract.

    Args:
        transition_name: Transition identifier
        inputs: Input dictionary to validate
        contract: Phase transition contract (if None, will be fetched)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if contract is None:
        contract = get_phase_transition_contract(transition_name)

    # Validate all required inputs are present and match validation rules
    for field_name, validation_rule in contract.required_inputs.items():
        if field_name not in inputs:
            return (False, f"Missing required input: {field_name}")
        if callable(validation_rule):
            try:
                if not validation_rule(inputs[field_name]):
                    return (False, f"Validation failed for input: {field_name}")
            except Exception as e:
                return (False, f"Validation error for input {field_name}: {str(e)}")

    return (True, None)


def enforce_phase_transition_contract(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    contract: Optional[PhaseTransitionContract] = None,
) -> Tuple[bool, Optional[str], Optional[Any]]:
    """
    Enforce phase transition contract (validate inputs and outputs).

    Args:
        transition_name: Transition identifier
        inputs: Input dictionary
        outputs: Output dictionary
        contract: Phase transition contract (if None, will be fetched)

    Returns:
        Tuple of (success, error_message, phase_transition_error)
    """
    from aeon.exceptions import PhaseTransitionError

    if contract is None:
        contract = get_phase_transition_contract(transition_name)

    # Validate inputs
    is_valid, error_message = validate_phase_transition_contract(transition_name, inputs, contract)
    if not is_valid:
        # Find matching failure condition
        failure_condition = next(
            (fc for fc in contract.failure_conditions if fc.condition in error_message.lower()),
            None,
        )
        if failure_condition:
            error = PhaseTransitionError(
                transition_name=transition_name,
                failure_condition=error_message,
                retryable=failure_condition.retryable,
            )
            return (False, error_message, error)
        else:
            # Default error for unenumerated failures
            error = PhaseTransitionError(
                transition_name=transition_name,
                failure_condition=error_message,
                retryable=False,
            )
            return (False, error_message, error)

    # Validate outputs
    for field_name, validation_rule in contract.guaranteed_outputs.items():
        if field_name not in outputs:
            return (False, f"Missing guaranteed output: {field_name}", None)
        if callable(validation_rule):
            try:
                if not validation_rule(outputs[field_name]):
                    return (False, f"Validation failed for output: {field_name}", None)
            except Exception as e:
                return (False, f"Validation error for output {field_name}: {str(e)}", None)

    return (True, None, None)


# Context Propagation Functions
def get_context_propagation_specification(
    phase: Literal["A", "B", "C", "D"]
) -> ContextPropagationSpecification:
    """
    Get context propagation specification for a phase.

    Args:
        phase: Phase identifier

    Returns:
        Context propagation specification

    Raises:
        ValueError: If phase is invalid
    """
    specs = {
        "A": CONTEXT_SPEC_PHASE_A,
        "B": CONTEXT_SPEC_PHASE_B,
        "C": CONTEXT_SPEC_PHASE_C,
        "D": CONTEXT_SPEC_PHASE_D,
    }
    if phase not in specs:
        raise ValueError(f"Invalid phase: {phase}")
    return specs[phase]


def validate_context_propagation(
    phase: Literal["A", "B", "C", "D"],
    context: Dict[str, Any],
    specification: Optional[ContextPropagationSpecification] = None,
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate context against propagation specification.

    Args:
        phase: Phase identifier
        context: Context dictionary to validate
        specification: Context propagation specification (if None, will be fetched)

    Returns:
        Tuple of (is_valid, error_message, missing_fields)
    """
    if specification is None:
        specification = get_context_propagation_specification(phase)

    missing_fields = []
    # Validate all must_have_fields are present and non-null
    for field_name in specification.must_have_fields:
        if field_name not in context or context[field_name] is None:
            missing_fields.append(field_name)

    if missing_fields:
        error_message = f"Missing required context fields: {', '.join(missing_fields)}"
        return (False, error_message, missing_fields)

    # Validate must_pass_unchanged_fields are present
    for field_name in specification.must_pass_unchanged_fields:
        if field_name not in context:
            missing_fields.append(field_name)

    if missing_fields:
        error_message = f"Missing must-pass-unchanged context fields: {', '.join(missing_fields)}"
        return (False, error_message, missing_fields)

    return (True, None, [])


def build_llm_context(
    phase: Literal["A", "B", "C", "D"],
    context: Dict[str, Any],
    specification: Optional[ContextPropagationSpecification] = None,
) -> Dict[str, Any]:
    """
    Build LLM context from context dictionary according to specification.

    Args:
        phase: Phase identifier
        context: Full context dictionary
        specification: Context propagation specification (if None, will be fetched)

    Returns:
        LLM context dictionary with only required fields

    Raises:
        ValueError: If required fields are missing or null
    """
    if specification is None:
        specification = get_context_propagation_specification(phase)

    # Validate context first
    is_valid, error_message, missing_fields = validate_context_propagation(phase, context, specification)
    if not is_valid:
        raise ValueError(error_message)

    # Extract only must_have_fields from context
    llm_context = {field_name: context[field_name] for field_name in specification.must_have_fields}

    return llm_context


def validate_and_enforce_phase_transition(
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
    contract: Optional[PhaseTransitionContract] = None,
) -> None:
    """
    Validate and enforce phase transition contract.
    
    This consolidates contract validation logic that was previously scattered
    in the orchestrator. Validates inputs and optionally enforces outputs.
    
    Args:
        transition_name: Transition identifier
        inputs: Input dictionary for the transition
        outputs: Optional output dictionary (if provided, contract is enforced)
        contract: Optional contract (will be fetched if not provided)
    
    Raises:
        PhaseTransitionError: If validation fails or contract is violated
    """
    from aeon.exceptions import PhaseTransitionError

    if contract is None:
        contract = get_phase_transition_contract(transition_name)

    # Validate inputs
    is_valid, error_message = validate_phase_transition_contract(transition_name, inputs, contract)
    if not is_valid:
        # Find matching failure condition
        failure_condition = next(
            (fc for fc in contract.failure_conditions if fc.condition.lower() in error_message.lower()),
            None,
        )
        if failure_condition:
            phase_error = PhaseTransitionError(
                transition_name=transition_name,
                failure_condition=error_message,
                retryable=failure_condition.retryable,
            )
            raise phase_error
        else:
            # Default error for unenumerated failures
            phase_error = PhaseTransitionError(
                transition_name=transition_name,
                failure_condition=error_message,
                retryable=False,
            )
            raise phase_error

    # If outputs provided, enforce contract
    if outputs is not None:
        success_contract, error_message, phase_error = enforce_phase_transition_contract(
            transition_name, inputs, outputs, contract
        )
        if not success_contract:
            if phase_error:
                raise phase_error
            else:
                phase_error = PhaseTransitionError(
                    transition_name=transition_name,
                    failure_condition=error_message or "Contract validation failed",
                    retryable=False,
                )
                raise phase_error


def execute_with_retry(
    func: Callable,
    transition_name: Literal["A→B", "B→C", "C→D", "D→A/B"],
    contract: Optional[PhaseTransitionContract] = None,
    max_retries: int = 1,
    *args,
    **kwargs,
) -> Tuple[bool, Any, Optional[str], Optional["PhaseTransitionError"]]:
    """
    Execute a phase transition function with retry logic for retryable errors.

    Args:
        func: Function to execute (phase transition function)
        transition_name: Transition identifier
        contract: Phase transition contract (if None, will be fetched)
        max_retries: Maximum number of retries (default 1, per FR-010)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Tuple of (success, result, error_message, phase_transition_error)
    """
    from aeon.exceptions import PhaseTransitionError

    if contract is None:
        contract = get_phase_transition_contract(transition_name)

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            return (True, result, None, None)
        except PhaseTransitionError as e:
            last_error = e
            if e.retryable and attempt < max_retries:
                # Retry if error is retryable and we haven't exceeded max retries
                continue
            else:
                # Don't retry: either not retryable or exceeded max retries
                return (False, None, str(e), e)
        except Exception as e:
            # Non-retryable error or unexpected exception
            error = PhaseTransitionError(
                transition_name=transition_name,
                failure_condition=str(e),
                retryable=False,
            )
            return (False, None, str(e), error)

    # All retries exhausted
    if last_error:
        return (False, None, str(last_error), last_error)
    else:
        error = PhaseTransitionError(
            transition_name=transition_name,
            failure_condition="Unknown error during phase transition",
            retryable=False,
        )
        return (False, None, "Unknown error during phase transition", error)


def call_llm_with_provider_error_handling(
    llm_adapter: Any,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    phase: Optional[Literal["A", "B", "C", "D"]] = None,
    execution_pass: Optional["ExecutionPass"] = None,
    ttl_remaining: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Call LLM adapter with provider error detection and retry logic per FR-011.

    Detects provider errors at every LLM call site, retries once for retryable errors,
    and aborts with structured error for non-retryable errors.

    Args:
        llm_adapter: LLM adapter instance
        prompt: User prompt
        system_prompt: System prompt (optional)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        phase: Phase identifier for error context (optional)

    Returns:
        LLM response dict

    Raises:
        LLMError: On non-retryable errors or after retry fails
        PhaseTransitionError: On retryable errors that fail after retry
    """
    from aeon.exceptions import LLMError, PhaseTransitionError

    # Classify provider errors as retryable or non-retryable
    # Retryable: transient network errors, rate limits (temporary), timeouts
    # Non-retryable: TTL exhaustion, incomplete profile, malformed responses, authentication errors

    retryable_error_keywords = [
        "network",
        "timeout",
        "rate limit",
        "temporary",
        "service unavailable",
        "connection",
    ]

    non_retryable_error_keywords = [
        "ttl",
        "expired",
        "authentication",
        "unauthorized",
        "invalid api key",
        "malformed",
        "parse error",
        "incomplete",
    ]

    def is_retryable_error(error: Exception) -> bool:
        """Determine if error is retryable based on error message and type."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Check for non-retryable keywords first
        for keyword in non_retryable_error_keywords:
            if keyword in error_str:
                return False

        # Check for retryable keywords
        for keyword in retryable_error_keywords:
            if keyword in error_str:
                return True

        # Default: treat LLMError as potentially retryable (network/timeout issues)
        # but other errors as non-retryable
        return isinstance(error, LLMError)

    # Attempt LLM call with retry logic
    last_error = None
    max_retries = 1  # Per FR-011: retry once for retryable errors

    for attempt in range(max_retries + 1):
        try:
            response = llm_adapter.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # T053: TTL check after each LLM call within phase
            if phase and execution_pass is not None and ttl_remaining is not None:
                can_proceed, expiration_response = check_ttl_after_llm_call(
                    ttl_remaining, phase, execution_pass
                )
                if not can_proceed:
                    from aeon.exceptions import TTLExpiredError
                    raise TTLExpiredError(
                        f"TTL expired mid-phase after LLM call in phase {phase}: "
                        f"{expiration_response.message if expiration_response else 'Unknown'}"
                    )
            
            return response
        except LLMError as e:
            last_error = e
            if is_retryable_error(e) and attempt < max_retries:
                # Retry once for retryable errors
                continue
            else:
                # Non-retryable or retry exhausted - abort with structured error
                if phase:
                    error = PhaseTransitionError(
                        transition_name=f"{phase}→*",  # Transition name depends on phase
                        failure_condition=f"LLM provider error: {str(e)}",
                        retryable=is_retryable_error(e) and attempt < max_retries,
                    )
                    raise error from e
                else:
                    raise LLMError(f"LLM provider error (non-retryable or retry exhausted): {str(e)}") from e
        except Exception as e:
            # Unexpected exception - treat as non-retryable
            if phase:
                error = PhaseTransitionError(
                    transition_name=f"{phase}→*",
                    failure_condition=f"Unexpected error during LLM call: {str(e)}",
                    retryable=False,
                )
                raise error from e
            else:
                raise LLMError(f"Unexpected error during LLM call: {str(e)}") from e

    # All retries exhausted
    if last_error:
        if phase:
            error = PhaseTransitionError(
                transition_name=f"{phase}→*",
                failure_condition=f"LLM provider error (retry exhausted): {str(last_error)}",
                retryable=False,
            )
            raise error from last_error
        else:
            raise LLMError(f"LLM provider error (retry exhausted): {str(last_error)}") from last_error
    else:
        if phase:
            error = PhaseTransitionError(
                transition_name=f"{phase}→*",
                failure_condition="Unknown error during LLM call",
                retryable=False,
            )
            raise error
        else:
            raise LLMError("Unknown error during LLM call")


class PhaseOrchestrator:
    """Orchestrates Phase A/B/C/D logic for multi-pass execution."""

    def phase_a_taskprofile_ttl(
        self,
        request: str,
        adaptive_depth: Optional[Any],  # AdaptiveDepth
        global_ttl: int,
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
    ) -> PhaseAResult:
        """
        Phase A: TaskProfile inference and TTL allocation.

        Args:
            request: Natural language request
            adaptive_depth: AdaptiveDepth instance (may be None for fallback)
            global_ttl: Global TTL limit
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            pass_number: Pass number (default 0 for Phase A)
            ttl_remaining: TTL cycles remaining (defaults to global_ttl if not provided)

        Returns:
            Tuple of (success, (task_profile, allocated_ttl), error_message)
        """
        from datetime import datetime
        from aeon.adaptive.models import TaskProfile
        from aeon.exceptions import ContextPropagationError

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else global_ttl

        # T084: Integrate phase entry logging in Phase A
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="A",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T096: Integrate TTL snapshot logging at Phase A boundary
        if logger and correlation_id:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="A",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase A
                ttl_at_boundary=ttl_before,
            )

        # Use provided ttl_remaining or default to global_ttl
        if ttl_remaining is None:
            ttl_remaining = global_ttl

        # T033: Update Phase A to propagate minimal context
        # Build context dict with required fields for Phase A
        # T046: Ensure all required keys are populated for prompt schemas
        # T047: Prevent null semantic inputs - ensure request is non-empty string
        if not request or not isinstance(request, str):
            return (False, (None, global_ttl), "Request must be a non-empty string")
        context = {
            "request": request,
            "pass_number": pass_number,
            "phase": "A",
            "ttl_remaining": ttl_remaining,
        }
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp

        # T092: Integrate state snapshot logging before Phase A transition
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="A",
                pass_number=pass_number,
                plan_state={},  # No plan state in Phase A
                ttl_remaining=ttl_remaining,
                phase_state={"request": request, "global_ttl": global_ttl},
                snapshot_type="before_transition",
            )

        # T028: Integrate context validation before Phase A LLM calls
        spec = get_context_propagation_specification("A")
        is_valid, error_message, missing_fields = validate_context_propagation("A", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="A",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T100: Integrate structured error logging for Phase A failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="A",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.A.001",
                    severity="ERROR",
                    affected_component="phase_a",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="A",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            return (False, (None, global_ttl), str(error))

        # Build LLM context from validated context
        llm_context = build_llm_context("A", context, spec)

        if not adaptive_depth:
            # Fallback to default if AdaptiveDepth not available
            default_task_profile = TaskProfile.default()
            allocated_ttl = global_ttl
            return (True, (default_task_profile, allocated_ttl), None)

        try:
            # Infer TaskProfile using AdaptiveDepth
            # Note: AdaptiveDepth.infer_task_profile doesn't accept context dict yet,
            # but we've validated the context is present and correct
            task_profile = adaptive_depth.infer_task_profile(
                task_description=request,
                context=llm_context,  # Pass validated context
            )

            # Allocate TTL based on TaskProfile
            allocated_ttl = adaptive_depth.allocate_ttl(
                task_profile=task_profile,
                global_ttl_limit=global_ttl,
            )

            # T092: Integrate state snapshot logging after Phase A transition
            if logger and correlation_id:
                logger.log_state_snapshot(
                    correlation_id=correlation_id,
                    phase="A",
                    pass_number=pass_number,
                    plan_state={},  # No plan state in Phase A
                    ttl_remaining=allocated_ttl,
                    phase_state={"task_profile": task_profile.model_dump() if hasattr(task_profile, "model_dump") else str(task_profile)},
                    snapshot_type="after_transition",
                )

            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            # T088: Integrate phase exit logging in Phase A
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="A",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )

            return (True, (task_profile, allocated_ttl), None)
        except Exception as e:
            # T100: Integrate structured error logging for Phase A failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="A",
                    pass_number=pass_number,
                    error_code="AEON.PHASE_TRANSITION.A_B.001",
                    severity="ERROR",
                    affected_component="phase_a",
                    failure_condition=str(e),
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="A",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # If inference or allocation fails, return error result
            return (False, (None, global_ttl), str(e))

    def phase_b_initial_plan_refinement(
        self,
        request: str,
        plan: "Plan",
        task_profile: Any,  # TaskProfile
        recursive_planner: Optional[Any],  # RecursivePlanner
        semantic_validator: Optional[Any],  # SemanticValidator
        tool_registry: Optional[Any],  # ToolRegistry
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
    ) -> PhaseBResult:
        """
        Phase B: Initial Plan & Pre-Execution Refinement.

        Args:
            request: Natural language request
            plan: Initial plan
            task_profile: TaskProfile from Phase A
            recursive_planner: RecursivePlanner instance (may be None)
            semantic_validator: SemanticValidator instance (may be None)
            tool_registry: ToolRegistry instance (may be None)
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            pass_number: Pass number (default 0 for Phase B)
            ttl_remaining: TTL cycles remaining

        Returns:
            Tuple of (success, refined_plan, error_message)
        """
        from datetime import datetime
        from aeon.exceptions import ContextPropagationError

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else None

        # T085: Integrate phase entry logging in Phase B
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="B",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T097: Integrate TTL snapshot logging at Phase B boundary
        if logger and correlation_id and ttl_before is not None:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="B",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase B
                ttl_at_boundary=ttl_before,
            )

        refined_plan = plan

        # T034: Update Phase B to propagate context
        # Build context dict with required fields for Phase B
        # T046: Ensure all required keys are populated for prompt schemas
        context = {
            "request": request,
            "task_profile": task_profile,
            "initial_plan": plan,
            "pass_number": pass_number,
            "phase": "B",
        }
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp
        if ttl_remaining is not None:
            context["ttl_remaining"] = ttl_remaining

        # Add initial_plan goal and step metadata to context (required by spec)
        # T044: initial_plan_steps is documented as optional/future use (not used in prompts currently)
        if plan:
            context["initial_plan_goal"] = plan.goal if hasattr(plan, "goal") else None
            # Note: initial_plan_steps is included for future prompt enhancements, not currently used
            context["initial_plan_steps"] = [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "status": step.status.value if hasattr(step.status, "value") else str(step.status),
                }
                for step in (plan.steps if hasattr(plan, "steps") and plan.steps else [])
            ]

        # T093: Integrate state snapshot logging before Phase B transition
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="B",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"request": request, "task_profile": task_profile.model_dump() if hasattr(task_profile, "model_dump") else str(task_profile)},
                snapshot_type="before_transition",
            )

        # T029: Integrate context validation before Phase B LLM calls
        spec = get_context_propagation_specification("B")
        is_valid, error_message, missing_fields = validate_context_propagation("B", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="B",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T101: Integrate structured error logging for Phase B failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="B",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.B.001",
                    severity="ERROR",
                    affected_component="phase_b",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="B",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            return (False, plan, str(error))

        # Build LLM context from validated context
        llm_context = build_llm_context("B", context, spec)

        try:
            # Use RecursivePlanner.generate_plan() if available to ensure proper structure
            if recursive_planner:
                try:
                    # T029: Context validated before LLM call
                    # Regenerate plan using RecursivePlanner to ensure step_index, total_steps, etc. are set
                    refined_plan = recursive_planner.generate_plan(
                        task_description=request,
                        task_profile=task_profile,
                        tool_registry=tool_registry,
                    )
                except Exception:
                    # If RecursivePlanner fails, fall back to existing plan
                    # Log error but continue with existing plan
                    pass

            # Phase B: Plan Validation - semantic validation
            if semantic_validator:
                try:
                    # T029: Context validated before LLM call (semantic validation)
                    semantic_validation_report = semantic_validator.validate(
                        artifact=refined_plan.model_dump(),
                        artifact_type="plan",
                        tool_registry=tool_registry,
                    )
                    # If validation issues found, refine plan
                    if semantic_validation_report.issues and recursive_planner:
                        from aeon.orchestration.refinement import PlanRefinement

                        refinement_actions = recursive_planner.refine_plan(
                            current_plan=refined_plan,
                            validation_issues=semantic_validation_report.issues,
                            convergence_reason_codes=[],
                            blocked_steps=[],
                            executed_step_ids=set(),
                        )
                        # Apply refinement actions to plan
                        from aeon.orchestration.refinement import PlanRefinement

                        plan_refinement = PlanRefinement()
                        success, refined_plan, error = plan_refinement.apply_actions(
                            refined_plan, refinement_actions
                        )
                        if not success:
                            # If refinement application fails, continue with existing plan
                            refined_plan = plan
                except Exception:
                    # If semantic validation fails, continue with existing plan (best-effort advisory)
                    # Log error but don't fail phase
                    pass

            # T093: Integrate state snapshot logging after Phase B transition
            if logger and correlation_id:
                logger.log_state_snapshot(
                    correlation_id=correlation_id,
                    phase="B",
                    pass_number=pass_number,
                    plan_state=refined_plan.model_dump() if hasattr(refined_plan, "model_dump") else {},
                    ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                    phase_state={"refined_plan": refined_plan.model_dump() if hasattr(refined_plan, "model_dump") else str(refined_plan)},
                    snapshot_type="after_transition",
                )

            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            # T089: Integrate phase exit logging in Phase B
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="B",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )

            return (True, refined_plan, None)
        except Exception as e:
            # T101: Integrate structured error logging for Phase B failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="B",
                    pass_number=pass_number,
                    error_code="AEON.PHASE_TRANSITION.B_C.001",
                    severity="ERROR",
                    affected_component="phase_b",
                    failure_condition=str(e),
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="B",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # On failure, return original plan with error
            return (False, plan, str(e))

    def phase_c_execute_batch(
        self,
        plan: "Plan",
        state: "OrchestrationState",
        step_executor: Any,  # StepExecutor
        tool_registry: Optional[Any],  # ToolRegistry
        memory: Optional[Any],  # Memory
        supervisor: Optional[Any],  # Supervisor
        execute_step_fn: Any,  # Function to execute a step (kernel method)
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        task_profile: Optional[Any] = None,  # TaskProfile
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
        request: Optional[str] = None,
        previous_outputs: Optional[List[Dict[str, Any]]] = None,
        refinement_changes: Optional[List[Dict[str, Any]]] = None,
    ) -> PhaseCExecuteResult:
        """
        Phase C: Execute batch of ready steps.

        Args:
            plan: Current plan
            state: Current orchestration state
            step_executor: StepExecutor instance
            tool_registry: ToolRegistry instance (may be None)
            memory: Memory interface
            supervisor: Supervisor instance (may be None)
            execute_step_fn: Function to execute a step (kernel._execute_step)
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            task_profile: TaskProfile instance (optional)
            pass_number: Pass number in multi-pass execution
            ttl_remaining: TTL cycles remaining
            request: Natural language request (optional)
            previous_outputs: Previous execution results (optional)
            refinement_changes: Refinement changes from previous pass (optional)

        Returns:
            List of execution results (dicts with step_id, status, output, clarity_state)
        """
        from datetime import datetime
        from aeon.plan.models import StepStatus
        from aeon.exceptions import ContextPropagationError

        from aeon.orchestration.step_prep import StepPreparation

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else None

        # T086: Integrate phase entry logging in Phase C (execute)
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="C",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T098: Integrate TTL snapshot logging at Phase C boundary (execute)
        if logger and correlation_id and ttl_before is not None:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase C execute
                ttl_at_boundary=ttl_before,
            )

        # T035: Update Phase C execution to propagate context
        # Build context dict with required fields for Phase C execution
        # T046: Ensure all required keys are populated for prompt schemas
        # T047: Prevent null semantic inputs - ensure request is non-empty string
        context = {
            "request": request or "",
            "refined_plan": plan,
            "pass_number": pass_number,
            "phase": "C",
        }
        if task_profile:
            context["task_profile"] = task_profile
        if ttl_remaining is not None:
            context["ttl_remaining"] = ttl_remaining
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp
        # Add refined_plan goal and step metadata
        # T044: refined_plan_steps is documented as optional/future use (not used in prompts currently)
        if plan:
            context["refined_plan_goal"] = plan.goal if hasattr(plan, "goal") else None
            # Note: refined_plan_steps is included for future prompt enhancements, not currently used
            context["refined_plan_steps"] = [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "status": step.status.value if hasattr(step.status, "value") else str(step.status),
                }
                for step in (plan.steps if hasattr(plan, "steps") and plan.steps else [])
            ]
        # Add previous outputs and refinement changes
        if previous_outputs:
            context["previous_outputs"] = previous_outputs
        if refinement_changes:
            context["refinement_changes"] = refinement_changes

        # T094: Integrate state snapshot logging before Phase C transition (execute)
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"request": request, "task_profile": task_profile.model_dump() if task_profile and hasattr(task_profile, "model_dump") else str(task_profile) if task_profile else None},
                snapshot_type="before_transition",
            )

        # T030: Integrate context validation before Phase C LLM calls (execution)
        spec = get_context_propagation_specification("C")
        is_valid, error_message, missing_fields = validate_context_propagation("C", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="C",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T102: Integrate structured error logging for Phase C failures (execute)
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="C",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.C.001",
                    severity="ERROR",
                    affected_component="phase_c_execute",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # Return empty results with error - step execution should not proceed without valid context
            return [{"error": str(error), "status": "failed"}]

        # Build LLM context from validated context - store in state for step executor to access
        llm_context = build_llm_context("C", context, spec)
        # Store context in state so execute_step_fn can access it
        # Store both the context and the phase so executor can validate correctly
        if hasattr(state, 'execution_context') and not state.execution_context:
            state.execution_context = execution_context
        if not hasattr(state, 'phase_context'):
            state.phase_context = {"phase": "C", "context": llm_context}
        else:
            state.phase_context = {"phase": "C", "context": llm_context}

        step_prep = StepPreparation()
        execution_results = []
        ready_steps = step_prep.get_ready_steps(plan, memory)

        for step in ready_steps:
            try:
                # Execute step - context is available via state.phase_c_context
                # Note: TTL decrement now happens in kernel._execute_step (constitutional requirement)
                execute_step_fn(step, state)
                # Handle both enum and string values (use_enum_values=True converts to string)
                status_value = step.status.value if hasattr(step.status, 'value') else str(step.status)
                execution_results.append({
                    "step_id": step.step_id,
                    "status": status_value,
                    "output": getattr(step, "step_output", None),
                    "clarity_state": getattr(step, "clarity_state", None),
                })
            except Exception as e:
                execution_results.append({
                    "step_id": step.step_id,
                    "status": StepStatus.FAILED.value,
                    "error": str(e),
                })

        # T094: Integrate state snapshot logging after Phase C transition (execute)
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"execution_results_count": len(execution_results)},
                snapshot_type="after_transition",
            )

        phase_duration = (datetime.now() - phase_start_time).total_seconds()
        # T090: Integrate phase exit logging in Phase C (execute)
        if logger and correlation_id:
            logger.log_phase_exit(
                phase="C",
                correlation_id=correlation_id,
                pass_number=pass_number,
                duration=phase_duration,
                outcome="success",
            )

        return execution_results

    def phase_c_evaluate(
        self,
        plan: "Plan",
        execution_results: List[Dict[str, Any]],
        semantic_validator: Optional[Any],  # SemanticValidator
        convergence_engine: Optional[Any],  # ConvergenceEngine
        tool_registry: Optional[Any],  # ToolRegistry
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        task_profile: Optional[Any] = None,  # TaskProfile
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
        request: Optional[str] = None,
    ) -> PhaseCEvaluateResult:
        """
        Phase C: Evaluate execution results (semantic validation + convergence).

        Args:
            plan: Current plan
            execution_results: Execution results from batch
            semantic_validator: SemanticValidator instance (may be None)
            convergence_engine: ConvergenceEngine instance (may be None)
            tool_registry: ToolRegistry instance (may be None)
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            task_profile: TaskProfile instance (optional)
            pass_number: Pass number in multi-pass execution
            ttl_remaining: TTL cycles remaining
            request: Natural language request (optional)

        Returns:
            Evaluation results dict
        """
        from datetime import datetime
        from aeon.plan.models import StepStatus
        from aeon.validation.models import SemanticValidationReport
        from aeon.convergence.models import ConvergenceAssessment
        from aeon.exceptions import ContextPropagationError

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else None

        # T086: Integrate phase entry logging in Phase C (evaluate)
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="C",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T098: Integrate TTL snapshot logging at Phase C boundary (evaluate)
        if logger and correlation_id and ttl_before is not None:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase C evaluate
                ttl_at_boundary=ttl_before,
            )

        # T036: Update Phase C evaluation to propagate context
        # Build context dict with required fields for Phase C evaluation
        # T046: Ensure all required keys are populated for prompt schemas
        # T047: Prevent null semantic inputs - ensure request is non-empty string
        context = {
            "request": request or "",
            "refined_plan": plan,
            "pass_number": pass_number,
            "phase": "C",
        }
        if task_profile:
            context["task_profile"] = task_profile
        if ttl_remaining is not None:
            context["ttl_remaining"] = ttl_remaining
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp
        # Add refined_plan goal and step metadata
        # T044: refined_plan_steps is documented as optional/future use (not used in prompts currently)
        if plan:
            context["refined_plan_goal"] = plan.goal if hasattr(plan, "goal") else None
            # Note: refined_plan_steps is included for future prompt enhancements, not currently used
            context["refined_plan_steps"] = [
                {
                    "step_id": step.step_id,
                    "description": step.description,
                    "status": step.status.value if hasattr(step.status, "value") else str(step.status),
                }
                for step in (plan.steps if hasattr(plan, "steps") and plan.steps else [])
            ]
        # Add current plan state and execution_results
        # Note: current_plan_state and execution_results are used by convergence/validation, not prompts
        context["current_plan_state"] = plan.model_dump() if plan else {}
        context["execution_results"] = execution_results

        # T094: Integrate state snapshot logging before Phase C transition (evaluate)
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"execution_results_count": len(execution_results)},
                snapshot_type="before_transition",
            )

        # T030: Integrate context validation before Phase C LLM calls
        spec = get_context_propagation_specification("C")
        is_valid, error_message, missing_fields = validate_context_propagation("C", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="C",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T102: Integrate structured error logging for Phase C failures (evaluate)
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="C",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.C.001",
                    severity="ERROR",
                    affected_component="phase_c_evaluate",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # Return error result instead of raising to maintain phase contract
            return {
                "converged": False,
                "needs_refinement": False,
                "semantic_validation": {},
                "convergence_assessment": {},
                "validation_issues": [],
                "convergence_reason_codes": [],
                "error": str(error),
            }

        # Build LLM context from validated context
        llm_context = build_llm_context("C", context, spec)

        # Build execution results for validation and convergence assessment
        # (execution_results is already provided, but we need step status info)
        step_results = []
        for step in plan.steps:
            if step.status in (StepStatus.COMPLETE, StepStatus.FAILED, StepStatus.INVALID):
                # Handle both enum and string values (use_enum_values=True converts to string)
                status_value = step.status.value if hasattr(step.status, 'value') else str(step.status)
                step_results.append({
                    "step_id": step.step_id,
                    "status": status_value,
                    "output": getattr(step, "step_output", None),
                    "clarity_state": getattr(step, "clarity_state", None),
                })

        # Use provided execution_results if available, otherwise use step_results
        eval_results = execution_results if execution_results else step_results

        # 1. Call SemanticValidator.validate() for execution artifacts
        semantic_validation_report = None
        if semantic_validator:
            try:
                # T030: Context validated before LLM call
                # Validate current plan state and execution artifacts
                execution_artifact = {
                    "plan": plan.model_dump(),
                    "execution_results": eval_results,
                }
                semantic_validation_report = semantic_validator.validate(
                    artifact=execution_artifact,
                    artifact_type="execution_artifact",
                    tool_registry=tool_registry,
                )
            except Exception:
                # If semantic validation fails, continue with empty report (best-effort advisory)
                semantic_validation_report = None

        # 2. Call ConvergenceEngine.assess() with validation report
        convergence_assessment = None
        if convergence_engine:
            try:
                # Create a default empty validation report if none exists
                if semantic_validation_report is None:
                    semantic_validation_report = SemanticValidationReport(
                        artifact_type="execution_artifact",
                        issues=[],
                    )

                convergence_assessment = convergence_engine.assess(
                    plan_state=plan.model_dump(),
                    execution_results=eval_results,
                    semantic_validation_report=semantic_validation_report,
                    execution_context=execution_context,
                    logger=logger,
                )
            except Exception as e:
                # If convergence assessment fails, create conservative assessment
                convergence_assessment = ConvergenceAssessment(
                    converged=False,
                    reason_codes=["convergence_assessment_failed", str(e)],
                    completeness_score=0.0,
                    coherence_score=0.0,
                    consistency_status={},
                    detected_issues=[f"Convergence assessment failed: {str(e)}"],
                    metadata={"error": str(e)},
                )
        else:
            # Fallback if convergence engine not available
            convergence_assessment = ConvergenceAssessment(
                converged=False,
                reason_codes=["convergence_engine_not_available"],
                completeness_score=0.0,
                coherence_score=0.0,
                consistency_status={},
                detected_issues=[],
                metadata={},
            )

        # Check if all steps are complete (automatic convergence detection)
        all_steps_complete = all(
            step.status in (StepStatus.COMPLETE, StepStatus.FAILED, StepStatus.INVALID)
            for step in plan.steps
        )

        # Determine if refinement is needed
        needs_refinement = False
        if semantic_validation_report and semantic_validation_report.issues:
            # Refinement needed if there are validation issues
            needs_refinement = True
        if convergence_assessment and not convergence_assessment.converged:
            # Refinement needed if not converged
            needs_refinement = True

        # Automatic convergence: if all steps are complete and no validation issues, mark as converged
        auto_converged = False
        if all_steps_complete:
            if not semantic_validation_report or not semantic_validation_report.issues:
                # All steps complete and no validation issues - auto-converge
                auto_converged = True
            elif semantic_validation_report.overall_severity in ("LOW", "INFO"):
                # All steps complete and only low-severity issues - auto-converge
                auto_converged = True

        # Use auto-convergence if LLM-based assessment didn't converge but conditions are met
        final_converged = convergence_assessment.converged if convergence_assessment else False
        if not final_converged and auto_converged:
            final_converged = True

        evaluation_result = {
            "converged": final_converged,
            "needs_refinement": needs_refinement and not auto_converged,  # Don't refine if auto-converged
            "semantic_validation": semantic_validation_report.model_dump() if semantic_validation_report else {},
            "convergence_assessment": convergence_assessment.model_dump() if convergence_assessment else {},
            "validation_issues": semantic_validation_report.issues if semantic_validation_report else [],
            "convergence_reason_codes": convergence_assessment.reason_codes if convergence_assessment else [],
        }
        
        # Log evaluation outcome (T025) - delegate to convergence engine
        if logger and execution_context and convergence_engine:
            # The convergence engine will log the evaluation outcome
            pass  # Logging is done in convergence engine.assess() method

        # T094: Integrate state snapshot logging after Phase C transition (evaluate)
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"converged": final_converged, "needs_refinement": needs_refinement},
                snapshot_type="after_transition",
            )

        phase_duration = (datetime.now() - phase_start_time).total_seconds()
        # T090: Integrate phase exit logging in Phase C (evaluate)
        if logger and correlation_id:
            logger.log_phase_exit(
                phase="C",
                correlation_id=correlation_id,
                pass_number=pass_number,
                duration=phase_duration,
                outcome="success",
            )
        
        return evaluation_result

    def phase_c_refine(
        self,
        plan: "Plan",
        evaluation_results: Dict[str, Any],
        recursive_planner: Optional[Any],  # RecursivePlanner
        populate_step_indices_fn: Any,  # Function to populate step indices
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        task_profile: Optional[Any] = None,  # TaskProfile
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
        request: Optional[str] = None,
        execution_results_list: Optional[List[Dict[str, Any]]] = None,
    ) -> PhaseCRefineResult:
        """
        Phase C: Refine plan based on evaluation results.

        Args:
            plan: Current plan
            evaluation_results: Results from evaluation phase
            recursive_planner: RecursivePlanner instance (may be None)
            populate_step_indices_fn: Function to populate step indices
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            task_profile: TaskProfile instance (optional)
            pass_number: Pass number in multi-pass execution
            ttl_remaining: TTL cycles remaining
            request: Natural language request (optional)
            execution_results_list: Execution results list (optional)

        Returns:
            Tuple of (success, refinement_changes, error_message)
        """
        from datetime import datetime
        from aeon.plan.models import StepStatus
        from aeon.exceptions import ContextPropagationError

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else None

        # T086: Integrate phase entry logging in Phase C (refine)
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="C",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T098: Integrate TTL snapshot logging at Phase C boundary (refine)
        if logger and correlation_id and ttl_before is not None:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase C refine
                ttl_at_boundary=ttl_before,
            )

        if not recursive_planner:
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )
            return (True, [], None, plan)  # Return original plan unchanged

        # T037: Update Phase C refinement to propagate context
        # Build context dict with required fields for Phase C refinement
        # T046: Ensure all required keys are populated for prompt schemas
        # T047: Prevent null semantic inputs - ensure request is non-empty string
        context = {
            "request": request or "",
            "refined_plan": plan,
            "pass_number": pass_number,
            "phase": "C",
        }
        if task_profile:
            context["task_profile"] = task_profile
        if ttl_remaining is not None:
            context["ttl_remaining"] = ttl_remaining
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp
        # Add current plan state, execution_results, evaluation_results, previous outputs
        # Note: current_plan_state, execution_results, and evaluation_results are used by refinement logic, not prompts
        context["current_plan_state"] = plan.model_dump() if plan else {}
        if execution_results_list:
            context["execution_results"] = execution_results_list
        context["evaluation_results"] = evaluation_results
        # Previous outputs are the execution_results
        if execution_results_list:
            context["previous_outputs"] = execution_results_list

        # T094: Integrate state snapshot logging before Phase C transition (refine)
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="C",
                pass_number=pass_number,
                plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"evaluation_results": evaluation_results},
                snapshot_type="before_transition",
            )

        # T030: Integrate context validation before Phase C LLM calls (refinement)
        spec = get_context_propagation_specification("C")
        is_valid, error_message, missing_fields = validate_context_propagation("C", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="C",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T102: Integrate structured error logging for Phase C failures (refine)
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="C",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.C.001",
                    severity="ERROR",
                    affected_component="phase_c_refine",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            return (False, [], str(error))

        # Build LLM context from validated context
        llm_context = build_llm_context("C", context, spec)

        try:
            # Extract validation issues, convergence reason codes, and blocked steps
            validation_issues = evaluation_results.get("validation_issues", [])
            convergence_reason_codes = evaluation_results.get("convergence_reason_codes", [])
            blocked_steps = evaluation_results.get("blocked_steps", [])

            # Get executed step IDs (steps with status complete or failed)
            executed_step_ids = {
                step.step_id
                for step in plan.steps
                if step.status in (StepStatus.COMPLETE, StepStatus.FAILED)
            }

            # T030: Context validated before LLM call
            # Generate refinement actions
            refinement_actions = recursive_planner.refine_plan(
                current_plan=plan,
                validation_issues=validation_issues,
                convergence_reason_codes=convergence_reason_codes,
                blocked_steps=blocked_steps,
                executed_step_ids=executed_step_ids,
            )

            # Create before_plan_fragment for logging (T024)
            before_plan_fragment = None
            if logger and execution_context and refinement_actions:
                from aeon.observability.models import PlanFragment
                # Get changed step IDs (will be determined after applying actions)
                changed_step_ids = set()
                unchanged_step_ids = {step.step_id for step in plan.steps}
                before_plan_fragment = PlanFragment(
                    changed_steps=[],
                    unchanged_step_ids=list(unchanged_step_ids),
                )

            # Apply refinement actions to plan
            if refinement_actions:
                from aeon.orchestration.refinement import PlanRefinement

                plan_refinement = PlanRefinement()
                success, updated_plan, error = plan_refinement.apply_actions(
                    plan, refinement_actions, execution_context, logger
                )
                if success:
                    plan = updated_plan
                    # Re-populate step indices after refinement
                    from aeon.orchestration.step_prep import StepPreparation

                    step_prep = StepPreparation()
                    step_prep.populate_step_indices(plan)
                else:
                    # If refinement application fails, continue without refinement
                    return (True, [], None, plan)  # Return original plan unchanged

            # Convert refinement actions to dict format for logging
            refinement_changes = [action.model_dump() for action in refinement_actions]
            
            # Log refinement outcome (T024)
            if logger and execution_context and refinement_actions and before_plan_fragment:
                from aeon.observability.models import PlanFragment
                # Create after_plan_fragment with changed steps
                changed_steps = []
                unchanged_step_ids_after = set()
                for step in plan.steps:
                    # Check if this step was modified/added by comparing with original plan
                    original_step = next((s for s in before_plan_fragment.unchanged_step_ids if s == step.step_id), None)
                    if original_step is None or step.step_id not in before_plan_fragment.unchanged_step_ids:
                        changed_steps.append(step)
                    else:
                        unchanged_step_ids_after.add(step.step_id)
                
                after_plan_fragment = PlanFragment(
                    changed_steps=changed_steps,
                    unchanged_step_ids=list(unchanged_step_ids_after),
                )
                
                # Build evaluation_signals from evaluation_results (T065, T066, T067)
                from aeon.observability.models import ConvergenceAssessmentSummary, ValidationIssuesSummary
                
                # Extract convergence assessment and create summary
                convergence_assessment_dict = evaluation_results.get("convergence_assessment", {})
                convergence_assessment_summary = None
                if convergence_assessment_dict:
                    try:
                        convergence_assessment_summary = ConvergenceAssessmentSummary(
                            converged=convergence_assessment_dict.get("converged", False),
                            reason_codes=convergence_assessment_dict.get("reason_codes", []),
                            scores=convergence_assessment_dict.get("scores") or {
                                "completeness": convergence_assessment_dict.get("completeness_score", 0.0),
                                "coherence": convergence_assessment_dict.get("coherence_score", 0.0),
                            },
                            pass_number=0,  # Pass number should come from caller if available
                        )
                    except Exception:
                        pass
                
                # Extract validation issues and create summary
                validation_issues = evaluation_results.get("validation_issues", [])
                validation_issues_summary = None
                if validation_issues:
                    try:
                        critical_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "CRITICAL" or (hasattr(i, "severity") and i.severity == "CRITICAL"))
                        error_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "ERROR" or (hasattr(i, "severity") and i.severity == "ERROR"))
                        warning_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "WARNING" or (hasattr(i, "severity") and i.severity == "WARNING"))
                        info_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "INFO" or (hasattr(i, "severity") and i.severity == "INFO"))
                        validation_issues_summary = ValidationIssuesSummary(
                            total_issues=len(validation_issues),
                            critical_count=critical_count,
                            error_count=error_count,
                            warning_count=warning_count,
                            info_count=info_count,
                            issues_by_type=None,
                        )
                    except Exception:
                        pass
                
                # Build evaluation_signals dict for backward compatibility
                evaluation_signals = {}
                if convergence_assessment_summary:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()
                
                # Log refinement trigger (T068) - log what triggered refinement
                if logger and execution_context:
                    trigger_reason = []
                    if convergence_assessment_dict and not convergence_assessment_dict.get("converged", True):
                        trigger_reason.append("convergence_not_achieved")
                    if validation_issues:
                        trigger_reason.append("validation_issues_detected")
                    if not trigger_reason:
                        trigger_reason.append("manual_refinement")
                    
                    # Log refinement trigger as part of refinement outcome
                    # The evaluation_signals already contains the trigger context
                
                # Log refinement actions (T069) - which steps were modified/added/removed
                # refinement_actions already contains this information in refinement_changes
                
                logger.log_refinement_outcome(
                    correlation_id=execution_context.correlation_id,
                    before_plan_fragment=before_plan_fragment,
                    after_plan_fragment=after_plan_fragment,
                    refinement_actions=refinement_changes,
                    evaluation_signals=evaluation_signals if evaluation_signals else None,
                    convergence_assessment_summary=convergence_assessment_summary,
                    validation_issues_summary=validation_issues_summary,
                    pass_number=pass_number,  # Use pass_number from method parameter
                )

            # T094: Integrate state snapshot logging after Phase C transition (refine)
            if logger and correlation_id:
                logger.log_state_snapshot(
                    correlation_id=correlation_id,
                    phase="C",
                    pass_number=pass_number,
                    plan_state=plan.model_dump() if hasattr(plan, "model_dump") else {},
                    ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                    phase_state={"refinement_changes_count": len(refinement_changes)},
                    snapshot_type="after_transition",
                )

            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            # T090: Integrate phase exit logging in Phase C (refine)
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )
            
            return (True, refinement_changes, None, plan)  # Return updated plan

        except Exception as e:
            # T102: Integrate structured error logging for Phase C failures (refine)
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="C",
                    pass_number=pass_number,
                    error_code="AEON.PHASE_TRANSITION.C_D.001",
                    severity="ERROR",
                    affected_component="phase_c_refine",
                    failure_condition=str(e),
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="C",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # If refinement fails, log error and continue without refinement
            return (False, [], str(e), plan)  # Return original plan on error

    def phase_d_adaptive_depth(
        self,
        task_profile: Any,  # TaskProfile
        evaluation_results: Dict[str, Any],
        plan: "Plan",
        adaptive_depth: Optional[Any],  # AdaptiveDepth
        state: "OrchestrationState",
        global_ttl: int,
        execution_passes: List["ExecutionPass"],
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
        pass_number: int = 0,
        ttl_remaining: Optional[int] = None,
        request: Optional[str] = None,
    ) -> PhaseDResult:
        """
        Phase D: Adaptive Depth - update TaskProfile at pass boundaries.

        Args:
            task_profile: Current TaskProfile
            evaluation_results: Results from evaluation phase
            plan: Current plan
            adaptive_depth: AdaptiveDepth instance (may be None)
            state: Current orchestration state
            global_ttl: Global TTL limit
            execution_passes: Execution passes list
            execution_context: Execution context with correlation_id and execution_start_timestamp
            logger: JSONL logger instance (optional)
            pass_number: Pass number in multi-pass execution
            ttl_remaining: TTL cycles remaining
            request: Natural language request (optional)

        Returns:
            Tuple of (success, updated_task_profile, error_message)
        """
        from datetime import datetime
        from aeon.exceptions import ContextPropagationError

        phase_start_time = datetime.now()
        correlation_id = execution_context.correlation_id if execution_context else None
        ttl_before = ttl_remaining if ttl_remaining is not None else None

        # T087: Integrate phase entry logging in Phase D
        if logger and correlation_id:
            logger.log_phase_entry(
                phase="D",
                correlation_id=correlation_id,
                pass_number=pass_number,
            )

        # T099: Integrate TTL snapshot logging at Phase D boundary
        if logger and correlation_id and ttl_before is not None:
            logger.log_ttl_snapshot(
                correlation_id=correlation_id,
                phase="D",
                pass_number=pass_number,
                ttl_before=ttl_before,
                ttl_after=ttl_before,  # TTL doesn't change in Phase D (decrements after)
                ttl_at_boundary=ttl_before,
            )

        if not adaptive_depth or not task_profile:
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="D",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )
            return (True, None, None)

        # T038: Update Phase D to propagate context
        # Build context dict with required fields for Phase D
        # T046: Ensure all required keys are populated for prompt schemas
        # T047: Prevent null semantic inputs - ensure request is non-empty string
        context = {
            "request": request or "",
            "task_profile": task_profile,
            "evaluation_results": evaluation_results,
            "plan_state": plan.model_dump() if plan else {},
            "pass_number": pass_number,
            "phase": "D",
        }
        if ttl_remaining is not None:
            context["ttl_remaining"] = ttl_remaining
        # T032: Ensure correlation_id and execution_start_timestamp are passed unchanged
        if execution_context:
            context["correlation_id"] = execution_context.correlation_id
            context["execution_start_timestamp"] = execution_context.execution_start_timestamp
        # Add adaptive depth decision inputs (from evaluation_results and plan state)
        # Note: adaptive_depth_inputs is used by AdaptiveDepth.update_task_profile(), not prompts
        context["adaptive_depth_inputs"] = {
            "convergence_assessment": evaluation_results.get("convergence_assessment", {}),
            "semantic_validation": evaluation_results.get("semantic_validation", {}),
            "plan_state": plan.model_dump() if plan else {},
        }

        # T095: Integrate state snapshot logging before Phase D transition
        if logger and correlation_id:
            logger.log_state_snapshot(
                correlation_id=correlation_id,
                phase="D",
                pass_number=pass_number,
                plan_state=plan.model_dump() if plan and hasattr(plan, "model_dump") else {},
                ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                phase_state={"task_profile": task_profile.model_dump() if hasattr(task_profile, "model_dump") else str(task_profile), "evaluation_results": evaluation_results},
                snapshot_type="before_transition",
            )

        # T031: Integrate context validation before Phase D LLM calls
        spec = get_context_propagation_specification("D")
        is_valid, error_message, missing_fields = validate_context_propagation("D", context, spec)
        if not is_valid:
            error = ContextPropagationError(
                phase="D",
                missing_fields=missing_fields,
                message=error_message,
            )
            # T103: Integrate structured error logging for Phase D failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="D",
                    pass_number=pass_number,
                    error_code="AEON.CONTEXT_PROPAGATION.D.001",
                    severity="ERROR",
                    affected_component="phase_d",
                    failure_condition=error_message,
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="D",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            return (False, None, str(error))

        # Build LLM context from validated context
        llm_context = build_llm_context("D", context, spec)

        try:
            # Extract convergence assessment and semantic validation report
            convergence_assessment_dict = evaluation_results.get("convergence_assessment", {})
            semantic_validation_dict = evaluation_results.get("semantic_validation", {})

            # Convert dicts to model instances if needed
            from aeon.convergence.models import ConvergenceAssessment
            from aeon.validation.models import SemanticValidationReport

            convergence_assessment = None
            if convergence_assessment_dict:
                try:
                    convergence_assessment = ConvergenceAssessment(**convergence_assessment_dict)
                except Exception:
                    pass

            semantic_validation_report = None
            if semantic_validation_dict:
                try:
                    semantic_validation_report = SemanticValidationReport(**semantic_validation_dict)
                except Exception:
                    pass

            # Collect clarity states from execution results
            clarity_states = []
            if plan:
                for step in plan.steps:
                    clarity_state = getattr(step, "clarity_state", None)
                    if clarity_state:
                        clarity_states.append(clarity_state)

            # T031: Context validated before LLM call
            # Call AdaptiveDepth.update_task_profile()
            updated_profile = adaptive_depth.update_task_profile(
                current_profile=task_profile,
                convergence_assessment=convergence_assessment,
                semantic_validation_report=semantic_validation_report,
                clarity_states=clarity_states,
            )

            if updated_profile:
                # Adjust TTL bidirectionally based on profile update
                old_ttl = state.ttl_remaining if state else global_ttl
                adjusted_ttl, adjustment_reason = adaptive_depth.adjust_ttl_for_updated_profile(
                    old_profile=task_profile,
                    new_profile=updated_profile,
                    current_ttl=old_ttl,
                    global_ttl_limit=global_ttl,
                )

                # Update state TTL
                if state:
                    state.ttl_remaining = adjusted_ttl

                # Record adjustment_reason in execution metadata
                # Store in the current execution pass
                if execution_passes:
                    current_pass = execution_passes[-1]
                    if "adaptive_depth_adjustment" not in current_pass.evaluation_results:
                        current_pass.evaluation_results["adaptive_depth_adjustment"] = {}
                    current_pass.evaluation_results["adaptive_depth_adjustment"] = {
                        "profile_version_old": task_profile.profile_version,
                        "profile_version_new": updated_profile.profile_version,
                        "adjustment_reason": adjustment_reason,
                        "ttl_old": old_ttl,
                        "ttl_new": adjusted_ttl,
                    }

                # T095: Integrate state snapshot logging after Phase D transition
                if logger and correlation_id:
                    logger.log_state_snapshot(
                        correlation_id=correlation_id,
                        phase="D",
                        pass_number=pass_number,
                        plan_state=plan.model_dump() if plan and hasattr(plan, "model_dump") else {},
                        ttl_remaining=adjusted_ttl,
                        phase_state={"updated_task_profile": updated_profile.model_dump() if hasattr(updated_profile, "model_dump") else str(updated_profile)},
                        snapshot_type="after_transition",
                    )

                phase_duration = (datetime.now() - phase_start_time).total_seconds()
                # T091: Integrate phase exit logging in Phase D
                if logger and correlation_id:
                    logger.log_phase_exit(
                        phase="D",
                        correlation_id=correlation_id,
                        pass_number=pass_number,
                        duration=phase_duration,
                        outcome="success",
                    )

                return (True, updated_profile, None)

            # T095: Integrate state snapshot logging after Phase D transition (no update)
            if logger and correlation_id:
                logger.log_state_snapshot(
                    correlation_id=correlation_id,
                    phase="D",
                    pass_number=pass_number,
                    plan_state=plan.model_dump() if plan and hasattr(plan, "model_dump") else {},
                    ttl_remaining=ttl_remaining if ttl_remaining is not None else 0,
                    phase_state={"task_profile": "unchanged"},
                    snapshot_type="after_transition",
                )

            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            # T091: Integrate phase exit logging in Phase D
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="D",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="success",
                )

            return (True, None, None)
        except Exception as e:
            # T103: Integrate structured error logging for Phase D failures
            if logger and correlation_id:
                logger.log_phase_transition_error(
                    correlation_id=correlation_id,
                    phase="D",
                    pass_number=pass_number,
                    error_code="AEON.PHASE_TRANSITION.D_A.001",
                    severity="ERROR",
                    affected_component="phase_d",
                    failure_condition=str(e),
                    retryable=False,
                )
            phase_duration = (datetime.now() - phase_start_time).total_seconds()
            if logger and correlation_id:
                logger.log_phase_exit(
                    phase="D",
                    correlation_id=correlation_id,
                    pass_number=pass_number,
                    duration=phase_duration,
                    outcome="failure",
                )
            # If update fails, return error
            return (False, None, str(e))
