"""Core orchestrator for LLM orchestration loop."""

from typing import Any, Dict, Optional

from aeon.exceptions import LLMError, PlanError, TTLExpiredError
from aeon.kernel.state import OrchestrationState
from aeon.llm.interface import LLMAdapter
from aeon.memory.interface import Memory
from aeon.plan.models import Plan
from aeon.plan.parser import PlanParser
from aeon.plan.validator import PlanValidator


class Orchestrator:
    """Core orchestrator for LLM orchestration loop."""

    def __init__(
        self,
        llm: LLMAdapter,
        memory: Optional[Memory] = None,
        ttl: int = 10,
        tool_registry: Optional[Any] = None,
        supervisor: Optional[Any] = None,
    ) -> None:
        """
        Initialize orchestrator.

        Args:
            llm: LLM adapter for generation
            memory: Memory interface (optional)
            ttl: Time-to-live in cycles (default 10)
            tool_registry: Tool registry (optional, for later phases)
            supervisor: Supervisor for error repair (optional, for later phases)
        """
        self.llm = llm
        self.memory = memory
        self.ttl = ttl
        self.tool_registry = tool_registry
        self.supervisor = supervisor
        self.parser = PlanParser()
        self.validator = PlanValidator()
        self.state: Optional[OrchestrationState] = None

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
            plan = self.parser.parse(plan_json)
            self.validator.validate_plan(plan.model_dump())

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
        
        # Try to extract JSON from text
        # This is a simplified extraction - can be enhanced with better JSON parsing
        import json
        import re
        
        # Look for JSON block in response
        json_match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # If no JSON found, try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise PlanError(f"Failed to extract plan JSON from response: {str(e)}") from e

    def execute(self, request: str) -> Dict[str, Any]:
        """
        Execute a request: generate plan and execute it.

        Args:
            request: Natural language request

        Returns:
            Execution result dict

        Raises:
            TTLExpiredError: If TTL expires during execution
            LLMError: If LLM operations fail
            PlanError: If plan operations fail
        """
        # Generate plan
        plan = self.generate_plan(request)
        
        # Initialize state
        self.state = OrchestrationState(plan=plan, ttl_remaining=self.ttl)
        
        # Execute plan (to be implemented in User Story 2)
        # For now, return plan
        return {
            "plan": plan.model_dump(),
            "status": "plan_generated",
            "ttl_remaining": self.state.ttl_remaining,
        }

    def get_state(self) -> Optional[OrchestrationState]:
        """
        Get current orchestration state.

        Returns:
            Current state or None if not initialized
        """
        return self.state


