# Implementation Plan: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Branch**: `004-kernel-refactor` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-kernel-refactor/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements a structural refactoring of the Aeon kernel to restore constitutional compliance by reducing kernel LOC from 1351 lines (1092 in orchestrator.py + 259 in executor.py) to ≤800 lines (target <750). The refactoring extracts all phase orchestration logic, plan transformation logic, heuristic decision logic, and TTL/expiration decision logic from the kernel to external modules in the `aeon/orchestration/` namespace, while preserving all existing functionality and maintaining backward compatibility.

**Technical Approach**: Extract strategy-level orchestration logic (phase logic, refinement heuristics, plan operations, TTL strategies) to new `aeon/orchestration/` modules while keeping core coordination responsibilities (LLM loop execution, plan creation/updates, state transitions, scheduling, tool invocation, TTL/token countdown, supervisor routing) in the kernel. All extracted logic interacts with the kernel through well-defined interface contracts.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0, jsonschema>=4.0.0, requests>=2.31.0, pyyaml>=6.0.0  
**Storage**: Memory subsystem (in-memory ExecutionHistory, via K/V interface for state)  
**Testing**: pytest with coverage, contract tests for interfaces, integration tests for multi-pass execution  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Maintain current performance levels (no degradation allowed)  
**Constraints**: Kernel <800 LOC (current: 1351 LOC, target: <750 LOC), deterministic phase transitions, no domain logic in kernel, all extracted logic via interfaces  
**Scale/Scope**: Kernel refactoring only - extract ~550+ LOC to external modules while preserving all functionality

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: No, this feature REMOVES code from the kernel. The refactoring extracts ~550+ LOC from the kernel to external modules, reducing kernel LOC from 1351 to ≤800 (target <750). This restores constitutional compliance.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Current kernel: 1351 LOC. Target after refactoring: <750 LOC. This refactoring explicitly reduces kernel LOC to restore compliance.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. This refactoring REMOVES domain logic from the kernel. All phase orchestration logic, plan transformation logic, heuristic decision logic, and TTL/expiration decision logic will be extracted to external modules. The kernel will contain only thin coordination logic.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: N/A - this is a refactoring, not a new capability. Extracted logic is moved to orchestration modules, not tools/supervisors, because it is orchestration strategy logic that coordinates execution phases.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. All extracted orchestration modules will define interfaces (PhaseOrchestrator, PlanRefinement, TTLStrategy) that kernel invokes. No direct access to kernel internals.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. Extracted orchestration modules receive plan/state snapshots through interfaces. Kernel orchestrator invokes external modules, not vice versa.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: Yes. Plans remain JSON/YAML declarative structures. Refactoring does not change plan structure.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: No. Refactoring does not add procedural logic to plans. All plan modifications remain declarative.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Yes. This refactoring extracts logic FROM the kernel, reducing kernel size. Extracted logic is moved to external modules, enabling future enhancements without kernel changes.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. This is a deliberate structural refactoring to restore constitutional compliance, extensively documented in spec.md and this plan. Kernel changes are structural (extraction of logic) not functional (no behavioral changes).

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes - this is a structural refactoring within Sprint 1 scope. It does not add new features, only reorganizes existing code to restore constitutional compliance.

## Project Structure

### Documentation (this feature)

```text
specs/004-kernel-refactor/
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
├── kernel/              # Core orchestrator (orchestrator.py, executor.py) - <800 LOC
│   ├── orchestrator.py  # Thin coordination logic only (target: ~400-500 LOC)
│   ├── executor.py      # Step execution routing (target: ~200-250 LOC)
│   └── state.py         # OrchestrationState (data structures only)
├── orchestration/       # NEW: Extracted orchestration strategy modules
│   ├── __init__.py
│   ├── phases.py        # Phase A/B/C/D orchestration logic
│   ├── refinement.py    # Plan refinement action application
│   ├── ttl.py           # TTL expiration response generation
│   └── step_prep.py     # Step preparation and context population
├── plan/                # Existing: Plan engine (unchanged)
├── validation/          # Existing: Schema validation (unchanged)
├── supervisor/          # Existing: Supervisor repair (unchanged)
├── tools/               # Existing: Tool registry and invocation (unchanged)
├── memory/              # Existing: Memory interface (unchanged)
├── llm/                 # Existing: LLM adapter interface (unchanged)
└── observability/       # Existing: Logging and observability (unchanged)

tests/
├── contract/            # Interface contract tests
├── integration/         # Multi-pass execution tests (verify no behavioral changes)
└── unit/                # Unit tests for all modules
    ├── orchestration/   # NEW: Orchestration module tests
    └── kernel/          # Existing: Kernel tests (verify no behavioral changes)
```

**Structure Decision**: Create new `aeon/orchestration/` namespace for extracted orchestration strategy logic. Kernel remains minimal with only orchestrator.py and executor.py counting toward LOC limit. All strategy-level orchestration logic is external modules that integrate through clean interfaces.

## Spec Requirements Coverage

This section confirms that all major requirements from spec.md are represented in this plan.

### ✅ Functional Requirements

**FR-001: Kernel LOC Reduction**
- Covered in: Technical Context, Project Structure
- Implementation: Extract ~550+ LOC from kernel to orchestration modules
- Spec reference: §FR-001

**FR-002: Extract Phase Orchestration Logic**
- Covered in: Project Structure (orchestration/phases.py)
- Implementation: Extract `_phase_a_taskprofile_ttl()`, `_phase_b_initial_plan_refinement()`, `_phase_c_execute_batch()`, `_phase_c_evaluate()`, `_phase_c_refine()`, `_phase_d_adaptive_depth()` to orchestration/phases.py
- Spec reference: §FR-002

**FR-003: Extract Plan Transformation Logic**
- Covered in: Project Structure (orchestration/refinement.py)
- Implementation: Extract `_apply_refinement_actions()` to orchestration/refinement.py
- Spec reference: §FR-003

**FR-004: Extract Heuristic Decision Logic**
- Covered in: Project Structure (orchestration/phases.py, orchestration/step_prep.py)
- Implementation: Extract step preparation logic, dependency checking, context population to orchestration modules
- Spec reference: §FR-004

**FR-005: Extract TTL/Expiration Decision Logic**
- Covered in: Project Structure (orchestration/ttl.py)
- Implementation: Extract `_create_ttl_expiration_response()` to orchestration/ttl.py
- Spec reference: §FR-005

**FR-006: Preserve Functionality**
- Covered in: Testing strategy, Success Criteria
- Implementation: All existing tests must pass without modification
- Spec reference: §FR-006

**FR-007-FR-008: Preserve Multi-Pass Execution Semantics**
- Covered in: Testing strategy, Integration tests
- Implementation: Integration tests verify identical multi-pass execution behavior
- Spec reference: §FR-007, FR-008

**FR-009-FR-011: Interface Contracts**
- Covered in: contracts/interfaces.md (Phase 1 output)
- Implementation: Define PhaseOrchestrator, PlanRefinement, TTLStrategy interfaces
- Spec reference: §FR-009, FR-009a, FR-010, FR-011

**FR-012: Kernel Thin Coordination**
- Covered in: Project Structure, Technical Context
- Implementation: Kernel contains only core coordination responsibilities after refactoring
- Spec reference: §FR-012

**FR-013-FR-016: Documentation**
- Covered in: Generated Artifacts section
- Implementation: Document all extracted logic, interfaces, LOC measurements
- Spec reference: §FR-013, FR-014, FR-015, FR-016

### ✅ Out of Scope (Kernel Responsibilities)

All kernel responsibilities that MUST remain in kernel are preserved:
- LLM loop execution coordination ✅
- Plan creation and plan updates (calling external modules) ✅
- State transitions (managing state object lifecycle) ✅
- Scheduling (determining execution order and sequencing) ✅
- Tool invocation (calling tool registry interfaces) ✅
- TTL/token countdown (tracking and decrementing TTL) ✅
- Supervisor routing (calling supervisor interfaces) ✅

### ✅ Success Criteria

All success criteria from spec.md §Success Criteria are addressed:
- SC-001: Kernel LOC ≤800 (target <750) ✅
- SC-002: 100% of existing tests pass ✅
- SC-003: Multi-pass execution identical behavior ✅
- SC-004: Orchestration logs match pre-refactor ✅
- SC-005: Extracted modules independently testable ✅
- SC-006: Kernel contains zero phase/heuristic logic ✅
- SC-007: All interfaces documented ✅
- SC-008: Before/after LOC documented ✅
- SC-009: Unit tests for extracted logic ✅
- SC-010: Kernel behavior matches pre-refactor ✅
- SC-011: Performance maintained ✅

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All constitutional constraints satisfied. This refactoring restores compliance by reducing kernel LOC.

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Output**: `research.md`

- ✅ Extracted technical decisions from feature spec
- ✅ Documented implementation patterns and best practices
- ✅ Resolved all technical questions (no "NEEDS CLARIFICATION" items)
- ✅ Consolidated research findings with rationale and alternatives

**Key Decisions Documented**:
1. Orchestration module structure (phases.py, refinement.py, step_prep.py, ttl.py)
2. Interface contract design (structured results, state snapshots)
3. Kernel state access pattern (no direct access, snapshot parameters)
4. Plan refinement action application (extracted to refinement.py)
5. Step preparation logic extraction (extracted to step_prep.py)
6. TTL expiration response generation (extracted to ttl.py)
7. Kernel coordination responsibilities (retained in kernel)
8. Testing strategy (comprehensive test suite)
9. LOC measurement and documentation (before/after breakdown)
10. Performance preservation (no degradation allowed)

### Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**: `data-model.md`, `contracts/interfaces.md`, `quickstart.md`

- ✅ Generated data-model.md with orchestration module entities
  - Defined PhaseResult, RefinementResult, StepPreparationResult, TTLExpirationResult
  - Defined interface parameter types for all orchestration modules
  - Documented relationships and validation rules
- ✅ Generated contracts/interfaces.md with interface definitions
  - PhaseOrchestrator interface (phase_a/b/c/d methods)
  - PlanRefinement interface (apply_actions method)
  - StepPreparation interface (get_ready_steps, populate_incoming_context, populate_step_indices)
  - TTLStrategy interface (create_expiration_response)
- ✅ Generated quickstart.md with refactoring examples
  - Before/after code examples
  - Usage patterns and testing examples
  - Migration guide and key patterns

### Phase 2: Task Breakdown

**Status**: Pending (to be generated by `/speckit.tasks` command)

**Next Steps**:
1. Run `/speckit.tasks` command to generate `tasks.md`
2. Break down refactoring into specific, actionable tasks
3. Organize tasks by module and priority

## Generated Artifacts

### Documentation
- ✅ `plan.md` - This implementation plan
- ✅ `research.md` - Technical decisions and research findings
- ✅ `data-model.md` - Entity schemas and relationships
- ✅ `contracts/interfaces.md` - Interface contracts for orchestration modules
- ✅ `quickstart.md` - Refactoring guide and examples

## LOC Measurements

### Before Refactoring (Baseline)

**Kernel LOC (Baseline)**:
- `orchestrator.py`: 1092 LOC
- `executor.py`: 259 LOC
- **Total Kernel LOC**: 1351 LOC
- **Constitutional Limit**: 800 LOC
- **Status**: ❌ **VIOLATION** (exceeds limit by 551 LOC)

### After Refactoring (Final)

**Kernel LOC (Final)**:
- `orchestrator.py`: 453 LOC (reduced by 639 LOC, 58.5% reduction)
- `executor.py`: 182 LOC (reduced by 77 LOC, 29.7% reduction)
- **Total Kernel LOC**: 635 LOC (orchestrator.py + executor.py only)
- **Constitutional Limit**: 800 LOC
- **Target**: <750 LOC
- **Status**: ✅ **COMPLIANT** (under limit by 165 LOC, under target by 115 LOC)

**LOC Reduction Summary**:
- **Total Reduction**: 716 LOC (from 1351 to 635)
- **Reduction Percentage**: 53.0%
- **Compliance Margin**: 165 LOC under limit (20.6% margin)
- **Target Margin**: 115 LOC under target (15.3% margin)

### Extracted Logic LOC Distribution

**Orchestration Modules (New)**:
- `orchestration/phases.py`: ~537 LOC (Phase A/B/C/D orchestration logic)
- `orchestration/refinement.py`: ~100 LOC (Plan refinement action application)
- `orchestration/step_prep.py`: ~137 LOC (Step preparation and dependency checking)
- `orchestration/ttl.py`: ~106 LOC (TTL expiration response generation)
- **Total Extracted LOC**: ~880 LOC (moved from kernel to orchestration modules)

**Note**: The extracted LOC (880) is greater than the kernel reduction (716) because:
1. Some code was refactored and improved during extraction
2. Interface contracts and error handling were added
3. Structured result types were introduced

### Method-Level LOC Breakdown

**Extracted from orchestrator.py**:
- `_phase_a_taskprofile_ttl()` → `PhaseOrchestrator.phase_a_taskprofile_ttl()`: ~30 LOC
- `_phase_b_initial_plan_refinement()` → `PhaseOrchestrator.phase_b_initial_plan_refinement()`: ~45 LOC
- `_phase_c_execute_batch()` → `PhaseOrchestrator.phase_c_execute_batch()`: ~120 LOC
- `_phase_c_evaluate()` → `PhaseOrchestrator.phase_c_evaluate()`: ~150 LOC
- `_phase_c_refine()` → `PhaseOrchestrator.phase_c_refine()`: ~80 LOC
- `_phase_d_adaptive_depth()` → `PhaseOrchestrator.phase_d_adaptive_depth()`: ~112 LOC
- `_apply_refinement_actions()` → `PlanRefinement.apply_actions()`: ~50 LOC
- `_get_ready_steps()` → `StepPreparation.get_ready_steps()`: ~45 LOC
- `_populate_incoming_context()` → `StepPreparation.populate_incoming_context()`: ~50 LOC
- `_populate_step_indices()` → `StepPreparation.populate_step_indices()`: ~15 LOC
- `_create_ttl_expiration_response()` → `TTLStrategy.create_expiration_response()`: ~60 LOC
- **Total Extracted Methods**: ~717 LOC (approximate, from original kernel methods)

## Branch and Paths

**Branch**: `004-kernel-refactor`  
**Implementation Plan**: `/home/brian/projects/Aeon-Architect/specs/004-kernel-refactor/plan.md`  
**Feature Spec**: `/home/brian/projects/Aeon-Architect/specs/004-kernel-refactor/spec.md`  
**Specs Directory**: `/home/brian/projects/Aeon-Architect/specs/004-kernel-refactor/`

