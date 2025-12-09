"""Core orchestrator for LLM orchestration loop.

Thin kernel implementation per Constitution Principle I. Coordinates phase
transitions, LLM calls, state updates, and TTL governance. All validation,
context building, error construction, and strategy logic has been extracted
to orchestration modules.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid

from aeon.adaptive.heuristics import AdaptiveDepth
from aeon.exceptions import LLMError, PlanError, SupervisorError, ToolError, TTLExpiredError
from aeon.kernel.executor import StepExecutor
from aeon.kernel.state import ExecutionContext, ExecutionHistory, ExecutionPass, OrchestrationState
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.observability.helpers import build_execution_result, generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.orchestration.contracts import (
    validate_phase_entry,
    validate_phase_exit,
    validate_phase_invariants,
    validate_transition_contract,
)
from aeon.orchestration.context_ops import build_phase_context
from aeon.orchestration.execution_pass_ops import (
    apply_refinement_to_plan_state,
    build_execution_pass_after_phase,
    build_execution_pass_before_phase,
    merge_evaluation_results,
    merge_execution_results,
)
from aeon.orchestration.phases import PhaseOrchestrator
from aeon.orchestration.refinement import PlanRefinement
from aeon.orchestration.step_prep import StepPreparation
from aeon.orchestration.strategy import determine_next_action, has_converged, should_refine
from aeon.orchestration.ttl import TTLStrategy, check_ttl_after_llm_call, check_ttl_before_phase_entry, decrement_ttl_per_cycle
from aeon.orchestration.validation import check_ttl_at_phase_boundary
from aeon.plan.executor import PlanExecutor
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.plan.parser import PlanParser
from aeon.plan.prompts import construct_plan_generation_prompt, get_plan_generation_system_prompt
from aeon.prompts.registry import get_prompt, PromptId, PlanGenerationSystemInput, PlanGenerationUserInput
from aeon.plan.validator import PlanValidator
from aeon.tools.registry import ToolRegistry
from aeon.validation.schema import Validator
from aeon.validation.semantic import SemanticValidator
from aeon.convergence.engine import ConvergenceEngine


class Orchestrator:
    """Core orchestrator for LLM orchestration loop."""

    def __init__(
        self,
        llm: LLMAdapter,
        memory: Optional[Memory] = None,
        ttl: int = 10,
        tool_registry: Optional[Any] = None,
        supervisor: Optional[Any] = None,
        logger: Optional[JSONLLogger] = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            llm: LLM adapter for generation
            memory: Memory interface (optional)
            ttl: Time-to-live in cycles (default 10)
            tool_registry: Tool registry (optional, for later phases)
            supervisor: Supervisor for error repair (optional, for later phases)
            logger: JSONL logger for cycle logging (optional)
        """
        self.llm = llm
        self.memory = memory
        self.ttl = ttl
        self.tool_registry = tool_registry
        self.supervisor = supervisor
        self.logger = logger
        self.parser = PlanParser()
        self.validator = PlanValidator()
        self.state: Optional[OrchestrationState] = None
        self.step_executor = StepExecutor()  # StepExecutor for multi-mode execution (T116)
        self.validator_schema = Validator()  # Validator for step tool validation
        # Multi-pass execution state
        self._pass_number = 0
        self._current_phase: Optional[Literal["A", "B", "C", "D"]] = None
        self._execution_passes: List[ExecutionPass] = []
        # External module interfaces for US2, US3, US4, US5, US6
        self._adaptive_depth: Optional[AdaptiveDepth] = (
            AdaptiveDepth(llm_adapter=self.llm, global_ttl_limit=self.ttl)
            if self.llm
            else None
        )
        # Initialize SemanticValidator if LLM and tool_registry are available
        if self.llm and self.tool_registry:
            self._semantic_validator = SemanticValidator(
                llm_adapter=self.llm,
                tool_registry=self.tool_registry,
            )
        else:
            self._semantic_validator = None
        # Initialize RecursivePlanner if LLM and tool_registry are available
        # Pass semantic_validator to enable validation of refined fragments (FR-033)
        if self.llm and self.tool_registry:
            from aeon.plan.recursive import RecursivePlanner
            self._recursive_planner = RecursivePlanner(
                llm_adapter=self.llm,
                tool_registry=self.tool_registry,
                semantic_validator=self._semantic_validator,
            )
        else:
            self._recursive_planner = None
        # Initialize ConvergenceEngine if LLM is available
        if self.llm:
            self._convergence_engine = ConvergenceEngine(llm_adapter=self.llm)
        else:
            self._convergence_engine = None
        # Initialize orchestration modules (T025)
        from aeon.orchestration.phases import PhaseOrchestrator
        from aeon.orchestration.refinement import PlanRefinement
        from aeon.orchestration.step_prep import StepPreparation
        from aeon.orchestration.ttl import TTLStrategy
        self._phase_orchestrator = PhaseOrchestrator()
        self._plan_refinement = PlanRefinement()
        self._step_preparation = StepPreparation()
        self._ttl_strategy = TTLStrategy()

    def generate_plan(self, request: str) -> Plan:
        """
        Generate a plan from a natural language request.

        Args:
            request: Natural language request

        Returns:
            Generated Plan object

        Raises:
            LLMError: If LLM generation fails
            PlanError: If plan parsing/validation fails
        """
        # Construct prompt for plan generation using registry
        system_prompt = get_prompt(PromptId.PLAN_GENERATION_SYSTEM, PlanGenerationSystemInput())
        # Build tool registry export for user prompt
        tool_registry_export = ""
        if self.tool_registry:
            available_tools = self.tool_registry.export_tools_for_llm()
            if available_tools:
                tool_registry_export = "Available tools:\n"
                for tool in available_tools:
                    tool_registry_export += f"- {tool['name']}: {tool.get('description', 'No description')}\n"
                    if tool.get('input_schema'):
                        import json
                        tool_registry_export += f"  Input schema: {json.dumps(tool['input_schema'], indent=2)}\n"
                tool_registry_export += "\n"
                tool_registry_export += "You may reference these tools in step.tool fields. Do not invent tools.\n\n"
        prompt = get_prompt(PromptId.PLAN_GENERATION_USER, PlanGenerationUserInput(
            request=request,
            tool_registry_export=tool_registry_export
        ))

        try:
            # Generate LLM response
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.7,
            )

            # Extract plan JSON from LLM response
            plan_json = self.parser.extract_plan_from_llm_response(response, self.supervisor)

            # Parse and validate plan
            try:
                plan = self.parser.parse(plan_json)
                self.validator.validate_plan(plan.model_dump())
            except PlanError as parse_error:
                # If supervisor is available and parsing failed, try to repair the plan structure
                if self.supervisor:
                    try:
                        repaired_plan_dict = self.supervisor.repair_plan(plan_json)
                        # Try parsing again with repaired plan
                        plan = self.parser.parse(repaired_plan_dict)
                        self.validator.validate_plan(plan.model_dump())
                        
                        # Log successful recovery if logger and execution_context are available
                        if self.logger and hasattr(self.state, 'execution_context') and self.state.execution_context:
                            from aeon.exceptions import PlanError as PlanErrorClass
                            original_error = PlanErrorClass("Failed to parse/validate plan")
                            error_record = original_error.to_error_record()
                            self.logger.log_error_recovery(
                                correlation_id=self.state.execution_context.correlation_id,
                                original_error=error_record,
                                recovery_action="supervisor_repair_plan",
                                recovery_outcome="success",
                            )
                    except (SupervisorError, PlanError) as repair_error:
                        # Log failed recovery if logger and execution_context are available
                        if self.logger and hasattr(self.state, 'execution_context') and self.state.execution_context:
                            from aeon.exceptions import PlanError as PlanErrorClass
                            original_error = PlanErrorClass("Failed to parse/validate plan")
                            error_record = original_error.to_error_record()
                            self.logger.log_error_recovery(
                                correlation_id=self.state.execution_context.correlation_id,
                                original_error=error_record,
                                recovery_action="supervisor_repair_plan",
                                recovery_outcome="failure",
                            )
                        raise PlanError(
                            f"Failed to parse/validate plan and supervisor repair failed: {str(repair_error)}"
                        ) from repair_error
                else:
                    raise

            return plan

        except LLMError as e:
            raise LLMError(f"Failed to generate plan: {str(e)}") from e
        except PlanError as e:
            raise PlanError(f"Failed to parse/validate plan: {str(e)}") from e
        except Exception as e:
            raise PlanError(f"Unexpected error during plan generation: {str(e)}") from e


    def get_state(self) -> Optional[OrchestrationState]:
        """
        Get current orchestration state.

        Returns:
            Current state or None if not initialized
        """
        return self.state

    def _execute_step(self, step: "PlanStep", state: OrchestrationState) -> None:
        """
        Execute a single plan step (T116-T118).

        Uses StepExecutor for multi-mode execution:
        - Tool-based execution if step.tool is present and valid
        - LLM reasoning execution if step.agent == "llm"
        - Missing-tool repair flow if tool is missing/invalid (T117)
        - Fallback execution if repair fails (T118)

        For User Story 4, this method:
        - Invokes tools if tool_registry is available
        - Validates tool inputs/outputs
        - Logs tool calls to tool_history
        - Handles tool errors gracefully (marks step failed, continues)

        For User Story 5, this method:
        - Memory is accessible via self.memory for read/write operations
        - Memory persists across steps during plan execution
        - Memory operations can be performed during step execution

        For User Story 7, this method:
        - Logs cycle after step execution completes
        - Captures plan state, LLM output, supervisor actions, tool calls, TTL, errors
        """
        # Ensure we have required dependencies for StepExecutor
        if not self.memory:
            # Fallback to no-op if memory not available
            # Note: Legacy cycle logging removed - multipass path uses phase-aware logging
            return None
        
        if not self.tool_registry:
            # If no tool registry, use StepExecutor with None registry (will fallback to LLM)
            tool_registry = None
        else:
            tool_registry = self.tool_registry
        
        if not self.supervisor:
            # Create a basic supervisor if not available (for repair functionality)
            from aeon.supervisor.repair import Supervisor
            supervisor = Supervisor(llm_adapter=self.llm)
        else:
            supervisor = self.supervisor
        
        # Handle missing-tool repair flow (T117) - validate and repair before execution
        from aeon.orchestration.tool_ops import handle_missing_tool_repair, should_attempt_repair
        
        # Get correlation_id from execution context if available
        correlation_id = None
        if hasattr(self.state, 'execution_context') and self.state.execution_context:
            correlation_id = self.state.execution_context.correlation_id
        
        if should_attempt_repair(step, tool_registry, supervisor):
            handle_missing_tool_repair(
                step,
                tool_registry,
                supervisor,
                state.plan.goal,
                self.validator_schema,
                self.logger,
                correlation_id,
            )
            # If repair failed, will fallback to LLM reasoning in StepExecutor (T118)
        
        # Use StepExecutor for multi-mode execution (T116)
        try:
            
            execution_result = self.step_executor.execute_step(
                step=step,
                registry=tool_registry or ToolRegistry(),  # Empty registry if None
                memory=self.memory,
                llm=self.llm,
                supervisor=supervisor,
                logger=self.logger,
                correlation_id=correlation_id,
                state=state,  # Pass state so StepExecutor can access phase_c_context
            )
            
            # Log execution mode and result
            if execution_result.execution_mode:
                # Store execution mode in state for logging
                if not hasattr(state, 'execution_modes'):
                    state.execution_modes = {}
                state.execution_modes[step.step_id] = execution_result.execution_mode
            
            # Log tool calls if tool-based execution
            if execution_result.execution_mode == "tool" and execution_result.success and tool_registry:
                from aeon.orchestration.tool_ops import log_tool_call_to_history
                log_tool_call_to_history(step, tool_registry, execution_result, state)
            
            # TTL governance: TTL decrement now happens once per cycle at Phase D completion (US4)
            # Per-step TTL decrement removed - TTL decrements exactly once per A→B→C→D cycle
            
        except Exception as e:
            # Handle execution errors
            step.status = StepStatus.FAILED
            # Note: Legacy cycle logging removed - multipass path uses phase-aware logging
            # Errors are logged via phase-aware logging methods in the multipass engine
            return None
        
        # Note: Legacy cycle logging removed - multipass path uses phase-aware logging
        # Step execution is logged via phase-aware logging methods in the multipass engine
        return None

    def execute_multipass(self, request: str, plan: Optional[Plan] = None) -> Dict[str, Any]:
        """
        Execute a request using multi-pass execution loop (User Story 1).

        Phase sequence:
        - Phase A: TaskProfile & TTL allocation
        - Phase B: Initial Plan & Pre-Execution Refinement
        - Phase C: Execution Passes (Execute Batch → Evaluate → Decide → Refine)
        - Phase D: Adaptive Depth (TaskProfile updates at pass boundaries)

        Args:
            request: Natural language request
            plan: Optional pre-generated plan

        Returns:
            Execution result dict with ExecutionHistory

        Raises:
            TTLExpiredError: If TTL expires during execution
            LLMError: If LLM operations fail
            PlanError: If plan operations fail
        """
        from aeon.orchestration.engine import OrchestrationEngine
        from aeon.observability.helpers import generate_correlation_id

        execution_start = datetime.now()
        execution_start_timestamp = execution_start.isoformat()

        # Generate correlation ID at execution start (T026)
        correlation_id = generate_correlation_id(execution_start_timestamp, request)
        
        # Create execution context (T026a-T026d)
        execution_context = ExecutionContext(
            correlation_id=correlation_id,
            execution_start_timestamp=execution_start_timestamp,
        )

        # Initialize state for execution
        if not self.state:
            plan_to_execute = plan or self.generate_plan(request)
            self.state = OrchestrationState(
                plan=plan_to_execute,
                ttl_remaining=self.ttl,
                memory=self.memory
            )
        else:
            plan_to_execute = plan or self.state.plan

        # Initialize multi-pass state
        self._pass_number = 0
        self._current_phase = None
        self._execution_passes = []

        # Construct orchestration engine
        engine = OrchestrationEngine(
            llm=self.llm,
            phase_orchestrator=self._phase_orchestrator,
            step_executor=self.step_executor,
            step_preparation=self._step_preparation,
            ttl_strategy=self._ttl_strategy,
            adaptive_depth=self._adaptive_depth,
            recursive_planner=self._recursive_planner,
            semantic_validator=self._semantic_validator,
            convergence_engine=self._convergence_engine,
            tool_registry=self.tool_registry,
            supervisor=self.supervisor,
            logger=self.logger,
            memory=self.memory,
            plan_generator=self.generate_plan,
        )

        # Run multipass execution via engine
        return engine.run_multipass(
            request=request,
            plan=plan_to_execute,
            execution_context=execution_context,
            state=self.state,
            ttl=self.ttl,
            execute_step_fn=self._execute_step,
        )

    def execute_legacy_compat(self, request: str, plan: Optional[Plan] = None) -> Dict[str, Any]:
        """
        Compatibility wrapper for tests that once depended on execute().
        
        This method wraps execute_multipass() to provide backward compatibility
        for tests that were written for the legacy single-pass execute() method.
        
        Args:
            request: Natural language request
            plan: Optional pre-generated plan
            
        Returns:
            Execution result dict with ExecutionHistory
        """
        return self.execute_multipass(request, plan)


