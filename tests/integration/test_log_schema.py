"""Integration tests for log schema validation (T124-T126)."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from aeon.observability.helpers import generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.observability.models import (
    ErrorRecord,
    ErrorSeverity,
    PlanFragment,
    PlanStateSlice,
    ConvergenceAssessmentSummary,
    ValidationIssuesSummary,
)
from aeon.plan.models import PlanStep


class TestLogSchema:
    """Test that all log entries conform to stable JSONL schemas."""

    def _create_logger(self) -> tuple[JSONLLogger, Path]:
        """Create logger with temp file and return logger and file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        return logger, file_path

    def test_all_log_entries_valid_json(self):
        """Test that all log entries conform to valid JSON (T124)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Create various log entries
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            
            before_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_1",
                step_count=3,
                steps_status_summary={"pending": 2, "running": 1, "complete": 0}
            )
            after_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_2",
                step_count=3,
                steps_status_summary={"pending": 1, "running": 1, "complete": 1}
            )
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="step_completed"
            )
            
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution"
            )
            logger.log_error(correlation_id=correlation_id, error=error_record)
            
            # Read and validate all entries are valid JSON
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 0
                
                for i, line in enumerate(lines):
                    try:
                        entry = json.loads(line)
                        # Verify entry is a dict
                        assert isinstance(entry, dict), f"Entry {i} should be a dict"
                        # Verify required fields
                        assert "timestamp" in entry, f"Entry {i} missing timestamp"
                        assert "event" in entry, f"Entry {i} missing event"
                    except json.JSONDecodeError as e:
                        pytest.fail(f"Entry {i} is not valid JSON: {e}")
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_phase_entry(self):
        """Test schema validation for phase_entry events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "phase_entry"
                assert "correlation_id" in entry
                assert entry["phase"] == "A"
                assert "timestamp" in entry
                
                # Verify optional fields
                assert "pass_number" in entry or entry.get("pass_number") is None
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_phase_exit(self):
        """Test schema validation for phase_exit events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "phase_exit"
                assert "correlation_id" in entry
                assert entry["phase"] == "A"
                assert entry["duration"] == 1.0
                assert entry["outcome"] == "success"
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_state_transition(self):
        """Test schema validation for state_transition events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            before_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_1",
                step_count=3,
                steps_status_summary={"pending": 2, "running": 1, "complete": 0}
            )
            after_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_2",
                step_count=3,
                steps_status_summary={"pending": 1, "running": 1, "complete": 1}
            )
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="step_completed"
            )
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "state_transition"
                assert "correlation_id" in entry
                assert entry["component"] == "plan"
                assert "before_state" in entry
                assert "after_state" in entry
                assert entry["transition_reason"] == "step_completed"
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_refinement_outcome(self):
        """Test schema validation for refinement_outcome events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            before_fragment = PlanFragment(
                changed_steps=[
                    PlanStep(step_id="step_1", description="Original step", status="pending")
                ],
                unchanged_step_ids=["step_2"]
            )
            after_fragment = PlanFragment(
                changed_steps=[
                    PlanStep(step_id="step_1", description="Updated step", status="complete")
                ],
                unchanged_step_ids=["step_2"]
            )
            logger.log_refinement_outcome(
                correlation_id=correlation_id,
                before_plan_fragment=before_fragment,
                after_plan_fragment=after_fragment,
                refinement_actions=[{"type": "modify_step", "step_id": "step_1"}]
            )
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "refinement_outcome"
                assert "correlation_id" in entry
                assert "before_plan_fragment" in entry
                assert "after_plan_fragment" in entry
                assert "refinement_actions" in entry
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_evaluation_outcome(self):
        """Test schema validation for evaluation_outcome events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            convergence_summary = ConvergenceAssessmentSummary(
                converged=False,
                reason_codes=["validation_issues"],
                scores={"completeness": 0.8},
                pass_number=1
            )
            validation_summary = ValidationIssuesSummary(
                total_issues=2,
                critical_count=0,
                error_count=1,
                warning_count=1,
                info_count=0
            )
            logger.log_evaluation_outcome(
                correlation_id=correlation_id,
                convergence_assessment_summary=convergence_summary,
                validation_issues_summary=validation_summary
            )
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "evaluation_outcome"
                assert "correlation_id" in entry
                assert "convergence_assessment" in entry
                assert "validation_report" in entry
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_error_event(self):
        """Test schema validation for error events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution"
            )
            logger.log_error(correlation_id=correlation_id, error=error_record)
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "error"
                assert "correlation_id" in entry
                assert "original_error" in entry
                assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
                assert entry["original_error"]["severity"] == "ERROR"
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_error_recovery(self):
        """Test schema validation for error_recovery events (T125)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution"
            )
            logger.log_error_recovery(
                correlation_id=correlation_id,
                original_error=error_record,
                recovery_action="retry",
                recovery_outcome="success"
            )
            
            with open(log_file, 'r') as f:
                entry = json.loads(f.readline())
                
                # Verify required fields
                assert entry["event"] == "error_recovery"
                assert "correlation_id" in entry
                assert "original_error" in entry
                assert entry["recovery_action"] == "retry"
                assert entry["recovery_outcome"] == "success"
                assert "timestamp" in entry
        finally:
            log_file.unlink(missing_ok=True)

    def test_schema_validation_cycle_event(self):
        """Test schema validation for cycle events (backward compatibility) (T125)."""
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
            logger.log_entry(entry)
            
            with open(log_file, 'r') as f:
                entry_dict = json.loads(f.readline())
                
                # Verify required fields
                assert entry_dict["event"] == "cycle"
                assert entry_dict["step_number"] == 1
                assert "plan_state" in entry_dict
                assert "llm_output" in entry_dict
                assert "supervisor_actions" in entry_dict
                assert "tool_calls" in entry_dict
                assert "ttl_remaining" in entry_dict
                assert "errors" in entry_dict
                assert "timestamp" in entry_dict
        finally:
            log_file.unlink(missing_ok=True)

    def test_log_schema_backward_compatibility(self):
        """Test that log schema maintains backward compatibility (T126)."""
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
            
            # Read and verify old format is still valid
            with open(log_file, 'r') as f:
                entry_dict = json.loads(f.readline())
                
                # Old format fields should still be present
                assert "step_number" in entry_dict
                assert "plan_state" in entry_dict
                assert "llm_output" in entry_dict
                assert "supervisor_actions" in entry_dict
                assert "tool_calls" in entry_dict
                assert "ttl_remaining" in entry_dict
                assert "errors" in entry_dict
                
                # New format fields should be present with defaults
                assert entry_dict["event"] == "cycle"
                assert "timestamp" in entry_dict
                
                # Schema should be backward compatible
                # Old parsers should still be able to read old format
        finally:
            log_file.unlink(missing_ok=True)

