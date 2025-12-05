# Implementation Plan: Observability, Logging, and Test Coverage

**Branch**: `005-observability-logging` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-observability-logging/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This plan implements comprehensive observability improvements for the Aeon reasoning loop, including phase-aware structured logging with correlation IDs, actionable error logging with structured error models, enhanced debug visibility for refinement and execution failures, and expanded test coverage to ≥80%. The implementation extends the existing JSONL logging infrastructure established in Sprint 1 with phase transition tracking, correlation ID generation, structured error records, and comprehensive test coverage expansion.

**Technical Approach**: Extend existing `aeon/observability/` modules with phase-aware logging capabilities, structured error models with error codes, correlation ID generation using deterministic UUIDv5, and comprehensive test coverage expansion. All observability improvements remain outside the kernel and do not affect kernel determinism or performance. Logging remains synchronous and lightweight unless profiling proves otherwise.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0, jsonschema>=4.0.0, requests>=2.31.0, pyyaml>=6.0.0, uuid (standard library for UUIDv5)  
**Storage**: File-based JSONL logging (existing infrastructure)  
**Testing**: pytest with pytest-cov for coverage reporting, contract tests for interfaces, integration tests for multi-pass execution  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Logging latency <10ms per log entry, no blocking operations, preserve kernel determinism  
**Constraints**: Logging must remain synchronous and lightweight, no async complexity, no external monitoring integrations, no kernel changes, test coverage ≥80%, preserve backward compatibility with existing log schema  
**Scale/Scope**: Observability improvements only - extend logging infrastructure, add error models, expand test coverage. No changes to core reasoning logic, planning, validation, or memory subsystems.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: No. This feature extends observability modules (`aeon/observability/`) which are outside the kernel. No kernel code changes are required. Logging is invoked by the kernel but implemented in external observability modules.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. No kernel code changes are required. All observability improvements are in `aeon/observability/` modules outside the kernel.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Observability is infrastructure, not domain logic. Logging captures execution state but does not contain domain-specific business logic.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Observability improvements are implemented in `aeon/observability/` modules, separate from the kernel. The kernel invokes logging through existing interfaces.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. Observability modules expose logging interfaces that the kernel and orchestration modules invoke. No direct access to kernel internals.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. Observability modules receive state snapshots and event data through interface parameters. No direct access to kernel internals.

**Observability (Principle VIII)**:
- [x] Does this feature enhance observability without affecting kernel determinism?
  - **Answer**: Yes. Logging remains synchronous and lightweight. Correlation IDs use deterministic UUIDv5 generation. No non-deterministic behavior is introduced.
- [x] Are logs in JSONL format and non-blocking?
  - **Answer**: Yes. Logs remain in JSONL format (existing infrastructure). Logging is non-blocking with silent failure on write errors to prevent cascading failures.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Yes. All observability improvements are in external modules. The kernel invokes logging through existing interfaces without modification.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: N/A - no kernel changes are required. All improvements are in observability modules.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes - observability and logging are within Sprint 1 scope. This feature extends existing JSONL logging infrastructure without adding external monitoring integrations, cloud logic, or advanced features.

## Project Structure

### Documentation (this feature)

```text
specs/005-observability-logging/
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
├── orchestration/       # Existing: Orchestration modules (unchanged)
├── plan/                # Existing: Plan engine (unchanged)
├── validation/          # Existing: Schema validation (unchanged)
├── supervisor/          # Existing: Supervisor repair (unchanged)
├── tools/               # Existing: Tool registry and invocation (unchanged)
├── memory/              # Existing: Memory interface (unchanged)
├── llm/                 # Existing: LLM adapter interface (unchanged)
└── observability/       # MODIFIED: Extended logging and error models
    ├── __init__.py
    ├── logger.py        # MODIFIED: Add phase-aware logging, correlation IDs
    ├── models.py        # MODIFIED: Add ErrorRecord, CorrelationID, phase event models
    └── helpers.py       # MODIFIED: Add correlation ID generation (UUIDv5)

aeon/exceptions.py       # MODIFIED: Add structured error classes with error codes

tests/
├── contract/            # Existing: Interface contract tests (unchanged)
├── integration/         # MODIFIED: Add phase transition tests, error-path tests, TTL boundary tests, context propagation tests, deterministic convergence tests
└── unit/                # MODIFIED: Expand test coverage to ≥80%
    └── observability/   # MODIFIED: Add tests for phase-aware logging, error models, correlation IDs
```

**Structure Decision**: Extend existing `aeon/observability/` modules with phase-aware logging capabilities. Add structured error models to `aeon/exceptions.py`. Expand test coverage across all modules. No new modules or kernel changes required.

## Spec Requirements Coverage

This section confirms that all major requirements from spec.md are represented in this plan.

### ✅ Functional Requirements

**FR-001 to FR-011: Structured Logging**
- Covered in: Project Structure (observability/logger.py, observability/models.py)
- Implementation: Extend LogEntry model with phase entry/exit events, correlation_id, state transitions, refinement outcomes, evaluation outcomes
- Spec reference: §FR-001 through §FR-011

**FR-012 to FR-018: Error Logging and Error Models**
- Covered in: Project Structure (aeon/exceptions.py, observability/models.py)
- Implementation: Add structured error classes with error codes (AEON.<COMPONENT>.<CODE>), severity levels, context fields. Extend logging to capture structured error records.
- Spec reference: §FR-012 through §FR-018

**FR-019 to FR-023: Debug Visibility**
- Covered in: Project Structure (observability/logger.py)
- Implementation: Add logging for refinement triggers, refinement actions, execution results, convergence assessment results
- Spec reference: §FR-019 through §FR-023

**FR-024 to FR-032: Test Coverage**
- Covered in: Project Structure (tests/), Testing Strategy
- Implementation: Expand test coverage to ≥80%, add phase transition tests, error-path tests, TTL boundary tests, context propagation tests, deterministic convergence tests
- Spec reference: §FR-024 through §FR-032

**FR-033 to FR-036: Performance and Simplicity Constraints**
- Covered in: Technical Context, Constitution Check
- Implementation: Ensure logging remains synchronous and lightweight, no async complexity, no external monitoring integrations, preserve kernel determinism
- Spec reference: §FR-033 through §FR-036

### ✅ Success Criteria

All success criteria from spec.md §Success Criteria are addressed:
- SC-001: Correlation ID traceability (100% of log entries contain correlation_id) ✅
- SC-002: Structured error fields (100% of error cases contain required fields) ✅
- SC-003: Test coverage ≥80% ✅
- SC-004: All required test types present and passing ✅
- SC-005: Logging latency <10ms per entry ✅
- SC-006: Kernel determinism preserved ✅
- SC-007: Stable JSONL schemas (100% valid JSON) ✅
- SC-008: Diagnostic capability (≥90% of failures diagnosable from logs) ✅

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All constitutional constraints satisfied. Observability improvements are external to the kernel and do not affect kernel determinism or LOC limits.

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Status**: ✅ Complete

**Output**: `research.md`

**Research Tasks**:
1. ✅ UUIDv5 deterministic correlation ID generation patterns and best practices
2. ✅ Structured error model design patterns (error codes, severity levels, context)
3. ✅ Phase-aware logging patterns and event schema design
4. ✅ State snapshot design (minimal structured state slices)
5. ✅ Plan fragment logging patterns (changed steps only with step IDs)
6. ✅ Evaluation signal logging patterns (convergence assessment summary, validation issues summary)
7. ✅ Test coverage expansion strategies (phase transitions, error paths, TTL boundaries, context propagation, deterministic convergence)
8. ✅ Logging performance optimization (synchronous, lightweight, <10ms latency)
9. ✅ Backward compatibility strategies for existing log schema
10. ✅ Error recovery logging patterns

**Key Decisions Documented**:
1. Correlation ID generation using deterministic UUIDv5 with timestamp component
2. Structured error model with error codes (AEON.<COMPONENT>.<CODE> format)
3. Phase-aware logging with event types (phase_entry, phase_exit, state_transition, etc.)
4. Minimal state slices for state transition logging
5. Plan fragments with changed steps only
6. Evaluation signal summaries (convergence assessment, validation issues)
7. Test coverage expansion to ≥80% with specific test types
8. Synchronous, lightweight logging with <10ms latency target
9. Backward compatibility with existing log schema
10. Error recovery logging patterns

### Phase 1: Design & Contracts ✅ COMPLETE

**Status**: ✅ Complete

**Outputs**: `data-model.md`, `contracts/interfaces.md`, `quickstart.md`

**Design Tasks**:
1. ✅ Define LogEntry extensions (phase events, correlation_id, state transitions, refinement outcomes, evaluation outcomes)
2. ✅ Define ErrorRecord model (error_code, severity, message, affected_component, context)
3. ✅ Define CorrelationID generation interface (deterministic UUIDv5)
4. ✅ Define phase event schemas (phase_entry, phase_exit, state_transition, refinement_outcome, evaluation_outcome, error_recovery)
5. ✅ Define error code schema (AEON.<COMPONENT>.<CODE> format)
6. ✅ Define logging interface contracts (phase-aware logging methods, error logging methods)
7. ✅ Define backward compatibility strategy (schema versioning, migration path)
8. ✅ Create quickstart examples (phase-aware logging, error logging, correlation ID usage)

**Key Artifacts Generated**:
1. `data-model.md`: Defines CorrelationID, ErrorRecord, extended LogEntry, PlanFragment, ConvergenceAssessmentSummary, ValidationIssuesSummary, StateSlice entities
2. `contracts/interfaces.md`: Defines JSONLLogger interface extensions, ErrorRecord interface, exception interface extensions, correlation ID helper interface
3. `quickstart.md`: Provides usage examples, log entry examples, testing examples, best practices

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
- ✅ `contracts/interfaces.md` - Interface contracts for logging and error models (Phase 1)
- ✅ `quickstart.md` - Usage guide and examples (Phase 1)

## Branch and Paths

**Branch**: `005-observability-logging`  
**Implementation Plan**: `/home/brian/projects/Aeon-Architect/specs/005-observability-logging/plan.md`  
**Feature Spec**: `/home/brian/projects/Aeon-Architect/specs/005-observability-logging/spec.md`  
**Specs Directory**: `/home/brian/projects/Aeon-Architect/specs/005-observability-logging/`

