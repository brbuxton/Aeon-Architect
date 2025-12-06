"""Integration tests for sequential plan execution."""

from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from aeon.plan.models import StepStatus
from tests.fixtures.mock_llm import MockLLMAdapter


class TestPlanExecution:
    """Validate orchestrator end-to-end step execution."""

    def _create_orchestrator(self) -> Orchestrator:
        return Orchestrator(llm=MockLLMAdapter(), memory=InMemoryKVStore(), ttl=5)


