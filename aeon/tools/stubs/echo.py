"""Echo tool stub for testing."""

from typing import Any, Dict

from aeon.exceptions import ToolError
from aeon.tools.interface import Tool


class EchoTool(Tool):
    """Echo tool that returns the input message."""

    name = "echo"
    description = "Echoes back the input message"
    input_schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to echo back"}
        },
        "required": ["message"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "echoed": {"type": "string", "description": "The echoed message"}
        },
        "required": ["echoed"]
    }

    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the echo tool.

        Args:
            **kwargs: Must contain 'message' key

        Returns:
            Dict with 'echoed' key containing the message

        Raises:
            ToolError: If message is missing
        """
        if "message" not in kwargs:
            raise ToolError("Missing required argument: message")
        
        message = kwargs["message"]
        if not isinstance(message, str):
            raise ToolError("message must be a string")
        
        return {"echoed": message}

