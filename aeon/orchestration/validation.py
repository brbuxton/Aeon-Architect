"""Transition invariants validation logic.

This module contains functions for validating transition invariants,
extracted from the kernel to reduce LOC.
"""

from typing import Any, Dict, Literal, Optional

from aeon.exceptions import TTLExpiredError
from aeon.kernel.state import ExecutionPass, TTLExpirationResponse
from aeon.orchestration.ttl import check_ttl_before_phase_entry

__all__ = [
    "check_ttl_at_phase_boundary",
    "validate_correlation_id_invariance",
    "validate_execution_start_timestamp_invariance",
    "validate_ttl_remaining_positive",
]


def check_ttl_at_phase_boundary(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
    execution_pass: Optional[ExecutionPass] = None,
    pass_number: int = 0,
    plan_state: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Check TTL at phase boundary.

    Raises TTLExpiredError if TTL is exhausted.

    Args:
        ttl_remaining: Remaining TTL cycles
        phase: Current phase
        execution_pass: Optional execution pass for TTL check
        pass_number: Pass number if execution_pass not provided
        plan_state: Plan state dict if execution_pass not provided

    Raises:
        TTLExpiredError: If TTL is exhausted
    """
    if ttl_remaining <= 0:
        # Create a temporary execution pass for TTL check if not provided
        if execution_pass is None:
            temp_pass = ExecutionPass(
                pass_number=pass_number,
                phase=phase,
                plan_state=plan_state or {},
                ttl_remaining=0,
            )
        else:
            temp_pass = execution_pass

        can_proceed, expiration_response = check_ttl_before_phase_entry(
            ttl_remaining, phase, temp_pass
        )
        if not can_proceed and expiration_response:
            raise TTLExpiredError(
                f"TTL expired at phase {phase} boundary: {expiration_response.message}"
            )
        raise TTLExpiredError(f"TTL expired at phase {phase} boundary")


def validate_correlation_id_invariance(
    correlation_id: str,
    previous_correlation_id: Optional[str] = None,
) -> None:
    """
    Validate that correlation_id remains unchanged across transitions.

    Args:
        correlation_id: Current correlation_id
        previous_correlation_id: Previous correlation_id (if available)

    Raises:
        ValueError: If correlation_id changes unexpectedly
    """
    if previous_correlation_id is not None and correlation_id != previous_correlation_id:
        raise ValueError(
            f"Correlation ID invariance violated: {previous_correlation_id} -> {correlation_id}"
        )


def validate_execution_start_timestamp_invariance(
    execution_start_timestamp: str,
    previous_execution_start_timestamp: Optional[str] = None,
) -> None:
    """
    Validate that execution_start_timestamp remains unchanged across transitions.

    Args:
        execution_start_timestamp: Current execution_start_timestamp
        previous_execution_start_timestamp: Previous execution_start_timestamp (if available)

    Raises:
        ValueError: If execution_start_timestamp changes unexpectedly
    """
    if (
        previous_execution_start_timestamp is not None
        and execution_start_timestamp != previous_execution_start_timestamp
    ):
        raise ValueError(
            f"Execution start timestamp invariance violated: {previous_execution_start_timestamp} -> {execution_start_timestamp}"
        )


def validate_ttl_remaining_positive(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
) -> None:
    """
    Validate that TTL remaining is positive before phase entry.

    Args:
        ttl_remaining: TTL cycles remaining
        phase: Phase identifier

    Raises:
        TTLExpiredError: If TTL is not positive
    """
    if ttl_remaining <= 0:
        raise TTLExpiredError(
            f"TTL remaining must be positive before phase {phase} entry, got {ttl_remaining}"
        )

