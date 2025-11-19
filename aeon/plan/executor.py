"""Sequential plan executor."""

from __future__ import annotations

from typing import Callable, Optional

from aeon.exceptions import PlanError, TTLExpiredError
from aeon.kernel.state import OrchestrationState
from aeon.plan.models import PlanStep

StepRunner = Callable[[PlanStep, OrchestrationState], None]


class PlanExecutor:
    """Execute plan steps sequentially with deterministic status updates."""

    def __init__(
        self,
        state: OrchestrationState,
        step_runner: Optional[StepRunner] = None,
    ) -> None:
        if state is None:
            raise ValueError("state is required")
        self.state = state
        self._step_runner = step_runner or self._noop_runner

    def execute(self) -> None:
        """Execute each plan step sequentially."""
        for step in self.state.plan.steps:
            # Check TTL before executing step
            if self.state.ttl_remaining <= 0:
                raise TTLExpiredError("TTL expired before step execution")
            
            self._run_step(step)
            
            # Decrement TTL after step execution
            self.state.ttl_remaining -= 1
            
            # Check TTL after decrement
            if self.state.ttl_remaining < 0:
                raise TTLExpiredError("TTL expired during step execution")

    def _run_step(self, step: PlanStep) -> None:
        """Execute a single step with status transitions."""
        self.state.start_step(step.step_id)
        try:
            self._step_runner(step, self.state)
        except TTLExpiredError:
            # Re-raise TTL expiration without marking step as failed
            raise
        except Exception as exc:
            self.state.fail_current_step(error=str(exc))
            raise PlanError(f"Step '{step.step_id}' failed: {exc}") from exc
        else:
            self.state.complete_current_step()

    @staticmethod
    def _noop_runner(step: PlanStep, state: OrchestrationState) -> None:
        """Default runner used until specific step handlers are implemented."""
        return None

