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
        """
        Validate input against input_schema.
        
        Args:
            **kwargs: Arguments to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        from aeon.exceptions import ValidationError
        import jsonschema
        
        try:
            jsonschema.validate(instance=kwargs, schema=self.input_schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValidationError(f"Input validation failed: {str(e)}") from e

    def validate_output(self, result: Dict[str, Any]) -> bool:
        """
        Validate output against output_schema.
        
        Args:
            result: Result dict to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        from aeon.exceptions import ValidationError
        import jsonschema
        
        try:
            jsonschema.validate(instance=result, schema=self.output_schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValidationError(f"Output validation failed: {str(e)}") from e



