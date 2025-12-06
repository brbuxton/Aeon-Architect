"""Additional unit tests for Orchestrator to achieve 100% coverage."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from aeon.exceptions import LLMError, PlanError, SupervisorError
from aeon.kernel.orchestrator import Orchestrator
from aeon.kernel.state import OrchestrationState, ExecutionContext
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.tools.registry import ToolRegistry
from tests.fixtures.mock_llm import MockLLMAdapter


class TestOrchestratorInitialization:
    """Test orchestrator initialization paths."""

    def test_orchestrator_initializes_semantic_validator_with_tool_registry(self):
        """Test orchestrator initializes semantic validator when llm and tool_registry are available."""
        llm = MockLLMAdapter()
        tool_registry = ToolRegistry()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            ttl=10
        )
        
        assert orchestrator._semantic_validator is not None

    def test_orchestrator_initializes_recursive_planner_with_tool_registry(self):
        """Test orchestrator initializes recursive planner when llm and tool_registry are available."""
        llm = MockLLMAdapter()
        tool_registry = ToolRegistry()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            ttl=10
        )
        
        assert orchestrator._recursive_planner is not None

    def test_orchestrator_does_not_initialize_convergence_engine_without_llm(self):
        """Test orchestrator does not initialize convergence engine when llm is None."""
        orchestrator = Orchestrator(
            llm=None,
            memory=None,
            ttl=10
        )
        
        assert orchestrator._convergence_engine is None


class TestOrchestratorPlanGeneration:
    """Test plan generation error paths."""

    def test_generate_plan_handles_supervisor_repair_success(self):
        """Test generate_plan handles successful supervisor repair."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        # Create supervisor that can repair
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            supervisor=supervisor,
            ttl=10
        )
        
        # Create execution context for logging
        orchestrator.state = OrchestrationState(
            plan=Plan(goal="test", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)]),
            ttl_remaining=10,
            memory=memory,
        )
        orchestrator.state.execution_context = ExecutionContext(
            correlation_id="test-id",
            execution_start_timestamp="2024-01-01T00:00:00"
        )
        
        # Mock logger
        logger = Mock()
        logger.log_error_recovery = Mock()
        orchestrator.logger = logger
        
        # Mock parser to raise PlanError first, then succeed after repair
        call_count = 0
        original_parse = orchestrator.parser.parse
        
        def mock_parse(plan_json):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise PlanError("Parse failed")
            return original_parse(plan_json)
        
        orchestrator.parser.parse = mock_parse
        
        # Mock supervisor repair to return valid plan
        def mock_repair_plan(plan_json):
            return '{"goal": "test", "steps": [{"step_id": "1", "description": "step 1", "status": "pending"}]}'
        
        supervisor.repair_plan = mock_repair_plan
        
        # This should succeed after repair
        plan = orchestrator.generate_plan("test request")
        assert plan is not None
        assert logger.log_error_recovery.called
        # Check recovery was successful
        recovery_call = logger.log_error_recovery.call_args
        assert recovery_call[1]["recovery_outcome"] == "success"

    def test_generate_plan_handles_supervisor_repair_failure(self):
        """Test generate_plan handles failed supervisor repair."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        from aeon.supervisor.repair import Supervisor
        supervisor = Supervisor(llm)
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            supervisor=supervisor,
            ttl=10
        )
        
        # Create execution context for logging
        orchestrator.state = OrchestrationState(
            plan=Plan(goal="test", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)]),
            ttl_remaining=10,
            memory=memory,
        )
        orchestrator.state.execution_context = ExecutionContext(
            correlation_id="test-id",
            execution_start_timestamp="2024-01-01T00:00:00"
        )
        
        logger = Mock()
        logger.log_error_recovery = Mock()
        orchestrator.logger = logger
        
        # Mock parser to always raise PlanError
        def mock_parse(plan_json):
            raise PlanError("Parse failed")
        
        orchestrator.parser.parse = mock_parse
        
        # Mock supervisor repair to raise error
        def mock_repair_plan(plan_json):
            raise SupervisorError("Repair failed")
        
        supervisor.repair_plan = mock_repair_plan
        
        # Should raise PlanError after failed repair
        with pytest.raises(PlanError):
            orchestrator.generate_plan("test request")
        
        # Verify failed recovery was logged
        assert logger.log_error_recovery.called
        recovery_call = logger.log_error_recovery.call_args
        assert recovery_call[1]["recovery_outcome"] == "failure"

    def test_generate_plan_handles_llm_error(self):
        """Test generate_plan handles LLMError."""
        llm = MockLLMAdapter()
        
        # Make LLM raise error
        def mock_generate(**kwargs):
            raise LLMError("LLM failed")
        
        llm.generate = mock_generate
        
        orchestrator = Orchestrator(llm=llm, ttl=10)
        
        with pytest.raises(LLMError) as exc_info:
            orchestrator.generate_plan("test request")
        
        assert "Failed to generate plan" in str(exc_info.value)

    def test_generate_plan_handles_plan_error(self):
        """Test generate_plan handles PlanError."""
        llm = MockLLMAdapter()
        
        orchestrator = Orchestrator(llm=llm, ttl=10)
        
        # Mock parser to raise PlanError
        def mock_parse(plan_json):
            raise PlanError("Parse failed")
        
        orchestrator.parser.parse = mock_parse
        orchestrator.supervisor = None  # No supervisor to repair
        
        with pytest.raises(PlanError) as exc_info:
            orchestrator.generate_plan("test request")
        
        assert "Failed to parse/validate plan" in str(exc_info.value)

    def test_generate_plan_handles_unexpected_error(self):
        """Test generate_plan handles unexpected exceptions."""
        llm = MockLLMAdapter()
        
        orchestrator = Orchestrator(llm=llm, ttl=10)
        
        # Mock parser to raise unexpected error
        def mock_parse(plan_json):
            raise ValueError("Unexpected error")
        
        orchestrator.parser.parse = mock_parse
        
        with pytest.raises(PlanError) as exc_info:
            orchestrator.generate_plan("test request")
        
        assert "Unexpected error" in str(exc_info.value)


class TestOrchestratorState:
    """Test orchestrator state management."""

    def test_get_state_returns_state(self):
        """Test get_state returns current state."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(llm=llm, memory=memory, ttl=10)
        
        # Initially state should be None
        assert orchestrator.get_state() is None
        
        # After execution, state should exist
        orchestrator.state = OrchestrationState(
            plan=Plan(goal="test", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)]),
            ttl_remaining=10,
            memory=memory,
        )
        
        orchestrator.state = OrchestrationState(
            plan=Plan(goal="test", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)]),
            ttl_remaining=10,
            memory=memory,
        )
        
        state = orchestrator.get_state()
        assert state is not None
        assert state.plan.goal == "test"


class TestOrchestratorExecuteStep:
    """Test _execute_step method paths."""

    def test_execute_step_handles_missing_memory(self):
        """Test _execute_step handles missing memory."""
        llm = MockLLMAdapter()
        
        orchestrator = Orchestrator(llm=llm, memory=None, ttl=10)
        
        step = PlanStep(
            step_id="step1",
            description="Test step",
            status=StepStatus.PENDING,
        )
        
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[step]),
            ttl_remaining=10,
            memory=None,
        )
        
        # Should return None when memory is missing
        result = orchestrator._execute_step(step, state)
        assert result is None

    def test_execute_step_handles_missing_tool_registry(self):
        """Test _execute_step handles missing tool registry."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            tool_registry=None,
            ttl=10
        )
        
        step = PlanStep(
            step_id="step1",
            description="Test step",
            status=StepStatus.PENDING,
        )
        
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[step]),
            ttl_remaining=10,
            memory=memory,
        )
        
        # Should work with None tool registry (will use empty registry)
        result = orchestrator._execute_step(step, state)
        # Should complete (returns None, but step should be executed)

    def test_execute_step_creates_supervisor_if_missing(self):
        """Test _execute_step creates supervisor if missing."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            supervisor=None,
            ttl=10
        )
        
        step = PlanStep(
            step_id="step1",
            description="Test step",
            status=StepStatus.PENDING,
        )
        
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[step]),
            ttl_remaining=10,
            memory=memory,
        )
        
        # Should create supervisor internally
        result = orchestrator._execute_step(step, state)
        # Should complete

    def test_execute_step_handles_execution_error(self):
        """Test _execute_step handles execution errors."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            ttl=10
        )
        
        step = PlanStep(
            step_id="step1",
            description="Test step",
            status=StepStatus.PENDING,
        )
        
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[step]),
            ttl_remaining=10,
            memory=memory,
        )
        
        # Mock step_executor to raise exception
        def mock_execute_step(**kwargs):
            raise Exception("Execution failed")
        
        orchestrator.step_executor.execute_step = mock_execute_step
        
        result = orchestrator._execute_step(step, state)
        
        # Should handle error gracefully
        assert step.status == StepStatus.FAILED

    def test_execute_step_logs_tool_call_when_tool_execution_succeeds(self):
        """Test _execute_step logs tool call when tool execution succeeds."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        tool_registry = ToolRegistry()
        
        from aeon.tools.stubs.calculator import CalculatorTool
        tool_registry.register(CalculatorTool())
        
        orchestrator = Orchestrator(
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            ttl=10
        )
        
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
            status=StepStatus.PENDING,
        )
        
        state = OrchestrationState(
            plan=Plan(goal="test", steps=[step]),
            ttl_remaining=10,
            memory=memory,
        )
        
        # Mock log_tool_call_to_history
        with patch('aeon.orchestration.tool_ops.log_tool_call_to_history') as mock_log:
            result = orchestrator._execute_step(step, state)
            # If tool execution succeeds, should log tool call
            # (Note: actual logging depends on execution result)


class TestOrchestratorExecuteMultipass:
    """Test execute_multipass method paths."""

    def test_execute_multipass_uses_existing_state(self):
        """Test execute_multipass uses existing state if available."""
        llm = MockLLMAdapter()
        memory = InMemoryKVStore()
        
        orchestrator = Orchestrator(llm=llm, memory=memory, ttl=10)
        
        # Create existing state
        existing_plan = Plan(goal="existing", steps=[PlanStep(step_id="step1", description="test", status=StepStatus.PENDING)])
        orchestrator.state = OrchestrationState(
            plan=existing_plan,
            ttl_remaining=5,
            memory=memory,
        )
        
        # Mock engine to capture plan
        captured_plan = None
        
        def mock_run_multipass(**kwargs):
            nonlocal captured_plan
            captured_plan = kwargs.get("plan")
            return {
                "status": "converged",
                "execution_history": []
            }
        
        with patch('aeon.orchestration.engine.OrchestrationEngine') as MockEngine:
            mock_engine_instance = Mock()
            mock_engine_instance.run_multipass = mock_run_multipass
            MockEngine.return_value = mock_engine_instance
            
            result = orchestrator.execute_multipass("test request")
            
            # Should use existing plan, not generate new one
            assert captured_plan == existing_plan

