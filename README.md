# Aeon Architect

**Adaptive multi-pass reasoning engine** that executes iterative plan → execute → evaluate → refine loops until convergence, using declarative plans, semantic validation, convergence detection, and adaptive depth heuristics.

## Overview

Aeon Architect is an adaptive multi-pass reasoning engine that reliably executes complex tasks through iterative refinement cycles. The system uses:

- **Multi-pass execution**: Iterative plan → execute → evaluate → refine loops until convergence or TTL expiration
- **Deterministic phase control**: Five-phase orchestration (A: TaskProfile & TTL → B: Planning & Refinement → C: Execution Passes → D: Adaptive Depth → E: Final Answer Synthesis) - All phases implemented and functional
- **Declarative plans**: JSON/YAML data structures describing multi-step execution
- **Semantic validation**: LLM-based validation of plans, steps, and execution artifacts
- **Convergence detection**: Automatic assessment of solution completeness, coherence, and consistency
- **Adaptive depth**: Dynamic adjustment of reasoning depth and TTL based on task complexity
- **Comprehensive observability**: Phase-aware structured logging with correlation IDs and actionable error reporting

## Architecture

Aeon follows strict architectural principles:

- **Kernel minimalism**: Core orchestrator remains under 800 LOC (constitutional requirement)
- **Separation of concerns**: Tools, memory, supervisor, validation, and orchestration strategy are external modules
- **Declarative plans**: Pure data structures, no executable code
- **Interface contracts**: All external modules communicate through well-defined interfaces
- **Deterministic execution**: Same inputs produce same phase transitions (LLM outputs may vary)
- **LLM-based reasoning**: Semantic judgments use LLM; control flow is host-based

### Multi-Pass Reasoning Loop

The system executes tasks through a deterministic five-phase cycle:

1. **Phase A: TaskProfile & TTL Allocation** - Infer task complexity and allocate resources
2. **Phase B: Initial Plan & Pre-Execution Refinement** - Generate and refine initial plan
3. **Phase C: Execution Passes** - Execute → Evaluate → Refine → Repeat until convergence
4. **Phase D: Adaptive Depth** - Adjust reasoning depth and TTL based on complexity mismatch
5. **Phase E: Final Answer Synthesis** - Synthesize coherent final answer from execution results

Each pass evaluates convergence (completeness, coherence, consistency) and refines the plan when needed, continuing until convergence is achieved or TTL expires. Phase E completes the reasoning loop by producing the final answer.

## Project Structure

```
aeon/
├── kernel/              # Core orchestrator (<800 LOC)
│   ├── orchestrator.py  # Thin coordination logic (453 LOC)
│   ├── executor.py      # Step execution routing (182 LOC)
│   └── state.py         # Orchestration state data structures
├── orchestration/       # Orchestration strategy modules (extracted from kernel)
│   ├── phases.py        # Phase A/B/C/D/E orchestration logic (includes Phase E synthesis)
│   ├── refinement.py    # Plan refinement action application
│   ├── step_prep.py     # Step preparation and dependency checking
│   └── ttl.py           # TTL expiration response generation
├── prompts/             # Centralized prompt management (Sprint 7)
│   └── registry.py      # Prompt registry with contracts and validation
├── plan/                # Plan engine (parser, validator, recursive planner)
├── adaptive/            # Adaptive reasoning heuristics
│   ├── heuristics.py    # TaskProfile inference and adaptive depth
│   └── models.py        # TaskProfile and adaptive depth models
├── convergence/         # Convergence detection engine
│   ├── engine.py        # Convergence assessment logic
│   └── models.py        # Convergence assessment models
├── validation/          # Validation layer (schema + semantic)
│   ├── schema.py        # Structural validation
│   └── semantic.py      # Semantic validation (LLM-based)
├── memory/              # Memory subsystem (K/V store)
├── tools/               # Tool system (registry, interface, stubs)
├── supervisor/          # Error repair module
├── llm/                 # LLM adapter interface
├── observability/       # Observability and logging (JSONL, phase-aware)
└── cli/                 # CLI interface (optional)

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── contract/            # Contract tests
```

## Features

### ✅ Sprint 1: Aeon Core
Core orchestration engine with plan generation, step execution, tool integration, memory operations, TTL handling, and structured logging. See [Sprint 1 specification](specs/001-aeon-core/spec.md) for details.

### ✅ Sprint 2: Adaptive Multi-Pass Reasoning
Multi-pass execution with deterministic phase control, TaskProfile inference, recursive planning, semantic validation, convergence detection, and adaptive depth adjustment. See [Sprint 2 specification](specs/003-adaptive-reasoning/spec.md) for details.

### ✅ Sprint 4: Kernel Refactoring
Kernel LOC reduced from 1351 to 635 (53% reduction) by extracting orchestration strategy to separate modules while preserving 100% behavioral compatibility. See [Sprint 4 specification](specs/004-kernel-refactor/spec.md) for details.

### ✅ Sprint 5: Observability & Logging
Phase-aware structured logging with correlation IDs, actionable error logging with error codes, and comprehensive test coverage (55% → 80%+). See [Sprint 5 specification](specs/005-observability-logging/spec.md) for details.

### ✅ Sprint 6: Phase Transition Stabilization
Explicit phase transition contracts, deterministic context propagation, prompt context alignment, TTL boundary behavior, ExecutionPass consistency, and phase boundary logging. See [Sprint 6 specification](specs/006-phase-transitions/spec.md) for details.

### ✅ Sprint 7: Prompt Infrastructure + Prompt Contracts (Completed)
Centralized prompt management with registry, schema-backed prompt contracts with validation, unified JSON extraction, and Phase E (Final Answer Synthesis) implementation. All 23 system prompts consolidated, typed input/output models, and complete A→B→C→D→E reasoning loop. See [Sprint 7 specification](specs/007-prompt-infrastructure/spec.md) for details.

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

### Command Line Interface

The easiest way to use Aeon Core is through the CLI:

**Installation:**
```bash
# Install the package in development mode to get the CLI
pip install -e .

# Verify installation
aeon --help
```

**Basic Usage:**
```bash
# Generate a plan from a natural language request
aeon plan "calculate the sum of 5 and 10"

# Execute a request (generate plan and run it)
aeon execute "calculate the sum of 5 and 10"

# Output as JSON
aeon execute --json "your request here"
aeon plan --json "your request here"
```

**LLM Adapter Options:**
```bash
# Use with llama-cpp (default, runs on localhost:8000)
aeon execute "analyze data and generate report"

# Use with mock LLM for testing
aeon --llm mock execute "test request"

# Use with remote API (requires API key)
aeon --llm remote --api-key YOUR_KEY --api-url https://api.openai.com/v1/chat/completions execute "your request"
```

**Configuration:**
```bash
# Use a config file (searches: .aeon.yaml, ~/.aeon.yaml, ~/.config/aeon/config.yaml)
aeon --config .aeon.yaml execute "your request"

# Override config with command-line options
aeon --llm llama-cpp --ttl 20 execute "your request"
```

**Example Output:**
```bash
$ aeon --llm mock execute "calculate 5 plus 10"

Executing request: calculate 5 plus 10

Generating plan...
Executing plan...

Status: completed
TTL remaining: 9

Plan:
  Goal: calculate 5 plus 10
  Steps: 1
    1. [complete][tool] Process request: calculate 5 plus 10
      Result: {'result': 'success'}
```

**Configuration File** (`.aeon.yaml`):
```yaml
llm:
  type: llama-cpp  # or "mock", "remote"
  api_url: http://localhost:8000
  model: your-model-name
  api_key: your-api-key  # for remote LLM

orchestrator:
  ttl: 10
  log_file: orchestration.jsonl
```

See `.aeon.yaml.example` for a complete example.

### Python API Usage

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

# Format and lint
black aeon/ tests/
ruff check aeon/ tests/
```

See [Testing Documentation](docs/TESTING.md) for details on unit, integration, and contract tests. Coverage requirement: 100% for kernel core logic.

## Constraints

- **Kernel LOC**: Must remain under 800 lines of code (constitutional requirement) - Currently 635 LOC
- **Domain-agnostic**: No cloud, IaC, diagram logic in kernel
- **Sequential execution**: Single-threaded, no concurrency
- **Simple memory**: Basic K/V store with prefix search only
- **Deterministic control flow**: Same inputs produce same phase transitions (LLM outputs may vary)
- **LLM-based reasoning**: Semantic judgments use LLM; control flow is host-based

## Out of Scope

- Diagram generation
- Infrastructure as Code (IaC) generation
- RAG systems
- Cloud-specific logic
- Embeddings and vector search
- Multi-agent concurrency
- Advanced memory features (deferred to Sprint 8)
- Long-term memory persistence (deferred to future sprints)

## Documentation

- **[Architecture Epic](ADAPTIVE_REASONING_FRAMEWORK.md)** - North Star, Golden Path Demos, and Sprint Gates
- **[Backlog](BACKLOG.md)** - Future enhancements and sprint breakdown
- **[Testing Guide](docs/TESTING.md)** - Testing documentation and guidelines

### Sprint Specifications

All sprint documentation is available in the [`specs/`](specs/) directory:

- **Sprint 1**: [Aeon Core](specs/001-aeon-core/) - Core orchestration engine
- **Sprint 2**: [Adaptive Multi-Pass Reasoning](specs/003-adaptive-reasoning/) - Multi-pass execution and convergence
- **Sprint 4**: [Kernel Refactoring](specs/004-kernel-refactor/) - LOC reduction and module extraction
- **Sprint 5**: [Observability & Logging](specs/005-observability-logging/) - Structured logging and error reporting
- **Sprint 6**: [Phase Transition Stabilization](specs/006-phase-transitions/) - Phase contracts and context propagation
- **Sprint 7**: [Prompt Infrastructure + Prompt Contracts](specs/007-prompt-infrastructure/) - Centralized prompt registry, schema-backed contracts, Phase E synthesis

Each sprint folder contains specifications, implementation plans, tasks, data models, and interface contracts.

## License

MIT

## Status

### Current State

- **Current Sprint**: Sprint 8 (Memory Foundations) - See [Backlog](BACKLOG.md) for details
- **Test Coverage**: 62% overall (92-97% for kernel core modules)
- **Kernel LOC**: 635 LOC (under 800 LOC constitutional limit)
- **Tests Passing**: 468 passed, 30 failed (498 total tests)
- **Kernel Coverage**: `executor.py` 92%, `orchestrator.py` 97% (constitutional requirement: 100%)

### Completed Sprints

✅ **Sprint 1** (Aeon Core) - 8 user stories: Plan generation, execution, tools, memory, TTL, logging  
✅ **Sprint 2** (Adaptive Multi-Pass Reasoning) - 6 user stories: Multi-pass execution, TaskProfile, convergence  
✅ **Sprint 4** (Kernel Refactoring) - Kernel LOC reduced 53%, 100% behavioral compatibility  
✅ **Sprint 5** (Observability & Logging) - 4 user stories: Structured logging, error codes, test coverage expansion  
✅ **Sprint 6** (Phase Transition Stabilization) - Phase transition contracts, context propagation, ExecutionPass consistency  
✅ **Sprint 7** (Prompt Infrastructure + Prompt Contracts) - 3 user stories: Centralized prompt registry (23 prompts), schema-backed contracts with validation, Phase E final answer synthesis completing A→B→C→D→E loop  
✅ **Sprint 7** (Prompt Infrastructure + Prompt Contracts) - Centralized prompt registry, schema-backed contracts, unified JSON extraction, Phase E final answer synthesis

See individual sprint specifications in [`specs/`](specs/) for detailed status and user stories.



