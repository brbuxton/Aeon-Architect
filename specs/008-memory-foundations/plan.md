# Implementation Plan: Memory Foundations

**Branch**: `008-memory-foundations` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-memory-foundations/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This sprint introduces Short-Term Memory (STM) and Session subsystems to enable session-scoped memory that persists across multiple executions (turns) within a single session. STM is ephemeral, bounded, and scoped to a single Aeon session. Memory entries are stored in-memory only with capacity and TTL-based eviction. The Memory Access Interface (MAI) abstracts all memory operations behind a replaceable interface, with STM and NullMemory implementations. Memory can be optionally injected into LLM prompts through explicit injection points in the prompt registry. All memory operations degrade gracefully and never block execution. Session subsystem manages session lifecycle independently, issuing unique session_ids and tracking session state (active/expired/closed).

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0 (for validation and data models), existing aeon kernel modules  
**Storage**: In-memory only (dict-based storage, no disk I/O, no persistence)  
**Testing**: pytest>=7.4.0 (unit, integration, contract tests)  
**Target Platform**: Linux server (Python runtime)
**Project Type**: Single Python package (aeon module structure)  
**Performance Goals**: Memory operations must be non-blocking and degrade gracefully. No specific throughput requirements, but operations should complete in <10ms for typical workloads.  
**Constraints**: 
- Kernel LOC must remain under 800 after this feature
- Memory operations must never raise exceptions that block execution
- Zero file I/O operations (verified by automated tests)
- Memory capacity must be bounded and deterministic
- TTL decrement must be deterministic and autonomous  
**Scale/Scope**: 
- Memory capacity: Configurable limit (e.g., 100-1000 entries per session)
- Session TTL: Initial value 3 (configurable)
- Memory Entry TTL: Initial value 10 (configurable)
- Multiple sessions supported concurrently
- Multiple executions (turns) per session supported

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ All gates passed. Re-evaluated after Phase 1 design completion.

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **YES, but minimal**: Kernel needs to wire memory access interface calls (write_entry, select_for_injection) at appropriate phase boundaries (Phase A, B, D completion). This is orchestration wiring, not domain logic. Memory subsystem is external to kernel.
- [x] Will kernel LOC remain under 800 after this feature?
  - **YES**: Estimated kernel changes: ~50-100 LOC for memory interface wiring at phase boundaries. Kernel remains well under 800 LOC limit.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **NO**: Kernel only wires memory interface calls. All memory logic (storage, eviction, TTL, selection) lives in external memory subsystem. Session subsystem is also external.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **YES**: Memory subsystem (STM, NullMemory) and Session subsystem are external modules with clean interfaces. Kernel only calls interface methods.
- [x] Do new modules interact through clean interfaces only?
  - **YES**: Memory Access Interface (MAI) abstracts all memory operations. Session subsystem has its own interface. Kernel communicates only through these interfaces.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **NO**: Memory and Session subsystems have no knowledge of kernel internals. They operate through interface contracts only.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **N/A**: This feature does not modify plan structure. Plans remain JSON declarative structures.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **NO**: No procedural logic added to plans. Memory is orthogonal to plan structure.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **PARTIAL**: Minimal kernel changes required for wiring memory interface calls at phase boundaries. Core memory logic is external.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **YES**: Kernel changes are minimal (~50-100 LOC), deliberate (orchestration wiring only), and fully documented in this plan and spec.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **YES**: This is Sprint 8 (Memory Foundations), explicitly scoped to Short-Term Memory only. No embeddings, LTM, persistence, or semantic analysis. Simple in-memory storage with deterministic eviction.

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
aeon/
├── memory/
│   ├── __init__.py
│   ├── interface.py          # Memory Access Interface (MAI) - abstract interface
│   ├── stm.py                 # Short-Term Memory (STM) implementation
│   ├── null_memory.py         # NullMemory implementation (no-op)
│   └── kv_store.py            # Existing InMemoryKVStore (kept for backward compatibility)
├── session/
│   ├── __init__.py
│   ├── interface.py           # Session subsystem interface
│   └── manager.py             # Session subsystem implementation
├── kernel/
│   ├── orchestrator.py        # Kernel orchestrator (minimal wiring changes)
│   └── executor.py            # Kernel executor (no changes)
├── prompts/
│   ├── registry.py             # Prompt registry (extend for memory injection points)
│   └── ...
└── ...

tests/
├── contract/
│   └── test_memory_interface.py    # Contract tests for MAI
├── integration/
│   ├── test_memory_integration.py  # Integration tests for memory + orchestrator
│   └── test_session_integration.py # Integration tests for session + orchestrator
└── unit/
    ├── test_stm.py                  # Unit tests for STM
    ├── test_null_memory.py          # Unit tests for NullMemory
    └── test_session_manager.py      # Unit tests for Session subsystem
```

**Structure Decision**: Single Python package structure. Memory subsystem lives in `aeon/memory/` with interface abstraction. Session subsystem lives in `aeon/session/` as a separate autonomous subsystem. Kernel (`aeon/kernel/`) has minimal wiring changes to call memory interface at phase boundaries. Prompt registry (`aeon/prompts/`) is extended to support memory injection points. All modules interact through clean interfaces only.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
