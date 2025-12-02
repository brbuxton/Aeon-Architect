"""Plan parser for JSON/YAML plan structures."""

import json
import re
from typing import Any, Dict, Optional, Union

from aeon.exceptions import PlanError, SupervisorError
from aeon.plan.models import Plan


class PlanParser:
    """Parser for JSON/YAML plan structures."""

    def parse(self, plan_data: Union[str, Dict]) -> Plan:
        """
        Parse plan from JSON string or dict.

        Args:
            plan_data: JSON string or dict containing plan data

        Returns:
            Parsed Plan object

        Raises:
            PlanError: If parsing fails or plan structure is invalid
        """
        try:
            # Parse JSON string to dict if needed
            if isinstance(plan_data, str):
                plan_dict = json.loads(plan_data)
            else:
                plan_dict = plan_data

            # Validate required fields
            if not isinstance(plan_dict, dict):
                raise PlanError("Plan data must be a dictionary")
            
            if "goal" not in plan_dict:
                raise PlanError("Plan must have a 'goal' field")
            
            if "steps" not in plan_dict:
                raise PlanError("Plan must have a 'steps' field")
            
            if not isinstance(plan_dict["steps"], list):
                raise PlanError("Plan 'steps' must be a list")
            
            if len(plan_dict["steps"]) == 0:
                raise PlanError("Plan must have at least one step")

            # Create Plan using pydantic (which will validate)
            try:
                plan = Plan(**plan_dict)
                return plan
            except Exception as e:
                raise PlanError(f"Invalid plan structure: {str(e)}") from e

        except json.JSONDecodeError as e:
            raise PlanError(f"Invalid JSON: {str(e)}") from e
        except PlanError:
            raise
        except Exception as e:
            raise PlanError(f"Failed to parse plan: {str(e)}") from e

    def extract_plan_from_llm_response(
        self, response: Dict[str, Any], supervisor: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Extract plan JSON from LLM response.

        Args:
            response: LLM response dict
            supervisor: Optional supervisor for JSON repair

        Returns:
            Plan JSON dict

        Raises:
            PlanError: If plan extraction fails
        """
        text = response.get("text", "")
        
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
            if supervisor:
                try:
                    repaired_json = supervisor.repair_json(text)
                    return repaired_json
                except SupervisorError as se:
                    raise PlanError(
                        f"Failed to extract plan JSON and supervisor repair failed: {str(se)}"
                    ) from se
            raise PlanError(f"Failed to extract plan JSON from response: {str(e)}") from e







