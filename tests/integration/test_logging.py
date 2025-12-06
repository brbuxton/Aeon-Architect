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






