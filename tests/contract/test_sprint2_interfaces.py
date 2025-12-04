"""Contract tests for Sprint 2 interfaces (ConvergenceEngine, SemanticValidator, AdaptiveDepth, RecursivePlanner)."""

import pytest

from aeon.adaptive.heuristics import AdaptiveDepth
from aeon.adaptive.models import TaskProfile
from aeon.convergence.engine import ConvergenceEngine
from aeon.convergence.models import ConvergenceAssessment
from aeon.exceptions import LLMError, ValidationError
from aeon.plan.recursive import RecursivePlanner
from aeon.tools.registry import ToolRegistry
from aeon.validation.models import SemanticValidationReport
from aeon.validation.semantic import SemanticValidator
from tests.fixtures.mock_llm import MockLLMAdapter


class TestConvergenceEngineInterface:
    """Contract tests for ConvergenceEngine interface."""

    @pytest.fixture
    def convergence_engine(self):
        """Create ConvergenceEngine instance for testing."""
        return ConvergenceEngine(llm_adapter=MockLLMAdapter())

    def test_convergence_engine_has_assess_method(self, convergence_engine):
        """Test that ConvergenceEngine has assess() method."""
        assert hasattr(convergence_engine, "assess")
        assert callable(convergence_engine.assess)

    def test_assess_returns_convergence_assessment(self, convergence_engine):
        """Test that assess() returns ConvergenceAssessment."""
        from aeon.validation.models import SemanticValidationReport
        
        plan_state = {"goal": "test", "steps": []}
        execution_results = []
        validation_report = SemanticValidationReport(
            validation_id="test",
            artifact_type="plan",
            issues=[],
        )
        
        result = convergence_engine.assess(
            plan_state=plan_state,
            execution_results=execution_results,
            semantic_validation_report=validation_report,
        )
        
        assert isinstance(result, ConvergenceAssessment)
        assert "converged" in result.model_dump()
        assert "reason_codes" in result.model_dump()

    def test_assess_handles_custom_criteria(self, convergence_engine):
        """Test that assess() accepts custom criteria."""
        from aeon.validation.models import SemanticValidationReport
        
        plan_state = {"goal": "test", "steps": []}
        execution_results = []
        validation_report = SemanticValidationReport(
            validation_id="test",
            artifact_type="plan",
            issues=[],
        )
        custom_criteria = {
            "completeness_threshold": 0.98,
            "coherence_threshold": 0.95,
        }
        
        result = convergence_engine.assess(
            plan_state=plan_state,
            execution_results=execution_results,
            semantic_validation_report=validation_report,
            custom_criteria=custom_criteria,
        )
        
        assert isinstance(result, ConvergenceAssessment)


class TestSemanticValidatorInterface:
    """Contract tests for SemanticValidator interface."""

    @pytest.fixture
    def semantic_validator(self):
        """Create SemanticValidator instance for testing."""
        return SemanticValidator(
            llm_adapter=MockLLMAdapter(),
            tool_registry=ToolRegistry(),
        )

    def test_semantic_validator_has_validate_method(self, semantic_validator):
        """Test that SemanticValidator has validate() method."""
        assert hasattr(semantic_validator, "validate")
        assert callable(semantic_validator.validate)

    def test_validate_returns_semantic_validation_report(self, semantic_validator):
        """Test that validate() returns SemanticValidationReport."""
        artifact = {"goal": "test", "steps": []}
        
        result = semantic_validator.validate(
            artifact=artifact,
            artifact_type="plan",
        )
        
        assert isinstance(result, SemanticValidationReport)
        assert "validation_id" in result.model_dump()
        assert "artifact_type" in result.model_dump()
        assert "issues" in result.model_dump()

    def test_validate_accepts_different_artifact_types(self, semantic_validator):
        """Test that validate() accepts different artifact types."""
        artifact = {"description": "test step"}
        
        for artifact_type in ["plan", "step", "execution_artifact", "cross_phase"]:
            result = semantic_validator.validate(
                artifact=artifact,
                artifact_type=artifact_type,
            )
            assert isinstance(result, SemanticValidationReport)
            assert result.artifact_type == artifact_type


class TestAdaptiveDepthInterface:
    """Contract tests for AdaptiveDepth interface."""

    @pytest.fixture
    def adaptive_depth(self):
        """Create AdaptiveDepth instance for testing."""
        return AdaptiveDepth(
            llm_adapter=MockLLMAdapter(),
            global_ttl_limit=10,
        )

    def test_adaptive_depth_has_infer_task_profile_method(self, adaptive_depth):
        """Test that AdaptiveDepth has infer_task_profile() method."""
        assert hasattr(adaptive_depth, "infer_task_profile")
        assert callable(adaptive_depth.infer_task_profile)

    def test_adaptive_depth_has_allocate_ttl_method(self, adaptive_depth):
        """Test that AdaptiveDepth has allocate_ttl() method."""
        assert hasattr(adaptive_depth, "allocate_ttl")
        assert callable(adaptive_depth.allocate_ttl)

    def test_infer_task_profile_returns_task_profile(self, adaptive_depth):
        """Test that infer_task_profile() returns TaskProfile."""
        result = adaptive_depth.infer_task_profile(
            task_description="test task",
        )
        
        assert isinstance(result, TaskProfile)
        assert hasattr(result, "reasoning_depth")
        assert hasattr(result, "information_sufficiency")

    def test_allocate_ttl_returns_integer(self, adaptive_depth):
        """Test that allocate_ttl() returns integer TTL."""
        task_profile = TaskProfile.default()
        
        result = adaptive_depth.allocate_ttl(
            task_profile=task_profile,
            global_ttl_limit=10,
        )
        
        assert isinstance(result, int)
        assert result >= 0
        assert result <= 10  # Should respect global limit

    def test_allocate_ttl_respects_global_limit(self, adaptive_depth):
        """Test that allocate_ttl() respects global TTL limit."""
        task_profile = TaskProfile.default()
        
        result = adaptive_depth.allocate_ttl(
            task_profile=task_profile,
            global_ttl_limit=5,
        )
        
        assert result <= 5


class TestRecursivePlannerInterface:
    """Contract tests for RecursivePlanner interface."""

    @pytest.fixture
    def recursive_planner(self):
        """Create RecursivePlanner instance for testing."""
        from aeon.validation.semantic import SemanticValidator
        
        return RecursivePlanner(
            llm_adapter=MockLLMAdapter(),
            tool_registry=ToolRegistry(),
            semantic_validator=SemanticValidator(
                llm_adapter=MockLLMAdapter(),
                tool_registry=ToolRegistry(),
            ),
        )

    def test_recursive_planner_has_generate_plan_method(self, recursive_planner):
        """Test that RecursivePlanner has generate_plan() method."""
        assert hasattr(recursive_planner, "generate_plan")
        assert callable(recursive_planner.generate_plan)

    def test_recursive_planner_has_refine_plan_method(self, recursive_planner):
        """Test that RecursivePlanner has refine_plan() method."""
        assert hasattr(recursive_planner, "refine_plan")
        assert callable(recursive_planner.refine_plan)

    def test_generate_plan_returns_plan(self, recursive_planner):
        """Test that generate_plan() returns Plan."""
        from aeon.plan.models import Plan
        from aeon.adaptive.models import TaskProfile
        
        task_profile = TaskProfile.default()
        tool_registry = ToolRegistry()
        
        result = recursive_planner.generate_plan(
            task_description="test request",
            task_profile=task_profile,
            tool_registry=tool_registry,
        )
        
        assert isinstance(result, Plan)
        assert hasattr(result, "goal")
        assert hasattr(result, "steps")

    def test_refine_plan_returns_refinement_actions(self, recursive_planner):
        """Test that refine_plan() returns list of RefinementAction."""
        from aeon.plan.models import Plan, PlanStep
        
        plan = Plan(
            goal="test",
            steps=[
                PlanStep(
                    step_id="step1",
                    description="test step",
                    status="pending",
                )
            ],
        )
        
        result = recursive_planner.refine_plan(
            current_plan=plan,
            validation_issues=[],
            convergence_reason_codes=[],
            blocked_steps=[],
            executed_step_ids=set(),
        )
        
        assert isinstance(result, list)
        # Result may be empty if no refinements needed

