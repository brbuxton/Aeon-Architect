"""Integration tests for error logging."""

import json
import tempfile
from pathlib import Path

import pytest

from aeon.exceptions import ExecutionError, RefinementError, ValidationError
from aeon.observability.logger import JSONLLogger
from aeon.observability.models import ErrorRecord, ErrorSeverity


class TestErrorLoggingIntegration:
    """Integration tests for error logging across components."""

    def test_refinement_error_logging_with_all_fields(self):
        """Test that refinement errors log with all required fields (T060)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-refinement"
            
            # Create refinement error
            refinement_error = RefinementError("Failed to apply refinement action")
            error_record = refinement_error.to_error_record(
                context={"refinement_actions_count": 2}
            )
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                before_plan_fragment={"changed_steps": [], "unchanged_step_ids": ["step_1"]},
                after_plan_fragment={"changed_steps": [], "unchanged_step_ids": ["step_1"]},
            )
            
            # Verify all required fields are present
            with open(file_path, 'r') as f:
                entry = json.loads(f.readline())
                assert entry["event"] == "error"
                assert entry["correlation_id"] == correlation_id
                assert entry["original_error"]["code"] == "AEON.REFINEMENT.001"
                assert entry["original_error"]["severity"] == "ERROR"
                assert entry["original_error"]["message"] == "Failed to apply refinement action"
                assert entry["original_error"]["affected_component"] == "refinement"
                assert "before_plan_fragment" in entry
                assert "after_plan_fragment" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_execution_error_logging_with_all_fields(self):
        """Test that execution errors log with all required fields (T061)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-execution"
            
            # Create execution error
            execution_error = ExecutionError("Step execution failed")
            error_record = execution_error.to_error_record()
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                step_id="step_1",
                attempted_action="tool_invoke",
                tool_name="calculator",
                error_context={"tool_args": {"x": 5, "y": 10}},
            )
            
            # Verify all required fields are present
            with open(file_path, 'r') as f:
                entry = json.loads(f.readline())
                assert entry["event"] == "error"
                assert entry["correlation_id"] == correlation_id
                assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
                assert entry["original_error"]["severity"] == "ERROR"
                assert entry["original_error"]["context"]["step_id"] == "step_1"
                assert entry["original_error"]["context"]["attempted_action"] == "tool_invoke"
                assert entry["original_error"]["context"]["tool_name"] == "calculator"
        finally:
            file_path.unlink(missing_ok=True)

    def test_validation_error_logging_with_all_fields(self):
        """Test that validation errors log with all required fields (T062)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-validation"
            
            # Create validation error
            validation_error = ValidationError("Validation check failed")
            error_record = validation_error.to_error_record()
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                validation_type="semantic",
                validation_details={"artifact_type": "plan", "issue_count": 2},
            )
            
            # Verify all required fields are present
            with open(file_path, 'r') as f:
                entry = json.loads(f.readline())
                assert entry["event"] == "error"
                assert entry["correlation_id"] == correlation_id
                assert entry["original_error"]["code"] == "AEON.VALIDATION.001"
                assert entry["original_error"]["severity"] == "ERROR"
                assert entry["original_error"]["context"]["validation_type"] == "semantic"
                assert entry["original_error"]["context"]["validation_details"]["artifact_type"] == "plan"
        finally:
            file_path.unlink(missing_ok=True)

    def test_error_recovery_logging(self):
        """Test that error recovery attempts are logged (T063)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-recovery"
            
            # Create original error
            original_error = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Tool execution failed",
                affected_component="execution",
            )
            
            # Log recovery attempt
            logger.log_error_recovery(
                correlation_id=correlation_id,
                original_error=original_error,
                recovery_action="supervisor_repair",
                recovery_outcome="success",
            )
            
            # Verify recovery entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.readline())
                assert entry["event"] == "error_recovery"
                assert entry["correlation_id"] == correlation_id
                assert entry["recovery_action"] == "supervisor_repair"
                assert entry["recovery_outcome"] == "success"
                assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
        finally:
            file_path.unlink(missing_ok=True)

    def test_structured_error_fields_completeness(self):
        """Test that 100% of error cases contain required fields (T064)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-completeness"
            
            # Test all error types
            errors = [
                (RefinementError("Refinement failed"), "refinement"),
                (ExecutionError("Execution failed"), "execution"),
                (ValidationError("Validation failed"), "validation"),
            ]
            
            for error, component in errors:
                error_record = error.to_error_record()
                logger.log_error(correlation_id=correlation_id, error=error_record)
            
            # Verify all entries have required fields
            with open(file_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    assert entry["event"] == "error"
                    assert entry["correlation_id"] == correlation_id
                    assert "original_error" in entry
                    assert "code" in entry["original_error"]
                    assert "severity" in entry["original_error"]
                    assert "message" in entry["original_error"]
                    assert "affected_component" in entry["original_error"]
                    assert entry["original_error"]["code"].startswith("AEON.")
        finally:
            file_path.unlink(missing_ok=True)


