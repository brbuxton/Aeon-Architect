"""Orchestration state management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.memory.interface import Memory


@dataclass
class ExecutionContext:
    """
    Execution context containing only correlation ID and execution start timestamp.
    
    This class MUST contain no orchestration or control-flow logic.
    The orchestrator MUST NOT populate fields other than correlation_id and execution_start_timestamp.
    Modules MUST NOT store evaluation, validation, convergence, adaptive-depth, TTL, or execution metadata inside context.
    Logging MUST use ExecutionContext only for correlation_id; all other fields come from domain objects.
    ExecutionContext MUST NOT be serialized wholesale.
    """
    
    correlation_id: str
    execution_start_timestamp: str


@dataclass
class OrchestrationState:
    """Current execution context maintained by the kernel."""

    plan: Plan
    current_step_id: Optional[str] = None
    tool_history: List[Dict[str, Any]] = field(default_factory=list)
    llm_outputs: List[Dict[str, Any]] = field(default_factory=list)
    supervisor_actions: List[Dict[str, Any]] = field(default_factory=list)
    ttl_remaining: int = 10
    memory: Optional[Memory] = None


    def get_current_step(self) -> Optional[PlanStep]:
        """Get the current step object if available."""
        if not self.current_step_id:
            return None
        for step in self.plan.steps:
            if step.step_id == self.current_step_id:
                return step
        return None

    def update_step_status(self, step_id: str, status: StepStatus) -> None:
        """Update the status of a step."""
        for step in self.plan.steps:
            if step.step_id == step_id:
                step.status = status
                return
        raise ValueError(f"Step '{step_id}' not found in plan.")

    def start_step(self, step_id: str) -> None:
        """Mark a step as running and set it as the current step."""
        self.update_step_status(step_id, StepStatus.RUNNING)
        self.current_step_id = step_id

    def complete_current_step(self) -> None:
        """Mark the current step as complete and clear the pointer."""
        if not self.current_step_id:
            raise ValueError("No step is currently running.")
        self.update_step_status(self.current_step_id, StepStatus.COMPLETE)
        self.current_step_id = None

    def fail_current_step(self, error: Optional[str] = None) -> None:
        """Mark the current step as failed and clear the pointer."""
        if not self.current_step_id:
            raise ValueError("No step is currently running.")
        self.update_step_status(self.current_step_id, StepStatus.FAILED)
        self.current_step_id = None
        if error:
            self.supervisor_actions.append({"type": "step_failure", "message": error})


class ExecutionPass(BaseModel):
    """Represents a single iteration of the multi-pass loop."""

    pass_number: int = Field(..., ge=0, description="Sequential identifier (0 for initial plan, 1-N for execution passes)")
    phase: Literal["A", "B", "C", "D"] = Field(..., description="Current phase (A=TaskProfile, B=Initial Plan, C=Execution, D=Adaptive Depth)")
    plan_state: Dict[str, Any] = Field(..., description="Snapshot of plan at pass start (JSON-serializable)")
    execution_results: List[Dict[str, Any]] = Field(default_factory=list, description="Step outputs and tool results (JSON-serializable)")
    evaluation_results: Dict[str, Any] = Field(default_factory=dict, description="Convergence assessment and semantic validation report (JSON-serializable)")
    refinement_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Plan/step modifications if any (JSON-serializable)")
    ttl_remaining: int = Field(..., ge=0, description="TTL cycles remaining")
    timing_information: Dict[str, Any] = Field(default_factory=dict, description="Contains start_time, end_time, duration (ISO 8601 timestamps)")

    model_config = {"extra": "forbid"}


class ExecutionHistory(BaseModel):
    """Structured history of completed multi-pass execution."""

    execution_id: str = Field(..., description="Unique identifier for execution")
    task_input: str = Field(..., description="Original task description")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Convergence criteria, TTL, adaptive depth settings (JSON-serializable)")
    passes: List[ExecutionPass] = Field(..., min_length=1, description="Ordered list of execution passes")
    final_result: Dict[str, Any] = Field(default_factory=dict, description="Converged or TTL-expired result (JSON-serializable)")
    overall_statistics: Dict[str, Any] = Field(default_factory=dict, description="Contains total_passes, total_refinements, convergence_achieved, total_time")

    model_config = {"extra": "forbid"}


class TTLExpirationResponse(BaseModel):
    """Response structure when TTL expires during execution."""

    expiration_type: Literal["phase_boundary", "mid_phase"] = Field(..., description="Where TTL expired: at phase boundary or mid-phase")
    phase: Literal["A", "B", "C", "D"] = Field(..., description="Phase where expiration occurred")
    pass_number: int = Field(..., ge=0, description="Pass number where expiration occurred")
    ttl_remaining: int = Field(..., ge=0, description="TTL cycles remaining (should be 0)")
    plan_state: Dict[str, Any] = Field(..., description="Plan state at expiration (JSON-serializable)")
    execution_results: List[Dict[str, Any]] = Field(default_factory=list, description="Partial execution results (JSON-serializable)")
    message: str = Field(..., description="Human-readable expiration message")

    model_config = {"extra": "forbid"}

