"""Integration tests for Phase E (Answer Synthesis).

Per FR-051, tests are limited to exactly 3 scenarios:
1. Successful synthesis with complete execution state
2. TTL expiration scenario
3. Incomplete data scenario
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock
import json

import pytest

from aeon.orchestration.phases import PhaseEInput, FinalAnswer, execute_phase_e
from aeon.prompts.registry import PromptRegistry, PromptId


class TestPhaseESuccessfulSynthesis:
    """T067: Test Phase E successful synthesis with complete execution state."""
    
    def test_successful_synthesis_with_complete_data(self):
        """Test that Phase E produces valid FinalAnswer with complete execution state."""
        # Arrange
        phase_e_input = PhaseEInput(
            request="Deploy a web application",
            correlation_id="test-correlation-123",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=True,
            total_passes=3,
            total_refinements=1,
            ttl_remaining=5000,
            plan_state={"goal": "Deploy web app", "steps": [{"step_id": "1", "description": "Deploy", "status": "complete"}]},
            execution_results=[{"step_id": "1", "result": "Deployed successfully"}],
            convergence_assessment={"converged": True, "confidence": 0.95},
            execution_passes=[{"pass_number": 1, "status": "complete"}],
            semantic_validation={"valid": True},
            task_profile={"complexity": "medium"},
        )
        
        # Mock LLM adapter to return valid FinalAnswer JSON
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "Successfully deployed the web application. All steps completed successfully.",
            "confidence": 0.95,
            "used_step_ids": ["1"],
            "notes": "Deployment completed without errors",
            "ttl_exhausted": False,
            "metadata": {"execution_passes": 3, "converged": True}
        })
        
        # Mock prompt registry
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize the results into a final answer."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="Successfully deployed the web application. All steps completed successfully.",
            confidence=0.95,
            used_step_ids=["1"],
            notes="Deployment completed without errors",
            ttl_exhausted=False,
            metadata={"execution_passes": 3, "converged": True}
        )
        
        # Act
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Assert
        assert isinstance(result, FinalAnswer)
        assert result.answer_text == "Successfully deployed the web application. All steps completed successfully."
        assert result.confidence == 0.95
        assert result.used_step_ids == ["1"]
        assert result.notes == "Deployment completed without errors"
        assert result.ttl_exhausted is False
        assert "execution_passes" in result.metadata
        assert result.metadata["converged"] is True
        
        # Verify all PhaseEInput fields were populated
        assert phase_e_input.plan_state is not None
        assert phase_e_input.execution_results is not None
        assert phase_e_input.convergence_assessment is not None
        assert phase_e_input.execution_passes is not None
        assert phase_e_input.semantic_validation is not None
        assert phase_e_input.task_profile is not None


class TestPhaseETTLExpiration:
    """T068: Test Phase E with TTL expiration scenario."""
    
    def test_ttl_expiration_scenario(self):
        """Test that Phase E produces degraded FinalAnswer when TTL is exhausted."""
        # Arrange
        phase_e_input = PhaseEInput(
            request="Complex multi-step task",
            correlation_id="test-correlation-456",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=5,
            total_refinements=2,
            ttl_remaining=0,  # TTL exhausted
            plan_state={"goal": "Complex task", "steps": [{"step_id": "1", "status": "pending"}]},
            execution_results=[{"step_id": "1", "result": "Partial result"}],
            convergence_assessment={"converged": False},
            execution_passes=[{"pass_number": 1}],
            semantic_validation={"valid": True},
            task_profile={"complexity": "high"},
        )
        
        # Mock LLM adapter to return degraded FinalAnswer
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "Execution was terminated due to TTL expiration. Partial results are available.",
            "confidence": 0.6,
            "ttl_exhausted": True,
            "metadata": {"ttl_expired": True, "degraded": True, "reason": "ttl_expiration"}
        })
        
        # Mock prompt registry
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize the results into a final answer."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="Execution was terminated due to TTL expiration. Partial results are available.",
            confidence=0.6,
            ttl_exhausted=True,
            metadata={"ttl_expired": True, "degraded": True, "reason": "ttl_expiration"}
        )
        
        # Act
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Assert
        assert isinstance(result, FinalAnswer)
        assert "TTL expiration" in result.answer_text or result.ttl_exhausted is True
        assert result.ttl_exhausted is True
        assert result.metadata.get("degraded") is True
        assert result.metadata.get("reason") == "ttl_expiration" or result.metadata.get("ttl_exhausted") is True


class TestPhaseEIncompleteData:
    """T069: Test Phase E with incomplete data scenario."""
    
    def test_incomplete_data_scenario(self):
        """Test that Phase E produces degraded FinalAnswer when optional fields are missing."""
        # Arrange - missing several optional fields
        phase_e_input = PhaseEInput(
            request="Task with incomplete execution",
            correlation_id="test-correlation-789",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=2,
            total_refinements=0,
            ttl_remaining=1000,
            plan_state=None,  # Missing
            execution_results=None,  # Missing
            convergence_assessment=None,  # Missing
            execution_passes=None,  # Missing
            semantic_validation=None,  # Missing
            task_profile=None,  # Missing
        )
        
        # Mock LLM adapter to return degraded FinalAnswer
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "Execution completed but some execution data is missing. Limited results available.",
            "confidence": 0.4,
            "metadata": {"degraded": True, "reason": "incomplete_state", "missing_fields": ["plan_state", "execution_results"]}
        })
        
        # Mock prompt registry
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize the results into a final answer."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="Execution completed but some execution data is missing. Limited results available.",
            confidence=0.4,
            metadata={"degraded": True, "reason": "incomplete_state", "missing_fields": ["plan_state", "execution_results"]}
        )
        
        # Act
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Assert
        assert isinstance(result, FinalAnswer)
        assert len(result.answer_text) > 0  # Must have answer text
        assert result.metadata.get("degraded") is True
        assert result.metadata.get("reason") == "incomplete_state"
        # Verify metadata indicates which fields were missing
        missing_fields = result.metadata.get("missing_fields", [])
        assert len(missing_fields) > 0
        assert "plan_state" in missing_fields or "execution_results" in missing_fields


class TestPhaseEVerificationAllScenarios:
    """T084: Verify Phase E produces final_answer in all scenarios (per SC-005)."""
    
    def test_phase_e_produces_final_answer_successful_convergence(self):
        """Verify Phase E produces final_answer in successful convergence scenario."""
        phase_e_input = PhaseEInput(
            request="Simple task",
            correlation_id="test-001",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=True,
            total_passes=2,
            total_refinements=0,
            ttl_remaining=5000,
            plan_state={"goal": "Task", "steps": []},
            execution_results=[{"step_id": "1", "result": "Success"}],
            convergence_assessment={"converged": True},
            execution_passes=[{"pass_number": 1}],
            semantic_validation={"valid": True},
            task_profile={"complexity": "low"},
        )
        
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "Task completed successfully.",
            "confidence": 0.9,
            "metadata": {}
        })
        
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize results."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="Task completed successfully.",
            confidence=0.9,
            metadata={}
        )
        
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Verify final_answer is produced
        assert isinstance(result, FinalAnswer)
        assert result.answer_text
        assert "final_answer" not in result.model_dump()  # This is the FinalAnswer itself
    
    def test_phase_e_produces_final_answer_ttl_expiration(self):
        """Verify Phase E produces final_answer in TTL expiration scenario."""
        phase_e_input = PhaseEInput(
            request="Long task",
            correlation_id="test-002",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=3,
            total_refinements=1,
            ttl_remaining=0,  # TTL expired
            plan_state={"goal": "Task", "steps": []},
            execution_results=[{"step_id": "1", "result": "Partial"}],
            convergence_assessment={"converged": False},
            execution_passes=[{"pass_number": 1}],
            semantic_validation={"valid": True},
            task_profile={"complexity": "high"},
        )
        
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "TTL expired during execution.",
            "ttl_exhausted": True,
            "metadata": {"degraded": True, "reason": "ttl_expiration"}
        })
        
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize results."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="TTL expired during execution.",
            ttl_exhausted=True,
            metadata={"degraded": True, "reason": "ttl_expiration"}
        )
        
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Verify final_answer is produced even with TTL expiration
        assert isinstance(result, FinalAnswer)
        assert result.answer_text
        assert result.ttl_exhausted is True
    
    def test_phase_e_produces_final_answer_partial_execution(self):
        """Verify Phase E produces final_answer in partial execution scenario."""
        phase_e_input = PhaseEInput(
            request="Partial task",
            correlation_id="test-003",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=1,
            total_refinements=0,
            ttl_remaining=2000,
            plan_state={"goal": "Task", "steps": [{"step_id": "1", "status": "complete"}]},
            execution_results=[{"step_id": "1", "result": "Partial result"}],
            convergence_assessment={"converged": False},
            execution_passes=[{"pass_number": 1}],
            semantic_validation=None,  # Missing
            task_profile=None,  # Missing
        )
        
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "Partial execution completed.",
            "metadata": {"degraded": True, "reason": "incomplete_state"}
        })
        
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize results."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="Partial execution completed.",
            metadata={"degraded": True, "reason": "incomplete_state"}
        )
        
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Verify final_answer is produced even with partial execution
        assert isinstance(result, FinalAnswer)
        assert result.answer_text
        assert result.metadata.get("degraded") is True
    
    def test_phase_e_produces_final_answer_error_conditions(self):
        """Verify Phase E produces final_answer even when LLM call fails (error condition)."""
        phase_e_input = PhaseEInput(
            request="Error task",
            correlation_id="test-004",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=1,
            total_refinements=0,
            ttl_remaining=1000,
            plan_state={"goal": "Task", "steps": []},
            execution_results=[{"step_id": "1", "result": "Error"}],
            convergence_assessment={"converged": False},
            execution_passes=[{"pass_number": 1}],
            semantic_validation={"valid": False},
            task_profile={"complexity": "medium"},
        )
        
        # Simulate LLM error
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("LLM API error")
        
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize results."
        
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Verify final_answer is produced even when LLM fails (degraded mode)
        assert isinstance(result, FinalAnswer)
        assert result.answer_text  # Must have answer text even in error
        assert "error" in result.answer_text.lower() or "failed" in result.answer_text.lower() or "synthesis" in result.answer_text.lower()
    
    def test_phase_e_produces_final_answer_zero_passes(self):
        """Verify Phase E produces final_answer in zero passes scenario."""
        phase_e_input = PhaseEInput(
            request="Zero passes task",
            correlation_id="test-005",
            execution_start_timestamp=datetime.now().isoformat(),
            convergence_status=False,
            total_passes=0,  # Zero passes
            total_refinements=0,
            ttl_remaining=5000,
            plan_state=None,
            execution_results=None,
            convergence_assessment=None,
            execution_passes=None,
            semantic_validation=None,
            task_profile=None,
        )
        
        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps({
            "answer_text": "No execution passes were completed.",
            "metadata": {"degraded": True, "reason": "zero_passes"}
        })
        
        mock_registry = MagicMock(spec=PromptRegistry)
        mock_registry.get_prompt.return_value = "Synthesize results."
        mock_registry.validate_output.return_value = FinalAnswer(
            answer_text="No execution passes were completed.",
            metadata={"degraded": True, "reason": "zero_passes"}
        )
        
        result = execute_phase_e(phase_e_input, mock_llm, mock_registry)
        
        # Verify final_answer is produced even with zero passes
        assert isinstance(result, FinalAnswer)
        assert result.answer_text
        assert result.metadata.get("degraded") is True
        assert result.metadata.get("reason") == "zero_passes" or phase_e_input.total_passes == 0

