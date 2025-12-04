"""Tool repair helper functions."""

from typing import Optional

from aeon.exceptions import SupervisorError
from aeon.plan.models import PlanStep
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry


def attempt_tool_repair(
    step: PlanStep,
    tool_registry: ToolRegistry,
    supervisor: Supervisor,
    plan_goal: str,
) -> bool:
    """
    Attempt to repair a step with missing/invalid tool.

    Args:
        step: PlanStep to repair (modified in-place)
        tool_registry: Tool registry for available tools
        supervisor: Supervisor for repair
        plan_goal: Plan goal for context

    Returns:
        True if repair succeeded, False otherwise
    """
    try:
        available_tools = tool_registry.export_tools_for_llm()
        repaired_step = supervisor.repair_missing_tool_step(step, available_tools, plan_goal)
        # Update step with repaired version
        step.tool = repaired_step.tool
        step.errors = None  # Errors cleared on successful repair
        return True
    except SupervisorError:
        # Repair failed - will fallback to LLM reasoning
        return False

