"""Integration tests for determinism validation (T121-T123)."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from aeon.observability.helpers import generate_correlation_id
from aeon.observability.logger import JSONLLogger


class TestDeterminism:
    """Test that logging operations preserve kernel determinism."""

    def _create_logger(self) -> tuple[JSONLLogger, Path]:
        """Create logger with temp file and return logger and file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        return logger, file_path

    def test_correlation_id_unique_for_different_inputs(self):
        """Test that correlation IDs are unique for different inputs."""
        timestamp = "2025-01-27T10:00:00.000000"
        request1 = "Test request 1"
        request2 = "Test request 2"
        
        id1 = generate_correlation_id(timestamp, request1)
        id2 = generate_correlation_id(timestamp, request2)
        
        # Should be different
        assert id1 != id2, "Correlation IDs should be unique for different inputs"

    def test_logging_operations_do_not_affect_determinism(self):
        """Test that logging operations do not affect kernel determinism (T122)."""
        logger1, log_file1 = self._create_logger()
        logger2, log_file2 = self._create_logger()
        
        try:
            timestamp = "2025-01-27T10:00:00.000000"
            request = "Test request for determinism"
            correlation_id = generate_correlation_id(timestamp, request)
            
            # Perform same logging operations twice
            logger1.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger1.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            
            logger2.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger2.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            
            # Read both log files
            with open(log_file1, 'r') as f1, open(log_file2, 'r') as f2:
                lines1 = f1.readlines()
                lines2 = f2.readlines()
            
            # Should have same number of entries
            assert len(lines1) == len(lines2), "Log files should have same number of entries"
            
            # Entries should be identical (except for timestamp which may vary slightly)
            # For deterministic operations, correlation_id and phase should match
            import json
            for i, (line1, line2) in enumerate(zip(lines1, lines2)):
                entry1 = json.loads(line1)
                entry2 = json.loads(line2)
                
                # Correlation ID should match
                assert entry1["correlation_id"] == entry2["correlation_id"], \
                    f"Entry {i} correlation_id should match"
                
                # Phase should match
                if "phase" in entry1:
                    assert entry1["phase"] == entry2["phase"], \
                        f"Entry {i} phase should match"
                
                # Event type should match
                assert entry1["event"] == entry2["event"], \
                    f"Entry {i} event should match"
        finally:
            log_file1.unlink(missing_ok=True)
            log_file2.unlink(missing_ok=True)

    def test_no_non_deterministic_behavior_introduced(self):
        """Test that no non-deterministic behavior was introduced by observability improvements (T123)."""
        logger, log_file = self._create_logger()
        
        try:
            timestamp = "2025-01-27T10:00:00.000000"
            request = "Test request"
            correlation_id = generate_correlation_id(timestamp, request)
            
            # Perform logging operations
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            logger.log_phase_entry(phase="B", correlation_id=correlation_id)
            logger.log_phase_exit(phase="B", correlation_id=correlation_id, duration=2.0, outcome="success")
            
            # Read log file
            import json
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Verify all entries have same correlation_id
            correlation_ids = set()
            for line in lines:
                entry = json.loads(line)
                correlation_ids.add(entry.get("correlation_id"))
            
            # Should have exactly one correlation ID
            assert len(correlation_ids) == 1, \
                f"All entries should have same correlation_id, found: {correlation_ids}"
            
            # Correlation ID should match expected value
            expected_id = generate_correlation_id(timestamp, request)
            assert correlation_ids.pop() == expected_id, \
                "Correlation ID should match expected deterministic value"
        finally:
            log_file.unlink(missing_ok=True)

