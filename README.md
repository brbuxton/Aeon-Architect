# Aeon Architect

**Adaptive multi-pass reasoning engine** that executes iterative plan → execute → evaluate → refine loops until convergence, using declarative plans, semantic validation, convergence detection, and adaptive depth heuristics.

## Overview

Aeon Architect is an adaptive multi-pass reasoning engine that reliably executes complex tasks through iterative refinement cycles. The system uses:

- **Multi-pass execution**: Iterative plan → execute → evaluate → refine loops until convergence or TTL expiration
- **Deterministic phase control**: Four-phase orchestration (A: TaskProfile & TTL → B: Planning & Refinement → C: Execution Passes → D: Adaptive Depth)
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

The system executes tasks through a deterministic four-phase cycle:

1. **Phase A: TaskProfile & TTL Allocation** - Infer task complexity and allocate resources
2. **Phase B: Initial Plan & Pre-Execution Refinement** - Generate and refine initial plan
3. **Phase C: Execution Passes** - Execute → Evaluate → Refine → Repeat until convergence
4. **Phase D: Adaptive Depth** - Adjust reasoning depth and TTL based on complexity mismatch

Each pass evaluates convergence (completeness, coherence, consistency) and refines the plan when needed, continuing until convergence is achieved or TTL expires.

## Project Structure

```
aeon/
├── kernel/              # Core orchestrator (<800 LOC)
│   ├── orchestrator.py  # Thin coordination logic (453 LOC)
│   ├── executor.py      # Step execution routing (182 LOC)
│   └── state.py         # Orchestration state data structures
├── orchestration/       # Orchestration strategy modules (extracted from kernel)
│   ├── phases.py        # Phase A/B/C/D orchestration logic
│   ├── refinement.py    # Plan refinement action application
│   ├── step_prep.py     # Step preparation and dependency checking
│   └── ttl.py           # TTL expiration response generation
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

### Sprint 1 Features ✅

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

### ✅ User Story 8: Multi-Mode Step Execution
Execute steps via tools, explicit LLM reasoning, or fallback when tools are missing. Includes missing-tool detection, supervisor repair, and graceful fallback to LLM reasoning.

### Sprint 2 Features ✅ (Adaptive Multi-Pass Reasoning Engine)

### ✅ User Story 1: Multi-Pass Execution with Deterministic Phase Control
Iteratively execute, evaluate, and refine plans until convergence or TTL expiration. Supports deterministic phase sequencing (Phase A: TaskProfile & TTL → Phase B: Initial Plan & Pre-Execution Refinement → Phase C: Execution Passes → Phase D: Adaptive Depth).

### ✅ User Story 2: TaskProfile Inference and TTL Allocation
Automatically infer task complexity characteristics (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) and allocate TTL accordingly before planning.

### ✅ User Story 3: Recursive Planning and Plan Refinement
Generate initial plans, create subplans for complex steps, and refine plan fragments using LLM-based reasoning with delta-style operations (ADD/MODIFY/REMOVE).

### ✅ User Story 4: Semantic Validation of Plans and Execution Artifacts
Validate plans, steps, and execution artifacts for semantic quality issues (specificity, relevance, consistency, hallucination, do/say mismatch) using LLM-based reasoning.

### ✅ User Story 5: Convergence Detection and Completion Assessment
Determine whether task execution has converged on a complete, coherent, consistent solution using LLM-based reasoning with configurable thresholds.

### ✅ User Story 6: Adaptive Depth Integration
Update TaskProfile at pass boundaries when complexity mismatch is detected, adjusting TTL, reasoning depth, and processing strategies dynamically.

### Sprint 4 Features ✅ (Kernel Refactoring)

### ✅ Kernel LOC Reduction
Refactored kernel from 1351 LOC to 635 LOC (53% reduction) by extracting orchestration strategy logic to `aeon/orchestration/` modules while preserving 100% behavioral compatibility.

### Sprint 5 Features ✅ (Observability & Logging)

### ✅ User Story 1: Phase-Aware Structured Logging
Structured logging with correlation IDs, phase entry/exit events, and state transitions that enable tracing execution through all phases and passes.

### ✅ User Story 2: Actionable Error Logging
Structured error logging with error codes (AEON.<COMPONENT>.<CODE>), severity levels, and comprehensive context for rapid diagnosis.

### ✅ User Story 3: Refinement and Execution Debug Visibility
Detailed logs showing refinement outcomes, evaluation signals, plan state changes, and execution results.

### ✅ User Story 4: Comprehensive Test Coverage
Test coverage expanded from 55% to 80%+ with comprehensive integration and unit tests covering phase transitions, error paths, TTL boundaries, and context propagation.

### Sprint 6 Features 🚧 (In Progress - Phase Transition Stabilization)

### 🚧 User Story 1: Explicit Phase Transition Contracts
Explicit, testable contracts for each phase transition (A→B, B→C, C→D, D→A/B) defining required inputs, guaranteed outputs, invariants, and enumerated failure conditions.

### 🚧 User Story 2: Deterministic Context Propagation
Complete and accurate context propagation to all LLM calls including task profile, plan metadata, previous outputs, evaluation results, and adaptive depth inputs.

### 🚧 User Story 3: Prompt Context Alignment
Verification that all prompt schema keys are populated or removed, with no null semantic inputs.

### 🚧 User Story 4: TTL Boundary Behavior
Correct TTL decrement behavior (once per cycle), proper handling at boundaries (TTL=1, TTL=0, expiration), and TTLExpirationResponse usage.

### 🚧 User Story 5: ExecutionPass Consistency
Consistent ExecutionPass objects with required fields populated before/after phases and invariants maintained.

### 🚧 User Story 6: Phase Boundary Logging
Complete phase boundary logging with entry/exit events, state snapshots, TTL snapshots, and structured error logs.

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

### Architecture Epic
- [Architecture Epic Documentation](ADAPTIVE_REASONING_FRAMEWORK.md) - North Star, Golden Path Demos, and Sprint Gates
- [Backlog](BACKLOG.md) - Future enhancements and sprint breakdown

### Sprint 1 (Aeon Core)
- [Specification](specs/001-aeon-core/spec.md)
- [Implementation Plan](specs/001-aeon-core/plan.md)
- [Tasks](specs/001-aeon-core/tasks.md)
- [Data Model](specs/001-aeon-core/data-model.md)
- [Interface Contracts](specs/001-aeon-core/contracts/interfaces.md)

### Sprint 2 (Adaptive Multi-Pass Reasoning)
- [Specification](specs/003-adaptive-reasoning/spec.md)
- [Implementation Plan](specs/003-adaptive-reasoning/plan.md)
- [Tasks](specs/003-adaptive-reasoning/tasks.md)
- [Data Model](specs/003-adaptive-reasoning/data-model.md)
- [Quickstart Guide](specs/003-adaptive-reasoning/quickstart.md)
- [Interface Contracts](specs/003-adaptive-reasoning/contracts/interfaces.md)

### Sprint 4 (Kernel Refactoring)
- [Specification](specs/004-kernel-refactor/spec.md)
- [Implementation Plan](specs/004-kernel-refactor/plan.md)
- [Tasks](specs/004-kernel-refactor/tasks.md)
- [Data Model](specs/004-kernel-refactor/data-model.md)
- [Interface Contracts](specs/004-kernel-refactor/contracts/interfaces.md)

### Sprint 5 (Observability & Logging)
- [Specification](specs/005-observability-logging/spec.md)
- [Implementation Plan](specs/005-observability-logging/plan.md)
- [Tasks](specs/005-observability-logging/tasks.md)
- [Data Model](specs/005-observability-logging/data-model.md)
- [Interface Contracts](specs/005-observability-logging/contracts/interfaces.md)

### Sprint 6 (Phase Transition Stabilization) 🚧
- [Specification](specs/006-phase-transitions/spec.md)
- [Tasks](specs/006-phase-transitions/tasks.md)
- [Analysis Report](specs/006-phase-transitions/ANALYSIS_REPORT.md)

## License

MIT

## Status

### ✅ Completed Sprints

**Sprint 1 (Aeon Core)** - All 8 user stories implemented and tested:
- ✅ Plan Generation (US1)
- ✅ Plan Execution (US2)
- ✅ Supervisor Error Correction (US3)
- ✅ Tool Registration and Invocation (US4)
- ✅ Key/Value Memory Operations (US5)
- ✅ TTL Expiration Handling (US6)
- ✅ Orchestration Cycle Logging (US7)
- ✅ Multi-Mode Step Execution (US8)

**Sprint 2 (Adaptive Multi-Pass Reasoning)** - All 6 user stories implemented:
- ✅ Multi-Pass Execution with Deterministic Phase Control (US1)
- ✅ TaskProfile Inference and TTL Allocation (US2)
- ✅ Recursive Planning and Plan Refinement (US3)
- ✅ Semantic Validation of Plans and Execution Artifacts (US4)
- ✅ Convergence Detection and Completion Assessment (US5)
- ✅ Adaptive Depth Integration (US6)

**Sprint 4 (Kernel Refactoring)** - Constitutional compliance restored:
- ✅ Kernel LOC reduced from 1351 to 635 LOC (53% reduction)
- ✅ All orchestration strategy logic extracted to `aeon/orchestration/` modules
- ✅ 100% behavioral compatibility preserved
- ✅ All 289 tests passing

**Sprint 5 (Observability & Logging)** - All 4 user stories implemented:
- ✅ Phase-Aware Structured Logging (US1)
- ✅ Actionable Error Logging (US2)
- ✅ Refinement and Execution Debug Visibility (US3)
- ✅ Comprehensive Test Coverage (US4) - Expanded from 55% to 80%+

### 🚧 Current Sprint

**Sprint 6 (Phase Transition Stabilization)** - In Progress:
- 🚧 Explicit Phase Transition Contracts (US1)
- 🚧 Deterministic Context Propagation (US2)
- 🚧 Prompt Context Alignment (US3)
- 🚧 TTL Boundary Behavior (US4)
- 🚧 ExecutionPass Consistency (US5)
- 🚧 Phase Boundary Logging (US6)

### Metrics

- **Test Coverage**: 80%+ overall coverage (80-100% for core modules)
- **Kernel LOC**: 635 LOC (under 800 LOC constitutional limit)
- **Tests Passing**: 289+ tests
- **Architecture**: Multi-pass reasoning engine with deterministic phase control



