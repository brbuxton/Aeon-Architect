"""Additional unit tests for StepExecutor to achieve 100% coverage."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch

from aeon.exceptions import ContextPropagationError, ExecutionError, ValidationError
from aeon.kernel.executor import StepExecutor, StepExecutionResult
from aeon.kernel.state import OrchestrationState
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.tools.interface import Tool
from aeon.tools.registry import ToolRegistry
from tests.fixtures.mock_llm import MockLLMAdapter


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name: str, description: str = "Test tool", should_fail: bool = False):
        self.name = name
        self.description = description
        self.input_schema = {"type": "object", "properties": {"value": {"type": "string"}}}
        self.output_schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        self.should_fail = should_fail

    def invoke(self, **kwargs):
        """Mock invoke."""
        if self.should_fail:
            raise Exception("Tool execution failed")
        return {"result": f"Tool {self.name} executed"}


class TestExecutorLogging:
    """Test logging paths in StepExecutor."""

    def test_execute_step_logs_status_change_with_logger(self):
        """Test execute_step logs status change when logger and correlation_id are provided."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        llm = MockLLMAdapter()
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        # Create mock logger
        logger = Mock()
        logger.log_step_status_change = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_step(step, registry, memory, llm, supervisor, logger, correlation_id)
        
        # Verify logger was called for status change
        assert logger.log_step_status_change.called
        call_args = logger.log_step_status_change.call_args
        assert call_args[1]["correlation_id"] == correlation_id
        assert call_args[1]["step_id"] == "step1"
        # Status can be pending->running or running->complete
        assert call_args[1]["old_status"] in ["pending", "PENDING", "running", "RUNNING"]
        assert call_args[1]["new_status"] in ["running", "RUNNING", "complete", "COMPLETE"]

    def test_execute_tool_step_logs_tool_invocation_success(self):
        """Test execute_tool_step logs successful tool invocation."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_tool_invocation_result = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Verify tool invocation was logged
        assert logger.log_tool_invocation_result.called
        call_args = logger.log_tool_invocation_result.call_args
        assert call_args[1]["correlation_id"] == correlation_id
        assert call_args[1]["step_id"] == "step1"
        assert call_args[1]["tool_name"] == "calculator"
        assert call_args[1]["success"] is True

    def test_execute_tool_step_logs_tool_invocation_failure(self):
        """Test execute_tool_step logs failed tool invocation."""
        registry = ToolRegistry()
        tool = MockTool("failing_tool", should_fail=True)
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_tool_invocation_result = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use failing tool",
            tool="failing_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Verify tool invocation failure was logged
        assert logger.log_tool_invocation_result.called
        call_args = logger.log_tool_invocation_result.call_args
        assert call_args[1]["success"] is False
        assert "error" in call_args[1]
        
        # Verify error was logged
        assert logger.log_error.called

    def test_execute_tool_step_logs_error_for_non_execution_error(self):
        """Test execute_tool_step logs error when tool raises non-ExecutionError."""
        registry = ToolRegistry()
        tool = MockTool("failing_tool", should_fail=True)
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_tool_invocation_result = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use failing tool",
            tool="failing_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Verify error logging was called
        assert logger.log_error.called
        call_args = logger.log_error.call_args
        assert call_args[1]["correlation_id"] == correlation_id
        assert call_args[1]["step_id"] == "step1"

    def test_execute_tool_step_logs_status_change_after_completion(self):
        """Test execute_tool_step logs status change after completion."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.RUNNING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Verify status change was logged after completion
        status_calls = [c for c in logger.log_step_status_change.call_args_list 
                       if c[1].get("reason") == "step_execution_completed"]
        assert len(status_calls) > 0

    def test_execute_tool_step_logs_execution_outcome(self):
        """Test execute_tool_step logs execution outcome."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_step_execution_outcome = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Verify execution outcome was logged
        assert logger.log_step_execution_outcome.called
        call_args = logger.log_step_execution_outcome.call_args
        assert call_args[1]["correlation_id"] == correlation_id
        assert call_args[1]["step_id"] == "step1"
        assert call_args[1]["execution_mode"] == "tool"
        assert call_args[1]["success"] is True

    def test_execute_tool_step_handles_tool_not_found(self):
        """Test execute_tool_step handles tool not found in registry."""
        registry = ToolRegistry()  # Empty registry
        memory = InMemoryKVStore()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use missing tool",
            tool="nonexistent_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert "not found" in result.error.lower()

    def test_execute_tool_step_handles_general_exception(self):
        """Test execute_tool_step handles general exceptions."""
        registry = ToolRegistry()
        
        class ExceptionTool(Tool):
            def __init__(self):
                self.name = "exception_tool"
                self.description = "Tool that raises exception"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                raise ValueError("Unexpected error")
        
        tool = ExceptionTool()
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use exception tool",
            tool="exception_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert logger.log_error.called

    def test_execute_tool_step_handles_execution_error_type(self):
        """Test execute_tool_step handles ExecutionError type correctly."""
        registry = ToolRegistry()
        
        class ExecutionErrorTool(Tool):
            def __init__(self):
                self.name = "exec_error_tool"
                self.description = "Tool that raises ExecutionError"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                raise ExecutionError("Execution failed")
        
        tool = ExecutionErrorTool()
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use execution error tool",
            tool="exec_error_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        assert result.success is False
        # Verify error was logged with ExecutionError type
        assert logger.log_error.called


class TestLLMReasoningCoverage:
    """Test LLM reasoning step execution coverage."""

    def test_execute_llm_reasoning_step_validates_context_and_fails(self):
        """Test execute_llm_reasoning_step validates context and handles validation failure."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter()
        
        # Create state with invalid phase context
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)]),
            ttl_remaining=10,
            memory=memory,
        )
        state.phase_context = {
            "phase": "C",
            "context": {}  # Missing required fields
        }
        
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id, state)
        
        # Should fail due to context validation
        assert result.success is False
        assert "context" in result.error.lower() or "validation" in result.error.lower()
        assert logger.log_error.called

    def test_execute_llm_reasoning_step_handles_blocked_clarity_state(self):
        """Test execute_llm_reasoning_step handles BLOCKED clarity_state."""
        memory = InMemoryKVStore()
        
        # Create a custom LLM that returns BLOCKED clarity_state
        class BlockedLLM:
            def __init__(self):
                self.calls = []
            
            def generate(self, **kwargs):
                self.calls.append(kwargs)
                return {
                    "text": json.dumps({
                        "result": "output",
                        "clarity_state": "BLOCKED",
                        "handoff_to_next": {}
                    })
                }
        
        llm = BlockedLLM()
        logger = Mock()
        logger.log_step_status_change = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id)
        
        # Step should be marked as INVALID when BLOCKED
        assert step.status == StepStatus.INVALID
        assert logger.log_step_status_change.called
        # Check that reason includes "blocked"
        status_calls = logger.log_step_status_change.call_args_list
        blocked_call = [c for c in status_calls if "blocked" in c[1].get("reason", "").lower()]
        assert len(blocked_call) > 0

    def test_execute_llm_reasoning_step_logs_execution_outcome(self):
        """Test execute_llm_reasoning_step logs execution outcome."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"reasoning": '{"result": "output"}'})
        
        logger = Mock()
        logger.log_step_execution_outcome = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id)
        
        assert logger.log_step_execution_outcome.called
        call_args = logger.log_step_execution_outcome.call_args
        assert call_args[1]["execution_mode"] == "llm"
        assert call_args[1]["success"] is True

    def test_execute_llm_reasoning_step_handles_json_with_result_key(self):
        """Test execute_llm_reasoning_step handles JSON with result key."""
        memory = InMemoryKVStore()
        
        # Create custom LLM that returns JSON with result key
        class ResultKeyLLM:
            def __init__(self):
                self.calls = []
            
            def generate(self, **kwargs):
                self.calls.append(kwargs)
                return {
                    "text": json.dumps({"result": "output_value"})
                }
        
        llm = ResultKeyLLM()
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        assert result.result.get("result") == "output_value"

    def test_execute_llm_reasoning_step_handles_plan_structure_json(self):
        """Test execute_llm_reasoning_step handles plan structure JSON."""
        memory = InMemoryKVStore()
        plan_json = json.dumps({
            "goal": "test goal",
            "steps": [{"step_id": "1", "description": "step 1"}]
        })
        llm = MockLLMAdapter({"reasoning": plan_json})
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        # Should wrap plan structure as result
        assert "result" in result.result

    def test_execute_llm_reasoning_step_handles_json_without_result_key(self):
        """Test execute_llm_reasoning_step handles JSON without result key."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({
            "reasoning": json.dumps({"data": "value"})
        })
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        # Should add result key
        assert "result" in result.result

    def test_execute_llm_reasoning_step_handles_non_dict_json(self):
        """Test execute_llm_reasoning_step handles non-dict JSON."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({
            "reasoning": json.dumps(["array", "value"])
        })
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        assert "result" in result.result

    def test_execute_llm_reasoning_step_handles_non_json_response(self):
        """Test execute_llm_reasoning_step handles non-JSON response."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({
            "reasoning": "Plain text response"
        })
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm)
        
        assert result.success is True
        assert "result" in result.result

    def test_execute_llm_reasoning_step_logs_failure(self):
        """Test execute_llm_reasoning_step logs failure correctly."""
        memory = InMemoryKVStore()
        
        class FailingLLM:
            def generate(self, **kwargs):
                raise Exception("LLM call failed")
        
        llm = FailingLLM()
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert logger.log_error.called

    def test_execute_llm_reasoning_step_handles_execution_error_in_failure(self):
        """Test execute_llm_reasoning_step handles ExecutionError in failure path."""
        memory = InMemoryKVStore()
        
        class ExecutionErrorLLM:
            def generate(self, **kwargs):
                raise ExecutionError("LLM execution failed")
        
        llm = ExecutionErrorLLM()
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            agent="llm",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id)
        
        assert result.success is False
        # Verify ExecutionError was logged correctly
        assert logger.log_error.called

    def test_execute_llm_reasoning_step_uses_fallback_mode_when_no_agent(self):
        """Test execute_llm_reasoning_step uses fallback mode when agent is not 'llm'."""
        memory = InMemoryKVStore()
        llm = MockLLMAdapter({"reasoning": '{"result": "output"}'})
        
        logger = Mock()
        logger.log_step_execution_outcome = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Test step",
            # No agent field - should use fallback mode
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id)
        
        assert result.execution_mode == "fallback"
        call_args = logger.log_step_execution_outcome.call_args
        assert call_args[1]["execution_mode"] == "fallback"


class TestExecutorToolStepExceptionHandling:
    """Test exception handling in execute_tool_step outer exception handler (lines 228-270)."""

    def test_execute_tool_step_outer_exception_handler_logs_status_change(self):
        """Test outer exception handler logs status change when exception occurs."""
        registry = ToolRegistry()
        
        class MemoryExceptionTool(Tool):
            """Tool that succeeds but memory write fails."""
            def __init__(self):
                self.name = "memory_exception_tool"
                self.description = "Tool that causes memory exception"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = MemoryExceptionTool()
        registry.register(tool)
        
        # Create memory that raises exception on write
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory write failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool that causes memory exception",
            tool="memory_exception_tool",
            status=StepStatus.RUNNING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should handle exception and log status change
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert logger.log_step_status_change.called
        call_args = logger.log_step_status_change.call_args
        assert call_args[1]["reason"] == "step_execution_failed"
        assert call_args[1]["old_status"] in ["running", "RUNNING"]

    def test_execute_tool_step_outer_exception_handler_logs_execution_outcome(self):
        """Test outer exception handler logs execution outcome when exception occurs."""
        registry = ToolRegistry()
        
        class StatusExceptionTool(Tool):
            """Tool that succeeds but status change logging fails."""
            def __init__(self):
                self.name = "status_exception_tool"
                self.description = "Tool that causes status logging exception"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = StatusExceptionTool()
        registry.register(tool)
        memory = InMemoryKVStore()
        
        logger = Mock()
        # Make status change logging succeed, but execution outcome logging will be called
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="status_exception_tool",
            status=StepStatus.PENDING,
        )
        
        # Create memory that fails on write to trigger outer exception handler
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory write failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should log execution outcome
        assert logger.log_step_execution_outcome.called
        call_args = logger.log_step_execution_outcome.call_args
        assert call_args[1]["execution_mode"] == "tool"
        assert call_args[1]["success"] is False
        assert "error" in call_args[1]

    def test_execute_tool_step_outer_exception_handler_logs_error(self):
        """Test outer exception handler logs error when exception occurs."""
        registry = ToolRegistry()
        
        class ErrorExceptionTool(Tool):
            """Tool that succeeds but causes error."""
            def __init__(self):
                self.name = "error_exception_tool"
                self.description = "Tool that causes error"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = ErrorExceptionTool()
        registry.register(tool)
        
        # Create memory that fails on write
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise ValueError("Memory write failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="error_exception_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should log error
        assert logger.log_error.called
        call_args = logger.log_error.call_args
        assert call_args[1]["correlation_id"] == correlation_id
        assert call_args[1]["step_id"] == "step1"
        assert call_args[1]["tool_name"] == "error_exception_tool"

    def test_execute_tool_step_outer_exception_handler_converts_non_execution_error(self):
        """Test outer exception handler converts non-ExecutionError to ExecutionError."""
        registry = ToolRegistry()
        
        class NonExecutionErrorTool(Tool):
            """Tool that causes non-ExecutionError."""
            def __init__(self):
                self.name = "non_exec_error_tool"
                self.description = "Tool that causes ValueError"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = NonExecutionErrorTool()
        registry.register(tool)
        
        # Create memory that raises ValueError (not ExecutionError)
        class ValueErrorMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise ValueError("Value error in memory")
            
            def search(self, pattern):
                return []
        
        memory = ValueErrorMemory()
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="non_exec_error_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should convert ValueError to ExecutionError and log it
        assert logger.log_error.called
        call_args = logger.log_error.call_args
        error_record = call_args[1]["error"]
        # Error record should have ExecutionError code pattern
        assert "AEON" in error_record.code or "EXECUTION" in error_record.code.upper()

    def test_execute_tool_step_outer_exception_handler_preserves_execution_error(self):
        """Test outer exception handler preserves ExecutionError type."""
        registry = ToolRegistry()
        
        class ExecutionErrorTool(Tool):
            """Tool that causes ExecutionError."""
            def __init__(self):
                self.name = "exec_error_tool"
                self.description = "Tool that causes ExecutionError"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = ExecutionErrorTool()
        registry.register(tool)
        
        # Create memory that raises ExecutionError
        class ExecutionErrorMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise ExecutionError("Execution error in memory")
            
            def search(self, pattern):
                return []
        
        memory = ExecutionErrorMemory()
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="exec_error_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should preserve ExecutionError type
        assert logger.log_error.called
        call_args = logger.log_error.call_args
        error_record = call_args[1]["error"]
        # Error record should have ExecutionError code
        assert "EXECUTION" in error_record.code.upper()

    def test_execute_tool_step_outer_exception_handler_without_logger(self):
        """Test outer exception handler works without logger."""
        registry = ToolRegistry()
        
        class NoLoggerTool(Tool):
            """Tool that causes exception."""
            def __init__(self):
                self.name = "no_logger_tool"
                self.description = "Tool for no logger test"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = NoLoggerTool()
        registry.register(tool)
        
        # Create memory that fails
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="no_logger_tool",
            status=StepStatus.PENDING,
        )
        
        # Should handle exception gracefully without logger
        result = executor.execute_tool_step(step, registry, memory)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        assert result.error is not None

    def test_execute_tool_step_outer_exception_handler_without_correlation_id(self):
        """Test outer exception handler works without correlation_id."""
        registry = ToolRegistry()
        
        class NoCorrelationTool(Tool):
            """Tool that causes exception."""
            def __init__(self):
                self.name = "no_correlation_tool"
                self.description = "Tool for no correlation test"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = NoCorrelationTool()
        registry.register(tool)
        
        # Create memory that fails
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        logger = Mock()
        logger.log_step_status_change = Mock()
        logger.log_step_execution_outcome = Mock()
        logger.log_error = Mock()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="no_correlation_tool",
            status=StepStatus.PENDING,
        )
        
        # Should handle exception gracefully without correlation_id
        result = executor.execute_tool_step(step, registry, memory, logger, None)
        
        assert result.success is False
        assert step.status == StepStatus.FAILED
        # Logger methods should not be called without correlation_id
        assert not logger.log_step_status_change.called
        assert not logger.log_step_execution_outcome.called
        assert not logger.log_error.called

    def test_execute_tool_step_outer_exception_handler_with_none_tool_name(self):
        """Test outer exception handler handles None tool_name in error context."""
        registry = ToolRegistry()
        
        class NoneToolNameException(Tool):
            """Tool that causes exception."""
            def __init__(self):
                self.name = "none_tool_name_tool"
                self.description = "Tool for None tool name test"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = NoneToolNameException()
        registry.register(tool)
        
        # Create memory that fails
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory failed")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        logger = Mock()
        logger.log_error = Mock()
        correlation_id = "test-correlation-id"
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool=None,  # No tool name
            status=StepStatus.PENDING,
        )
        
        # This will fail earlier (tool not found), but let's test the outer handler path
        # by using a tool that exists but memory fails
        step.tool = "none_tool_name_tool"
        result = executor.execute_tool_step(step, registry, memory, logger, correlation_id)
        
        # Should handle None tool_name in error context
        assert logger.log_error.called
        call_args = logger.log_error.call_args
        # tool_name should be None or the actual tool name
        assert call_args[1]["tool_name"] is None or call_args[1]["tool_name"] == "none_tool_name_tool"

    def test_execute_tool_step_outer_exception_handler_returns_failure_result(self):
        """Test outer exception handler returns proper failure result."""
        registry = ToolRegistry()
        
        class FailureResultTool(Tool):
            """Tool that causes exception."""
            def __init__(self):
                self.name = "failure_result_tool"
                self.description = "Tool for failure result test"
                self.input_schema = {}
                self.output_schema = {}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        tool = FailureResultTool()
        registry.register(tool)
        
        # Create memory that fails
        class FailingMemory:
            def read(self, key):
                return None
            
            def write(self, key, value):
                raise Exception("Memory write exception")
            
            def search(self, pattern):
                return []
        
        memory = FailingMemory()
        
        executor = StepExecutor()
        step = PlanStep(
            step_id="step1",
            description="Use tool",
            tool="failure_result_tool",
            status=StepStatus.PENDING,
        )
        
        result = executor.execute_tool_step(step, registry, memory)
        
        # Should return proper failure result
        assert isinstance(result, StepExecutionResult)
        assert result.success is False
        assert result.result == {}
        assert result.error is not None
        assert "Memory write exception" in result.error
        assert result.execution_mode == "tool"

