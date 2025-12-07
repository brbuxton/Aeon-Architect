# Implementation Plan: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Branch**: `007-prompt-infrastructure` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-prompt-infrastructure/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a unified, contract-driven prompt subsystem and Phase E (Answer Synthesis) to complete the conceptual A→B→C→D→E reasoning loop. The implementation consolidates all inline prompts into a centralized registry with schema-backed contracts (Pydantic input/output models), removes all inline prompt strings from kernel, supervisor, phases, and tools modules, and introduces minimal answer synthesis that integrates correctly with Aeon's actual execution flow.

**Technical Approach**: Create a centralized prompt registry (`aeon/prompts/registry.py`) with Pydantic contracts for all prompts, extract all inline prompts from identified modules and register them, implement Phase E as a first-class orchestration phase in `aeon/orchestration/phases.py` that synthesizes final answers from execution state, and integrate Phase E at the C-loop exit point in OrchestrationEngine.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0 (existing), existing ModelClient/LLMAdapter abstraction (no modifications needed)  
**Storage**: N/A (in-memory prompt registry, no persistence required)  
**Testing**: pytest (existing), Level 1 prompt tests for contract validation  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Prompt registry lookup <1ms, prompt rendering <10ms, Phase E synthesis <30s (LLM-dependent)  
**Constraints**: Kernel <800 LOC (must remain compliant), prompt registry must support <100 prompts in single file, Phase E must always produce answer (never raise exceptions for missing state)  
**Scale/Scope**: ~20-30 prompts to be extracted and registered, Phase E completes A→B→C→D→E reasoning loop

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, minimal code (~10-20 LOC) for Phase E invocation wiring. Phase E itself is outside kernel (in orchestration module). Wiring is necessary orchestration logic to complete the reasoning loop. Prompt registry and Phase E logic are outside kernel per Principle II.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Kernel changes limited to: (1) removing inline prompt imports (~-50 LOC), (2) Phase E invocation wiring (~+20 LOC). Net change: ~-30 LOC. Kernel remains well under 800 LOC limit.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: NO. Prompt registry is outside kernel. Phase E synthesis logic is outside kernel. Only orchestration wiring (building PhaseEInput and calling execute_phase_e) is in engine, which is outside kernel proper. Kernel only removes prompt imports.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: YES. Prompt registry is a new top-level module (`aeon/prompts/`). Phase E is in orchestration module (`aeon/orchestration/phases.py`). Both are outside kernel.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: YES. Prompt registry provides `get_prompt(prompt_id, input_data)` interface. Phase E provides `execute_phase_e(phase_e_input, llm_adapter, prompt_registry)` interface. All interactions through defined contracts.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: NO. Prompt registry and Phase E do not access kernel internals. They interact only through public interfaces (LLMAdapter, PromptRegistry).

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: N/A. This feature does not modify plan structure. Plans remain declarative JSON/YAML structures.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: NO. Plans remain pure declarative structures. No procedural logic added.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Mostly yes. Prompt registry is completely outside kernel. Phase E is outside kernel. Only minimal wiring (~20 LOC) in OrchestrationEngine (outside kernel proper) for Phase E invocation. Kernel itself only removes imports.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: YES. Kernel changes are minimal (prompt import removal only) and well-documented in spec. Phase E wiring is in OrchestrationEngine, not kernel proper.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: YES. This is Sprint 7 feature focused on prompt infrastructure and answer synthesis. No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, or advanced memory involved. Simple prompt registry and synthesis phase.

## Project Structure

### Documentation (this feature)

```text
specs/007-prompt-infrastructure/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command) ✅ COMPLETE
├── data-model.md        # Phase 1 output (/speckit.plan command) ✅ COMPLETE
├── quickstart.md        # Phase 1 output (/speckit.plan command) ✅ COMPLETE
├── contracts/           # Phase 1 output (/speckit.plan command) ✅ COMPLETE
│   ├── phase-e.md       # Phase E interface contract
│   └── prompt-registry.md  # Prompt registry interface contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan) ✅ EXISTS
```

### Source Code (repository root)

```text
aeon/
├── prompts/             # NEW: Prompt infrastructure module
│   ├── __init__.py
│   └── registry.py      # Prompt registry with contracts (single file for <100 prompts)
├── orchestration/
│   └── phases.py        # EXISTING: Enhanced with Phase E implementation
├── kernel/              # EXISTING: Prompt imports removed, Phase E wiring (minimal)
│   ├── executor.py      # Remove inline prompt imports
│   └── orchestrator.py  # Remove inline prompt imports
├── supervisor/
│   └── repair.py        # Remove inline prompts, use registry
├── plan/
│   ├── prompts.py       # Remove inline prompts, use registry
│   └── recursive.py     # Remove inline prompts, use registry
├── validation/
│   └── semantic.py      # Remove inline prompts, use registry
├── convergence/
│   └── engine.py        # Remove inline prompts, use registry
├── adaptive/
│   └── heuristics.py    # Remove inline prompts, use registry
└── cli/
    └── main.py          # EXISTING: Enhanced with FinalAnswer display

tests/
├── unit/
│   └── prompts/         # NEW: Prompt infrastructure unit tests
│       ├── __init__.py
│       └── test_registry.py  # Level 1 prompt tests: model instantiation, rendering, validation, invariants
├── integration/
│   └── test_phase_e.py  # NEW: Phase E integration tests (3 scenarios: success, TTL expiration, incomplete data)
└── [existing test structure preserved]
```

**Structure Decision**: Single Python package structure. New `aeon/prompts/` module for prompt infrastructure. Phase E in existing `aeon/orchestration/phases.py`. All prompt extraction from existing modules. No new top-level directories required. Tests mirror source structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All changes are justified and within constitutional bounds:
- Prompt registry is outside kernel (new top-level module)
- Phase E is outside kernel (in orchestration module)
- Kernel changes are minimal (prompt import removal only)
- Phase E wiring (~20 LOC) is in OrchestrationEngine, not kernel proper
- All interactions through clean interfaces (PromptRegistry, LLMAdapter)

## Phase 0: Research & Technical Decisions ✅ COMPLETE

**Status**: All research decisions resolved. See `research.md` for details.

**Key Decisions**:
1. ✅ Pydantic v2 API surface (codebase already uses >=2.0.0)
2. ✅ F-string rendering for prompt templates (simple, native Python)
3. ✅ Single-file registry for <100 prompts (current scale: ~20-30)
4. ✅ Phase E at C-loop exit point (after `_execute_phase_c_loop` returns)
5. ✅ Complete prompt extraction from identified modules
6. ✅ Optional output models for JSON-producing prompts only
7. ✅ System/user prompt pattern for Phase E synthesis
8. ✅ Minimal kernel changes (prompt removal + Phase E wiring only)
9. ✅ No versioning in Sprint 7 (contracts mutable, acceptable for <100 prompts)
10. ✅ Level 1 prompt tests + Phase E integration tests (3 scenarios only)

**Research Output**: `research.md` ✅

## Phase 1: Design & Contracts ✅ COMPLETE

**Status**: All design artifacts generated. See `data-model.md`, `contracts/`, and `quickstart.md` for details.

### Data Model

**Output**: `data-model.md` ✅

**Key Entities Defined**:
- PromptRegistry: Central repository with Dict[PromptId, PromptDefinition]
- PromptId: Enumeration of all prompt identifiers (~23 prompts)
- PromptDefinition: Contains template, input model (required), output model (optional), render function
- PromptInput: Base class for all prompt input models (Pydantic BaseModel)
- PromptOutput: Base class for prompt output models (Pydantic BaseModel, optional)
- PhaseEInput: Input model for Phase E with required/optional fields explicitly defined
- FinalAnswer: Output model for Phase E with answer_text (required), optional fields, and metadata

### Interface Contracts

**Output**: `contracts/` ✅

**Contracts Defined**:
1. **`contracts/prompt-registry.md`**: PromptRegistry interface with `get_prompt(prompt_id, input_data) -> str`
2. **`contracts/phase-e.md`**: Phase E interface with `execute_phase_e(phase_e_input, llm_adapter, prompt_registry) -> FinalAnswer`

**Contract Details**:
- PromptRegistry: Type-safe prompt retrieval with input validation and rendering
- PhaseEInput: Pydantic model with required fields (request, correlation_id, execution_start_timestamp, convergence_status, total_passes, total_refinements, ttl_remaining) and optional fields (plan_state, execution_results, convergence_assessment, execution_passes, semantic_validation, task_profile)
- FinalAnswer: Pydantic model with required answer_text and metadata, optional confidence, used_step_ids, notes, ttl_exhausted

### Quickstart Guide

**Output**: `quickstart.md` ✅

**Quickstart Contents**:
- Overview of prompt registry usage
- Phase E synthesis examples
- Test scenarios for User Story 3 (successful synthesis, TTL expiration, incomplete data)

## Phase 2: Implementation Planning

**Status**: Ready for task breakdown via `/speckit.tasks` command.

**Implementation Phases** (from spec dependencies):
1. **Phase 1 (P1)**: Prompt Consolidation & Registry
   - Extract all prompts from identified modules
   - Create prompt registry with PromptId enum
   - Remove inline prompts from all modules
   - Wire registry lookups

2. **Phase 2 (P2)**: Schema-Backed Prompt Contracts
   - Create input models for all prompts
   - Create output models for JSON-producing prompts
   - Implement validation before/after LLM calls
   - Enforce invariants (Location, Schema, Registration)

3. **Phase 3 (P3)**: Phase E Answer Synthesis
   - Implement Phase E in `aeon/orchestration/phases.py`
   - Create PhaseEInput and FinalAnswer models
   - Create synthesis prompts (ANSWER_SYNTHESIS_SYSTEM, ANSWER_SYNTHESIS_USER)
   - Wire Phase E invocation at C-loop exit
   - Implement degraded answer handling
   - Update CLI to display FinalAnswer

**Next Steps**: Run `/speckit.tasks` to generate detailed task breakdown from this plan.
