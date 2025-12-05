"""Unit tests for observability models."""

import pytest

from aeon.observability.models import (
    ConvergenceAssessmentSummary,
    CorrelationID,
    ErrorRecord,
    ErrorSeverity,
    ExecutionStateSlice,
    PlanFragment,
    PlanStateSlice,
    RefinementStateSlice,
    ValidationIssuesSummary,
)
from aeon.plan.models import PlanStep, StepStatus


class TestCorrelationID:
    """Test CorrelationID model."""

    def test_correlation_id_valid_uuid(self):
        """Test that CorrelationID accepts valid UUID format."""
        correlation_id = CorrelationID(value="6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        assert correlation_id.value == "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

    def test_correlation_id_valid_fallback_format(self):
        """Test that CorrelationID accepts valid fallback format."""
        correlation_id = CorrelationID(value="aeon-2024-01-01T00:00:00-12345678")
        assert correlation_id.value == "aeon-2024-01-01T00:00:00-12345678"

    def test_correlation_id_invalid_format(self):
        """Test that CorrelationID rejects invalid format."""
        with pytest.raises(Exception):  # ValueError from validator
            CorrelationID(value="invalid-id")

    def test_correlation_id_is_frozen(self):
        """Test that CorrelationID is immutable."""
        correlation_id = CorrelationID(value="6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        with pytest.raises(Exception):  # ValidationError from Pydantic
            correlation_id.value = "new-value"


class TestErrorRecord:
    """Test ErrorRecord model."""

    def test_error_record_valid(self):
        """Test that ErrorRecord accepts valid data."""
        error = ErrorRecord(
            code="AEON.REFINEMENT.001",
            severity=ErrorSeverity.ERROR,
            message="Test error",
            affected_component="refinement",
        )
        assert error.code == "AEON.REFINEMENT.001"
        assert error.severity == ErrorSeverity.ERROR
        assert error.message == "Test error"
        assert error.affected_component == "refinement"

    def test_error_record_with_context(self):
        """Test that ErrorRecord accepts optional context."""
        error = ErrorRecord(
            code="AEON.EXECUTION.002",
            severity=ErrorSeverity.ERROR,
            message="Execution failed",
            affected_component="execution",
            context={"step_id": "step_1", "tool_name": "calculator"},
        )
        assert error.context == {"step_id": "step_1", "tool_name": "calculator"}

    def test_error_record_invalid_code_format(self):
        """Test that ErrorRecord rejects invalid error code format."""
        with pytest.raises(Exception):  # ValueError from validator
            ErrorRecord(
                code="INVALID.FORMAT",
                severity=ErrorSeverity.ERROR,
                message="Test",
                affected_component="test",
            )

    def test_error_record_empty_message(self):
        """Test that ErrorRecord rejects empty message."""
        with pytest.raises(Exception):  # ValueError from validator
            ErrorRecord(
                code="AEON.REFINEMENT.001",
                severity=ErrorSeverity.ERROR,
                message="",
                affected_component="refinement",
            )

    def test_error_record_all_severity_levels(self):
        """Test that ErrorRecord accepts all severity levels."""
        for severity in ErrorSeverity:
            error = ErrorRecord(
                code="AEON.REFINEMENT.001",
                severity=severity,
                message="Test",
                affected_component="refinement",
            )
            assert error.severity == severity


class TestPlanFragment:
    """Test PlanFragment model."""

    def test_plan_fragment_valid(self):
        """Test that PlanFragment accepts valid data."""
        step1 = PlanStep(step_id="step_1", description="Step 1", status=StepStatus.PENDING)
        step2 = PlanStep(step_id="step_2", description="Step 2", status=StepStatus.PENDING)
        
        fragment = PlanFragment(
            changed_steps=[step1],
            unchanged_step_ids=["step_2"],
        )
        assert len(fragment.changed_steps) == 1
        assert len(fragment.unchanged_step_ids) == 1

    def test_plan_fragment_no_overlap(self):
        """Test that PlanFragment rejects overlapping step IDs."""
        step1 = PlanStep(step_id="step_1", description="Step 1", status=StepStatus.PENDING)
        
        with pytest.raises(Exception):  # ValueError from validator
            PlanFragment(
                changed_steps=[step1],
                unchanged_step_ids=["step_1"],  # Overlap!
            )


class TestConvergenceAssessmentSummary:
    """Test ConvergenceAssessmentSummary model."""

    def test_convergence_assessment_summary_valid(self):
        """Test that ConvergenceAssessmentSummary accepts valid data."""
        summary = ConvergenceAssessmentSummary(
            converged=True,
            reason_codes=["all_steps_complete", "validation_passed"],
            pass_number=2,
        )
        assert summary.converged is True
        assert len(summary.reason_codes) == 2
        assert summary.pass_number == 2

    def test_convergence_assessment_summary_with_scores(self):
        """Test that ConvergenceAssessmentSummary accepts optional scores."""
        summary = ConvergenceAssessmentSummary(
            converged=True,
            reason_codes=["all_steps_complete"],
            scores={"completeness": 1.0, "coherence": 0.95},
            pass_number=1,
        )
        assert summary.scores == {"completeness": 1.0, "coherence": 0.95}

    def test_convergence_assessment_summary_empty_reason_codes(self):
        """Test that ConvergenceAssessmentSummary rejects empty reason_codes."""
        with pytest.raises(Exception):  # ValueError from validator
            ConvergenceAssessmentSummary(
                converged=True,
                reason_codes=[],
                pass_number=1,
            )


class TestValidationIssuesSummary:
    """Test ValidationIssuesSummary model."""

    def test_validation_issues_summary_valid(self):
        """Test that ValidationIssuesSummary accepts valid data."""
        summary = ValidationIssuesSummary(
            total_issues=3,
            critical_count=0,
            error_count=2,
            warning_count=1,
            info_count=0,
        )
        assert summary.total_issues == 3
        assert summary.error_count == 2
        assert summary.warning_count == 1

    def test_validation_issues_summary_total_matches_sum(self):
        """Test that ValidationIssuesSummary validates total matches sum."""
        summary = ValidationIssuesSummary(
            total_issues=5,
            critical_count=1,
            error_count=2,
            warning_count=1,
            info_count=1,
        )
        assert summary.total_issues == 5

    def test_validation_issues_summary_total_mismatch(self):
        """Test that ValidationIssuesSummary rejects total that doesn't match sum."""
        with pytest.raises(Exception):  # ValueError from validator
            ValidationIssuesSummary(
                total_issues=5,
                critical_count=1,
                error_count=2,
                warning_count=1,
                info_count=0,  # Sum is 4, not 5
            )


class TestStateSlices:
    """Test state slice models."""

    def test_plan_state_slice(self):
        """Test PlanStateSlice model."""
        slice_obj = PlanStateSlice(
            timestamp="2024-01-01T00:00:00",
            step_count=5,
            steps_status_summary={"pending": 2, "running": 1, "complete": 2},
        )
        assert slice_obj.component == "plan"
        assert slice_obj.step_count == 5

    def test_execution_state_slice(self):
        """Test ExecutionStateSlice model."""
        slice_obj = ExecutionStateSlice(
            timestamp="2024-01-01T00:00:00",
            step_status="running",
            tool_calls_count=3,
            errors_count=0,
        )
        assert slice_obj.component == "execution"
        assert slice_obj.step_status == "running"

    def test_refinement_state_slice(self):
        """Test RefinementStateSlice model."""
        slice_obj = RefinementStateSlice(
            timestamp="2024-01-01T00:00:00",
            refinement_type="add_step",
            changed_steps_count=2,
            added_steps_count=1,
            removed_steps_count=0,
        )
        assert slice_obj.component == "refinement"
        assert slice_obj.refinement_type == "add_step"


class TestErrorRecordConversion:
    """Test to_error_record conversion from exceptions."""

    def test_aeon_error_to_error_record(self):
        """Test that AeonError converts to ErrorRecord."""
        from aeon.exceptions import AeonError
        
        error = AeonError("Test error message")
        error_record = error.to_error_record()
        
        assert error_record.code == "AEON.UNKNOWN.000"
        assert error_record.severity == ErrorSeverity.ERROR
        assert error_record.message == "Test error message"
        assert error_record.affected_component == "unknown"
        assert error_record.stack_trace is not None

    def test_refinement_error_to_error_record(self):
        """Test that RefinementError converts to ErrorRecord."""
        from aeon.exceptions import RefinementError
        
        error = RefinementError("Refinement failed")
        error_record = error.to_error_record()
        
        assert error_record.code == "AEON.REFINEMENT.001"
        assert error_record.severity == ErrorSeverity.ERROR
        assert error_record.message == "Refinement failed"
        assert error_record.affected_component == "refinement"

    def test_execution_error_to_error_record(self):
        """Test that ExecutionError converts to ErrorRecord."""
        from aeon.exceptions import ExecutionError
        
        error = ExecutionError("Execution failed")
        error_record = error.to_error_record(context={"step_id": "step_1"})
        
        assert error_record.code == "AEON.EXECUTION.001"
        assert error_record.severity == ErrorSeverity.ERROR
        assert error_record.message == "Execution failed"
        assert error_record.affected_component == "execution"
        assert error_record.context == {"step_id": "step_1", "affected_component": "execution"}

    def test_validation_error_to_error_record(self):
        """Test that ValidationError converts to ErrorRecord."""
        from aeon.exceptions import ValidationError
        
        error = ValidationError("Validation failed")
        error_record = error.to_error_record()
        
        assert error_record.code == "AEON.VALIDATION.001"
        assert error_record.severity == ErrorSeverity.ERROR
        assert error_record.message == "Validation failed"
        assert error_record.affected_component == "validation"

    def test_error_code_format_validation(self):
        """Test that error codes follow AEON.<COMPONENT>.<CODE> format."""
        from aeon.exceptions import RefinementError, ExecutionError, ValidationError
        
        refinement_error = RefinementError("Test")
        assert refinement_error.ERROR_CODE.startswith("AEON.REFINEMENT.")
        
        execution_error = ExecutionError("Test")
        assert execution_error.ERROR_CODE.startswith("AEON.EXECUTION.")
        
        validation_error = ValidationError("Test")
        assert validation_error.ERROR_CODE.startswith("AEON.VALIDATION.")

    def test_severity_level_validation(self):
        """Test that all exception classes have valid severity levels."""
        from aeon.exceptions import (
            AeonError,
            RefinementError,
            ExecutionError,
            ValidationError,
            PlanError,
            ToolError,
            MemoryError,
            LLMError,
            SupervisorError,
            TTLExpiredError,
        )
        
        # Test that all have valid severity
        assert AeonError.SEVERITY in ErrorSeverity
        assert RefinementError.SEVERITY in ErrorSeverity
        assert ExecutionError.SEVERITY in ErrorSeverity
        assert ValidationError.SEVERITY in ErrorSeverity
        assert PlanError.SEVERITY in ErrorSeverity
        assert ToolError.SEVERITY in ErrorSeverity
        assert MemoryError.SEVERITY in ErrorSeverity
        assert LLMError.SEVERITY in ErrorSeverity
        assert SupervisorError.SEVERITY in ErrorSeverity
        assert TTLExpiredError.SEVERITY == ErrorSeverity.CRITICAL  # TTL should be critical

