"""Tool registry for managing tool registration and lookup."""

from typing import Any, Dict, List, Optional

from aeon.tools.interface import Tool


class ToolRegistry:
    """Tool registration and lookup."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool name already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            List of tool dicts containing name, description, input_schema, output_schema,
            sorted alphabetically by tool name.
        """
        tools = []
        for tool_name in sorted(self._tools.keys()):
            tool = self._tools[tool_name]
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "output_schema": tool.output_schema,
                }
            )
        return tools

    def unregister(self, name: str) -> None:
        """
        Unregister a tool.

        Args:
            name: Tool name to unregister
        """
        if name in self._tools:
            del self._tools[name]

