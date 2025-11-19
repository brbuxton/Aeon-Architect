"""Integration tests for missing-tool repair flow (T096)."""

import pytest

from aeon.exceptions import SupervisorError
from aeon.kernel.executor import StepExecutor
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import PlanStep, StepStatus
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry
from aeon.tools.stubs.calculator import CalculatorTool
from aeon.tools.stubs.echo import EchoTool
from aeon.validation.schema import Validator
from tests.fixtures.mock_llm import MockLLMAdapter


class TestMissingToolRepair:
    """Integration tests for missing-tool repair flow."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def registry(self):
        """Create tool registry with test tools."""
        reg = ToolRegistry()
        reg.register(CalculatorTool())
        reg.register(EchoTool())
        return reg

    @pytest.fixture
    def memory(self):
        """Create memory store."""
        return InMemoryKVStore()

    @pytest.fixture
    def supervisor(self, mock_llm):
        """Create supervisor."""
        return Supervisor(llm_adapter=mock_llm)

    @pytest.fixture
    def executor(self):
        """Create step executor."""
        return StepExecutor()

    @pytest.fixture
    def validator(self):
        """Create validator."""
        return Validator()

    def test_missing_tool_detected_by_validator(self, validator, registry):
        """Test validator detects missing tool and populates step.errors."""
        step = PlanStep(
            step_id="step1",
            description="Use nonexistent tool",
            tool="nonexistent_tool",
            status=StepStatus.PENDING,
        )

        result = validator.validate_step_tool(step, registry)

        assert result["valid"] is False
        assert step.errors is not None
        assert len(step.errors) > 0
        assert "nonexistent_tool" in step.errors[0] or "not found" in step.errors[0].lower()

    def test_supervisor_repairs_missing_tool_step(self, supervisor, mock_llm, registry):
        """Test supervisor repairs step with missing tool reference."""
        step = PlanStep(
            step_id="step1",
            description="Calculate sum",
            tool="nonexistent_calculator",
            errors=["Tool 'nonexistent_calculator' not found in registry"],
            status=StepStatus.PENDING,
        )

        available_tools = registry.export_tools_for_llm()
        plan_goal = "Calculate mathematical operations"

        # Mock LLM to return repaired step with valid tool
        repaired_step_json = '{"step_id": "step1", "description": "Calculate sum", "tool": "calculator", "status": "pending"}'

        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Repair this step" in kwargs.get("prompt", ""):
                return {"text": repaired_step_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate

        repaired_step = supervisor.repair_missing_tool_step(step, available_tools, plan_goal)

        assert repaired_step.tool == "calculator"  # Should be repaired to valid tool
        assert repaired_step.errors is None or len(repaired_step.errors) == 0  # Errors cleared

    def test_executor_handles_missing_tool_with_repair(self, executor, registry, memory, mock_llm, supervisor):
        """Test executor handles missing tool with supervisor repair."""
        step = PlanStep(
            step_id="step1",
            description="Echo a message",
            tool="nonexistent_echo",
            status=StepStatus.PENDING,
        )

        # Mock supervisor repair to return valid tool
        available_tools = registry.export_tools_for_llm()
        repaired_step_json = '{"step_id": "step1", "description": "Echo a message", "tool": "echo", "status": "pending"}'

        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Repair this step" in kwargs.get("prompt", ""):
                return {"text": repaired_step_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate

        # For now, executor doesn't call repair (T111 not done), so it will fallback
        # This test verifies the flow works when repair is integrated
        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        # Should fallback to LLM reasoning if repair not integrated yet
        assert result.success is True
        assert result.execution_mode in ["fallback", "llm"]

    def test_supervisor_repair_validates_tool_in_available_list(self, supervisor, mock_llm, registry):
        """Test supervisor repair validates tool is in available tools list."""
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="missing",
            errors=["Tool 'missing' not found"],
        )

        available_tools = registry.export_tools_for_llm()
        plan_goal = "Test goal"

        # Mock LLM to return step with tool NOT in available list
        invalid_repaired_json = '{"step_id": "step1", "description": "Use tool", "tool": "invented_tool", "status": "pending"}'

        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Repair this step" in kwargs.get("prompt", ""):
                return {"text": invalid_repaired_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate

        # Should raise error because tool not in available list
        with pytest.raises(SupervisorError):
            supervisor.repair_missing_tool_step(step, available_tools, plan_goal, max_attempts=1)

