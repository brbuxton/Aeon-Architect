"""Unit tests for tool invocation."""

import pytest

from aeon.exceptions import ToolError, ValidationError
from aeon.tools.interface import Tool
from aeon.tools.registry import ToolRegistry


class ValidatingTool(Tool):
    """Tool with validation."""

    name = "validating_tool"
    description = "A tool that validates inputs and outputs"
    input_schema = {
        "type": "object",
        "properties": {
            "value": {"type": "number"}
        },
        "required": ["value"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "number"}
        }
    }

    def invoke(self, **kwargs):
        """Execute tool."""
        if "value" not in kwargs:
            raise ToolError("Missing required argument: value")
        if not isinstance(kwargs["value"], (int, float)):
            raise ToolError("value must be a number")
        return {"result": kwargs["value"] * 2}


class TestToolInvocation:
    """Test tool invocation functionality."""

    def test_invoke_tool_with_valid_args(self):
        """Test invoking a tool with valid arguments."""
        tool = ValidatingTool()
        result = tool.invoke(value=5)
        assert result["result"] == 10

    def test_invoke_tool_with_invalid_args_raises_error(self):
        """Test that invoking tool with invalid args raises ToolError."""
        tool = ValidatingTool()
        with pytest.raises(ToolError):
            tool.invoke()  # Missing required argument

    def test_invoke_tool_through_registry(self):
        """Test invoking a tool retrieved from registry."""
        registry = ToolRegistry()
        tool = ValidatingTool()
        registry.register(tool)
        
        retrieved_tool = registry.get("validating_tool")
        assert retrieved_tool is not None
        result = retrieved_tool.invoke(value=3)
        assert result["result"] == 6

    def test_tool_invocation_is_deterministic(self):
        """Test that tool invocation is deterministic."""
        tool = ValidatingTool()
        result1 = tool.invoke(value=7)
        result2 = tool.invoke(value=7)
        assert result1 == result2

    def test_tool_returns_dict(self):
        """Test that tool invocation returns a dict."""
        tool = ValidatingTool()
        result = tool.invoke(value=1)
        assert isinstance(result, dict)
        assert "result" in result

