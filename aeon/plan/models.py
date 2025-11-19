"""Plan data models."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StepStatus(str, Enum):
    """Plan step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


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

    @field_validator("step_id", "description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are non-empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

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


