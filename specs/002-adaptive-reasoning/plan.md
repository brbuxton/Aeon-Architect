# Implementation Plan: Sprint 2 - Adaptive Reasoning Engine

**Branch**: `002-adaptive-reasoning` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-adaptive-reasoning/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Sprint 2 transforms Aeon from a deterministic single-pass orchestrator into a recursive, adaptive, semantically-aware intelligent reasoning engine with five Tier-1 capabilities: Multi-Pass Execution Loop, Recursive Planning & Re-Planning, Convergence Engine, Adaptive Depth Heuristics, and Semantic Validation Layer.

**Prerequisite**: Before Sprint 2 implementation begins, a mandatory kernel refactoring must be completed to reduce combined LOC of `orchestrator.py` and `executor.py` from 786 to below 700 LOC.

## Mandatory Kernel Refactoring Phase (Prerequisite)

**Status**: Required before any Sprint 2 User Stories implementation  
**Current LOC**: 786 lines (522 orchestrator.py + 264 executor.py)  
**Target LOC**: <700 lines (combined)  
**Constitutional Limit**: 800 LOC (providing 100+ LOC headroom)

### Refactoring Objectives

1. **LOC Reduction**: Measure and reduce combined LOC of `orchestrator.py` and `executor.py` to below 700 LOC
2. **Structural Refactoring Only**: No behavior changes, no interface changes - pure structural reorganization
3. **Logic Extraction**: Move non-orchestration logic to appropriate external modules
4. **Behavioral Preservation**: Maintain 100% Sprint 1 behavioral compatibility

### Refactoring Constraints

- **Structural-Only**: Refactoring MUST be structural only — no behavior changes, no interface changes
- **Logic Extraction**: Any non-orchestration logic found in `orchestrator.py` or `executor.py` MUST be moved into appropriate external modules
- **Supporting Modules**: Supporting kernel modules (e.g., `state.py`) may contain only pure data structures and simple containers, and may NOT be used to circumvent kernel LOC limits
- **Regression Testing**: All existing Sprint 1 tests MUST pass without modification after refactoring
- **No Behavioral Drift**: Sprint 1 behavior MUST remain identical - verified through comprehensive regression test suite

### Refactoring Approach

1. **Analysis Phase**:
   - Audit `orchestrator.py` and `executor.py` to identify non-orchestration logic
   - Identify extractable functions, classes, or modules that can be moved externally
   - Measure current LOC and identify reduction targets

2. **Extraction Phase**:
   - Move non-orchestration logic to appropriate external modules (tools, supervisors, utilities)
   - Ensure extracted code maintains clean interfaces
   - Preserve all existing functionality and interfaces

3. **Validation Phase**:
   - Run full regression test suite to confirm no behavioral changes
   - Verify LOC is below 700 (combined)
   - Confirm all interfaces remain unchanged
   - Document refactoring changes

### Success Criteria

- [ ] Combined LOC of `orchestrator.py` and `executor.py` is below 700 lines
- [ ] All Sprint 1 regression tests pass without modification
- [ ] No interface changes (all existing code using kernel continues to work)
- [ ] No behavioral changes (execution results identical to Sprint 1)
- [ ] Refactoring documented with before/after LOC measurements

### Blocking Condition

**This refactoring MUST be completed and validated before any Sprint 2 functional requirements are implemented.**

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12  
**Primary Dependencies**: pydantic >= 2.0.0, jsonschema >= 4.0.0, requests >= 2.31.0, pyyaml >= 6.0.0
**Storage**: File storage: JSONL logs and YAML config files and In-memory storage: InMemoryKVStore (not persistent)
**Testing**: pytest
**Target Platform**: Linux x86_64 (Ubuntu 22.04 or later)
**Project Type**: simple CLI wrapper over a scalable backend for future web and mobile frontends
**Performance Goals**: 95% of tasks whose initial TaskProfile indicates high reasoning_depth or low information_sufficiency completed within 5 minutes, average passes per task <= 5, convergence engine evaluation completing within 250ms
**Constraints**: 800 line Kernel LOC limit, no domain logic in the Kernel, all semantic, planning, refinement and convergence logic MUST live in external modules.
**Scale/Scope**: single-node local execution, 1-5 tasks per request expected, combined input/output of 2k-8k tokens is typical task size.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Prerequisite**: Mandatory kernel refactoring (Phase -1) must be completed first to bring kernel LOC below 700 before Sprint 2 implementation begins.

**Kernel Minimalism (Principle I)**: 
- [ ] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
- [ ] Will kernel LOC remain under 800 after this feature? (Prerequisite: Must be <700 after refactoring)
- [ ] Does this feature add domain logic to the kernel? (MUST be NO)

**Separation of Concerns (Principle II)**:
- [ ] Are new capabilities implemented as tools/supervisors, not kernel changes?
- [ ] Do new modules interact through clean interfaces only?
- [ ] Are kernel internals accessed by external modules? (MUST be NO)

**Declarative Plans (Principle III)**:
- [ ] If this feature affects plans, are they JSON/YAML declarative structures?
- [ ] Is any procedural logic added to plans? (MUST be NO)

**Extensibility (Principle IX)**:
- [ ] Can this feature be added without kernel mutation?
- [ ] If kernel changes are required, are they rare, deliberate, and documented?

**Sprint 1 Scope (Principle X)**:
- [ ] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)

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
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Implementation Phases

### Phase -1: Mandatory Kernel Refactoring (PREREQUISITE)

**Status**: Blocking - Must be completed before any Sprint 2 work begins

- Measure current LOC (orchestrator.py + executor.py)
- Identify and extract non-orchestration logic to external modules
- Reduce combined LOC to below 700 lines
- Validate no behavioral changes through regression testing
- Document refactoring changes

**Deliverables**:
- Refactored kernel with LOC < 700
- Regression test results confirming no behavioral drift
- Refactoring documentation

### Phase 0: Research & Design

**Prerequisites**: Phase -1 complete, kernel LOC < 700

- Research multi-pass execution patterns
- Research recursive planning approaches
- Research convergence detection algorithms
- Design semantic validation architecture
- Design adaptive depth heuristics

**Deliverables**: `research.md`

### Phase 1: Design & Contracts

**Prerequisites**: Phase 0 complete

- Define data models for execution passes, convergence assessments, etc.
- Generate API contracts for new interfaces
- Create quickstart documentation
- Update agent context

**Deliverables**: `data-model.md`, `contracts/`, `quickstart.md`

### Phase 2: Implementation Tasks

**Prerequisites**: Phase 1 complete

- Break down implementation into specific tasks
- Define task dependencies and sequencing

**Deliverables**: `tasks.md` (created by `/speckit.tasks` command)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
