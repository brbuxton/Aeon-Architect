"""Unit tests for PlanExecutor."""

import pytest

from aeon.kernel.state import OrchestrationState
from aeon.plan.executor import PlanExecutor
from aeon.plan.models import Plan, PlanStep, StepStatus


def _build_plan(step_count: int = 2) -> Plan:
    """Helper to create a plan with a given number of steps."""
    steps = [
        PlanStep(step_id=f"step{i}", description=f"Step {i}", status=StepStatus.PENDING)
        for i in range(1, step_count + 1)
    ]
    return Plan(goal="Test goal", steps=steps)


class TestPlanExecutor:
    """Tests for sequential plan execution."""

    def test_execute_updates_step_statuses_in_order(self):
        """Executor should mark each step running before completion."""
        plan = _build_plan(step_count=2)
        state = OrchestrationState(plan=plan, ttl_remaining=5)
        call_order: list[str] = []

        def runner(step: PlanStep, state: OrchestrationState) -> None:
            call_order.append(step.step_id)
            # Runner sees the step marked as running with matching current_step_id
            assert step.status == StepStatus.RUNNING
            assert state.current_step_id == step.step_id

        executor = PlanExecutor(state=state, step_runner=runner)
        executor.execute()

        assert call_order == ["step1", "step2"]
        assert all(step.status == StepStatus.COMPLETE for step in state.plan.steps)
        assert state.current_step_id is None

    def test_execute_marks_failed_step_on_runner_exception(self):
        """Executor should mark the failing step as failed and raise PlanError."""
        from aeon.exceptions import PlanError

        plan = _build_plan(step_count=2)
        state = OrchestrationState(plan=plan, ttl_remaining=5)

        def runner(step: PlanStep, state: OrchestrationState) -> None:
            if step.step_id == "step2":
                raise RuntimeError("boom")

        executor = PlanExecutor(state=state, step_runner=runner)

        with pytest.raises(PlanError) as exc:
            executor.execute()

        assert "step2" in str(exc.value)
        assert plan.steps[0].status == StepStatus.COMPLETE
        assert plan.steps[1].status == StepStatus.FAILED
        assert state.current_step_id is None

