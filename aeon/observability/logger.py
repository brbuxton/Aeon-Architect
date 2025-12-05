"""JSONL logger for orchestration cycles."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from aeon.observability.models import (
    ConvergenceAssessmentSummary,
    ErrorRecord,
    ExecutionMetrics,
    LogEntry,
    PlanFragment,
    StateSlice,
    ValidationIssuesSummary,
)


class JSONLLogger:
    """JSONL logger for orchestration cycle logging."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        """
        Initialize JSONL logger.

        Args:
            file_path: Path to JSONL log file (optional, defaults to None for no-op logger)
        """
        self.file_path = file_path

    def log_entry(self, entry: LogEntry) -> None:
        """
        Write a log entry to the JSONL file.

        Args:
            entry: LogEntry to write

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Append mode - creates file if it doesn't exist
            with open(self.file_path, 'a', encoding='utf-8') as f:
                json_str = entry.model_dump_json()
                f.write(json_str + '\n')
        except Exception:
            # Non-blocking: silently fail on write errors
            pass

    def format_entry(
        self,
        step_number: int,
        plan_state: dict,
        llm_output: dict,
        supervisor_actions: list = None,
        tool_calls: list = None,
        ttl_remaining: int = 0,
        errors: list = None,
        pass_number: Optional[int] = None,
        phase: Optional[str] = None,
    ) -> LogEntry:
        """
        Format a log entry from orchestration cycle data.

        Args:
            step_number: Sequential cycle identifier
            plan_state: Snapshot of plan at cycle start
            llm_output: Raw LLM response
            supervisor_actions: Supervisor repairs in this cycle (optional)
            tool_calls: Tool invocations in this cycle (optional)
            ttl_remaining: Cycles left before expiration
            errors: Errors in this cycle (optional)
            pass_number: Pass number in multi-pass execution (optional, for Sprint 2)
            phase: Current phase in multi-pass execution (optional, for Sprint 2)

        Returns:
            Formatted LogEntry
        """
        return LogEntry(
            step_number=step_number,
            plan_state=plan_state,
            llm_output=llm_output,
            supervisor_actions=supervisor_actions or [],
            tool_calls=tool_calls or [],
            ttl_remaining=ttl_remaining,
            errors=errors or [],
            timestamp=datetime.now().isoformat(),
            pass_number=pass_number,
            phase=phase,
        )

    def log_multipass_entry(
        self,
        pass_number: int,
        phase: str,
        plan_state: dict,
        execution_results: list = None,
        evaluation_results: dict = None,
        refinement_changes: list = None,
        ttl_remaining: int = 0,
        errors: list = None,
    ) -> None:
        """
        Log a multi-pass execution entry (Sprint 2).

        Args:
            pass_number: Pass number in multi-pass execution
            phase: Current phase (A, B, C, D)
            plan_state: Snapshot of plan at pass start
            execution_results: Step outputs and tool results (optional)
            evaluation_results: Convergence assessment and semantic validation (optional)
            refinement_changes: Plan/step modifications (optional)
            ttl_remaining: TTL cycles remaining
            errors: Errors in this pass (optional)
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = {
                "type": "multipass_entry",
                "pass_number": pass_number,
                "phase": phase,
                "plan_state": plan_state,
                "execution_results": execution_results or [],
                "evaluation_results": evaluation_results or {},
                "refinement_changes": refinement_changes or [],
                "ttl_remaining": ttl_remaining,
                "errors": errors or [],
                "timestamp": datetime.now().isoformat(),
            }
            with open(self.file_path, 'a', encoding='utf-8') as f:
                json_str = json.dumps(entry, default=str)
                f.write(json_str + '\n')
        except Exception:
            # Non-blocking: silently fail on write errors
            pass

    def log_phase_entry(
        self,
        phase: Literal["A", "B", "C", "D"],
        correlation_id: str,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a phase entry event.

        Args:
            phase: Current phase (A, B, C, D)
            correlation_id: Correlation ID linking events for a single execution
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = LogEntry(
                event="phase_entry",
                correlation_id=correlation_id,
                phase=phase,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_phase_exit(
        self,
        phase: Literal["A", "B", "C", "D"],
        correlation_id: str,
        duration: float,
        outcome: Literal["success", "failure"],
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a phase exit event.

        Args:
            phase: Current phase (A, B, C, D)
            correlation_id: Correlation ID linking events for a single execution
            duration: Duration in seconds
            outcome: Outcome (success, failure)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = LogEntry(
                event="phase_exit",
                correlation_id=correlation_id,
                phase=phase,
                duration=duration,
                outcome=outcome,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_state_transition(
        self,
        correlation_id: str,
        component: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        transition_reason: str,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a state transition event.

        Args:
            correlation_id: Correlation ID linking events for a single execution
            component: Component name (e.g., "plan", "execution", "refinement")
            before_state: State snapshot before transition (dict or StateSlice model_dump())
            after_state: State snapshot after transition (dict or StateSlice model_dump())
            transition_reason: Reason for state transition
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = LogEntry(
                event="state_transition",
                correlation_id=correlation_id,
                component=component,
                before_state=before_state,
                after_state=after_state,
                transition_reason=transition_reason,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_refinement_outcome(
        self,
        correlation_id: str,
        before_plan_fragment: PlanFragment,
        after_plan_fragment: PlanFragment,
        refinement_actions: List[Dict[str, Any]],
        evaluation_signals: Optional[Dict[str, Any]] = None,
        convergence_assessment_summary: Optional[ConvergenceAssessmentSummary] = None,
        validation_issues_summary: Optional[ValidationIssuesSummary] = None,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a refinement outcome event.

        Args:
            correlation_id: Correlation ID linking events for a single execution
            before_plan_fragment: Plan fragment before refinement
            after_plan_fragment: Plan fragment after refinement
            refinement_actions: Refinement actions applied
            evaluation_signals: Evaluation signals summary (optional, for backward compatibility)
            convergence_assessment_summary: Convergence assessment summary (optional, T066)
            validation_issues_summary: Validation issues summary (optional, T067)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
            If evaluation_signals is provided, it takes precedence. Otherwise, summaries are used.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Build evaluation_signals from summaries if not provided (T065, T066, T067)
            if evaluation_signals is None:
                evaluation_signals = {}
                if convergence_assessment_summary:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()
            else:
                # Ensure evaluation_signals has proper structure (T065)
                # If it's a dict with convergence_assessment/validation_issues keys, use as-is
                # Otherwise, try to extract from summaries
                if convergence_assessment_summary and "convergence_assessment" not in evaluation_signals:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary and "validation_issues" not in evaluation_signals:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()

            entry = LogEntry(
                event="refinement_outcome",
                correlation_id=correlation_id,
                before_plan_fragment=before_plan_fragment.model_dump() if isinstance(before_plan_fragment, PlanFragment) else before_plan_fragment,
                after_plan_fragment=after_plan_fragment.model_dump() if isinstance(after_plan_fragment, PlanFragment) else after_plan_fragment,
                refinement_actions=refinement_actions,
                evaluation_signals=evaluation_signals if evaluation_signals else None,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_evaluation_outcome(
        self,
        correlation_id: str,
        convergence_assessment: Optional[Dict[str, Any]] = None,
        validation_report: Optional[Dict[str, Any]] = None,
        evaluation_signals: Optional[Dict[str, Any]] = None,
        convergence_assessment_summary: Optional[ConvergenceAssessmentSummary] = None,
        validation_issues_summary: Optional[ValidationIssuesSummary] = None,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log an evaluation outcome event (T074).

        Args:
            correlation_id: Correlation ID linking events for a single execution
            convergence_assessment: Convergence assessment summary dict (optional, for backward compatibility)
            validation_report: Validation report summary dict (optional, for backward compatibility)
            evaluation_signals: Evaluation signals summary dict (optional, for backward compatibility)
            convergence_assessment_summary: Convergence assessment summary model (optional, T074)
            validation_issues_summary: Validation issues summary model (optional, T074)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
            If summaries are provided, they take precedence over dict versions.
            Reason codes from convergence_assessment_summary explain why convergence was not achieved (T076).
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Use summary models if provided, otherwise use dicts (T074)
            if convergence_assessment_summary:
                convergence_assessment = convergence_assessment_summary.model_dump()
            if validation_issues_summary:
                validation_report = validation_issues_summary.model_dump()
            
            # Build evaluation_signals from summaries if not provided (T074)
            if evaluation_signals is None:
                evaluation_signals = {}
                if convergence_assessment_summary:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()
            else:
                # Ensure evaluation_signals has proper structure
                if convergence_assessment_summary and "convergence_assessment" not in evaluation_signals:
                    evaluation_signals["convergence_assessment"] = convergence_assessment_summary.model_dump()
                if validation_issues_summary and "validation_issues" not in evaluation_signals:
                    evaluation_signals["validation_issues"] = validation_issues_summary.model_dump()

            entry = LogEntry(
                event="evaluation_outcome",
                correlation_id=correlation_id,
                convergence_assessment=convergence_assessment,
                validation_report=validation_report,
                evaluation_signals=evaluation_signals if evaluation_signals else None,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_error(
        self,
        correlation_id: str,
        error: ErrorRecord,
        step_id: Optional[str] = None,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
        # Refinement error context
        before_plan_fragment: Optional[Dict[str, Any]] = None,
        after_plan_fragment: Optional[Dict[str, Any]] = None,
        evaluation_signals: Optional[Dict[str, Any]] = None,
        # Execution error context
        attempted_action: Optional[str] = None,
        tool_name: Optional[str] = None,
        error_context: Optional[Dict[str, Any]] = None,
        # Validation error context
        validation_type: Optional[str] = None,
        validation_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an error event with structured error record.

        Args:
            correlation_id: Correlation ID linking events for a single execution
            error: ErrorRecord with error code, severity, message, and context
            step_id: Step ID where error occurred (optional, for execution errors)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)
            before_plan_fragment: Plan fragment before refinement (optional, for refinement errors)
            after_plan_fragment: Plan fragment after refinement (optional, for refinement errors)
            evaluation_signals: Evaluation signals summary (optional, for refinement errors)
            attempted_action: Action that was attempted (optional, for execution errors)
            tool_name: Tool name that failed (optional, for execution errors)
            error_context: Additional error context (optional, for execution errors)
            validation_type: Type of validation that failed (optional, for validation errors)
            validation_details: Validation details (optional, for validation errors)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Enhance error context based on error type
            enhanced_context = error.context.copy() if error.context else {}
            
            if step_id:
                enhanced_context["step_id"] = step_id
            if attempted_action:
                enhanced_context["attempted_action"] = attempted_action
            if tool_name:
                enhanced_context["tool_name"] = tool_name
            if error_context:
                enhanced_context.update(error_context)
            if validation_type:
                enhanced_context["validation_type"] = validation_type
            if validation_details:
                enhanced_context["validation_details"] = validation_details

            # Create enhanced error record with context
            enhanced_error = ErrorRecord(
                code=error.code,
                severity=error.severity,
                message=error.message,
                affected_component=error.affected_component,
                context=enhanced_context if enhanced_context else None,
                stack_trace=error.stack_trace,
            )

            entry = LogEntry(
                event="error",
                correlation_id=correlation_id,
                original_error=enhanced_error.model_dump(),
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
                # Include refinement-specific fields
                before_plan_fragment=before_plan_fragment,
                after_plan_fragment=after_plan_fragment,
                evaluation_signals=evaluation_signals,
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_error_recovery(
        self,
        correlation_id: str,
        original_error: ErrorRecord,
        recovery_action: str,
        recovery_outcome: Literal["success", "failure"],
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log an error recovery attempt event.

        Args:
            correlation_id: Correlation ID linking events for a single execution
            original_error: Original error that triggered recovery
            recovery_action: Recovery action attempted
            recovery_outcome: Outcome of recovery attempt (success, failure)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = LogEntry(
                event="error_recovery",
                correlation_id=correlation_id,
                original_error=original_error.model_dump(),
                recovery_action=recovery_action,
                recovery_outcome=recovery_outcome,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_step_execution_outcome(
        self,
        correlation_id: str,
        step_id: str,
        execution_mode: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a step execution outcome event (T070).

        Args:
            correlation_id: Correlation ID linking events for a single execution
            step_id: Step ID that was executed
            execution_mode: Execution mode (tool, llm, fallback)
            success: Whether execution succeeded
            result: Execution result (optional)
            error: Error message if execution failed (optional)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Use state_transition event type for step execution outcomes
            entry = LogEntry(
                event="state_transition",
                correlation_id=correlation_id,
                component="execution",
                before_state={"step_id": step_id, "execution_mode": execution_mode},
                after_state={
                    "step_id": step_id,
                    "execution_mode": execution_mode,
                    "success": success,
                    "result": result,
                    "error": error,
                },
                transition_reason=f"step_execution_{'success' if success else 'failure'}",
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_tool_invocation_result(
        self,
        correlation_id: str,
        step_id: str,
        tool_name: str,
        success: bool,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a tool invocation result event (T071).

        Args:
            correlation_id: Correlation ID linking events for a single execution
            step_id: Step ID where tool was invoked
            tool_name: Name of the tool that was invoked
            success: Whether tool invocation succeeded
            result: Tool invocation result (optional)
            error: Error message if invocation failed (optional)
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            # Use state_transition event type for tool invocation results
            entry = LogEntry(
                event="state_transition",
                correlation_id=correlation_id,
                component="execution",
                before_state={"step_id": step_id, "tool_name": tool_name},
                after_state={
                    "step_id": step_id,
                    "tool_name": tool_name,
                    "success": success,
                    "result": result,
                    "error": error,
                },
                transition_reason=f"tool_invocation_{'success' if success else 'failure'}",
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

    def log_step_status_change(
        self,
        correlation_id: str,
        step_id: str,
        old_status: str,
        new_status: str,
        reason: str,
        pass_number: Optional[int] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Log a step status change event (T072).

        Args:
            correlation_id: Correlation ID linking events for a single execution
            step_id: Step ID whose status changed
            old_status: Previous status
            new_status: New status
            reason: Reason for status change
            pass_number: Pass number in multi-pass execution (optional)
            timestamp: ISO 8601 timestamp (optional, defaults to now)

        Note:
            This method is non-blocking and will silently fail if file write fails.
        """
        if not self.file_path:
            return  # No-op if no file path provided

        try:
            entry = LogEntry(
                event="state_transition",
                correlation_id=correlation_id,
                component="execution",
                before_state={"step_id": step_id, "status": old_status},
                after_state={"step_id": step_id, "status": new_status},
                transition_reason=reason,
                pass_number=pass_number,
                timestamp=timestamp or datetime.now().isoformat(),
            )
            self.log_entry(entry)
        except Exception:
            # Non-blocking: silently fail on errors
            pass

