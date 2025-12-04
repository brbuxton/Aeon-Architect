"""Tool invocation utilities."""

from datetime import datetime
from typing import Any, Dict

from aeon.exceptions import ToolError, ValidationError
from aeon.kernel.state import OrchestrationState
from aeon.tools.models import ToolCall
from aeon.tools.registry import ToolRegistry


def invoke_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    step_id: str,
    state: OrchestrationState,
    tool_registry: ToolRegistry,
) -> Dict[str, Any]:
    """
    Invoke a tool with validated arguments.

    Args:
        tool_name: Name of the tool to invoke
        arguments: Arguments to pass to the tool
        step_id: ID of the step that triggered this tool call
        state: Current orchestration state
        tool_registry: Tool registry

    Returns:
        Tool result dict

    Raises:
        ToolError: If tool invocation fails
        ValidationError: If input/output validation fails
    """
    tool = tool_registry.get(tool_name)
    if not tool:
        raise ToolError(f"Tool '{tool_name}' not found in registry")
    
    # Validate input
    try:
        tool.validate_input(**arguments)
    except ValidationError as e:
        raise ToolError(f"Input validation failed for tool '{tool_name}': {str(e)}") from e
    
    # Invoke tool
    try:
        result = tool.invoke(**arguments)
    except ToolError:
        raise
    except Exception as e:
        raise ToolError(f"Tool '{tool_name}' execution failed: {str(e)}") from e
    
    # Validate output
    try:
        tool.validate_output(result)
    except ValidationError as e:
        raise ToolError(f"Output validation failed for tool '{tool_name}': {str(e)}") from e
    
    # Log tool call to history
    tool_call = ToolCall(
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        timestamp=datetime.now().isoformat(),
        step_id=step_id,
    )
    state.tool_history.append(tool_call.model_dump())
    
    return result


def handle_tool_error(
    tool_name: str,
    error: Exception,
    step_id: str,
    state: OrchestrationState,
) -> None:
    """
    Handle tool invocation error.

    Args:
        tool_name: Name of the tool that failed
        error: The error that occurred
        step_id: ID of the step that triggered this tool call
        state: Current orchestration state
    """
    # Log failed tool call
    tool_call = ToolCall(
        tool_name=tool_name,
        arguments={},
        error={"type": type(error).__name__, "message": str(error)},
        timestamp=datetime.now().isoformat(),
        step_id=step_id,
    )
    state.tool_history.append(tool_call.model_dump())
    
    # Mark step as failed but don't raise - allow execution to continue
    # This enables partial success scenarios
    state.fail_current_step(error=f"Tool '{tool_name}' failed: {str(error)}")
