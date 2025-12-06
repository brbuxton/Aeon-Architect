"""TTL expiration response generation logic.

This module contains the TTLStrategy class that generates TTL expiration responses,
extracted from the kernel to reduce LOC.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple

if TYPE_CHECKING:
    from aeon.kernel.state import ExecutionPass, OrchestrationState

__all__ = [
    "TTLStrategy",
    "TTLExpirationResult",
    "check_ttl_before_phase_entry",
    "check_ttl_after_llm_call",
    "decrement_ttl_per_cycle",
]


# Data model: TTLExpirationResult
# Structured result from TTL expiration response generation.
#
# Fields (as tuple return):
# - success (boolean, required): Whether expiration response generation succeeded
# - response (Dict[str, Any], optional): TTL expiration response dict
# - error (string, optional): Error message if success is False
#
# Validation Rules:
# - If success is True, response must be present
# - If success is False, error must be present
# - response must contain: execution_history, status, ttl_expiration, ttl_remaining

# Type alias for TTL expiration result tuple
TTLExpirationResult = Tuple[bool, Dict[str, Any], Optional[str]]


class TTLStrategy:
    """Generates TTL expiration responses."""

    def create_expiration_response(
        self,
        expiration_type: Literal["phase_boundary", "mid_phase"],
        phase: Literal["A", "B", "C", "D"],
        execution_pass: "ExecutionPass",
        execution_passes: List["ExecutionPass"],
        state: Optional["OrchestrationState"],
        execution_id: str,
        task_input: str,
    ) -> TTLExpirationResult:
        """
        Create TTL expiration response.

        Args:
            expiration_type: Where TTL expired (phase_boundary or mid_phase)
            phase: Phase where expiration occurred
            execution_pass: Last execution pass
            execution_passes: All execution passes
            state: Current orchestration state (may be None)
            execution_id: Execution ID for ExecutionHistory
            task_input: Original task input

        Returns:
            Tuple of (success, response_dict, error_message)
        """
        from aeon.kernel.state import ExecutionHistory, TTLExpirationResponse

        try:
            ttl_remaining = state.ttl_remaining if state else 0

            expiration_response = TTLExpirationResponse(
                expiration_type=expiration_type,
                phase=phase,
                pass_number=execution_pass.pass_number,
                ttl_remaining=ttl_remaining,
                plan_state=execution_pass.plan_state,
                execution_results=execution_pass.execution_results,
                message=f"TTL expired {expiration_type} during phase {phase} at pass {execution_pass.pass_number}",
            )

            # Build ExecutionHistory with partial results
            execution_history = ExecutionHistory(
                execution_id=execution_id,
                task_input=task_input,
                configuration={},
                passes=execution_passes,
                final_result={
                    "status": "ttl_expired",
                    "expiration": expiration_response.model_dump(),
                },
                overall_statistics={
                    "total_passes": len(execution_passes),
                    "total_refinements": sum(
                        len(p.refinement_changes) for p in execution_passes
                    ),
                    "convergence_achieved": False,
                    "total_time": 0.0,
                },
            )

            response_dict = {
                "execution_history": execution_history.model_dump(),
                "status": "ttl_expired",
                "ttl_expiration": expiration_response.model_dump(),
                "ttl_remaining": ttl_remaining,
            }

            return (True, response_dict, None)
        except Exception as e:
            # If response generation fails, return error
            return (False, {}, str(e))


def check_ttl_before_phase_entry(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
    execution_pass: "ExecutionPass",
) -> Tuple[bool, Optional["TTLExpirationResponse"]]:
    """
    Check TTL before phase entry.

    Args:
        ttl_remaining: TTL cycles remaining
        phase: Phase identifier
        execution_pass: Current execution pass

    Returns:
        Tuple of (can_proceed, ttl_expiration_response)
        - If ttl_remaining > 0, returns (True, None)
        - If ttl_remaining == 0, returns (False, TTLExpirationResponse with expiration_type="phase_boundary")
    """
    from aeon.kernel.state import TTLExpirationResponse

    if ttl_remaining > 0:
        return (True, None)

    # TTL expired at phase boundary
    expiration_response = TTLExpirationResponse(
        expiration_type="phase_boundary",
        phase=phase,
        pass_number=execution_pass.pass_number,
        ttl_remaining=0,
        plan_state=execution_pass.plan_state,
        execution_results=execution_pass.execution_results,
        message=f"TTL expired at phase boundary before entering phase {phase} at pass {execution_pass.pass_number}",
    )

    return (False, expiration_response)


def check_ttl_after_llm_call(
    ttl_remaining: int,
    phase: Literal["A", "B", "C", "D"],
    execution_pass: "ExecutionPass",
) -> Tuple[bool, Optional["TTLExpirationResponse"]]:
    """
    Check TTL after LLM call within phase.

    Args:
        ttl_remaining: TTL cycles remaining
        phase: Phase identifier
        execution_pass: Current execution pass

    Returns:
        Tuple of (can_proceed, ttl_expiration_response)
        - If ttl_remaining > 0, returns (True, None)
        - If ttl_remaining == 0, returns (False, TTLExpirationResponse with expiration_type="mid_phase")
    """
    from aeon.kernel.state import TTLExpirationResponse

    if ttl_remaining > 0:
        return (True, None)

    # TTL expired mid-phase
    expiration_response = TTLExpirationResponse(
        expiration_type="mid_phase",
        phase=phase,
        pass_number=execution_pass.pass_number,
        ttl_remaining=0,
        plan_state=execution_pass.plan_state,
        execution_results=execution_pass.execution_results,
        message=f"TTL expired mid-phase during phase {phase} at pass {execution_pass.pass_number}",
    )

    return (False, expiration_response)


def decrement_ttl_per_cycle(ttl_remaining: int) -> int:
    """
    Decrement TTL exactly once per cycle.

    Args:
        ttl_remaining: Current TTL cycles remaining

    Returns:
        Decremented TTL (ttl_remaining - 1)

    Behavior:
        - Decrements TTL by exactly 1
        - Called once per complete cycle (A→B→C→D)
        - Returns max(0, ttl_remaining - 1) to prevent negative values
    """
    return max(0, ttl_remaining - 1)

