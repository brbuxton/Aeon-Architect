"""Observability data models."""

from typing import Any, Dict, List

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

    model_config = ConfigDict(
        frozen=False,  # Allow updates during cycle
    )



