"""Unit tests for TTL counter and expiration."""

import pytest

from aeon.exceptions import TTLExpiredError
from aeon.kernel.state import OrchestrationState
from aeon.plan.models import Plan, PlanStep


def _create_mock_plan() -> Plan:
    """Helper to create a mock plan for testing."""
    steps = [
        PlanStep(step_id="step1", description="Test step 1", status="pending"),
        PlanStep(step_id="step2", description="Test step 2", status="pending"),
    ]
    return Plan(goal="Test goal", steps=steps)


class TestTTLCounter:
    """Test TTL counter functionality."""

    def test_ttl_initialized_in_state(self):
        """Test that TTL is initialized in OrchestrationState."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan, ttl_remaining=5)
        assert state.ttl_remaining == 5

    def test_ttl_default_value(self):
        """Test that TTL defaults to 10 if not specified."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan)
        assert state.ttl_remaining == 10

    def test_ttl_can_be_decremented(self):
        """Test that TTL can be decremented."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan, ttl_remaining=5)
        state.ttl_remaining -= 1
        assert state.ttl_remaining == 4

    def test_ttl_reaches_zero(self):
        """Test that TTL can reach zero."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan, ttl_remaining=1)
        state.ttl_remaining -= 1
        assert state.ttl_remaining == 0

    def test_ttl_can_go_negative(self):
        """Test that TTL can go negative (for testing expiration)."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan, ttl_remaining=1)
        state.ttl_remaining -= 2
        assert state.ttl_remaining == -1

    def test_ttl_expired_check(self):
        """Test checking if TTL has expired."""
        plan = _create_mock_plan()
        state = OrchestrationState(plan=plan, ttl_remaining=0)
        assert state.ttl_remaining <= 0  # Expired

        state2 = OrchestrationState(plan=plan, ttl_remaining=1)
        assert state2.ttl_remaining > 0  # Not expired

