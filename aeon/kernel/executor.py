"""Step executor for multi-mode step execution."""

import json
from typing import Any, Dict, Optional

from aeon.exceptions import ToolError, ValidationError
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.plan.models import PlanStep, StepStatus
from aeon.plan.prompts import build_reasoning_prompt
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
        # Update step status to running
        step.status = StepStatus.RUNNING

        # Tool field takes precedence over agent field
        if step.tool:
            # Validate tool
            validation_result = self.validator.validate_step_tool(step, registry)
            if validation_result["valid"]:
                # Tool is valid - execute tool-based step
                return self.execute_tool_step(step, registry, memory)
            else:
                # Tool is missing/invalid - fallback to LLM reasoning
                # Orchestrator will handle repair flow if supervisor is available
                # For now, fallback to LLM reasoning (orchestrator can intercept and repair)
                return self.execute_llm_reasoning_step(step, memory, llm)
        elif step.agent == "llm":
            # Explicit LLM reasoning step
            return self.execute_llm_reasoning_step(step, memory, llm)
        else:
            # No tool, no agent - treat as missing-tool, use fallback
            return self.execute_llm_reasoning_step(step, memory, llm)

    def execute_tool_step(
        self,
        step: PlanStep,
        registry: ToolRegistry,
        memory: Memory,
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

            # Invoke tool (no arguments for now - can be enhanced later)
            try:
                result = tool.invoke()
            except Exception as e:
                step.status = StepStatus.FAILED
                error_msg = f"Tool '{step.tool}' execution failed: {str(e)}"
                return StepExecutionResult(
                    success=False,
                    result={},
                    error=error_msg,
                    execution_mode="tool",
                )

            # Store result in memory
            memory_key = f"step_{step.step_id}_result"
            memory.write(memory_key, result)

            # Mark step as complete
            step.status = StepStatus.COMPLETE

            return StepExecutionResult(
                success=True,
                result=result,
                error=None,
                execution_mode="tool",
            )

        except Exception as e:
            step.status = StepStatus.FAILED
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
    ) -> StepExecutionResult:
        """
        Execute LLM reasoning step (explicit or fallback).

        Handles clarity_state (CLEAR, PARTIALLY_CLEAR, BLOCKED) and context propagation.

        Args:
            step: PlanStep with agent="llm" or missing tool
            memory: Memory interface
            llm: LLM adapter

        Returns:
            StepExecutionResult
        """
        try:
            # Build prompt with step description, context propagation fields, and memory context
            prompt = build_reasoning_prompt(step, memory)

            # Invoke LLM
            response = llm.generate(
                prompt=prompt,
                system_prompt="You are a reasoning assistant. Provide clear, structured responses. Include clarity_state and handoff_to_next in your response.",
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

            # Handle clarity_state: BLOCKED → mark as invalid
            if clarity_state == "BLOCKED":
                step.status = StepStatus.INVALID
            else:
                step.status = StepStatus.COMPLETE

            # Store result in memory
            memory_key = f"step_{step.step_id}_result"
            memory.write(memory_key, result)

            return StepExecutionResult(
                success=True,
                result=result,
                error=None,
                execution_mode="llm" if step.agent == "llm" else "fallback",
            )

        except Exception as e:
            step.status = StepStatus.FAILED
            return StepExecutionResult(
                success=False,
                result={},
                error=str(e),
                execution_mode="llm" if step.agent == "llm" else "fallback",
            )


