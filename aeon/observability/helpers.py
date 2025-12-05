"""Helper functions for observability data collection."""

import hashlib
import uuid
from typing import Any, Dict, List, Optional

from aeon.kernel.state import OrchestrationState

# Fixed namespace UUID for correlation ID generation
# This is a deterministic namespace UUID for Aeon correlation IDs
CORRELATION_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def generate_correlation_id(execution_start_timestamp: str, request: str) -> str:
    """
    Generate a deterministic correlation ID using UUIDv5.

    Args:
        execution_start_timestamp: ISO 8601 timestamp of execution start
        request: Request string (e.g., user query, task description)

    Returns:
        Correlation ID as UUIDv5 string

    Note:
        Uses deterministic UUIDv5 generation to preserve kernel determinism.
        Same inputs produce the same correlation ID.
    """
    try:
        # Create request hash for uniqueness
        request_hash = hashlib.sha256(request.encode("utf-8")).hexdigest()
        
        # Create name component: timestamp + request hash
        name = f"{execution_start_timestamp}:{request_hash}"
        
        # Generate UUIDv5 with fixed namespace
        correlation_uuid = uuid.uuid5(CORRELATION_NAMESPACE, name)
        
        return str(correlation_uuid)
    except Exception:
        # Fallback to deterministic timestamp-based ID if UUID generation fails
        request_hash = hashlib.sha256(request.encode("utf-8")).hexdigest()
        return f"aeon-{execution_start_timestamp}-{request_hash[:8]}"


def collect_cycle_data(state: OrchestrationState) -> Dict[str, Any]:
    """
    Collect data for cycle logging from orchestration state.

    Args:
        state: Current orchestration state

    Returns:
        Dict with:
            - tool_calls: List of tool calls for current step
            - supervisor_actions: List of supervisor actions (last one)
            - llm_output: Last LLM output
    """
    # Get tool calls from current step (from tool_history)
    tool_calls: List[Dict[str, Any]] = []
    if state.tool_history:
        # Get tool calls for current step
        current_step_id = state.current_step_id
        for tool_call in state.tool_history:
            if tool_call.get("step_id") == current_step_id:
                tool_calls.append(tool_call)

    # Get supervisor actions (from supervisor_actions)
    supervisor_actions = state.supervisor_actions[-1:] if state.supervisor_actions else []

    # Get LLM output (from llm_outputs, use last one if available)
    llm_output = state.llm_outputs[-1] if state.llm_outputs else {}

    return {
        "tool_calls": tool_calls,
        "supervisor_actions": supervisor_actions,
        "llm_output": llm_output,
    }

