"""Contract tests for Tool interface."""

import pytest

from aeon.exceptions import ToolError
from aeon.tools.interface import Tool


class TestTool(Tool):
    """Test tool that implements Tool interface."""

    name = "test_tool"
    description = "A test tool for contract testing"
    input_schema = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    }

    def invoke(self, **kwargs) -> dict:
        """Execute the tool."""
        if "input" not in kwargs:
            raise ToolError("Missing required argument: input")
        return {"result": f"Processed: {kwargs['input']}"}


class TestToolInterface:
    """Contract tests verifying Tool interface compliance."""

    def test_tool_has_required_attributes(self):
        """Test that Tool implementation has required attributes."""
        tool = TestTool()
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
        assert hasattr(tool, "input_schema")
        assert hasattr(tool, "output_schema")
        assert tool.name == "test_tool"
        assert isinstance(tool.description, str)
        assert isinstance(tool.input_schema, dict)
        assert isinstance(tool.output_schema, dict)

    def test_tool_invoke_is_callable(self):
        """Test that Tool.invoke() is callable."""
        tool = TestTool()
        assert callable(tool.invoke)

    def test_tool_invoke_returns_dict(self):
        """Test that Tool.invoke() returns a dict."""
        tool = TestTool()
        result = tool.invoke(input="test")
        assert isinstance(result, dict)
        assert "result" in result

    def test_tool_invoke_raises_tool_error_on_failure(self):
        """Test that Tool.invoke() raises ToolError on failure."""
        tool = TestTool()
        with pytest.raises(ToolError):
            tool.invoke()  # Missing required argument

    def test_tool_is_deterministic(self):
        """Test that Tool.invoke() is deterministic (same inputs → same outputs)."""
        tool = TestTool()
        result1 = tool.invoke(input="test")
        result2 = tool.invoke(input="test")
        assert result1 == result2

    def test_tool_validate_input_exists(self):
        """Test that Tool has validate_input() method."""
        tool = TestTool()
        assert hasattr(tool, "validate_input")
        assert callable(tool.validate_input)

    def test_tool_validate_output_exists(self):
        """Test that Tool has validate_output() method."""
        tool = TestTool()
        assert hasattr(tool, "validate_output")
        assert callable(tool.validate_output)

