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
    needs_refinement = evaluation_results.get("needs_refinement", False)
    
    # Check if explicitly marked as needing refinement
    if needs_refinement:
        return True

    # Check for validation issues
    validation_issues = evaluation_results.get("validation_issues", [])
    if validation_issues:
        # Check if any issues are critical or high severity
        for issue in validation_issues:
            severity = issue.get("severity") if isinstance(issue, dict) else getattr(issue, "severity", None)
            if severity in ("CRITICAL", "ERROR"):
                return True

    # Check convergence status
    convergence_assessment = evaluation_results.get("convergence_assessment", {})
    converged = convergence_assessment.get("converged", False) if isinstance(convergence_assessment, dict) else getattr(convergence_assessment, "converged", False)
    if not converged:
        return True

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
    converged = evaluation_results.get("converged", False)
    
    # Check convergence assessment if available
    convergence_assessment = evaluation_results.get("convergence_assessment", {})
    if isinstance(convergence_assessment, dict):
        assessment_converged = convergence_assessment.get("converged", False)
        if assessment_converged:
            return True
    elif hasattr(convergence_assessment, "converged"):
        if convergence_assessment.converged:
            return True

    return converged


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

