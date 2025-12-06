"""Phase transition contract validation logic.

This module contains functions for validating phase transition contracts,
extracted from the kernel to reduce LOC.
"""

from typing import Any, Dict, Literal, Optional

from aeon.exceptions import ExecutionPassValidationError, PhaseTransitionError
from aeon.orchestration.phases import validate_and_enforce_phase_transition
from aeon.validation.execution_pass import (
    validate_execution_pass_after_phase,
    validate_execution_pass_before_phase,
    validate_execution_pass_invariants,
)

__all__ = [
    "validate_phase_entry",
    "validate_phase_exit",
    "validate_phase_invariants",
    "validate_transition_contract",
]


def validate_phase_entry(
    execution_pass: Any,  # ExecutionPass
    phase: Literal["A", "B", "C", "D"],
) -> None:
    """
    Validate ExecutionPass before phase entry.

    Raises ExecutionPassValidationError if validation fails.

    Args:
        execution_pass: ExecutionPass to validate
        phase: Phase identifier

    Raises:
        ExecutionPassValidationError: If validation fails
    """
    is_valid, error_message = validate_execution_pass_before_phase(execution_pass, phase)
    if not is_valid:
        raise ExecutionPassValidationError(
            phase=phase,
            validation_type="before_phase",
            error_message=error_message or "Validation failed",
        )


def validate_phase_exit(
    execution_pass: Any,  # ExecutionPass
    phase: Literal["A", "B", "C", "D"],
) -> None:
    """
    Validate ExecutionPass after phase exit.

    Raises ExecutionPassValidationError if validation fails.

    Args:
        execution_pass: ExecutionPass to validate
        phase: Phase identifier

    Raises:
        ExecutionPassValidationError: If validation fails
    """
    is_valid, error_message = validate_execution_pass_after_phase(execution_pass, phase)
    if not is_valid:
        raise ExecutionPassValidationError(
            phase=phase,
            validation_type="after_phase",
            error_message=error_message or "Validation failed",
        )


def validate_phase_invariants(
    execution_pass: Any,  # ExecutionPass
    phase: Literal["A", "B", "C", "D"],
) -> None:
    """
    Validate ExecutionPass invariants.

    Raises ExecutionPassValidationError if validation fails.

    Args:
        execution_pass: ExecutionPass to validate
        phase: Phase identifier

    Raises:
        ExecutionPassValidationError: If validation fails
    """
    is_valid, error_message = validate_execution_pass_invariants(execution_pass, phase)
    if not is_valid:
        raise ExecutionPassValidationError(
            phase=phase,
            validation_type="invariants",
            error_message=error_message or "Invariant validation failed",
        )


def validate_transition_contract(
    transition: Literal["A→B", "B→C", "C→D", "D→A/B"],
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Validate phase transition contract.

    Raises PhaseTransitionError if validation fails.

    Args:
        transition: Transition identifier
        inputs: Input fields for transition
        outputs: Optional output fields for transition

    Raises:
        PhaseTransitionError: If contract validation fails
    """
    try:
        validate_and_enforce_phase_transition(transition, inputs, outputs)
    except Exception as e:
        if isinstance(e, PhaseTransitionError):
            raise
        raise PhaseTransitionError(
            transition=transition,
            message=f"Contract validation failed: {str(e)}",
        ) from e

