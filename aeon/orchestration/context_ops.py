"""Context building and normalization logic.

This module contains functions for building and normalizing context before
LLM calls, extracted from the kernel to reduce LOC.
"""

from typing import Any, Dict, Literal, Optional

from aeon.orchestration.phases import (
    build_llm_context,
    get_context_propagation_specification,
    validate_context_propagation,
)

__all__ = [
    "build_phase_context",
    "normalize_context",
    "validate_context_before_llm",
]


def build_phase_context(
    phase: Literal["A", "B", "C", "D"],
    base_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build normalized context for a phase before LLM call.

    Args:
        phase: Phase identifier
        base_context: Base context dictionary

    Returns:
        Normalized context dictionary for LLM

    Raises:
        ValueError: If required context fields are missing
    """
    spec = get_context_propagation_specification(phase)
    is_valid, error_message, missing_fields = validate_context_propagation(phase, base_context, spec)
    if not is_valid:
        raise ValueError(f"Context validation failed for phase {phase}: {error_message}")

    return build_llm_context(phase, base_context, spec)


def normalize_context(
    context: Dict[str, Any],
    phase: Literal["A", "B", "C", "D"],
) -> Dict[str, Any]:
    """
    Normalize context dictionary for a phase.

    Ensures all required fields are present and properly formatted.

    Args:
        context: Context dictionary to normalize
        phase: Phase identifier

    Returns:
        Normalized context dictionary
    """
    spec = get_context_propagation_specification(phase)

    # Ensure all must_have_fields are present
    normalized = {}
    for field_name in spec.must_have_fields:
        if field_name in context:
            normalized[field_name] = context[field_name]
        else:
            # Provide defaults for optional fields if needed
            if field_name in ["request"]:
                normalized[field_name] = ""
            elif field_name in ["pass_number"]:
                normalized[field_name] = 0
            else:
                normalized[field_name] = None

    # Include must_pass_unchanged_fields
    for field_name in spec.must_pass_unchanged_fields:
        if field_name in context:
            normalized[field_name] = context[field_name]

    return normalized


def validate_context_before_llm(
    phase: Literal["A", "B", "C", "D"],
    context: Dict[str, Any],
) -> tuple[bool, Optional[str], list[str]]:
    """
    Validate context before LLM call.

    Args:
        phase: Phase identifier
        context: Context dictionary to validate

    Returns:
        Tuple of (is_valid, error_message, missing_fields)
    """
    spec = get_context_propagation_specification(phase)
    return validate_context_propagation(phase, context, spec)

