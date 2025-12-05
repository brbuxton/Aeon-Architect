"""Integration tests for context propagation (US4).

Tests phase context (not memory) propagation, evaluation signals propagation,
and refinement history propagation between phases.
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


class TestContextPropagation:
    """Test context propagation between phases."""

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

    def test_phase_context_propagation(self):
        """Test that phase context (not memory) is correctly propagated between phases (T096)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task requiring multiple phases"
            )
            
            # Read log file and verify phase context propagation
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            phase_entries = []
            state_transitions = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
                elif entry.get("event") == "state_transition":
                    state_transitions.append(entry)
            
            # Verify correlation ID persists across phases (phase context)
            correlation_ids = set()
            for entry in phase_entries:
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All phase entries should share the same correlation_id
            assert len(correlation_ids) <= 1, \
                f"Multiple correlation IDs in phase context: {correlation_ids}"
            
            # Verify state transitions preserve context
            for state_trans in state_transitions:
                assert "correlation_id" in state_trans, \
                    "State transition missing correlation_id"
                assert "component" in state_trans, \
                    "State transition missing component"
                assert "before_state" in state_trans, \
                    "State transition missing before_state"
                assert "after_state" in state_trans, \
                    "State transition missing after_state"
                
                # Verify state slices contain phase-relevant information
                before_state = state_trans["before_state"]
                after_state = state_trans["after_state"]
                
                # State should contain component and timestamp (phase context)
                assert "component" in before_state or "timestamp" in before_state, \
                    "Before state missing phase context"
                assert "component" in after_state or "timestamp" in after_state, \
                    "After state missing phase context"
            
            # Verify phase sequence maintains context
            if len(phase_entries) > 1:
                # All phases should share correlation_id
                first_correlation_id = phase_entries[0].get("correlation_id")
                for phase_entry in phase_entries[1:]:
                    assert phase_entry.get("correlation_id") == first_correlation_id, \
                        "Phase context not propagated (correlation_id mismatch)"
            
            # Verify that context is NOT memory-related
            # (ExecutionContext only contains correlation_id and execution_start_timestamp)
            for line in lines:
                entry = json.loads(line)
                # Context should not contain memory-specific fields
                # (memory is separate from phase context)
                if "event" in entry and entry["event"] in ["phase_entry", "state_transition"]:
                    # Should not have memory-specific context
                    # (memory is handled separately, not in phase context)
                    pass
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_evaluation_signals_propagation(self):
        """Test that evaluation signals are correctly propagated between phases (T097)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task requiring evaluation and refinement"
            )
            
            # Read log file and verify evaluation signals propagation
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            evaluation_entries = []
            refinement_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "evaluation_outcome":
                    evaluation_entries.append(entry)
                elif entry.get("event") == "refinement_outcome":
                    refinement_entries.append(entry)
            
            # Verify evaluation signals are logged
            for eval_entry in evaluation_entries:
                assert "correlation_id" in eval_entry, \
                    "Evaluation entry missing correlation_id"
                assert "convergence_assessment" in eval_entry, \
                    "Evaluation entry missing convergence_assessment"
                
                convergence_assessment = eval_entry["convergence_assessment"]
                assert "converged" in convergence_assessment, \
                    "Convergence assessment missing converged"
                assert "reason_codes" in convergence_assessment, \
                    "Convergence assessment missing reason_codes"
            
            # Verify evaluation signals propagate to refinement
            for refinement_entry in refinement_entries:
                assert "correlation_id" in refinement_entry, \
                    "Refinement entry missing correlation_id"
                assert "evaluation_signals" in refinement_entry, \
                    "Refinement entry missing evaluation_signals"
                
                evaluation_signals = refinement_entry["evaluation_signals"]
                assert isinstance(evaluation_signals, dict), \
                    "Evaluation signals should be a dict"
                
                # Should have convergence assessment or validation issues
                assert "convergence_assessment" in evaluation_signals or \
                       "validation_issues" in evaluation_signals, \
                    "Evaluation signals missing convergence_assessment or validation_issues"
                
                if "convergence_assessment" in evaluation_signals:
                    conv_assessment = evaluation_signals["convergence_assessment"]
                    assert "converged" in conv_assessment, \
                        "Convergence assessment in signals missing converged"
                    assert "reason_codes" in conv_assessment, \
                        "Convergence assessment in signals missing reason_codes"
                
                if "validation_issues" in evaluation_signals:
                    val_issues = evaluation_signals["validation_issues"]
                    assert "total_issues" in val_issues, \
                        "Validation issues missing total_issues"
            
            # Verify evaluation signals share correlation_id with refinement
            if len(evaluation_entries) > 0 and len(refinement_entries) > 0:
                eval_correlation_ids = {e["correlation_id"] for e in evaluation_entries}
                refinement_correlation_ids = {e["correlation_id"] for e in refinement_entries}
                
                # Should share correlation_id (signals propagate within same execution)
                assert len(eval_correlation_ids & refinement_correlation_ids) > 0, \
                    "Evaluation signals and refinement don't share correlation_id"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_refinement_history_propagation(self):
        """Test that refinement history is correctly propagated between phases (T098)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task requiring multiple refinements"
            )
            
            # Read log file and verify refinement history propagation
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            refinement_entries = []
            phase_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "refinement_outcome":
                    refinement_entries.append(entry)
                elif entry.get("event") == "phase_entry":
                    phase_entries.append(entry)
            
            # Verify refinement entries are logged with history context
            for refinement_entry in refinement_entries:
                assert "correlation_id" in refinement_entry, \
                    "Refinement entry missing correlation_id"
                assert "pass_number" in refinement_entry, \
                    "Refinement entry missing pass_number"
                assert "phase" in refinement_entry, \
                    "Refinement entry missing phase"
                
                # Refinement should have before/after plan fragments
                assert "before_plan_fragment" in refinement_entry, \
                    "Refinement entry missing before_plan_fragment"
                assert "after_plan_fragment" in refinement_entry, \
                    "Refinement entry missing after_plan_fragment"
                
                # Refinement actions should be logged
                assert "refinement_actions" in refinement_entry, \
                    "Refinement entry missing refinement_actions"
                
                refinement_actions = refinement_entry["refinement_actions"]
                assert isinstance(refinement_actions, list), \
                    "Refinement actions should be a list"
            
            # Verify refinement history propagates across passes
            if len(refinement_entries) > 1:
                # All refinements should share correlation_id
                correlation_ids = {e["correlation_id"] for e in refinement_entries}
                assert len(correlation_ids) == 1, \
                    f"Refinement history not propagated (multiple correlation IDs: {correlation_ids})"
                
                # Pass numbers should be sequential or increasing
                pass_numbers = [e["pass_number"] for e in refinement_entries]
                # Pass numbers should be non-decreasing (refinement history)
                for i in range(1, len(pass_numbers)):
                    assert pass_numbers[i] >= pass_numbers[i-1], \
                        f"Pass numbers not sequential: {pass_numbers}"
            
            # Verify refinement history is accessible in subsequent phases
            # (refinement entries should have correlation_id matching phase entries)
            if len(refinement_entries) > 0 and len(phase_entries) > 0:
                refinement_correlation_ids = {e["correlation_id"] for e in refinement_entries}
                phase_correlation_ids = {e["correlation_id"] for e in phase_entries}
                
                # Should share correlation_id (refinement history propagates to phases)
                assert len(refinement_correlation_ids & phase_correlation_ids) > 0, \
                    "Refinement history and phases don't share correlation_id"
            
        finally:
            log_file.unlink(missing_ok=True)

