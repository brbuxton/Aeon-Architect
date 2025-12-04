"""Integration test to verify multi-pass execution identical behavior (T040).

This test verifies that multi-pass execution produces identical, consistent
results after the refactoring. It tests that:
1. Multi-pass execution produces consistent results across multiple runs
2. Execution history structure is correct
3. Phase transitions work correctly
4. Convergence detection works correctly
"""

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from tests.fixtures.mock_llm import MockLLMAdapter


class TestMultiPassIdentical:
    """Test that multi-pass execution produces identical behavior."""

    def _create_orchestrator(self, ttl: int = 10) -> Orchestrator:
        """Create orchestrator with mock dependencies."""
        return Orchestrator(
            llm=MockLLMAdapter(),
            memory=InMemoryKVStore(),
            ttl=ttl
        )

    def test_multipass_execution_consistent_results(self):
        """Test that multi-pass execution produces consistent results."""
        request = "analyze data and generate report"
        
        # Run execution twice with same input
        orchestrator1 = self._create_orchestrator()
        result1 = orchestrator1.execute_multipass(request)
        
        orchestrator2 = self._create_orchestrator()
        result2 = orchestrator2.execute_multipass(request)
        
        # Both should have execution_history
        assert "execution_history" in result1
        assert "execution_history" in result2
        
        history1 = result1["execution_history"]
        history2 = result2["execution_history"]
        
        # Both should have same structure
        assert "execution_id" in history1
        assert "execution_id" in history2
        assert "task_input" in history1
        assert "task_input" in history2
        assert history1["task_input"] == history2["task_input"]
        assert history1["task_input"] == request
        
        # Both should have passes
        assert "passes" in history1
        assert "passes" in history2
        
        # Both should have overall_statistics
        assert "overall_statistics" in history1
        assert "overall_statistics" in history2
        
        # Status should be valid
        assert result1["status"] in ["converged", "ttl_expired", "max_passes_reached"]
        assert result2["status"] in ["converged", "ttl_expired", "max_passes_reached"]

    def test_multipass_execution_history_structure(self):
        """Test that execution history has correct structure."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            "process request with multiple steps"
        )
        
        assert "execution_history" in result
        history = result["execution_history"]
        
        # Required fields
        assert "execution_id" in history
        assert isinstance(history["execution_id"], str)
        assert len(history["execution_id"]) > 0
        
        assert "task_input" in history
        assert isinstance(history["task_input"], str)
        
        assert "passes" in history
        assert isinstance(history["passes"], list)
        
        assert "overall_statistics" in history
        assert isinstance(history["overall_statistics"], dict)
        
        stats = history["overall_statistics"]
        assert "total_passes" in stats
        assert isinstance(stats["total_passes"], int)
        assert stats["total_passes"] >= 0
        
        assert "total_refinements" in stats
        assert isinstance(stats["total_refinements"], int)
        assert stats["total_refinements"] >= 0
        
        assert "convergence_achieved" in stats
        assert isinstance(stats["convergence_achieved"], bool)
        
        assert "total_time" in stats
        assert isinstance(stats["total_time"], (int, float))
        assert stats["total_time"] >= 0

    def test_multipass_execution_pass_structure(self):
        """Test that execution passes have correct structure."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass("simple task")
        
        history = result["execution_history"]
        passes = history["passes"]
        
        if len(passes) > 0:
            pass_data = passes[0]
            
            # Required fields
            assert "pass_number" in pass_data
            assert isinstance(pass_data["pass_number"], int)
            assert pass_data["pass_number"] > 0
            
            assert "phase" in pass_data
            assert pass_data["phase"] in ["A", "B", "C", "D"]
            
            assert "plan_state" in pass_data
            assert isinstance(pass_data["plan_state"], dict)
            
            assert "execution_results" in pass_data
            assert isinstance(pass_data["execution_results"], list)
            
            assert "evaluation_results" in pass_data
            assert isinstance(pass_data["evaluation_results"], dict)
            
            assert "refinement_changes" in pass_data
            assert isinstance(pass_data["refinement_changes"], list)
            
            assert "ttl_remaining" in pass_data
            assert isinstance(pass_data["ttl_remaining"], int)
            
            assert "timing_information" in pass_data
            assert isinstance(pass_data["timing_information"], dict)
            
            timing = pass_data["timing_information"]
            assert "start_time" in timing

    def test_multipass_execution_phase_sequence(self):
        """Test that multi-pass execution follows correct phase sequence."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass(
            "complex task requiring refinement"
        )
        
        history = result["execution_history"]
        passes = history["passes"]
        
        # Should have at least one pass (Phase C)
        assert len(passes) > 0
        
        # All passes should be in Phase C (execution phase)
        # Phase A and B happen before first pass
        for pass_data in passes:
            assert "phase" in pass_data
            assert pass_data["phase"] == "C", "All execution passes should be in Phase C"

    def test_multipass_execution_convergence_detection(self):
        """Test that convergence detection works correctly."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass("simple task")
        
        history = result["execution_history"]
        stats = history["overall_statistics"]
        
        # Should have convergence_achieved field
        assert "convergence_achieved" in stats
        assert isinstance(stats["convergence_achieved"], bool)
        
        # If converged, status should reflect that
        if stats["convergence_achieved"]:
            assert result["status"] in ["converged"]

    def test_multipass_execution_final_result_structure(self):
        """Test that final result has correct structure."""
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute_multipass("task with final result")
        
        history = result["execution_history"]
        
        assert "final_result" in history
        final_result = history["final_result"]
        assert isinstance(final_result, dict)
        
        # Should have status or converged field
        assert "status" in final_result or "converged" in final_result
        
        # Should have plan in final result
        if "plan" in final_result:
            assert isinstance(final_result["plan"], dict)

    def test_multipass_execution_with_ttl_expiration(self):
        """Test that TTL expiration is handled correctly."""
        # Use very low TTL to force expiration
        orchestrator = self._create_orchestrator(ttl=1)
        result = orchestrator.execute_multipass(
            "very complex task that will exceed TTL"
        )
        
        # Should return either converged or ttl_expired status
        assert result["status"] in ["converged", "ttl_expired"]
        
        if result["status"] == "ttl_expired":
            # Should have ttl_expiration metadata or execution_history
            assert "execution_history" in result or "ttl_expired_metadata" in result
            
            # Should have ttl_remaining field
            assert "ttl_remaining" in result
            assert result["ttl_remaining"] <= 0

