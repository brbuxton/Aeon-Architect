"""Integration tests for tool invocation in orchestration loop."""

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.tools.registry import ToolRegistry
from aeon.tools.stubs.calculator import CalculatorTool
from aeon.tools.stubs.echo import EchoTool
from tests.fixtures.mock_llm import MockLLMAdapter


class TestToolInvocation:
    """Integration tests for tool invocation in orchestration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def tool_registry(self):
        """Create tool registry with stub tools."""
        registry = ToolRegistry()
        registry.register(EchoTool())
        registry.register(CalculatorTool())
        return registry

    @pytest.fixture
    def orchestrator(self, mock_llm, tool_registry):
        """Create orchestrator with tool registry."""
        memory = InMemoryKVStore()
        return Orchestrator(
            llm=mock_llm,
            memory=memory,
            ttl=10,
            tool_registry=tool_registry
        )

    def test_tool_registry_contains_registered_tools(self, tool_registry):
        """Test that tool registry contains registered tools."""
        echo_tool = tool_registry.get("echo")
        assert echo_tool is not None
        assert echo_tool.name == "echo"
        
        calc_tool = tool_registry.get("calculator")
        assert calc_tool is not None
        assert calc_tool.name == "calculator"

    def test_tool_can_be_invoked_directly(self, tool_registry):
        """Test that registered tools can be invoked directly."""
        echo_tool = tool_registry.get("echo")
        result = echo_tool.invoke(message="Hello, world!")
        assert result["echoed"] == "Hello, world!"
        
        calc_tool = tool_registry.get("calculator")
        result = calc_tool.invoke(operation="add", a=5, b=3)
        assert result["result"] == 8

    def test_tool_input_validation(self, tool_registry):
        """Test that tool input validation works."""
        echo_tool = tool_registry.get("echo")
        
        # Valid input
        echo_tool.validate_input(message="test")
        
        # Invalid input - missing required field
        from aeon.exceptions import ValidationError
        with pytest.raises(ValidationError):
            echo_tool.validate_input()

    def test_tool_output_validation(self, tool_registry):
        """Test that tool output validation works."""
        echo_tool = tool_registry.get("echo")
        result = echo_tool.invoke(message="test")
        
        # Valid output
        echo_tool.validate_output(result)
        
        # Invalid output - missing required field
        from aeon.exceptions import ValidationError
        with pytest.raises(ValidationError):
            echo_tool.validate_output({"invalid": "output"})

    def test_tool_registry_list_all(self, tool_registry):
        """Test that list_all() returns all tools sorted alphabetically."""
        tools = tool_registry.list_all()
        assert len(tools) == 2
        assert tools[0]["name"] == "calculator"  # Alphabetically first
        assert tools[1]["name"] == "echo"

