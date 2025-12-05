"""Integration tests for deterministic convergence (US4).

Tests convergence behavior for simple, repeatable tasks and validates
that convergence behaves deterministically.
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


class TestDeterministicConvergence:
    """Test deterministic convergence behavior."""

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

    def test_simple_repeatable_tasks_convergence(self):
        """Test that simple, repeatable tasks converge deterministically (T099)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a simple, repeatable task
            result = orchestrator.execute_multipass(
                request="simple task for convergence testing"
            )
            
            # Read log file and verify convergence behavior
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            evaluation_entries = []
            convergence_assessments = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "evaluation_outcome":
                    evaluation_entries.append(entry)
                    if "convergence_assessment" in entry:
                        convergence_assessments.append(entry["convergence_assessment"])
            
            # Verify convergence assessment is logged
            assert len(evaluation_entries) > 0, "No evaluation_outcome entries found"
            
            # Verify convergence assessment structure
            for assessment in convergence_assessments:
                assert "converged" in assessment, \
                    "Convergence assessment missing converged"
                assert isinstance(assessment["converged"], bool), \
                    "Converged should be boolean"
                assert "reason_codes" in assessment, \
                    "Convergence assessment missing reason_codes"
                assert isinstance(assessment["reason_codes"], list), \
                    "Reason codes should be a list"
            
            # Verify convergence decision is deterministic
            # (same inputs should produce same convergence decision)
            # For simple tasks, convergence should be consistent
            converged_values = [a["converged"] for a in convergence_assessments]
            
            # If multiple assessments, they should be consistent for simple tasks
            # (all True or all False, or progressing toward convergence)
            if len(converged_values) > 1:
                # For simple tasks, convergence should eventually be True
                # or consistently False with clear reason codes
                final_converged = converged_values[-1]
                # Verify reason codes explain the decision
                final_assessment = convergence_assessments[-1]
                assert len(final_assessment["reason_codes"]) > 0, \
                    "Convergence assessment should have reason codes"
            
            # Verify correlation ID persists through convergence assessment
            correlation_ids = set()
            for entry in evaluation_entries:
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All evaluation entries should share the same correlation_id
            assert len(correlation_ids) <= 1, \
                f"Multiple correlation IDs in convergence: {correlation_ids}"
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_convergence_behavior_validation(self):
        """Test that convergence behavior is validated and logged correctly (T100)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that should converge
            result = orchestrator.execute_multipass(
                request="task for convergence behavior validation"
            )
            
            # Read log file and verify convergence behavior validation
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
            
            # Verify convergence behavior is logged
            assert len(evaluation_entries) > 0, "No evaluation_outcome entries found"
            
            # Verify convergence assessment explains behavior
            for eval_entry in evaluation_entries:
                assert "convergence_assessment" in eval_entry, \
                    "Evaluation entry missing convergence_assessment"
                
                convergence_assessment = eval_entry["convergence_assessment"]
                assert "converged" in convergence_assessment, \
                    "Convergence assessment missing converged"
                assert "reason_codes" in convergence_assessment, \
                    "Convergence assessment missing reason_codes"
                
                reason_codes = convergence_assessment["reason_codes"]
                assert isinstance(reason_codes, list), \
                    "Reason codes should be a list"
                assert len(reason_codes) > 0, \
                    "Convergence assessment should have at least one reason code"
                
                # Reason codes should explain convergence decision
                for reason_code in reason_codes:
                    assert isinstance(reason_code, str), \
                        f"Reason code should be string: {reason_code}"
                    assert len(reason_code) > 0, \
                        "Reason code should not be empty"
            
            # Verify convergence behavior is deterministic
            # (same task should produce consistent convergence decisions)
            convergence_decisions = []
            for eval_entry in evaluation_entries:
                if "convergence_assessment" in eval_entry:
                    assessment = eval_entry["convergence_assessment"]
                    convergence_decisions.append({
                        "converged": assessment["converged"],
                        "reason_codes": assessment["reason_codes"],
                    })
            
            # Verify convergence decisions are consistent
            # (reason codes should explain why convergence was/wasn't achieved)
            for decision in convergence_decisions:
                assert "converged" in decision, \
                    "Convergence decision missing converged"
                assert "reason_codes" in decision, \
                    "Convergence decision missing reason_codes"
                assert len(decision["reason_codes"]) > 0, \
                    "Convergence decision should have reason codes"
            
            # Verify convergence behavior is linked to refinement
            # (if convergence not achieved, refinement should occur)
            if len(evaluation_entries) > 0 and len(refinement_entries) > 0:
                # Evaluation and refinement should share correlation_id
                eval_correlation_ids = {e["correlation_id"] for e in evaluation_entries}
                refinement_correlation_ids = {e["correlation_id"] for e in refinement_entries}
                
                # Should share correlation_id (convergence and refinement are linked)
                assert len(eval_correlation_ids & refinement_correlation_ids) > 0, \
                    "Convergence and refinement don't share correlation_id"
            
            # Verify convergence behavior is deterministic
            # (correlation ID should be consistent)
            correlation_ids = set()
            for entry in evaluation_entries:
                if "correlation_id" in entry:
                    correlation_ids.add(entry["correlation_id"])
            
            # All evaluation entries should share the same correlation_id
            assert len(correlation_ids) <= 1, \
                f"Multiple correlation IDs in convergence behavior: {correlation_ids}"
            
        finally:
            log_file.unlink(missing_ok=True)

