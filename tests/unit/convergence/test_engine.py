"""Unit tests for ConvergenceEngine."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from aeon.convergence.engine import ConvergenceEngine
from aeon.convergence.models import ConvergenceAssessment
from aeon.exceptions import LLMError, ValidationError
from aeon.validation.models import SemanticValidationReport, ValidationIssue
from tests.fixtures.mock_llm import MockLLMAdapter


class TestConvergenceEngine:
    """Test ConvergenceEngine initialization and assessment."""

    def test_initialization_with_defaults(self):
        """Test ConvergenceEngine initialization with default thresholds."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        assert engine.llm_adapter == llm
        assert engine.completeness_threshold == 0.95
        assert engine.coherence_threshold == 0.90
        assert engine.consistency_threshold == 0.90
        assert engine.supervisor is not None

    def test_initialization_with_custom_thresholds(self):
        """Test ConvergenceEngine initialization with custom thresholds."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(
            llm_adapter=llm,
            completeness_threshold=0.98,
            coherence_threshold=0.85,
            consistency_threshold=0.88,
        )
        
        assert engine.completeness_threshold == 0.98
        assert engine.coherence_threshold == 0.85
        assert engine.consistency_threshold == 0.88

    def test_assess_with_converged_result(self):
        """Test assess() with converged result."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        # Mock LLM response for converged assessment
        mock_response = {
            "completeness_score": 0.98,
            "coherence_score": 0.95,
            "consistency_status": {
                "plan_aligned": True,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": [],
            "reason_codes": ["completeness_threshold_met", "coherence_threshold_met", "consistency_aligned"],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            assert assessment.converged is True
            assert assessment.completeness_score == 0.98
            assert assessment.coherence_score == 0.95
            assert assessment.consistency_status["plan_aligned"] is True
            assert len(assessment.reason_codes) > 0

    def test_assess_with_not_converged_result(self):
        """Test assess() with not converged result."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        # Mock LLM response for not converged assessment
        mock_response = {
            "completeness_score": 0.80,
            "coherence_score": 0.85,
            "consistency_status": {
                "plan_aligned": False,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": ["Issue 1", "Issue 2"],
            "reason_codes": [],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            assert assessment.converged is False
            assert assessment.completeness_score == 0.80
            assert assessment.coherence_score == 0.85
            assert assessment.consistency_status["plan_aligned"] is False
            assert len(assessment.reason_codes) > 0
            assert "completeness_below_threshold" in str(assessment.reason_codes)
            assert "consistency_not_aligned" in assessment.reason_codes

    def test_assess_with_custom_criteria(self):
        """Test assess() with custom convergence criteria."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        mock_response = {
            "completeness_score": 0.92,
            "coherence_score": 0.88,
            "consistency_status": {
                "plan_aligned": True,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": [],
            "reason_codes": [],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            # Custom criteria with lower thresholds
            custom_criteria = {
                "completeness_threshold": 0.90,
                "coherence_threshold": 0.85,
                "consistency_threshold": 0.90,
            }
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
                custom_criteria=custom_criteria,
            )
            
            # Should converge with custom lower thresholds
            assert assessment.converged is True
            assert assessment.completeness_score == 0.92
            assert assessment.coherence_score == 0.88

    def test_assess_with_llm_error(self):
        """Test assess() handles LLM errors gracefully."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        with patch.object(engine, '_perform_convergence_assessment', side_effect=LLMError("LLM call failed")):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            # Should return conservative assessment (not converged)
            assert assessment.converged is False
            assert assessment.completeness_score == 0.0
            assert assessment.coherence_score == 0.0
            assert "llm_assessment_failed" in assessment.reason_codes
            assert len(assessment.detected_issues) > 0

    def test_assess_with_validation_error(self):
        """Test assess() handles validation errors gracefully."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        with patch.object(engine, '_perform_convergence_assessment', side_effect=ValidationError("Validation failed")):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            # Should return conservative assessment (not converged)
            assert assessment.converged is False
            assert assessment.completeness_score == 0.0
            assert "llm_assessment_failed" in assessment.reason_codes

    def test_assess_with_unexpected_error(self):
        """Test assess() handles unexpected errors gracefully."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        with patch.object(engine, '_perform_convergence_assessment', side_effect=Exception("Unexpected error")):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            # Should return conservative assessment (not converged)
            assert assessment.converged is False
            assert assessment.completeness_score == 0.0
            assert "unexpected_error" in assessment.reason_codes

    def test_assess_with_consistency_conflict(self):
        """Test assess() handles consistency conflicts."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        # High scores but consistency not aligned
        mock_response = {
            "completeness_score": 0.98,
            "coherence_score": 0.95,
            "consistency_status": {
                "plan_aligned": False,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": ["Consistency conflict"],
            "reason_codes": [],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            # Should not converge due to consistency conflict
            assert assessment.converged is False
            assert "consistency_conflict" in assessment.reason_codes
            assert "consistency_not_aligned" in assessment.reason_codes

    def test_assess_with_logging(self):
        """Test assess() logs evaluation outcome when logger and context provided."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        mock_response = {
            "completeness_score": 0.98,
            "coherence_score": 0.95,
            "consistency_status": {
                "plan_aligned": True,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": [],
            "reason_codes": ["completeness_threshold_met", "coherence_threshold_met", "consistency_aligned"],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            validation_report = SemanticValidationReport(
                issues=[],
                overall_severity="INFO",
            )
            
            # Mock logger and execution context
            mock_logger = Mock()
            from aeon.kernel.state import ExecutionContext
            execution_context = ExecutionContext(
                correlation_id="test-correlation-id",
                execution_start_timestamp="2025-01-27T12:00:00Z",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
                execution_context=execution_context,
                logger=mock_logger,
            )
            
            # Verify logger was called
            assert mock_logger.log_evaluation_outcome.called
            call_args = mock_logger.log_evaluation_outcome.call_args
            assert call_args.kwargs["correlation_id"] == "test-correlation-id"
            assert "convergence_assessment" in call_args.kwargs
            assert "validation_report" in call_args.kwargs

    def test_assess_with_validation_issues(self):
        """Test assess() with validation issues in report."""
        llm = MockLLMAdapter()
        engine = ConvergenceEngine(llm_adapter=llm)
        
        mock_response = {
            "completeness_score": 0.98,
            "coherence_score": 0.95,
            "consistency_status": {
                "plan_aligned": True,
                "step_aligned": True,
                "answer_aligned": True,
                "memory_aligned": True,
            },
            "detected_issues": [],
            "reason_codes": [],
        }
        
        with patch.object(engine, '_perform_convergence_assessment', return_value=mock_response):
            plan_state = {"goal": "Test goal", "steps": []}
            execution_results = []
            
            # Create validation report with issues
            validation_issues = [
                ValidationIssue(
                    severity="ERROR",
                    message="Test error",
                    artifact_type="plan",
                ),
                ValidationIssue(
                    severity="WARNING",
                    message="Test warning",
                    artifact_type="step",
                ),
            ]
            validation_report = SemanticValidationReport(
                issues=validation_issues,
                overall_severity="ERROR",
            )
            
            assessment = engine.assess(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=validation_report,
            )
            
            # Metadata should include validation issue counts
            assert assessment.metadata["semantic_validation_issues_count"] == 2
            assert assessment.metadata["semantic_validation_severity"] == "ERROR"

