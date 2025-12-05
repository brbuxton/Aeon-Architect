"""Integration tests for phase transitions (US4).

Tests phase entry/exit behavior, state handoffs, error handling at phase boundaries,
and correlation ID persistence across phases.
"""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from tests.fixtures.mock_llm import MockLLMAdapter


class TestPhaseTransitions:
    """Test phase transition behavior and boundaries."""

    def _create_orchestrator_with_logger(self) -> Tuple[Orchestrator, Path]:
        """Create orchestrator with logger and return temp file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        orchestrator = Orchestrator(
            llm=MockLLMAdapter(),
            memory=InMemoryKVStore(),
            ttl=10,
            logger=logger,
        )
        return orchestrator, file_path

    def test_phase_entry_exit_behavior(self):
        """Test that phase entry/exit events are correctly logged (T085)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="simple task for phase transition testing"
            )
            
            # Read log file and verify phase entry/exit behavior
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            phase_entries = []
            phase_exits = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
                elif entry.get("event") == "phase_exit":
                    phase_exits.append(entry)
            
            # Should have at least one phase entry and exit
            assert len(phase_entries) > 0, "No phase_entry events found"
            assert len(phase_exits) > 0, "No phase_exit events found"
            
            # Verify phase entry structure
            for entry in phase_entries:
                assert "phase" in entry, "Phase entry missing phase field"
                assert entry["phase"] in ["A", "B", "C", "D"], f"Invalid phase: {entry['phase']}"
                assert "correlation_id" in entry, "Phase entry missing correlation_id"
                assert "timestamp" in entry, "Phase entry missing timestamp"
            
            # Verify phase exit structure
            for exit_entry in phase_exits:
                assert "phase" in exit_entry, "Phase exit missing phase field"
                assert exit_entry["phase"] in ["A", "B", "C", "D"], f"Invalid phase: {exit_entry['phase']}"
                assert "correlation_id" in exit_entry, "Phase exit missing correlation_id"
                assert "timestamp" in exit_entry, "Phase exit missing timestamp"
                assert "outcome" in exit_entry, "Phase exit missing outcome"
                assert exit_entry["outcome"] in ["success", "failure"], f"Invalid outcome: {exit_entry['outcome']}"
            
            # Verify each phase entry has a corresponding exit (or at least sequence is correct)
            # Phase A should be entered first
            first_entry = phase_entries[0]
            assert first_entry["phase"] == "A", "First phase should be A"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_state_handoffs_between_phases(self):
        """Test that state is correctly handed off between phases (T086)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task requiring multiple phases"
            )
            
            # Read log file and verify state handoffs
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            # Track phase transitions and state transitions
            phase_transitions = []
            state_transitions = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "phase_exit":
                    phase_transitions.append(entry)
                elif entry.get("event") == "state_transition":
                    state_transitions.append(entry)
            
            # Verify that state transitions occur around phase boundaries
            # When a phase exits, there should be state transitions that prepare for next phase
            if len(phase_transitions) > 0:
                # At minimum, verify state transitions have proper structure
                for state_trans in state_transitions:
                    assert "component" in state_trans, "State transition missing component"
                    assert "before_state" in state_trans, "State transition missing before_state"
                    assert "after_state" in state_trans, "State transition missing after_state"
                    assert "transition_reason" in state_trans, "State transition missing transition_reason"
                    assert "correlation_id" in state_trans, "State transition missing correlation_id"
            
            # Verify correlation ID persists across state handoffs
            correlation_ids = set()
            for entry in phase_transitions + state_transitions:
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All entries should share the same correlation_id
            assert len(correlation_ids) <= 1, f"Multiple correlation IDs found: {correlation_ids}"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_error_handling_at_phase_boundaries(self):
        """Test that errors at phase boundaries are properly handled and logged (T087)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that might trigger errors
            result = orchestrator.execute_multipass(
                request="task that may cause phase boundary errors"
            )
            
            # Read log file and check for error handling
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            error_entries = []
            phase_exits = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "error":
                    error_entries.append(entry)
                elif entry.get("event") == "phase_exit":
                    phase_exits.append(entry)
            
            # If errors occurred, verify they are properly structured
            for error_entry in error_entries:
                assert "correlation_id" in error_entry, "Error entry missing correlation_id"
                assert "original_error" in error_entry, "Error entry missing original_error"
                assert "code" in error_entry["original_error"], "Error missing code"
                assert "severity" in error_entry["original_error"], "Error missing severity"
                assert "affected_component" in error_entry["original_error"], "Error missing affected_component"
            
            # Verify phase exits indicate outcome (success/failure)
            for exit_entry in phase_exits:
                assert "outcome" in exit_entry, "Phase exit missing outcome"
                # If phase failed, outcome should be "failure"
                if exit_entry.get("outcome") == "failure":
                    # Should have error information or error recovery
                    # Check if there are error entries around this phase
                    pass
            
            # Verify error recovery is logged if recovery occurred
            recovery_entries = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "error_recovery":
                    recovery_entries.append(entry)
            
            # If recovery occurred, verify structure
            for recovery_entry in recovery_entries:
                assert "correlation_id" in recovery_entry, "Recovery entry missing correlation_id"
                assert "original_error" in recovery_entry, "Recovery entry missing original_error"
                assert "recovery_action" in recovery_entry, "Recovery entry missing recovery_action"
                assert "recovery_outcome" in recovery_entry, "Recovery entry missing recovery_outcome"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_correlation_id_persistence_across_phases(self):
        """Test that correlation ID persists across all phases (T088)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="multi-phase task for correlation ID testing"
            )
            
            # Read log file and verify correlation ID persistence
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            correlation_ids = set()
            phase_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if "correlation_id" in entry:
                    correlation_id = entry["correlation_id"]
                    correlation_ids.add(correlation_id)
                    
                    if entry.get("event") == "phase_entry":
                        phase_entries.append(entry)
            
            # All entries should share the same correlation_id
            assert len(correlation_ids) == 1, f"Multiple correlation IDs found: {correlation_ids}"
            
            correlation_id = list(correlation_ids)[0]
            assert correlation_id is not None
            assert correlation_id != ""
            
            # Verify correlation ID appears in all phase entries
            for phase_entry in phase_entries:
                assert phase_entry["correlation_id"] == correlation_id, \
                    f"Phase entry has different correlation_id: {phase_entry['correlation_id']}"
            
            # Verify correlation ID appears in all log entry types
            entry_types = set()
            for line in lines:
                entry = json.loads(line)
                if "correlation_id" in entry:
                    assert entry["correlation_id"] == correlation_id, \
                        f"Entry has different correlation_id: {entry.get('event', 'unknown')}"
                    entry_types.add(entry.get("event", "unknown"))
            
            # Should have multiple entry types with same correlation_id
            assert len(entry_types) > 1, "Only one entry type found with correlation_id"
            
        finally:
            log_file.unlink(missing_ok=True)

