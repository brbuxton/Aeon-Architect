# Implementation Plan: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Branch**: `007-prompt-infrastructure` | **Date**: 2025-01-27 | **Spec**: `/specs/007-prompt-infrastructure/spec.md`
**Input**: Feature specification from `/specs/007-prompt-infrastructure/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Establish a unified, contract-driven prompt subsystem by consolidating all inline prompts into a centralized registry (`aeon/prompts/registry.py`) with schema-backed Pydantic contracts for input/output validation. Implement Phase E (Answer Synthesis) to complete the A→B→C→D→E reasoning loop, integrating synthesis at the C-loop exit point in `OrchestrationEngine.run_multipass()`. This sprint eliminates all inline prompts, enforces schema-backed prompt contracts, and introduces minimal answer synthesis that integrates correctly with Aeon's actual execution flow.

## Technical Context

**Language/Version**: Python 3.x (existing codebase)  
**Primary Dependencies**: Pydantic >= 2.0.0 (existing), existing ModelClient/LLMAdapter abstraction (no modifications needed)  
**Storage**: N/A (in-memory prompt registry, no persistence required)  
**Testing**: pytest (existing test infrastructure)  
**Target Platform**: Linux (existing platform)
**Project Type**: Single Python project (existing structure)  
**Performance Goals**: Minimal overhead - prompt registry lookups should be O(1), prompt rendering should not add significant latency to LLM calls  
**Constraints**: Kernel LOC must remain under 800 (Constitution Principle I), no domain logic in kernel, prompt registry must be outside kernel (Constitution Principle II), <100 prompts expected in registry (single-file registry acceptable)  
**Scale/Scope**: ~20-30 prompts to be extracted from existing codebase (kernel, supervisor, phases, tools, validation, convergence, adaptive modules), single-file registry implementation sufficient for current scale

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Minimal kernel changes required - only removal of inline prompt imports and Phase E invocation wiring (~10-20 LOC). Prompt registry and Phase E module are outside kernel. Justification: Phase E must be invoked at C-loop exit point in `run_multipass()`, which is kernel orchestration logic (not domain logic). Prompt removal is refactoring, not new functionality.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: YES - prompt removal reduces kernel LOC, Phase E wiring is minimal (~10-20 LOC net change)
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: NO - Phase E synthesis logic resides in `aeon/orchestration/phases.py` (outside kernel), kernel only invokes it

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: YES - Prompt registry is new module `aeon/prompts/registry.py` (outside kernel), Phase E is in orchestration module (outside kernel)
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: YES - Prompt registry provides `get_prompt(prompt_id, input_data)` interface, Phase E provides `execute_phase_e(phase_e_input)` interface
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: NO - Prompt registry and Phase E are stateless modules that receive data via function parameters

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: N/A - No changes to plan structure
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: NO - No procedural logic added to plans

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: PARTIALLY - Minimal kernel mutation required for Phase E invocation (~10-20 LOC), but prompt registry and Phase E are external modules
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: YES - Kernel changes are minimal, deliberate (required for Phase E integration), and will be documented in code comments

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: NO - This feature is beyond Sprint 1 scope, but constitution allows features beyond Sprint 1. This is acceptable as it's a foundational infrastructure improvement.

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
├── prompts/                    # NEW: Prompt infrastructure module
│   ├── __init__.py
│   └── registry.py             # Prompt registry with contracts
├── orchestration/
│   ├── phases.py               # MODIFY: Add Phase E synthesis method
│   └── engine.py               # MODIFY: Wire Phase E invocation at C-loop exit
├── kernel/
│   ├── orchestrator.py         # MODIFY: Remove inline prompt imports
│   └── executor.py             # MODIFY: Remove inline prompt imports
├── plan/
│   └── prompts.py              # MODIFY: Remove prompt definitions, use registry
├── validation/
│   └── semantic.py             # MODIFY: Remove inline prompts, use registry
├── convergence/
│   └── engine.py               # MODIFY: Remove inline prompts, use registry
├── adaptive/
│   └── heuristics.py           # MODIFY: Remove inline prompts, use registry
└── supervisor/
    └── repair.py               # MODIFY: Remove inline prompts, use registry

tests/
├── unit/
│   └── prompts/                # NEW: Prompt registry tests
│       ├── __init__.py
│       └── test_registry.py
└── integration/
    └── test_phase_e.py         # NEW: Phase E integration tests
```
- The `aeon/plan/` package contains the system’s planning logic. This includes 
  both high-level plan prompt templates (in plan/prompts.py) and recursive 
  planning behavior (in plan/recursive.py).
- The recursive planning module defines domain-specific prompts for 
  subplan generation and plan refinement. These prompts must be centralized 
  into the prompt registry during Sprint 7.
- Aeon does NOT define a generic or free-floating “reasoning prompt” 
  category. All reasoning-related prompting is tied to specific domains such as 
  execution reasoning (kernel/executor.py) or recursive planning (plan/recursive.py).

**Structure Decision**: Single Python project structure (existing). New `aeon/prompts/` module added for prompt infrastructure. Phase E synthesis logic added to existing `aeon/orchestration/phases.py`. All prompt extraction and Phase E integration modifies existing modules without changing project structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. All Constitution Check gates pass.

## Phase Completion Status

### Phase 0: Outline & Research ✅
- **Status**: Complete
- **Output**: `research.md` generated with all technical decisions documented
- **Clarifications Resolved**: All technical decisions resolved (Pydantic compatibility, rendering mechanism, registry organization, Phase E integration, extraction strategy, etc.)

### Phase 1: Design & Contracts ✅
- **Status**: Complete
- **Outputs Generated**:
  - `data-model.md`: Complete data model with all entities (PromptRegistry, PromptId, PromptDefinition, PromptInput, PromptOutput, PhaseEInput, FinalAnswer)
  - `contracts/prompt-registry.md`: Prompt registry interface contract
  - `contracts/phase-e.md`: Phase E interface contract
  - `quickstart.md`: Test scenarios and usage examples
- **Agent Context**: Updated via `update-agent-context.sh cursor-agent`

### Constitution Check Re-evaluation ✅
- **Status**: Re-evaluated post-design
- **Result**: All gates pass. Design maintains kernel minimalism, separation of concerns, and extensibility principles.
- **Kernel Impact**: Minimal (~10-20 LOC for Phase E wiring, prompt removal reduces LOC)
- **External Modules**: Prompt registry and Phase E are outside kernel per Constitution requirements

## Next Steps

1. **Phase 2**: Run `/speckit.tasks` to generate task breakdown
2. **Implementation**: Follow tasks.md to implement prompt infrastructure and Phase E
3. **Testing**: Execute test scenarios from quickstart.md
4. **Validation**: Run invariant tests to ensure compliance
