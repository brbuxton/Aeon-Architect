"""Integration tests for supervisor error correction."""

import pytest

from aeon.exceptions import SupervisorError
from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.supervisor.repair import Supervisor
from tests.fixtures.mock_llm import MockLLMAdapter


class TestSupervisorErrorCorrection:
    """Integration tests for supervisor error correction in orchestration."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM adapter that can simulate malformed JSON."""
        return MockLLMAdapter()

    @pytest.fixture
    def supervisor(self, mock_llm):
        """Create supervisor instance."""
        system_prompt = "You are a JSON repair assistant. Fix malformed JSON. Return only corrected JSON."
        return Supervisor(llm_adapter=mock_llm, system_prompt=system_prompt)

    @pytest.fixture
    def orchestrator(self, mock_llm, supervisor):
        """Create orchestrator with supervisor."""
        memory = InMemoryKVStore()
        return Orchestrator(
            llm=mock_llm,
            memory=memory,
            ttl=10,
            supervisor=supervisor
        )

    def test_supervisor_repairs_malformed_plan_json(self, orchestrator, mock_llm):
        """Test that supervisor repairs malformed JSON in plan generation."""
        # Setup mock to first return malformed JSON, then supervisor repairs it
        malformed_response = '{"goal": "test", "steps": [{"step_id": "1"'  # Missing closing
        
        call_count = 0
        original_generate = mock_llm.generate
        
        def generate_with_repair(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call returns malformed JSON
                return {"text": malformed_response}
            else:
                # Supervisor repair call returns fixed JSON
                return {"text": '{"goal": "test", "steps": [{"step_id": "1", "description": "Step 1", "status": "pending"}]}'}
        
        mock_llm.generate = generate_with_repair
        
        # This should trigger supervisor repair and succeed
        plan = orchestrator.generate_plan("test request")
        assert plan.goal == "test"
        assert len(plan.steps) == 1


