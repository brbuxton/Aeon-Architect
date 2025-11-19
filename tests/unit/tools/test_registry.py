"""Unit tests for ToolRegistry."""

import pytest

from aeon.tools.interface import Tool
from aeon.tools.registry import ToolRegistry


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, name: str, description: str = "Test tool"):
        self.name = name
        self.description = description
        self.input_schema = {"type": "object", "properties": {}}
        self.output_schema = {"type": "object", "properties": {}}

    def invoke(self, **kwargs):
        """Mock invoke."""
        return {"result": "success"}


class TestToolRegistry:
    """Test ToolRegistry implementation."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register(tool)
        assert registry.get("test_tool") == tool

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering duplicate tool raises ValueError."""
        registry = ToolRegistry()
        tool1 = MockTool("test_tool")
        tool2 = MockTool("test_tool")
        registry.register(tool1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(tool2)

    def test_get_existing_tool(self):
        """Test getting an existing tool."""
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register(tool)
        retrieved = registry.get("test_tool")
        assert retrieved == tool

    def test_get_nonexistent_tool_returns_none(self):
        """Test that getting nonexistent tool returns None."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all_returns_all_tools(self):
        """Test that list_all() returns all registered tools."""
        registry = ToolRegistry()
        tool1 = MockTool("tool_a", "First tool")
        tool2 = MockTool("tool_b", "Second tool")
        tool3 = MockTool("tool_c", "Third tool")
        
        registry.register(tool3)  # Register out of order
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_all()
        assert len(tools) == 3
        
        # Should be sorted alphabetically
        assert tools[0]["name"] == "tool_a"
        assert tools[1]["name"] == "tool_b"
        assert tools[2]["name"] == "tool_c"

    def test_list_all_includes_all_required_fields(self):
        """Test that list_all() includes name, description, input_schema, output_schema."""
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test description")
        tool.input_schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        tool.output_schema = {"type": "object", "properties": {"y": {"type": "number"}}}
        registry.register(tool)
        
        tools = registry.list_all()
        assert len(tools) == 1
        tool_info = tools[0]
        assert tool_info["name"] == "test_tool"
        assert tool_info["description"] == "Test description"
        assert tool_info["input_schema"] == tool.input_schema
        assert tool_info["output_schema"] == tool.output_schema

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register(tool)
        assert registry.get("test_tool") == tool
        
        registry.unregister("test_tool")
        assert registry.get("test_tool") is None

    def test_unregister_nonexistent_tool_no_error(self):
        """Test that unregistering nonexistent tool doesn't raise error."""
        registry = ToolRegistry()
        registry.unregister("nonexistent")  # Should not raise

    def test_export_tools_for_llm_returns_tool_list(self):
        """Test export_tools_for_llm returns list of tools formatted for LLM (T094)."""
        registry = ToolRegistry()
        tool1 = MockTool("calculator", "Calculator tool")
        tool2 = MockTool("echo", "Echo tool")
        registry.register(tool1)
        registry.register(tool2)
        
        exported = registry.export_tools_for_llm()
        
        assert isinstance(exported, list)
        assert len(exported) == 2
        # Should be sorted alphabetically
        assert exported[0]["name"] == "calculator"
        assert exported[1]["name"] == "echo"

    def test_export_tools_for_llm_includes_all_required_fields(self):
        """Test export_tools_for_llm includes name, description, input_schema, output_schema."""
        registry = ToolRegistry()
        tool = MockTool("test_tool", "Test description")
        tool.input_schema = {"type": "object", "properties": {"value": {"type": "string"}}}
        tool.output_schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        registry.register(tool)
        
        exported = registry.export_tools_for_llm()
        
        assert len(exported) == 1
        tool_info = exported[0]
        assert "name" in tool_info
        assert "description" in tool_info
        assert "input_schema" in tool_info
        assert "output_schema" in tool_info
        assert tool_info["name"] == "test_tool"
        assert tool_info["description"] == "Test description"
        assert tool_info["input_schema"] == tool.input_schema
        assert tool_info["output_schema"] == tool.output_schema

    def test_export_tools_for_llm_may_include_example(self):
        """Test export_tools_for_llm may include example field (optional)."""
        registry = ToolRegistry()
        tool = MockTool("test_tool")
        registry.register(tool)
        
        exported = registry.export_tools_for_llm()
        
        # Example is optional, but structure should allow it
        assert len(exported) == 1
        tool_info = exported[0]
        # Example field may or may not be present
        # Just verify the structure is correct

    def test_export_tools_for_llm_returns_empty_list_when_no_tools(self):
        """Test export_tools_for_llm returns empty list when no tools registered."""
        registry = ToolRegistry()
        exported = registry.export_tools_for_llm()
        assert exported == []

