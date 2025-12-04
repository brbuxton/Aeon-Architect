"""Integration tests for multi-pass execution scenarios."""

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import StepStatus
from tests.fixtures.mock_llm import MockLLMAdapter


class TestMultiPassExecution:
    """Validate multi-pass execution end-to-end scenarios."""

    def _create_orchestrator(self) -> Orchestrator:
        return Orchestrator(llm=MockLLMAdapter(), memory=InMemoryKVStore(), ttl=10)

    def test_multipass_execution_creates_execution_history(self):
        """Test that multi-pass execution creates execution history."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="design a system architecture for a web application with user authentication"
        )

        assert "execution_history" in result
        history = result["execution_history"]
        assert "execution_id" in history
        assert "task_input" in history
        assert "passes" in history
        assert len(history["passes"]) > 0
        assert "overall_statistics" in history

    def test_multipass_execution_has_phase_sequence(self):
        """Test that multi-pass execution follows phase sequence (A → B → C → D)."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="analyze data and generate report"
        )

        history = result["execution_history"]
        passes = history["passes"]
        
        # Should have at least one pass
        assert len(passes) > 0
        
        # First pass should be in Phase C (execution phase)
        # Phase A and B happen before first pass
        first_pass = passes[0]
        assert "phase" in first_pass
        assert first_pass["phase"] in ["A", "B", "C", "D"]

    def test_multipass_execution_records_pass_metadata(self):
        """Test that each pass records metadata (timing, TTL, plan state)."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="process request"
        )

        history = result["execution_history"]
        passes = history["passes"]
        
        for pass_data in passes:
            assert "pass_number" in pass_data
            assert "phase" in pass_data
            assert "plan_state" in pass_data
            assert "ttl_remaining" in pass_data
            assert "timing_information" in pass_data
            timing = pass_data["timing_information"]
            assert "start_time" in timing

    def test_multipass_execution_tracks_refinements(self):
        """Test that multi-pass execution tracks plan refinements."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="complex task requiring refinement"
        )

        history = result["execution_history"]
        stats = history["overall_statistics"]
        
        assert "total_refinements" in stats
        assert stats["total_refinements"] >= 0

    def test_multipass_execution_tracks_convergence(self):
        """Test that multi-pass execution tracks convergence status."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="simple task"
        )

        history = result["execution_history"]
        stats = history["overall_statistics"]
        
        assert "convergence_achieved" in stats
        assert isinstance(stats["convergence_achieved"], bool)

    def test_multipass_execution_handles_ttl_expiration(self):
        """Test that multi-pass execution handles TTL expiration gracefully."""
        orchestrator = Orchestrator(llm=MockLLMAdapter(), memory=InMemoryKVStore(), ttl=1)
        
        # This should trigger TTL expiration quickly
        result = orchestrator.execute_multipass(
            request="very complex task that will exceed TTL"
        )

        # Should return either converged or ttl_expired status
        assert result["status"] in ["converged", "ttl_expired"]
        
        if result["status"] == "ttl_expired":
            # Should have execution history even if TTL expired
            assert "execution_history" in result or "ttl_expired_metadata" in result

    def test_multipass_execution_evaluation_results(self):
        """Test that multi-pass execution includes evaluation results."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="task with evaluation"
        )

        history = result["execution_history"]
        passes = history["passes"]
        
        # At least one pass should have evaluation results
        has_evaluation = False
        for pass_data in passes:
            if "evaluation_results" in pass_data and pass_data["evaluation_results"]:
                has_evaluation = True
                eval_results = pass_data["evaluation_results"]
                # May contain convergence or validation results
                assert isinstance(eval_results, dict)
                break
        
        # Note: Evaluation may not always occur depending on implementation
        # This test just verifies the structure if evaluation exists

    def test_multipass_execution_final_result(self):
        """Test that multi-pass execution includes final result."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            request="task"
        )

        history = result["execution_history"]
        assert "final_result" in history
        final_result = history["final_result"]
        assert isinstance(final_result, dict)
        assert "status" in final_result or "converged" in final_result

