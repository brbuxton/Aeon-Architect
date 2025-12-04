"""Plan refinement logic for applying refinement actions.

This module contains the PlanRefinement class that applies refinement actions
to plans, extracted from the kernel to reduce LOC.
"""

from typing import TYPE_CHECKING, Any, List, Optional, Tuple

if TYPE_CHECKING:
    from aeon.plan.models import Plan, RefinementAction

__all__ = ["PlanRefinement", "RefinementResult"]


# Data model: RefinementResult
# Structured result from plan refinement operations.
#
# Fields (as tuple return):
# - success (boolean, required): Whether refinement application succeeded
# - updated_plan (Plan, optional): Updated plan after applying refinement actions
# - error (string, optional): Error message if success is False
#
# Validation Rules:
# - If success is True, updated_plan must be present
# - If success is False, error must be present
# - updated_plan must be a valid Plan structure

# Type alias for refinement result tuple
RefinementResult = Tuple[bool, "Plan", Optional[str]]


class PlanRefinement:
    """Applies refinement actions to plans."""

    def apply_actions(
        self,
        plan: "Plan",
        refinement_actions: List[Any],  # List[RefinementAction]
    ) -> RefinementResult:
        """
        Apply refinement actions to plan.

        Args:
            plan: Current plan
            refinement_actions: List of RefinementAction objects

        Returns:
            Tuple of (success, updated_plan, error_message)
        """
        from aeon.plan.models import PlanStep, RefinementAction

        try:
            updated_plan = plan  # Start with original plan

            for action in refinement_actions:
                if not isinstance(action, RefinementAction):
                    continue

                if action.action_type == "ADD":
                    if action.new_step:
                        # Create new PlanStep from new_step dict
                        new_step = PlanStep(**action.new_step)
                        updated_plan.steps.append(new_step)
                elif action.action_type == "MODIFY":
                    if action.target_step_id:
                        # Find step and update it
                        step = next(
                            (s for s in updated_plan.steps if s.step_id == action.target_step_id),
                            None,
                        )
                        if step and action.new_step:
                            # Update step fields from new_step dict
                            for key, value in action.new_step.items():
                                if hasattr(step, key):
                                    setattr(step, key, value)
                elif action.action_type == "REMOVE":
                    if action.target_step_id:
                        # Remove step from plan
                        updated_plan.steps = [
                            s for s in updated_plan.steps if s.step_id != action.target_step_id
                        ]
                elif action.action_type == "REPLACE":
                    if action.target_step_id and action.new_step:
                        # Replace step with new step
                        step_index = next(
                            (
                                i
                                for i, s in enumerate(updated_plan.steps)
                                if s.step_id == action.target_step_id
                            ),
                            None,
                        )
                        if step_index is not None:
                            new_step = PlanStep(**action.new_step)
                            updated_plan.steps[step_index] = new_step

            return (True, updated_plan, None)
        except Exception as e:
            # If action application fails, return error with original plan
            return (False, plan, str(e))

