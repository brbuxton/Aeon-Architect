"""ExecutionPass validation functions.

This module contains validation functions for ExecutionPass consistency,
ensuring required fields are populated before/after each phase and invariants
are maintained. This module is separate from aeon/kernel/state.py to maintain
kernel minimalism (Constitution Principle I).
"""

from typing import TYPE_CHECKING, Literal, Optional, Tuple

if TYPE_CHECKING:
    from aeon.kernel.state import ExecutionPass

__all__ = [
    "validate_execution_pass_before_phase",
    "validate_execution_pass_after_phase",
    "validate_execution_pass_invariants",
]


def validate_execution_pass_before_phase(
    execution_pass: "ExecutionPass",
    phase: Literal["A", "B", "C", "D"],
) -> Tuple[bool, Optional[str]]:
    """
    Validate ExecutionPass required fields before phase entry.

    Args:
        execution_pass: Execution pass to validate
        phase: Phase identifier

    Returns:
        Tuple of (is_valid, error_message)

    Required fields before phase entry:
    - pass_number (int, required): Sequential identifier
    - phase (enum, required): Current phase (A, B, C, D)
    - plan_state (dict, required): Snapshot of plan at pass start
    - ttl_remaining (int, required): TTL cycles remaining (>= 0)
    - timing_information.start_time (string, required): ISO 8601 timestamp of pass start
    """
    # Validate pass_number
    if not hasattr(execution_pass, "pass_number") or execution_pass.pass_number is None:
        return (False, "Missing required field: pass_number")

    if not isinstance(execution_pass.pass_number, int) or execution_pass.pass_number < 0:
        return (False, f"Invalid pass_number: {execution_pass.pass_number} (must be non-negative integer)")

    # Validate phase
    if not hasattr(execution_pass, "phase") or execution_pass.phase is None:
        return (False, "Missing required field: phase")

    if execution_pass.phase not in ("A", "B", "C", "D"):
        return (False, f"Invalid phase: {execution_pass.phase} (must be A, B, C, or D)")

    # Validate plan_state
    if not hasattr(execution_pass, "plan_state") or execution_pass.plan_state is None:
        return (False, "Missing required field: plan_state")

    # Validate ttl_remaining
    if not hasattr(execution_pass, "ttl_remaining") or execution_pass.ttl_remaining is None:
        return (False, "Missing required field: ttl_remaining")

    if not isinstance(execution_pass.ttl_remaining, int) or execution_pass.ttl_remaining < 0:
        return (False, f"Invalid ttl_remaining: {execution_pass.ttl_remaining} (must be non-negative integer)")

    # Validate timing_information.start_time
    if not hasattr(execution_pass, "timing_information") or execution_pass.timing_information is None:
        return (False, "Missing required field: timing_information")

    timing_info = execution_pass.timing_information
    if isinstance(timing_info, dict):
        if "start_time" not in timing_info or timing_info["start_time"] is None:
            return (False, "Missing required field: timing_information.start_time")
    else:
        if not hasattr(timing_info, "start_time") or timing_info.start_time is None:
            return (False, "Missing required field: timing_information.start_time")

    return (True, None)


def validate_execution_pass_after_phase(
    execution_pass: "ExecutionPass",
    phase: Literal["A", "B", "C", "D"],
) -> Tuple[bool, Optional[str]]:
    """
    Validate ExecutionPass required fields after phase exit.

    Args:
        execution_pass: Execution pass to validate
        phase: Phase identifier

    Returns:
        Tuple of (is_valid, error_message)

    Required fields after phase exit:
    - execution_results (list, required if Phase C): Step outputs and tool results
    - evaluation_results (dict, required if Phase C): Convergence assessment and semantic validation report
    - refinement_changes (list, required if Phase C refinement occurred): Plan/step modifications
    - timing_information.end_time (string, required): ISO 8601 timestamp of pass end
    - timing_information.duration (float, required): Duration in seconds
    """
    # Validate timing_information.end_time
    if not hasattr(execution_pass, "timing_information") or execution_pass.timing_information is None:
        return (False, "Missing required field: timing_information")

    timing_info = execution_pass.timing_information
    if isinstance(timing_info, dict):
        if "end_time" not in timing_info or timing_info["end_time"] is None:
            return (False, "Missing required field: timing_information.end_time")
        if "duration" not in timing_info or timing_info["duration"] is None:
            return (False, "Missing required field: timing_information.duration")
        if not isinstance(timing_info["duration"], (int, float)) or timing_info["duration"] < 0:
            return (False, f"Invalid duration: {timing_info['duration']} (must be non-negative number)")
    else:
        if not hasattr(timing_info, "end_time") or timing_info.end_time is None:
            return (False, "Missing required field: timing_information.end_time")
        if not hasattr(timing_info, "duration") or timing_info.duration is None:
            return (False, "Missing required field: timing_information.duration")
        if not isinstance(timing_info.duration, (int, float)) or timing_info.duration < 0:
            return (False, f"Invalid duration: {timing_info.duration} (must be non-negative number)")

    # Phase C specific validations
    if phase == "C":
        # Validate execution_results (required for Phase C)
        if not hasattr(execution_pass, "execution_results") or execution_pass.execution_results is None:
            return (False, "Missing required field: execution_results (required for Phase C)")

        if not isinstance(execution_pass.execution_results, list):
            return (False, f"Invalid execution_results: must be list, got {type(execution_pass.execution_results)}")

        # Validate evaluation_results (required for Phase C)
        if not hasattr(execution_pass, "evaluation_results") or execution_pass.evaluation_results is None:
            return (False, "Missing required field: evaluation_results (required for Phase C)")

        if not isinstance(execution_pass.evaluation_results, dict):
            return (False, f"Invalid evaluation_results: must be dict, got {type(execution_pass.evaluation_results)}")

        # Validate refinement_changes (required if Phase C refinement occurred)
        # Note: refinement_changes may be empty list if no refinement occurred
        if hasattr(execution_pass, "refinement_changes"):
            if execution_pass.refinement_changes is not None and not isinstance(
                execution_pass.refinement_changes, list
            ):
                return (
                    False,
                    f"Invalid refinement_changes: must be list, got {type(execution_pass.refinement_changes)}",
                )

    return (True, None)


def validate_execution_pass_invariants(
    execution_pass: "ExecutionPass",
    phase: Literal["A", "B", "C", "D"],
) -> Tuple[bool, Optional[str]]:
    """
    Validate ExecutionPass invariants.

    Args:
        execution_pass: Execution pass to validate
        phase: Phase identifier

    Returns:
        Tuple of (is_valid, error_message)

    Invariants:
    - execution_results contain step outputs and status
    - evaluation_results contain convergence assessment and validation report
    - No conflicts between execution_results and evaluation_results
    - Refinement_changes are correctly applied to plan_state
    - TTL decrements exactly once per cycle (A→B→C→D)
    """
    # Validate execution_results structure (if present)
    if hasattr(execution_pass, "execution_results") and execution_pass.execution_results is not None:
        if not isinstance(execution_pass.execution_results, list):
            return (False, "Invariant violation: execution_results must be list")

        # Validate each execution result has required fields
        for i, result in enumerate(execution_pass.execution_results):
            if not isinstance(result, dict):
                return (False, f"Invariant violation: execution_results[{i}] must be dict")
            # Check for step_id and status (minimal required fields)
            if "step_id" not in result:
                return (False, f"Invariant violation: execution_results[{i}] missing step_id")
            if "status" not in result:
                return (False, f"Invariant violation: execution_results[{i}] missing status")

    # Validate evaluation_results structure (if present)
    if hasattr(execution_pass, "evaluation_results") and execution_pass.evaluation_results is not None:
        if not isinstance(execution_pass.evaluation_results, dict):
            return (False, "Invariant violation: evaluation_results must be dict")

        # Check for convergence assessment (if Phase C)
        if phase == "C":
            if "convergence_assessment" not in execution_pass.evaluation_results:
                return (False, "Invariant violation: evaluation_results missing convergence_assessment (required for Phase C)")

    # Validate refinement_changes structure (if present)
    if hasattr(execution_pass, "refinement_changes") and execution_pass.refinement_changes is not None:
        if not isinstance(execution_pass.refinement_changes, list):
            return (False, "Invariant violation: refinement_changes must be list")

    # Note: TTL decrement validation is handled at cycle boundary, not per-phase
    # This invariant is validated by checking TTL decrements exactly once per complete cycle

    return (True, None)

