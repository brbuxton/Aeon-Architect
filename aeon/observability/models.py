"""Observability data models."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class LogEntry(BaseModel):
    """A JSONL record of a single orchestration cycle."""

    step_number: int = Field(..., ge=1, description="Sequential cycle identifier")
    plan_state: Dict[str, Any] = Field(..., description="Snapshot of plan at cycle start")
    llm_output: Dict[str, Any] = Field(..., description="Raw LLM response")
    supervisor_actions: List[Dict[str, Any]] = Field(
        default_factory=list, description="Supervisor repairs in this cycle (empty if none)"
    )
    tool_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Tool invocations in this cycle (empty if none)"
    )
    ttl_remaining: int = Field(..., ge=0, description="Cycles left before expiration")
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="Errors in this cycle (empty if none)"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of the cycle")
    # Multi-pass execution fields (Sprint 2)
    pass_number: Optional[int] = Field(None, ge=0, description="Pass number in multi-pass execution (None for single-pass)")
    phase: Optional[Literal["A", "B", "C", "D"]] = Field(None, description="Current phase in multi-pass execution (None for single-pass)")

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



