"""Integration tests for sequential plan execution."""

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import StepStatus
from tests.fixtures.mock_llm import MockLLMAdapter


class TestPlanExecution:
    """Validate orchestrator end-to-end step execution."""

    def _create_orchestrator(self) -> Orchestrator:
        return Orchestrator(llm=MockLLMAdapter(), memory=InMemoryKVStore(), ttl=5)

    def test_execute_runs_all_steps_to_completion(self):
        orchestrator = self._create_orchestrator()
        result = orchestrator.execute(
            request="analyze a dataset, generate statistics, and create a report"
        )

        assert result["status"] == "completed"
        assert "plan" in result
        steps = result["plan"]["steps"]
        assert len(steps) == 3
        assert all(step["status"] == StepStatus.COMPLETE for step in steps)

        state = orchestrator.get_state()
        assert state is not None
        assert state.current_step_id is None
        assert all(step.status == StepStatus.COMPLETE for step in state.plan.steps)

