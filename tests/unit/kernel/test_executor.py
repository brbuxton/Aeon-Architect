"""Unit tests for StepExecutor."""

import pytest

from aeon.exceptions import ValidationError
from aeon.kernel.executor import StepExecutor, StepExecutionResult
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import PlanStep, StepStatus
from aeon.tools.interface import Tool
from aeon.tools.registry import ToolRegistry
from tests.fixtures.mock_llm import MockLLMAdapter


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name: str, description: str = "Test tool"):
        self.name = name
        self.description = description
        self.input_schema = {"type": "object", "properties": {"value": {"type": "string"}}}
        self.output_schema = {"type": "object", "properties": {"result": {"type": "string"}}}

    def invoke(self, **kwargs):
        """Mock invoke."""
        return {"result": f"Tool {self.name} executed with {kwargs}"}


class TestStepExecutorRouting:
    """Test StepExecutor routing logic (T089)."""

    def test_execute_step_routes_to_tool_when_tool_present(self):
        """Test execute_step routes to tool execution when step.tool is present and valid."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        llm = MockLLMAdapter()
        
        # Mock supervisor (not used for tool steps)
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        assert isinstance(result, StepExecutionResult)
        assert result.execution_mode == "tool"
        assert result.success is True
        assert step.status == StepStatus.COMPLETE

    def test_execute_step_routes_to_llm_when_agent_llm_present(self):
        """Test execute_step routes to LLM reasoning when step.agent == 'llm'."""
        registry = ToolRegistry()
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"reasoning prompt": '{"result": "LLM reasoning output"}'})
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step2",
            description="Use LLM reasoning",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        assert isinstance(result, StepExecutionResult)
        assert result.execution_mode == "llm"
        assert result.success is True
        assert step.status == StepStatus.COMPLETE

    def test_execute_step_routes_to_fallback_when_tool_missing(self):
        """Test execute_step routes to fallback when tool is missing/invalid."""
        registry = ToolRegistry()
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"fallback prompt": '{"result": "Fallback output"}'})
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step3",
            description="Step with missing tool",
            tool="nonexistent_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        assert isinstance(result, StepExecutionResult)
        assert result.execution_mode == "fallback"
        assert result.success is True
        assert step.status == StepStatus.COMPLETE

    def test_execute_step_tool_takes_precedence_over_agent(self):
        """Test that tool field takes precedence over agent field."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        llm = MockLLMAdapter()
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step4",
            description="Step with both tool and agent",
            tool="calculator",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        # Tool should take precedence
        assert result.execution_mode == "tool"


class TestToolBasedExecution:
    """Test tool-based step execution (T090)."""

    def test_execute_tool_step_invokes_tool(self):
        """Test execute_tool_step invokes the tool correctly."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory)
        
        assert result.success is True
        assert result.execution_mode == "tool"
        assert "result" in result.result
        assert step.status == StepStatus.COMPLETE

    def test_execute_tool_step_stores_result_in_memory(self):
        """Test execute_tool_step stores result in memory."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
        )
        
        result = executor.execute_tool_step(step, registry, memory)
        
        # Check memory contains result
        stored = memory.read(f"step_{step.step_id}_result")
        assert stored is not None
        assert stored == result.result

    def test_execute_tool_step_marks_failed_on_tool_error(self):
        """Test execute_tool_step marks step as failed when tool raises error."""
        registry = ToolRegistry()
        
        class FailingTool(Tool):
            def __init__(self):
                self.name = "failing_tool"
                self.description = "Tool that fails"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                raise Exception("Tool execution failed")
        
        tool = FailingTool()
        registry.register(tool)
        memory = InMemoryKVStore()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use failing tool",
            tool="failing_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert result.error is not None


class TestLLMReasoningExecution:
    """Test LLM reasoning step execution (T091)."""

    def test_execute_llm_reasoning_step_invokes_llm(self):
        """Test execute_llm_reasoning_step invokes LLM with reasoning prompt."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"reasoning": '{"result": "LLM output"}'})
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use LLM reasoning",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        assert result.execution_mode == "llm"
        assert "result" in result.result
        assert step.status == StepStatus.COMPLETE
        # Verify LLM was called
        assert len(llm.calls) > 0

    def test_execute_llm_reasoning_step_includes_memory_context(self):
        """Test execute_llm_reasoning_step includes memory context in prompt."""
        memory = InMemoryKVStore()
        memory.write("context_key", "context_value")
        llm = MockLLMAdapter()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use LLM with context",
            agent="llm",
        )
        
        executor.execute_llm_reasoning_step(step, memory, llm)
        
        # Check that memory context was included in prompt
        assert len(llm.calls) > 0
        call = llm.calls[0]
        assert "context" in call["prompt"].lower() or "memory" in call["prompt"].lower()

    def test_execute_llm_reasoning_step_stores_result_in_memory(self):
        """Test execute_llm_reasoning_step stores result in memory."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"reasoning": '{"result": "LLM output"}'})
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use LLM",
            agent="llm",
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        # Check memory contains result
        stored = memory.read(f"step_{step.step_id}_result")
        assert stored is not None


class TestFallbackExecution:
    """Test fallback execution (T092)."""

    def test_execute_step_fallback_when_tool_missing(self):
        """Test execute_step falls back to LLM when tool is missing."""
        registry = ToolRegistry()  # Empty registry
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"fallback": '{"result": "Fallback output"}'})
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Step with missing tool",
            tool="nonexistent",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        assert result.execution_mode == "fallback"
        assert result.success is True
        assert step.status == StepStatus.COMPLETE

    def test_execute_step_fallback_uses_step_description_as_prompt(self):
        """Test fallback execution uses step description as prompt."""
        registry = ToolRegistry()
        memory = InMemoryKVStore()
        llm = MockLLMAdapter()
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="This is the fallback prompt",
            tool="missing_tool",
        )
        
        executor.execute_step(step, registry, memory, llm, supervisor)
        
        # Check that step description was used in prompt
        assert len(llm.calls) > 0
        call = llm.calls[-1]  # Last call should be fallback
        assert "This is the fallback prompt" in call["prompt"]

    def test_execute_step_fallback_stores_result_in_memory(self):
        """Test fallback execution stores result in memory."""
        registry = ToolRegistry()
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"fallback": '{"result": "Fallback result"}'})
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Fallback step",
            tool="missing",
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor)
        
        # Check memory contains result
        stored = memory.read(f"step_{step.step_id}_result")
        assert stored is not None

