"""Tool data models."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    """A record of a tool invocation during plan execution."""

    tool_name: str = Field(..., description="Name of the tool that was called")
    arguments: Dict[str, Any] = Field(..., description="Arguments passed to the tool")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Result returned by the tool"
    )
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error information if failed")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the call")
    step_id: str = Field(..., description="ID of the plan step that triggered this tool call")

    model_config = ConfigDict(frozen=False)  # Allow result/error updates



