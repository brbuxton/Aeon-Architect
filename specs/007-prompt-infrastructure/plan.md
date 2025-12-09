# Implementation Plan: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Branch**: `007-prompt-infrastructure` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-prompt-infrastructure/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a unified, contract-driven prompt subsystem and Phase E (Answer Synthesis) to complete the conceptual A→B→C→D→E reasoning loop. The implementation consolidates all inline prompts into a centralized registry with schema-backed contracts, enforces JSON extraction and validation for structured outputs, and introduces minimal answer synthesis that integrates correctly with Aeon's actual execution flow. All prompts are extracted from kernel, supervisor, phases, and tools modules into a new `aeon/prompts/registry.py` module, and Phase E is implemented as a first-class orchestration phase invoked at the C-loop exit point.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0 (existing), jsonschema>=4.0.0 (existing), requests>=2.31.0 (existing), pyyaml>=6.0.0 (existing), existing ModelClient/LLMAdapter abstraction (no modifications needed)  
**Storage**: N/A (in-memory prompt registry, no persistence required)  
**Testing**: pytest (existing), pytest-cov (existing), Level 1 prompt tests (unit tests for prompt infrastructure components)  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Prompt registry lookup <1ms, prompt rendering <10ms, JSON extraction <50ms per response  
**Constraints**: Kernel <800 LOC (must remain compliant), prompt registry single-file until >100 prompts, Pydantic v1/v2 compatibility required, no inline prompts outside registry  
**Scale/Scope**: <100 prompts (single-file registry acceptable), all prompts extracted from kernel/supervisor/phases/tools modules, Phase E integration at C-loop exit point

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, minimal wiring code in OrchestrationEngine.run_multipass() to invoke Phase E at C-loop exit point. This is orchestration control flow (invoking a phase), not domain logic. Phase E itself is implemented outside kernel in `aeon/orchestration/phases.py` as a first-class phase, not as a helper function in OrchestrationEngine. The kernel only builds PhaseEInput and calls execute_phase_e() - this is minimal orchestration wiring, not business logic.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Estimated addition: ~20-30 LOC for Phase E invocation wiring (building PhaseEInput, calling execute_phase_e, attaching final_answer to execution result). Prompt removal from kernel reduces LOC. Net change should be minimal or negative. Current kernel (orchestrator.py + executor.py) is well under 800 LOC.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Prompt consolidation removes domain logic (prompt strings) from kernel. Phase E wiring is orchestration control flow only. All prompt logic and Phase E synthesis logic reside outside kernel.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Prompt registry is a new top-level module `aeon/prompts/registry.py` (outside kernel). Phase E is implemented in `aeon/orchestration/phases.py` as a first-class phase (outside kernel). Kernel only has minimal wiring for Phase E invocation.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. Prompt registry exposes PromptId enum and PromptRegistry class with get_prompt() and validate_output() methods. Phase E has explicit function signature: `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer`. All interactions are through well-defined interfaces.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. Prompt registry and Phase E do not access kernel internals. They receive only the data they need through explicit parameters (PhaseEInput, LLMAdapter, PromptRegistry).

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: N/A. This feature does not modify plan structure. Plans remain JSON/YAML declarative structures.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: N/A. No procedural logic added to plans.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Partially. Minimal kernel mutation required for Phase E wiring (invocation at C-loop exit). This is rare, deliberate, and documented. Prompt consolidation actually reduces kernel code by removing inline prompts.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. Phase E wiring is minimal (~20-30 LOC), deliberate (required for C-loop exit integration), and documented in spec (FR-019 through FR-024). Prompt removal is documented in FR-004 and FR-128.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes. This feature is infrastructure-focused (prompt management, contracts, answer synthesis). No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, or advanced memory required.

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
├── prompts/
│   └── registry.py              # Prompt registry with PromptId enum, PromptDefinition, PromptRegistry class
├── orchestration/
│   └── phases.py                # Phase E implementation (execute_phase_e function, PhaseEInput, FinalAnswer models)
├── kernel/
│   └── orchestrator.py          # Minimal Phase E wiring (removes inline prompts, adds Phase E invocation)
└── [existing modules: supervisor, validation, convergence, adaptive, plan, tools, etc.]

tests/
├── unit/
│   └── prompts/
│       └── test_registry.py     # Level 1 prompt tests (model instantiation, rendering, output validation, invariants)
├── integration/
│   └── orchestration/
│       └── test_phase_e.py      # Phase E integration tests (3 scenarios: complete data, TTL expiration, incomplete data)
└── cli/
    └── test_final_answer_display.py  # CLI display tests for FinalAnswer
```

**Structure Decision**: Single Python package structure. Prompt registry is a new top-level module `aeon/prompts/registry.py` (outside kernel per Principle II). Phase E is implemented in existing `aeon/orchestration/phases.py` as a first-class phase function. Kernel changes are minimal (prompt removal + Phase E wiring in `aeon/kernel/orchestrator.py`). Tests follow existing structure: unit tests for prompt infrastructure, integration tests for Phase E, CLI tests for display logic.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All constitutional requirements are satisfied. Minimal kernel changes are justified as orchestration control flow (Phase E invocation), not domain logic.
