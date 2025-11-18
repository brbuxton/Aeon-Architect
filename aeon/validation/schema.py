"""Schema validation base classes."""

from abc import ABC
from typing import Any, Dict

from aeon.exceptions import ValidationError


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



