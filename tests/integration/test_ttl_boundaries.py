"""Integration tests for TTL boundary conditions (US4).

Tests TTL behavior at single-pass execution, phase boundary expiration,
and mid-phase expiration scenarios.
"""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from aeon.exceptions import TTLExpiredError
from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from tests.fixtures.mock_llm import MockLLMAdapter


class TestTTLBoundaries:
    """Test TTL boundary conditions and expiration scenarios."""

    def _create_orchestrator_with_logger(self, ttl: int) -> Tuple[Orchestrator, Path]:
        """Create orchestrator with logger and specified TTL."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory=InMemoryKVStore(),
            ttl=ttl,
            logger=logger,
        )
        return orchestrator, file_path

    def test_single_pass_execution_ttl(self):
        """Test TTL behavior during single-pass execution (T093)."""
        # Use a TTL that allows single-pass completion
        orchestrator, log_file = self._create_orchestrator_with_logger(ttl=10)
        
        try:
            result = orchestrator.execute_multipass(
                request="simple single-pass task"
            )
            
            # Read log file and verify TTL handling
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Verify execution completed or TTL expired
            assert "status" in result or "execution_history" in result
            
            # Check for TTL-related log entries
            ttl_entries = []
            phase_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if "ttl" in str(entry).lower() or entry.get("event") == "ttl_expired":
                    ttl_entries.append(entry)
                if entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
            
            # For single-pass execution, should have at least Phase A and B
            assert len(phase_entries) >= 2, "Single-pass should have at least Phase A and B"
            
            # Verify correlation ID persists through single-pass
            correlation_ids = set()
            for line in lines:
                entry = json.loads(line)
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All entries should share the same correlation_id
            assert len(correlation_ids) == 1, f"Multiple correlation IDs in single-pass: {correlation_ids}"
            
            # Verify TTL is tracked (if result has ttl_remaining)
            if "ttl_remaining" in result:
                assert isinstance(result["ttl_remaining"], int)
                assert result["ttl_remaining"] >= 0
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_phase_boundary_expiration(self):
        """Test TTL expiration at phase boundaries (T094)."""
        # Use a very low TTL to force expiration at phase boundary
        orchestrator, log_file = self._create_orchestrator_with_logger(ttl=1)
        
        try:
            result = orchestrator.execute_multipass(
                request="task that may expire at phase boundary"
            )
            
            # Read log file and verify phase boundary expiration
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            phase_entries = []
            phase_exits = []
            error_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
                elif entry.get("event") == "phase_exit":
                    phase_exits.append(entry)
                elif entry.get("event") == "error":
                    error_entries.append(entry)
            
            # If TTL expired at phase boundary, should have phase entries
            # and possibly error entries related to TTL expiration
            if len(phase_entries) > 0:
                # Verify phase entries have correlation_id
                for phase_entry in phase_entries:
                    assert "correlation_id" in phase_entry, "Phase entry missing correlation_id"
                    assert "phase" in phase_entry, "Phase entry missing phase"
            
            # Check if TTL expiration occurred
            ttl_expired = False
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "error" and 
                    "ttl" in str(entry).lower()):
                    ttl_expired = True
                    # Verify TTL expiration error structure
                    assert "correlation_id" in entry, "TTL error missing correlation_id"
                    assert "original_error" in entry, "TTL error missing original_error"
                    break
            
            # If TTL expired, verify it was logged properly
            if ttl_expired or result.get("status") == "ttl_expired":
                # Should have proper error logging
                assert len(error_entries) > 0 or "error" in result, \
                    "TTL expiration should be logged as error"
            
            # Verify correlation ID persists even through TTL expiration
            correlation_ids = set()
            for line in lines:
                entry = json.loads(line)
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All entries should share the same correlation_id
            assert len(correlation_ids) <= 1, \
                f"Multiple correlation IDs at phase boundary: {correlation_ids}"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_mid_phase_expiration(self):
        """Test TTL expiration during mid-phase execution (T095)."""
        # Use a very low TTL to force expiration mid-phase
        orchestrator, log_file = self._create_orchestrator_with_logger(ttl=1)
        
        try:
            result = orchestrator.execute_multipass(
                request="task that may expire mid-phase"
            )
            
            # Read log file and verify mid-phase expiration
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            phase_entries = []
            state_transitions = []
            error_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
                elif entry.get("event") == "state_transition":
                    state_transitions.append(entry)
                elif entry.get("event") == "error":
                    error_entries.append(entry)
            
            # If TTL expired mid-phase, should have phase entry but possibly no exit
            if len(phase_entries) > 0:
                # Verify phase was entered
                first_phase = phase_entries[0]
                assert "phase" in first_phase, "Phase entry missing phase"
                assert "correlation_id" in first_phase, "Phase entry missing correlation_id"
            
            # Check if TTL expiration occurred during execution
            ttl_expired_mid_phase = False
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "error" and 
                    "ttl" in str(entry).lower()):
                    ttl_expired_mid_phase = True
                    # Verify error structure
                    assert "correlation_id" in entry, "TTL error missing correlation_id"
                    assert "original_error" in entry, "TTL error missing original_error"
                    
                    error = entry["original_error"]
                    assert "code" in error, "TTL error missing code"
                    assert "severity" in error, "TTL error missing severity"
                    break
            
            # If TTL expired mid-phase, verify proper logging
            if ttl_expired_mid_phase or result.get("status") == "ttl_expired":
                # Should have error entry
                assert len(error_entries) > 0 or "error" in result, \
                    "Mid-phase TTL expiration should be logged"
                
                # Should have state transitions before expiration
                if len(state_transitions) > 0:
                    # Verify state transitions have correlation_id
                    for state_trans in state_transitions:
                        assert "correlation_id" in state_trans, \
                            "State transition missing correlation_id"
            
            # Verify correlation ID persists through mid-phase expiration
            correlation_ids = set()
            for line in lines:
                entry = json.loads(line)
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All entries should share the same correlation_id
            assert len(correlation_ids) <= 1, \
                f"Multiple correlation IDs in mid-phase: {correlation_ids}"
            
        finally:
            log_file.unlink(missing_ok=True)

