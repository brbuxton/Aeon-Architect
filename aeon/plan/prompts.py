"""Prompt construction utilities for plan generation and execution."""

from typing import Any, Optional

from aeon.plan.models import PlanStep
from aeon.memory.interface import Memory


def get_plan_generation_system_prompt() -> str:
    """Get system prompt for plan generation."""
    return """You are a planning assistant. Generate declarative plans in JSON format.
A plan must have:
- "goal": string describing the objective
- "steps": array of step objects, each with:
  - "step_id": unique identifier (string)
  - "description": what the step does (string)
  - "status": "pending" (always pending for new plans)
  - "tool": (optional) name of registered tool for tool-based execution
  - "agent": (optional) "llm" for explicit LLM reasoning steps

IMPORTANT: Only reference tools that exist in the available tools list. Do not invent tools.
If a step requires a tool, use the "tool" field with the exact tool name from the available list.
If a step requires reasoning without a tool, use "agent": "llm".

Return only valid JSON."""


def construct_plan_generation_prompt(request: str, tool_registry: Optional[Any] = None) -> str:
    """
    Construct prompt for plan generation.
    
    Includes tool registry if available.
    
    Args:
        request: Natural language request
        tool_registry: Optional tool registry to include available tools
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Generate a plan to accomplish the following request:

{request}

"""
    
    # Include tool registry if available
    if tool_registry:
        available_tools = tool_registry.export_tools_for_llm()
        if available_tools:
            prompt += "Available tools:\n"
            for tool in available_tools:
                prompt += f"- {tool['name']}: {tool.get('description', 'No description')}\n"
                if tool.get('input_schema'):
                    import json
                    prompt += f"  Input schema: {json.dumps(tool['input_schema'], indent=2)}\n"
            prompt += "\n"
            prompt += "You may reference these tools in step.tool fields. Do not invent tools.\n\n"
    
    prompt += "Return a JSON plan with goal and steps."
    return prompt


def build_reasoning_prompt(step: PlanStep, memory: Memory) -> str:
    """
    Build reasoning prompt with step description, context propagation fields, and memory context.

    Args:
        step: PlanStep to execute
        memory: Memory interface

    Returns:
        Prompt string
    """
    # Start with step description
    prompt = f"Task: {step.description}\n\n"

    # Add step context (step_index, total_steps) if available
    if hasattr(step, 'step_index') and step.step_index is not None:
        prompt += f"Step {step.step_index}"
        if hasattr(step, 'total_steps') and step.total_steps is not None:
            prompt += f" of {step.total_steps}"
        prompt += "\n\n"

    # Add incoming context from previous steps if available
    if hasattr(step, 'incoming_context') and step.incoming_context:
        prompt += f"Context from previous steps:\n{step.incoming_context}\n\n"

    # Add memory context if available
    try:
        # Search for relevant memory entries (prefix with step_id or general context)
        context_entries = memory.search("step_")
        if context_entries:
            prompt += "Additional context from memory:\n"
            for key, value in context_entries[:5]:  # Limit to 5 most recent
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
    except Exception:
        # If memory search fails, continue without context
        pass

    prompt += "Please provide your reasoning and result. "
    prompt += "If the task is clear and you can proceed, respond with clarity_state: CLEAR. "
    prompt += "If the task is partially clear but needs more information, respond with clarity_state: PARTIALLY_CLEAR. "
    prompt += "If the task is blocked and cannot proceed, respond with clarity_state: BLOCKED. "
    prompt += "Include a 'handoff_to_next' field with context to pass to the next step."
    return prompt
