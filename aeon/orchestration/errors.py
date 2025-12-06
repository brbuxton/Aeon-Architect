"""Structured error creation logic.

This module contains functions for creating structured errors with component
assignment and error codes, extracted from the kernel to reduce LOC.
"""

from typing import Any, Dict, Optional

from aeon.exceptions import AeonError
from aeon.observability.models import ErrorRecord

__all__ = [
    "create_error_record",
    "determine_component",
    "assign_error_code",
]


def determine_component(phase: Optional[str] = None, subsystem: Optional[str] = None) -> str:
    """
    Determine the affected component for error reporting.

    Args:
        phase: Optional phase identifier (A, B, C, D)
        subsystem: Optional subsystem identifier

    Returns:
        Component identifier string
    """
    if subsystem:
        return subsystem
    if phase:
        return f"phase_{phase.lower()}"
    return "unknown"


def assign_error_code(
    error_type: str,
    phase: Optional[str] = None,
    transition: Optional[str] = None,
) -> str:
    """
    Assign error code based on error type and context.

    Args:
        error_type: Type of error (e.g., "VALIDATION", "TTL_EXPIRED")
        phase: Optional phase identifier
        transition: Optional transition identifier

    Returns:
        Error code string in format AEON.<TYPE>.<PHASE/TRANSITION>.<CODE>
    """
    base_code = f"AEON.{error_type}"
    if transition:
        # Normalize transition (A→B -> A_B)
        normalized = transition.replace("→", "_").replace("/", "_")
        return f"{base_code}.{normalized}.001"
    if phase:
        return f"{base_code}.{phase}.001"
    return f"{base_code}.001"


def create_error_record(
    error: Exception,
    phase: Optional[str] = None,
    subsystem: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    transition: Optional[str] = None,
) -> ErrorRecord:
    """
    Create structured error record from exception.

    Args:
        error: Exception to convert
        phase: Optional phase identifier
        subsystem: Optional subsystem identifier
        context: Optional additional context
        transition: Optional transition identifier

    Returns:
        ErrorRecord with error code, severity, message, and context
    """
    component = determine_component(phase, subsystem)

    # If error already has to_error_record method, use it
    if isinstance(error, AeonError):
        error_record = error.to_error_record(context=context)
        # Override component if specified
        if component != "unknown":
            error_record.affected_component = component
        return error_record

    # Determine error type from exception class name
    error_type = type(error).__name__.upper().replace("ERROR", "")
    if error_type.endswith("ERROR"):
        error_type = error_type[:-5]

    error_code = assign_error_code(error_type, phase, transition)

    from aeon.observability.models import ErrorSeverity

    return ErrorRecord(
        code=error_code,
        severity=ErrorSeverity.ERROR,
        message=str(error),
        affected_component=component,
        context=context or {},
        stack_trace="",
    )

