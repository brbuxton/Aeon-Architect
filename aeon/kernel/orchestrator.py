"""Core orchestrator for LLM orchestration loop."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid

from aeon.adaptive.heuristics import AdaptiveDepth
from aeon.exceptions import LLMError, PlanError, SupervisorError, ToolError, TTLExpiredError, ValidationError
from aeon.kernel.executor import StepExecutor
from aeon.kernel.state import ExecutionHistory, ExecutionPass, OrchestrationState, TTLExpirationResponse
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.observability.helpers import collect_cycle_data
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
                    except (SupervisorError, PlanError) as repair_error:
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
                attempt_tool_repair(step, tool_registry, supervisor, state.plan.goal)
                # If repair failed, will fallback to LLM reasoning in StepExecutor (T118)
        
        # Use StepExecutor for multi-mode execution (T116)
        try:
            execution_result = self.step_executor.execute_step(
                step=step,
                registry=tool_registry or ToolRegistry(),  # Empty registry if None
                memory=self.memory,
                llm=self.llm,
                supervisor=supervisor,
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

        # Initialize multi-pass state
        self._pass_number = 0
        self._current_phase = None
        self._execution_passes = []
        ttl_allocated = self.ttl  # Will be updated by Phase A

        try:
            # Phase A: TaskProfile & TTL allocation
            task_profile, ttl_allocated = self._phase_a_taskprofile_ttl(request)
            self._check_ttl_at_phase_boundary(ttl_allocated, "A")

            # Initialize state for execution
            plan_to_execute = plan or self.generate_plan(request)
            # Populate step indices before execution
            self._populate_step_indices(plan_to_execute)
            self.state = OrchestrationState(
                plan=plan_to_execute,
                ttl_remaining=ttl_allocated,
                memory=self.memory
            )
            self._cycle_number = 0

            # Phase B: Initial Plan & Pre-Execution Refinement
            plan_to_execute = self._phase_b_initial_plan_refinement(request, plan_to_execute, task_profile)
            # Re-populate step indices after refinement (in case steps were added/removed)
            self._populate_step_indices(plan_to_execute)
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

                # Execute batch of ready steps
                execution_results = self._phase_c_execute_batch()
                execution_pass.execution_results = execution_results

                # Check TTL at safe boundary (after batch execution)
                if self.state.ttl_remaining <= 0:
                    # TTL expired mid-phase
                    execution_pass.timing_information["end_time"] = datetime.now().isoformat()
                    execution_pass.timing_information["duration"] = (datetime.now() - pass_start).total_seconds()
                    self._execution_passes.append(execution_pass)
                    return self._create_ttl_expiration_response("mid_phase", "C", execution_pass)

                # Evaluate: semantic validation + convergence
                evaluation_results = self._phase_c_evaluate()
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
                    # Refine plan
                    refinement_changes = self._phase_c_refine(evaluation_results)
                    execution_pass.refinement_changes = refinement_changes

                # Phase D: Adaptive Depth (at pass boundary)
                if self._pass_number > 0:  # Only after first pass
                    task_profile = self._phase_d_adaptive_depth(task_profile, evaluation_results)
                    self._check_ttl_at_phase_boundary(self.state.ttl_remaining, "D")

                # Complete pass
                execution_pass.timing_information["end_time"] = datetime.now().isoformat()
                execution_pass.timing_information["duration"] = (datetime.now() - pass_start).total_seconds()
                self._execution_passes.append(execution_pass)

                # Check TTL at phase boundary before next pass
                if self.state.ttl_remaining <= 0:
                    return self._create_ttl_expiration_response("phase_boundary", "C", execution_pass)

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
            # Handle TTL expiration
            if self._execution_passes:
                last_pass = self._execution_passes[-1]
                return self._create_ttl_expiration_response("mid_phase", self._current_phase or "C", last_pass)
            raise

    def _phase_a_taskprofile_ttl(self, request: str) -> tuple[Any, int]:
        """
        Phase A: TaskProfile inference and TTL allocation.

        Implements User Story 2 - TaskProfile inference and TTL allocation.

        Args:
            request: Natural language request

        Returns:
            Tuple of (TaskProfile, allocated_ttl)

        Raises:
            LLMError: If LLM operations fail
        """
        if not self._adaptive_depth:
            # Fallback to default if AdaptiveDepth not available
            from aeon.adaptive.models import TaskProfile
            default_task_profile = TaskProfile.default()
            allocated_ttl = self.ttl
            return default_task_profile, allocated_ttl

        # Infer TaskProfile using AdaptiveDepth
        task_profile = self._adaptive_depth.infer_task_profile(
            task_description=request,
            context=None,  # Can be extended with previous attempts, user preferences, etc.
        )

        # Allocate TTL based on TaskProfile
        allocated_ttl = self._adaptive_depth.allocate_ttl(
            task_profile=task_profile,
            global_ttl_limit=self.ttl,  # Use configured TTL as global limit
        )

        return task_profile, allocated_ttl

    def _phase_b_initial_plan_refinement(self, request: str, plan: Plan, task_profile: Any) -> Plan:
        """
        Phase B: Initial Plan & Pre-Execution Refinement.

        Args:
            request: Natural language request
            plan: Initial plan
            task_profile: TaskProfile from Phase A

        Returns:
            Refined plan
        """
        # Use RecursivePlanner.generate_plan() if available to ensure proper structure
        if self._recursive_planner:
            try:
                # Regenerate plan using RecursivePlanner to ensure step_index, total_steps, etc. are set
                plan = self._recursive_planner.generate_plan(
                    task_description=request,
                    task_profile=task_profile,
                    tool_registry=self.tool_registry,
                )
            except Exception as e:
                # If RecursivePlanner fails, fall back to existing plan
                # Log error but continue with existing plan
                pass

        # Phase B: Plan Validation - semantic validation
        if self._semantic_validator:
            try:
                semantic_validation_report = self._semantic_validator.validate(
                    artifact=plan.model_dump(),
                    artifact_type="plan",
                    tool_registry=self.tool_registry,
                )
                # If validation issues found, refine plan
                if semantic_validation_report.issues and self._recursive_planner:
                    refinement_actions = self._recursive_planner.refine_plan(
                        current_plan=plan,
                        validation_issues=semantic_validation_report.issues,
                        convergence_reason_codes=[],
                        blocked_steps=[],
                        executed_step_ids=set(),
                    )
                    # Apply refinement actions to plan
                    plan = self._apply_refinement_actions(plan, refinement_actions)
            except Exception as e:
                # If semantic validation fails, continue with existing plan (best-effort advisory)
                # Log error but don't fail phase
                pass

        return plan

    def _phase_c_execute_batch(self) -> List[Dict[str, Any]]:
        """
        Phase C: Execute batch of ready steps.

        Executes all steps that are ready (dependencies satisfied) in parallel.

        Returns:
            List of execution results
        """
        execution_results = []
        ready_steps = self._get_ready_steps()

        for step in ready_steps:
            try:
                # Execute step
                self._execute_step(step, self.state)
                execution_results.append({
                    "step_id": step.step_id,
                    "status": step.status.value,
                    "output": getattr(step, 'step_output', None),
                    "clarity_state": getattr(step, 'clarity_state', None)
                })
                # Decrement TTL after step execution
                self.state.ttl_remaining -= 1
            except Exception as e:
                execution_results.append({
                    "step_id": step.step_id,
                    "status": "failed",
                    "error": str(e)
                })

        return execution_results

    def _phase_c_evaluate(self) -> Dict[str, Any]:
        """
        Phase C: Evaluate execution results (semantic validation + convergence).

        Returns:
            Evaluation results with converged flag and needs_refinement flag
        """
        if not self.state:
            return {
                "converged": False,
                "needs_refinement": False,
                "semantic_validation": {},
                "convergence_assessment": {},
            }

        # Build execution results for validation and convergence assessment
        execution_results = [
            {
                "step_id": step.step_id,
                "status": step.status.value,
                "output": getattr(step, "step_output", None),
                "clarity_state": getattr(step, "clarity_state", None),
            }
            for step in self.state.plan.steps
            if step.status in (StepStatus.COMPLETE, StepStatus.FAILED, StepStatus.INVALID)
        ]

        # 1. Call SemanticValidator.validate() for execution artifacts
        semantic_validation_report = None
        if self._semantic_validator:
            try:
                # Validate current plan state and execution artifacts
                execution_artifact = {
                    "plan": self.state.plan.model_dump(),
                    "execution_results": execution_results,
                }
                semantic_validation_report = self._semantic_validator.validate(
                    artifact=execution_artifact,
                    artifact_type="execution_artifact",
                    tool_registry=self.tool_registry,
                )
            except Exception as e:
                # If semantic validation fails, continue with empty report (best-effort advisory)
                semantic_validation_report = None

        # 2. Call ConvergenceEngine.assess() with validation report
        convergence_assessment = None
        if self._convergence_engine:
            try:
                # Create a default empty validation report if none exists
                if semantic_validation_report is None:
                    from aeon.validation.models import SemanticValidationReport
                    semantic_validation_report = SemanticValidationReport(
                        artifact_type="execution_artifact",
                        issues=[],
                    )
                
                convergence_assessment = self._convergence_engine.assess(
                    plan_state=self.state.plan.model_dump(),
                    execution_results=execution_results,
                    semantic_validation_report=semantic_validation_report,
                )
            except Exception as e:
                # If convergence assessment fails, create conservative assessment
                from aeon.convergence.models import ConvergenceAssessment
                convergence_assessment = ConvergenceAssessment(
                    converged=False,
                    reason_codes=["convergence_assessment_failed", str(e)],
                    completeness_score=0.0,
                    coherence_score=0.0,
                    consistency_status={},
                    detected_issues=[f"Convergence assessment failed: {str(e)}"],
                    metadata={"error": str(e)},
                )
        else:
            # Fallback if convergence engine not available
            from aeon.convergence.models import ConvergenceAssessment
            convergence_assessment = ConvergenceAssessment(
                converged=False,
                reason_codes=["convergence_engine_not_available"],
                completeness_score=0.0,
                coherence_score=0.0,
                consistency_status={},
                detected_issues=[],
                metadata={},
            )

        # Check if all steps are complete (automatic convergence detection)
        all_steps_complete = all(
            step.status in (StepStatus.COMPLETE, StepStatus.FAILED, StepStatus.INVALID)
            for step in self.state.plan.steps
        )
        
        # Determine if refinement is needed
        needs_refinement = False
        if semantic_validation_report and semantic_validation_report.issues:
            # Refinement needed if there are validation issues
            needs_refinement = True
        if convergence_assessment and not convergence_assessment.converged:
            # Refinement needed if not converged
            needs_refinement = True

        # Automatic convergence: if all steps are complete and no validation issues, mark as converged
        auto_converged = False
        if all_steps_complete:
            if not semantic_validation_report or not semantic_validation_report.issues:
                # All steps complete and no validation issues - auto-converge
                auto_converged = True
            elif semantic_validation_report.overall_severity in ("LOW", "INFO"):
                # All steps complete and only low-severity issues - auto-converge
                auto_converged = True

        # Use auto-convergence if LLM-based assessment didn't converge but conditions are met
        final_converged = convergence_assessment.converged if convergence_assessment else False
        if not final_converged and auto_converged:
            final_converged = True

        return {
            "converged": final_converged,
            "needs_refinement": needs_refinement and not auto_converged,  # Don't refine if auto-converged
            "semantic_validation": semantic_validation_report.model_dump() if semantic_validation_report else {},
            "convergence_assessment": convergence_assessment.model_dump() if convergence_assessment else {},
            "validation_issues": semantic_validation_report.issues if semantic_validation_report else [],
            "convergence_reason_codes": convergence_assessment.reason_codes if convergence_assessment else [],
        }

    def _phase_c_refine(self, evaluation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Phase C: Refine plan based on evaluation results.

        Args:
            evaluation_results: Results from evaluation phase

        Returns:
            List of refinement changes
        """
        if not self._recursive_planner or not self.state:
            return []

        # Extract validation issues, convergence reason codes, and blocked steps
        validation_issues = evaluation_results.get("validation_issues", [])
        convergence_reason_codes = evaluation_results.get("convergence_reason_codes", [])
        blocked_steps = evaluation_results.get("blocked_steps", [])

        # Get executed step IDs (steps with status complete or failed)
        executed_step_ids = {
            step.step_id
            for step in self.state.plan.steps
            if step.status in (StepStatus.COMPLETE, StepStatus.FAILED)
        }

        try:
            # Generate refinement actions
            refinement_actions = self._recursive_planner.refine_plan(
                current_plan=self.state.plan,
                validation_issues=validation_issues,
                convergence_reason_codes=convergence_reason_codes,
                blocked_steps=blocked_steps,
                executed_step_ids=executed_step_ids,
            )

            # Apply refinement actions to plan
            if refinement_actions:
                self.state.plan = self._apply_refinement_actions(self.state.plan, refinement_actions)
                # Re-populate step indices after refinement
                self._populate_step_indices(self.state.plan)

            # Convert refinement actions to dict format for logging
            refinement_changes = [action.model_dump() for action in refinement_actions]
            return refinement_changes

        except Exception as e:
            # If refinement fails, log error and continue without refinement
            # TODO: Add proper error logging
            return []

    def _apply_refinement_actions(self, plan: Plan, refinement_actions: List[Any]) -> Plan:
        """
        Apply refinement actions to plan.

        Args:
            plan: Current plan
            refinement_actions: List of RefinementAction objects

        Returns:
            Updated plan
        """
        from aeon.plan.models import RefinementAction

        for action in refinement_actions:
            if not isinstance(action, RefinementAction):
                continue

            if action.action_type == "ADD":
                if action.new_step:
                    # Create new PlanStep from new_step dict
                    new_step = PlanStep(**action.new_step)
                    plan.steps.append(new_step)
            elif action.action_type == "MODIFY":
                if action.target_step_id:
                    # Find step and update it
                    step = next((s for s in plan.steps if s.step_id == action.target_step_id), None)
                    if step and action.new_step:
                        # Update step fields from new_step dict
                        for key, value in action.new_step.items():
                            if hasattr(step, key):
                                setattr(step, key, value)
            elif action.action_type == "REMOVE":
                if action.target_step_id:
                    # Remove step from plan
                    plan.steps = [s for s in plan.steps if s.step_id != action.target_step_id]
            elif action.action_type == "REPLACE":
                if action.target_step_id and action.new_step:
                    # Replace step with new step
                    step_index = next(
                        (i for i, s in enumerate(plan.steps) if s.step_id == action.target_step_id),
                        None
                    )
                    if step_index is not None:
                        new_step = PlanStep(**action.new_step)
                        plan.steps[step_index] = new_step

        return plan

    def _phase_d_adaptive_depth(self, task_profile: Any, evaluation_results: Dict[str, Any]) -> Any:
        """
        Phase D: Adaptive Depth - update TaskProfile at pass boundaries.

        Args:
            task_profile: Current TaskProfile
            evaluation_results: Results from evaluation phase (includes convergence_assessment, semantic_validation, clarity_states)

        Returns:
            Updated TaskProfile (or original if no update triggered)
        """
        if not self._adaptive_depth or not task_profile:
            return task_profile

        # Extract convergence assessment and semantic validation report
        convergence_assessment_dict = evaluation_results.get("convergence_assessment", {})
        semantic_validation_dict = evaluation_results.get("semantic_validation", {})

        # Convert dicts to model instances if needed
        from aeon.convergence.models import ConvergenceAssessment
        from aeon.validation.models import SemanticValidationReport

        convergence_assessment = None
        if convergence_assessment_dict:
            try:
                convergence_assessment = ConvergenceAssessment(**convergence_assessment_dict)
            except Exception:
                pass

        semantic_validation_report = None
        if semantic_validation_dict:
            try:
                semantic_validation_report = SemanticValidationReport(**semantic_validation_dict)
            except Exception:
                pass

        # Collect clarity states from execution results
        clarity_states = []
        if self.state and self.state.plan:
            for step in self.state.plan.steps:
                clarity_state = getattr(step, 'clarity_state', None)
                if clarity_state:
                    clarity_states.append(clarity_state)

        # Call AdaptiveDepth.update_task_profile() (T101, T102, T105)
        updated_profile = self._adaptive_depth.update_task_profile(
            current_profile=task_profile,
            convergence_assessment=convergence_assessment,
            semantic_validation_report=semantic_validation_report,
            clarity_states=clarity_states,
        )

        if updated_profile:
            # Adjust TTL bidirectionally based on profile update (T103)
            old_ttl = self.state.ttl_remaining if self.state else self.ttl
            adjusted_ttl, adjustment_reason = self._adaptive_depth.adjust_ttl_for_updated_profile(
                old_profile=task_profile,
                new_profile=updated_profile,
                current_ttl=old_ttl,
                global_ttl_limit=self.ttl,
            )

            # Update state TTL (T103)
            if self.state:
                self.state.ttl_remaining = adjusted_ttl

            # Record adjustment_reason in execution metadata (T105)
            # Store in the current execution pass
            if self._execution_passes:
                current_pass = self._execution_passes[-1]
                if "adaptive_depth_adjustment" not in current_pass.evaluation_results:
                    current_pass.evaluation_results["adaptive_depth_adjustment"] = {}
                current_pass.evaluation_results["adaptive_depth_adjustment"] = {
                    "profile_version_old": task_profile.profile_version,
                    "profile_version_new": updated_profile.profile_version,
                    "adjustment_reason": adjustment_reason,
                    "ttl_old": old_ttl,
                    "ttl_new": adjusted_ttl,
                }

            return updated_profile

        return task_profile

    def _get_ready_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready_steps = []
        for step in self.state.plan.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are complete
                dependencies_satisfied = True
                # Check for dependencies field (may not exist in all plans)
                dependencies = getattr(step, 'dependencies', None)
                if dependencies:
                    for dep_id in dependencies:
                        dep_step = next((s for s in self.state.plan.steps if s.step_id == dep_id), None)
                        if not dep_step or dep_step.status != StepStatus.COMPLETE:
                            dependencies_satisfied = False
                            break
                if dependencies_satisfied:
                    # Populate incoming_context from dependency outputs
                    self._populate_incoming_context(step)
                    ready_steps.append(step)
        return ready_steps

    def _populate_incoming_context(self, step: PlanStep) -> None:
        """
        Populate incoming_context from dependency step outputs.

        Args:
            step: PlanStep to populate context for
        """
        if not self.memory:
            return

        dependencies = getattr(step, 'dependencies', None)
        if not dependencies:
            return

        context_parts = []
        for dep_id in dependencies:
            # Try to get output from memory
            memory_key = f"step_{dep_id}_result"
            try:
                dep_output = self.memory.read(memory_key)
                if dep_output:
                    # Also check for handoff_to_next from the dependency step
                    dep_step = next((s for s in self.state.plan.steps if s.step_id == dep_id), None)
                    if dep_step and hasattr(dep_step, 'handoff_to_next') and dep_step.handoff_to_next:
                        context_parts.append(f"From step {dep_id}: {dep_step.handoff_to_next}")
                    else:
                        context_parts.append(f"From step {dep_id}: {dep_output}")
            except Exception:
                # If memory read fails, continue without that context
                pass

        if context_parts and hasattr(step, 'incoming_context'):
            step.incoming_context = "\n".join(context_parts)

    def _populate_step_indices(self, plan: Plan) -> None:
        """
        Populate step_index and total_steps for all steps in plan.

        Args:
            plan: Plan to populate indices for
        """
        total_steps = len(plan.steps)
        for idx, step in enumerate(plan.steps, start=1):
            if hasattr(step, 'step_index'):
                step.step_index = idx
            if hasattr(step, 'total_steps'):
                step.total_steps = total_steps

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

    def _create_ttl_expiration_response(
        self,
        expiration_type: Literal["phase_boundary", "mid_phase"],
        phase: Literal["A", "B", "C", "D"],
        execution_pass: ExecutionPass
    ) -> Dict[str, Any]:
        """
        Create TTL expiration response.

        Args:
            expiration_type: Where TTL expired (phase_boundary or mid_phase)
            phase: Phase where expiration occurred
            execution_pass: Last execution pass

        Returns:
            TTL expiration response dict
        """
        expiration_response = TTLExpirationResponse(
            expiration_type=expiration_type,
            phase=phase,
            pass_number=execution_pass.pass_number,
            ttl_remaining=self.state.ttl_remaining if self.state else 0,
            plan_state=execution_pass.plan_state,
            execution_results=execution_pass.execution_results,
            message=f"TTL expired {expiration_type} during phase {phase} at pass {execution_pass.pass_number}"
        )

        # Build ExecutionHistory with partial results
        execution_history = ExecutionHistory(
            execution_id=str(uuid.uuid4()),
            task_input="",  # Will be set by caller
            configuration={},
            passes=self._execution_passes,
            final_result={
                "status": "ttl_expired",
                "expiration": expiration_response.model_dump()
            },
            overall_statistics={
                "total_passes": len(self._execution_passes),
                "total_refinements": sum(len(p.refinement_changes) for p in self._execution_passes),
                "convergence_achieved": False,
                "total_time": 0.0
            }
        )

        return {
            "execution_history": execution_history.model_dump(),
            "status": "ttl_expired",
            "ttl_expiration": expiration_response.model_dump(),
            "ttl_remaining": self.state.ttl_remaining if self.state else 0,
        }

