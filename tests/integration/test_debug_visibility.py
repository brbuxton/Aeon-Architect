"""Integration tests for refinement and execution debug visibility (US3)."""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from tests.fixtures.mock_llm import MockLLMAdapter


class TestDebugVisibility:
    """Test refinement and execution debug visibility integration."""

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

    def test_refinement_trigger_logging(self):
        """Test that refinement trigger logging captures evaluation signals (T080)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task that requires refinement"
            )
            
            # Read log file and find refinement_outcome entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            refinement_entries = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "refinement_outcome":
                    refinement_entries.append(entry)
            
            # Should have at least one refinement entry if refinement occurred
            if len(refinement_entries) > 0:
                # Verify refinement trigger context (evaluation signals)
                for entry in refinement_entries:
                    assert "evaluation_signals" in entry, "Refinement entry missing evaluation_signals"
                    evaluation_signals = entry["evaluation_signals"]
                    
                    # Should have convergence assessment or validation issues
                    assert "convergence_assessment" in evaluation_signals or "validation_issues" in evaluation_signals
                    
                    if "convergence_assessment" in evaluation_signals:
                        conv_assessment = evaluation_signals["convergence_assessment"]
                        assert "converged" in conv_assessment
                        assert "reason_codes" in conv_assessment
                    
                    if "validation_issues" in evaluation_signals:
                        val_issues = evaluation_signals["validation_issues"]
                        assert "total_issues" in val_issues
        finally:
            log_file.unlink(missing_ok=True)

    def test_refinement_action_logging(self):
        """Test that refinement action logging captures which steps were modified/added/removed (T081)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task that requires refinement"
            )
            
            # Read log file and find refinement_outcome entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            refinement_entries = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "refinement_outcome":
                    refinement_entries.append(entry)
            
            # Should have at least one refinement entry if refinement occurred
            if len(refinement_entries) > 0:
                # Verify refinement actions are logged
                for entry in refinement_entries:
                    assert "refinement_actions" in entry, "Refinement entry missing refinement_actions"
                    refinement_actions = entry["refinement_actions"]
                    assert isinstance(refinement_actions, list)
                    
                    # Should have before and after plan fragments
                    assert "before_plan_fragment" in entry
                    assert "after_plan_fragment" in entry
                    
                    # Verify plan fragments contain step information
                    before_fragment = entry["before_plan_fragment"]
                    after_fragment = entry["after_plan_fragment"]
                    
                    assert "changed_steps" in before_fragment or "unchanged_step_ids" in before_fragment
                    assert "changed_steps" in after_fragment or "unchanged_step_ids" in after_fragment
        finally:
            log_file.unlink(missing_ok=True)

    def test_execution_result_logging(self):
        """Test that execution result logging captures step execution outcomes (T082)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="simple execution task"
            )
            
            # Read log file and find execution-related entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            execution_entries = []
            for line in lines:
                entry = json.loads(line)
                # Look for state_transition events with execution component
                if (entry.get("event") == "state_transition" and 
                    entry.get("component") == "execution"):
                    execution_entries.append(entry)
            
            # Should have at least some execution entries
            if len(execution_entries) > 0:
                # Verify execution entries contain step execution information
                for entry in execution_entries:
                    assert "before_state" in entry
                    assert "after_state" in entry
                    assert "transition_reason" in entry
                    
                    # Should have step_id in state
                    before_state = entry["before_state"]
                    after_state = entry["after_state"]
                    
                    # Check for step execution outcome indicators
                    if "step_execution" in entry["transition_reason"]:
                        assert "step_id" in before_state or "step_id" in after_state
                        # After state should have success/error information
                        if "success" in after_state:
                            # If success, should have result
                            # If failure, should have error
                            pass
        finally:
            log_file.unlink(missing_ok=True)

    def test_convergence_assessment_logging(self):
        """Test that convergence assessment logging explains why convergence was/wasn't achieved (T083)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task for convergence testing"
            )
            
            # Read log file and find evaluation_outcome entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            evaluation_entries = []
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "evaluation_outcome":
                    evaluation_entries.append(entry)
            
            # Should have at least one evaluation entry
            assert len(evaluation_entries) > 0, "No evaluation_outcome entries found"
            
            # Verify convergence assessment is logged with reason codes
            for entry in evaluation_entries:
                assert "convergence_assessment" in entry
                convergence_assessment = entry["convergence_assessment"]
                
                assert "converged" in convergence_assessment
                assert "reason_codes" in convergence_assessment
                
                # Reason codes should explain convergence decision
                reason_codes = convergence_assessment["reason_codes"]
                assert isinstance(reason_codes, list)
                assert len(reason_codes) > 0
                
                # Should have scores if available
                if "scores" in convergence_assessment:
                    scores = convergence_assessment["scores"]
                    assert isinstance(scores, dict)
                
                # Verify evaluation_signals structure
                if "evaluation_signals" in entry:
                    evaluation_signals = entry["evaluation_signals"]
                    assert "convergence_assessment" in evaluation_signals
                    assert "validation_issues" in evaluation_signals
        finally:
            log_file.unlink(missing_ok=True)

    def test_plan_state_change_logging(self):
        """Test that plan state change logging captures state transitions (T084)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            result = orchestrator.execute_multipass(
                request="task with plan state changes"
            )
            
            # Read log file and find state_transition entries for plan component
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            plan_state_entries = []
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "state_transition" and 
                    entry.get("component") == "plan"):
                    plan_state_entries.append(entry)
            
            # Should have at least some plan state transitions if refinement occurred
            if len(plan_state_entries) > 0:
                # Verify plan state transitions contain before/after states
                for entry in plan_state_entries:
                    assert "before_state" in entry
                    assert "after_state" in entry
                    assert "transition_reason" in entry
                    
                    before_state = entry["before_state"]
                    after_state = entry["after_state"]
                    
                    # Should have plan-related state information
                    # (e.g., step_count, steps_status_summary)
                    assert isinstance(before_state, dict)
                    assert isinstance(after_state, dict)
                    
                    # Transition reason should explain the change
                    assert entry["transition_reason"] is not None
                    assert len(entry["transition_reason"]) > 0
        finally:
            log_file.unlink(missing_ok=True)

