# Implementation Plan: Sprint 2 - Adaptive Reasoning Engine

**Branch**: `002-adaptive-reasoning` | **Date**: 2025-12-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-adaptive-reasoning/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements five Tier-1 capabilities to evolve Aeon from a deterministic single-pass orchestrator into a recursive, adaptive, semantically-aware intelligent reasoning engine: Multi-Pass Execution Loop, Recursive Planning & Re-Planning, Convergence Engine, Adaptive Depth Heuristics, and Semantic Validation Layer. The implementation extends the existing Aeon Core orchestration kernel with modular components that integrate through clean interfaces, preserving kernel minimalism (<800 LOC) while adding sophisticated reasoning capabilities.

**Technical Approach**: Implement all Tier-1 features as external modules (convergence/, adaptive/, validation/) that integrate with the kernel through well-defined interfaces. The kernel orchestrator will coordinate multi-pass execution, but semantic reasoning, convergence assessment, and adaptive depth decisions will be handled by external modules using LLM-based reasoning. Plans remain declarative JSON/YAML structures, and all new capabilities respect constitutional constraints.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0, jsonschema>=4.0.0, requests>=2.31.0, pyyaml>=6.0.0  
**Storage**: Memory subsystem (in-memory ExecutionHistory for Sprint 2, via K/V interface for state)  
**Testing**: pytest with coverage, contract tests for interfaces, integration tests for multi-pass execution  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Multi-pass execution converges within 5 minutes for 90% of complex tasks, convergence detection accuracy 90%, semantic validation detects 90% of issues  
**Constraints**: Kernel <800 LOC (current: 561 LOC), deterministic phase transitions, no domain logic in kernel, all semantic judgments via LLM-based reasoning  
**Scale/Scope**: Sprint 2 - adaptive reasoning engine with 5 Tier-1 capabilities, modular architecture, in-memory execution history

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, minimal kernel changes required for multi-pass loop coordination. The orchestrator must manage pass sequencing, phase transitions, and TTL checks. This is core orchestration logic (deterministic control flow), not domain logic. Multi-pass coordination is fundamental orchestration responsibility, similar to single-pass execution in Sprint 1. Estimated addition: ~100-150 LOC for pass management, phase sequencing, and TTL boundary checks. All semantic reasoning (convergence, validation, adaptive depth) is external.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Current kernel: 561 LOC. Estimated addition: ~100-150 LOC. Total: ~661-711 LOC, well under 800 LOC limit. Kernel refactoring requirement (spec §Mandatory Kernel Refactoring Requirement) ensures LOC remains compliant.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Kernel only handles deterministic phase sequencing (plan → execute → evaluate → refine → re-execute), TTL boundary checks, and pass coordination. All semantic judgments (convergence, validation, adaptive depth, recursive planning) are in external modules using LLM-based reasoning.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Convergence engine (convergence/), adaptive depth heuristics (adaptive/), semantic validation layer (validation/), and recursive planner (plan/) are all external modules. Kernel only coordinates execution flow.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. All new modules define interfaces (ConvergenceEngine, AdaptiveDepth, SemanticValidator, RecursivePlanner) that kernel invokes. No direct access to kernel internals.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. External modules receive plan/state snapshots through interfaces. Kernel orchestrator invokes external modules, not vice versa.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: Yes. Plans remain JSON/YAML declarative structures. New fields (step_index, total_steps, incoming_context, handoff_to_next, clarity_state) are declarative metadata, not procedural logic.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: No. All plan modifications are declarative (ADD/MODIFY/REMOVE operations on step structures). RefinementActions are declarative change descriptions.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: No, but kernel changes are minimal and justified. Multi-pass loop coordination requires kernel changes for phase sequencing and TTL management. This is core orchestration capability, similar to single-pass execution. Changes are limited to orchestrator pass management logic.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. This is a deliberate extension of core orchestration capability, extensively documented in spec.md and this plan. Kernel changes are structural (pass coordination) not functional (semantic reasoning).

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: No - this is Sprint 2 scope. Sprint 2 explicitly extends Sprint 1 with adaptive reasoning capabilities. Multi-pass execution, recursive planning, convergence detection, adaptive depth, and semantic validation are Sprint 2 Tier-1 features, not Sprint 1 scope.

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
├── kernel/              # Core orchestrator (orchestrator.py, executor.py) - <800 LOC
│   ├── orchestrator.py  # Multi-pass loop coordination, phase sequencing
│   ├── executor.py      # Step execution, batch processing
│   └── state.py         # OrchestrationState (data structures only)
├── convergence/         # NEW: Convergence engine module
│   └── engine.py        # ConvergenceAssessment, completeness/coherence/consistency checks
├── adaptive/            # NEW: Adaptive depth heuristics module
│   └── heuristics.py    # TaskProfile inference, TTL allocation, reasoning depth
├── plan/                # Existing: Plan engine (extended for recursive planning)
│   ├── executor.py      # Plan execution
│   ├── models.py        # Plan, PlanStep (extended with new fields)
│   ├── parser.py        # Plan parsing
│   ├── prompts.py       # Plan generation prompts
│   ├── validator.py     # Plan validation
│   └── recursive.py     # NEW: Recursive planner for refinement
├── validation/          # Existing: Schema validation (extended for semantic validation)
│   ├── schema.py        # Structural validation
│   └── semantic.py      # NEW: Semantic validation layer
├── supervisor/          # Existing: Supervisor repair (uses repair_json from Sprint 1)
├── tools/               # Existing: Tool registry and invocation
├── memory/              # Existing: Memory interface (K/V store)
├── llm/                 # Existing: LLM adapter interface
└── observability/       # Existing: Logging and observability

tests/
├── contract/            # Interface contract tests
├── integration/        # Multi-pass execution, convergence, refinement tests
└── unit/                # Unit tests for all modules
    ├── convergence/     # NEW: Convergence engine tests
    ├── adaptive/        # NEW: Adaptive depth tests
    └── validation/      # Extended: Semantic validation tests
```

**Structure Decision**: Single Python package structure (Option 1). All Sprint 2 features are implemented as new modules (convergence/, adaptive/) or extensions to existing modules (plan/recursive.py, validation/semantic.py). Kernel remains minimal with only orchestrator.py and executor.py counting toward LOC limit. All semantic reasoning capabilities are external modules that integrate through clean interfaces.

## Mandatory Kernel Refactoring Requirement

**PREREQUISITE**: This refactoring MUST be completed before any Sprint 2 User Stories implementation begins.

### Refactoring Scope

Before implementing Sprint 2 functional requirements, the kernel codebase MUST undergo mandatory structural refactoring to ensure compliance with constitutional LOC limits and maintain architectural purity.

### Refactoring Constraints

1. **LOC Measurement and Reduction**: 
   - Measure combined LOC of `orchestrator.py` and `executor.py`
   - If >700 LOC, reduce to <700 LOC to ensure headroom under 800 LOC constitutional limit
   - Current: 561 LOC (orchestrator.py: 325, executor.py: 236)
   - Target: <700 LOC after refactoring

2. **Structural-Only Refactoring**:
   - MUST be structural only — no behavior changes, no interface changes
   - All existing functionality must remain identical in behavior and external interface
   - Extract non-orchestration logic to external modules
   - Supporting kernel modules may contain only pure data structures and simple containers
   - MUST NOT use supporting modules to circumvent kernel LOC limits

3. **Logic Extraction**:
   - Any non-orchestration logic in `orchestrator.py` or `executor.py` MUST be moved to appropriate external modules
   - Preserve orchestration logic in kernel (pass sequencing, phase transitions, TTL checks)

4. **Behavioral Preservation**:
   - Sprint 1 behavior MUST remain identical after refactoring
   - All existing tests MUST pass without modification
   - Regression tests MUST confirm no behavioral drift
   - No new behavioral differences introduced

### Implementation Approach

- Analyze current kernel code for extractable logic
- Identify non-orchestration code that can be moved to external modules
- Refactor while maintaining all existing interfaces
- Run full test suite to verify behavioral preservation
- Document before/after LOC measurements

**Reference**: See spec.md §Mandatory Kernel Refactoring Requirement for complete details.

## Spec Requirements Coverage

This section confirms that all major requirements from spec.md are represented in this plan.

### ✅ CORE EXECUTION MODEL

**Phase A: TaskProfile & TTL**
- Covered in: AdaptiveDepth interface (contracts/interfaces.md), research.md Decision 6
- Implementation: `adaptive/heuristics.py` - `infer_task_profile()`, `allocate_ttl()`
- Spec reference: §Phase A: TaskProfile & TTL

**Phase B: Initial Plan & Pre-Execution Refinement**
- Covered in: RecursivePlanner interface (contracts/interfaces.md), research.md Decision 4
- Implementation: `plan/recursive.py` - `generate_plan()`, `refine_plan()`
- Spec reference: §Phase B: Initial Plan & Pre-Execution Refinement

**Phase C: Execution Passes (1..N)**
- Covered in: Orchestrator coordination (plan.md Summary), research.md Decision 1
- Implementation: `kernel/orchestrator.py` - multi-pass loop coordination
- Spec reference: §Phase C: Execution Passes (1..N)

**Phase D: Adaptive Depth Integration**
- Covered in: AdaptiveDepth interface (contracts/interfaces.md), research.md Decision 6
- Implementation: `adaptive/heuristics.py` - `update_task_profile()`
- Spec reference: §Phase D: Adaptive Depth Integration

### ✅ STEP SCHEMA AND PROMPTING

- Covered in: data-model.md (PlanStep extensions), contracts/interfaces.md (RecursivePlanner)
- New fields: step_index, total_steps, incoming_context, handoff_to_next
- Step execution prompt construction: FR-090
- Spec reference: §STEP SCHEMA AND PROMPTING

### ✅ LLM-ONLY SEMANTIC RULE

- Covered in: research.md Decision 2, contracts/interfaces.md (all interfaces)
- Master Constraint: All semantic judgments MUST be LLM-based
- Spec reference: §LLM-ONLY SEMANTIC RULE, §Master Constraint: LLM-Based Reasoning Requirement

### ✅ ORCHESTRATOR REQUIREMENTS

- Covered in: research.md Decision 1, plan.md Summary
- Phase order: EXECUTE → VALIDATE → CONVERGENCE → REFINEMENT → NEXT PASS
- Initial pass: Plan → Validate → Refine pre-execution phase
- TTL checks: Pass boundaries and safe step boundaries only
- ExecutionHistory recording: data-model.md (ExecutionPass, ExecutionHistory)
- Spec reference: §ORCHESTRATOR REQUIREMENTS

### ✅ WHAT YOU MUST NOT DO

- Covered in: research.md Decision 2, contracts/interfaces.md constraints
- No semantic heuristics: All interfaces use LLM-based reasoning
- No LLM control flow: Orchestrator controls loop, LLM emits signals only
- No full plan regeneration: Delta-style refinement only
- No duplicate JSON repair: Reuse Sprint 1 supervisor.repair_json()
- Spec reference: §WHAT YOU MUST NOT DO

### ✅ User Stories

**User Story 1 - Multi-Pass Execution with Convergence (P1)**
- Covered in: research.md Decision 1, contracts/interfaces.md (ConvergenceEngine)
- Implementation: `kernel/orchestrator.py` + `convergence/engine.py`
- Spec reference: §User Story 1

**User Story 2 - Recursive Planning and Plan Refinement (P1)**
- Covered in: research.md Decision 4, contracts/interfaces.md (RecursivePlanner)
- Implementation: `plan/recursive.py`
- Spec reference: §User Story 2

**User Story 3 - Convergence Detection and Completion Assessment (P1)**
- Covered in: contracts/interfaces.md (ConvergenceEngine), data-model.md (ConvergenceAssessment)
- Implementation: `convergence/engine.py`
- Spec reference: §User Story 3

**User Story 4 - Adaptive Reasoning Depth Based on Task Complexity (P2)**
- Covered in: contracts/interfaces.md (AdaptiveDepth), data-model.md (TaskProfile)
- Implementation: `adaptive/heuristics.py`
- Spec reference: §User Story 4

**User Story 5 - Semantic Validation of Plans and Execution Artifacts (P1)**
- Covered in: contracts/interfaces.md (SemanticValidator), data-model.md (SemanticValidationReport)
- Implementation: `validation/semantic.py`
- Spec reference: §User Story 5

**User Story 6 - Inspect Multi-Pass Execution (P2)**
- Covered in: data-model.md (ExecutionHistory), quickstart.md (inspection examples)
- Implementation: ExecutionHistory returned as part of execution result
- Spec reference: §User Story 6

### ✅ Functional Requirements Coverage

**Multi-Pass Execution Loop (FR-001, FR-084-FR-095)**
- Covered in: research.md Decision 1, contracts/interfaces.md, data-model.md
- All FRs represented in implementation approach

**Recursive Planning & Re-Planning (FR-009-FR-016, FR-065-FR-066, FR-069-FR-070, FR-083)**
- Covered in: contracts/interfaces.md (RecursivePlanner), research.md Decision 4
- All FRs represented in interface design

**Convergence Engine (FR-017-FR-025, FR-068)**
- Covered in: contracts/interfaces.md (ConvergenceEngine), data-model.md (ConvergenceAssessment)
- All FRs represented in interface design

**Adaptive Depth Heuristics (FR-026-FR-035, FR-077, FR-080, FR-094, FR-NEW-001-FR-NEW-010)**
- Covered in: contracts/interfaces.md (AdaptiveDepth), data-model.md (TaskProfile)
- All FRs represented in interface design

**Semantic Validation Layer (FR-036-FR-046, FR-081-FR-082)**
- Covered in: contracts/interfaces.md (SemanticValidator), data-model.md (SemanticValidationReport)
- All FRs represented in interface design

**Integration Requirements (FR-047-FR-051, FR-079)**
- Covered in: research.md Decision 8, contracts/interfaces.md integration patterns
- All FRs represented in integration approach

**Execution Inspection and History (FR-071-FR-076, FR-078, FR-095)**
- Covered in: data-model.md (ExecutionHistory, ExecutionPass), quickstart.md
- All FRs represented in data model design

### ✅ Key Entities

All entities from spec.md §Key Entities are defined in data-model.md:
- ExecutionPass ✅
- ExecutionHistory ✅
- RefinementAction ✅
- ConvergenceAssessment ✅
- SemanticValidationReport ✅
- ValidationIssue ✅
- AdaptiveDepthConfiguration ✅
- Subplan ✅
- Step (extended) ✅
- TTLExpirationResponse ✅
- TaskProfile ✅

### ✅ Schema Constraints

All schema constraints from spec.md §Schema Constraints are defined in data-model.md:
- ValidationIssue ✅
- SemanticValidationReport ✅
- ConvergenceAssessment ✅
- TaskProfile ✅
- RefinementAction ✅
- Step (extended) ✅
- ExecutionPass ✅
- ExecutionHistory ✅

### ✅ Success Criteria

Success criteria from spec.md §Success Criteria are addressed in:
- Technical Context: Performance Goals section
- Implementation approach ensures measurable outcomes
- Testing strategy covers all success criteria

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All constitutional constraints satisfied.

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Output**: `research.md`

- ✅ Extracted technical decisions from feature spec
- ✅ Documented implementation patterns and best practices
- ✅ Resolved all technical questions (no "NEEDS CLARIFICATION" items)
- ✅ Consolidated research findings with rationale and alternatives

**Key Decisions Documented**:
1. Multi-pass loop architecture (deterministic phase sequence)
2. LLM-only semantic reasoning (primary mechanism)
3. Modular external components (convergence/, adaptive/, validation/)
4. Declarative plan refinement (delta-style operations)
5. In-memory execution history (Sprint 2 scope)
6. TaskProfile tier stability (±1 tier requirement)
7. TTL boundary safety (safe step boundaries only)
8. Convergence engine integration (consumes validation report)
9. Supervisor repair integration (reuse Sprint 1 repair_json())
10. Refinement attempt limits (3 per fragment, 10 global)

### Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**: `data-model.md`, `contracts/interfaces.md`, `quickstart.md`

- ✅ Generated data-model.md with all Sprint 2 entities
  - Extended PlanStep with new fields (step_index, total_steps, incoming_context, handoff_to_next, clarity_state)
  - Defined ExecutionPass, ExecutionHistory, RefinementAction
  - Defined ConvergenceAssessment, SemanticValidationReport, ValidationIssue
  - Defined TaskProfile, AdaptiveDepthConfiguration, Subplan, TTLExpirationResponse
- ✅ Generated contracts/interfaces.md with interface definitions
  - ConvergenceEngine interface
  - AdaptiveDepth interface
  - SemanticValidator interface
  - RecursivePlanner interface
- ✅ Generated quickstart.md with usage examples and patterns
- ✅ Updated agent context (cursor-agent) with new technology stack

**Agent Context Updated**: ✅
- Language: Python 3.11+
- Frameworks: pydantic>=2.0.0, jsonschema>=4.0.0, requests>=2.31.0, pyyaml>=6.0.0
- Database: Memory subsystem (in-memory ExecutionHistory for Sprint 2, via K/V interface for state)

### Phase 2: Task Breakdown

**Status**: Pending (to be generated by `/speckit.tasks` command)

**Next Steps**:
1. Run `/speckit.tasks` command to generate `tasks.md`
2. Break down implementation into specific, actionable tasks
3. Organize tasks by module and priority

## Generated Artifacts

### Documentation
- ✅ `plan.md` - This implementation plan
- ✅ `research.md` - Technical decisions and research findings
- ✅ `data-model.md` - Entity schemas and relationships
- ✅ `contracts/interfaces.md` - Interface contracts for external modules
- ✅ `quickstart.md` - Usage guide and examples

### Agent Context
- ✅ `.cursor/rules/specify-rules.mdc` - Updated with Sprint 2 technology stack

## Branch and Paths

**Branch**: `002-adaptive-reasoning`  
**Implementation Plan**: `/home/brian/projects/Aeon-Architect/specs/002-adaptive-reasoning/plan.md`  
**Feature Spec**: `/home/brian/projects/Aeon-Architect/specs/002-adaptive-reasoning/spec.md`  
**Specs Directory**: `/home/brian/projects/Aeon-Architect/specs/002-adaptive-reasoning/`
