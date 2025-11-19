"""Unit tests for JSONL logger."""

import json
import tempfile
from pathlib import Path

import pytest

from aeon.observability.logger import JSONLLogger
from aeon.observability.models import LogEntry


class TestJSONLLogger:
    """Test JSONL logger implementation."""

    def test_logger_initializes_with_file_path(self):
        """Test that logger initializes with a file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            assert logger.file_path == file_path
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_writes_to_file(self):
        """Test that log_entry writes a JSONL line to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read file and verify content
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert entry["step_number"] == 1
                assert entry["plan_state"]["goal"] == "test"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_appends_multiple_entries(self):
        """Test that multiple log entries are appended to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            for i in range(3):
                log_entry = LogEntry(
                    step_number=i + 1,
                    plan_state={"goal": f"test_{i}", "steps": []},
                    llm_output={"text": f"response_{i}"},
                    ttl_remaining=10 - i,
                    timestamp=f"2024-01-01T00:00:{i:02d}Z"
                )
                logger.log_entry(log_entry)
            
            # Read file and verify all entries
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                for i, line in enumerate(lines):
                    entry = json.loads(line)
                    assert entry["step_number"] == i + 1
                    assert entry["ttl_remaining"] == 10 - i
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_includes_all_fields(self):
        """Test that log entry includes all required fields."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                supervisor_actions=[{"type": "json_repair"}],
                tool_calls=[{"tool_name": "echo", "arguments": {"message": "hello"}}],
                ttl_remaining=5,
                errors=[{"type": "ToolError", "message": "test error"}],
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read and verify all fields
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert "step_number" in entry
                assert "plan_state" in entry
                assert "llm_output" in entry
                assert "supervisor_actions" in entry
                assert "tool_calls" in entry
                assert "ttl_remaining" in entry
                assert "errors" in entry
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_handles_empty_lists(self):
        """Test that log entry handles empty optional lists."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read and verify empty lists are present
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["supervisor_actions"] == []
                assert entry["tool_calls"] == []
                assert entry["errors"] == []
        finally:
            file_path.unlink(missing_ok=True)

    def test_logger_creates_file_if_not_exists(self):
        """Test that logger creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            assert file_path.exists()
            with open(file_path, 'r') as f:
                assert len(f.readlines()) == 1

