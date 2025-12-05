"""Integration tests for logging performance validation (T113-T116)."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from aeon.observability.helpers import generate_correlation_id
from aeon.observability.logger import JSONLLogger
from aeon.observability.models import ErrorRecord, ErrorSeverity, PlanFragment, PlanStateSlice
from aeon.plan.models import PlanStep
from datetime import datetime


class TestLoggingPerformance:
    """Test logging performance and latency requirements."""

    def _create_logger(self) -> tuple[JSONLLogger, Path]:
        """Create logger with temp file and return logger and file path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            file_path = Path(f.name)
        
        logger = JSONLLogger(file_path=file_path)
        return logger, file_path

    def test_logging_latency_phase_entry(self):
        """Test that phase entry logging latency is <10ms (T114)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Measure latency
            start = time.perf_counter()
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            latency_ms = (time.perf_counter() - start) * 1000
            
            # SC-005: Logging latency <10ms
            assert latency_ms < 10.0, f"Phase entry logging latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_latency_phase_exit(self):
        """Test that phase exit logging latency is <10ms (T114)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Measure latency
            start = time.perf_counter()
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            latency_ms = (time.perf_counter() - start) * 1000
            
            # SC-005: Logging latency <10ms
            assert latency_ms < 10.0, f"Phase exit logging latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_latency_state_transition(self):
        """Test that state transition logging latency is <10ms (T114)."""
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
            
            # Measure latency
            start = time.perf_counter()
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="step_completed"
            )
            latency_ms = (time.perf_counter() - start) * 1000
            
            # SC-005: Logging latency <10ms
            assert latency_ms < 10.0, f"State transition logging latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_latency_error_logging(self):
        """Test that error logging latency is <10ms (T114)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution",
                context={"step_id": "step_1"}
            )
            
            # Measure latency
            start = time.perf_counter()
            logger.log_error(correlation_id=correlation_id, error=error_record)
            latency_ms = (time.perf_counter() - start) * 1000
            
            # SC-005: Logging latency <10ms
            assert latency_ms < 10.0, f"Error logging latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_latency_refinement_outcome(self):
        """Test that refinement outcome logging latency is <10ms (T114)."""
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
            
            # Measure latency
            start = time.perf_counter()
            logger.log_refinement_outcome(
                correlation_id=correlation_id,
                before_plan_fragment=before_fragment,
                after_plan_fragment=after_fragment,
                refinement_actions=[{"type": "modify_step", "step_id": "step_1"}]
            )
            latency_ms = (time.perf_counter() - start) * 1000
            
            # SC-005: Logging latency <10ms
            assert latency_ms < 10.0, f"Refinement outcome logging latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_operations_profile(self):
        """Profile logging operations and measure latency (T113)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Profile multiple operations
            latencies = {}
            
            # Phase entry
            start = time.perf_counter()
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            latencies["phase_entry"] = (time.perf_counter() - start) * 1000
            
            # Phase exit
            start = time.perf_counter()
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            latencies["phase_exit"] = (time.perf_counter() - start) * 1000
            
            # State transition
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
            start = time.perf_counter()
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="step_completed"
            )
            latencies["state_transition"] = (time.perf_counter() - start) * 1000
            
            # Error logging
            error_record = ErrorRecord(
                code="AEON.EXECUTION.001",
                severity=ErrorSeverity.ERROR,
                message="Test error",
                affected_component="execution"
            )
            start = time.perf_counter()
            logger.log_error(correlation_id=correlation_id, error=error_record)
            latencies["error"] = (time.perf_counter() - start) * 1000
            
            # Verify all latencies are <10ms
            for operation, latency_ms in latencies.items():
                assert latency_ms < 10.0, f"{operation} latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

    def test_logging_non_blocking_on_errors(self):
        """Test that logging is non-blocking and fails silently on errors (T116)."""
        # Use invalid file path to trigger write error
        invalid_path = Path("/invalid/path/that/does/not/exist/file.jsonl")
        logger = JSONLLogger(file_path=invalid_path)
        correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
        
        # Should not raise exception
        try:
            logger.log_phase_entry(phase="A", correlation_id=correlation_id)
            logger.log_phase_exit(phase="A", correlation_id=correlation_id, duration=1.0, outcome="success")
            logger.log_error(
                correlation_id=correlation_id,
                error=ErrorRecord(
                    code="AEON.EXECUTION.001",
                    severity=ErrorSeverity.ERROR,
                    message="Test error",
                    affected_component="execution"
                )
            )
        except Exception as e:
            pytest.fail(f"Logging should not raise exceptions, got: {e}")
        
        # Execution continues
        assert True  # No exception raised

    def test_json_serialization_performance(self):
        """Test JSON serialization performance (T115)."""
        logger, log_file = self._create_logger()
        
        try:
            correlation_id = generate_correlation_id(datetime.now().isoformat(), "test")
            
            # Create complex state with many fields
            before_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_1",
                step_count=100,
                steps_status_summary={"pending": 50, "running": 25, "complete": 25}
            )
            after_state = PlanStateSlice(
                component="plan",
                timestamp=datetime.now().isoformat(),
                plan_id="plan_123",
                current_step_id="step_2",
                step_count=100,
                steps_status_summary={"pending": 49, "running": 25, "complete": 26}
            )
            
            # Measure serialization latency
            start = time.perf_counter()
            logger.log_state_transition(
                correlation_id=correlation_id,
                component="plan",
                before_state=before_state.model_dump(),
                after_state=after_state.model_dump(),
                transition_reason="step_completed"
            )
            latency_ms = (time.perf_counter() - start) * 1000
            
            # Should still be <10ms even with complex state
            assert latency_ms < 10.0, f"JSON serialization latency {latency_ms:.2f}ms exceeds 10ms threshold"
        finally:
            log_file.unlink(missing_ok=True)

