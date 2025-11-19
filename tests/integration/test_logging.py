"""Integration tests for orchestration cycle logging."""

import json
import tempfile
from pathlib import Path

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.observability.logger import JSONLLogger
from aeon.plan.models import Plan, PlanStep
from tests.fixtures.mock_llm import MockLLMAdapter


class TestCycleLogging:
    """Integration tests for cycle logging in orchestration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter."""
        return MockLLMAdapter()

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

    def test_logging_integrated_with_orchestrator(self, mock_llm, logger, log_file):
        """Test that logging is integrated with orchestrator."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=10, logger=logger)
        
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

    def test_log_entry_contains_all_required_fields(self, mock_llm, logger, log_file):
        """Test that log entries contain all required fields."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=10, logger=logger)
        
        steps = [
            PlanStep(step_id="step1", description="Step 1", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        
        orchestrator.execute("test", plan=plan)
        
        # Read and verify log entry structure
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            assert "step_number" in entry
            assert "plan_state" in entry
            assert "llm_output" in entry
            assert "supervisor_actions" in entry
            assert "tool_calls" in entry
            assert "ttl_remaining" in entry
            assert "errors" in entry
            assert "timestamp" in entry

    def test_logging_captures_plan_state(self, mock_llm, logger, log_file):
        """Test that logging captures plan state correctly."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=10, logger=logger)
        
        steps = [
            PlanStep(step_id="step1", description="Step 1", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        
        orchestrator.execute("test", plan=plan)
        
        # Verify plan state is captured
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            assert entry["plan_state"]["goal"] == "Test goal"
            assert len(entry["plan_state"]["steps"]) == 1

    def test_logging_captures_ttl_remaining(self, mock_llm, logger, log_file):
        """Test that logging captures TTL remaining."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=5, logger=logger)
        
        steps = [
            PlanStep(step_id="step1", description="Step 1", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        
        orchestrator.execute("test", plan=plan)
        
        # Verify TTL is captured
        with open(log_file, 'r') as f:
            entry = json.loads(f.readline())
            assert entry["ttl_remaining"] <= 5
            assert entry["ttl_remaining"] >= 0

    def test_logging_is_non_blocking(self, mock_llm, logger, log_file):
        """Test that logging doesn't block execution."""
        orchestrator = Orchestrator(llm=mock_llm, ttl=10, logger=logger)
        
        steps = [
            PlanStep(step_id="step1", description="Step 1", status="pending"),
            PlanStep(step_id="step2", description="Step 2", status="pending"),
        ]
        plan = Plan(goal="Test goal", steps=steps)
        
        # Execution should complete normally even with logging
        result = orchestrator.execute("test", plan=plan)
        assert result["status"] == "completed"
        
        # Verify log entries were written
        assert log_file.exists()
        with open(log_file, 'r') as f:
            assert len(f.readlines()) >= 2

