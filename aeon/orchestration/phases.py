"""Phase orchestration logic for multi-pass execution.

This module contains the PhaseOrchestrator class that orchestrates Phase A/B/C/D
logic for multi-pass execution, extracted from the kernel to reduce LOC.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple

if TYPE_CHECKING:
    from aeon.adaptive.models import TaskProfile
    from aeon.plan.models import Plan
    from aeon.kernel.state import ExecutionContext, OrchestrationState, ExecutionPass
    from aeon.observability.logger import JSONLLogger

__all__ = ["PhaseOrchestrator", "PhaseResult"]


# Data model: PhaseResult
# Structured result from phase orchestration methods, enabling kernel to handle success/error cases gracefully.
# 
# Fields (as tuple return):
# - success (boolean, required): Whether the phase operation succeeded
# - result (Any, optional): Operation result (type depends on phase method)
# - error (string, optional): Error message if success is False
#
# Validation Rules:
# - If success is True, result must be present
# - If success is False, error must be present
# - Result type depends on phase method (see PhaseOrchestrator interface)

# Type aliases for phase result tuples
PhaseAResult = Tuple[bool, Tuple[Optional["TaskProfile"], int], Optional[str]]
PhaseBResult = Tuple[bool, "Plan", Optional[str]]
PhaseCExecuteResult = List[Dict[str, Any]]  # No error tuple, returns list directly
PhaseCEvaluateResult = Dict[str, Any]  # No error tuple, returns dict directly
PhaseCRefineResult = Tuple[bool, List[Dict[str, Any]], Optional[str]]
PhaseDResult = Tuple[bool, Optional["TaskProfile"], Optional[str]]

# Legacy alias for backwards compatibility
PhaseResult = Any  # Type varies by phase method


class PhaseOrchestrator:
    """Orchestrates Phase A/B/C/D logic for multi-pass execution."""

    def phase_a_taskprofile_ttl(
        self,
        request: str,
        adaptive_depth: Optional[Any],  # AdaptiveDepth
        global_ttl: int,
    ) -> PhaseAResult:
        """
        Phase A: TaskProfile inference and TTL allocation.

        Args:
            request: Natural language request
            adaptive_depth: AdaptiveDepth instance (may be None for fallback)
            global_ttl: Global TTL limit

        Returns:
            Tuple of (success, (task_profile, allocated_ttl), error_message)
        """
        from aeon.adaptive.models import TaskProfile

        if not adaptive_depth:
            # Fallback to default if AdaptiveDepth not available
            default_task_profile = TaskProfile.default()
            allocated_ttl = global_ttl
            return (True, (default_task_profile, allocated_ttl), None)

        try:
            # Infer TaskProfile using AdaptiveDepth
            task_profile = adaptive_depth.infer_task_profile(
                task_description=request,
                context=None,  # Can be extended with previous attempts, user preferences, etc.
            )

            # Allocate TTL based on TaskProfile
            allocated_ttl = adaptive_depth.allocate_ttl(
                task_profile=task_profile,
                global_ttl_limit=global_ttl,
            )

            return (True, (task_profile, allocated_ttl), None)
        except Exception as e:
            # If inference or allocation fails, return error result
            return (False, (None, global_ttl), str(e))

    def phase_b_initial_plan_refinement(
        self,
        request: str,
        plan: "Plan",
        task_profile: Any,  # TaskProfile
        recursive_planner: Optional[Any],  # RecursivePlanner
        semantic_validator: Optional[Any],  # SemanticValidator
        tool_registry: Optional[Any],  # ToolRegistry
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
    ) -> PhaseBResult:
        """
        Phase B: Initial Plan & Pre-Execution Refinement.

        Args:
            request: Natural language request
            plan: Initial plan
            task_profile: TaskProfile from Phase A
            recursive_planner: RecursivePlanner instance (may be None)
            semantic_validator: SemanticValidator instance (may be None)
            tool_registry: ToolRegistry instance (may be None)

        Returns:
            Tuple of (success, refined_plan, error_message)
        """
        refined_plan = plan

        try:
            # Use RecursivePlanner.generate_plan() if available to ensure proper structure
            if recursive_planner:
                try:
                    # Regenerate plan using RecursivePlanner to ensure step_index, total_steps, etc. are set
                    refined_plan = recursive_planner.generate_plan(
                        task_description=request,
                        task_profile=task_profile,
                        tool_registry=tool_registry,
                    )
                except Exception:
                    # If RecursivePlanner fails, fall back to existing plan
                    # Log error but continue with existing plan
                    pass

            # Phase B: Plan Validation - semantic validation
            if semantic_validator:
                try:
                    semantic_validation_report = semantic_validator.validate(
                        artifact=refined_plan.model_dump(),
                        artifact_type="plan",
                        tool_registry=tool_registry,
                    )
                    # If validation issues found, refine plan
                    if semantic_validation_report.issues and recursive_planner:
                        from aeon.orchestration.refinement import PlanRefinement

                        refinement_actions = recursive_planner.refine_plan(
                            current_plan=refined_plan,
                            validation_issues=semantic_validation_report.issues,
                            convergence_reason_codes=[],
                            blocked_steps=[],
                            executed_step_ids=set(),
                        )
                        # Apply refinement actions to plan
                        from aeon.orchestration.refinement import PlanRefinement

                        plan_refinement = PlanRefinement()
                        success, refined_plan, error = plan_refinement.apply_actions(
                            refined_plan, refinement_actions
                        )
                        if not success:
                            # If refinement application fails, continue with existing plan
                            refined_plan = plan
                except Exception:
                    # If semantic validation fails, continue with existing plan (best-effort advisory)
                    # Log error but don't fail phase
                    pass

            return (True, refined_plan, None)
        except Exception as e:
            # On failure, return original plan with error
            return (False, plan, str(e))

    def phase_c_execute_batch(
        self,
        plan: "Plan",
        state: "OrchestrationState",
        step_executor: Any,  # StepExecutor
        tool_registry: Optional[Any],  # ToolRegistry
        memory: Optional[Any],  # Memory
        supervisor: Optional[Any],  # Supervisor
        execute_step_fn: Any,  # Function to execute a step (kernel method)
    ) -> PhaseCExecuteResult:
        """
        Phase C: Execute batch of ready steps.

        Args:
            plan: Current plan
            state: Current orchestration state
            step_executor: StepExecutor instance
            tool_registry: ToolRegistry instance (may be None)
            memory: Memory interface
            supervisor: Supervisor instance (may be None)
            get_ready_steps_fn: Function to get ready steps (StepPreparation.get_ready_steps)
            execute_step_fn: Function to execute a step (kernel._execute_step)

        Returns:
            List of execution results (dicts with step_id, status, output, clarity_state)
        """
        from aeon.plan.models import StepStatus

        from aeon.orchestration.step_prep import StepPreparation

        step_prep = StepPreparation()
        execution_results = []
        ready_steps = step_prep.get_ready_steps(plan, memory)

        for step in ready_steps:
            try:
                # Execute step
                execute_step_fn(step, state)
                # Handle both enum and string values (use_enum_values=True converts to string)
                status_value = step.status.value if hasattr(step.status, 'value') else str(step.status)
                execution_results.append({
                    "step_id": step.step_id,
                    "status": status_value,
                    "output": getattr(step, "step_output", None),
                    "clarity_state": getattr(step, "clarity_state", None),
                })
                # Decrement TTL after step execution
                if state:
                    state.ttl_remaining -= 1
            except Exception as e:
                execution_results.append({
                    "step_id": step.step_id,
                    "status": StepStatus.FAILED.value,
                    "error": str(e),
                })

        return execution_results

    def phase_c_evaluate(
        self,
        plan: "Plan",
        execution_results: List[Dict[str, Any]],
        semantic_validator: Optional[Any],  # SemanticValidator
        convergence_engine: Optional[Any],  # ConvergenceEngine
        tool_registry: Optional[Any],  # ToolRegistry
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
    ) -> PhaseCEvaluateResult:
        """
        Phase C: Evaluate execution results (semantic validation + convergence).

        Args:
            plan: Current plan
            execution_results: Execution results from batch
            semantic_validator: SemanticValidator instance (may be None)
            convergence_engine: ConvergenceEngine instance (may be None)
            tool_registry: ToolRegistry instance (may be None)

        Returns:
            Evaluation results dict
        """
        from aeon.plan.models import StepStatus
        from aeon.validation.models import SemanticValidationReport
        from aeon.convergence.models import ConvergenceAssessment

        # Build execution results for validation and convergence assessment
        # (execution_results is already provided, but we need step status info)
        step_results = []
        for step in plan.steps:
            if step.status in (StepStatus.COMPLETE, StepStatus.FAILED, StepStatus.INVALID):
                # Handle both enum and string values (use_enum_values=True converts to string)
                status_value = step.status.value if hasattr(step.status, 'value') else str(step.status)
                step_results.append({
                    "step_id": step.step_id,
                    "status": status_value,
                    "output": getattr(step, "step_output", None),
                    "clarity_state": getattr(step, "clarity_state", None),
                })

        # Use provided execution_results if available, otherwise use step_results
        eval_results = execution_results if execution_results else step_results

        # 1. Call SemanticValidator.validate() for execution artifacts
        semantic_validation_report = None
        if semantic_validator:
            try:
                # Validate current plan state and execution artifacts
                execution_artifact = {
                    "plan": plan.model_dump(),
                    "execution_results": eval_results,
                }
                semantic_validation_report = semantic_validator.validate(
                    artifact=execution_artifact,
                    artifact_type="execution_artifact",
                    tool_registry=tool_registry,
                )
            except Exception:
                # If semantic validation fails, continue with empty report (best-effort advisory)
                semantic_validation_report = None

        # 2. Call ConvergenceEngine.assess() with validation report
        convergence_assessment = None
        if convergence_engine:
            try:
                # Create a default empty validation report if none exists
                if semantic_validation_report is None:
                    semantic_validation_report = SemanticValidationReport(
                        artifact_type="execution_artifact",
                        issues=[],
                    )

                convergence_assessment = convergence_engine.assess(
                    plan_state=plan.model_dump(),
                    execution_results=eval_results,
                    semantic_validation_report=semantic_validation_report,
                    execution_context=execution_context,
                    logger=logger,
                )
            except Exception as e:
                # If convergence assessment fails, create conservative assessment
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
            for step in plan.steps
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

        evaluation_result = {
            "converged": final_converged,
            "needs_refinement": needs_refinement and not auto_converged,  # Don't refine if auto-converged
            "semantic_validation": semantic_validation_report.model_dump() if semantic_validation_report else {},
            "convergence_assessment": convergence_assessment.model_dump() if convergence_assessment else {},
            "validation_issues": semantic_validation_report.issues if semantic_validation_report else [],
            "convergence_reason_codes": convergence_assessment.reason_codes if convergence_assessment else [],
        }
        
        # Log evaluation outcome (T025) - delegate to convergence engine
        if logger and execution_context and convergence_engine:
            # The convergence engine will log the evaluation outcome
            pass  # Logging is done in convergence engine.assess() method
        
        return evaluation_result

    def phase_c_refine(
        self,
        plan: "Plan",
        evaluation_results: Dict[str, Any],
        recursive_planner: Optional[Any],  # RecursivePlanner
        populate_step_indices_fn: Any,  # Function to populate step indices
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
    ) -> PhaseCRefineResult:
        """
        Phase C: Refine plan based on evaluation results.

        Args:
            plan: Current plan
            evaluation_results: Results from evaluation phase
            recursive_planner: RecursivePlanner instance (may be None)
            apply_refinement_actions_fn: Function to apply refinement actions
            populate_step_indices_fn: Function to populate step indices

        Returns:
            Tuple of (success, refinement_changes, error_message)
        """
        from aeon.plan.models import StepStatus

        if not recursive_planner:
            return (True, [], None)

        try:
            # Extract validation issues, convergence reason codes, and blocked steps
            validation_issues = evaluation_results.get("validation_issues", [])
            convergence_reason_codes = evaluation_results.get("convergence_reason_codes", [])
            blocked_steps = evaluation_results.get("blocked_steps", [])

            # Get executed step IDs (steps with status complete or failed)
            executed_step_ids = {
                step.step_id
                for step in plan.steps
                if step.status in (StepStatus.COMPLETE, StepStatus.FAILED)
            }

            # Generate refinement actions
            refinement_actions = recursive_planner.refine_plan(
                current_plan=plan,
                validation_issues=validation_issues,
                convergence_reason_codes=convergence_reason_codes,
                blocked_steps=blocked_steps,
                executed_step_ids=executed_step_ids,
            )

            # Create before_plan_fragment for logging (T024)
            before_plan_fragment = None
            if logger and execution_context and refinement_actions:
                from aeon.observability.models import PlanFragment
                # Get changed step IDs (will be determined after applying actions)
                changed_step_ids = set()
                unchanged_step_ids = {step.step_id for step in plan.steps}
                before_plan_fragment = PlanFragment(
                    changed_steps=[],
                    unchanged_step_ids=list(unchanged_step_ids),
                )

            # Apply refinement actions to plan
            if refinement_actions:
                from aeon.orchestration.refinement import PlanRefinement

                plan_refinement = PlanRefinement()
                success, updated_plan, error = plan_refinement.apply_actions(
                    plan, refinement_actions, execution_context, logger
                )
                if success:
                    plan = updated_plan
                    # Re-populate step indices after refinement
                    from aeon.orchestration.step_prep import StepPreparation

                    step_prep = StepPreparation()
                    step_prep.populate_step_indices(plan)
                else:
                    # If refinement application fails, continue without refinement
                    return (True, [], None)

            # Convert refinement actions to dict format for logging
            refinement_changes = [action.model_dump() for action in refinement_actions]
            
            # Log refinement outcome (T024)
            if logger and execution_context and refinement_actions and before_plan_fragment:
                from aeon.observability.models import PlanFragment
                # Create after_plan_fragment with changed steps
                changed_steps = []
                unchanged_step_ids_after = set()
                for step in plan.steps:
                    # Check if this step was modified/added by comparing with original plan
                    original_step = next((s for s in before_plan_fragment.unchanged_step_ids if s == step.step_id), None)
                    if original_step is None or step.step_id not in before_plan_fragment.unchanged_step_ids:
                        changed_steps.append(step)
                    else:
                        unchanged_step_ids_after.add(step.step_id)
                
                after_plan_fragment = PlanFragment(
                    changed_steps=changed_steps,
                    unchanged_step_ids=list(unchanged_step_ids_after),
                )
                
                # Build evaluation_signals from evaluation_results (T065, T066, T067)
                from aeon.observability.models import ConvergenceAssessmentSummary, ValidationIssuesSummary
                
                # Extract convergence assessment and create summary
                convergence_assessment_dict = evaluation_results.get("convergence_assessment", {})
                convergence_assessment_summary = None
                if convergence_assessment_dict:
                    try:
                        convergence_assessment_summary = ConvergenceAssessmentSummary(
                            converged=convergence_assessment_dict.get("converged", False),
                            reason_codes=convergence_assessment_dict.get("reason_codes", []),
                            scores=convergence_assessment_dict.get("scores") or {
                                "completeness": convergence_assessment_dict.get("completeness_score", 0.0),
                                "coherence": convergence_assessment_dict.get("coherence_score", 0.0),
                            },
                            pass_number=0,  # Pass number should come from caller if available
                        )
                    except Exception:
                        pass
                
                # Extract validation issues and create summary
                validation_issues = evaluation_results.get("validation_issues", [])
                validation_issues_summary = None
                if validation_issues:
                    try:
                        critical_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "CRITICAL" or (hasattr(i, "severity") and i.severity == "CRITICAL"))
                        error_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "ERROR" or (hasattr(i, "severity") and i.severity == "ERROR"))
                        warning_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "WARNING" or (hasattr(i, "severity") and i.severity == "WARNING"))
                        info_count = sum(1 for i in validation_issues if isinstance(i, dict) and i.get("severity") == "INFO" or (hasattr(i, "severity") and i.severity == "INFO"))
                        validation_issues_summary = ValidationIssuesSummary(
                            total_issues=len(validation_issues),
                            critical_count=critical_count,
                            error_count=error_count,
                            warning_count=warning_count,
                            info_count=info_count,
                            issues_by_type=None,
                        )
                    except Exception:
                        pass
                
                # Build evaluation_signals dict for backward compatibility
                evaluation_signals = {}
                if convergence_assessment_summary:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()
                
                # Log refinement trigger (T068) - log what triggered refinement
                if logger and execution_context:
                    trigger_reason = []
                    if convergence_assessment_dict and not convergence_assessment_dict.get("converged", True):
                        trigger_reason.append("convergence_not_achieved")
                    if validation_issues:
                        trigger_reason.append("validation_issues_detected")
                    if not trigger_reason:
                        trigger_reason.append("manual_refinement")
                    
                    # Log refinement trigger as part of refinement outcome
                    # The evaluation_signals already contains the trigger context
                
                # Log refinement actions (T069) - which steps were modified/added/removed
                # refinement_actions already contains this information in refinement_changes
                
                logger.log_refinement_outcome(
                    correlation_id=execution_context.correlation_id,
                    before_plan_fragment=before_plan_fragment,
                    after_plan_fragment=after_plan_fragment,
                    refinement_actions=refinement_changes,
                    evaluation_signals=evaluation_signals if evaluation_signals else None,
                    convergence_assessment_summary=convergence_assessment_summary,
                    validation_issues_summary=validation_issues_summary,
                    pass_number=None,  # Pass number should come from caller if available
                )
            
            return (True, refinement_changes, None)

        except Exception as e:
            # If refinement fails, log error and continue without refinement
            return (False, [], str(e))

    def phase_d_adaptive_depth(
        self,
        task_profile: Any,  # TaskProfile
        evaluation_results: Dict[str, Any],
        plan: "Plan",
        adaptive_depth: Optional[Any],  # AdaptiveDepth
        state: "OrchestrationState",
        global_ttl: int,
        execution_passes: List["ExecutionPass"],
    ) -> PhaseDResult:
        """
        Phase D: Adaptive Depth - update TaskProfile at pass boundaries.

        Args:
            task_profile: Current TaskProfile
            evaluation_results: Results from evaluation phase
            plan: Current plan
            adaptive_depth: AdaptiveDepth instance (may be None)
            state: Current orchestration state
            global_ttl: Global TTL limit
            execution_passes: Execution passes list

        Returns:
            Tuple of (success, updated_task_profile, error_message)
        """
        if not adaptive_depth or not task_profile:
            return (True, None, None)

        try:
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
            if plan:
                for step in plan.steps:
                    clarity_state = getattr(step, "clarity_state", None)
                    if clarity_state:
                        clarity_states.append(clarity_state)

            # Call AdaptiveDepth.update_task_profile()
            updated_profile = adaptive_depth.update_task_profile(
                current_profile=task_profile,
                convergence_assessment=convergence_assessment,
                semantic_validation_report=semantic_validation_report,
                clarity_states=clarity_states,
            )

            if updated_profile:
                # Adjust TTL bidirectionally based on profile update
                old_ttl = state.ttl_remaining if state else global_ttl
                adjusted_ttl, adjustment_reason = adaptive_depth.adjust_ttl_for_updated_profile(
                    old_profile=task_profile,
                    new_profile=updated_profile,
                    current_ttl=old_ttl,
                    global_ttl_limit=global_ttl,
                )

                # Update state TTL
                if state:
                    state.ttl_remaining = adjusted_ttl

                # Record adjustment_reason in execution metadata
                # Store in the current execution pass
                if execution_passes:
                    current_pass = execution_passes[-1]
                    if "adaptive_depth_adjustment" not in current_pass.evaluation_results:
                        current_pass.evaluation_results["adaptive_depth_adjustment"] = {}
                    current_pass.evaluation_results["adaptive_depth_adjustment"] = {
                        "profile_version_old": task_profile.profile_version,
                        "profile_version_new": updated_profile.profile_version,
                        "adjustment_reason": adjustment_reason,
                        "ttl_old": old_ttl,
                        "ttl_new": adjusted_ttl,
                    }

                return (True, updated_profile, None)

            return (True, None, None)
        except Exception as e:
            # If update fails, return error
            return (False, None, str(e))
