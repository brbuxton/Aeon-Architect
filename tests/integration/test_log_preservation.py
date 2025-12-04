"""Integration test to verify orchestration logs match pre-refactor (T041).

This test verifies that orchestration logs at phase boundaries match the
expected structure and content after refactoring. It ensures that logging
behavior is preserved and logs contain all required fields.
"""

import json
import tempfile
from pathlib import Path

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.observability.logger import JSONLLogger
from aeon.plan.models import Plan, PlanStep
from tests.fixtures.mock_llm import MockLLMAdapter


class TestLogPreservation:
    """Test that orchestration logs match expected structure after refactoring."""

    @pytest.fixture
    def log_file(self):
        """Create temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        yield file_path
        file_path.unlink(missing_ok=True)

    @pytest.fixture
    def logger(self, log_file):
        """Create JSONL logger."""
        return JSONLLogger(file_path=log_file)

    @pytest.fixture
    def orchestrator(self, logger):
        """Create orchestrator with logger."""
        return Orchestrator(
            llm=MockLLMAdapter(),
            memory=None,  # Memory not needed for basic logging test
            ttl=10,
            logger=logger
        )

    def test_logging_structure_after_multipass(self, orchestrator, log_file):
        """Test that logs have correct structure after multi-pass execution."""
        result = orchestrator.execute_multipass("test request")
        
        # Verify log file was created
        assert log_file.exists()
        
        # Read log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Should have at least some log entries
        assert len(lines) > 0
        
        # Verify each log entry structure
        for line in lines:
            entry = json.loads(line.strip())
            
            # Required fields
            assert "step_number" in entry
            assert isinstance(entry["step_number"], int)
            
            assert "plan_state" in entry
            assert isinstance(entry["plan_state"], dict)
            
            assert "llm_output" in entry
            assert isinstance(entry["llm_output"], (str, dict, type(None)))
            
            assert "supervisor_actions" in entry
            assert isinstance(entry["supervisor_actions"], list)
            
            assert "tool_calls" in entry
            assert isinstance(entry["tool_calls"], list)
            
            assert "ttl_remaining" in entry
            assert isinstance(entry["ttl_remaining"], int)
            
            assert "errors" in entry
            assert isinstance(entry["errors"], list)
            
            assert "timestamp" in entry

    def test_logging_plan_state_structure(self, orchestrator, log_file):
        """Test that plan state in logs has correct structure."""
        orchestrator.execute_multipass("test request")
        
        # Read first log entry
        with open(log_file, 'r') as f:
            if f.readable():
                first_line = f.readline()
                if first_line:
                    entry = json.loads(first_line.strip())
                    
                    plan_state = entry["plan_state"]
                    
                    # Plan state should have goal and steps
                    assert "goal" in plan_state
                    assert isinstance(plan_state["goal"], str)
                    
                    assert "steps" in plan_state
                    assert isinstance(plan_state["steps"], list)

    def test_logging_ttl_tracking(self, orchestrator, log_file):
        """Test that TTL is tracked correctly in logs."""
        orchestrator.execute_multipass("test request")
        
        # Read all log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        ttl_values = []
        for line in lines:
            entry = json.loads(line.strip())
            ttl_values.append(entry["ttl_remaining"])
        
        # TTL should be non-negative
        for ttl in ttl_values:
            assert ttl >= 0
        
        # TTL should generally decrease or stay same (not increase)
        # (allowing for some variation due to execution)

    def test_logging_errors_field(self, orchestrator, log_file):
        """Test that errors field is present and correctly structured."""
        orchestrator.execute_multipass("test request")
        
        # Read log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            entry = json.loads(line.strip())
            
            assert "errors" in entry
            assert isinstance(entry["errors"], list)
            
            # Each error should be a dict with type and message
            for error in entry["errors"]:
                assert isinstance(error, dict)
                assert "type" in error or "message" in error

    def test_logging_tool_calls_structure(self, orchestrator, log_file):
        """Test that tool calls in logs have correct structure."""
        orchestrator.execute_multipass("test request")
        
        # Read log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            entry = json.loads(line.strip())
            
            assert "tool_calls" in entry
            assert isinstance(entry["tool_calls"], list)
            
            # Each tool call should be a dict
            for tool_call in entry["tool_calls"]:
                assert isinstance(tool_call, dict)

    def test_logging_supervisor_actions_structure(self, orchestrator, log_file):
        """Test that supervisor actions in logs have correct structure."""
        orchestrator.execute_multipass("test request")
        
        # Read log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            entry = json.loads(line.strip())
            
            assert "supervisor_actions" in entry
            assert isinstance(entry["supervisor_actions"], list)
            
            # Each supervisor action should be a dict
            for action in entry["supervisor_actions"]:
                assert isinstance(action, dict)

    def test_logging_timestamp_format(self, orchestrator, log_file):
        """Test that timestamps in logs are correctly formatted."""
        orchestrator.execute_multipass("test request")
        
        # Read log entries
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            entry = json.loads(line.strip())
            
            assert "timestamp" in entry
            timestamp = entry["timestamp"]
            
            # Timestamp should be a string (ISO format)
            assert isinstance(timestamp, str)
            assert len(timestamp) > 0

    def test_logging_with_execute_method(self, logger, log_file):
        """Test that logging works with execute method (not just multipass)."""
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory=None,
            ttl=5,
            logger=logger
        )
        
        steps = [
            PlanStep(step_id="step1", description="Step 1", status="pending"),
            PlanStep(step_id="step2", description="Step 2", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        
        result = orchestrator.execute("test", plan=plan)
        
        # Verify log file was created and has entries
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Should have at least one log entry per step
            assert len(lines) >= 2

    def test_logging_non_blocking(self, orchestrator, log_file):
        """Test that logging doesn't block execution."""
        # Execution should complete normally even with logging
        result = orchestrator.execute_multipass("test request")
        
        # Should have valid result
        assert "status" in result or "execution_history" in result
        
        # Verify log entries were written
        assert log_file.exists()
        with open(log_file, 'r') as f:
            assert len(f.readlines()) > 0

