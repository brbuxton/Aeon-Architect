"""Plan parser for JSON/YAML plan structures."""

import json
from typing import Dict, Union

from aeon.exceptions import PlanError
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







