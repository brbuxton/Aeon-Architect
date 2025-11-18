"""Integration tests for plan generation from natural language."""

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import Plan, StepStatus
from tests.fixtures.mock_llm import MockLLMAdapter


class TestPlanGeneration:
    """Integration tests for plan generation."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM adapter for testing."""
        return MockLLMAdapter()

    @pytest.fixture
    def orchestrator(self, mock_llm):
        """Create orchestrator instance."""
        memory = InMemoryKVStore()
        return Orchestrator(llm=mock_llm, memory=memory, ttl=10)

    def test_generate_plan_from_simple_request(self, orchestrator):
        """Test generating a plan from a simple natural language request."""
        request = "calculate the sum of 5 and 10"
        plan = orchestrator.generate_plan(request)
        
        assert isinstance(plan, Plan)
        assert plan.goal == request or "calculate" in plan.goal.lower()
        assert len(plan.steps) > 0
        assert all(step.status == StepStatus.PENDING for step in plan.steps)
        assert all(step.step_id for step in plan.steps)
        assert all(step.description for step in plan.steps)

    def test_generate_plan_from_complex_request(self, orchestrator):
        """Test generating a plan from a complex multi-step request."""
        request = "analyze a dataset, generate statistics, and create a report"
        plan = orchestrator.generate_plan(request)
        
        assert isinstance(plan, Plan)
        assert len(plan.steps) >= 2  # Should have multiple steps for complex request
        assert all(step.status == StepStatus.PENDING for step in plan.steps)

    def test_generate_plan_with_valid_structure(self, orchestrator):
        """Test that generated plan has valid structure."""
        request = "calculate the sum of 5 and 10"
        plan = orchestrator.generate_plan(request)
        
        # Validate plan structure
        assert plan.goal
        assert len(plan.steps) > 0
        step_ids = [step.step_id for step in plan.steps]
        assert len(step_ids) == len(set(step_ids))  # Unique step IDs

