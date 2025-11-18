# Implementation Plan: Aeon Core

**Branch**: `001-aeon-core` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-aeon-core/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Aeon Core is a minimal LLM orchestration kernel that reliably executes a structured thought → tool → thought loop using declarative plans, supervised validation, state management, and deterministic execution. The system implements a strict kernel architecture where the orchestrator (kernel) handles only LLM loop execution, plan management, state transitions, tool invocation, TTL governance, and supervisor routing. All domain logic, tools, memory, and validation are external modules communicating through clean interfaces. The kernel remains under 800 LOC, domain-agnostic, and testable.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: 
- LLM adapter interface (supporting vLLM, llama-cpp-python, or remote API)
- pydantic or jsonschema for validation
- Standard Python logging or JSONL writer
- Optional: SQLite for state persistence (Sprint 2)

**Storage**: 
- Sprint 1: In-memory key/value store (dict-based implementation)
- Optional Sprint 2: File-based or SQLite persistence

**Testing**: pytest with 100% coverage requirement for kernel core logic  
**Target Platform**: Linux/macOS/Windows (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: 
- Plan generation: <10 seconds (SC-001)
- Kernel execution loop: Deterministic, no specific latency target for Sprint 1
- Memory operations: 99% success rate (SC-005)

**Constraints**: 
- Kernel MUST remain under 800 LOC (constitutional requirement)
- Kernel MUST be domain-agnostic (no cloud, IaC, diagram logic)
- Single-threaded, sequential execution (no concurrency in Sprint 1)
- LLM API retry: 3 attempts with exponential backoff
- Supervisor retry: 2 repair attempts before declaring unrecoverable

**Scale/Scope**: 
- Sprint 1: Single orchestration session, in-memory state
- Plans: Up to 10 steps (SC-002)
- Tools: Stub/dummy tools only (echo, calculator)
- Memory: Simple K/V with prefix search
- No RAG, embeddings, multi-agent, or advanced features

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, but only core orchestration logic (LLM loop, plan execution, state management, TTL governance). All domain logic (tools, memory, validation, supervisor) are external modules. Kernel remains minimal and focused.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes, kernel will be designed to stay under 800 LOC. All non-core functionality is external.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: NO. Kernel contains only orchestration logic. All domain logic (cloud, IaC, diagrams, validation rules) is in external modules.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Tools, memory, supervisor, and validation are separate modules with clean interfaces.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. All external modules (tools, memory, supervisor, validation) communicate through well-defined interface contracts.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: NO. External modules only access kernel through public interface methods.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: Yes. Plans are pure JSON data structures with no executable code.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: NO. Plans are declarative only, describing what to do, not how.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Partially. Core kernel is required for Sprint 1, but all extensions (new tools, memory implementations, supervisors) can be added without kernel changes.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. Kernel changes are limited to core orchestration. All changes will be documented and justified against Principle I.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes. Sprint 1 includes only: kernel, plan engine, state manager, simple memory K/V, tool interface, supervisor, validation layer. All excluded capabilities (diagrams, IaC, RAG, cloud, embeddings, multi-agent) are explicitly out of scope.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
aeon/
├── kernel/              # Core orchestrator (<800 LOC)
│   ├── __init__.py
│   ├── orchestrator.py # Main LLM loop, plan execution
│   ├── state.py        # State management
│   └── ttl.py          # TTL governance
├── plan/               # Plan engine
│   ├── __init__.py
│   ├── parser.py       # JSON/YAML plan parsing
│   ├── validator.py    # Plan schema validation
│   └── executor.py     # Plan step execution
├── memory/             # Memory subsystem
│   ├── __init__.py
│   ├── interface.py    # Memory interface contract
│   └── kv_store.py     # Simple K/V implementation
├── tools/               # Tool system
│   ├── __init__.py
│   ├── registry.py     # Tool registration
│   ├── interface.py    # Tool interface contract
│   └── stubs/          # Sprint 1 stub tools
│       ├── echo.py
│       └── calculator.py
├── supervisor/          # Supervisor module
│   ├── __init__.py
│   └── repair.py       # JSON repair logic
├── validation/          # Validation layer
│   ├── __init__.py
│   ├── schema.py       # Schema validation
│   └── plan_validator.py
├── llm/                 # LLM adapter interface
│   ├── __init__.py
│   ├── interface.py    # LLM adapter contract
│   └── adapters/       # LLM implementations
│       ├── vllm.py
│       ├── llama_cpp.py
│       └── remote_api.py
├── observability/       # Logging
│   ├── __init__.py
│   └── logger.py       # JSONL logging
└── cli/                 # CLI interface (optional Sprint 1)
    ├── __init__.py
    └── main.py

tests/
├── unit/
│   ├── kernel/
│   ├── plan/
│   ├── memory/
│   ├── tools/
│   └── validation/
├── integration/
│   ├── test_orchestration_loop.py
│   ├── test_supervisor_repair.py
│   └── test_tool_invocation.py
└── contract/
    ├── test_memory_interface.py
    ├── test_tool_interface.py
    └── test_llm_interface.py
```

**Structure Decision**: Single Python package following strict separation of concerns. Kernel is isolated in its own module with minimal dependencies. All external modules (memory, tools, supervisor, validation) are separate packages with interface contracts. This structure enforces constitutional principles and enables independent testing and replacement of components.

## Complexity Tracking

No constitutional violations. All design decisions align with constitutional principles:
- Kernel remains minimal and domain-agnostic
- All components communicate through interfaces
- No domain logic in kernel
- Sprint 1 scope constraints respected
