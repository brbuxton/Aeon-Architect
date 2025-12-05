# Implementation Plan: Phase Transition Stabilization & Deterministic Context Propagation

**Branch**: `006-phase-transitions` | **Date**: 2025-12-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-phase-transitions/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan stabilizes and strengthens the A→B→C→D orchestration loop by defining explicit phase transition contracts, ensuring deterministic and complete context propagation into each LLM call, correcting TTL boundary behavior, and enforcing consistent error-handling semantics. The implementation focuses on stabilization and correctness rather than new features, ensuring all phases operate coherently and predictably with correct contextual inputs. This sprint prepares Aeon for Sprint 7 (Prompt Contracts) by ensuring phase transitions are deterministic, testable, and fully observable.

**Technical Approach**: Define explicit phase transition contracts with input requirements, output guarantees, invariants, and enumerated failure conditions. Create a unified Context Propagation Specification that defines required fields for each phase. Fix TTL boundary behavior to ensure deterministic decrementing and correct expiration handling. Ensure ExecutionPass consistency across the loop. Extend existing logging infrastructure with phase boundary logging. All improvements remain outside the kernel and use existing models without expansion beyond bug fixes.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0 (for data models), existing orchestration modules (`aeon/orchestration/phases.py`), existing state models (`aeon/kernel/state.py`), existing logging infrastructure (`aeon/observability/logger.py`), existing exception models (`aeon/exceptions.py`)  
**Storage**: N/A (process context only, no persistent storage required)  
**Testing**: pytest with pytest-cov for coverage reporting, contract tests for phase transition interfaces, integration tests for multi-pass execution with phase transitions  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Phase transitions must be deterministic and complete in <100ms per transition, no blocking operations, preserve kernel determinism  
**Constraints**: All improvements must remain outside the kernel, use existing models without expansion beyond bug fixes, no new heuristic frameworks or fallback strategies, preserve backward compatibility with existing phase orchestration, all behavior must be deterministic for identical inputs  
**Scale/Scope**: Stabilization improvements only - define contracts, fix TTL behavior, ensure context propagation, extend logging. No changes to core reasoning logic, planning algorithms, or memory subsystems beyond bug fixes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: No. This feature stabilizes existing phase orchestration logic in `aeon/orchestration/phases.py` which is outside the kernel. Phase transition contracts, context propagation specifications, and TTL boundary fixes are implemented in orchestration modules, not the kernel. No kernel code changes are required.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. No kernel code changes are required. All stabilization improvements are in `aeon/orchestration/` modules outside the kernel.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Phase transition contracts and context propagation are orchestration infrastructure, not domain logic. The kernel invokes phase orchestration through existing interfaces without modification.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Phase transition contracts, context propagation specifications, and TTL boundary fixes are implemented in `aeon/orchestration/` modules, separate from the kernel. The kernel invokes phase orchestration through existing interfaces.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. Phase transition contracts define explicit interfaces for phase transitions. Context propagation specifications define required fields. All interactions use existing interface contracts.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. Orchestration modules receive state snapshots and context through interface parameters. No direct access to kernel internals.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: N/A - this feature does not modify plan structure. Plans remain JSON/YAML declarative structures. This feature ensures context propagation includes plan state correctly.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: No. Plans remain pure data structures. This feature ensures context propagation correctly includes plan state in LLM calls.

**Observability (Principle VIII)**:
- [x] Does this feature enhance observability without affecting kernel determinism?
  - **Answer**: Yes. Phase boundary logging extends existing logging infrastructure with phase entry/exit logs, state snapshots, and TTL snapshots. Logging remains synchronous and lightweight. No non-deterministic behavior is introduced.
- [x] Are logs in JSONL format and non-blocking?
  - **Answer**: Yes. Logs remain in JSONL format (existing infrastructure). Logging is non-blocking with silent failure on write errors to prevent cascading failures.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Yes. All stabilization improvements are in orchestration modules. The kernel invokes phase orchestration through existing interfaces without modification.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: N/A - no kernel changes are required. All improvements are in orchestration modules.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes - phase orchestration stabilization is within Sprint 1 scope. This feature extends existing orchestration infrastructure without adding external monitoring integrations, cloud logic, or advanced features.

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
├── kernel/              # Core orchestrator (unchanged - no modifications)
├── orchestration/       # MODIFIED: Phase transition contracts, context propagation, TTL fixes
│   ├── phases.py        # MODIFIED: Add phase transition contract validation, context propagation
│   ├── ttl.py           # MODIFIED: Fix TTL boundary behavior, ensure deterministic decrementing
│   └── refinement.py    # MODIFIED: Ensure context propagation includes refinement changes
├── plan/                # Existing: Plan engine (unchanged)
├── validation/          # Existing: Schema validation (unchanged)
├── supervisor/          # Existing: Supervisor repair (unchanged)
├── tools/               # Existing: Tool registry and invocation (unchanged)
├── memory/              # Existing: Memory interface (unchanged)
├── llm/                 # Existing: LLM adapter interface (unchanged)
└── observability/       # MODIFIED: Extend logging with phase boundary logging
    ├── logger.py        # MODIFIED: Add phase entry/exit logging, state snapshots, TTL snapshots
    └── models.py        # MODIFIED: Add phase transition event models (if needed)

aeon/exceptions.py       # MODIFIED: Add phase transition error classes with error codes

tests/
├── contract/            # MODIFIED: Add phase transition contract tests
├── integration/         # MODIFIED: Add phase transition integration tests, context propagation tests, TTL boundary tests
└── unit/                # MODIFIED: Add phase transition unit tests, ExecutionPass consistency tests
    └── orchestration/   # MODIFIED: Add tests for phase transition contracts, context propagation, TTL behavior
```

**Structure Decision**: Extend existing `aeon/orchestration/` modules with phase transition contracts, context propagation specifications, and TTL boundary fixes. Extend existing `aeon/observability/` modules with phase boundary logging. Add phase transition error classes to `aeon/exceptions.py`. Expand test coverage for phase transitions, context propagation, and TTL behavior. No new modules or kernel changes required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All constitutional constraints satisfied. Phase transition stabilization improvements are external to the kernel and do not affect kernel determinism or LOC limits.

## Spec Requirements Coverage

This section confirms that all major requirements from spec.md are represented in this plan.

### ✅ Functional Requirements

**FR-001 to FR-005: Phase Transition Contracts**
- Covered in: Project Structure (orchestration/phases.py)
- Implementation: Define explicit input requirements, output guarantees, invariants, and failure modes for A→B, B→C, C→D, D→A/B transitions. Enumerate all failure conditions with retryability classification.
- Spec reference: §FR-001 through §FR-005

**FR-006 to FR-011: Phase Transition Failure Contracts**
- Covered in: Project Structure (orchestration/phases.py, aeon/exceptions.py)
- Implementation: Define explicit failure condition enumeration with retryability classification. Add structured error logging with error codes (AEON.PHASE_TRANSITION.<CODE>). Implement retry logic (once if retryable, abort if non-retryable).
- Spec reference: §FR-006 through §FR-011

**FR-012 to FR-021: Context Propagation**
- Covered in: Project Structure (orchestration/phases.py)
- Implementation: Define unified Context Propagation Specification as structured document. Ensure all LLM calls receive required context fields (task_profile, plan state, execution_results, evaluation_results, pass_number, phase, TTL remaining, correlation_id, adaptive depth inputs). Ensure correlation_id and execution_start_timestamp are passed unchanged.
- Spec reference: §FR-012 through §FR-021

**FR-022 to FR-024: Prompt Context Alignment**
- Covered in: Project Structure (orchestration/phases.py)
- Implementation: Review all prompt schemas, remove unused keys or ensure orchestrator/phases populate them. Ensure no prompt contains null semantic inputs.
- Spec reference: §FR-022 through §FR-024

**FR-025 to FR-030a: TTL Boundary Behavior**
- Covered in: Project Structure (orchestration/ttl.py, orchestration/phases.py)
- Implementation: Fix TTL to decrement exactly once per cycle. Ensure correct behavior at TTL=1, TTL=0, expiration boundaries. Check TTL before phase entry AND after each LLM call within phase. Use TTLExpirationResponse for all expiration cases.
- Spec reference: §FR-025 through §FR-030a

**FR-031 to FR-034: ExecutionPass Consistency**
- Covered in: Project Structure (kernel/state.py)
- Implementation: Define required fields before/after each phase. Define invariants for merging execution_results and evaluation_results. Ensure ExecutionPass consistency across the loop.
- Spec reference: §FR-031 through §FR-034

**FR-035 to FR-040: Logging Requirements**
- Covered in: Project Structure (observability/logger.py, observability/models.py)
- Implementation: Add phase entry/exit logging, deterministic state snapshots, TTL snapshots, structured error logs for phase boundary failures. Use existing logging schema from Sprint 5.
- Spec reference: §FR-035 through §FR-040

### ✅ Success Criteria

All success criteria from spec.md §Success Criteria are addressed:
- SC-001: All A→B→C→D transitions are deterministic, logged, and testable ✅
- SC-002: All LLM prompts see complete and accurate context ✅
- SC-003: TTL behavior is correct and fully observable ✅
- SC-004: ExecutionPass consistency is guaranteed across the loop ✅
- SC-005: Failure handling follows explicit contracts with no new heuristics ✅
- SC-006: Gate Condition Met: Phase integration is sufficiently stable for Sprint 7 ✅

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Status**: ✅ Complete

**Output**: `research.md`

**Research Tasks**:
1. ✅ Phase transition contract design patterns (input requirements, output guarantees, invariants, failure modes)
2. ✅ Context propagation specification design (must-have, must-pass-unchanged, may-modify fields)
3. ✅ TTL boundary behavior patterns (decrement timing, expiration detection, boundary conditions)
4. ✅ ExecutionPass consistency patterns (required fields, invariants, merging rules)
5. ✅ Phase boundary logging patterns (entry/exit logs, state snapshots, TTL snapshots)
6. ✅ Error classification patterns (retryable vs non-retryable, error codes, structured error logging)
7. ✅ LLM call context requirements (minimal context per phase, context validation)
8. ✅ Prompt schema alignment patterns (unused key removal, null input prevention)

**Key Decisions Documented**:
1. Phase transition contracts define explicit input requirements, output guarantees, invariants, and enumerated failure conditions
2. Context Propagation Specification defines must-have, must-pass-unchanged, and may-modify fields per phase
3. TTL decrements exactly once per cycle (A→B→C→D), checked before phase entry AND after each LLM call
4. ExecutionPass required fields defined before/after each phase with invariants for merging
5. Phase boundary logging extends existing logging with entry/exit logs, state snapshots, TTL snapshots
6. Error classification: retryable (transient network errors, JSON parsing errors) vs non-retryable (TTL exhaustion, incomplete profile, context propagation failure)
7. LLM call context requirements: minimal context per phase with validation that all required fields are present
8. Prompt schema alignment: review all schemas, remove unused keys or populate them, ensure no null semantic inputs

### Phase 1: Design & Contracts ✅ COMPLETE

**Status**: ✅ Complete

**Outputs**: `data-model.md`, `contracts/interfaces.md`, `quickstart.md`

**Design Tasks**:
1. ✅ Define PhaseTransitionContract model (input requirements, output guarantees, invariants, failure modes)
2. ✅ Define ContextPropagationSpecification model (must-have, must-pass-unchanged, may-modify fields per phase)
3. ✅ Define ExecutionPass consistency requirements (required fields, invariants, merging rules)
4. ✅ Define TTL boundary behavior specification (decrement timing, expiration detection, boundary conditions)
5. ✅ Define phase boundary logging interface (entry/exit logs, state snapshots, TTL snapshots)
6. ✅ Define phase transition error classes (error codes, retryability classification)
7. ✅ Define LLM call context validation interface (context requirements per phase, validation rules)
8. ✅ Create quickstart examples (phase transition contracts, context propagation, TTL behavior, logging)

**Key Artifacts Generated**:
1. `data-model.md`: Defines PhaseTransitionContract, ContextPropagationSpecification, ExecutionPass consistency requirements, TTL boundary behavior specification, phase boundary logging models
2. `contracts/interfaces.md`: Defines phase transition contract interfaces, context propagation interfaces, TTL boundary interfaces, phase boundary logging interfaces, error interfaces
3. `quickstart.md`: Provides usage examples, phase transition examples, context propagation examples, TTL behavior examples, logging examples, testing examples, best practices

### Phase 2: Task Breakdown

**Status**: Pending (to be generated by `/speckit.tasks` command)

**Next Steps**:
1. Run `/speckit.tasks` command to generate `tasks.md`
2. Break down implementation into specific, actionable tasks
3. Organize tasks by module and priority

## Generated Artifacts

### Documentation
- ✅ `plan.md` - This implementation plan
- ✅ `research.md` - Technical decisions and research findings (Phase 0)
- ✅ `data-model.md` - Entity schemas and relationships (Phase 1)
- ✅ `contracts/interfaces.md` - Interface contracts for phase transitions, context propagation, TTL behavior, logging (Phase 1)
- ✅ `quickstart.md` - Usage guide and examples (Phase 1)

## Branch and Paths

**Branch**: `006-phase-transitions`  
**Implementation Plan**: `/home/brian/projects/Aeon-Architect/specs/006-phase-transitions/plan.md`  
**Feature Spec**: `/home/brian/projects/Aeon-Architect/specs/006-phase-transitions/spec.md`  
**Specs Directory**: `/home/brian/projects/Aeon-Architect/specs/006-phase-transitions/`
