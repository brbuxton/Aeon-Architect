"""Helper functions for observability data collection."""

from typing import Any, Dict, List, Optional

from aeon.kernel.state import OrchestrationState


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

