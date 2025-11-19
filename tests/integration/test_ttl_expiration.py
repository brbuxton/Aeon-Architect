"""Integration tests for TTL expiration in orchestration."""

import pytest

from aeon.exceptions import TTLExpiredError
from aeon.kernel.orchestrator import Orchestrator
from aeon.plan.models import Plan, PlanStep
from tests.fixtures.mock_llm import MockLLMAdapter


class TestTTLExpiration:
    """Integration tests for TTL expiration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    def test_ttl_initialized_from_orchestrator(self, mock_llm):
        """Test that TTL is initialized from orchestrator and decrements after each step."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=5)
        steps = [
            PlanStep(step_id="step1", description="Test step 1", status="pending"),
            PlanStep(step_id="step2", description="Test step 2", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        result = orchestrator.execute("test", plan=plan)
        # TTL starts at 5, decrements by 1 after each step (2 steps), so should be 3
        assert result["ttl_remaining"] == 3

    def test_ttl_expires_during_execution(self, mock_llm):
        """Test that TTL expiration stops execution gracefully."""
        # Create a plan with many steps
        steps = [
            PlanStep(step_id=f"step_{i}", description=f"Step {i}", status="pending")
            for i in range(10)
        ]
        plan = Plan(goal="Test goal with many steps", steps=steps)

        # Set TTL to 2 (should expire after 2 steps complete, TTL becomes 0)
        orchestrator = Orchestrator(llm=mock_llm, ttl=2)

        # Execute and expect TTL expiration
        result = orchestrator.execute("test", plan=plan)

        # Should return TTL expired status
        assert result["status"] == "ttl_expired"
        assert result["ttl_remaining"] <= 0
        assert "error" in result
        assert "TTL expired" in result["error"]

    def test_ttl_expired_response_structure(self, mock_llm):
        """Test that TTL expired response has correct structure."""
        # Create a plan with many steps
        steps = [
            PlanStep(step_id=f"step_{i}", description=f"Step {i}", status="pending")
            for i in range(10)
        ]
        plan = Plan(goal="Test goal with many steps", steps=steps)

        orchestrator = Orchestrator(llm=mock_llm, ttl=1)

        # Should return structured TTL expired response
        result = orchestrator.execute("test", plan=plan)
        assert result["status"] == "ttl_expired"
        assert "ttl_remaining" in result
        assert result["ttl_remaining"] <= 0
        assert "plan" in result
        assert "error" in result
        assert "TTL expired" in result["error"]

    def test_ttl_not_expired_completes_normally(self, mock_llm):
        """Test that execution completes normally when TTL doesn't expire."""
        # Create a plan with few steps
        steps = [
            PlanStep(step_id="step_1", description="Step 1", status="pending"),
            PlanStep(step_id="step_2", description="Step 2", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)

        orchestrator = Orchestrator(llm=mock_llm, ttl=10)

        result = orchestrator.execute("test", plan=plan)
        assert result["status"] == "completed"
        assert result["ttl_remaining"] >= 0

    def test_ttl_decrements_after_each_step(self, mock_llm):
        """Test that TTL decrements after each step execution."""
        steps = [
            PlanStep(step_id="step_1", description="Step 1", status="pending"),
            PlanStep(step_id="step_2", description="Step 2", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)

        orchestrator = Orchestrator(llm=mock_llm, ttl=5)

        result = orchestrator.execute("test", plan=plan)
        # TTL starts at 5, decrements by 1 after each step (2 steps), so should be 3
        assert result["ttl_remaining"] == 3
        assert result["status"] == "completed"

