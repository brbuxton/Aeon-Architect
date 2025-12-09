"""Step executor for multi-mode step execution.

Part of the kernel per Constitution. See orchestrator.py for constitutional LOC notes.
"""

import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from aeon.exceptions import ExecutionError

if TYPE_CHECKING:
    from aeon.observability.logger import JSONLLogger
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.plan.models import PlanStep, StepStatus
from aeon.plan.prompts import build_reasoning_prompt
from aeon.prompts.registry import get_prompt, PromptId, ReasoningStepSystemInput
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry
from aeon.validation.schema import Validator


class StepExecutionResult:
    """Result of step execution."""

    def __init__(
        self,
        success: bool,
        result: Dict[str, Any],
        error: Optional[str] = None,
        execution_mode: str = "unknown",
    ):
        """Initialize execution result."""
        self.success = success
        self.result = result
        self.error = error
        self.execution_mode = execution_mode


class StepExecutor:
    """Execute plan steps in different modes."""

    def __init__(self):
        """Initialize step executor."""
        self.validator = Validator()

    def execute_step(
        self,
        step: PlanStep,
        registry: ToolRegistry,
        memory: Memory,
        llm: LLMAdapter,
        supervisor: Supervisor,
        logger: Optional["JSONLLogger"] = None,
        correlation_id: Optional[str] = None,
        state: Optional[Any] = None,  # OrchestrationState (to access phase_c_context)
    ) -> StepExecutionResult:
        """
        Execute a plan step.

        Determines execution mode:
        - If step.tool present and valid → tool-based execution
        - Else if step.agent == "llm" → LLM reasoning execution
        - Else → missing-tool path (repair → fallback)

        Args:
            step: PlanStep to execute
            registry: Tool registry
            memory: Memory interface for storing results
            llm: LLM adapter for reasoning steps
            supervisor: Supervisor for missing-tool repair

        Returns:
            StepExecutionResult with execution outcome

        Raises:
            ExecutionError: On unrecoverable execution failure
        """
        # Update step status to running (T072)
        old_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
        step.status = StepStatus.RUNNING
        new_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
        if logger and correlation_id:
            logger.log_step_status_change(
                correlation_id=correlation_id,
                step_id=step.step_id,
                old_status=old_status,
                new_status=new_status,
                reason="step_execution_started",
            )

        # Tool field takes precedence over agent field
        if step.tool:
            # Validate tool
            validation_result = self.validator.validate_step_tool(step, registry)
            if validation_result["valid"]:
                # Tool is valid - execute tool-based step
                return self.execute_tool_step(step, registry, memory, logger, correlation_id)
            else:
                # Tool is missing/invalid - fallback to LLM reasoning
                # Orchestrator will handle repair flow if supervisor is available
                # For now, fallback to LLM reasoning (orchestrator can intercept and repair)
                return self.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id, state)
        elif step.agent == "llm":
            # Explicit LLM reasoning step
            return self.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id, state)
        else:
            # No tool, no agent - treat as missing-tool, use fallback
            return self.execute_llm_reasoning_step(step, memory, llm, logger, correlation_id, state)

    def execute_tool_step(
        self,
        step: PlanStep,
        registry: ToolRegistry,
        memory: Memory,
        logger: Optional["JSONLLogger"] = None,
        correlation_id: Optional[str] = None,
    ) -> StepExecutionResult:
        """
        Execute tool-based step.

        Args:
            step: PlanStep with tool field
            registry: Tool registry
            memory: Memory interface

        Returns:
            StepExecutionResult
        """
        try:
            # Get tool from registry
            tool = registry.get(step.tool)
            if not tool:
                step.status = StepStatus.FAILED
                error_msg = f"Tool '{step.tool}' not found in registry"
                return StepExecutionResult(
                    success=False,
                    result={},
                    error=error_msg,
                    execution_mode="tool",
                )

            # Invoke tool (no arguments for now - can be enhanced later) (T071)
            try:
                result = tool.invoke()
                
                # Log tool invocation result (T071)
                if logger and correlation_id:
                    logger.log_tool_invocation_result(
                        correlation_id=correlation_id,
                        step_id=step.step_id,
                        tool_name=step.tool,
                        success=True,
                        result=result if isinstance(result, dict) else {"result": result},
                    )
            except Exception as e:
                step.status = StepStatus.FAILED
                error_msg = f"Tool '{step.tool}' execution failed: {str(e)}"
                
                # Log tool invocation failure (T071)
                if logger and correlation_id:
                    logger.log_tool_invocation_result(
                        correlation_id=correlation_id,
                        step_id=step.step_id,
                        tool_name=step.tool,
                        success=False,
                        error=error_msg,
                    )
                
                # Log error if logger and correlation_id are available
                if logger and correlation_id:
                    from aeon.exceptions import ExecutionError
                    if not isinstance(e, ExecutionError):
                        execution_error = ExecutionError(error_msg)
                    else:
                        execution_error = e
                    error_record = execution_error.to_error_record(
                        context={"step_id": step.step_id, "tool_name": step.tool, "attempted_action": "tool_invoke"}
                    )
                    logger.log_error(
                        correlation_id=correlation_id,
                        error=error_record,
                        step_id=step.step_id,
                        tool_name=step.tool,
                        attempted_action="tool_invoke",
                    )
                
                return StepExecutionResult(
                    success=False,
                    result={},
                    error=error_msg,
                    execution_mode="tool",
                )

            # Store result in memory
            memory_key = f"step_{step.step_id}_result"
            memory.write(memory_key, result)

            # Mark step as complete (T072)
            old_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            step.status = StepStatus.COMPLETE
            new_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            if logger and correlation_id:
                logger.log_step_status_change(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    old_status=old_status,
                    new_status=new_status,
                    reason="step_execution_completed",
                )

            # Log step execution outcome (T070)
            if logger and correlation_id:
                logger.log_step_execution_outcome(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    execution_mode="tool",
                    success=True,
                    result=result if isinstance(result, dict) else {"result": result},
                )

            return StepExecutionResult(
                success=True,
                result=result,
                error=None,
                execution_mode="tool",
            )

        except Exception as e:
            old_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            step.status = StepStatus.FAILED
            new_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            
            # Log step status change (T072)
            if logger and correlation_id:
                logger.log_step_status_change(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    old_status=old_status,
                    new_status=new_status,
                    reason="step_execution_failed",
                )
            
            # Log step execution outcome (T070)
            if logger and correlation_id:
                logger.log_step_execution_outcome(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    execution_mode="tool",
                    success=False,
                    error=str(e),
                )
            
            # Log error if logger and correlation_id are available
            if logger and correlation_id:
                from aeon.exceptions import ExecutionError
                if not isinstance(e, ExecutionError):
                    execution_error = ExecutionError(str(e))
                else:
                    execution_error = e
                error_record = execution_error.to_error_record(
                    context={"step_id": step.step_id, "tool_name": step.tool if step.tool else None}
                )
                logger.log_error(
                    correlation_id=correlation_id,
                    error=error_record,
                    step_id=step.step_id,
                    tool_name=step.tool if step.tool else None,
                )
            
            return StepExecutionResult(
                success=False,
                result={},
                error=str(e),
                execution_mode="tool",
            )

    def execute_llm_reasoning_step(
        self,
        step: PlanStep,
        memory: Memory,
        llm: LLMAdapter,
        logger: Optional["JSONLLogger"] = None,
        correlation_id: Optional[str] = None,
        state: Optional[Any] = None,  # OrchestrationState (to access phase_c_context)
    ) -> StepExecutionResult:
        """
        Execute LLM reasoning step (explicit or fallback).

        Handles clarity_state (CLEAR, PARTIALLY_CLEAR, BLOCKED) and context propagation.

        Args:
            step: PlanStep with agent="llm" or missing tool
            memory: Memory interface
            llm: LLM adapter
            logger: Optional logger
            correlation_id: Optional correlation ID
            state: Optional OrchestrationState to access phase_c_context

        Returns:
            StepExecutionResult
        """
        from aeon.orchestration.phases import (
            get_context_propagation_specification,
            validate_context_propagation,
        )
        from aeon.exceptions import ContextPropagationError

        try:
            # Validate context before LLM call if available in state
            # Only validate if we have phase context (i.e., called from multipass with context propagation)
            phase_context_dict = None
            if state and hasattr(state, 'phase_context') and state.phase_context:
                phase = state.phase_context.get("phase")
                phase_context_dict = state.phase_context.get("context")
                if phase and phase_context_dict:
                    # Context was already validated in phase method, but verify it's still valid
                    spec = get_context_propagation_specification(phase)
                    is_valid, error_message, missing_fields = validate_context_propagation(phase, phase_context_dict, spec)
                    if not is_valid:
                        error = ContextPropagationError(
                            phase=phase,
                            missing_fields=missing_fields,
                            message=f"Context validation failed during step execution: {error_message}",
                        )
                        # Log error and return failure
                        if logger and correlation_id:
                            error_record = error.to_error_record()
                            logger.log_error(
                                correlation_id=correlation_id,
                                error=error_record,
                                step_id=step.step_id,
                            )
                        return StepExecutionResult(
                            success=False,
                            result={},
                            error=str(error),
                            execution_mode="llm" if step.agent == "llm" else "fallback",
                        )

            # Build prompt with step description, context propagation fields, and memory context
            # Pass phase context if available (from multipass execution)
            prompt = build_reasoning_prompt(step, memory, phase_context=phase_context_dict)

            # Invoke LLM (context already validated above)
            # Get system prompt from registry
            system_prompt = get_prompt(PromptId.REASONING_STEP_SYSTEM, ReasoningStepSystemInput())
            response = llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.7,
            )

            # Extract result from LLM response
            result_text = response.get("text", "").strip()
            
            # Try to parse as JSON
            try:
                parsed = json.loads(result_text)
                # If it's a dict with "result" key, use it directly
                if isinstance(parsed, dict) and "result" in parsed:
                    result = parsed
                # If it's a plan structure (has "goal" and "steps"), wrap as result
                elif isinstance(parsed, dict) and "goal" in parsed and "steps" in parsed:
                    # This is a plan structure from MockLLMAdapter default - extract or wrap
                    # For now, wrap the entire response as result
                    result = {"result": result_text}
                else:
                    # Other JSON structure - ensure it has "result" key
                    if isinstance(parsed, dict):
                        if "result" not in parsed:
                            result = {"result": parsed}
                        else:
                            result = parsed
                    else:
                        result = {"result": parsed}
            except json.JSONDecodeError:
                # If not JSON, wrap in result dict
                result = {"result": result_text}

            # Extract clarity_state and handoff_to_next from result
            clarity_state = None
            handoff_to_next = None
            if isinstance(result, dict):
                clarity_state = result.get("clarity_state")
                handoff_to_next = result.get("handoff_to_next")
                # Remove clarity_state and handoff_to_next from result dict (they're step fields, not result)
                result = {k: v for k, v in result.items() if k not in ["clarity_state", "handoff_to_next"]}

            # Populate step fields
            if hasattr(step, 'clarity_state'):
                step.clarity_state = clarity_state
            if hasattr(step, 'handoff_to_next'):
                step.handoff_to_next = handoff_to_next
            if hasattr(step, 'step_output'):
                # Store the result text as step_output
                step.step_output = result_text if not isinstance(result, dict) else json.dumps(result)

            # Handle clarity_state: BLOCKED → mark as invalid (T072)
            old_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            if clarity_state == "BLOCKED":
                step.status = StepStatus.INVALID
            else:
                step.status = StepStatus.COMPLETE
            new_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            if logger and correlation_id:
                logger.log_step_status_change(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    old_status=old_status,
                    new_status=new_status,
                    reason="step_execution_completed" if clarity_state != "BLOCKED" else "step_blocked",
                )

            # Store result in memory
            memory_key = f"step_{step.step_id}_result"
            memory.write(memory_key, result)

            # Log step execution outcome (T070)
            if logger and correlation_id:
                logger.log_step_execution_outcome(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    execution_mode="llm" if step.agent == "llm" else "fallback",
                    success=True,
                    result=result if isinstance(result, dict) else {"result": result},
                )

            return StepExecutionResult(
                success=True,
                result=result,
                error=None,
                execution_mode="llm" if step.agent == "llm" else "fallback",
            )

        except Exception as e:
            old_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            step.status = StepStatus.FAILED
            new_status = step.status.value if hasattr(step.status, 'value') else str(step.status)
            
            # Log step status change (T072)
            if logger and correlation_id:
                logger.log_step_status_change(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    old_status=old_status,
                    new_status=new_status,
                    reason="step_execution_failed",
                )
            
            # Log step execution outcome (T070)
            if logger and correlation_id:
                logger.log_step_execution_outcome(
                    correlation_id=correlation_id,
                    step_id=step.step_id,
                    execution_mode="llm" if step.agent == "llm" else "fallback",
                    success=False,
                    error=str(e),
                )
            
            # Log error if logger and correlation_id are available
            if logger and correlation_id:
                from aeon.exceptions import ExecutionError
                if not isinstance(e, ExecutionError):
                    execution_error = ExecutionError(str(e))
                else:
                    execution_error = e
                error_record = execution_error.to_error_record(
                    context={"step_id": step.step_id, "execution_mode": "llm" if step.agent == "llm" else "fallback"}
                )
                logger.log_error(
                    correlation_id=correlation_id,
                    error=error_record,
                    step_id=step.step_id,
                    attempted_action="llm_reasoning",
                )
            
            return StepExecutionResult(
                success=False,
                result={},
                error=str(e),
                execution_mode="llm" if step.agent == "llm" else "fallback",
            )


