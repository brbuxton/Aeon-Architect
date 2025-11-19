"""Unit tests for supervisor repair functionality."""

import json
import pytest

from aeon.exceptions import SupervisorError
from aeon.supervisor.repair import Supervisor
from tests.fixtures.mock_llm import MockLLMAdapter


class TestSupervisorRepair:
    """Test Supervisor JSON repair functionality."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

    @pytest.fixture
    def supervisor(self, mock_llm):
        """Create supervisor instance."""
        system_prompt = "You are a JSON repair assistant. Fix malformed JSON. Return only corrected JSON."
        return Supervisor(llm_adapter=mock_llm, system_prompt=system_prompt)

    def test_repair_json_fixes_malformed_json(self, supervisor, mock_llm):
        """Test that repair_json fixes malformed JSON strings."""
        # Setup mock to return valid JSON
        malformed_json = '{"goal": "test", "steps": [{"step_id": "1"}]'  # Missing closing brace
        valid_json = '{"goal": "test", "steps": [{"step_id": "1"}]}'
        
        # Override generate to return our fixed JSON
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Fix this malformed JSON" in kwargs.get("prompt", ""):
                return {"text": valid_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        result = supervisor.repair_json(malformed_json)
        assert isinstance(result, dict)
        assert result["goal"] == "test"
        assert len(result["steps"]) == 1

    def test_repair_json_retries_on_failure(self, supervisor, mock_llm):
        """Test that repair_json retries up to max_attempts (2) on failure."""
        malformed_json = '{"invalid": json}'
        
        # First attempt returns still-invalid JSON, second succeeds
        mock_llm.responses = {
            f"Fix this malformed JSON: {malformed_json}": '{"still": invalid}',  # First attempt fails
        }
        # Second attempt will use different prompt, simulate it
        call_count = 0
        original_generate = mock_llm.generate
        
        def counting_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"text": '{"still": invalid}'}
            else:
                return {"text": '{"goal": "fixed", "steps": []}'}
        
        mock_llm.generate = counting_generate
        
        result = supervisor.repair_json(malformed_json, max_attempts=2)
        assert call_count == 2  # Should retry once
        assert result["goal"] == "fixed"

    def test_repair_json_raises_after_max_attempts(self, supervisor, mock_llm):
        """Test that repair_json raises SupervisorError after max_attempts exhausted."""
        malformed_json = '{"invalid": json}'
        
        # Mock always returns invalid JSON
        def always_invalid(*args, **kwargs):
            return {"text": '{"still": invalid}'}
        
        mock_llm.generate = always_invalid
        
        with pytest.raises(SupervisorError):
            supervisor.repair_json(malformed_json, max_attempts=2)

    def test_repair_tool_call_fixes_malformed_tool_call(self, supervisor, mock_llm):
        """Test that repair_tool_call fixes malformed tool call dicts."""
        malformed_call = {"tool_name": "echo", "args": "test"}  # Should be "arguments"
        tool_schema = {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string"},
                "arguments": {"type": "object"}
            },
            "required": ["tool_name", "arguments"]
        }
        
        fixed_call = {"tool_name": "echo", "arguments": {"message": "test"}}
        
        # Override generate to return our fixed tool call
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Fix this malformed tool call" in kwargs.get("prompt", ""):
                return {"text": json.dumps(fixed_call)}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        result = supervisor.repair_tool_call(malformed_call, tool_schema)
        assert result["tool_name"] == "echo"
        assert "arguments" in result

    def test_repair_plan_fixes_malformed_plan(self, supervisor, mock_llm):
        """Test that repair_plan fixes malformed plan structures."""
        malformed_plan = {"goal": "test"}  # Missing "steps"
        
        fixed_plan = {"goal": "test", "steps": [{"step_id": "1", "description": "Step 1", "status": "pending"}]}
        
        # Override generate to return our fixed plan
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Fix this malformed plan" in kwargs.get("prompt", ""):
                return {"text": json.dumps(fixed_plan)}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        result = supervisor.repair_plan(malformed_plan)
        assert result["goal"] == "test"
        assert "steps" in result
        assert len(result["steps"]) == 1

    def test_repair_missing_tool_step_repairs_step_with_missing_tool(self, supervisor, mock_llm):
        """Test repair_missing_tool_step repairs step with missing tool reference (T093)."""
        from aeon.plan.models import PlanStep
        
        # Step with missing tool
        step = PlanStep(
            step_id="step1",
            description="Calculate sum of numbers",
            tool="nonexistent_calculator",
            errors=["Tool 'nonexistent_calculator' not found in registry"],
        )
        
        # Available tools
        from aeon.tools.interface import Tool
        
        class MockTool(Tool):
            def __init__(self, name):
                self.name = name
                self.description = f"{name} tool"
                self.input_schema = {"type": "object", "properties": {}}
                self.output_schema = {"type": "object", "properties": {}}
            
            def invoke(self, **kwargs):
                return {"result": "success"}
        
        available_tools = [
            {
                "name": "calculator",
                "description": "Calculator tool for math operations",
                "input_schema": {"type": "object", "properties": {}},
                "output_schema": {"type": "object", "properties": {}},
            }
        ]
        
        plan_goal = "Calculate mathematical operations"
        
        # Mock LLM to return repaired step with valid tool
        repaired_step_json = '{"step_id": "step1", "description": "Calculate sum of numbers", "tool": "calculator", "status": "pending"}'
        
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Repair this step" in kwargs.get("prompt", ""):
                return {"text": repaired_step_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        # Repair the step
        repaired_step = supervisor.repair_missing_tool_step(step, available_tools, plan_goal)
        
        assert isinstance(repaired_step, PlanStep)
        assert repaired_step.tool == "calculator"  # Should be repaired to valid tool
        assert repaired_step.step_id == "step1"  # Step ID preserved
        assert repaired_step.errors is None or len(repaired_step.errors) == 0  # Errors cleared

    def test_repair_missing_tool_step_clears_errors_on_success(self, supervisor, mock_llm):
        """Test repair_missing_tool_step clears step.errors on successful repair."""
        from aeon.plan.models import PlanStep
        
        step = PlanStep(
            step_id="step1",
            description="Use calculator",
            tool="missing_tool",
            errors=["Tool 'missing_tool' not found"],
        )
        
        available_tools = [
            {
                "name": "calculator",
                "description": "Calculator tool",
                "input_schema": {},
                "output_schema": {},
            }
        ]
        
        repaired_step_json = '{"step_id": "step1", "description": "Use calculator", "tool": "calculator", "status": "pending"}'
        
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            if "Repair this step" in kwargs.get("prompt", ""):
                return {"text": repaired_step_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        repaired_step = supervisor.repair_missing_tool_step(step, available_tools, "Test goal")
        
        # Errors should be cleared on successful repair
        assert repaired_step.errors is None or len(repaired_step.errors) == 0

    def test_repair_missing_tool_step_includes_tool_registry_in_prompt(self, supervisor, mock_llm):
        """Test repair_missing_tool_step includes tool registry in prompt."""
        from aeon.plan.models import PlanStep
        
        step = PlanStep(
            step_id="step1",
            description="Calculate",
            tool="missing",
        )
        
        available_tools = [
            {
                "name": "calculator",
                "description": "Calculator",
                "input_schema": {},
                "output_schema": {},
            }
        ]
        
        repaired_step_json = '{"step_id": "step1", "description": "Calculate", "tool": "calculator", "status": "pending"}'
        
        captured_prompt = None
        original_generate = mock_llm.generate
        def mock_generate(*args, **kwargs):
            nonlocal captured_prompt
            if "Repair this step" in kwargs.get("prompt", ""):
                captured_prompt = kwargs.get("prompt", "")
                return {"text": repaired_step_json}
            return original_generate(*args, **kwargs)
        mock_llm.generate = mock_generate
        
        supervisor.repair_missing_tool_step(step, available_tools, "Test goal")
        
        # Verify tool registry is included in prompt
        assert captured_prompt is not None
        assert "calculator" in captured_prompt or "available tools" in captured_prompt.lower()

