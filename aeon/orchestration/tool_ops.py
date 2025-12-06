"""Tool repair, recovery, and retry logic.

This module contains functions for handling tool execution failures,
repair attempts, and recovery behavior, extracted from the kernel to reduce LOC.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from aeon.observability.logger import JSONLLogger
    from aeon.plan.models import PlanStep
    from aeon.tools.registry import ToolRegistry
    from aeon.validation.schema import Validator

__all__ = [
    "handle_missing_tool_repair",
    "should_attempt_repair",
    "attempt_tool_repair_with_logging",
    "log_tool_call_to_history",
]


def should_attempt_repair(
    step: "PlanStep",
    tool_registry: Optional["ToolRegistry"],
    supervisor: Optional[Any],
) -> bool:
    """
    Determine if repair should be attempted for a step.

    Args:
        step: Plan step to check
        tool_registry: Tool registry
        supervisor: Supervisor instance

    Returns:
        True if repair should be attempted, False otherwise
    """
    return bool(step.tool and tool_registry and supervisor)


def handle_missing_tool_repair(
    step: "PlanStep",
    tool_registry: "ToolRegistry",
    supervisor: Any,
    plan_goal: str,
    validator: "Validator",
    logger: Optional["JSONLLogger"] = None,
    correlation_id: Optional[str] = None,
) -> bool:
    """
    Handle missing tool repair flow (T117).

    Validates tool, attempts repair if missing/invalid, and logs the outcome.

    Args:
        step: Plan step with tool field
        tool_registry: Tool registry
        supervisor: Supervisor for repair
        plan_goal: Plan goal for repair context
        validator: Validator for tool validation
        logger: Optional logger for repair logging
        correlation_id: Optional correlation ID for logging

    Returns:
        True if repair was successful, False otherwise
    """
    from aeon.exceptions import ToolError
    from aeon.tools.repair import attempt_tool_repair

    # Validate tool before execution
    validation_result = validator.validate_step_tool(step, tool_registry)
    if validation_result["valid"]:
        return True  # Tool is valid, no repair needed

    # Tool is missing/invalid - log original error before repair attempt
    if logger and correlation_id:
        original_error = ToolError(f"Tool '{step.tool}' not found in registry")
        error_record = original_error.to_error_record(
            context={"step_id": step.step_id, "tool_name": step.tool}
        )
        logger.log_error(
            correlation_id=correlation_id,
            error=error_record,
            step_id=step.step_id,
            tool_name=step.tool,
        )

    # Attempt repair
    repair_success = attempt_tool_repair(step, tool_registry, supervisor, plan_goal)

    # Log recovery outcome
    if logger and correlation_id:
        original_error = ToolError(f"Tool '{step.tool}' not found in registry")
        error_record = original_error.to_error_record(
            context={"step_id": step.step_id, "tool_name": step.tool}
        )
        logger.log_error_recovery(
            correlation_id=correlation_id,
            original_error=error_record,
            recovery_action="supervisor_repair_missing_tool",
            recovery_outcome="success" if repair_success else "failure",
        )

    return repair_success


def attempt_tool_repair_with_logging(
    step: "PlanStep",
    tool_registry: "ToolRegistry",
    supervisor: Any,
    plan_goal: str,
    validator: "Validator",
    logger: Optional["JSONLLogger"] = None,
    correlation_id: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Attempt tool repair with full logging support.

    Args:
        step: Plan step with tool field
        tool_registry: Tool registry
        supervisor: Supervisor for repair
        plan_goal: Plan goal for repair context
        validator: Validator for tool validation
        logger: Optional logger
        correlation_id: Optional correlation ID

    Returns:
        Tuple of (repair_success, error_message)
    """
    try:
        success = handle_missing_tool_repair(
            step, tool_registry, supervisor, plan_goal, validator, logger, correlation_id
        )
        return (success, None if success else "Tool repair failed")
    except Exception as e:
        if logger and correlation_id:
            from aeon.exceptions import ToolError
            error = ToolError(f"Tool repair attempt failed: {str(e)}")
            error_record = error.to_error_record(
                context={"step_id": step.step_id, "tool_name": step.tool}
            )
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                step_id=step.step_id,
                tool_name=step.tool,
            )
        return (False, str(e))


def log_tool_call_to_history(
    step: "PlanStep",
    tool_registry: "ToolRegistry",
    execution_result: Any,
    state: Any,  # OrchestrationState
) -> None:
    """
    Log a successful tool call to state.tool_history.

    Args:
        step: Plan step with tool field
        tool_registry: Tool registry
        execution_result: StepExecutionResult with tool execution result
        state: OrchestrationState to update tool_history
    """
    from datetime import datetime
    from aeon.tools.models import ToolCall

    if not (step.tool and execution_result.success):
        return

    tool = tool_registry.get(step.tool)
    if tool:
        tool_call = ToolCall(
            tool_name=step.tool,
            arguments={},  # No args for now
            result=execution_result.result,
            timestamp=datetime.now().isoformat(),
            step_id=step.step_id,
        )
        state.tool_history.append(tool_call.model_dump())

