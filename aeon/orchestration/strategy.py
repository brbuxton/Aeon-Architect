"""Refinement and evaluation decision logic.

This module contains functions for making decisions about refinement needs
and mapping convergence/evaluation output into next actions, extracted from
the kernel to reduce LOC.
"""

from typing import Any, Dict, Optional

__all__ = [
    "should_refine",
    "has_converged",
    "determine_next_action",
]


def should_refine(
    evaluation_results: Dict[str, Any],
) -> bool:
    """
    Determine if refinement is needed based on evaluation results.

    Args:
        evaluation_results: Evaluation results dictionary

    Returns:
        True if refinement is needed, False otherwise
    """
    # STUB: Disable refinement while implementing Memory
    return False


def has_converged(
    evaluation_results: Dict[str, Any],
) -> bool:
    """
    Determine if execution has converged based on evaluation results.

    Args:
        evaluation_results: Evaluation results dictionary

    Returns:
        True if converged, False otherwise
    """
    # STUB: Force convergence while implementing Memory
    return True


def determine_next_action(
    evaluation_results: Dict[str, Any],
    converged: bool,
) -> str:
    """
    Determine next action based on convergence and evaluation results.

    Args:
        evaluation_results: Evaluation results dictionary
        converged: Whether execution has converged

    Returns:
        Next action: "continue", "refine", or "converge"
    """
    if converged:
        return "converge"

    if should_refine(evaluation_results):
        return "refine"

    return "continue"

