"""Unit tests for phase transition contract validation (US1).

Tests explicit phase transition contracts, including:
- Valid transitions (A→B, B→C, C→D, D→A/B)
- Invalid transitions (A→C, C→B, etc.)
- Contract validation with valid/invalid inputs
- Retry logic for retryable errors
- LLM provider failure handling
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from aeon.orchestration.phases import (
    get_phase_transition_contract,
    validate_phase_transition_contract,
    enforce_phase_transition_contract,
    CONTRACT_A_TO_B,
    CONTRACT_B_TO_C,
    CONTRACT_C_TO_D,
    CONTRACT_D_TO_A_B,
    execute_with_retry,
    call_llm_with_provider_error_handling,
)
from aeon.exceptions import PhaseTransitionError
from aeon.plan.models import Plan, PlanStep
from aeon.adaptive.models import TaskProfile
from aeon.llm.interface import LLMAdapter
from aeon.exceptions import LLMError


class TestPhaseTransitionContracts:
    """Test phase transition contract constants and retrieval."""

    def test_get_contract_a_to_b(self):
        """Test retrieving A→B contract."""
        contract = get_phase_transition_contract("A→B")
        assert contract.transition_name == "A→B"
        assert contract == CONTRACT_A_TO_B

    def test_get_contract_b_to_c(self):
        """Test retrieving B→C contract."""
        contract = get_phase_transition_contract("B→C")
        assert contract.transition_name == "B→C"
        assert contract == CONTRACT_B_TO_C

    def test_get_contract_c_to_d(self):
        """Test retrieving C→D contract."""
        contract = get_phase_transition_contract("C→D")
        assert contract.transition_name == "C→D"
        assert contract == CONTRACT_C_TO_D

    def test_get_contract_d_to_a_b(self):
        """Test retrieving D→A/B contract."""
        contract = get_phase_transition_contract("D→A/B")
        assert contract.transition_name == "D→A/B"
        assert contract == CONTRACT_D_TO_A_B

    def test_get_contract_invalid_transition(self):
        """Test that invalid transition names raise ValueError."""
        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("A→C")  # Invalid: A should go to B, not C

        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("C→B")  # Invalid: C should go to D, not B


class TestContractAtoB:
    """Test A→B phase transition contract validation."""

    def test_validate_a_to_b_valid_inputs(self):
        """Test A→B contract with valid inputs."""
        task_profile = TaskProfile.default()
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        
        inputs = {
            "task_profile": task_profile,
            "initial_plan": plan,
            "ttl": 10,
        }
        
        is_valid, error_message = validate_phase_transition_contract("A→B", inputs)
        assert is_valid is True
        assert error_message is None

    def test_validate_a_to_b_missing_task_profile(self):
        """Test A→B contract with missing task_profile."""
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        
        inputs = {
            "initial_plan": plan,
            "ttl": 10,
        }
        
        is_valid, error_message = validate_phase_transition_contract("A→B", inputs)
        assert is_valid is False
        assert "task_profile" in error_message.lower()

    def test_validate_a_to_b_invalid_ttl(self):
        """Test A→B contract with invalid TTL (zero or negative)."""
        task_profile = TaskProfile.default()
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        
        # Test with TTL = 0 (invalid, must be > 0)
        inputs = {
            "task_profile": task_profile,
            "initial_plan": plan,
            "ttl": 0,
        }
        
        is_valid, error_message = validate_phase_transition_contract("A→B", inputs)
        assert is_valid is False
        assert "ttl" in error_message.lower() or "validation" in error_message.lower()

    def test_enforce_a_to_b_valid_inputs_outputs(self):
        """Test A→B contract enforcement with valid inputs and outputs."""
        task_profile = TaskProfile.default()
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        refined_plan = Plan(goal="Refined goal", steps=[PlanStep(step_id="1", description="Refined Step 1")])
        
        inputs = {
            "task_profile": task_profile,
            "initial_plan": plan,
            "ttl": 10,
        }
        outputs = {
            "refined_plan": refined_plan,
        }
        
        success, error_message, phase_error = enforce_phase_transition_contract("A→B", inputs, outputs)
        assert success is True
        assert error_message is None
        assert phase_error is None

    def test_enforce_a_to_b_missing_output(self):
        """Test A→B contract enforcement with missing output."""
        task_profile = TaskProfile.default()
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        
        inputs = {
            "task_profile": task_profile,
            "initial_plan": plan,
            "ttl": 10,
        }
        outputs = {}  # Missing refined_plan
        
        success, error_message, phase_error = enforce_phase_transition_contract("A→B", inputs, outputs)
        assert success is False
        assert "refined_plan" in error_message.lower() or "output" in error_message.lower()


class TestContractBtoC:
    """Test B→C phase transition contract validation."""

    def test_validate_b_to_c_valid_inputs(self):
        """Test B→C contract with valid inputs."""
        plan = Plan(
            goal="Test goal",
            steps=[
                PlanStep(step_id="1", description="Step 1"),
                PlanStep(step_id="2", description="Step 2"),
            ]
        )
        
        inputs = {
            "refined_plan": plan,
            "refined_plan_steps": plan.steps,
        }
        
        is_valid, error_message = validate_phase_transition_contract("B→C", inputs)
        assert is_valid is True
        assert error_message is None

    def test_validate_b_to_c_empty_steps(self):
        """Test B→C contract with empty steps (invalid)."""
        # Cannot create Plan with empty steps due to Pydantic validation
        # Instead, test with a Plan that has steps, but pass empty list for refined_plan_steps
        from aeon.plan.models import PlanStep, StepStatus
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Test step", status=StepStatus.PENDING)]
        )
        
        inputs = {
            "refined_plan": plan,
            "refined_plan_steps": [],  # Empty steps list - this should fail validation
        }
        
        is_valid, error_message = validate_phase_transition_contract("B→C", inputs)
        assert is_valid is False
        assert "steps" in error_message.lower() or "validation" in error_message.lower()

    def test_enforce_b_to_c_valid_execution_results(self):
        """Test B→C contract enforcement with valid execution results."""
        plan = Plan(goal="Test goal", steps=[PlanStep(step_id="1", description="Step 1")])
        
        inputs = {
            "refined_plan": plan,
            "refined_plan_steps": plan.steps,
        }
        outputs = {
            "execution_results": [
                {"step_id": "1", "status": "complete", "output": "Result"}
            ],
        }
        
        success, error_message, phase_error = enforce_phase_transition_contract("B→C", inputs, outputs)
        assert success is True
        assert error_message is None
        assert phase_error is None


class TestContractCtoD:
    """Test C→D phase transition contract validation."""

    def test_validate_c_to_d_valid_inputs(self):
        """Test C→D contract with valid inputs."""
        inputs = {
            "execution_results": [
                {"step_id": "1", "status": "complete"}
            ],
            "evaluation_results": {
                "converged": False,
                "needs_refinement": True,
            },
        }
        
        is_valid, error_message = validate_phase_transition_contract("C→D", inputs)
        assert is_valid is True
        assert error_message is None

    def test_validate_c_to_d_missing_execution_results(self):
        """Test C→D contract with missing execution results."""
        inputs = {
            "evaluation_results": {
                "converged": False,
            },
        }
        
        is_valid, error_message = validate_phase_transition_contract("C→D", inputs)
        assert is_valid is False
        assert "execution_results" in error_message.lower()


class TestContractDtoAB:
    """Test D→A/B phase transition contract validation."""

    def test_validate_d_to_a_b_valid_inputs(self):
        """Test D→A/B contract with valid inputs."""
        task_profile = TaskProfile.default()
        
        inputs = {
            "task_profile": task_profile,
            "ttl_remaining": 5,
        }
        
        is_valid, error_message = validate_phase_transition_contract("D→A/B", inputs)
        assert is_valid is True
        assert error_message is None

    def test_validate_d_to_a_b_invalid_ttl(self):
        """Test D→A/B contract with negative TTL (invalid)."""
        task_profile = TaskProfile.default()
        
        inputs = {
            "task_profile": task_profile,
            "ttl_remaining": -1,  # Invalid: TTL must be >= 0
        }
        
        is_valid, error_message = validate_phase_transition_contract("D→A/B", inputs)
        assert is_valid is False
        assert "ttl" in error_message.lower() or "validation" in error_message.lower()


class TestInvalidTransitions:
    """Test that invalid phase transitions are prevented."""

    def test_cannot_get_contract_for_invalid_transition(self):
        """Test that invalid transitions like A→C cannot retrieve contracts."""
        # A→C is invalid: A should transition to B, not C
        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("A→C")

        # C→B is invalid: C should transition to D, not B
        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("C→B")

        # B→A is invalid: B should transition to C, not A
        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("B→A")

        # D→C is invalid: D should transition to A/B, not C
        with pytest.raises(ValueError, match="Invalid transition name"):
            get_phase_transition_contract("D→C")

    def test_invalid_transitions_cannot_be_validated(self):
        """Test that invalid transitions cannot be validated."""
        # Attempting to validate an invalid transition should fail at contract retrieval
        inputs = {"test": "data"}
        
        with pytest.raises(ValueError, match="Invalid transition name"):
            validate_phase_transition_contract("A→C", inputs)

        with pytest.raises(ValueError, match="Invalid transition name"):
            validate_phase_transition_contract("C→B", inputs)

    def test_only_valid_transitions_are_enforced(self):
        """Test that only valid transitions can be enforced."""
        inputs = {}
        outputs = {}
        
        with pytest.raises(ValueError, match="Invalid transition name"):
            enforce_phase_transition_contract("A→C", inputs, outputs)

        with pytest.raises(ValueError, match="Invalid transition name"):
            enforce_phase_transition_contract("C→B", inputs, outputs)


class TestRetryLogic:
    """Test retry logic for retryable phase transition errors."""

    def test_execute_with_retry_success(self):
        """Test execute_with_retry with successful execution."""
        def success_func():
            return "success"
        
        success, result, error_message, phase_error = execute_with_retry(
            success_func,
            "A→B",
            max_retries=1,
        )
        
        assert success is True
        assert result == "success"
        assert error_message is None
        assert phase_error is None

    def test_execute_with_retry_retryable_error_succeeds_on_retry(self):
        """Test execute_with_retry with retryable error that succeeds on retry."""
        attempt_count = [0]
        
        def func_with_retryable_error():
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                error = PhaseTransitionError(
                    transition_name="A→B",
                    failure_condition="malformed plan JSON",
                    retryable=True,
                )
                raise error
            return "success after retry"
        
        success, result, error_message, phase_error = execute_with_retry(
            func_with_retryable_error,
            "A→B",
            max_retries=1,
        )
        
        assert success is True
        assert result == "success after retry"
        assert attempt_count[0] == 2  # Should have retried once

    def test_execute_with_retry_non_retryable_error(self):
        """Test execute_with_retry with non-retryable error (no retry)."""
        def func_with_non_retryable_error():
            error = PhaseTransitionError(
                transition_name="A→B",
                failure_condition="incomplete profile",
                retryable=False,  # Non-retryable
            )
            raise error
        
        success, result, error_message, phase_error = execute_with_retry(
            func_with_non_retryable_error,
            "A→B",
            max_retries=1,
        )
        
        assert success is False
        assert phase_error is not None
        assert phase_error.retryable is False

    def test_execute_with_retry_exhausts_retries(self):
        """Test execute_with_retry when all retries are exhausted."""
        attempt_count = [0]
        
        def func_always_fails():
            attempt_count[0] += 1
            error = PhaseTransitionError(
                transition_name="A→B",
                failure_condition="malformed plan JSON",
                retryable=True,
            )
            raise error
        
        success, result, error_message, phase_error = execute_with_retry(
            func_always_fails,
            "A→B",
            max_retries=1,
        )
        
        assert success is False
        assert attempt_count[0] == 2  # Initial attempt + 1 retry
        assert phase_error is not None


class TestLLMProviderErrorHandling:
    """Test LLM provider failure handling per FR-011."""

    def test_llm_call_success(self):
        """Test successful LLM call."""
        mock_llm = Mock(spec=LLMAdapter)
        mock_llm.generate.return_value = {"text": "Success response"}
        
        response = call_llm_with_provider_error_handling(
            llm_adapter=mock_llm,
            prompt="Test prompt",
            phase="B",
        )
        
        assert response == {"text": "Success response"}
        mock_llm.generate.assert_called_once()

    def test_llm_call_retryable_error_succeeds_on_retry(self):
        """Test LLM call with retryable error that succeeds on retry."""
        attempt_count = [0]
        mock_llm = Mock(spec=LLMAdapter)
        
        def mock_generate(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] == 1:
                raise LLMError("Network timeout - temporary error")
            return {"text": "Success after retry"}
        
        mock_llm.generate.side_effect = mock_generate
        
        response = call_llm_with_provider_error_handling(
            llm_adapter=mock_llm,
            prompt="Test prompt",
            phase="B",
        )
        
        assert response == {"text": "Success after retry"}
        assert attempt_count[0] == 2  # Initial attempt + 1 retry

    def test_llm_call_non_retryable_error(self):
        """Test LLM call with non-retryable error (no retry)."""
        mock_llm = Mock(spec=LLMAdapter)
        mock_llm.generate.side_effect = LLMError("Invalid API key - authentication failed")
        
        with pytest.raises(PhaseTransitionError) as exc_info:
            call_llm_with_provider_error_handling(
                llm_adapter=mock_llm,
                prompt="Test prompt",
                phase="B",
            )
        
        assert exc_info.value.retryable is False
        mock_llm.generate.assert_called_once()  # No retry for non-retryable errors

    def test_llm_call_exhausts_retries(self):
        """Test LLM call when all retries are exhausted."""
        attempt_count = [0]
        mock_llm = Mock(spec=LLMAdapter)
        
        def mock_generate(*args, **kwargs):
            attempt_count[0] += 1
            raise LLMError("Network timeout - temporary error")
        
        mock_llm.generate.side_effect = mock_generate
        
        with pytest.raises(PhaseTransitionError) as exc_info:
            call_llm_with_provider_error_handling(
                llm_adapter=mock_llm,
                prompt="Test prompt",
                phase="B",
            )
        
        assert attempt_count[0] == 2  # Initial attempt + 1 retry
        assert exc_info.value.retryable is False  # After retry exhaustion, treated as non-retryable


class TestFailureConditions:
    """Test failure condition enumeration and classification."""

    def test_a_to_b_failure_conditions(self):
        """Test A→B contract failure conditions are properly classified."""
        contract = CONTRACT_A_TO_B
        
        # Find incomplete profile condition (should be non-retryable)
        incomplete_profile = next(
            (fc for fc in contract.failure_conditions if "incomplete" in fc.condition.lower()),
            None
        )
        assert incomplete_profile is not None
        assert incomplete_profile.retryable is False
        assert incomplete_profile.error_code == "AEON.PHASE_TRANSITION.A_B.001"
        
        # Find malformed plan JSON condition (should be retryable)
        malformed_json = next(
            (fc for fc in contract.failure_conditions if "malformed plan json" in fc.condition.lower()),
            None
        )
        assert malformed_json is not None
        assert malformed_json.retryable is True
        assert malformed_json.error_code == "AEON.PHASE_TRANSITION.A_B.002"

    def test_b_to_c_failure_conditions(self):
        """Test B→C contract failure conditions are properly classified."""
        contract = CONTRACT_B_TO_C
        
        # Find missing steps condition (should be non-retryable)
        missing_steps = next(
            (fc for fc in contract.failure_conditions if "missing steps" in fc.condition.lower()),
            None
        )
        assert missing_steps is not None
        assert missing_steps.retryable is False

    def test_failure_conditions_have_error_codes(self):
        """Test that all failure conditions have error codes."""
        contracts = [CONTRACT_A_TO_B, CONTRACT_B_TO_C, CONTRACT_C_TO_D, CONTRACT_D_TO_A_B]
        
        for contract in contracts:
            for failure_condition in contract.failure_conditions:
                assert failure_condition.error_code is not None
                assert failure_condition.error_code.startswith("AEON.PHASE_TRANSITION.")
                assert len(failure_condition.error_code.split(".")) >= 4  # Format: AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>

