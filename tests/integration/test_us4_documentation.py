"""Integration tests for User Story 4 - Document Refactoring Architecture (T067-T070).

These tests verify that all documentation exists and is complete:
- Specification document lists all extracted logic
- Interface contracts are documented
- Data models are documented
- LOC measurements are documented
"""

import re
from pathlib import Path

import pytest


class TestSpecificationDocumentation:
    """Test T067: Verify specification document lists all extracted logic."""

    @pytest.fixture
    def spec_path(self):
        """Get path to spec.md."""
        return Path(__file__).parent.parent.parent / "specs" / "004-kernel-refactor" / "spec.md"

    def test_spec_document_exists(self, spec_path):
        """Verify spec.md exists."""
        assert spec_path.exists(), f"spec.md not found at {spec_path}"

    def test_spec_lists_extracted_phase_logic(self, spec_path):
        """Verify spec.md lists extracted phase orchestration logic."""
        content = spec_path.read_text()

        # Check for phase orchestration extraction (FR-002)
        assert "phase orchestration" in content.lower() or "Phase A" in content or "Phase B" in content, (
            "spec.md must document phase orchestration logic extraction"
        )

    def test_spec_lists_extracted_refinement_logic(self, spec_path):
        """Verify spec.md lists extracted plan refinement logic."""
        content = spec_path.read_text()

        # Check for plan refinement extraction (FR-003)
        assert "refinement" in content.lower() or "plan transformation" in content.lower(), (
            "spec.md must document plan refinement logic extraction"
        )

    def test_spec_lists_extracted_heuristic_logic(self, spec_path):
        """Verify spec.md lists extracted heuristic decision logic."""
        content = spec_path.read_text()

        # Check for heuristic extraction (FR-004)
        assert "heuristic" in content.lower() or "step preparation" in content.lower(), (
            "spec.md must document heuristic decision logic extraction"
        )

    def test_spec_lists_extracted_ttl_logic(self, spec_path):
        """Verify spec.md lists extracted TTL/expiration logic."""
        content = spec_path.read_text()

        # Check for TTL extraction (FR-005)
        assert "ttl" in content.lower() or "expiration" in content.lower(), (
            "spec.md must document TTL/expiration logic extraction"
        )

    def test_spec_documents_module_boundaries(self, spec_path):
        """Verify spec.md documents new module boundaries."""
        content = spec_path.read_text()

        # Check for orchestration module namespace
        assert "orchestration" in content.lower() or "aeon/orchestration" in content, (
            "spec.md must document new orchestration module boundaries"
        )


class TestInterfaceContractsDocumentation:
    """Test T068: Verify interface contracts are documented."""

    @pytest.fixture
    def contracts_path(self):
        """Get path to contracts/interfaces.md."""
        return (
            Path(__file__).parent.parent.parent
            / "specs"
            / "004-kernel-refactor"
            / "contracts"
            / "interfaces.md"
        )

    def test_contracts_document_exists(self, contracts_path):
        """Verify contracts/interfaces.md exists."""
        assert contracts_path.exists(), f"contracts/interfaces.md not found at {contracts_path}"

    def test_contracts_document_phase_orchestrator(self, contracts_path):
        """Verify PhaseOrchestrator interface is documented."""
        content = contracts_path.read_text()

        assert "PhaseOrchestrator" in content or "phase_orchestrator" in content.lower(), (
            "contracts/interfaces.md must document PhaseOrchestrator interface"
        )

        # Check for phase methods
        assert "phase_a" in content.lower() or "phase_a_taskprofile_ttl" in content, (
            "contracts/interfaces.md must document phase_a_taskprofile_ttl method"
        )

    def test_contracts_document_plan_refinement(self, contracts_path):
        """Verify PlanRefinement interface is documented."""
        content = contracts_path.read_text()

        assert "PlanRefinement" in content or "plan_refinement" in content.lower(), (
            "contracts/interfaces.md must document PlanRefinement interface"
        )

        assert "apply_actions" in content.lower(), (
            "contracts/interfaces.md must document apply_actions method"
        )

    def test_contracts_document_step_preparation(self, contracts_path):
        """Verify StepPreparation interface is documented."""
        content = contracts_path.read_text()

        assert "StepPreparation" in content or "step_preparation" in content.lower(), (
            "contracts/interfaces.md must document StepPreparation interface"
        )

        assert "get_ready_steps" in content.lower(), (
            "contracts/interfaces.md must document get_ready_steps method"
        )

    def test_contracts_document_ttl_strategy(self, contracts_path):
        """Verify TTLStrategy interface is documented."""
        content = contracts_path.read_text()

        assert "TTLStrategy" in content or "ttl_strategy" in content.lower(), (
            "contracts/interfaces.md must document TTLStrategy interface"
        )

        assert "create_expiration_response" in content.lower(), (
            "contracts/interfaces.md must document create_expiration_response method"
        )


class TestDataModelDocumentation:
    """Test T069: Verify data models are documented."""

    @pytest.fixture
    def data_model_path(self):
        """Get path to data-model.md."""
        return (
            Path(__file__).parent.parent.parent
            / "specs"
            / "004-kernel-refactor"
            / "data-model.md"
        )

    def test_data_model_document_exists(self, data_model_path):
        """Verify data-model.md exists."""
        assert data_model_path.exists(), f"data-model.md not found at {data_model_path}"

    def test_data_model_documents_phase_result(self, data_model_path):
        """Verify PhaseResult data model is documented."""
        content = data_model_path.read_text()

        assert "PhaseResult" in content, (
            "data-model.md must document PhaseResult data model"
        )

    def test_data_model_documents_refinement_result(self, data_model_path):
        """Verify RefinementResult data model is documented."""
        content = data_model_path.read_text()

        assert "RefinementResult" in content, (
            "data-model.md must document RefinementResult data model"
        )

    def test_data_model_documents_step_preparation_result(self, data_model_path):
        """Verify StepPreparationResult data model is documented."""
        content = data_model_path.read_text()

        assert "StepPreparationResult" in content, (
            "data-model.md must document StepPreparationResult data model"
        )

    def test_data_model_documents_ttl_expiration_result(self, data_model_path):
        """Verify TTLExpirationResult data model is documented."""
        content = data_model_path.read_text()

        assert "TTLExpirationResult" in content, (
            "data-model.md must document TTLExpirationResult data model"
        )


class TestLOCMeasurementsDocumentation:
    """Test T070: Verify LOC measurements are documented."""

    @pytest.fixture
    def plan_path(self):
        """Get path to plan.md."""
        return Path(__file__).parent.parent.parent / "specs" / "004-kernel-refactor" / "plan.md"

    def test_plan_document_exists(self, plan_path):
        """Verify plan.md exists."""
        assert plan_path.exists(), f"plan.md not found at {plan_path}"

    def test_plan_documents_baseline_loc(self, plan_path):
        """Verify plan.md documents baseline LOC measurement."""
        content = plan_path.read_text()

        # Check for baseline LOC (should mention ~1351 or similar)
        loc_pattern = r"\d{3,4}\s*(?:LOC|lines?|lines of code)"
        assert re.search(loc_pattern, content, re.IGNORECASE), (
            "plan.md must document baseline LOC measurement (before refactoring)"
        )

    def test_plan_documents_target_loc(self, plan_path):
        """Verify plan.md documents target LOC (≤800)."""
        content = plan_path.read_text()

        # Check for target LOC (≤800 or <750)
        assert "800" in content or "≤800" in content or "<=800" in content, (
            "plan.md must document target LOC (≤800)"
        )

    def test_plan_documents_loc_reduction(self, plan_path):
        """Verify plan.md documents LOC reduction goal."""
        content = plan_path.read_text()

        # Check for reduction language
        assert (
            "reduce" in content.lower()
            or "reduction" in content.lower()
            or "extract" in content.lower()
        ), (
            "plan.md must document LOC reduction goal"
        )

    def test_plan_documents_kernel_files(self, plan_path):
        """Verify plan.md documents which files count toward kernel LOC."""
        content = plan_path.read_text()

        # Check for orchestrator.py and executor.py
        assert "orchestrator" in content.lower() and "executor" in content.lower(), (
            "plan.md must document which kernel files count toward LOC (orchestrator.py, executor.py)"
        )

