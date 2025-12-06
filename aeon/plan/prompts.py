"""Prompt construction utilities for plan generation and execution."""

from typing import Any, Dict, Optional

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


def build_reasoning_prompt(
    step: PlanStep,
    memory: Memory,
    phase_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build reasoning prompt with step description, context propagation fields, and memory context.

    Args:
        step: PlanStep to execute
        memory: Memory interface
        phase_context: Optional phase context dict with request, task_profile, plan metadata, etc.
                      (Only present when called from multipass execution with context propagation)
                      
                      Required keys (if phase_context provided):
                      - request: Natural language request (string, non-null)
                      - pass_number: Pass number (int, non-null)
                      - phase: Phase identifier (str, non-null)
                      - ttl_remaining: TTL cycles remaining (int, non-null)
                      - correlation_id: Correlation ID (str, non-null)
                      
                      Optional keys:
                      - refined_plan_goal or initial_plan_goal: Plan goal (string)
                      - previous_outputs: Previous execution results (list)
                      - refinement_changes: Refinement changes (list)
                      
                      Unused keys (present in context but not used in prompt):
                      - initial_plan_steps: Step metadata (for future use)
                      - refined_plan_steps: Step metadata (for future use)
                      - current_plan_state: Full plan state (for future use)
                      - execution_results: Execution results (for future use)
                      - evaluation_results: Evaluation results (for future use)
                      - adaptive_depth_inputs: Adaptive depth inputs (for future use)
                      - execution_start_timestamp: Timestamp (for logging, not prompt)
                      - task_profile: Task profile (for future use)

    Returns:
        Prompt string
        
    Raises:
        ValueError: If phase_context is provided but required keys are missing or null
    """
    # T047: Validate phase_context to prevent null semantic inputs
    if phase_context is not None:
        required_keys = ["request", "pass_number", "phase", "ttl_remaining", "correlation_id"]
        missing_keys = []
        null_keys = []
        
        for key in required_keys:
            if key not in phase_context:
                missing_keys.append(key)
            elif phase_context[key] is None:
                null_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required phase_context keys: {', '.join(missing_keys)}")
        if null_keys:
            raise ValueError(f"Null semantic inputs in phase_context: {', '.join(null_keys)}")
    
    # Start with step description
    prompt = f"Task: {step.description}\n\n"

    # Add phase context if available (T035: propagate context to step execution)
    # This is only present when called from multipass execution (e.g., Phase C)
    if phase_context:
        prompt += "=== Execution Context ===\n"
        # T047: All required keys validated above, safe to use without .get() checks
        prompt += f"Request: {phase_context['request']}\n"
        # Handle plan goal - can be from different phases (initial_plan_goal or refined_plan_goal)
        plan_goal = phase_context.get("refined_plan_goal") or phase_context.get("initial_plan_goal")
        if plan_goal:
            prompt += f"Plan Goal: {plan_goal}\n"
        prompt += f"Pass Number: {phase_context['pass_number']}\n"
        prompt += f"Phase: {phase_context['phase']}\n"
        prompt += f"TTL Remaining: {phase_context['ttl_remaining']}\n"
        prompt += f"Correlation ID: {phase_context['correlation_id']}\n"
        if phase_context.get("previous_outputs"):
            prompt += f"Previous Outputs: {len(phase_context['previous_outputs'])} result(s)\n"
        if phase_context.get("refinement_changes"):
            prompt += f"Refinement Changes: {len(phase_context['refinement_changes'])} change(s)\n"
        prompt += "\n"

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
