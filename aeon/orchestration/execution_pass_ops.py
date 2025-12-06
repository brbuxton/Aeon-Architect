"""ExecutionPass consistency and merging logic.

This module contains functions for building and merging ExecutionPass objects,
extracted from the kernel to reduce LOC.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from aeon.kernel.state import ExecutionPass

__all__ = [
    "build_execution_pass_before_phase",
    "build_execution_pass_after_phase",
    "merge_execution_results",
    "merge_evaluation_results",
    "apply_refinement_to_plan_state",
    "set_refinement_changes",
    "update_ttl_remaining",
    "get_execution_results",
    "get_refinement_changes",
]


def build_execution_pass_before_phase(
    pass_number: int,
    phase: Literal["A", "B", "C", "D"],
    plan_state: Dict[str, Any],
    ttl_remaining: int,
) -> ExecutionPass:
    """
    Build ExecutionPass object before phase entry.

    Args:
        pass_number: Pass number
        phase: Phase identifier
        plan_state: Plan state dictionary
        ttl_remaining: TTL cycles remaining

    Returns:
        ExecutionPass object with required before-phase fields
    """
    return ExecutionPass(
        pass_number=pass_number,
        phase=phase,
        plan_state=plan_state,
        ttl_remaining=ttl_remaining,
        timing_information={"start_time": datetime.now().isoformat()},
    )


def build_execution_pass_after_phase(
    execution_pass: ExecutionPass,
    end_time: Optional[datetime] = None,
) -> ExecutionPass:
    """
    Complete ExecutionPass object after phase exit.

    Args:
        execution_pass: ExecutionPass to complete
        end_time: Optional end time (defaults to now)

    Returns:
        Completed ExecutionPass with timing information
    """
    if end_time is None:
        end_time = datetime.now()

    start_time_str = (
        execution_pass.timing_information.get("start_time")
        if isinstance(execution_pass.timing_information, dict)
        else getattr(execution_pass.timing_information, "start_time", None)
    )

    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
            duration = (end_time - start_time).total_seconds()
        except Exception:
            duration = 0.0
    else:
        duration = 0.0

    if isinstance(execution_pass.timing_information, dict):
        execution_pass.timing_information["end_time"] = end_time.isoformat()
        execution_pass.timing_information["duration"] = duration
    else:
        setattr(execution_pass.timing_information, "end_time", end_time.isoformat())
        setattr(execution_pass.timing_information, "duration", duration)

    return execution_pass


def merge_execution_results(
    execution_pass: ExecutionPass,
    new_execution_results: List[Dict[str, Any]],
) -> ExecutionPass:
    """
    Merge execution results into ExecutionPass.

    Args:
        execution_pass: ExecutionPass to update
        new_execution_results: New execution results to merge

    Returns:
        Updated ExecutionPass
    """
    execution_pass.execution_results = new_execution_results
    return execution_pass


def merge_evaluation_results(
    execution_pass: ExecutionPass,
    evaluation_results: Dict[str, Any],
) -> ExecutionPass:
    """
    Merge evaluation results into ExecutionPass.

    Args:
        execution_pass: ExecutionPass to update
        evaluation_results: Evaluation results to merge

    Returns:
        Updated ExecutionPass
    """
    execution_pass.evaluation_results = evaluation_results
    return execution_pass


def apply_refinement_to_plan_state(
    execution_pass: ExecutionPass,
    refined_plan: Any,  # Plan
) -> ExecutionPass:
    """
    Apply refinement changes to ExecutionPass plan_state.

    Args:
        execution_pass: ExecutionPass to update
        refined_plan: Refined plan object

    Returns:
        Updated ExecutionPass with refined plan_state
    """
    execution_pass.plan_state = refined_plan.model_dump() if hasattr(refined_plan, "model_dump") else refined_plan
    return execution_pass


def set_refinement_changes(
    execution_pass: ExecutionPass,
    refinement_changes: List[Dict[str, Any]],
) -> ExecutionPass:
    """
    Set refinement changes on ExecutionPass.

    Args:
        execution_pass: ExecutionPass to update
        refinement_changes: List of refinement change dictionaries

    Returns:
        Updated ExecutionPass
    """
    execution_pass.refinement_changes = refinement_changes
    return execution_pass


def update_ttl_remaining(
    execution_pass: ExecutionPass,
    ttl_remaining: int,
) -> ExecutionPass:
    """
    Update TTL remaining on ExecutionPass.

    Args:
        execution_pass: ExecutionPass to update
        ttl_remaining: New TTL remaining value

    Returns:
        Updated ExecutionPass
    """
    execution_pass.ttl_remaining = ttl_remaining
    return execution_pass


def get_execution_results(
    execution_pass: ExecutionPass,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get execution results from ExecutionPass.

    Args:
        execution_pass: ExecutionPass to read from

    Returns:
        Execution results list or None if not present
    """
    return getattr(execution_pass, "execution_results", None)


def get_refinement_changes(
    execution_pass: ExecutionPass,
) -> Optional[List[Dict[str, Any]]]:
    """
    Get refinement changes from ExecutionPass.

    Args:
        execution_pass: ExecutionPass to read from

    Returns:
        Refinement changes list or None if not present
    """
    return getattr(execution_pass, "refinement_changes", None)

