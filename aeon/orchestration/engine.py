"""Orchestration engine for multi-pass execution loop.

This module contains the OrchestrationEngine class that owns the multipass loop
and phase sequencing logic, extracted from the kernel to reduce LOC.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Tuple
import uuid

if TYPE_CHECKING:
    from aeon.adaptive.models import TaskProfile
    from aeon.plan.models import Plan
    from aeon.kernel.state import ExecutionContext, ExecutionHistory, ExecutionPass, OrchestrationState
    from aeon.observability.logger import JSONLLogger
    from aeon.kernel.executor import StepExecutor
    from aeon.llm.interface import LLMAdapter

__all__ = ["OrchestrationEngine"]


class OrchestrationEngine:
    """Engine that owns the multipass execution loop and phase sequencing."""

    def __init__(
        self,
        llm: "LLMAdapter",
        phase_orchestrator: Any,  # PhaseOrchestrator
        step_executor: "StepExecutor",
        step_preparation: Any,  # StepPreparation
        ttl_strategy: Any,  # TTLStrategy
        adaptive_depth: Optional[Any] = None,  # AdaptiveDepth
        recursive_planner: Optional[Any] = None,  # RecursivePlanner
        semantic_validator: Optional[Any] = None,  # SemanticValidator
        convergence_engine: Optional[Any] = None,  # ConvergenceEngine
        tool_registry: Optional[Any] = None,  # ToolRegistry
        supervisor: Optional[Any] = None,  # Supervisor
        logger: Optional["JSONLLogger"] = None,
        memory: Optional[Any] = None,  # Memory
        plan_generator: Optional[Callable] = None,  # Function to generate plans
    ):
        """
        Initialize orchestration engine.

        Args:
            llm: LLM adapter
            phase_orchestrator: PhaseOrchestrator instance
            step_executor: StepExecutor instance
            step_preparation: StepPreparation instance
            ttl_strategy: TTLStrategy instance
            adaptive_depth: Optional AdaptiveDepth instance
            recursive_planner: Optional RecursivePlanner instance
            semantic_validator: Optional SemanticValidator instance
            convergence_engine: Optional ConvergenceEngine instance
            tool_registry: Optional ToolRegistry instance
            supervisor: Optional Supervisor instance
            logger: Optional JSONL logger
            memory: Optional Memory interface
            plan_generator: Optional function to generate plans
        """
        self.llm = llm
        self._phase_orchestrator = phase_orchestrator
        self.step_executor = step_executor
        self._step_preparation = step_preparation
        self._ttl_strategy = ttl_strategy
        self._adaptive_depth = adaptive_depth
        self._recursive_planner = recursive_planner
        self._semantic_validator = semantic_validator
        self._convergence_engine = convergence_engine
        self.tool_registry = tool_registry
        self.supervisor = supervisor
        self.logger = logger
        self.memory = memory
        self._plan_generator = plan_generator

    def run_multipass(
        self,
        request: str,
        plan: Optional["Plan"],
        execution_context: "ExecutionContext",
        state: "OrchestrationState",
        ttl: int,
        execute_step_fn: Callable,
    ) -> Dict[str, Any]:
        """
        Run the multipass execution loop.

        Phase sequence:
        - Phase A: TaskProfile & TTL allocation
        - Phase B: Initial Plan & Pre-Execution Refinement
        - Phase C: Execution Passes (Execute Batch → Evaluate → Decide → Refine)
        - Phase D: Adaptive Depth (TaskProfile updates at pass boundaries)

        Args:
            request: Natural language request
            plan: Optional pre-generated plan
            execution_context: Execution context with correlation_id and execution_start_timestamp
            state: OrchestrationState instance
            ttl: Initial TTL value
            execute_step_fn: Function to execute a step

        Returns:
            Execution result dict with ExecutionHistory

        Raises:
            TTLExpiredError: If TTL expires during execution
        """
        from aeon.kernel.state import ExecutionPass
        from aeon.observability.helpers import build_execution_result
        from aeon.orchestration.contracts import validate_transition_contract
        from aeon.exceptions import TTLExpiredError

        execution_id = str(uuid.uuid4())
        execution_start = datetime.now()
        execution_start_timestamp = execution_context.execution_start_timestamp

        # Initialize multi-pass state
        pass_number = 0
        current_phase: Optional[Literal["A", "B", "C", "D"]] = None
        execution_passes: List[ExecutionPass] = []
        ttl_allocated = ttl  # Will be updated by Phase A

        try:
            # Phase A: TaskProfile & TTL allocation
            task_profile, ttl_allocated = self.execute_phase_a(request, ttl, execution_context)

            # Initialize state for execution
            plan_to_execute = plan or (self._plan_generator(request) if self._plan_generator else None)
            if not plan_to_execute:
                raise ValueError("Plan is required but not provided and no plan generator available")
            self._step_preparation.populate_step_indices(plan_to_execute)
            state.plan = plan_to_execute
            state.ttl_remaining = ttl_allocated

            # Contract validation: A→B transition
            inputs_a_b = {
                "task_profile": task_profile,
                "initial_plan": plan_to_execute,
                "ttl": ttl_allocated,
            }
            validate_transition_contract("A→B", inputs_a_b)

            # Phase B: Initial Plan & Pre-Execution Refinement
            plan_to_execute = self.execute_phase_b(
                request, plan_to_execute, task_profile, ttl_allocated, execution_context
            )
            self._step_preparation.populate_step_indices(plan_to_execute)
            state.plan = plan_to_execute

            # Contract validation: A→B transition outputs
            outputs_a_b = {"refined_plan": plan_to_execute}
            validate_transition_contract("A→B", inputs_a_b, outputs_a_b)

            # Contract validation: B→C transition inputs
            inputs_b_c = {
                "refined_plan": plan_to_execute,
                "refined_plan_steps": plan_to_execute.steps if plan_to_execute.steps else [],
            }
            validate_transition_contract("B→C", inputs_b_c)

            # Phase C: Execution Passes
            max_passes = 50  # Safety limit to prevent infinite loops
            try:
                converged, task_profile = self._execute_phase_c_loop(
                    execution_context,
                    execution_id,
                    request,
                    task_profile,
                    inputs_b_c,
                    max_passes,
                    state,
                    execution_passes,
                    execute_step_fn,
                )
            except TTLExpiredError:
                # TTL expiration handled by _execute_phase_c_loop, re-raise to be caught by outer handler
                raise

            # Phase E: Answer Synthesis (T080-T083)
            from aeon.orchestration.phases import execute_phase_e, PhaseEInput
            from aeon.prompts.registry import get_prompt_registry
            from aeon.orchestration.execution_pass_ops import get_execution_results
            
            # Build PhaseEInput from final execution state (T081)
            final_pass_number = len(execution_passes) if execution_passes else 0
            total_refinements = state.total_refinements if hasattr(state, 'total_refinements') else 0
            
            # Extract data from execution passes if available
            plan_state = None
            execution_results_list = None
            convergence_assessment = None
            semantic_validation = None
            execution_passes_data = None
            
            if execution_passes:
                last_pass = execution_passes[-1]
                # Serialize plan state from last pass or current state
                if last_pass.plan_state:
                    plan_state = last_pass.plan_state
                elif state.plan:
                    plan_state = state.plan.model_dump() if hasattr(state.plan, 'model_dump') else state.plan
                
                # Extract execution results from all passes
                execution_results_list = []
                for pass_item in execution_passes:
                    pass_results = get_execution_results(pass_item)
                    if pass_results:
                        execution_results_list.extend(pass_results if isinstance(pass_results, list) else [pass_results])
                
                # Extract convergence assessment and semantic validation from last pass
                if hasattr(last_pass, 'evaluation_results') and last_pass.evaluation_results:
                    evaluation_results = last_pass.evaluation_results
                    if isinstance(evaluation_results, dict):
                        convergence_assessment = evaluation_results.get('convergence_assessment')
                        semantic_validation = evaluation_results.get('semantic_validation')
                    else:
                        convergence_assessment = evaluation_results
                
                # Serialize execution passes
                execution_passes_data = [
                    pass_item.model_dump() if hasattr(pass_item, 'model_dump') else pass_item
                    for pass_item in execution_passes
                ]
            
            # Determine convergence status (PhaseEInput uses bool, but AnswerSynthesisInput accepts Union[bool, str])
            # We pass bool to PhaseEInput, and it will be converted to string in AnswerSynthesisInput if needed
            
            phase_e_input = PhaseEInput(
                request=request,
                correlation_id=execution_context.correlation_id,
                execution_start_timestamp=execution_start_timestamp.isoformat() if isinstance(execution_start_timestamp, datetime) else execution_start_timestamp,
                convergence_status=converged,
                total_passes=final_pass_number,
                total_refinements=total_refinements,
                ttl_remaining=state.ttl_remaining,
                plan_state=plan_state,
                execution_results=execution_results_list,
                convergence_assessment=convergence_assessment,
                execution_passes=execution_passes_data,
                semantic_validation=semantic_validation,
                task_profile=task_profile.model_dump() if task_profile and hasattr(task_profile, 'model_dump') else task_profile,
            )
            
            # Execute Phase E (T082) - must execute unconditionally (FR-020, FR-024)
            prompt_registry = get_prompt_registry()
            final_answer = execute_phase_e(phase_e_input, self.llm, prompt_registry)
            
            # Check if max passes limit was reached
            execution_end = datetime.now()
            if final_pass_number >= max_passes and not converged:
                result = build_execution_result(
                    execution_id,
                    request,
                    execution_start,
                    execution_end,
                    ttl_allocated,
                    task_profile,
                    converged=False,
                    status="max_passes_reached",
                    state=state,
                    execution_passes=execution_passes,
                )
                # Attach FinalAnswer to execution result (T083)
                result["final_answer"] = final_answer.model_dump() if hasattr(final_answer, 'model_dump') else final_answer
                return result

            # Build ExecutionHistory
            result = build_execution_result(
                execution_id,
                request,
                execution_start,
                execution_end,
                ttl_allocated,
                task_profile,
                converged=converged,
                status="converged" if converged else "ttl_expired",
                state=state,
                execution_passes=execution_passes,
            )
            # Attach FinalAnswer to execution result (T083)
            result["final_answer"] = final_answer.model_dump() if hasattr(final_answer, 'model_dump') else final_answer
            return result

        except TTLExpiredError as e:
            # Handle TTL expiration - Phase E must still execute (FR-020, FR-024)
            from aeon.orchestration.phases import execute_phase_e, PhaseEInput
            from aeon.prompts.registry import get_prompt_registry
            from aeon.orchestration.execution_pass_ops import get_execution_results
            
            # Build PhaseEInput for TTL expiration scenario
            final_pass_number = len(execution_passes) if execution_passes else 0
            total_refinements = state.total_refinements if hasattr(state, 'total_refinements') else 0
            
            plan_state = None
            execution_results_list = None
            convergence_assessment = None
            semantic_validation = None
            execution_passes_data = None
            
            if execution_passes:
                last_pass = execution_passes[-1]
                if last_pass.plan_state:
                    plan_state = last_pass.plan_state
                elif state.plan:
                    plan_state = state.plan.model_dump() if hasattr(state.plan, 'model_dump') else state.plan
                
                execution_results_list = []
                for pass_item in execution_passes:
                    pass_results = get_execution_results(pass_item)
                    if pass_results:
                        execution_results_list.extend(pass_results if isinstance(pass_results, list) else [pass_results])
                
                if hasattr(last_pass, 'evaluation_results') and last_pass.evaluation_results:
                    evaluation_results = last_pass.evaluation_results
                    if isinstance(evaluation_results, dict):
                        convergence_assessment = evaluation_results.get('convergence_assessment')
                        semantic_validation = evaluation_results.get('semantic_validation')
                
                execution_passes_data = [
                    pass_item.model_dump() if hasattr(pass_item, 'model_dump') else pass_item
                    for pass_item in execution_passes
                ]
            
            phase_e_input = PhaseEInput(
                request=request,
                correlation_id=execution_context.correlation_id,
                execution_start_timestamp=execution_start_timestamp.isoformat() if isinstance(execution_start_timestamp, datetime) else execution_start_timestamp,
                convergence_status=False,  # TTL expired means not converged
                total_passes=final_pass_number,
                total_refinements=total_refinements,
                ttl_remaining=0,  # TTL expired
                plan_state=plan_state,
                execution_results=execution_results_list,
                convergence_assessment=convergence_assessment,
                execution_passes=execution_passes_data,
                semantic_validation=semantic_validation,
                task_profile=task_profile.model_dump() if task_profile and hasattr(task_profile, 'model_dump') else task_profile,
            )
            
            # Execute Phase E even on TTL expiration
            prompt_registry = get_prompt_registry()
            final_answer = execute_phase_e(phase_e_input, self.llm, prompt_registry)
            
            # Try to get TTL expiration response if available
            if execution_passes:
                last_pass = execution_passes[-1]
                success, response, error = self._ttl_strategy.create_expiration_response(
                    "mid_phase",
                    current_phase or "C",
                    last_pass,
                    execution_passes,
                    state,
                    execution_id,
                    request,
                )
                if success:
                    # Attach FinalAnswer to expiration response
                    response["final_answer"] = final_answer.model_dump() if hasattr(final_answer, 'model_dump') else final_answer
                    return response
            
            # Fallback: return minimal response with FinalAnswer
            execution_end = datetime.now()
            return {
                "execution_id": execution_id,
                "request": request,
                "status": "ttl_expired",
                "final_answer": final_answer.model_dump() if hasattr(final_answer, 'model_dump') else final_answer,
            }

    def execute_phase_a(
        self,
        request: str,
        ttl: int,
        execution_context: "ExecutionContext",
    ) -> Tuple[Any, int]:  # Returns (task_profile, ttl_allocated)
        """
        Execute Phase A: TaskProfile & TTL allocation.
        
        Returns:
            Tuple of (task_profile, ttl_allocated)
        """
        from aeon.orchestration.contracts import validate_phase_entry, validate_phase_exit
        from aeon.orchestration.execution_pass_ops import (
            build_execution_pass_after_phase,
            build_execution_pass_before_phase,
        )
        from aeon.orchestration.ttl import check_ttl_before_phase_entry
        from aeon.orchestration.validation import check_ttl_at_phase_boundary
        from aeon.exceptions import TTLExpiredError

        temp_pass_a = build_execution_pass_before_phase(0, "A", {}, ttl)
        validate_phase_entry(temp_pass_a, "A")
        can_proceed, expiration_response = check_ttl_before_phase_entry(ttl, "A", temp_pass_a)
        if not can_proceed:
            raise TTLExpiredError(f"TTL expired before Phase A: {expiration_response.message if expiration_response else 'Unknown'}")

        success, (task_profile, ttl_allocated), error = self._execute_phase_with_logging(
            phase="A",
            correlation_id=execution_context.correlation_id,
            pass_number=0,
            phase_fn=self._phase_orchestrator.phase_a_taskprofile_ttl,
            request=request,
            adaptive_depth=self._adaptive_depth,
            global_ttl=ttl,
            execution_context=execution_context,
            ttl_remaining=ttl,
        )
        if not success:
            from aeon.adaptive.models import TaskProfile
            task_profile = TaskProfile.default()
            ttl_allocated = ttl

        temp_pass_a = build_execution_pass_after_phase(temp_pass_a, datetime.now())
        validate_phase_exit(temp_pass_a, "A")
        check_ttl_at_phase_boundary(ttl_allocated, "A", temp_pass_a, 0, {})

        return (task_profile, ttl_allocated)

    def execute_phase_b(
        self,
        request: str,
        plan: "Plan",
        task_profile: Any,
        ttl_allocated: int,
        execution_context: "ExecutionContext",
    ) -> "Plan":  # Returns refined plan
        """
        Execute Phase B: Initial Plan & Pre-Execution Refinement.
        
        Returns:
            Refined plan
        """
        from aeon.orchestration.contracts import validate_phase_entry, validate_phase_exit
        from aeon.orchestration.execution_pass_ops import (
            build_execution_pass_after_phase,
            build_execution_pass_before_phase,
        )
        from aeon.orchestration.ttl import check_ttl_before_phase_entry
        from aeon.orchestration.validation import check_ttl_at_phase_boundary
        from aeon.exceptions import TTLExpiredError

        temp_pass_b = build_execution_pass_before_phase(
            0, "B", plan.model_dump() if plan else {}, ttl_allocated
        )
        validate_phase_entry(temp_pass_b, "B")
        can_proceed, expiration_response = check_ttl_before_phase_entry(ttl_allocated, "B", temp_pass_b)
        if not can_proceed:
            raise TTLExpiredError(f"TTL expired before Phase B: {expiration_response.message if expiration_response else 'Unknown'}")

        success, refined_plan, error = self._execute_phase_with_logging(
            phase="B",
            correlation_id=execution_context.correlation_id,
            pass_number=0,
            phase_fn=self._phase_orchestrator.phase_b_initial_plan_refinement,
            request=request,
            plan=plan,
            task_profile=task_profile,
            recursive_planner=self._recursive_planner,
            semantic_validator=self._semantic_validator,
            tool_registry=self.tool_registry,
            execution_context=execution_context,
            logger=self.logger,
            ttl_remaining=ttl_allocated,
        )
        if not success:
            refined_plan = plan  # Continue with original plan if refinement fails

        temp_pass_b = build_execution_pass_after_phase(temp_pass_b, datetime.now())
        validate_phase_exit(temp_pass_b, "B")
        check_ttl_at_phase_boundary(ttl_allocated, "B", None, 0, refined_plan.model_dump() if refined_plan else {})

        return refined_plan

    def _execute_phase_with_logging(
        self,
        phase: str,
        correlation_id: str,
        pass_number: int,
        phase_fn: Callable,
        *args,
        **kwargs,
    ) -> Tuple[Any, ...]:
        """
        Execute a phase function with entry/exit logging.
        Returns the result of the phase function.
        """
        start_time = datetime.now()
        if self.logger:
            self.logger.log_phase_entry(phase=phase, correlation_id=correlation_id, pass_number=pass_number)
        try:
            result = phase_fn(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            if self.logger:
                success = result[0] if isinstance(result, tuple) and len(result) > 0 else True
                self.logger.log_phase_exit(
                    phase=phase,
                    correlation_id=correlation_id,
                    duration=duration,
                    outcome="success" if success else "failure",
                    pass_number=pass_number,
                )
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            if self.logger:
                self.logger.log_phase_exit(
                    phase=phase,
                    correlation_id=correlation_id,
                    duration=duration,
                    outcome="failure",
                    pass_number=pass_number,
                )
            raise

    def _execute_phase_c_loop(
        self,
        execution_context: "ExecutionContext",
        execution_id: str,
        request: str,
        task_profile: Any,
        inputs_b_c: Dict[str, Any],
        max_passes: int,
        state: "OrchestrationState",
        execution_passes: List["ExecutionPass"],
        execute_step_fn: Callable,
    ) -> Tuple[bool, Any]:
        """
        Execute Phase C execution passes until convergence or TTL expiration.
        Returns (converged, updated_task_profile).
        """
        from aeon.orchestration.contracts import (
            validate_phase_entry,
            validate_phase_exit,
            validate_phase_invariants,
            validate_transition_contract,
        )
        from aeon.orchestration.execution_pass_ops import (
            apply_refinement_to_plan_state,
            build_execution_pass_after_phase,
            build_execution_pass_before_phase,
            merge_evaluation_results,
            merge_execution_results,
        )
        from aeon.orchestration.strategy import has_converged, should_refine
        from aeon.orchestration.ttl import check_ttl_after_llm_call, check_ttl_before_phase_entry, decrement_ttl_per_cycle
        from aeon.orchestration.validation import check_ttl_at_phase_boundary
        from aeon.exceptions import TTLExpiredError

        converged = False
        initial_pass_number = len(execution_passes)
        pass_number = initial_pass_number
        while not converged and state.ttl_remaining > 0 and pass_number < max_passes:
            pass_number += 1

            # Create ExecutionPass for this pass
            execution_pass = build_execution_pass_before_phase(
                pass_number,
                "C",
                state.plan.model_dump(),
                state.ttl_remaining,
            )

            # Validate before Phase C entry
            validate_phase_entry(execution_pass, "C")

            # TTL check before phase entry
            can_proceed, expiration_response = check_ttl_before_phase_entry(state.ttl_remaining, "C", execution_pass)
            if not can_proceed:
                execution_pass = build_execution_pass_after_phase(execution_pass, datetime.now())
                execution_passes.append(execution_pass)
                success, response, error = self._ttl_strategy.create_expiration_response(
                    "phase_boundary",
                    "C",
                    execution_pass,
                    execution_passes,
                    state,
                    execution_id,
                    request,
                )
                if success:
                    raise TTLExpiredError(f"TTL expired before Phase C: {expiration_response.message if expiration_response else 'Unknown'}")
                raise TTLExpiredError("TTL expired before Phase C")

            # Execute batch of ready steps
            from aeon.orchestration.execution_pass_ops import get_execution_results, get_refinement_changes
            previous_outputs = get_execution_results(execution_pass)
            refinement_changes = get_refinement_changes(execution_pass)
            execution_results = self._phase_orchestrator.phase_c_execute_batch(
                state.plan,
                state,
                self.step_executor,
                self.tool_registry,
                self.memory,
                self.supervisor,
                execute_step_fn,
                execution_context=execution_context,
                task_profile=task_profile,
                pass_number=pass_number,
                ttl_remaining=state.ttl_remaining,
                request=request,
                previous_outputs=previous_outputs,
                refinement_changes=refinement_changes,
            )
            execution_pass = merge_execution_results(execution_pass, execution_results)

            # Contract validation: B→C transition outputs
            outputs_b_c = {"execution_results": execution_results}
            validate_transition_contract("B→C", inputs_b_c, outputs_b_c)

            # TTL check after LLM call within phase
            can_proceed, expiration_response = check_ttl_after_llm_call(state.ttl_remaining, "C", execution_pass)
            if not can_proceed:
                execution_pass = build_execution_pass_after_phase(execution_pass, datetime.now())
                execution_passes.append(execution_pass)
                success, response, error = self._ttl_strategy.create_expiration_response(
                    "mid_phase",
                    "C",
                    execution_pass,
                    execution_passes,
                    state,
                    execution_id,
                    request,
                )
                if success:
                    raise TTLExpiredError(f"TTL expired mid-phase C: {expiration_response.message if expiration_response else 'Unknown'}")
                raise TTLExpiredError("TTL expired mid-phase C")

            # Evaluate: semantic validation + convergence
            evaluation_results = self._phase_orchestrator.phase_c_evaluate(
                state.plan,
                execution_results,
                self._semantic_validator,
                self._convergence_engine,
                self.tool_registry,
                execution_context=execution_context,
                logger=self.logger,
                task_profile=task_profile,
                pass_number=pass_number,
                ttl_remaining=state.ttl_remaining,
                request=request,
            )
            execution_pass = merge_evaluation_results(execution_pass, evaluation_results)

            # Contract validation: C→D transition inputs
            inputs_c_d = {
                "execution_results": execution_results,
                "evaluation_results": evaluation_results,
            }
            validate_transition_contract("C→D", inputs_c_d)

            # Check convergence
            converged = has_converged(evaluation_results)
            if converged:
                execution_pass = build_execution_pass_after_phase(execution_pass, datetime.now())
                validate_phase_exit(execution_pass, "C")
                validate_phase_invariants(execution_pass, "C")
                execution_passes.append(execution_pass)
                break

            # Decide: check if refinement needed
            needs_refinement = should_refine(evaluation_results)
            if needs_refinement:
                success, refinement_changes, error, updated_plan = self._phase_orchestrator.phase_c_refine(
                    state.plan,
                    evaluation_results,
                    self._recursive_planner,
                    lambda p: self._step_preparation.populate_step_indices(p),
                    execution_context=execution_context,
                    logger=self.logger,
                    task_profile=task_profile,
                    pass_number=pass_number,
                    ttl_remaining=state.ttl_remaining,
                    request=request,
                    execution_results_list=execution_results,
                )
                if success and updated_plan:
                    state.plan = updated_plan
                    from aeon.orchestration.execution_pass_ops import set_refinement_changes
                    execution_pass = set_refinement_changes(execution_pass, refinement_changes)
                    execution_pass = apply_refinement_to_plan_state(execution_pass, updated_plan)

            # Phase D: Adaptive Depth (at pass boundary)
            if pass_number > 0:
                # Validate before Phase D entry
                validate_phase_entry(execution_pass, "D")
                # TTL check before phase entry
                can_proceed, expiration_response = check_ttl_before_phase_entry(state.ttl_remaining, "D", execution_pass)
                if not can_proceed:
                    execution_pass = build_execution_pass_after_phase(execution_pass, datetime.now())
                    execution_passes.append(execution_pass)
                    success, response, error = self._ttl_strategy.create_expiration_response(
                        "phase_boundary",
                        "D",
                        execution_pass,
                        execution_passes,
                        state,
                        execution_id,
                        request,
                    )
                    if success:
                        raise TTLExpiredError(f"TTL expired before Phase D: {expiration_response.message if expiration_response else 'Unknown'}")
                    raise TTLExpiredError("TTL expired before Phase D")

                success, updated_task_profile, error = self._phase_orchestrator.phase_d_adaptive_depth(
                    task_profile,
                    evaluation_results,
                    state.plan,
                    self._adaptive_depth,
                    state,
                    state.ttl_remaining,  # Use state.ttl_remaining instead of self.ttl
                    execution_passes,
                    execution_context=execution_context,
                    logger=self.logger,
                    pass_number=pass_number,
                    ttl_remaining=state.ttl_remaining,
                    request=request,
                )
                if success and updated_task_profile:
                    task_profile = updated_task_profile

                validate_phase_invariants(execution_pass, "D")
                check_ttl_at_phase_boundary(state.ttl_remaining, "D", execution_pass, pass_number, state.plan.model_dump() if state else {})

                # Contract validation: C→D transition outputs
                outputs_c_d = {"updated_task_profile": updated_task_profile}
                validate_transition_contract("C→D", inputs_c_d, outputs_c_d)

                # Contract validation: D→A/B transition inputs
                inputs_d_ab = {
                    "task_profile": task_profile,
                    "ttl_remaining": state.ttl_remaining,
                }
                validate_transition_contract("D→A/B", inputs_d_ab)

                # TTL decrement occurs in Phase D completion
                state.ttl_remaining = decrement_ttl_per_cycle(state.ttl_remaining)
                from aeon.orchestration.execution_pass_ops import update_ttl_remaining
                execution_pass = update_ttl_remaining(execution_pass, state.ttl_remaining)

            # Complete pass
            execution_pass = build_execution_pass_after_phase(execution_pass, datetime.now())
            validate_phase_exit(execution_pass, "C")
            validate_phase_invariants(execution_pass, "C")
            execution_passes.append(execution_pass)

            # Check TTL at phase boundary before next pass
            if state.ttl_remaining <= 0:
                raise TTLExpiredError("TTL expired at phase C boundary")

        return (converged, task_profile)

