"""Calculator tool stub for testing."""

from typing import Any, Dict

from aeon.exceptions import ToolError
from aeon.tools.interface import Tool


class CalculatorTool(Tool):
    """Calculator tool that performs basic arithmetic operations."""

    name = "calculator"
    description = "Performs basic arithmetic operations (add, subtract, multiply, divide)"
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "Operation to perform"
            },
            "a": {"type": "number", "description": "First number"},
            "b": {"type": "number", "description": "Second number"}
        },
        "required": ["operation", "a", "b"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "number", "description": "Result of the operation"}
        },
        "required": ["result"]
    }

    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the calculator tool.

        Args:
            **kwargs: Must contain 'operation', 'a', and 'b' keys

        Returns:
            Dict with 'result' key containing the calculation result

        Raises:
            ToolError: If arguments are missing or invalid
        """
        if "operation" not in kwargs or "a" not in kwargs or "b" not in kwargs:
            raise ToolError("Missing required arguments: operation, a, b")
        
        operation = kwargs["operation"]
        a = kwargs["a"]
        b = kwargs["b"]
        
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ToolError("a and b must be numbers")
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ToolError("Division by zero")
            result = a / b
        else:
            raise ToolError(f"Invalid operation: {operation}")
        
        return {"result": result}

