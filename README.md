# Aeon Core

**Minimal LLM orchestration kernel** that reliably executes a structured thought → tool → thought loop using declarative plans, supervised validation, state management, and deterministic execution.

## Overview

Aeon Core is a minimal LLM orchestration kernel designed for Sprint 1 to demonstrate reliable execution of a structured reasoning loop. The system uses:

- **Declarative plans**: JSON/YAML data structures describing multi-step execution
- **Supervised validation**: Automatic repair of malformed LLM outputs
- **State management**: Tracking orchestration context, tool calls, and TTL
- **Deterministic execution**: Sequential step execution with status updates

## Architecture

The kernel follows strict architectural principles:

- **Kernel minimalism**: Core orchestrator remains under 800 LOC
- **Separation of concerns**: Tools, memory, supervisor, and validation are external modules
- **Declarative plans**: Pure data structures, no executable code
- **Interface contracts**: All external modules communicate through well-defined interfaces

## Project Structure

```
aeon/
├── kernel/              # Core orchestrator (<800 LOC)
├── plan/                # Plan engine (parser, validator, executor)
├── memory/              # Memory subsystem (K/V store)
├── tools/               # Tool system (registry, interface, stubs)
├── supervisor/          # Error repair module
├── validation/          # Validation layer
├── llm/                 # LLM adapter interface
├── observability/       # Logging (JSONL)
└── cli/                 # CLI interface (optional)

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── contract/            # Contract tests
```

## Features (Sprint 1)

### ✅ User Story 1: Plan Generation
Generate declarative multi-step plans from natural language requests.

### ✅ User Story 2: Plan Execution
Execute plans step-by-step with deterministic status updates (pending → running → complete/failed).

### ✅ User Story 3: Supervisor Error Correction
Automatically repair malformed JSON, tool calls, and plan fragments.

### ✅ User Story 4: Tool Registration and Invocation
Register tools and invoke them with validated arguments integrated into LLM reasoning cycles.

### ✅ User Story 5: Key/Value Memory Operations
Store and retrieve values from memory during multi-step reasoning.

### ✅ User Story 6: TTL Expiration Handling
Gracefully stop reasoning when TTL expires with structured response.

### ✅ User Story 7: Orchestration Cycle Logging
Generate JSONL logs for each orchestration cycle with all required fields.

## Installation

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

## Quick Start

### Basic Usage

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.llm.adapters.remote_api import RemoteAPIAdapter
from aeon.memory.kv_store import InMemoryKVStore
from aeon.observability.logger import JSONLLogger
from pathlib import Path

# Initialize components
llm = RemoteAPIAdapter(api_key="your-api-key")
memory = InMemoryKVStore()
logger = JSONLLogger(file_path=Path("orchestration.log"))

# Create orchestrator
orchestrator = Orchestrator(
    llm=llm,
    memory=memory,
    ttl=10,
    logger=logger
)

# Generate and execute plan
result = orchestrator.execute("calculate the sum of 5 and 10")
print(result)
# Output: {"plan": {...}, "status": "completed", "ttl_remaining": 9}
```

### With Tools

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.tools.registry import ToolRegistry
from aeon.tools.stubs.calculator import CalculatorTool
from aeon.tools.stubs.echo import EchoTool
from tests.fixtures.mock_llm import MockLLMAdapter

# Register tools
registry = ToolRegistry()
registry.register(CalculatorTool())
registry.register(EchoTool())

# Create orchestrator with tools
orchestrator = Orchestrator(
    llm=MockLLMAdapter(),
    tool_registry=registry,
    ttl=10
)

# Execute plan with tool invocation
result = orchestrator.execute("add 5 and 10")
```

### With Memory

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.memory.kv_store import InMemoryKVStore
from tests.fixtures.mock_llm import MockLLMAdapter

# Create memory store
memory = InMemoryKVStore()

# Store values before execution
memory.write("user_name", "Alice")
memory.write("user_age", 30)

# Create orchestrator with memory
orchestrator = Orchestrator(
    llm=MockLLMAdapter(),
    memory=memory,
    ttl=10
)

# Execute plan - memory persists across steps
result = orchestrator.execute("process user data")

# Retrieve stored values
name = memory.read("user_name")  # Returns "Alice"
age = memory.read("user_age")    # Returns 30
```

### With Logging

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.observability.logger import JSONLLogger
from pathlib import Path
from tests.fixtures.mock_llm import MockLLMAdapter

# Create logger
logger = JSONLLogger(file_path=Path("orchestration.jsonl"))

# Create orchestrator with logging
orchestrator = Orchestrator(
    llm=MockLLMAdapter(),
    logger=logger,
    ttl=10
)

# Execute plan - logs written to JSONL file
result = orchestrator.execute("analyze dataset and generate report")

# Log file contains structured entries for each cycle:
# {"step_number": 1, "plan_state": {...}, "llm_output": {...}, ...}
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=aeon --cov-report=html

# Format code
black aeon/ tests/

# Lint code
ruff check aeon/ tests/
```

## Testing

- **Unit tests**: Tests for individual components
- **Integration tests**: End-to-end orchestration scenarios
- **Contract tests**: Interface compliance verification

Coverage requirement: 100% test coverage for kernel core logic.

## Constraints

- **Kernel LOC**: Must remain under 800 lines of code (constitutional requirement)
- **Domain-agnostic**: No cloud, IaC, diagram logic in kernel
- **Sequential execution**: Single-threaded, no concurrency in Sprint 1
- **Simple memory**: Basic K/V store with prefix search only

## Out of Scope (Sprint 1)

- Diagram generation
- Infrastructure as Code (IaC) generation
- RAG systems
- Cloud-specific logic
- Embeddings and vector search
- Multi-agent concurrency
- Advanced memory features

## Documentation

- [Specification](specs/001-aeon-core/spec.md)
- [Implementation Plan](specs/001-aeon-core/plan.md)
- [Tasks](specs/001-aeon-core/tasks.md)
- [Data Model](specs/001-aeon-core/data-model.md)
- [Interface Contracts](specs/001-aeon-core/contracts/interfaces.md)

## License

MIT

## Status

🚧 **In Development** - Sprint 1 implementation in progress.



