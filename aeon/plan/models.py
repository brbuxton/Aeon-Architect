"""Plan data models."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StepStatus(str, Enum):
    """Plan step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    INVALID = "invalid"


class PlanStep(BaseModel):
    """A single step within a plan."""

    step_id: str = Field(..., description="Unique identifier for the step")
    description: str = Field(..., description="Human-readable description of what the step does")
    status: StepStatus = Field(
        default=StepStatus.PENDING, description="Current execution state"
    )
    tool: Optional[str] = Field(
        default=None, description="Name of registered tool for tool-based execution"
    )
    agent: Optional[str] = Field(
        default=None, description="Execution agent type ('llm' for explicit LLM reasoning)"
    )
    errors: Optional[List[str]] = Field(
        default=None, description="List of error messages. Populated by validator when validation fails. Cleared by supervisor on successful repair."
    )
    # User Story 1: Context propagation fields
    step_index: Optional[int] = Field(
        default=None, ge=1, description="1-based step number"
    )
    total_steps: Optional[int] = Field(
        default=None, ge=1, description="Total number of steps in plan"
    )
    incoming_context: Optional[str] = Field(
        default=None, description="Context from previous steps (may be empty initially)"
    )
    handoff_to_next: Optional[str] = Field(
        default=None, description="Context to pass to next step (may be empty initially)"
    )
    step_output: Optional[str] = Field(
        default=None, description="Output from step execution"
    )
    clarity_state: Optional[Literal["CLEAR", "PARTIALLY_CLEAR", "BLOCKED"]] = Field(
        default=None, description="Clarity state returned by step execution LLM"
    )

    @field_validator("step_id", "description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate tool field (T100).
        
        If tool is present, it must be a non-empty string.
        Actual tool registration validation is done by Validator.validate_step_tool().
        """
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Tool field cannot be empty if present")
            return v.strip()
        return v

    @field_validator("agent")
    @classmethod
    def validate_agent(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate agent field (T101).
        
        If agent is present, it must be "llm".
        """
        if v is not None:
            v = v.strip().lower()
            if v != "llm":
                raise ValueError(f"Agent field must be 'llm' if present, got '{v}'")
            return "llm"
        return v

    model_config = ConfigDict(
        frozen=False,  # Allow status updates
        use_enum_values=True,
    )


class Plan(BaseModel):
    """A declarative plan representing a multi-step execution strategy."""

    goal: str = Field(..., description="The objective or goal of the plan")
    steps: List[PlanStep] = Field(..., min_length=1, description="Ordered list of execution steps")

    @field_validator("goal")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        """Validate that goal is non-empty."""
        if not v or not v.strip():
            raise ValueError("Goal cannot be empty")
        return v.strip()

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, v: List[PlanStep]) -> List[PlanStep]:
        """Validate that step IDs are unique."""
        step_ids = [step.step_id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Step IDs must be unique within a plan")
        return v

    model_config = ConfigDict(
        frozen=False,  # Allow step updates
    )


class RefinementAction(BaseModel):
    """A modification to plan or steps during refinement phase."""

    action_type: Literal["ADD", "MODIFY", "REMOVE", "REPLACE"] = Field(
        ..., description="Type of refinement action"
    )
    target_step_id: Optional[str] = Field(
        default=None, description="Identifier of step being changed (None for plan-level changes)"
    )
    target_plan_section: Optional[str] = Field(
        default=None, description="Plan section being changed (None for step-level changes)"
    )
    new_step: Optional[Dict[str, Any]] = Field(
        default=None, description="New step content for ADD/MODIFY actions (JSON-serializable)"
    )
    changes: Dict[str, Any] = Field(
        ..., description="Modified content description (JSON-serializable)"
    )
    reason: str = Field(..., description="Explanation of why refinement was needed")
    semantic_validation_input: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Validation issues that triggered refinement (JSON-serializable)",
    )
    inconsistency_detected: bool = Field(
        default=False,
        description="True if refinement creates inconsistency with executed steps",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Validate that reason is non-empty."""
        if not v or not v.strip():
            raise ValueError("Reason cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_target(self) -> "RefinementAction":
        """Validate that either target_step_id or target_plan_section is provided, but not both."""
        has_step_id = self.target_step_id is not None
        has_section = self.target_plan_section is not None

        if not has_step_id and not has_section:
            raise ValueError(
                "Either target_step_id or target_plan_section must be provided"
            )
        if has_step_id and has_section:
            raise ValueError(
                "Cannot specify both target_step_id and target_plan_section"
            )
        return self

    @model_validator(mode="after")
    def validate_new_step_for_action(self) -> "RefinementAction":
        """Validate that new_step is provided for ADD/MODIFY actions."""
        if self.action_type in ("ADD", "MODIFY"):
            if self.new_step is None:
                raise ValueError(
                    f"new_step is required for {self.action_type} actions"
                )
        return self

    model_config = ConfigDict(
        frozen=False,
    )


class Subplan(BaseModel):
    """A nested plan created for complex step decomposition."""

    plan: Plan = Field(..., description="The nested plan structure")
    parent_step_id: str = Field(..., description="ID of the parent step being decomposed")
    nesting_depth: int = Field(..., ge=1, description="Current nesting depth (1-based)")

    @field_validator("parent_step_id")
    @classmethod
    def validate_parent_step_id(cls, v: str) -> str:
        """Validate that parent_step_id is non-empty."""
        if not v or not v.strip():
            raise ValueError("Parent step ID cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        frozen=False,
    )


