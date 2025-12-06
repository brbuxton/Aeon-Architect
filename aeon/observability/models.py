"""Observability data models."""

import re
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aeon.plan.models import PlanStep


class CorrelationID(BaseModel):
    """A unique identifier that links all log entries for a single execution cycle."""

    value: str = Field(..., description="UUIDv5 string representation of the correlation ID")

    @field_validator("value")
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Validate that value is a valid UUID format."""
        # UUID format: 8-4-4-4-12 hex digits
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        # Also allow fallback format: aeon-timestamp-hash
        fallback_pattern = r"^aeon-\d{4}-\d{2}-\d{2}T[\d:\.]+-[0-9a-f]{8}$"
        if not (re.match(uuid_pattern, v, re.IGNORECASE) or re.match(fallback_pattern, v)):
            raise ValueError("Correlation ID must be a valid UUID or fallback format")
        return v

    model_config = ConfigDict(frozen=True)


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ErrorRecord(BaseModel):
    """A structured error record containing error code, severity level, message, and context."""

    code: str = Field(..., description="Error code in format 'AEON.<COMPONENT>.<CODE>'")
    severity: ErrorSeverity = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable error message")
    affected_component: str = Field(..., description="Component where error occurred")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context for diagnosis"
    )
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")

    @field_validator("code")
    @classmethod
    def validate_error_code_format(cls, v: str) -> str:
        """Validate that error code matches AEON.<COMPONENT>.<CODE> format."""
        pattern = r"^AEON\.(REFINEMENT|EXECUTION|VALIDATION|PHASE|PLAN|TOOL|MEMORY|LLM|SUPERVISOR)\.\d{3}$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Error code must match pattern AEON.<COMPONENT>.<CODE>, got '{v}'"
            )
        return v

    @field_validator("message", "affected_component")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    model_config = ConfigDict(frozen=True)


class PlanFragment(BaseModel):
    """A plan fragment containing only changed steps with step IDs."""

    changed_steps: List[PlanStep] = Field(
        ..., description="Steps that were modified, added, or removed (full step data)"
    )
    unchanged_step_ids: List[str] = Field(
        ..., description="Step IDs of unchanged steps (ID only, no full data)"
    )

    @field_validator("unchanged_step_ids")
    @classmethod
    def validate_no_overlap(cls, v: List[str], info) -> List[str]:
        """Validate that step IDs in changed_steps and unchanged_step_ids don't overlap."""
        if "changed_steps" in info.data:
            changed_ids = {step.step_id for step in info.data["changed_steps"]}
            unchanged_ids = set(v)
            overlap = changed_ids & unchanged_ids
            if overlap:
                raise ValueError(
                    f"Step IDs in changed_steps and unchanged_step_ids must not overlap, "
                    f"found overlap: {overlap}"
                )
        return v

    model_config = ConfigDict(frozen=True)


class ConvergenceAssessmentSummary(BaseModel):
    """A summary of convergence assessment results."""

    converged: bool = Field(..., description="Whether convergence was achieved")
    reason_codes: List[str] = Field(
        ..., min_length=1, description="Reason codes explaining convergence decision"
    )
    scores: Optional[Dict[str, float]] = Field(
        default=None, description="Convergence scores (completeness, coherence, consistency)"
    )
    pass_number: int = Field(..., ge=0, description="Pass number when assessment was made")

    @field_validator("reason_codes")
    @classmethod
    def validate_non_empty(cls, v: List[str]) -> List[str]:
        """Validate that reason_codes is non-empty."""
        if not v:
            raise ValueError("reason_codes must be non-empty")
        return v

    model_config = ConfigDict(frozen=True)


class ValidationIssuesSummary(BaseModel):
    """A summary of validation issues containing issue counts by severity level."""

    total_issues: int = Field(..., ge=0, description="Total number of validation issues")
    critical_count: int = Field(..., ge=0, description="Number of critical issues")
    error_count: int = Field(..., ge=0, description="Number of error-level issues")
    warning_count: int = Field(..., ge=0, description="Number of warning-level issues")
    info_count: int = Field(..., ge=0, description="Number of info-level issues")
    issues_by_type: Optional[Dict[str, int]] = Field(
        default=None, description="Issues grouped by type"
    )

    @model_validator(mode="after")
    def validate_total_matches_sum(self) -> "ValidationIssuesSummary":
        """Validate that total_issues equals sum of severity counts."""
        expected_total = (
            self.critical_count + self.error_count + self.warning_count + self.info_count
        )
        if self.total_issues != expected_total:
            raise ValueError(
                f"total_issues ({self.total_issues}) must equal sum of severity counts ({expected_total})"
            )
        return self

    model_config = ConfigDict(frozen=True)


class StateSlice(BaseModel):
    """Base class for minimal structured state slices."""

    component: str = Field(..., description="Component name (e.g., 'plan', 'execution', 'refinement')")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the state snapshot")

    @field_validator("component")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that component is non-empty."""
        if not v or not v.strip():
            raise ValueError("Component cannot be empty")
        return v.strip()

    model_config = ConfigDict(frozen=True)


class PlanStateSlice(StateSlice):
    """State slice for plan component."""

    plan_id: Optional[str] = Field(default=None, description="Plan identifier")
    current_step_id: Optional[str] = Field(default=None, description="Currently executing step ID")
    step_count: int = Field(..., ge=0, description="Total number of steps")
    steps_status_summary: Dict[str, int] = Field(
        ..., description="Summary of step statuses (e.g., {'pending': 2, 'running': 1, 'complete': 3})"
    )

    def __init__(self, **data):
        """Initialize PlanStateSlice with component='plan'."""
        if "component" not in data:
            data["component"] = "plan"
        super().__init__(**data)


class ExecutionStateSlice(StateSlice):
    """State slice for execution component."""

    current_step_id: Optional[str] = Field(default=None, description="Currently executing step ID")
    step_status: Literal["pending", "running", "complete", "failed"] = Field(
        ..., description="Current step status"
    )
    tool_calls_count: int = Field(..., ge=0, description="Number of tool calls made")
    errors_count: int = Field(..., ge=0, description="Number of errors encountered")

    def __init__(self, **data):
        """Initialize ExecutionStateSlice with component='execution'."""
        if "component" not in data:
            data["component"] = "execution"
        super().__init__(**data)


class RefinementStateSlice(StateSlice):
    """State slice for refinement component."""

    refinement_type: str = Field(..., description="Type of refinement (add_step, modify_step, remove_step)")
    changed_steps_count: int = Field(..., ge=0, description="Number of changed steps")
    added_steps_count: int = Field(..., ge=0, description="Number of added steps")
    removed_steps_count: int = Field(..., ge=0, description="Number of removed steps")

    def __init__(self, **data):
        """Initialize RefinementStateSlice with component='refinement'."""
        if "component" not in data:
            data["component"] = "refinement"
        super().__init__(**data)


class LogEntry(BaseModel):
    """A JSONL record of an orchestration event (extended with phase-aware fields)."""

    # Legacy cycle event fields (for backward compatibility)
    step_number: Optional[int] = Field(None, ge=1, description="Sequential cycle identifier (for cycle events)")
    plan_state: Optional[Dict[str, Any]] = Field(None, description="Snapshot of plan at cycle start (for cycle events)")
    llm_output: Optional[Dict[str, Any]] = Field(None, description="Raw LLM response (for cycle events)")
    supervisor_actions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Supervisor repairs in this cycle (for cycle events)"
    )
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool invocations in this cycle (for cycle events)"
    )
    ttl_remaining: Optional[int] = Field(None, ge=0, description="Cycles left before expiration (for cycle events)")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Errors in this cycle (for cycle events)"
    )
    
    # Phase-aware logging fields
    event: Literal[
        "phase_entry",
        "phase_exit",
        "state_transition",
        "state_snapshot",
        "ttl_snapshot",
        "phase_transition_error",
        "refinement_outcome",
        "evaluation_outcome",
        "error",
        "error_recovery",
        "step_execution_outcome",
        "tool_invocation_result",
        "cycle",
    ] = Field(default="cycle", description="Event type")
    correlation_id: Optional[str] = Field(None, description="Correlation ID linking events for a single execution")
    phase: Optional[Literal["A", "B", "C", "D"]] = Field(None, description="Current phase (required for phase events)")
    pass_number: Optional[int] = Field(None, ge=0, description="Pass number in multi-pass execution")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the event")
    
    @field_validator("pass_number", mode="before")
    @classmethod
    def normalize_pass_number(cls, v: Optional[int]) -> int:
        """
        Normalize pass_number to ensure it's always a valid integer >= 0.
        
        Defaults to 0 if None or missing. This ensures all log entries used
        for TTL/phase reasoning have a valid pass_number.
        """
        if v is None:
            return 0
        return max(0, int(v))
    
    # Phase exit fields
    duration: Optional[float] = Field(None, ge=0.0, description="Duration in seconds (for phase_exit events)")
    outcome: Optional[Literal["success", "failure"]] = Field(None, description="Outcome (for phase_exit events)")
    
    # State transition fields
    component: Optional[str] = Field(None, description="Component name (for state_transition events)")
    before_state: Optional[Dict[str, Any]] = Field(None, description="State snapshot before transition (for state_transition events)")
    after_state: Optional[Dict[str, Any]] = Field(None, description="State snapshot after transition (for state_transition events)")
    transition_reason: Optional[str] = Field(None, description="Reason for state transition (for state_transition events)")
    
    # Refinement outcome fields
    evaluation_signals: Optional[Dict[str, Any]] = Field(None, description="Evaluation signals summary (for refinement_outcome, evaluation_outcome events)")
    refinement_actions: Optional[List[Dict[str, Any]]] = Field(None, description="Refinement actions applied (for refinement_outcome events)")
    before_plan_fragment: Optional[Dict[str, Any]] = Field(None, description="Plan fragment before refinement (for refinement_outcome events)")
    after_plan_fragment: Optional[Dict[str, Any]] = Field(None, description="Plan fragment after refinement (for refinement_outcome events)")
    
    # Evaluation outcome fields
    convergence_assessment: Optional[Dict[str, Any]] = Field(None, description="Convergence assessment summary (for evaluation_outcome events)")
    validation_report: Optional[Dict[str, Any]] = Field(None, description="Validation report summary (for evaluation_outcome events)")
    
    # Error recovery fields
    original_error: Optional[Dict[str, Any]] = Field(None, description="Original error (for error_recovery events)")
    recovery_action: Optional[str] = Field(None, description="Recovery action attempted (for error_recovery events)")
    recovery_outcome: Optional[Literal["success", "failure"]] = Field(None, description="Recovery outcome (for error_recovery events)")

    model_config = ConfigDict(
        frozen=False,  # Allow updates during cycle
    )


class ExecutionMetrics(BaseModel):
    """Observability metrics for multi-pass execution."""

    execution_id: str = Field(..., description="Unique identifier for execution")
    total_passes: int = Field(..., ge=0, description="Total number of execution passes")
    total_refinements: int = Field(..., ge=0, description="Total number of plan refinements")
    convergence_achieved: bool = Field(..., description="Whether convergence was achieved")
    convergence_rate: float = Field(..., ge=0.0, le=1.0, description="Convergence rate (1.0 if converged, 0.0 if TTL expired)")
    average_pass_duration: float = Field(..., ge=0.0, description="Average duration per pass in seconds")
    total_execution_time: float = Field(..., ge=0.0, description="Total execution time in seconds")
    refinement_rate: float = Field(..., ge=0.0, description="Average refinements per pass")
    phase_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Number of passes per phase (A, B, C, D)"
    )
    ttl_utilization: float = Field(..., ge=0.0, le=1.0, description="TTL utilization (used_ttl / allocated_ttl)")
    semantic_validation_issues: int = Field(..., ge=0, description="Total semantic validation issues detected")
    convergence_scores: Dict[str, float] = Field(
        default_factory=dict, description="Convergence scores (completeness, coherence, consistency)"
    )

    model_config = ConfigDict(
        frozen=True,  # Metrics are immutable once created
    )

    @classmethod
    def from_execution_history(
        cls,
        execution_id: str,
        total_passes: int,
        total_refinements: int,
        convergence_achieved: bool,
        total_execution_time: float,
        passes: list,
        allocated_ttl: int,
        used_ttl: int,
        convergence_scores: Optional[Dict[str, float]] = None,
    ) -> "ExecutionMetrics":
        """
        Create ExecutionMetrics from execution history data.

        Args:
            execution_id: Unique identifier for execution
            total_passes: Total number of execution passes
            total_refinements: Total number of plan refinements
            convergence_achieved: Whether convergence was achieved
            total_execution_time: Total execution time in seconds
            passes: List of ExecutionPass objects
            allocated_ttl: TTL allocated at start
            used_ttl: TTL used during execution
            convergence_scores: Optional convergence scores dict

        Returns:
            ExecutionMetrics instance
        """
        # Calculate average pass duration
        durations = [
            p.timing_information.get("duration", 0.0)
            for p in passes
            if p.timing_information.get("duration") is not None
        ]
        average_pass_duration = sum(durations) / len(durations) if durations else 0.0

        # Calculate refinement rate
        refinement_rate = total_refinements / total_passes if total_passes > 0 else 0.0

        # Calculate phase distribution
        phase_distribution: Dict[str, int] = {}
        for p in passes:
            phase = p.phase
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1

        # Calculate TTL utilization
        ttl_utilization = used_ttl / allocated_ttl if allocated_ttl > 0 else 0.0

        # Count semantic validation issues
        semantic_validation_issues = 0
        for p in passes:
            if "validation" in p.evaluation_results:
                val_report = p.evaluation_results["validation"]
                if hasattr(val_report, "issues"):
                    semantic_validation_issues += len(val_report.issues)
                elif isinstance(val_report, dict) and "issues" in val_report:
                    semantic_validation_issues += len(val_report["issues"])

        # Convergence rate
        convergence_rate = 1.0 if convergence_achieved else 0.0

        return cls(
            execution_id=execution_id,
            total_passes=total_passes,
            total_refinements=total_refinements,
            convergence_achieved=convergence_achieved,
            convergence_rate=convergence_rate,
            average_pass_duration=average_pass_duration,
            total_execution_time=total_execution_time,
            refinement_rate=refinement_rate,
            phase_distribution=phase_distribution,
            ttl_utilization=ttl_utilization,
            semantic_validation_issues=semantic_validation_issues,
            convergence_scores=convergence_scores or {},
        )



