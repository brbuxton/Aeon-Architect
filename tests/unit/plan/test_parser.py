"""Unit tests for plan parser."""

import json
import pytest

from aeon.exceptions import PlanError
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.plan.parser import PlanParser


class TestPlanParser:
    """Test PlanParser implementation."""

    def test_parse_valid_json_plan(self):
        """Test parsing a valid JSON plan."""
        parser = PlanParser()
        plan_json = {
            "goal": "Calculate the sum of 5 and 10",
            "steps": [
                {"step_id": "step1", "description": "Add 5 and 10", "status": "pending"},
            ],
        }
        plan = parser.parse(json.dumps(plan_json))
        assert isinstance(plan, Plan)
        assert plan.goal == "Calculate the sum of 5 and 10"
        assert len(plan.steps) == 1
        assert plan.steps[0].step_id == "step1"
        assert plan.steps[0].description == "Add 5 and 10"
        assert plan.steps[0].status == StepStatus.PENDING

    def test_parse_malformed_json(self):
        """Test parsing malformed JSON raises PlanError."""
        parser = PlanParser()
        with pytest.raises(PlanError):
            parser.parse("{ invalid json }")

    def test_parse_invalid_plan_structure(self):
        """Test parsing invalid plan structure."""
        parser = PlanParser()
        invalid_json = {"invalid": "structure"}
        with pytest.raises(PlanError):
            parser.parse(json.dumps(invalid_json))

    def test_parse_plan_with_multiple_steps(self):
        """Test parsing plan with multiple steps."""
        parser = PlanParser()
        plan_json = {
            "goal": "Complex task",
            "steps": [
                {"step_id": "step1", "description": "First step", "status": "pending"},
                {"step_id": "step2", "description": "Second step", "status": "pending"},
                {"step_id": "step3", "description": "Third step", "status": "pending"},
            ],
        }
        plan = parser.parse(json.dumps(plan_json))
        assert len(plan.steps) == 3
        assert all(step.status == StepStatus.PENDING for step in plan.steps)

    def test_parse_plan_with_duplicate_step_ids(self):
        """Test parsing plan with duplicate step IDs raises error."""
        parser = PlanParser()
        plan_json = {
            "goal": "Task with duplicates",
            "steps": [
                {"step_id": "step1", "description": "First step", "status": "pending"},
                {"step_id": "step1", "description": "Duplicate step", "status": "pending"},
            ],
        }
        with pytest.raises(PlanError):
            parser.parse(json.dumps(plan_json))







