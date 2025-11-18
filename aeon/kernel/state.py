"""Orchestration state management."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aeon.plan.models import Plan, PlanStep, StepStatus


@dataclass
class OrchestrationState:
    """Current execution context maintained by the kernel."""

    plan: Plan
    current_step_id: Optional[str] = None
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    llm_outputs: List[Dict[str, Any]] = field(default_factory=list)
    supervisor_actions: List[Dict[str, Any]] = field(default_factory=list)
    ttl_remaining: int = 10

    def get_current_step(self) -> Optional[PlanStep]:
        """Get the current step object if available."""
        if not self.current_step_id:
            return None
        for step in self.plan.steps:
            if step.step_id == self.current_step_id:
                return step
        return None

    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """Update the status of a step."""
        for step in self.plan.steps:
            if step.step_id == step_id:
                step.status = status
                return
        raise ValueError(f"Step '{step_id}' not found in plan.")

    def start_step(self, step_id: str) -> None:
        """Mark a step as running and set it as the current step."""
        self.update_step_status(step_id, StepStatus.RUNNING)
        self.current_step_id = step_id

    def complete_current_step(self) -> None:
        """Mark the current step as complete and clear the pointer."""
        if not self.current_step_id:
            raise ValueError("No step is currently running.")
        self.update_step_status(self.current_step_id, StepStatus.COMPLETE)
        self.current_step_id = None

    def fail_current_step(self, error: Optional[str] = None) -> None:
        """Mark the current step as failed and clear the pointer."""
        if not self.current_step_id:
            raise ValueError("No step is currently running.")
        self.update_step_status(self.current_step_id, StepStatus.FAILED)
        self.current_step_id = None
        if error:
            self.supervisor_actions.append({"type": "step_failure", "message": error})



