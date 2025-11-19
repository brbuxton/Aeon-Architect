"""Schema validation base classes."""

from abc import ABC
from typing import Any, Dict, Optional

from aeon.exceptions import ValidationError
from aeon.plan.models import PlanStep
from aeon.tools.registry import ToolRegistry


class Validator(ABC):
    """Base class for schema validators."""

    def validate(self, data: Any, schema: Dict[str, Any]) -> bool:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            schema: JSON schema to validate against

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        # Base implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement validate()")

    def validate_plan(self, plan_data: Dict[str, Any]) -> bool:
        """
        Validate plan structure.

        Args:
            plan_data: Plan data dict

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        raise NotImplementedError("Subclasses must implement validate_plan()")

    def validate_tool_call(self, tool_call: Dict[str, Any], tool_schema: Dict[str, Any]) -> bool:
        """
        Validate tool call against tool schema.

        Args:
            tool_call: Tool call dict
            tool_schema: Tool input schema

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        raise NotImplementedError("Subclasses must implement validate_tool_call()")

    def validate_step_tool(
        self,
        step: PlanStep,
        tool_registry: ToolRegistry,
    ) -> Dict[str, Any]:
        """
        Validate that step references a registered tool.

        Populates step.errors with error messages if validation fails.
        The step object is modified in-place (errors field is set).

        Args:
            step: PlanStep object to validate (modified in-place)
            tool_registry: Tool registry to check against

        Returns:
            Dict with:
                - "valid": bool - True if step.tool is valid or step has no tool field
                - "error": Optional[str] - error message if invalid (also added to step.errors)

        Raises:
            ValidationError: If step structure is invalid (not tool-related)

        Note:
            This method modifies step.errors in-place. If step.tool is missing or invalid,
            step.errors is populated with error messages (e.g., "Tool 'X' not found in registry").
            Supervisor repair MUST read step.errors and clear it on successful repair.
        """
        # If step has no tool field (None), it's valid (not a tool-based step)
        if step.tool is None:
            return {"valid": True, "error": None}

        # Empty tool string is invalid
        if step.tool.strip() == "":
            error_msg = "Tool field cannot be empty"
            if step.errors is None:
                step.errors = []
            step.errors.append(error_msg)
            return {"valid": False, "error": error_msg}

        # Check if tool exists in registry
        tool = tool_registry.get(step.tool)
        if tool is None:
            error_msg = f"Tool '{step.tool}' not found in registry"
            if step.errors is None:
                step.errors = []
            step.errors.append(error_msg)
            return {"valid": False, "error": error_msg}

        # Tool is valid
        return {"valid": True, "error": None}



