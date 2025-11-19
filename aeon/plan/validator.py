"""Plan validator for schema validation."""

from typing import Any, Dict

from aeon.exceptions import PlanError
from aeon.plan.models import Plan, PlanStep, StepStatus
from aeon.validation.schema import Validator


class PlanValidator(Validator):
    """Validator for plan structures."""

    def validate(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema: JSON schema to validate against

        Returns:
            True if valid

        Raises:
            PlanError: If validation fails
        """
        # For now, use pydantic validation
        # Can be extended with jsonschema validation if needed
        try:
            if isinstance(data, dict):
                Plan(**data)
            elif isinstance(data, Plan):
                # Plan is already validated
                pass
            else:
                raise PlanError(f"Invalid data type for plan: {type(data)}")
            return True
        except Exception as e:
            raise PlanError(f"Plan validation failed: {str(e)}") from e

    def validate_plan(self, plan_data: Dict[str, Any]) -> bool:
        """
        Validate plan structure.

        Args:
            plan_data: Plan data dict

        Returns:
            True if valid

        Raises:
            PlanError: If validation fails
        """
        try:
            plan = Plan(**plan_data)
            
            # Validate step status values (Pydantic already validates enum, but check value is valid)
            for step in plan.steps:
                # With use_enum_values=True, step.status is a string, so check if it's a valid enum value
                if step.status not in [s.value for s in StepStatus]:
                    raise PlanError(f"Invalid step status: {step.status}")
            
            # Validate step IDs are unique (handled by Plan model)
            # Additional validations can be added here
            
            return True
        except Exception as e:
            if isinstance(e, PlanError):
                raise
            raise PlanError(f"Plan validation failed: {str(e)}") from e

    def validate_tool_call(self, tool_call: Dict[str, Any], tool_schema: Dict[str, Any]) -> bool:
        """
        Validate tool call against tool schema.

        This is not used for plan validation, but required by base class.

        Args:
            tool_call: Tool call dict
            tool_schema: Tool input schema

        Returns:
            True if valid

        Raises:
            PlanError: If validation fails
        """
        raise NotImplementedError("Use ToolValidator for tool call validation")


