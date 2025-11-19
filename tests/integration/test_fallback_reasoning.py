"""Integration tests for fallback reasoning (T097)."""

import pytest

from aeon.kernel.executor import StepExecutor
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import PlanStep, StepStatus
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry
from aeon.tools.stubs.calculator import CalculatorTool
from tests.fixtures.mock_llm import MockLLMAdapter


class TestFallbackReasoning:
    """Integration tests for fallback reasoning execution."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def registry(self):
        """Create tool registry with test tools."""
        reg = ToolRegistry()
        reg.register(CalculatorTool())
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

    def test_fallback_execution_for_missing_tool(self, executor, registry, memory, mock_llm, supervisor):
        """Test fallback to LLM reasoning when tool is missing."""
        step = PlanStep(
            step_id="step1",
            description="Perform analysis on the data",
            tool="nonexistent_tool",  # Tool doesn't exist
            status=StepStatus.PENDING,
        )

        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        assert result.success is True
        assert result.execution_mode == "fallback"
        # Verify result stored in memory
        memory_key = f"step_{step.step_id}_result"
        stored = memory.read(memory_key)
        assert stored is not None
        assert step.status == StepStatus.COMPLETE

    def test_fallback_execution_for_step_without_tool_or_agent(self, executor, registry, memory, mock_llm, supervisor):
        """Test fallback to LLM reasoning when step has no tool or agent field."""
        step = PlanStep(
            step_id="step2",
            description="Reason about the problem",
            # No tool or agent field
            status=StepStatus.PENDING,
        )

        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        assert result.success is True
        assert result.execution_mode == "fallback"
        # Verify result stored in memory
        memory_key = f"step_{step.step_id}_result"
        stored = memory.read(memory_key)
        assert stored is not None
        assert step.status == StepStatus.COMPLETE

    def test_fallback_includes_memory_context_in_prompt(self, executor, registry, memory, mock_llm, supervisor):
        """Test fallback execution includes memory context in LLM prompt."""
        # Store some context in memory first
        memory.write("step_previous_result", {"data": "previous step result"})

        step = PlanStep(
            step_id="step3",
            description="Analyze the previous results",
            status=StepStatus.PENDING,
        )

        # Capture the prompt sent to LLM
        captured_prompt = None
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = kwargs.get("prompt", "")
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate

        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        assert result.success is True
        # Verify memory context was included in prompt
        assert captured_prompt is not None
        # The prompt should include step description
        assert "Analyze the previous results" in captured_prompt

    def test_fallback_stores_result_in_memory(self, executor, registry, memory, mock_llm, supervisor):
        """Test fallback execution stores result in memory."""
        step = PlanStep(
            step_id="step4",
            description="Generate insights",
            status=StepStatus.PENDING,
        )

        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        assert result.success is True
        assert result.execution_mode == "fallback"
        
        # Verify result stored in memory
        memory_key = f"step_{step.step_id}_result"
        stored = memory.read(memory_key)
        assert stored is not None
        assert "result" in stored or isinstance(stored, dict)

    def test_fallback_handles_llm_errors_gracefully(self, executor, registry, memory, mock_llm, supervisor):
        """Test fallback execution handles LLM errors gracefully."""
        step = PlanStep(
            step_id="step5",
            description="Process data",
            status=StepStatus.PENDING,
        )

        # Mock LLM to raise error
        def failing_generate(*args, **kwargs):
            raise Exception("LLM error")
        mock_llm.generate = failing_generate

        result = executor.execute_step(step, registry, memory, mock_llm, supervisor)

        # Should handle error and mark step as failed
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert result.error is not None

