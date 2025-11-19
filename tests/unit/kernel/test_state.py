"""Unit tests for OrchestrationState helpers."""

import pytest

from aeon.kernel.state import OrchestrationState
from aeon.plan.models import Plan, PlanStep, StepStatus


def _sample_plan() -> Plan:
    return Plan(
        goal="Sample",
        steps=[
            PlanStep(step_id="step1", description="First"),
            PlanStep(step_id="step2", description="Second"),
        ],
    )


class TestOrchestrationState:
    """Tests for state transition helpers."""

    def test_start_step_sets_current_and_status(self):
        state = OrchestrationState(plan=_sample_plan(), ttl_remaining=5)
        state.start_step("step1")
        assert state.current_step_id == "step1"
        assert state.plan.steps[0].status == StepStatus.RUNNING

    def test_complete_current_step_marks_complete_and_clears_current(self):
        state = OrchestrationState(plan=_sample_plan(), ttl_remaining=5)
        state.start_step("step1")
        state.complete_current_step()
        assert state.plan.steps[0].status == StepStatus.COMPLETE
        assert state.current_step_id is None

    def test_fail_current_step_marks_failed(self):
        state = OrchestrationState(plan=_sample_plan(), ttl_remaining=5)
        state.start_step("step1")
        state.fail_current_step(error="Test failure")
        assert state.plan.steps[0].status == StepStatus.FAILED
        assert state.current_step_id is None

    def test_start_step_raises_for_invalid_step(self):
        state = OrchestrationState(plan=_sample_plan(), ttl_remaining=5)
        with pytest.raises(ValueError):
            state.start_step("missing")

