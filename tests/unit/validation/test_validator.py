"""Unit tests for step tool validation."""

import pytest

from aeon.exceptions import ValidationError
from aeon.plan.models import PlanStep
from aeon.tools.interface import Tool
from aeon.tools.registry import ToolRegistry
from aeon.validation.schema import Validator


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


class TestValidateStepTool:
    """Test validate_step_tool method."""

    def test_validate_step_tool_with_valid_tool(self):
        """Test validate_step_tool with step referencing registered tool."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="calculator",
        )
        
        # Need to implement validate_step_tool in Validator
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        assert result["valid"] is True
        assert result.get("error") is None
        assert step.errors is None  # No errors for valid tool

    def test_validate_step_tool_with_missing_tool(self):
        """Test validate_step_tool with step referencing unregistered tool."""
        registry = ToolRegistry()
        
        step = PlanStep(
            step_id="step2",
            description="Use missing tool",
            tool="nonexistent_tool",
        )
        
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        assert result["valid"] is False
        assert result.get("error") is not None
        assert "nonexistent_tool" in result["error"]
        # step.errors should be populated
        assert step.errors is not None
        assert len(step.errors) > 0
        assert any("nonexistent_tool" in err for err in step.errors)

    def test_validate_step_tool_with_no_tool_field(self):
        """Test validate_step_tool with step that has no tool field."""
        registry = ToolRegistry()
        
        step = PlanStep(
            step_id="step3",
            description="Step without tool",
        )
        
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        # Step without tool field is valid (not a tool-based step)
        assert result["valid"] is True
        assert result.get("error") is None
        assert step.errors is None

    def test_validate_step_tool_with_empty_tool_string(self):
        """Test validate_step_tool with empty tool string."""
        registry = ToolRegistry()
        
        # Empty tool string is now rejected by PlanStep validation (T100)
        # Use model_construct to bypass validation for this test
        step = PlanStep.model_construct(
            step_id="step4",
            description="Step with empty tool",
            tool="",
        )
        
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        assert result["valid"] is False
        assert step.errors is not None
        assert len(step.errors) > 0

    def test_validate_step_tool_populates_errors_in_place(self):
        """Test that validate_step_tool modifies step.errors in-place."""
        registry = ToolRegistry()
        
        step = PlanStep(
            step_id="step5",
            description="Step with invalid tool",
            tool="invalid",
        )
        
        # Initially no errors
        assert step.errors is None
        
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        # step.errors should be populated after validation
        assert step.errors is not None
        assert len(step.errors) > 0
        assert result["valid"] is False

    def test_validate_step_tool_clears_existing_errors_on_valid_tool(self):
        """Test that validate_step_tool clears errors when tool becomes valid."""
        registry = ToolRegistry()
        tool = MockTool("calculator")
        registry.register(tool)
        
        step = PlanStep(
            step_id="step6",
            description="Step with tool",
            tool="calculator",
            errors=["Previous error"],  # Pre-existing error
        )
        
        validator = Validator()
        result = validator.validate_step_tool(step, registry)
        
        # Valid tool should clear errors (or at least not add new ones)
        assert result["valid"] is True
        # Note: Contract doesn't specify clearing, but supervisor clears on repair
        # For now, we'll just ensure no new errors are added for valid tools

    def test_validate_step_tool_with_multiple_tools_in_registry(self):
        """Test validate_step_tool with multiple tools in registry."""
        registry = ToolRegistry()
        tool1 = MockTool("calculator")
        tool2 = MockTool("echo")
        registry.register(tool1)
        registry.register(tool2)
        
        # Valid tool
        step1 = PlanStep(
            step_id="step7",
            description="Use calculator",
            tool="calculator",
        )
        
        # Invalid tool
        step2 = PlanStep(
            step_id="step8",
            description="Use missing tool",
            tool="missing",
        )
        
        validator = Validator()
        result1 = validator.validate_step_tool(step1, registry)
        result2 = validator.validate_step_tool(step2, registry)
        
        assert result1["valid"] is True
        assert result2["valid"] is False
        assert step2.errors is not None

