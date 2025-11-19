"""Supervisor data models."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Type of supervisor repair action."""

    JSON_REPAIR = "json_repair"
    TOOL_CALL_REPAIR = "tool_call_repair"
    PLAN_REPAIR = "plan_repair"


class SupervisorAction(BaseModel):
    """A record of a supervisor repair attempt."""

    action_type: ActionType = Field(..., description="Type of repair action")
    original_output: Dict[str, Any] = Field(..., description="The malformed output that triggered repair")
    repaired_output: Optional[Dict[str, Any]] = Field(
        default=None, description="The corrected output (if repair succeeded)"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None, description="Error information if repair failed"
    )
    attempt_number: int = Field(..., ge=1, le=2, description="Which repair attempt this was (1 or 2)")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the action")

    class Config:
        """Pydantic config."""

        use_enum_values = True
        frozen = False  # Allow repaired_output/error updates



