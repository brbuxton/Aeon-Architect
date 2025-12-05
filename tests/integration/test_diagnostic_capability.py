"""Integration tests for diagnostic capability validation (T127-T128)."""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from aeon.observability.helpers import generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.observability.models import ErrorRecord, ErrorSeverity, PlanFragment, PlanStateSlice
from aeon.plan.models import PlanStep


class TestDiagnosticCapability:
    """Test that ≥90% of failures are diagnosable from logs."""

    def _create_logger(self) -> tuple[JSONLLogger, Path]:
        """Create logger with temp file and return logger and file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        return logger, file_path

    def _read_log_entries(self, log_file: Path) -> list[dict]:
        """Read all log entries from file."""
        with open(log_file, 'r') as f:
            return [json.loads(line) for line in f.readlines()]

    def test_refinement_error_diagnosable(self):
        """Test that refinement errors are diagnosable from logs."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Log refinement error with context
            error_record = ErrorRecord(
                code="AEON.REFINEMENT.001",
                severity=ErrorSeverity.ERROR,
                message="Failed to apply refinement action: invalid step_id",
                affected_component="refinement",
                context={"step_id": "step_1", "attempted_action": "modify_step"}
            )
            
            before_fragment = PlanFragment(
                changed_steps=[
                    PlanStep(step_id="step_1", description="Original step", status="pending")
                ],
                unchanged_step_ids=["step_2"]
            )
            after_fragment = PlanFragment(
                changed_steps=[
                    PlanStep(step_id="step_1", description="Updated step", status="pending")
                ],
                unchanged_step_ids=["step_2"]
            )
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                before_plan_fragment=before_fragment.model_dump(),
                after_plan_fragment=after_fragment.model_dump()
            )
            
            # Read log and verify diagnostic information
            entries = self._read_log_entries(log_file)
            assert len(entries) == 1
            
            entry = entries[0]
            
            # Verify error code is present
            assert "original_error" in entry
            assert entry["original_error"]["code"] == "AEON.REFINEMENT.001"
            assert entry["original_error"]["severity"] == "ERROR"
            assert entry["original_error"]["message"] is not None
            assert entry["original_error"]["affected_component"] == "refinement"
            
            # Verify context is present
            assert "context" in entry["original_error"]
            assert entry["original_error"]["context"]["step_id"] == "step_1"
            assert entry["original_error"]["context"]["attempted_action"] == "modify_step"
            
            # Verify plan fragments are present
            assert "before_plan_fragment" in entry
            assert "after_plan_fragment" in entry
            
            # Verify correlation ID for traceability
            assert entry["correlation_id"] == correlation_id
        finally:
            log_file.unlink(missing_ok=True)

    def test_execution_error_diagnosable(self):
        """Test that execution errors are diagnosable from logs."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Log execution error with context
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Step execution failed: tool not found",
                affected_component="execution",
                context={"step_id": "step_1"}
            )
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                step_id="step_1",
                attempted_action="invoke_tool",
                tool_name="missing_tool",
                error_context={"tool_registry": "available_tools"}
            )
            
            # Read log and verify diagnostic information
            entries = self._read_log_entries(log_file)
            assert len(entries) == 1
            
            entry = entries[0]
            
            # Verify error code is present
            assert "original_error" in entry
            assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
            assert entry["original_error"]["severity"] == "ERROR"
            assert entry["original_error"]["message"] is not None
            assert entry["original_error"]["affected_component"] == "execution"
            
            # Verify context is present
            assert "context" in entry["original_error"]
            assert entry["original_error"]["context"]["step_id"] == "step_1"
            assert entry["original_error"]["context"]["attempted_action"] == "invoke_tool"
            assert entry["original_error"]["context"]["tool_name"] == "missing_tool"
            
            # Verify correlation ID for traceability
            assert entry["correlation_id"] == correlation_id
        finally:
            log_file.unlink(missing_ok=True)

    def test_validation_error_diagnosable(self):
        """Test that validation errors are diagnosable from logs."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Log validation error with context
            error_record = ErrorRecord(
                code="AEON.VALIDATION.001",
                severity=ErrorSeverity.ERROR,
                message="Semantic validation failed: missing required field",
                affected_component="validation",
                context={}
            )
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                validation_type="semantic",
                validation_details={"missing_field": "tool_name", "step_id": "step_1"}
            )
            
            # Read log and verify diagnostic information
            entries = self._read_log_entries(log_file)
            assert len(entries) == 1
            
            entry = entries[0]
            
            # Verify error code is present
            assert "original_error" in entry
            assert entry["original_error"]["code"] == "AEON.VALIDATION.001"
            assert entry["original_error"]["severity"] == "ERROR"
            assert entry["original_error"]["message"] is not None
            assert entry["original_error"]["affected_component"] == "validation"
            
            # Verify context is present
            assert "context" in entry["original_error"]
            assert entry["original_error"]["context"]["validation_type"] == "semantic"
            assert "validation_details" in entry["original_error"]["context"]
            
            # Verify correlation ID for traceability
            assert entry["correlation_id"] == correlation_id
        finally:
            log_file.unlink(missing_ok=True)

    def test_error_recovery_diagnosable(self):
        """Test that error recovery attempts are diagnosable from logs."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Log original error
            original_error = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Step execution failed",
                affected_component="execution"
            )
            logger.log_error(correlation_id=correlation_id, error=original_error)
            
            # Log recovery attempt
            logger.log_error_recovery(
                correlation_id=correlation_id,
                original_error=original_error,
                recovery_action="retry_with_fallback",
                recovery_outcome="success"
            )
            
            # Read log and verify diagnostic information
            entries = self._read_log_entries(log_file)
            assert len(entries) == 2
            
            # First entry should be error
            error_entry = entries[0]
            assert error_entry["event"] == "error"
            assert error_entry["original_error"]["code"] == "AEON.EXECUTION.001"
            
            # Second entry should be recovery
            recovery_entry = entries[1]
            assert recovery_entry["event"] == "error_recovery"
            assert recovery_entry["original_error"]["code"] == "AEON.EXECUTION.001"
            assert recovery_entry["recovery_action"] == "retry_with_fallback"
            assert recovery_entry["recovery_outcome"] == "success"
            
            # Both should have same correlation_id
            assert error_entry["correlation_id"] == correlation_id
            assert recovery_entry["correlation_id"] == correlation_id
        finally:
            log_file.unlink(missing_ok=True)

    def test_diagnostic_capability_threshold(self):
        """Test that ≥90% of failures are diagnosable from logs (T127)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Simulate various failure scenarios
            failure_scenarios = [
                {
                    "error": ErrorRecord(
                        code="AEON.REFINEMENT.001",
                        severity=ErrorSeverity.ERROR,
                        message="Refinement failed",
                        affected_component="refinement",
                        context={"step_id": "step_1"}
                    ),
                    "has_context": True,
                },
                {
                    "error": ErrorRecord(
                        code="AEON.EXECUTION.001",
                        severity=ErrorSeverity.ERROR,
                        message="Execution failed",
                        affected_component="execution",
                        context={"step_id": "step_2"}
                    ),
                    "has_context": True,
                },
                {
                    "error": ErrorRecord(
                        code="AEON.VALIDATION.001",
                        severity=ErrorSeverity.ERROR,
                        message="Validation failed",
                        affected_component="validation",
                        context={}
                    ),
                    "has_context": True,
                },
            ]
            
            # Log all failures
            for scenario in failure_scenarios:
                logger.log_error(correlation_id=correlation_id, error=scenario["error"])
            
            # Read log and verify diagnostic capability
            entries = self._read_log_entries(log_file)
            assert len(entries) == len(failure_scenarios)
            
            diagnosable_count = 0
            for entry in entries:
                # Check if entry has sufficient diagnostic information
                has_error_code = "original_error" in entry and "code" in entry["original_error"]
                has_severity = "original_error" in entry and "severity" in entry["original_error"]
                has_message = "original_error" in entry and "message" in entry["original_error"]
                has_component = "original_error" in entry and "affected_component" in entry["original_error"]
                has_correlation_id = "correlation_id" in entry and entry["correlation_id"] is not None
                
                if has_error_code and has_severity and has_message and has_component and has_correlation_id:
                    diagnosable_count += 1
            
            # Calculate diagnostic capability percentage
            diagnostic_capability = (diagnosable_count / len(entries)) * 100
            
            # SC-008: Diagnostic capability ≥90%
            assert diagnostic_capability >= 90.0, \
                f"Diagnostic capability {diagnostic_capability:.1f}% is below 90% threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_log_based_failure_diagnosis(self):
        """Test log-based failure diagnosis (T128)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Simulate a failure scenario with full logging
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            
            # Log state transition
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
                current_step_id="step_1",
                step_count=3,
                steps_status_summary={"pending": 2, "running": 1, "complete": 0}
            )
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="refinement_attempted"
            )
            
            # Log error
            error_record = ErrorRecord(
                code="AEON.REFINEMENT.001",
                severity=ErrorSeverity.ERROR,
                message="Refinement failed: invalid step_id",
                affected_component="refinement",
                context={"step_id": "step_1", "attempted_action": "modify_step"}
            )
            logger.log_error(correlation_id=correlation_id, error=error_record)
            
            # Log phase exit with failure
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="failure")
            
            # Read log and perform diagnosis
            entries = self._read_log_entries(log_file)
            
            # Verify we can diagnose the failure from logs
            error_entries = [e for e in entries if e.get("event") == "error"]
            assert len(error_entries) == 1
            
            error_entry = error_entries[0]
            
            # Diagnosis should be possible with:
            # 1. Error code
            assert "original_error" in error_entry
            assert error_entry["original_error"]["code"] == "AEON.REFINEMENT.001"
            
            # 2. Error message
            assert "message" in error_entry["original_error"]
            
            # 3. Affected component
            assert error_entry["original_error"]["affected_component"] == "refinement"
            
            # 4. Context
            assert "context" in error_entry["original_error"]
            assert error_entry["original_error"]["context"]["step_id"] == "step_1"
            
            # 5. Correlation ID for traceability
            assert error_entry["correlation_id"] == correlation_id
            
            # 6. Phase context
            phase_entries = [e for e in entries if e.get("event") == "phase_entry"]
            assert len(phase_entries) == 1
            assert phase_entries[0]["phase"] == "A"
            
            # 7. State transition context
            state_entries = [e for e in entries if e.get("event") == "state_transition"]
            assert len(state_entries) == 1
            assert state_entries[0]["transition_reason"] == "refinement_attempted"
        finally:
            log_file.unlink(missing_ok=True)

