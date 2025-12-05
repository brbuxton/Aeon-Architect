"""Integration tests for backward compatibility (T117-T120)."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from aeon.observability.helpers import generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.observability.models import LogEntry


class TestBackwardCompatibility:
    """Test backward compatibility with existing logging methods."""

    def _create_logger(self) -> tuple[JSONLLogger, Path]:
        """Create logger with temp file and return logger and file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        return logger, file_path

    def test_format_entry_creates_cycle_event(self):
        """Test that format_entry method creates event='cycle' for backward compatibility (T117)."""
        logger, log_file = self._create_logger()
        
        try:
            entry = logger.format_entry(
                step_number=1,
                plan_state={"goal": "Test goal", "steps": []},
                llm_output={"response": "Test response"},
                supervisor_actions=[],
                tool_calls=[],
                ttl_remaining=10,
                errors=[],
                pass_number=1,
                phase="A"
            )
            
            # Verify entry has event="cycle"
            assert entry.event == "cycle", "format_entry should create event='cycle'"
            assert entry.step_number == 1
            assert entry.plan_state is not None
            assert entry.llm_output is not None
        finally:
            log_file.unlink(missing_ok=True)

    def test_log_entry_method_works(self):
        """Test that existing log_entry method continues to work (T118)."""
        logger, log_file = self._create_logger()
        
        try:
            entry = LogEntry(
                step_number=1,
                plan_state={"goal": "Test goal", "steps": []},
                llm_output={"response": "Test response"},
                supervisor_actions=[],
                tool_calls=[],
                ttl_remaining=10,
                errors=[],
                timestamp=datetime.now().isoformat(),
                pass_number=1,
                phase="A"
            )
            
            # Should not raise exception
            logger.log_entry(entry)
            
            # Verify entry was written
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                entry_dict = json.loads(lines[0])
                assert entry_dict["event"] == "cycle"
                assert entry_dict["step_number"] == 1
        finally:
            log_file.unlink(missing_ok=True)

    def test_backward_compatibility_with_existing_parsers(self):
        """Test backward compatibility with existing log parsers (T119)."""
        logger, log_file = self._create_logger()
        
        try:
            # Create entries using both old and new methods
            # Old method: format_entry + log_entry
            entry = logger.format_entry(
                step_number=1,
                plan_state={"goal": "Test goal", "steps": []},
                llm_output={"response": "Test response"},
                supervisor_actions=[],
                tool_calls=[],
                ttl_remaining=10,
                errors=[],
                pass_number=1,
                phase="A"
            )
            logger.log_entry(entry)
            
            # New method: phase-aware logging
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            
            # Read log file and verify both formats are valid JSON
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                # Parse all entries
                entries = []
                for line in lines:
                    entry_dict = json.loads(line)
                    entries.append(entry_dict)
                
                # First entry should be cycle event (old format)
                assert entries[0]["event"] == "cycle"
                assert "step_number" in entries[0]
                assert "plan_state" in entries[0]
                
                # Second entry should be phase_entry (new format)
                assert entries[1]["event"] == "phase_entry"
                assert "correlation_id" in entries[1]
                
                # Third entry should be phase_exit (new format)
                assert entries[2]["event"] == "phase_exit"
                assert "correlation_id" in entries[2]
                
                # All entries should be valid JSON
                for entry_dict in entries:
                    # Verify required fields exist
                    assert "timestamp" in entry_dict
                    assert "event" in entry_dict
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_evolution_backward_compatibility(self):
        """Test that schema evolution maintains backward compatibility (T120)."""
        logger, log_file = self._create_logger()
        
        try:
            # Create entry using old format
            entry = logger.format_entry(
                step_number=1,
                plan_state={"goal": "Test goal", "steps": []},
                llm_output={"response": "Test response"},
                supervisor_actions=[],
                tool_calls=[],
                ttl_remaining=10,
                errors=[],
                pass_number=1,
                phase="A"
            )
            logger.log_entry(entry)
            
            # Read and verify old format is still parseable
            with open(log_file, 'r') as f:
                line = f.readline()
                entry_dict = json.loads(line)
                
                # Old format fields should still be present
                assert "step_number" in entry_dict
                assert "plan_state" in entry_dict
                assert "llm_output" in entry_dict
                assert "supervisor_actions" in entry_dict
                assert "tool_calls" in entry_dict
                assert "ttl_remaining" in entry_dict
                assert "errors" in entry_dict
                
                # New format fields should be present with defaults
                assert entry_dict["event"] == "cycle"  # Default event type
                assert "timestamp" in entry_dict
                
                # Optional new fields may be None or absent
                # correlation_id, phase, pass_number are optional for cycle events
        finally:
            log_file.unlink(missing_ok=True)

