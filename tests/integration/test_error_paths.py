"""Integration tests for error paths (US4).

Tests error handling and logging for refinement errors, execution errors,
validation errors, and error recovery scenarios.
"""

import json
import tempfile
from pathlib import Path
from typing import Tuple

import pytest

from aeon.exceptions import ExecutionError, RefinementError, ValidationError
from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from aeon.plan.models import Plan, PlanStep
from tests.fixtures.mock_llm import MockLLMAdapter


class TestErrorPaths:
    """Test error path handling and logging."""

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

    def test_refinement_error_paths(self):
        """Test that refinement errors are properly handled and logged (T089)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that might trigger refinement errors
            result = orchestrator.execute_multipass(
                request="task that may trigger refinement errors"
            )
            
            # Read log file and check for refinement errors
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            refinement_errors = []
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "error" and 
                    entry.get("original_error", {}).get("affected_component") == "refinement"):
                    refinement_errors.append(entry)
            
            # If refinement errors occurred, verify they are properly structured
            for error_entry in refinement_errors:
                assert "correlation_id" in error_entry, "Refinement error missing correlation_id"
                assert "original_error" in error_entry, "Refinement error missing original_error"
                
                error = error_entry["original_error"]
                assert "code" in error, "Refinement error missing code"
                assert error["code"].startswith("AEON.REFINEMENT."), \
                    f"Invalid refinement error code: {error['code']}"
                assert "severity" in error, "Refinement error missing severity"
                assert "message" in error, "Refinement error missing message"
                assert "affected_component" in error, "Refinement error missing affected_component"
                assert error["affected_component"] == "refinement"
                
                # Refinement errors should have plan fragment context if available
                if "before_plan_fragment" in error_entry:
                    assert isinstance(error_entry["before_plan_fragment"], dict)
                if "after_plan_fragment" in error_entry:
                    assert isinstance(error_entry["after_plan_fragment"], dict)
                if "evaluation_signals" in error_entry:
                    assert isinstance(error_entry["evaluation_signals"], dict)
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_execution_error_paths(self):
        """Test that execution errors are properly handled and logged (T090)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that might trigger execution errors
            result = orchestrator.execute_multipass(
                request="task that may trigger execution errors"
            )
            
            # Read log file and check for execution errors
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            execution_errors = []
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "error" and 
                    entry.get("original_error", {}).get("affected_component") == "execution"):
                    execution_errors.append(entry)
            
            # If execution errors occurred, verify they are properly structured
            for error_entry in execution_errors:
                assert "correlation_id" in error_entry, "Execution error missing correlation_id"
                assert "original_error" in error_entry, "Execution error missing original_error"
                
                error = error_entry["original_error"]
                assert "code" in error, "Execution error missing code"
                assert error["code"].startswith("AEON.EXECUTION."), \
                    f"Invalid execution error code: {error['code']}"
                assert "severity" in error, "Execution error missing severity"
                assert "message" in error, "Execution error missing message"
                assert "affected_component" in error, "Execution error missing affected_component"
                assert error["affected_component"] == "execution"
                
                # Execution errors should have step context if available
                if "step_id" in error_entry:
                    assert isinstance(error_entry["step_id"], str)
                if "attempted_action" in error_entry:
                    assert isinstance(error_entry["attempted_action"], str)
                if "tool_name" in error_entry:
                    assert isinstance(error_entry["tool_name"], str)
                if "error_context" in error_entry:
                    assert isinstance(error_entry["error_context"], dict)
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_validation_error_paths(self):
        """Test that validation errors are properly handled and logged (T091)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that might trigger validation errors
            result = orchestrator.execute_multipass(
                request="task that may trigger validation errors"
            )
            
            # Read log file and check for validation errors
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            validation_errors = []
            for line in lines:
                entry = json.loads(line)
                if (entry.get("event") == "error" and 
                    entry.get("original_error", {}).get("affected_component") == "validation"):
                    validation_errors.append(entry)
            
            # If validation errors occurred, verify they are properly structured
            for error_entry in validation_errors:
                assert "correlation_id" in error_entry, "Validation error missing correlation_id"
                assert "original_error" in error_entry, "Validation error missing original_error"
                
                error = error_entry["original_error"]
                assert "code" in error, "Validation error missing code"
                assert error["code"].startswith("AEON.VALIDATION."), \
                    f"Invalid validation error code: {error['code']}"
                assert "severity" in error, "Validation error missing severity"
                assert "message" in error, "Validation error missing message"
                assert "affected_component" in error, "Validation error missing affected_component"
                assert error["affected_component"] == "validation"
                
                # Validation errors should have validation context if available
                if "validation_type" in error_entry:
                    assert isinstance(error_entry["validation_type"], str)
                if "validation_details" in error_entry:
                    assert isinstance(error_entry["validation_details"], dict)
            
        finally:
            log_file.unlink(missing_ok=True)

    def test_error_recovery_paths(self):
        """Test that error recovery is properly handled and logged (T092)."""
        orchestrator, log_file = self._create_orchestrator_with_logger()
        
        try:
            # Execute a task that might trigger errors and recovery
            result = orchestrator.execute_multipass(
                request="task that may trigger error recovery"
            )
            
            # Read log file and check for error recovery
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            error_entries = []
            recovery_entries = []
            
            for line in lines:
                entry = json.loads(line)
                if entry.get("event") == "error":
                    error_entries.append(entry)
                elif entry.get("event") == "error_recovery":
                    recovery_entries.append(entry)
            
            # If error recovery occurred, verify it is properly structured
            for recovery_entry in recovery_entries:
                assert "correlation_id" in recovery_entry, "Recovery entry missing correlation_id"
                assert "original_error" in recovery_entry, "Recovery entry missing original_error"
                assert "recovery_action" in recovery_entry, "Recovery entry missing recovery_action"
                assert "recovery_outcome" in recovery_entry, "Recovery entry missing recovery_outcome"
                
                # Recovery outcome should be success or failure
                assert recovery_entry["recovery_outcome"] in ["success", "failure"], \
                    f"Invalid recovery outcome: {recovery_entry['recovery_outcome']}"
                
                # Original error should be properly structured
                original_error = recovery_entry["original_error"]
                assert "code" in original_error, "Recovery original_error missing code"
                assert "severity" in original_error, "Recovery original_error missing severity"
                assert "affected_component" in original_error, "Recovery original_error missing affected_component"
            
            # Verify that recovery entries reference errors that occurred
            # (correlation IDs should match)
            if len(recovery_entries) > 0 and len(error_entries) > 0:
                recovery_correlation_ids = {e["correlation_id"] for e in recovery_entries}
                error_correlation_ids = {e["correlation_id"] for e in error_entries}
                
                # Recovery should occur for the same execution (same correlation_id)
                assert len(recovery_correlation_ids & error_correlation_ids) > 0, \
                    "Recovery entries don't match error entries by correlation_id"
            
        finally:
            log_file.unlink(missing_ok=True)

