# Tasks: Observability, Logging, and Test Coverage

**Input**: Design documents from `/specs/005-observability-logging/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/`, `tests/` at repository root
- All paths shown below use absolute paths from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create test directories per implementation plan: tests/unit/observability/, tests/integration/ (if needed)
- [ ] T002 [P] Verify existing observability module structure: aeon/observability/__init__.py, aeon/observability/logger.py, aeon/observability/models.py, aeon/observability/helpers.py
- [ ] T003 [P] Configure pytest test structure for observability modules in tests/unit/observability/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that must be complete before user stories can be implemented

**⚠️ CRITICAL**: No user story work can begin until correlation ID generation and base models are complete

### Correlation ID Infrastructure

- [ ] T004 [P] Implement generate_correlation_id function using UUIDv5 in aeon/observability/helpers.py
- [ ] T005 [P] Add fallback correlation ID generation (timestamp-based) in aeon/observability/helpers.py
- [ ] T006 [P] Add unit tests for correlation ID generation (deterministic, unique) in tests/unit/observability/test_helpers.py

### Base Data Models

- [ ] T007 [P] [US1] Create CorrelationID model in aeon/observability/models.py
- [ ] T008 [P] [US2] Create ErrorRecord model with code, severity, message, affected_component, context fields in aeon/observability/models.py
- [ ] T009 [P] [US1] Create PlanFragment model with changed_steps and unchanged_step_ids in aeon/observability/models.py
- [ ] T010 [P] [US1] Create ConvergenceAssessmentSummary model in aeon/observability/models.py
- [ ] T011 [P] [US1] Create ValidationIssuesSummary model in aeon/observability/models.py
- [ ] T012 [P] [US1] Create StateSlice base model and component-specific slices (PlanStateSlice, ExecutionStateSlice, RefinementStateSlice) in aeon/observability/models.py
- [ ] T013 [P] Extend LogEntry model with event, correlation_id, phase, pass_number, and event-specific fields in aeon/observability/models.py
- [ ] T014 [P] Add unit tests for all data models in tests/unit/observability/test_models.py

**Checkpoint**: Correlation ID generation and base models complete. User story implementation can now begin.

---

## Phase 3: User Story 1 - Phase-Aware Structured Logging (Priority: P1) 🎯 MVP

**Goal**: Implement phase-aware structured logging with correlation IDs that enable trace reconstruction through multi-pass execution.

**Independent Test**: Execute a multi-pass reasoning task and verify that logs contain phase entry/exit markers, state transition records, and a consistent correlation ID that appears in all log entries for that execution. The test delivers value by proving developers can trace execution flow and identify where failures occur.

**Dependencies**: Requires Phase 2 (correlation ID and base models) completion. This story is foundational for US2, US3.

### Logging Interface Extensions

- [ ] T015 [P] [US1] Implement log_phase_entry method in aeon/observability/logger.py
- [ ] T016 [P] [US1] Implement log_phase_exit method in aeon/observability/logger.py
- [ ] T017 [P] [US1] Implement log_state_transition method in aeon/observability/logger.py
- [ ] T018 [P] [US1] Implement log_refinement_outcome method in aeon/observability/logger.py
- [ ] T019 [P] [US1] Implement log_evaluation_outcome method in aeon/observability/logger.py
- [ ] T020 [P] [US1] Ensure all logging methods include correlation_id in log entries in aeon/observability/logger.py
- [ ] T021 [P] [US1] Ensure all logging methods are non-blocking with silent failure on errors in aeon/observability/logger.py

### Integration Points

- [ ] T022 [US1] Integrate phase entry/exit logging in aeon/orchestration/phases.py
- [ ] T023 [US1] Integrate state transition logging in aeon/orchestration/refinement.py
- [ ] T024 [US1] Integrate refinement outcome logging in aeon/orchestration/refinement.py
- [ ] T025 [US1] Integrate evaluation outcome logging in aeon/convergence/engine.py
- [ ] T026 [US1] Generate correlation ID at execution start in aeon/kernel/orchestrator.py
- [ ] T026a [US1] Create a new data class AeonExecutionContext that stores correlation_id, execution_start_timestamp, and other execution metadata. The class MUST contain no orchestration or control-flow logic.
- [ ] T026b [US1] The orchestrator MUST NOT populate fields other than correlation_id and execution_start_timestamp.
AeonExecutionContext MUST NOT be used by external modules to store diagnostic or pass/step/module-scoped metadata.
- [ ] T026c [US1] Modules MUST NOT store evaluation, validation, convergence, adaptive-depth, TTL, or execution metadata inside context.
- [ ] T026d [US1] Logging MUST use AeonExecutionContext only for correlation_id; all other fields come from domain objects (ExecutionPass, StepExecutionResult, ValidationReport, etc.). AeonExecutionContext MUST NOT be serialized wholesale.
- [ ] T027 [US1] Pass correlation ID through all phases and passes in aeon/kernel/orchestrator.py

### Unit Tests

- [ ] T028 [P] [US1] Add unit tests for phase entry/exit logging in tests/unit/observability/test_logger.py
- [ ] T029 [P] [US1] Add unit tests for state transition logging in tests/unit/observability/test_logger.py
- [ ] T030 [P] [US1] Add unit tests for refinement outcome logging in tests/unit/observability/test_logger.py
- [ ] T031 [P] [US1] Add unit tests for evaluation outcome logging in tests/unit/observability/test_logger.py
- [ ] T032 [P] [US1] Add unit tests for correlation ID persistence across phases in tests/unit/observability/test_logger.py

### Integration Tests

- [ ] T033 [US1] Add integration test for multi-pass execution with phase logging in tests/integration/test_phase_logging.py
- [ ] T034 [US1] Add integration test for correlation ID traceability (100% of entries contain correlation_id) in tests/integration/test_phase_logging.py
- [ ] T035 [US1] Add integration test for phase transition sequence (A→B→C→D) in tests/integration/test_phase_logging.py
- [ ] T036 [US1] Add integration test for state transition logging with minimal slices in tests/integration/test_phase_logging.py

**Checkpoint**: Phase-aware structured logging complete. All log entries contain correlation IDs, phase transitions are logged, state transitions are captured with minimal slices.

---

## Phase 4: User Story 2 - Actionable Error Logging (Priority: P1)

**Goal**: Implement structured error logging with error codes, severity levels, and context that enables rapid diagnosis.

**Independent Test**: Trigger various error conditions (refinement failures, execution errors, validation failures) and verify that error logs contain all required fields (code, severity, message, component, step_id, context) in a structured format. The test delivers value by proving developers can quickly identify root causes and affected components.

**Dependencies**: Requires Phase 3 (phase-aware logging) completion for correlation ID integration.

### Exception Extensions

- [ ] T037 [P] [US2] Add ERROR_CODE constant to RefinementError class in aeon/exceptions.py
- [ ] T038 [P] [US2] Add ERROR_CODE constant to ExecutionError class in aeon/exceptions.py
- [ ] T039 [P] [US2] Add ERROR_CODE constant to ValidationError class in aeon/exceptions.py
- [ ] T040 [P] [US2] Add SEVERITY constant to all error classes in aeon/exceptions.py
- [ ] T041 [P] [US2] Implement to_error_record method on RefinementError in aeon/exceptions.py
- [ ] T042 [P] [US2] Implement to_error_record method on ExecutionError in aeon/exceptions.py
- [ ] T043 [P] [US2] Implement to_error_record method on ValidationError in aeon/exceptions.py
- [ ] T044 [P] [US2] Implement to_error_record method on base AeonError class in aeon/exceptions.py
- [ ] T045 [P] [US2] Add error codes for all existing exception classes following AEON.<COMPONENT>.<CODE> format in aeon/exceptions.py

### Error Logging Interface

- [ ] T046 [P] [US2] Implement log_error method in aeon/observability/logger.py
- [ ] T047 [P] [US2] Implement log_error_recovery method in aeon/observability/logger.py
- [ ] T048 [P] [US2] Ensure error logging includes correlation_id in aeon/observability/logger.py
- [ ] T049 [P] [US2] Ensure error logging captures refinement errors with before_plan_fragment, after_plan_fragment, evaluation_signals in aeon/observability/logger.py
- [ ] T050 [P] [US2] Ensure error logging captures execution errors with step_id, attempted_action, tool_name, error_context in aeon/observability/logger.py
- [ ] T051 [P] [US2] Ensure error logging captures validation errors with validation_type, validation_details in aeon/observability/logger.py

### Integration Points

- [ ] T052 [US2] Integrate error logging in refinement error catch sites in aeon/orchestration/refinement.py
- [ ] T053 [US2] Integrate error logging in execution error catch sites in aeon/kernel/executor.py
- [ ] T054 [US2] Integrate error logging in validation error catch sites in aeon/validation/schema.py and aeon/validation/semantic.py
- [ ] T055 [US2] Integrate error recovery logging in kernel recovery decision points in aeon/kernel/orchestrator.py

### Unit Tests

- [ ] T056 [P] [US2] Add unit tests for to_error_record conversion in tests/unit/observability/test_models.py
- [ ] T057 [P] [US2] Add unit tests for error logging methods in tests/unit/observability/test_logger.py
- [ ] T058 [P] [US2] Add unit tests for error code format validation in tests/unit/observability/test_models.py
- [ ] T059 [P] [US2] Add unit tests for severity level validation in tests/unit/observability/test_models.py

### Integration Tests

- [ ] T060 [US2] Add integration test for refinement error logging with all required fields in tests/integration/test_error_logging.py
- [ ] T061 [US2] Add integration test for execution error logging with all required fields in tests/integration/test_error_logging.py
- [ ] T062 [US2] Add integration test for validation error logging with all required fields in tests/integration/test_error_logging.py
- [ ] T063 [US2] Add integration test for error recovery logging in tests/integration/test_error_logging.py
- [ ] T064 [US2] Add integration test for structured error fields (100% of error cases contain required fields) in tests/integration/test_error_logging.py

**Checkpoint**: Actionable error logging complete. All error cases log structured error records with error codes, severity levels, and context.

---

## Phase 5: User Story 3 - Refinement and Execution Debug Visibility (Priority: P2)

**Goal**: Implement detailed logging for refinement outcomes, evaluation signals, plan state changes, and execution results.

**Independent Test**: Execute a plan that requires refinement and verify that logs capture refinement triggers (evaluation signals, validation issues), refinement actions applied, before/after plan fragments, and execution results with sufficient detail to understand failures. The test delivers value by proving developers can understand refinement and execution behavior.

**Dependencies**: Requires Phase 3 (phase-aware logging) and Phase 4 (error logging) completion.

### Refinement Debug Logging

- [ ] T065 [P] [US3] Enhance log_refinement_outcome to include refinement triggers (evaluation signals) in aeon/observability/logger.py
- [ ] T066 [P] [US3] Ensure refinement outcome logging includes convergence assessment summary in aeon/observability/logger.py
- [ ] T067 [P] [US3] Ensure refinement outcome logging includes validation issues summary in aeon/observability/logger.py
- [ ] T068 [US3] Integrate refinement trigger logging in aeon/orchestration/refinement.py
- [ ] T069 [US3] Integrate refinement action logging (which steps modified/added/removed) in aeon/orchestration/refinement.py

### Execution Debug Logging

- [ ] T070 [US3] Add logging for step execution outcomes in aeon/kernel/executor.py
- [ ] T071 [US3] Add logging for tool invocation results in aeon/kernel/executor.py
- [ ] T072 [US3] Add logging for step status changes in aeon/kernel/executor.py
- [ ] T073 [US3] Integrate execution result logging in aeon/kernel/executor.py

### Convergence Debug Logging

- [ ] T074 [US3] Enhance log_evaluation_outcome to include convergence assessment results with reason codes in aeon/observability/logger.py
- [ ] T075 [US3] Integrate convergence assessment logging in aeon/convergence/engine.py
- [ ] T076 [US3] Ensure convergence assessment logging explains why convergence was not achieved in aeon/convergence/engine.py

### Unit Tests

- [ ] T077 [P] [US3] Add unit tests for refinement outcome logging with evaluation signals in tests/unit/observability/test_logger.py
- [ ] T078 [P] [US3] Add unit tests for execution result logging in tests/unit/observability/test_logger.py
- [ ] T079 [P] [US3] Add unit tests for convergence assessment logging in tests/unit/observability/test_logger.py

### Integration Tests

- [ ] T080 [US3] Add integration test for refinement trigger logging in tests/integration/test_debug_visibility.py
- [ ] T081 [US3] Add integration test for refinement action logging in tests/integration/test_debug_visibility.py
- [ ] T082 [US3] Add integration test for execution result logging in tests/integration/test_debug_visibility.py
- [ ] T083 [US3] Add integration test for convergence assessment logging in tests/integration/test_debug_visibility.py
- [ ] T084 [US3] Add integration test for plan state change logging in tests/integration/test_debug_visibility.py

**Checkpoint**: Refinement and execution debug visibility complete. Logs provide sufficient detail to understand why refinements were applied or why execution failed.

---

## Phase 6: User Story 4 - Comprehensive Test Coverage (Priority: P1)

**Goal**: Expand test coverage to ≥80% with phase transition tests, error-path tests, TTL boundary tests, context propagation tests, and deterministic convergence tests.

**Independent Test**: Run the test suite with coverage reporting and verify that coverage is ≥80%, that phase transition tests exist, that error-path tests cover refinement and execution failures, that TTL boundary tests exist, and that context propagation tests validate phase context (not memory). The test delivers value by proving the codebase is well-tested and safe to refactor.

**Dependencies**: Requires Phase 3, Phase 4, and Phase 5 completion for comprehensive coverage.

### Phase Transition Tests

- [ ] T085 [P] [US4] Add phase transition tests for phase entry/exit behavior in tests/integration/test_phase_transitions.py
- [ ] T086 [P] [US4] Add phase transition tests for state handoffs in tests/integration/test_phase_transitions.py
- [ ] T087 [P] [US4] Add phase transition tests for error handling at phase boundaries in tests/integration/test_phase_transitions.py
- [ ] T088 [P] [US4] Add phase transition tests for correlation ID persistence across phases in tests/integration/test_phase_transitions.py

### Error-Path Tests

- [ ] T089 [P] [US4] Add error-path tests for refinement errors in tests/integration/test_error_paths.py
- [ ] T090 [P] [US4] Add error-path tests for execution errors in tests/integration/test_error_paths.py
- [ ] T091 [P] [US4] Add error-path tests for validation errors in tests/integration/test_error_paths.py
- [ ] T092 [P] [US4] Add error-path tests for error recovery in tests/integration/test_error_paths.py

### TTL Boundary Tests

- [ ] T093 [P] [US4] Add TTL boundary tests for single-pass execution in tests/integration/test_ttl_boundaries.py
- [ ] T094 [P] [US4] Add TTL boundary tests for phase boundary expiration in tests/integration/test_ttl_boundaries.py
- [ ] T095 [P] [US4] Add TTL boundary tests for mid-phase expiration in tests/integration/test_ttl_boundaries.py

### Context Propagation Tests

- [ ] T096 [P] [US4] Add context propagation tests for phase context (not memory) in tests/integration/test_context_propagation.py
- [ ] T097 [P] [US4] Add context propagation tests for evaluation signals propagation in tests/integration/test_context_propagation.py
- [ ] T098 [P] [US4] Add context propagation tests for refinement history propagation in tests/integration/test_context_propagation.py

### Deterministic Convergence Tests

- [ ] T099 [P] [US4] Add deterministic convergence tests for simple, repeatable tasks in tests/integration/test_deterministic_convergence.py
- [ ] T100 [P] [US4] Add deterministic convergence tests for convergence behavior validation in tests/integration/test_deterministic_convergence.py

### Unit Test Coverage Expansion

- [ ] T101 [P] [US4] Expand unit test coverage for observability modules to ≥90% in tests/unit/observability/
- [ ] T102 [P] [US4] Expand unit test coverage for error models to ≥90% in tests/unit/observability/test_models.py
- [ ] T103 [P] [US4] Expand unit test coverage for orchestration modules in tests/unit/orchestration/
- [ ] T104 [P] [US4] Expand unit test coverage for kernel modules in tests/unit/kernel/
- [ ] T105 [P] [US4] Expand unit test coverage for plan modules in tests/unit/plan/
- [ ] T106 [P] [US4] Expand unit test coverage for validation modules in tests/unit/validation/
- [ ] T107 [P] [US4] Expand unit test coverage for convergence modules in tests/unit/convergence/
- [ ] T108 [P] [US4] Expand unit test coverage for supervisor modules in tests/unit/supervisor/
- [ ] T109 [P] [US4] Expand unit test coverage for tools modules in tests/unit/tools/

### Coverage Validation

- [ ] T110 [US4] Run coverage report and verify overall coverage ≥80% using pytest-cov
- [ ] T111 [US4] Verify all required test types are present and passing (phase transitions, error paths, TTL boundaries, context propagation, deterministic convergence)
- [ ] T112 [US4] Document coverage improvements and test additions

**Checkpoint**: Comprehensive test coverage complete. Overall coverage ≥80%, all required test types present and passing.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final polish, performance validation, backward compatibility, and documentation

### Performance Validation

- [ ] T113 [P] Profile logging operations and measure latency in tests/integration/test_logging_performance.py
- [ ] T114 [P] Verify logging latency <10ms per entry (SC-005) in tests/integration/test_logging_performance.py
- [ ] T115 [P] Optimize JSON serialization if latency exceeds 10ms in aeon/observability/logger.py
- [ ] T116 [P] Verify logging is non-blocking and fails silently on errors in tests/integration/test_logging_performance.py

### Backward Compatibility

- [ ] T117 [P] Verify existing format_entry method continues to work (creates event="cycle") in aeon/observability/logger.py
- [ ] T118 [P] Verify existing log_entry method continues to work in aeon/observability/logger.py
- [ ] T119 [P] Test backward compatibility with existing log parsers in tests/integration/test_backward_compatibility.py
- [ ] T120 [P] Document schema evolution and backward compatibility in quickstart.md

### Determinism Validation

- [ ] T121 [P] Verify correlation ID generation is deterministic (same inputs produce same ID) in tests/unit/observability/test_helpers.py
- [ ] T122 [P] Verify logging operations do not affect kernel determinism in tests/integration/test_determinism.py
- [ ] T123 [P] Verify no non-deterministic behavior introduced by observability improvements in tests/integration/test_determinism.py

### Schema Validation

- [ ] T124 [P] Verify all log entries conform to stable JSONL schemas (100% valid JSON) in tests/integration/test_log_schema.py
- [ ] T125 [P] Add schema validation tests for all event types in tests/integration/test_log_schema.py
- [ ] T126 [P] Verify log schema backward compatibility in tests/integration/test_log_schema.py

### Diagnostic Capability Validation

- [ ] T127 [P] Verify diagnostic capability (≥90% of failures diagnosable from logs) in tests/integration/test_diagnostic_capability.py
- [ ] T128 [P] Add tests for log-based failure diagnosis in tests/integration/test_diagnostic_capability.py

### Documentation

- [ ] T129 [P] Update quickstart.md with phase-aware logging examples
- [ ] T130 [P] Update quickstart.md with error logging examples
- [ ] T131 [P] Document correlation ID usage patterns in quickstart.md
- [ ] T132 [P] Document error code conventions in quickstart.md

**Checkpoint**: Polish complete. Performance validated, backward compatibility verified, determinism preserved, schema validated, diagnostic capability confirmed.

---

## Dependencies

### User Story Completion Order

1. **Phase 2 (Foundational)** → **Phase 3 (US1)** → **Phase 4 (US2)** → **Phase 5 (US3)** → **Phase 6 (US4)** → **Phase 7 (Polish)**

2. **US1 (Phase-Aware Logging)** is foundational for US2 and US3 (provides correlation IDs and phase logging infrastructure)

3. **US2 (Error Logging)** depends on US1 (requires correlation IDs)

4. **US3 (Debug Visibility)** depends on US1 and US2 (requires phase logging and error logging)

5. **US4 (Test Coverage)** depends on US1, US2, and US3 (requires all features to be implemented for comprehensive coverage)

6. **Phase 7 (Polish)** depends on all user stories (validates performance, compatibility, determinism)

### Parallel Execution Opportunities

**Within Phase 2 (Foundational)**:
- T004-T006 (correlation ID) can run in parallel with T007-T014 (data models)
- T007-T014 (data models) can run in parallel with each other (different models)

**Within Phase 3 (US1)**:
- T015-T021 (logging methods) can run in parallel (different methods)
- T028-T032 (unit tests) can run in parallel (different test files)

**Within Phase 4 (US2)**:
- T037-T045 (exception extensions) can run in parallel (different exception classes)
- T046-T051 (error logging interface) can run in parallel with T037-T045
- T056-T059 (unit tests) can run in parallel

**Within Phase 5 (US3)**:
- T065-T067 (refinement debug logging) can run in parallel
- T070-T073 (execution debug logging) can run in parallel
- T077-T079 (unit tests) can run in parallel

**Within Phase 6 (US4)**:
- T085-T100 (integration tests) can run in parallel (different test files)
- T101-T109 (unit test coverage) can run in parallel (different modules)

**Within Phase 7 (Polish)**:
- T113-T116 (performance validation) can run in parallel
- T117-T120 (backward compatibility) can run in parallel
- T121-T123 (determinism validation) can run in parallel
- T124-T126 (schema validation) can run in parallel
- T127-T128 (diagnostic capability) can run in parallel
- T129-T132 (documentation) can run in parallel

---

## Implementation Strategy

### MVP Scope

**MVP includes**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1 - Phase-Aware Structured Logging)

**Rationale**: Phase-aware structured logging with correlation IDs is foundational for all subsequent observability work. This MVP enables trace reconstruction through multi-pass execution, which is essential for debugging.

### Incremental Delivery

1. **Sprint 1**: Phase 1 + Phase 2 + Phase 3 (US1) - Phase-aware structured logging
2. **Sprint 2**: Phase 4 (US2) - Actionable error logging
3. **Sprint 3**: Phase 5 (US3) - Refinement and execution debug visibility
4. **Sprint 4**: Phase 6 (US4) - Comprehensive test coverage
5. **Sprint 5**: Phase 7 (Polish) - Performance, compatibility, determinism validation

### Success Criteria Validation

- **SC-001**: Correlation ID traceability - Validated in T034 (100% of entries contain correlation_id)
- **SC-002**: Structured error fields - Validated in T064 (100% of error cases contain required fields)
- **SC-003**: Test coverage ≥80% - Validated in T110
- **SC-004**: All required test types present - Validated in T111
- **SC-005**: Logging latency <10ms - Validated in T114
- **SC-006**: Kernel determinism preserved - Validated in T123
- **SC-007**: Stable JSONL schemas - Validated in T124
- **SC-008**: Diagnostic capability ≥90% - Validated in T127

---

## Task Summary

- **Total Tasks**: 132
- **Setup Tasks**: 3 (T001-T003)
- **Foundational Tasks**: 11 (T004-T014)
- **US1 Tasks**: 22 (T015-T036)
- **US2 Tasks**: 28 (T037-T064)
- **US3 Tasks**: 20 (T065-T084)
- **US4 Tasks**: 28 (T085-T112)
- **Polish Tasks**: 20 (T113-T132)

### Parallel Opportunities

- **Phase 2**: 8 parallel tasks (T004-T014)
- **Phase 3**: 12 parallel tasks (T015-T021, T028-T032)
- **Phase 4**: 18 parallel tasks (T037-T045, T046-T051, T056-T059)
- **Phase 5**: 9 parallel tasks (T065-T067, T070-T073, T077-T079)
- **Phase 6**: 28 parallel tasks (T085-T109)
- **Phase 7**: 20 parallel tasks (T113-T132)

### Independent Test Criteria

- **US1**: Multi-pass execution with phase logging and correlation ID traceability
- **US2**: Error conditions trigger structured error logging with all required fields
- **US3**: Refinement and execution logs provide sufficient detail for debugging
- **US4**: Test suite achieves ≥80% coverage with all required test types

---

## Notes

- All tasks follow the strict checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- Tasks are organized by user story to enable independent implementation and testing
- Parallel tasks ([P]) can be executed concurrently if working on different files
- Story labels ([US1], [US2], [US3], [US4]) indicate which user story each task belongs to
- File paths are absolute from repository root for clarity
- MVP scope focuses on Phase 1 + Phase 2 + Phase 3 (US1) for initial delivery


