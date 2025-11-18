"""Tool interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from aeon.exceptions import ToolError


class Tool(ABC):
    """Abstract interface for tools."""

    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON schema
    output_schema: Dict[str, Any]  # JSON schema

    @abstractmethod
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with validated arguments.

        Args:
            **kwargs: Arguments validated against input_schema

        Returns:
            Result dict validated against output_schema

        Raises:
            ToolError: On execution failure
        """
        pass

    def validate_input(self, **kwargs) -> bool:
        """Validate input against input_schema (default implementation uses pydantic)."""
        # Default implementation - subclasses can override
        return True

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """Validate output against output_schema (default implementation uses pydantic)."""
        # Default implementation - subclasses can override
        return True


