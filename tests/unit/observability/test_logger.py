"""Unit tests for JSONL logger."""

import json
import tempfile
from pathlib import Path

import pytest

from aeon.observability.logger import JSONLLogger
from aeon.observability.models import LogEntry


class TestJSONLLogger:
    """Test JSONL logger implementation."""

    def test_logger_initializes_with_file_path(self):
        """Test that logger initializes with a file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            assert logger.file_path == file_path
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_writes_to_file(self):
        """Test that log_entry writes a JSONL line to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read file and verify content
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert entry["step_number"] == 1
                assert entry["plan_state"]["goal"] == "test"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_appends_multiple_entries(self):
        """Test that multiple log entries are appended to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            for i in range(3):
                log_entry = LogEntry(
                    step_number=i + 1,
                    plan_state={"goal": f"test_{i}", "steps": []},
                    llm_output={"text": f"response_{i}"},
                    ttl_remaining=10 - i,
                    timestamp=f"2024-01-01T00:00:{i:02d}Z"
                )
                logger.log_entry(log_entry)
            
            # Read file and verify all entries
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                for i, line in enumerate(lines):
                    entry = json.loads(line)
                    assert entry["step_number"] == i + 1
                    assert entry["ttl_remaining"] == 10 - i
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_includes_all_fields(self):
        """Test that log entry includes all required fields."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                supervisor_actions=[{"type": "json_repair"}],
                tool_calls=[{"tool_name": "echo", "arguments": {"message": "hello"}}],
                ttl_remaining=5,
                errors=[{"type": "ToolError", "message": "test error"}],
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read and verify all fields
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert "step_number" in entry
                assert "plan_state" in entry
                assert "llm_output" in entry
                assert "supervisor_actions" in entry
                assert "tool_calls" in entry
                assert "ttl_remaining" in entry
                assert "errors" in entry
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_entry_handles_empty_lists(self):
        """Test that log entry handles empty optional lists."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            # Read and verify empty lists are present
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["supervisor_actions"] == []
                assert entry["tool_calls"] == []
                assert entry["errors"] == []
        finally:
            file_path.unlink(missing_ok=True)

    def test_logger_creates_file_if_not_exists(self):
        """Test that logger creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            logger = JSONLLogger(file_path=file_path)
            
            log_entry = LogEntry(
                step_number=1,
                plan_state={"goal": "test", "steps": []},
                llm_output={"text": "test response"},
                ttl_remaining=10,
                timestamp="2024-01-01T00:00:00Z"
            )
            
            logger.log_entry(log_entry)
            
            assert file_path.exists()
            with open(file_path, 'r') as f:
                assert len(f.readlines()) == 1


class TestPhaseAwareLogging:
    """Test phase-aware logging methods (T028-T032)."""

    def test_log_phase_entry_creates_correct_entry(self):
        """Test that log_phase_entry creates a phase_entry event with correlation_id (T028)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            logger.log_phase_entry(
                phase="A",
                correlation_id=correlation_id,
                pass_number=0,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "phase_entry"
                assert entry["correlation_id"] == correlation_id
                assert entry["phase"] == "A"
                assert entry["pass_number"] == 0
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_phase_exit_creates_correct_entry(self):
        """Test that log_phase_exit creates a phase_exit event with duration and outcome (T028)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            logger.log_phase_exit(
                phase="A",
                correlation_id=correlation_id,
                duration=1.23,
                outcome="success",
                pass_number=0,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "phase_exit"
                assert entry["correlation_id"] == correlation_id
                assert entry["phase"] == "A"
                assert entry["duration"] == 1.23
                assert entry["outcome"] == "success"
                assert entry["pass_number"] == 0
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_state_transition_creates_correct_entry(self):
        """Test that log_state_transition creates a state_transition event with before/after states (T029)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            before_state = {"component": "plan", "step_count": 3}
            after_state = {"component": "plan", "step_count": 4}
            
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state,
                after_state=after_state,
                transition_reason="refinement_applied",
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "state_transition"
                assert entry["correlation_id"] == correlation_id
                assert entry["component"] == "plan"
                assert entry["before_state"] == before_state
                assert entry["after_state"] == after_state
                assert entry["transition_reason"] == "refinement_applied"
                assert entry["pass_number"] == 1
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_refinement_outcome_creates_correct_entry(self):
        """Test that log_refinement_outcome creates a refinement_outcome event (T030)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            from aeon.observability.models import PlanFragment
            from aeon.plan.models import PlanStep
            
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            before_fragment = PlanFragment(
                changed_steps=[],
                unchanged_step_ids=["step1", "step2"],
            )
            after_fragment = PlanFragment(
                changed_steps=[PlanStep(step_id="step3", description="New step", status="pending")],
                unchanged_step_ids=["step1", "step2"],
            )
            refinement_actions = [{"action_type": "ADD", "new_step": {"step_id": "step3"}}]
            
            logger.log_refinement_outcome(
                correlation_id=correlation_id,
                before_plan_fragment=before_fragment,
                after_plan_fragment=after_fragment,
                refinement_actions=refinement_actions,
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "refinement_outcome"
                assert entry["correlation_id"] == correlation_id
                assert "before_plan_fragment" in entry
                assert "after_plan_fragment" in entry
                assert entry["refinement_actions"] == refinement_actions
                assert entry["pass_number"] == 1
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_evaluation_outcome_creates_correct_entry(self):
        """Test that log_evaluation_outcome creates an evaluation_outcome event (T031)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            convergence_assessment = {"converged": True, "reason_codes": ["all_steps_complete"]}
            validation_report = {"total_issues": 0, "critical_count": 0}
            
            logger.log_evaluation_outcome(
                correlation_id=correlation_id,
                convergence_assessment=convergence_assessment,
                validation_report=validation_report,
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "evaluation_outcome"
                assert entry["correlation_id"] == correlation_id
                assert entry["convergence_assessment"] == convergence_assessment
                assert entry["validation_report"] == validation_report
                assert entry["pass_number"] == 1
                assert "timestamp" in entry
        finally:
            file_path.unlink(missing_ok=True)

    def test_correlation_id_persistence_across_phases(self):
        """Test that correlation_id persists across multiple phase entries (T032)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            # Log multiple phase entries with same correlation_id
            logger.log_phase_entry(phase="A", correlation_id=correlation_id, pass_number=0)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success", pass_number=0)
            logger.log_phase_entry(phase="B", correlation_id=correlation_id, pass_number=0)
            logger.log_phase_exit(phase="B", correlation_id=correlation_id, duration=2.0, outcome="success", pass_number=0)
            
            # Read and verify all entries have same correlation_id
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 4
                for line in lines:
                    entry = json.loads(line)
                    assert entry["correlation_id"] == correlation_id
        finally:
            file_path.unlink(missing_ok=True)

    def test_logging_methods_are_non_blocking(self):
        """Test that logging methods fail silently on errors (T021)."""
        # Create logger with invalid file path (directory instead of file)
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = Path(tmpdir)  # This is a directory, not a file
            
            logger = JSONLLogger(file_path=invalid_path)
            correlation_id = "test-correlation-id-123"
            
            # These should not raise exceptions
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state={},
                after_state={},
                transition_reason="test",
            )
            
            # If we get here without exception, the methods are non-blocking
            assert True

    def test_log_error_writes_error_event(self):
        """Test that log_error writes an error event to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            from aeon.observability.models import ErrorRecord, ErrorSeverity
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution",
            )
            
            logger.log_error(
                correlation_id=correlation_id,
                error=error_record,
                step_id="step_1",
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert entry["event"] == "error"
                assert entry["correlation_id"] == correlation_id
                assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
                assert entry["original_error"]["context"]["step_id"] == "step_1"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_error_recovery_writes_recovery_event(self):
        """Test that log_error_recovery writes a recovery event to file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-123"
            
            from aeon.observability.models import ErrorRecord, ErrorSeverity
            original_error = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Original error",
                affected_component="execution",
            )
            
            logger.log_error_recovery(
                correlation_id=correlation_id,
                original_error=original_error,
                recovery_action="retry",
                recovery_outcome="success",
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                entry = json.loads(lines[0])
                assert entry["event"] == "error_recovery"
                assert entry["correlation_id"] == correlation_id
                assert entry["recovery_action"] == "retry"
                assert entry["recovery_outcome"] == "success"
                assert entry["original_error"]["code"] == "AEON.EXECUTION.001"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_error_includes_correlation_id(self):
        """Test that log_error includes correlation_id in entry."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-456"
            
            from aeon.observability.models import ErrorRecord, ErrorSeverity
            error_record = ErrorRecord(
                code="AEON.REFINEMENT.001",
                severity=ErrorSeverity.ERROR,
                message="Refinement error",
                affected_component="refinement",
            )
            
            logger.log_error(correlation_id=correlation_id, error=error_record)
            
            with open(file_path, 'r') as f:
                entry = json.loads(f.readline())
                assert entry["correlation_id"] == correlation_id
        finally:
            file_path.unlink(missing_ok=True)


class TestUS3DebugLogging:
    """Test US3 debug logging features (T077-T079)."""

    def test_log_refinement_outcome_with_evaluation_signals(self):
        """Test that log_refinement_outcome includes evaluation signals (T077)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            from aeon.observability.models import (
                PlanFragment,
                ConvergenceAssessmentSummary,
                ValidationIssuesSummary,
            )
            from aeon.plan.models import PlanStep
            
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            before_fragment = PlanFragment(
                changed_steps=[],
                unchanged_step_ids=["step1", "step2"],
            )
            after_fragment = PlanFragment(
                changed_steps=[PlanStep(step_id="step3", description="New step", status="pending")],
                unchanged_step_ids=["step1", "step2"],
            )
            refinement_actions = [{"action_type": "ADD", "new_step": {"step_id": "step3"}}]
            
            # Create evaluation signals with summaries
            convergence_summary = ConvergenceAssessmentSummary(
                converged=False,
                reason_codes=["completeness_below_threshold_0.8_<_0.95"],
                scores={"completeness": 0.8, "coherence": 0.9},
                pass_number=1,
            )
            validation_summary = ValidationIssuesSummary(
                total_issues=2,
                critical_count=0,
                error_count=1,
                warning_count=1,
                info_count=0,
            )
            
            logger.log_refinement_outcome(
                correlation_id=correlation_id,
                before_plan_fragment=before_fragment,
                after_plan_fragment=after_fragment,
                refinement_actions=refinement_actions,
                convergence_assessment_summary=convergence_summary,
                validation_issues_summary=validation_summary,
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "refinement_outcome"
                assert entry["correlation_id"] == correlation_id
                assert "evaluation_signals" in entry
                assert "convergence_assessment" in entry["evaluation_signals"]
                assert "validation_issues" in entry["evaluation_signals"]
                assert entry["evaluation_signals"]["convergence_assessment"]["converged"] is False
                assert entry["evaluation_signals"]["convergence_assessment"]["reason_codes"] == ["completeness_below_threshold_0.8_<_0.95"]
                assert entry["evaluation_signals"]["validation_issues"]["total_issues"] == 2
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_step_execution_outcome(self):
        """Test that log_step_execution_outcome logs step execution results (T078)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            logger.log_step_execution_outcome(
                correlation_id=correlation_id,
                step_id="step_1",
                execution_mode="tool",
                success=True,
                result={"output": "test result"},
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "state_transition"
                assert entry["correlation_id"] == correlation_id
                assert entry["component"] == "execution"
                assert entry["before_state"]["step_id"] == "step_1"
                assert entry["after_state"]["step_id"] == "step_1"
                assert entry["after_state"]["success"] is True
                assert entry["after_state"]["result"]["output"] == "test result"
                assert entry["transition_reason"] == "step_execution_success"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_step_execution_outcome_failure(self):
        """Test that log_step_execution_outcome logs step execution failures (T078)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            logger.log_step_execution_outcome(
                correlation_id=correlation_id,
                step_id="step_1",
                execution_mode="llm",
                success=False,
                error="Execution failed",
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "state_transition"
                assert entry["after_state"]["success"] is False
                assert entry["after_state"]["error"] == "Execution failed"
                assert entry["transition_reason"] == "step_execution_failure"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_tool_invocation_result(self):
        """Test that log_tool_invocation_result logs tool invocation results (T078)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            logger.log_tool_invocation_result(
                correlation_id=correlation_id,
                step_id="step_1",
                tool_name="echo",
                success=True,
                result={"output": "hello"},
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "state_transition"
                assert entry["correlation_id"] == correlation_id
                assert entry["before_state"]["tool_name"] == "echo"
                assert entry["after_state"]["tool_name"] == "echo"
                assert entry["after_state"]["success"] is True
                assert entry["transition_reason"] == "tool_invocation_success"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_step_status_change(self):
        """Test that log_step_status_change logs step status transitions (T078)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            logger.log_step_status_change(
                correlation_id=correlation_id,
                step_id="step_1",
                old_status="pending",
                new_status="running",
                reason="step_execution_started",
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "state_transition"
                assert entry["correlation_id"] == correlation_id
                assert entry["component"] == "execution"
                assert entry["before_state"]["status"] == "pending"
                assert entry["after_state"]["status"] == "running"
                assert entry["transition_reason"] == "step_execution_started"
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_evaluation_outcome_with_convergence_assessment(self):
        """Test that log_evaluation_outcome includes convergence assessment with reason codes (T079)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            from aeon.observability.models import (
                ConvergenceAssessmentSummary,
                ValidationIssuesSummary,
            )
            
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            convergence_summary = ConvergenceAssessmentSummary(
                converged=False,
                reason_codes=[
                    "completeness_below_threshold_0.8_<_0.95",
                    "coherence_below_threshold_0.85_<_0.90",
                ],
                scores={"completeness": 0.8, "coherence": 0.85},
                pass_number=1,
            )
            validation_summary = ValidationIssuesSummary(
                total_issues=3,
                critical_count=0,
                error_count=2,
                warning_count=1,
                info_count=0,
            )
            
            logger.log_evaluation_outcome(
                correlation_id=correlation_id,
                convergence_assessment_summary=convergence_summary,
                validation_issues_summary=validation_summary,
                pass_number=1,
            )
            
            # Read and verify entry
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["event"] == "evaluation_outcome"
                assert entry["correlation_id"] == correlation_id
                assert "convergence_assessment" in entry
                assert entry["convergence_assessment"]["converged"] is False
                assert len(entry["convergence_assessment"]["reason_codes"]) == 2
                assert "completeness_below_threshold_0.8_<_0.95" in entry["convergence_assessment"]["reason_codes"]
                assert "evaluation_signals" in entry
                assert "convergence_assessment" in entry["evaluation_signals"]
                assert "validation_issues" in entry["evaluation_signals"]
        finally:
            file_path.unlink(missing_ok=True)

    def test_log_evaluation_outcome_explains_non_convergence(self):
        """Test that convergence assessment logging explains why convergence was not achieved (T079)."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        try:
            from aeon.observability.models import ConvergenceAssessmentSummary
            
            logger = JSONLLogger(file_path=file_path)
            correlation_id = "test-correlation-id-us3"
            
            # Test with reason codes explaining non-convergence
            convergence_summary = ConvergenceAssessmentSummary(
                converged=False,
                reason_codes=[
                    "completeness_below_threshold_0.7_<_0.95",
                    "consistency_not_aligned",
                ],
                scores={"completeness": 0.7, "coherence": 0.95},
                pass_number=2,
            )
            
            logger.log_evaluation_outcome(
                correlation_id=correlation_id,
                convergence_assessment_summary=convergence_summary,
                pass_number=2,
            )
            
            # Read and verify entry explains non-convergence
            with open(file_path, 'r') as f:
                entry = json.loads(f.read())
                assert entry["convergence_assessment"]["converged"] is False
                reason_codes = entry["convergence_assessment"]["reason_codes"]
                assert len(reason_codes) > 0
                # Reason codes should explain why convergence was not achieved
                assert any("completeness" in code for code in reason_codes)
                assert any("consistency" in code for code in reason_codes)
        finally:
            file_path.unlink(missing_ok=True)

