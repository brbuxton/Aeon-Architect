"""Supervisor for repairing malformed LLM outputs."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from aeon.exceptions import SupervisorError
from aeon.llm.interface import LLMAdapter
from aeon.plan.models import PlanStep


class Supervisor:
    """Supervisor for repairing malformed LLM outputs."""

    def __init__(self, llm_adapter: LLMAdapter, system_prompt: Optional[str] = None) -> None:
        """
        Initialize supervisor.

        Args:
            llm_adapter: LLM adapter to use for repair
            system_prompt: Reduced system prompt for repair focus (optional)
        """
        self.llm_adapter = llm_adapter
        self.system_prompt = system_prompt or self._get_default_system_prompt()

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for JSON repair."""
        return """You are a JSON repair assistant. Fix malformed JSON, tool calls, or plan structures.
Return only the corrected JSON. Do not add new fields, tools, or semantic meaning.
Your job is to correct syntax and structure only."""

    def repair_json(
        self,
        malformed_json: str,
        expected_schema: Optional[Dict[str, Any]] = None,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed JSON.

        Args:
            malformed_json: Malformed JSON string
            expected_schema: Expected JSON schema (optional)
            max_attempts: Maximum repair attempts (default 2)

        Returns:
            Repaired JSON as dict

        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        prompt = self._construct_json_repair_prompt(malformed_json, expected_schema)
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.llm_adapter.generate(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=2048,
                    temperature=0.3,  # Lower temperature for repair
                )
                
                # Extract JSON from response
                repaired_text = response.get("text", "").strip()
                repaired_dict = self._extract_json_from_text(repaired_text)
                
                # Validate it's valid JSON
                json.dumps(repaired_dict)  # Will raise if invalid
                
                return repaired_dict
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Failed to repair JSON after {max_attempts} attempts: {str(e)}"
                    ) from e
                # Continue to next attempt
                continue
            except Exception as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Unexpected error during JSON repair after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
        
        raise SupervisorError(f"Failed to repair JSON after {max_attempts} attempts")

    def repair_tool_call(
        self,
        malformed_call: Dict[str, Any],
        tool_schema: Dict[str, Any],
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed tool call.

        Args:
            malformed_call: Malformed tool call dict
            tool_schema: Tool input schema
            max_attempts: Maximum repair attempts (default 2)

        Returns:
            Repaired tool call dict

        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        prompt = self._construct_tool_call_repair_prompt(malformed_call, tool_schema)
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.llm_adapter.generate(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=2048,
                    temperature=0.3,
                )
                
                repaired_text = response.get("text", "").strip()
                repaired_dict = self._extract_json_from_text(repaired_text)
                
                # Validate against tool schema (basic check)
                if "tool_name" not in repaired_dict:
                    raise ValueError("Repaired tool call missing 'tool_name'")
                
                return repaired_dict
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Failed to repair tool call after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
            except Exception as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Unexpected error during tool call repair after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
        
        raise SupervisorError(f"Failed to repair tool call after {max_attempts} attempts")

    def repair_plan(
        self,
        malformed_plan: Dict[str, Any],
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed plan structure.

        Args:
            malformed_plan: Malformed plan dict
            max_attempts: Maximum repair attempts (default 2)

        Returns:
            Repaired plan dict

        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        prompt = self._construct_plan_repair_prompt(malformed_plan)
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = self.llm_adapter.generate(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=2048,
                    temperature=0.3,
                )
                
                repaired_text = response.get("text", "").strip()
                repaired_dict = self._extract_json_from_text(repaired_text)
                
                # Validate plan structure
                if "goal" not in repaired_dict:
                    raise ValueError("Repaired plan missing 'goal'")
                if "steps" not in repaired_dict:
                    raise ValueError("Repaired plan missing 'steps'")
                
                return repaired_dict
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Failed to repair plan after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
            except Exception as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Unexpected error during plan repair after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
        
        raise SupervisorError(f"Failed to repair plan after {max_attempts} attempts")

    def _construct_json_repair_prompt(self, malformed_json: str, expected_schema: Optional[Dict[str, Any]] = None) -> str:
        """Construct prompt for JSON repair."""
        prompt = f"Fix this malformed JSON: {malformed_json}"
        if expected_schema:
            prompt += f"\n\nExpected schema: {json.dumps(expected_schema, indent=2)}"
        prompt += "\n\nReturn only the corrected JSON, no explanation."
        return prompt

    def _construct_tool_call_repair_prompt(self, malformed_call: Dict[str, Any], tool_schema: Dict[str, Any]) -> str:
        """Construct prompt for tool call repair."""
        return f"""Fix this malformed tool call: {json.dumps(malformed_call, indent=2)}

Tool schema: {json.dumps(tool_schema, indent=2)}

Return only the corrected tool call JSON, no explanation."""

    def _construct_plan_repair_prompt(self, malformed_plan: Dict[str, Any]) -> str:
        """Construct prompt for plan repair."""
        return f"""Fix this malformed plan: {json.dumps(malformed_plan, indent=2)}

A valid plan must have:
- "goal": string
- "steps": array of step objects with "step_id", "description", "status"

Return only the corrected plan JSON, no explanation."""

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON dict from text response.

        Args:
            text: Text that may contain JSON

        Returns:
            Extracted JSON dict

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        import re
        
        # Try to find JSON block
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire text
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"No valid JSON found in text: {text[:100]}", text, 0) from e

    def repair_missing_tool_step(
        self,
        step: PlanStep,
        available_tools: List[Dict[str, Any]],
        plan_goal: str,
        max_attempts: int = 2,
    ) -> PlanStep:
        """
        Repair step with missing or invalid tool reference.

        Args:
            step: PlanStep with missing/invalid tool
            available_tools: List of available tools (from ToolRegistry.export_tools_for_llm())
            plan_goal: Overall plan goal for context
            max_attempts: Maximum repair attempts (default 2)

        Returns:
            Repaired PlanStep with valid tool reference

        Raises:
            SupervisorError: If repair fails after max_attempts

        Note:
            This method reads step.errors and clears it on successful repair.
            The repaired step will have a valid tool reference from available_tools.
        """
        prompt = self._construct_missing_tool_repair_prompt(step, available_tools, plan_goal)

        for attempt in range(1, max_attempts + 1):
            try:
                response = self.llm_adapter.generate(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=2048,
                    temperature=0.3,
                )

                repaired_text = response.get("text", "").strip()
                repaired_dict = self._extract_json_from_text(repaired_text)

                # Validate repaired step structure
                if "step_id" not in repaired_dict:
                    raise ValueError("Repaired step missing 'step_id'")
                if "description" not in repaired_dict:
                    raise ValueError("Repaired step missing 'description'")

                # Validate tool reference is in available tools
                if "tool" in repaired_dict:
                    tool_name = repaired_dict["tool"]
                    tool_names = [t["name"] for t in available_tools]
                    if tool_name not in tool_names:
                        raise ValueError(f"Repaired step references tool '{tool_name}' not in available tools")

                # Create repaired PlanStep
                repaired_step = PlanStep(
                    step_id=repaired_dict.get("step_id", step.step_id),
                    description=repaired_dict.get("description", step.description),
                    tool=repaired_dict.get("tool"),
                    agent=repaired_dict.get("agent"),
                    status=repaired_dict.get("status", step.status),
                    errors=None,  # Clear errors on successful repair
                )

                return repaired_step

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Failed to repair missing-tool step after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue
            except Exception as e:
                if attempt == max_attempts:
                    raise SupervisorError(
                        f"Unexpected error during missing-tool step repair after {max_attempts} attempts: {str(e)}"
                    ) from e
                continue

        raise SupervisorError(f"Failed to repair missing-tool step after {max_attempts} attempts")

    def _construct_missing_tool_repair_prompt(
        self,
        step: PlanStep,
        available_tools: List[Dict[str, Any]],
        plan_goal: str,
    ) -> str:
        """
        Construct prompt for missing-tool step repair.

        Args:
            step: PlanStep with missing/invalid tool
            available_tools: List of available tools
            plan_goal: Overall plan goal

        Returns:
            Prompt string
        """
        # Build tools list for prompt
        tools_text = "Available tools:\n"
        for tool in available_tools:
            tools_text += f"- {tool['name']}: {tool.get('description', 'No description')}\n"
            if tool.get('input_schema'):
                tools_text += f"  Input schema: {json.dumps(tool['input_schema'], indent=2)}\n"

        # Build step context
        step_context = step.model_dump()
        if step.errors:
            step_context["errors"] = step.errors

        prompt = f"""Repair this step to reference a valid tool from the available list. Do not invent tools.

Plan goal: {plan_goal}

Step to repair:
{json.dumps(step_context, indent=2)}

{tools_text}

Return only the corrected step JSON with a valid tool reference from the available tools list.
The step must have: step_id, description, and tool (referencing one of the available tools).
Clear any errors field on successful repair."""
        return prompt

