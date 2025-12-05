"""Core orchestrator for LLM orchestration loop."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid

from aeon.adaptive.heuristics import AdaptiveDepth
from aeon.exceptions import LLMError, PlanError, SupervisorError, ToolError, TTLExpiredError, ValidationError
from aeon.kernel.executor import StepExecutor
from aeon.kernel.state import ExecutionContext, ExecutionHistory, ExecutionPass, OrchestrationState, TTLExpirationResponse
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.observability.helpers import collect_cycle_data, generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.plan.executor import PlanExecutor
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.plan.parser import PlanParser
from aeon.plan.prompts import construct_plan_generation_prompt, get_plan_generation_system_prompt
from aeon.plan.validator import PlanValidator
from aeon.tools.invocation import handle_tool_error, invoke_tool
from aeon.tools.models import ToolCall
from aeon.tools.repair import attempt_tool_repair
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
        self._cycle_number = 0
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
        # Construct prompt for plan generation
        system_prompt = get_plan_generation_system_prompt()
        prompt = construct_plan_generation_prompt(request, self.tool_registry)

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


    def execute(self, request: str, plan: Optional[Plan] = None) -> Dict[str, Any]:
        """
        Execute a request: generate plan (if needed) and run it sequentially.

        Args:
            request: Natural language request
            plan: Optional pre-generated plan

        Returns:
            Execution result dict

        Raises:
            TTLExpiredError: If TTL expires during execution
            LLMError: If LLM operations fail
            PlanError: If plan operations fail
        """
        # Generate plan if one was not supplied
        plan_to_execute = plan or self.generate_plan(request)

        # Initialize state for execution
        self.state = OrchestrationState(plan=plan_to_execute, ttl_remaining=self.ttl, memory=self.memory)
        self._cycle_number = 0

        # Execute plan sequentially
        try:
            executor = PlanExecutor(state=self.state, step_runner=self._execute_step)
            executor.execute()
            
            # Execution completed successfully
            return {
                "plan": self.state.plan.model_dump(),
                "status": "completed",
                "ttl_remaining": self.state.ttl_remaining,
            }
        except TTLExpiredError:
            # Log TTL expiration if logger is available
            if self.logger:
                self._log_cycle(errors=[{"type": "TTLExpiredError", "message": "TTL expired during plan execution"}])
            
            # TTL expired - return structured expiration response
            return {
                "plan": self.state.plan.model_dump(),
                "status": "ttl_expired",
                "ttl_remaining": self.state.ttl_remaining,
                "error": "TTL expired during plan execution",
            }

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
            if self.logger:
                self._log_cycle()
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
        if step.tool and tool_registry and supervisor:
            # Validate tool before execution
            validation_result = self.validator_schema.validate_step_tool(step, tool_registry)
            if not validation_result["valid"]:
                # Tool is missing/invalid - attempt repair
                # Get correlation_id for logging
                correlation_id = None
                if hasattr(self.state, 'execution_context') and self.state.execution_context:
                    correlation_id = self.state.execution_context.correlation_id
                
                # Log original error before repair attempt
                if self.logger and correlation_id:
                    from aeon.exceptions import ToolError
                    original_error = ToolError(f"Tool '{step.tool}' not found in registry")
                    error_record = original_error.to_error_record(
                        context={"step_id": step.step_id, "tool_name": step.tool}
                    )
                    self.logger.log_error(
                        correlation_id=correlation_id,
                        error=error_record,
                        step_id=step.step_id,
                        tool_name=step.tool,
                    )
                
                # Attempt repair
                repair_success = attempt_tool_repair(step, tool_registry, supervisor, state.plan.goal)
                
                # Log recovery outcome
                if self.logger and correlation_id:
                    from aeon.exceptions import ToolError
                    original_error = ToolError(f"Tool '{step.tool}' not found in registry")
                    error_record = original_error.to_error_record(
                        context={"step_id": step.step_id, "tool_name": step.tool}
                    )
                    self.logger.log_error_recovery(
                        correlation_id=correlation_id,
                        original_error=error_record,
                        recovery_action="supervisor_repair_missing_tool",
                        recovery_outcome="success" if repair_success else "failure",
                    )
                
                # If repair failed, will fallback to LLM reasoning in StepExecutor (T118)
        
        # Use StepExecutor for multi-mode execution (T116)
        try:
            # Get correlation_id from execution context if available
            correlation_id = None
            if hasattr(self.state, 'execution_context') and self.state.execution_context:
                correlation_id = self.state.execution_context.correlation_id
            
            execution_result = self.step_executor.execute_step(
                step=step,
                registry=tool_registry or ToolRegistry(),  # Empty registry if None
                memory=self.memory,
                llm=self.llm,
                supervisor=supervisor,
                logger=self.logger,
                correlation_id=correlation_id,
            )
            
            # Log execution mode and result
            if execution_result.execution_mode:
                # Store execution mode in state for logging
                if not hasattr(state, 'execution_modes'):
                    state.execution_modes = {}
                state.execution_modes[step.step_id] = execution_result.execution_mode
            
            # Log tool calls if tool-based execution
            if execution_result.execution_mode == "tool" and execution_result.success:
                # Tool call was successful - log it
                if tool_registry and step.tool:
                    tool = tool_registry.get(step.tool)
                    if tool:
                        tool_call = ToolCall(
                            tool_name=step.tool,
                            arguments={},  # No args for now
                            result=execution_result.result,
                            timestamp=datetime.now().isoformat(),
                            step_id=step.step_id,
                        )
                        state.tool_history.append(tool_call.model_dump())
            
        except Exception as e:
            # Handle execution errors
            step.status = StepStatus.FAILED
            if self.logger:
                self._log_cycle(errors=[{"type": type(e).__name__, "message": str(e)}])
            return None
        
        # Log cycle after step execution
        if self.logger:
            self._log_cycle()
        
        return None

    def _log_cycle(self, errors: Optional[list] = None) -> None:
        """
        Log an orchestration cycle.

        Args:
            errors: Optional list of errors to include in log entry
        """
        if not self.logger or not self.state:
            return

        self._cycle_number += 1

        # Collect cycle data using helper function
        cycle_data = collect_cycle_data(self.state)
        tool_calls = cycle_data["tool_calls"]
        supervisor_actions = cycle_data["supervisor_actions"]
        llm_output = cycle_data["llm_output"]

        # Format and log entry
        log_entry = self.logger.format_entry(
            step_number=self._cycle_number,
            plan_state=self.state.plan.model_dump(),
            llm_output=llm_output,
            supervisor_actions=supervisor_actions,
            tool_calls=tool_calls,
            ttl_remaining=self.state.ttl_remaining,
            errors=errors or [],
        )

        self.logger.log_entry(log_entry)

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
        execution_id = str(uuid.uuid4())
        execution_start = datetime.now()
        execution_start_timestamp = execution_start.isoformat()

        # Generate correlation ID at execution start (T026)
        correlation_id = generate_correlation_id(execution_start_timestamp, request)
        
        # Create execution context (T026a-T026d)
        execution_context = ExecutionContext(
            correlation_id=correlation_id,
            execution_start_timestamp=execution_start_timestamp,
        )

        # Initialize multi-pass state
        self._pass_number = 0
        self._current_phase = None
        self._execution_passes = []
        ttl_allocated = self.ttl  # Will be updated by Phase A

        try:
            # Phase A: TaskProfile & TTL allocation (T026)
            phase_a_start = datetime.now()
            if self.logger:
                self.logger.log_phase_entry(
                    phase="A",
                    correlation_id=execution_context.correlation_id,
                    pass_number=0,
                )
            success, (task_profile, ttl_allocated), error = self._phase_orchestrator.phase_a_taskprofile_ttl(
                request, self._adaptive_depth, self.ttl
            )
            phase_a_duration = (datetime.now() - phase_a_start).total_seconds()
            if self.logger:
                self.logger.log_phase_exit(
                    phase="A",
                    correlation_id=execution_context.correlation_id,
                    duration=phase_a_duration,
                    outcome="success" if success else "failure",
                    pass_number=0,
                )
            if not success:
                # Fallback to default if phase orchestration fails
                from aeon.adaptive.models import TaskProfile
                task_profile = TaskProfile.default()
                ttl_allocated = self.ttl
            self._check_ttl_at_phase_boundary(ttl_allocated, "A")

            # Initialize state for execution
            plan_to_execute = plan or self.generate_plan(request)
            # Populate step indices before execution (T035)
            self._step_preparation.populate_step_indices(plan_to_execute)
            self.state = OrchestrationState(
                plan=plan_to_execute,
                ttl_remaining=ttl_allocated,
                memory=self.memory
            )
            self._cycle_number = 0

            # Phase B: Initial Plan & Pre-Execution Refinement (T027)
            phase_b_start = datetime.now()
            if self.logger:
                self.logger.log_phase_entry(
                    phase="B",
                    correlation_id=execution_context.correlation_id,
                    pass_number=0,
                )
            success, plan_to_execute, error = self._phase_orchestrator.phase_b_initial_plan_refinement(
                request, plan_to_execute, task_profile,
                self._recursive_planner, self._semantic_validator, self.tool_registry,
                execution_context=execution_context,
                logger=self.logger,
            )
            phase_b_duration = (datetime.now() - phase_b_start).total_seconds()
            if self.logger:
                self.logger.log_phase_exit(
                    phase="B",
                    correlation_id=execution_context.correlation_id,
                    duration=phase_b_duration,
                    outcome="success" if success else "failure",
                    pass_number=0,
                )
            if not success:
                # Continue with original plan if refinement fails
                pass
            # Re-populate step indices after refinement (in case steps were added/removed) (T035)
            self._step_preparation.populate_step_indices(plan_to_execute)
            self._check_ttl_at_phase_boundary(self.state.ttl_remaining, "B")

            # Phase C: Execution Passes
            converged = False
            max_passes = 50  # Safety limit to prevent infinite loops
            while not converged and self.state.ttl_remaining > 0 and self._pass_number < max_passes:
                self._pass_number += 1
                pass_start = datetime.now()

                # Create ExecutionPass for this pass
                execution_pass = ExecutionPass(
                    pass_number=self._pass_number,
                    phase="C",
                    plan_state=self.state.plan.model_dump(),
                    execution_results=[],
                    evaluation_results={},
                    refinement_changes=[],
                    ttl_remaining=self.state.ttl_remaining,
                    timing_information={"start_time": pass_start.isoformat()}
                )

                # Execute batch of ready steps (T028)
                execution_results = self._phase_orchestrator.phase_c_execute_batch(
                    self.state.plan, self.state, self.step_executor,
                    self.tool_registry, self.memory, self.supervisor,
                    self._execute_step
                )
                execution_pass.execution_results = execution_results

                # Check TTL at safe boundary (after batch execution) (T036)
                if self.state.ttl_remaining <= 0:
                    # TTL expired mid-phase
                    execution_pass.timing_information["end_time"] = datetime.now().isoformat()
                    execution_pass.timing_information["duration"] = (datetime.now() - pass_start).total_seconds()
                    self._execution_passes.append(execution_pass)
                    success, response, error = self._ttl_strategy.create_expiration_response(
                        "mid_phase", "C", execution_pass, self._execution_passes,
                        self.state, execution_id, request
                    )
                    if success:
                        return response
                    # Fallback if TTL strategy fails
                    raise TTLExpiredError(f"TTL expired mid-phase C")

                # Evaluate: semantic validation + convergence (T029)
                evaluation_results = self._phase_orchestrator.phase_c_evaluate(
                    self.state.plan, execution_results,
                    self._semantic_validator, self._convergence_engine, self.tool_registry,
                    execution_context=execution_context,
                    logger=self.logger,
                )
                execution_pass.evaluation_results = evaluation_results

                # Check convergence
                converged = evaluation_results.get("converged", False)
                if converged:
                    execution_pass.timing_information["end_time"] = datetime.now().isoformat()
                    execution_pass.timing_information["duration"] = (datetime.now() - pass_start).total_seconds()
                    self._execution_passes.append(execution_pass)
                    break

                # Decide: check if refinement needed
                needs_refinement = evaluation_results.get("needs_refinement", False)
                if needs_refinement:
                    # Refine plan (T030)
                    # Note: phase_c_refine applies refinement actions internally and modifies plan in place
                    # but doesn't return the updated plan. Since Pydantic models are immutable,
                    # we need to reconstruct the plan from refinement_changes.
                    # However, phase_c_refine already applied the actions, so we need to get the updated plan.
                    # For now, we'll call apply_actions again to get the updated plan.
                    success, refinement_changes, error = self._phase_orchestrator.phase_c_refine(
                        self.state.plan, evaluation_results, self._recursive_planner,
                        lambda p: self._step_preparation.populate_step_indices(p),
                        execution_context=execution_context,
                        logger=self.logger,
                    )
                    if success and refinement_changes:
                        # phase_c_refine already applied actions internally, but we need to update state.plan
                        # Reconstruct refinement_actions from refinement_changes and apply to get updated plan
                        from aeon.plan.models import RefinementAction
                        refinement_actions = [RefinementAction(**change) for change in refinement_changes]
                        success_apply, updated_plan, error_apply = self._plan_refinement.apply_actions(
                            self.state.plan, refinement_actions
                        )
                        if success_apply:
                            self.state.plan = updated_plan
                            # Re-populate step indices after refinement (T035)
                            self._step_preparation.populate_step_indices(self.state.plan)
                        execution_pass.refinement_changes = refinement_changes

                # Phase D: Adaptive Depth (at pass boundary) (T031)
                if self._pass_number > 0:  # Only after first pass
                    success, updated_task_profile, error = self._phase_orchestrator.phase_d_adaptive_depth(
                        task_profile, evaluation_results, self.state.plan,
                        self._adaptive_depth, self.state, self.ttl, self._execution_passes
                    )
                    if success and updated_task_profile:
                        task_profile = updated_task_profile
                    self._check_ttl_at_phase_boundary(self.state.ttl_remaining, "D")

                # Complete pass
                execution_pass.timing_information["end_time"] = datetime.now().isoformat()
                execution_pass.timing_information["duration"] = (datetime.now() - pass_start).total_seconds()
                self._execution_passes.append(execution_pass)

                # Check TTL at phase boundary before next pass (T036)
                if self.state.ttl_remaining <= 0:
                    success, response, error = self._ttl_strategy.create_expiration_response(
                        "phase_boundary", "C", execution_pass, self._execution_passes,
                        self.state, execution_id, request
                    )
                    if success:
                        return response
                    # Fallback if TTL strategy fails
                    raise TTLExpiredError(f"TTL expired at phase C boundary")

            # Check if max passes limit was reached
            if self._pass_number >= max_passes and not converged:
                # Max passes reached without convergence - return with status
                execution_history = ExecutionHistory(
                    execution_id=execution_id,
                    task_input=request,
                    configuration={
                        "ttl": ttl_allocated,
                        "task_profile": task_profile.model_dump() if hasattr(task_profile, 'model_dump') else task_profile
                    },
                    passes=self._execution_passes,
                    final_result={
                        "converged": False,
                        "plan": self.state.plan.model_dump() if self.state else {},
                        "status": "max_passes_reached"
                    },
                    overall_statistics={
                        "total_passes": len(self._execution_passes),
                        "total_refinements": sum(len(p.refinement_changes) for p in self._execution_passes),
                        "convergence_achieved": False,
                        "total_time": (datetime.now() - execution_start).total_seconds()
                    }
                )
                return {
                    "execution_history": execution_history.model_dump(),
                    "status": "max_passes_reached",
                    "ttl_remaining": self.state.ttl_remaining if self.state else 0,
                }

            # Build ExecutionHistory
            execution_end = datetime.now()
            execution_history = ExecutionHistory(
                execution_id=execution_id,
                task_input=request,
                configuration={
                    "ttl": ttl_allocated,
                    "task_profile": task_profile.model_dump() if hasattr(task_profile, 'model_dump') else task_profile
                },
                passes=self._execution_passes,
                final_result={
                    "converged": converged,
                    "plan": self.state.plan.model_dump(),
                    "status": "converged" if converged else "ttl_expired"
                },
                overall_statistics={
                    "total_passes": len(self._execution_passes),
                    "total_refinements": sum(len(p.refinement_changes) for p in self._execution_passes),
                    "convergence_achieved": converged,
                    "total_time": (execution_end - execution_start).total_seconds()
                }
            )

            return {
                "execution_history": execution_history.model_dump(),
                "status": "converged" if converged else "ttl_expired",
                "ttl_remaining": self.state.ttl_remaining,
            }

        except TTLExpiredError as e:
            # Handle TTL expiration (T036)
            if self._execution_passes:
                last_pass = self._execution_passes[-1]
                success, response, error = self._ttl_strategy.create_expiration_response(
                    "mid_phase", self._current_phase or "C", last_pass, self._execution_passes,
                    self.state, execution_id, request
                )
                if success:
                    return response
            raise

    # Removed extracted methods (T037):
    # - _phase_a_taskprofile_ttl -> PhaseOrchestrator.phase_a_taskprofile_ttl
    # - _phase_b_initial_plan_refinement -> PhaseOrchestrator.phase_b_initial_plan_refinement
    # - _phase_c_execute_batch -> PhaseOrchestrator.phase_c_execute_batch
    # - _phase_c_evaluate -> PhaseOrchestrator.phase_c_evaluate
    # - _phase_c_refine -> PhaseOrchestrator.phase_c_refine
    # - _phase_d_adaptive_depth -> PhaseOrchestrator.phase_d_adaptive_depth
    # - _apply_refinement_actions -> PlanRefinement.apply_actions
    # - _get_ready_steps -> StepPreparation.get_ready_steps
    # - _populate_incoming_context -> StepPreparation.populate_incoming_context
    # - _populate_step_indices -> StepPreparation.populate_step_indices
    # - _create_ttl_expiration_response -> TTLStrategy.create_expiration_response

    def _check_ttl_at_phase_boundary(self, ttl_remaining: int, phase: Literal["A", "B", "C", "D"]) -> None:
        """
        Check TTL at phase boundary.

        Raises TTLExpiredError if TTL is exhausted.

        Args:
            ttl_remaining: Remaining TTL cycles
            phase: Current phase

        Raises:
            TTLExpiredError: If TTL is exhausted
        """
        if ttl_remaining <= 0:
            self._current_phase = phase
            raise TTLExpiredError(f"TTL expired at phase {phase} boundary")

