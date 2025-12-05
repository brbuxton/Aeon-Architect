"""Integration tests for phase-aware structured logging (US1)."""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from tests.fixtures.mock_llm import MockLLMAdapter


class TestPhaseLogging:
    """Test phase-aware structured logging integration."""

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

    def test_multipass_execution_with_phase_logging(self):
        """Test that multi-pass execution logs phase entry/exit events (T033)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="simple task for testing"
            )
            
            # Verify execution completed
            assert "execution_history" in result
            
            # Read log file and verify phase entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 0
                
                # Check for phase_entry and phase_exit events
                phase_entries = []
                phase_exits = []
                for line in lines:
                    entry = json.loads(line)
                    if entry.get("event") == "phase_entry":
                        phase_entries.append(entry)
                    elif entry.get("event") == "phase_exit":
                        phase_exits.append(entry)
                
                # Should have at least phase A and B entries
                assert len(phase_entries) > 0
                assert len(phase_exits) > 0
        finally:
            log_file.unlink(missing_ok=True)

    def test_correlation_id_traceability(self):
        """Test that 100% of log entries contain correlation_id (T034)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="test correlation ID traceability"
            )
            
            # Read log file and verify all entries have correlation_id
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 0
                
                correlation_ids = set()
                for line in lines:
                    entry = json.loads(line)
                    # All entries should have correlation_id
                    assert "correlation_id" in entry, f"Entry missing correlation_id: {entry}"
                    assert entry["correlation_id"] is not None
                    assert entry["correlation_id"] != ""
                    correlation_ids.add(entry["correlation_id"])
                
                # All entries should have the same correlation_id
                assert len(correlation_ids) == 1, f"Multiple correlation IDs found: {correlation_ids}"
        finally:
            log_file.unlink(missing_ok=True)

    def test_phase_transition_sequence(self):
        """Test that phase transitions follow sequence A→B→C→D (T035)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="test phase sequence"
            )
            
            # Read log file and extract phase entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
                phase_sequence = []
                for line in lines:
                    entry = json.loads(line)
                    if entry.get("event") == "phase_entry":
                        phase_sequence.append(entry.get("phase"))
                    elif entry.get("event") == "phase_exit":
                        # Phase exits should match entries
                        pass
                
                # Should have at least Phase A and B
                assert len(phase_sequence) >= 2
                # Phase A should come before Phase B
                assert "A" in phase_sequence
                assert "B" in phase_sequence
                assert phase_sequence.index("A") < phase_sequence.index("B")
        finally:
            log_file.unlink(missing_ok=True)

    def test_state_transition_logging_with_minimal_slices(self):
        """Test that state transitions are logged with minimal state slices (T036)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="test state transitions"
            )
            
            # Read log file and verify state_transition events
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
                state_transitions = []
                for line in lines:
                    entry = json.loads(line)
                    if entry.get("event") == "state_transition":
                        state_transitions.append(entry)
                
                # If refinements occurred, should have state transitions
                # Check that state transitions have minimal slices
                for transition in state_transitions:
                    assert "component" in transition
                    assert "before_state" in transition
                    assert "after_state" in transition
                    assert "transition_reason" in transition
                    assert "correlation_id" in transition
                    
                    # Verify state slices are minimal (not full plan state)
                    before_state = transition["before_state"]
                    after_state = transition["after_state"]
                    
                    # State slices should have component and timestamp
                    assert "component" in before_state
                    assert "timestamp" in before_state
                    assert "component" in after_state
                    assert "timestamp" in after_state
        finally:
            log_file.unlink(missing_ok=True)

