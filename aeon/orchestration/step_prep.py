"""Step preparation logic for dependency checking and context population.

This module contains the StepPreparation class that handles step preparation,
including dependency checking, context population, and index population,
extracted from the kernel to reduce LOC.
"""

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from aeon.plan.models import Plan, PlanStep
    from aeon.memory.interface import Memory

__all__ = ["StepPreparation", "StepPreparationResult"]


# Data model: StepPreparationResult
# Structured result from step preparation operations.
#
# Fields (as direct return):
# - ready_steps (List[PlanStep], required): List of steps ready to execute
#
# Validation Rules:
# - ready_steps must be present (may be empty list)
# - All steps in ready_steps must have dependencies satisfied
#
# Note: Step preparation methods return List[PlanStep] directly (no error tuple)
# as dependency checking is deterministic and doesn't fail in ways that need
# error propagation.

# Type alias for step preparation result
StepPreparationResult = List["PlanStep"]


class StepPreparation:
    """Handles step preparation including dependency checking and context population."""

    def get_ready_steps(
        self,
        plan: "Plan",
        memory: Optional["Memory"],
    ) -> StepPreparationResult:
        """
        Get steps that are ready to execute (dependencies satisfied).

        Args:
            plan: Current plan
            memory: Memory interface (optional)

        Returns:
            List of PlanStep objects ready to execute
        """
        from aeon.plan.models import StepStatus

        ready_steps = []
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are complete
                dependencies_satisfied = True
                # Check for dependencies field (may not exist in all plans)
                dependencies = getattr(step, "dependencies", None)
                if dependencies:
                    for dep_id in dependencies:
                        dep_step = next(
                            (s for s in plan.steps if s.step_id == dep_id), None
                        )
                        if not dep_step or dep_step.status != StepStatus.COMPLETE:
                            dependencies_satisfied = False
                            break
                if dependencies_satisfied:
                    # Populate incoming_context from dependency outputs
                    self.populate_incoming_context(step, plan, memory)
                    ready_steps.append(step)
        return ready_steps

    def populate_incoming_context(
        self,
        step: "PlanStep",
        plan: "Plan",
        memory: Optional["Memory"],
    ) -> None:
        """
        Populate incoming_context from dependency step outputs.

        Args:
            step: PlanStep to populate context for
            plan: Current plan
            memory: Memory interface (optional)
        """
        if not memory:
            return

        dependencies = getattr(step, "dependencies", None)
        if not dependencies:
            return

        context_parts = []
        for dep_id in dependencies:
            # Try to get output from memory
            memory_key = f"step_{dep_id}_result"
            try:
                dep_output = memory.read(memory_key)
                if dep_output:
                    # Also check for handoff_to_next from the dependency step
                    dep_step = next(
                        (s for s in plan.steps if s.step_id == dep_id), None
                    )
                    if (
                        dep_step
                        and hasattr(dep_step, "handoff_to_next")
                        and dep_step.handoff_to_next
                    ):
                        context_parts.append(
                            f"From step {dep_id}: {dep_step.handoff_to_next}"
                        )
                    else:
                        context_parts.append(f"From step {dep_id}: {dep_output}")
            except Exception:
                # If memory read fails, continue without that context
                pass

        if context_parts and hasattr(step, "incoming_context"):
            step.incoming_context = "\n".join(context_parts)

    def populate_step_indices(self, plan: "Plan") -> None:
        """
        Populate step_index and total_steps for all steps in plan.

        Args:
            plan: Plan to populate indices for
        """
        total_steps = len(plan.steps)
        for idx, step in enumerate(plan.steps, start=1):
            if hasattr(step, "step_index"):
                step.step_index = idx
            if hasattr(step, "total_steps"):
                step.total_steps = total_steps

