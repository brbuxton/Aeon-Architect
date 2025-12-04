"""Unit tests for PlanRefinement."""

import pytest

from aeon.orchestration.refinement import PlanRefinement
from aeon.plan.models import Plan, PlanStep, RefinementAction


class TestPlanRefinement:
    """Test PlanRefinement.apply_actions()."""

    def test_apply_actions_add(self):
        """Test applying ADD action."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        actions = [
            RefinementAction(
                action_type="ADD",
                new_step={"step_id": "step2", "description": "Step 2"},
                target_plan_section="steps",
                changes={"added_step": "step2"},
                reason="Add new step"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert len(updated_plan.steps) == 2
        assert updated_plan.steps[1].step_id == "step2"
        assert error is None

    def test_apply_actions_modify(self):
        """Test applying MODIFY action."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        actions = [
            RefinementAction(
                action_type="MODIFY",
                target_step_id="step1",
                new_step={"description": "Modified Step 1"},
                changes={"description": "Modified Step 1"},
                reason="Modify step description"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert updated_plan.steps[0].description == "Modified Step 1"
        assert error is None

    def test_apply_actions_remove(self):
        """Test applying REMOVE action."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[
                PlanStep(step_id="step1", description="Step 1"),
                PlanStep(step_id="step2", description="Step 2")
            ]
        )
        
        actions = [
            RefinementAction(
                action_type="REMOVE",
                target_step_id="step1",
                changes={"removed_step": "step1"},
                reason="Remove step"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert len(updated_plan.steps) == 1
        assert updated_plan.steps[0].step_id == "step2"
        assert error is None

    def test_apply_actions_replace(self):
        """Test applying REPLACE action."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        actions = [
            RefinementAction(
                action_type="REPLACE",
                target_step_id="step1",
                new_step={"step_id": "step1", "description": "Replaced Step 1"},
                changes={"replaced_step": "step1"},
                reason="Replace step"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert updated_plan.steps[0].description == "Replaced Step 1"
        assert error is None

    def test_apply_actions_multiple(self):
        """Test applying multiple actions."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        actions = [
            RefinementAction(
                action_type="ADD",
                new_step={"step_id": "step2", "description": "Step 2"},
                target_plan_section="steps",
                changes={"added_step": "step2"},
                reason="Add new step"
            ),
            RefinementAction(
                action_type="MODIFY",
                target_step_id="step1",
                new_step={"description": "Modified Step 1"},
                changes={"description": "Modified Step 1"},
                reason="Modify step description"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert len(updated_plan.steps) == 2
        assert updated_plan.steps[0].description == "Modified Step 1"
        assert updated_plan.steps[1].step_id == "step2"
        assert error is None

    def test_apply_actions_empty_list(self):
        """Test applying empty action list."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        success, updated_plan, error = refinement.apply_actions(plan, [])
        
        assert success is True
        assert updated_plan == plan
        assert error is None

    def test_apply_actions_invalid_action_type(self):
        """Test applying invalid action type (should be skipped)."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        # Create action with invalid type (not a RefinementAction instance)
        actions = [{"action_type": "INVALID", "target_step_id": "step1"}]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert updated_plan == plan  # No changes applied
        assert error is None

    def test_apply_actions_modify_nonexistent_step(self):
        """Test applying MODIFY action to nonexistent step."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        actions = [
            RefinementAction(
                action_type="MODIFY",
                target_step_id="nonexistent",
                new_step={"description": "Modified"},
                changes={"description": "Modified"},
                reason="Modify nonexistent step"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        assert success is True
        assert updated_plan == plan  # No changes applied
        assert error is None

    def test_apply_actions_failure(self):
        """Test apply_actions with failure during step creation."""
        refinement = PlanRefinement()
        
        plan = Plan(
            goal="Test goal",
            steps=[PlanStep(step_id="step1", description="Step 1")]
        )
        
        # Create action with invalid step data that will cause PlanStep creation to fail
        # We'll use a dict that can't be converted to PlanStep
        actions = [
            RefinementAction(
                action_type="ADD",
                new_step={"step_id": "", "description": ""},  # Empty strings will fail validation
                target_plan_section="steps",
                changes={"added_step": "step2"},
                reason="Add step"
            )
        ]
        
        success, updated_plan, error = refinement.apply_actions(plan, actions)
        
        # PlanStep validation will fail, so apply_actions should return error
        assert success is False
        assert updated_plan == plan  # Returns original plan
        assert error is not None

