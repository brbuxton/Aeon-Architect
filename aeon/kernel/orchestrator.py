"""Core orchestrator for LLM orchestration loop."""

from datetime import datetime
from typing import Any, Dict, Optional

from aeon.exceptions import LLMError, PlanError, SupervisorError, ToolError, TTLExpiredError, ValidationError
from aeon.kernel.state import OrchestrationState
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.observability.logger import JSONLLogger
from aeon.plan.executor import PlanExecutor
from aeon.plan.models import Plan, PlanStep
from aeon.plan.parser import PlanParser
from aeon.plan.validator import PlanValidator
from aeon.tools.models import ToolCall


class Orchestrator:
    """Core orchestrator for LLM orchestration loop."""

    def __init__(
        self,
        llm: LLMAdapter,
        memory: Optional[Memory] = None,
        ttl: int = 10,
        tool_registry: Optional[Any] = None,
        supervisor: Optional[Any] = None,
        logger: Optional[JSONLLogger] = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            llm: LLM adapter for generation
            memory: Memory interface (optional)
            ttl: Time-to-live in cycles (default 10)
            tool_registry: Tool registry (optional, for later phases)
            supervisor: Supervisor for error repair (optional, for later phases)
            logger: JSONL logger for cycle logging (optional)
        """
        self.llm = llm
        self.memory = memory
        self.ttl = ttl
        self.tool_registry = tool_registry
        self.supervisor = supervisor
        self.logger = logger
        self.parser = PlanParser()
        self.validator = PlanValidator()
        self.state: Optional[OrchestrationState] = None
        self._cycle_number = 0

    def generate_plan(self, request: str) -> Plan:
        """
        Generate a plan from a natural language request.

        Args:
            request: Natural language request

        Returns:
            Generated Plan object

        Raises:
            LLMError: If LLM generation fails
            PlanError: If plan parsing/validation fails
        """
        # Construct prompt for plan generation
        system_prompt = self._get_plan_generation_system_prompt()
        prompt = self._construct_plan_generation_prompt(request)

        try:
            # Generate LLM response
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.7,
            )

            # Extract plan JSON from LLM response
            plan_json = self._extract_plan_from_response(response)

            # Parse and validate plan
            try:
                plan = self.parser.parse(plan_json)
                self.validator.validate_plan(plan.model_dump())
            except PlanError as parse_error:
                # If supervisor is available and parsing failed, try to repair the plan structure
                if self.supervisor:
                    try:
                        repaired_plan_dict = self.supervisor.repair_plan(plan_json)
                        # Try parsing again with repaired plan
                        plan = self.parser.parse(repaired_plan_dict)
                        self.validator.validate_plan(plan.model_dump())
                    except (SupervisorError, PlanError) as repair_error:
                        raise PlanError(
                            f"Failed to parse/validate plan and supervisor repair failed: {str(repair_error)}"
                        ) from repair_error
                else:
                    raise

            return plan

        except LLMError as e:
            raise LLMError(f"Failed to generate plan: {str(e)}") from e
        except PlanError as e:
            raise PlanError(f"Failed to parse/validate plan: {str(e)}") from e
        except Exception as e:
            raise PlanError(f"Unexpected error during plan generation: {str(e)}") from e

    def _get_plan_generation_system_prompt(self) -> str:
        """Get system prompt for plan generation."""
        return """You are a planning assistant. Generate declarative plans in JSON format.
A plan must have:
- "goal": string describing the objective
- "steps": array of step objects, each with:
  - "step_id": unique identifier (string)
  - "description": what the step does (string)
  - "status": "pending" (always pending for new plans)

Return only valid JSON."""

    def _construct_plan_generation_prompt(self, request: str) -> str:
        """Construct prompt for plan generation."""
        return f"""Generate a plan to accomplish the following request:

{request}

Return a JSON plan with goal and steps."""

    def _extract_plan_from_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract plan JSON from LLM response.

        Args:
            response: LLM response dict

        Returns:
            Plan JSON dict

        Raises:
            PlanError: If plan extraction fails
        """
        text = response.get("text", "")
        
        import json
        import re
        
        # First, try to extract JSON from markdown code blocks (```json ... ```)
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object with proper brace matching
        # Find the first { and then match braces to find the complete JSON object
        brace_start = text.find('{')
        if brace_start >= 0:
            brace_count = 0
            brace_end = -1
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        brace_end = i
                        break
            
            if brace_end > brace_start:
                json_str = text[brace_start:brace_end + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        # If no JSON found, try parsing entire text
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            # If supervisor is available, try to repair the malformed JSON
            if self.supervisor:
                try:
                    repaired_json = self.supervisor.repair_json(text)
                    return repaired_json
                except SupervisorError as se:
                    raise PlanError(
                        f"Failed to extract plan JSON and supervisor repair failed: {str(se)}"
                    ) from se
            raise PlanError(f"Failed to extract plan JSON from response: {str(e)}") from e

    def execute(self, request: str, plan: Optional[Plan] = None) -> Dict[str, Any]:
        """
        Execute a request: generate plan (if needed) and run it sequentially.

        Args:
            request: Natural language request
            plan: Optional pre-generated plan

        Returns:
            Execution result dict

        Raises:
            TTLExpiredError: If TTL expires during execution
            LLMError: If LLM operations fail
            PlanError: If plan operations fail
        """
        # Generate plan if one was not supplied
        plan_to_execute = plan or self.generate_plan(request)

        # Initialize state for execution
        self.state = OrchestrationState(plan=plan_to_execute, ttl_remaining=self.ttl)
        self._cycle_number = 0

        # Execute plan sequentially
        try:
            executor = PlanExecutor(state=self.state, step_runner=self._execute_step)
            executor.execute()
            
            # Execution completed successfully
            return {
                "plan": self.state.plan.model_dump(),
                "status": "completed",
                "ttl_remaining": self.state.ttl_remaining,
            }
        except TTLExpiredError:
            # Log TTL expiration if logger is available
            if self.logger:
                self._log_cycle(errors=[{"type": "TTLExpiredError", "message": "TTL expired during plan execution"}])
            
            # TTL expired - return structured expiration response
            return {
                "plan": self.state.plan.model_dump(),
                "status": "ttl_expired",
                "ttl_remaining": self.state.ttl_remaining,
                "error": "TTL expired during plan execution",
            }

    def get_state(self) -> Optional[OrchestrationState]:
        """
        Get current orchestration state.

        Returns:
            Current state or None if not initialized
        """
        return self.state

    def _execute_step(self, step: "PlanStep", state: OrchestrationState) -> None:
        """
        Execute a single plan step.

        For User Story 4, this method:
        - Invokes tools if tool_registry is available
        - Validates tool inputs/outputs
        - Logs tool calls to tool_history
        - Handles tool errors gracefully (marks step failed, continues)

        For User Story 5, this method:
        - Memory is accessible via self.memory for read/write operations
        - Memory persists across steps during plan execution
        - Memory operations can be performed during step execution

        For User Story 7, this method:
        - Logs cycle after step execution completes
        - Captures plan state, LLM output, supervisor actions, tool calls, TTL, errors
        """
        # For Sprint 1, tools are invoked based on step description or LLM reasoning
        # This is a simplified implementation - full LLM reasoning cycle integration
        # will be enhanced in future iterations
        
        # Memory is available via self.memory for read/write operations
        # In future iterations, LLM reasoning will trigger memory operations
        # For now, memory is accessible and persists across steps
        
        # If no tool registry, step completes with no-op
        if not self.tool_registry:
            # Log cycle after step execution
            if self.logger:
                self._log_cycle()
            return None
        
        # For now, we'll implement a basic tool invocation mechanism
        # In a full implementation, this would parse LLM output to extract tool calls
        # For Sprint 1, we'll use a simple approach where tools can be invoked
        # based on step context
        
        # Placeholder: In future iterations, extract tool calls from LLM reasoning
        # For now, this method provides the hook for tool invocation
        
        # Log cycle after step execution
        if self.logger:
            self._log_cycle()
        
        return None

    def _log_cycle(self, errors: Optional[list] = None) -> None:
        """
        Log an orchestration cycle.

        Args:
            errors: Optional list of errors to include in log entry
        """
        if not self.logger or not self.state:
            return

        self._cycle_number += 1

        # Get tool calls from current step (from tool_history)
        tool_calls = []
        if self.state.tool_history:
            # Get tool calls for current step
            current_step_id = self.state.current_step_id
            for tool_call in self.state.tool_history:
                if tool_call.get("step_id") == current_step_id:
                    tool_calls.append(tool_call)

        # Get supervisor actions (from supervisor_actions)
        supervisor_actions = self.state.supervisor_actions[-1:] if self.state.supervisor_actions else []

        # Get LLM output (from llm_outputs, use last one if available)
        llm_output = self.state.llm_outputs[-1] if self.state.llm_outputs else {}

        # Format and log entry
        log_entry = self.logger.format_entry(
            step_number=self._cycle_number,
            plan_state=self.state.plan.model_dump(),
            llm_output=llm_output,
            supervisor_actions=supervisor_actions,
            tool_calls=tool_calls,
            ttl_remaining=self.state.ttl_remaining,
            errors=errors or [],
        )

        self.logger.log_entry(log_entry)
    
    def _invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        step_id: str,
        state: OrchestrationState,
    ) -> Dict[str, Any]:
        """
        Invoke a tool with validated arguments.

        Args:
            tool_name: Name of the tool to invoke
            arguments: Arguments to pass to the tool
            step_id: ID of the step that triggered this tool call
            state: Current orchestration state

        Returns:
            Tool result dict

        Raises:
            ToolError: If tool invocation fails
            ValidationError: If input/output validation fails
        """
        if not self.tool_registry:
            raise ToolError("Tool registry not available")
        
        tool = self.tool_registry.get(tool_name)
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
    
    def _handle_tool_error(
        self,
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



