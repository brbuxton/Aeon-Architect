"""Unit tests for plan models."""

import pytest

from aeon.plan.models import Plan, PlanStep, StepStatus


class TestPlanStep:
    """Test PlanStep model with tool/agent/errors fields."""

    def test_plan_step_with_tool_field(self):
        """Test PlanStep can be created with tool field."""
        step = PlanStep(
            step_id="step1",
            description="Execute calculator tool",
            tool="calculator",
        )
        assert step.step_id == "step1"
        assert step.description == "Execute calculator tool"
        assert step.tool == "calculator"
        assert step.agent is None
        assert step.errors is None
        assert step.status == StepStatus.PENDING

    def test_plan_step_with_agent_field(self):
        """Test PlanStep can be created with agent field."""
        step = PlanStep(
            step_id="step2",
            description="Use LLM reasoning",
            agent="llm",
        )
        assert step.step_id == "step2"
        assert step.description == "Use LLM reasoning"
        assert step.agent == "llm"
        assert step.tool is None
        assert step.errors is None

    def test_plan_step_with_both_tool_and_agent(self):
        """Test PlanStep with both tool and agent - tool takes precedence."""
        step = PlanStep(
            step_id="step3",
            description="Step with both fields",
            tool="calculator",
            agent="llm",
        )
        assert step.tool == "calculator"
        assert step.agent == "llm"
        # Tool takes precedence per spec, but both fields are stored

    def test_plan_step_with_errors_field(self):
        """Test PlanStep can be created with errors field."""
        step = PlanStep(
            step_id="step4",
            description="Step with errors",
            errors=["Tool 'invalid_tool' not found", "Invalid tool reference"],
        )
        assert step.errors == ["Tool 'invalid_tool' not found", "Invalid tool reference"]
        assert step.tool is None
        assert step.agent is None

    def test_plan_step_with_all_optional_fields(self):
        """Test PlanStep with all optional fields."""
        step = PlanStep(
            step_id="step5",
            description="Complete step",
            tool="calculator",
            agent="llm",
            errors=["Some error"],
            status=StepStatus.RUNNING,
        )
        assert step.tool == "calculator"
        assert step.agent == "llm"
        assert step.errors == ["Some error"]
        assert step.status == StepStatus.RUNNING

    def test_plan_step_errors_can_be_cleared(self):
        """Test that errors field can be cleared (not frozen)."""
        step = PlanStep(
            step_id="step6",
            description="Step with errors",
            errors=["Error 1"],
        )
        assert step.errors == ["Error 1"]
        
        # Clear errors (model is not frozen)
        step.errors = None
        assert step.errors is None
        
        # Or set to empty list
        step.errors = []
        assert step.errors == []

    def test_plan_step_serialization_with_tool(self):
        """Test PlanStep serialization includes tool field."""
        step = PlanStep(
            step_id="step7",
            description="Tool step",
            tool="calculator",
        )
        data = step.model_dump()
        assert data["tool"] == "calculator"
        assert "agent" in data
        assert data["agent"] is None

    def test_plan_step_serialization_with_agent(self):
        """Test PlanStep serialization includes agent field."""
        step = PlanStep(
            step_id="step8",
            description="LLM step",
            agent="llm",
        )
        data = step.model_dump()
        assert data["agent"] == "llm"
        assert "tool" in data
        assert data["tool"] is None

    def test_plan_step_serialization_with_errors(self):
        """Test PlanStep serialization includes errors field."""
        step = PlanStep(
            step_id="step9",
            description="Error step",
            errors=["Error message"],
        )
        data = step.model_dump()
        assert data["errors"] == ["Error message"]

    def test_plan_with_steps_containing_tool_fields(self):
        """Test Plan can contain steps with tool/agent fields."""
        plan = Plan(
            goal="Test goal",
            steps=[
                PlanStep(
                    step_id="step1",
                    description="Tool step",
                    tool="calculator",
                ),
                PlanStep(
                    step_id="step2",
                    description="LLM step",
                    agent="llm",
                ),
            ],
        )
        assert len(plan.steps) == 2
        assert plan.steps[0].tool == "calculator"
        assert plan.steps[1].agent == "llm"

    def test_plan_step_rejects_empty_tool_string(self):
        """Test PlanStep rejects empty tool string (T100)."""
        with pytest.raises(ValueError, match="Tool field cannot be empty"):
            PlanStep(step_id="step1", description="Step 1", tool="")

    def test_plan_step_rejects_whitespace_only_tool(self):
        """Test PlanStep rejects whitespace-only tool (T100)."""
        with pytest.raises(ValueError, match="Tool field cannot be empty"):
            PlanStep(step_id="step1", description="Step 1", tool="   ")

    def test_plan_step_accepts_valid_tool(self):
        """Test PlanStep accepts valid tool string (T100)."""
        step = PlanStep(step_id="step1", description="Step 1", tool="calculator")
        assert step.tool == "calculator"

    def test_plan_step_rejects_invalid_agent_value(self):
        """Test PlanStep rejects invalid agent value (T101)."""
        with pytest.raises(ValueError, match="Agent field must be 'llm'"):
            PlanStep(step_id="step1", description="Step 1", agent="human")

    def test_plan_step_accepts_llm_agent(self):
        """Test PlanStep accepts 'llm' agent value (T101)."""
        step = PlanStep(step_id="step1", description="Step 1", agent="llm")
        assert step.agent == "llm"

    def test_plan_step_normalizes_agent_case(self):
        """Test PlanStep normalizes agent case to lowercase (T101)."""
        step = PlanStep(step_id="step1", description="Step 1", agent="LLM")
        assert step.agent == "llm"

