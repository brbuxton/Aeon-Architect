# Tasks: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Input**: Design documents from `/specs/004-kernel-refactor/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are included to verify behavioral preservation and ensure all existing tests pass without modification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/` package at repository root
- **Tests**: `tests/` at repository root
- All paths follow plan.md structure

## Phase 1: Setup (Project Initialization)

**Purpose**: Create orchestration module structure and prepare for extraction

- [X] T001 Create orchestration module directory structure in aeon/orchestration/
- [X] T002 [P] Create __init__.py in aeon/orchestration/__init__.py
- [X] T003 [P] Create phases.py stub in aeon/orchestration/phases.py
- [X] T004 [P] Create refinement.py stub in aeon/orchestration/refinement.py
- [X] T005 [P] Create step_prep.py stub in aeon/orchestration/step_prep.py
- [X] T006 [P] Create ttl.py stub in aeon/orchestration/ttl.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Measure and document baseline kernel LOC in aeon/kernel/orchestrator.py and aeon/kernel/executor.py
- [X] T008 [P] Create PhaseResult data model in aeon/orchestration/phases.py per data-model.md
- [X] T009 [P] Create RefinementResult data model in aeon/orchestration/refinement.py per data-model.md
- [X] T010 [P] Create StepPreparationResult data model in aeon/orchestration/step_prep.py per data-model.md
- [X] T011 [P] Create TTLExpirationResult data model in aeon/orchestration/ttl.py per data-model.md

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Restore Constitutional Compliance (Priority: P1) 🎯 MVP

**Goal**: Reduce kernel LOC from 1351 to ≤800 (target <750) by extracting orchestration strategy logic

**Independent Test**: Measure kernel LOC after refactoring and verify it is ≤800 LOC (target <750). Only orchestrator.py and executor.py count toward the limit.

**Dependencies**: Phase 2 complete

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for LOC measurement in tests/unit/kernel/test_loc.py
- [X] T013 [P] [US1] Integration test to verify kernel LOC ≤800 after refactoring in tests/integration/test_kernel_loc.py

### Implementation for User Story 1

- [X] T014 [US1] Extract _phase_a_taskprofile_ttl() to PhaseOrchestrator.phase_a_taskprofile_ttl() in aeon/orchestration/phases.py
- [X] T015 [US1] Extract _phase_b_initial_plan_refinement() to PhaseOrchestrator.phase_b_initial_plan_refinement() in aeon/orchestration/phases.py
- [X] T016 [US1] Extract _phase_c_execute_batch() to PhaseOrchestrator.phase_c_execute_batch() in aeon/orchestration/phases.py
- [X] T017 [US1] Extract _phase_c_evaluate() to PhaseOrchestrator.phase_c_evaluate() in aeon/orchestration/phases.py
- [X] T018 [US1] Extract _phase_c_refine() to PhaseOrchestrator.phase_c_refine() in aeon/orchestration/phases.py
- [X] T019 [US1] Extract _phase_d_adaptive_depth() to PhaseOrchestrator.phase_d_adaptive_depth() in aeon/orchestration/phases.py
- [X] T020 [US1] Extract _apply_refinement_actions() to PlanRefinement.apply_actions() in aeon/orchestration/refinement.py
- [X] T021 [US1] Extract _get_ready_steps() to StepPreparation.get_ready_steps() in aeon/orchestration/step_prep.py
- [X] T022 [US1] Extract _populate_incoming_context() to StepPreparation.populate_incoming_context() in aeon/orchestration/step_prep.py
- [X] T023 [US1] Extract _populate_step_indices() to StepPreparation.populate_step_indices() in aeon/orchestration/step_prep.py
- [X] T024 [US1] Extract _create_ttl_expiration_response() to TTLStrategy.create_expiration_response() in aeon/orchestration/ttl.py
- [X] T025 [US1] Update Orchestrator.__init__() to initialize orchestration modules in aeon/kernel/orchestrator.py
- [X] T026 [US1] Replace _phase_a_taskprofile_ttl() call with PhaseOrchestrator.phase_a_taskprofile_ttl() in aeon/kernel/orchestrator.py
- [X] T027 [US1] Replace _phase_b_initial_plan_refinement() call with PhaseOrchestrator.phase_b_initial_plan_refinement() in aeon/kernel/orchestrator.py
- [X] T028 [US1] Replace _phase_c_execute_batch() call with PhaseOrchestrator.phase_c_execute_batch() in aeon/kernel/orchestrator.py
- [X] T029 [US1] Replace _phase_c_evaluate() call with PhaseOrchestrator.phase_c_evaluate() in aeon/kernel/orchestrator.py
- [X] T030 [US1] Replace _phase_c_refine() call with PhaseOrchestrator.phase_c_refine() in aeon/kernel/orchestrator.py
- [X] T031 [US1] Replace _phase_d_adaptive_depth() call with PhaseOrchestrator.phase_d_adaptive_depth() in aeon/kernel/orchestrator.py
- [X] T032 [US1] Replace _apply_refinement_actions() call with PlanRefinement.apply_actions() in aeon/kernel/orchestrator.py
- [X] T033 [US1] Replace _get_ready_steps() call with StepPreparation.get_ready_steps() in aeon/kernel/orchestrator.py
- [X] T034 [US1] Replace _populate_incoming_context() call with StepPreparation.populate_incoming_context() in aeon/kernel/orchestrator.py
- [X] T035 [US1] Replace _populate_step_indices() call with StepPreparation.populate_step_indices() in aeon/kernel/orchestrator.py
- [X] T036 [US1] Replace _create_ttl_expiration_response() call with TTLStrategy.create_expiration_response() in aeon/kernel/orchestrator.py
- [X] T037 [US1] Remove extracted methods from Orchestrator class in aeon/kernel/orchestrator.py
- [X] T038 [US1] Measure and document final kernel LOC in aeon/kernel/orchestrator.py and aeon/kernel/executor.py

**Checkpoint**: At this point, User Story 1 should be complete. Kernel LOC should be ≤800 (target <750). All extracted logic moved to orchestration modules.

---

## Phase 4: User Story 2 - Preserve System Behavior (Priority: P1)

**Goal**: Ensure all existing functionality continues working after refactoring - all tests pass without modification

**Independent Test**: Run the complete test suite and verify all tests pass without modification. Multi-pass execution workflows produce identical results before and after refactoring.

**Dependencies**: Phase 3 complete

### Tests for User Story 2

- [X] T039 [P] [US2] Integration test to verify all existing tests pass in tests/integration/test_behavioral_preservation.py
- [X] T040 [P] [US2] Integration test to verify multi-pass execution identical behavior in tests/integration/test_multipass_identical.py
- [X] T041 [P] [US2] Integration test to verify orchestration logs match pre-refactor in tests/integration/test_log_preservation.py

### Implementation for User Story 2

- [X] T042 [US2] Run full test suite and verify all tests pass without modification
- [X] T043 [US2] Fix any test failures caused by refactoring (interface mismatches, import errors)
- [X] T044 [US2] Verify error handling in orchestration modules returns structured results per contracts/interfaces.md
- [X] T045 [US2] Verify kernel handles orchestration module errors gracefully (fallback, retry, or propagate) in aeon/kernel/orchestrator.py
- [X] T046 [US2] Verify multi-pass execution produces identical results before/after refactoring
- [X] T047 [US2] Verify orchestration logs at phase boundaries match pre-refactor logs

**Checkpoint**: At this point, User Stories 1 AND 2 should be complete. All existing functionality preserved, all tests pass.

---

## Phase 5: User Story 3 - Establish Clean Module Boundaries (Priority: P2)

**Goal**: Ensure extracted orchestration modules have clean interfaces, are independently testable, and have no kernel dependencies

**Independent Test**: Verify extracted modules are independently testable, have no kernel dependencies (except state.py for data structures), and expose stable interfaces per contracts/interfaces.md.

**Dependencies**: Phase 4 complete

### Tests for User Story 3

- [X] T048 [P] [US3] Unit test for PhaseOrchestrator.phase_a_taskprofile_ttl() in tests/unit/orchestration/test_phases.py
- [X] T049 [P] [US3] Unit test for PhaseOrchestrator.phase_b_initial_plan_refinement() in tests/unit/orchestration/test_phases.py
- [X] T050 [P] [US3] Unit test for PhaseOrchestrator.phase_c_execute_batch() in tests/unit/orchestration/test_phases.py
- [X] T051 [P] [US3] Unit test for PhaseOrchestrator.phase_c_evaluate() in tests/unit/orchestration/test_phases.py
- [X] T052 [P] [US3] Unit test for PhaseOrchestrator.phase_c_refine() in tests/unit/orchestration/test_phases.py
- [X] T053 [P] [US3] Unit test for PhaseOrchestrator.phase_d_adaptive_depth() in tests/unit/orchestration/test_phases.py
- [X] T054 [P] [US3] Unit test for PlanRefinement.apply_actions() in tests/unit/orchestration/test_refinement.py
- [X] T055 [P] [US3] Unit test for StepPreparation.get_ready_steps() in tests/unit/orchestration/test_step_prep.py
- [X] T056 [P] [US3] Unit test for StepPreparation.populate_incoming_context() in tests/unit/orchestration/test_step_prep.py
- [X] T057 [P] [US3] Unit test for StepPreparation.populate_step_indices() in tests/unit/orchestration/test_step_prep.py
- [X] T058 [P] [US3] Unit test for TTLStrategy.create_expiration_response() in tests/unit/orchestration/test_ttl.py
- [X] T059 [P] [US3] Contract test to verify orchestration modules have no kernel imports (except state.py) in tests/contract/test_orchestration_interfaces.py

### Implementation for User Story 3

- [X] T060 [US3] Verify PhaseOrchestrator has no kernel imports (except state.py) in aeon/orchestration/phases.py
- [X] T061 [US3] Verify PlanRefinement has no kernel imports in aeon/orchestration/refinement.py
- [X] T062 [US3] Verify StepPreparation has no kernel imports in aeon/orchestration/step_prep.py
- [X] T063 [US3] Verify TTLStrategy has no kernel imports (except state.py) in aeon/orchestration/ttl.py
- [X] T064 [US3] Verify all orchestration module methods return structured results (success/error tuples) per contracts/interfaces.md
- [X] T065 [US3] Verify all orchestration module methods accept plan/state snapshots (no direct kernel state access)
- [X] T066 [US3] Verify kernel contains zero lines of phase orchestration logic, plan transformation logic, or heuristic decision logic in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1-3 should be complete. Clean module boundaries established, modules independently testable.

---

## Phase 6: User Story 4 - Document Refactoring Architecture (Priority: P3)

**Goal**: Document what was extracted, where it lives, interface contracts, and LOC measurements

**Independent Test**: Verify specification documents, interface contracts, and module design documents exist and are complete. Before/after LOC measurements are documented.

**Dependencies**: Phase 5 complete

### Tests for User Story 4

- [X] T067 [P] [US4] Verify specification document lists all extracted logic in specs/004-kernel-refactor/spec.md
- [X] T068 [P] [US4] Verify interface contracts are documented in specs/004-kernel-refactor/contracts/interfaces.md
- [X] T069 [P] [US4] Verify data models are documented in specs/004-kernel-refactor/data-model.md
- [X] T070 [P] [US4] Verify LOC measurements are documented showing reduction from ~1351 to ≤800 lines

### Implementation for User Story 4

- [X] T071 [US4] Document all extracted logic and new module boundaries in specs/004-kernel-refactor/spec.md
- [X] T072 [US4] Document interface contracts for all orchestration modules in specs/004-kernel-refactor/contracts/interfaces.md
- [X] T073 [US4] Document before/after LOC measurements with breakdown by file and method in specs/004-kernel-refactor/plan.md
- [X] T074 [US4] Update quickstart.md with final refactoring examples in specs/004-kernel-refactor/quickstart.md
- [X] T075 [US4] Document module dependencies and relationships in specs/004-kernel-refactor/data-model.md

**Checkpoint**: At this point, all User Stories 1-4 should be complete. Refactoring fully documented.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, performance testing, and cleanup

**Dependencies**: All user stories complete

### Performance & Verification

- [X] T076 [P] Performance test to verify no performance degradation in tests/integration/test_performance.py
- [X] T077 [P] Final LOC measurement and verification (kernel ≤800 LOC) in aeon/kernel/orchestrator.py and aeon/kernel/executor.py
- [X] T078 [P] Run full test suite one final time to verify all tests pass
- [X] T079 [P] Verify kernel behavior matches pre-refactor behavior in all execution scenarios

### Documentation & Cleanup

- [X] T080 [P] Update README.md if needed to reflect new orchestration module structure
- [X] T081 [P] Clean up any temporary files or debug code
- [X] T082 [P] Verify all imports are correct and no circular dependencies exist
- [X] T083 [P] Final code review to ensure all extracted logic follows interface contracts

---

## Dependencies

### User Story Completion Order

1. **User Story 1 (P1)** - Must complete first: Extracts logic and reduces LOC
2. **User Story 2 (P1)** - Depends on US1: Verifies behavioral preservation after extraction
3. **User Story 3 (P2)** - Depends on US2: Establishes clean boundaries and independent testability
4. **User Story 4 (P3)** - Depends on US3: Documents the refactoring architecture

### Parallel Execution Opportunities

**Within User Story 1**:
- T008-T011: Data model creation (can run in parallel)
- T014-T024: Extraction of different methods (can run in parallel for different modules)
- T026-T036: Kernel method replacements (can run in parallel after extractions complete)

**Within User Story 2**:
- T039-T041: Integration tests (can run in parallel)

**Within User Story 3**:
- T048-T059: Unit tests for different modules (can run in parallel)

**Within User Story 4**:
- T067-T070: Documentation verification (can run in parallel)

**Within Phase 7**:
- T076-T079: Performance and verification tests (can run in parallel)

## Implementation Strategy

### MVP Scope

**MVP**: User Story 1 only (Restore Constitutional Compliance)
- Extracts all orchestration logic to external modules
- Reduces kernel LOC to ≤800 (target <750)
- Establishes basic module structure

**Incremental Delivery**:
1. **Phase 1**: Extract Phase A/B/C/D logic (T014-T019) → Verify tests pass
2. **Phase 2**: Extract refinement logic (T020) → Verify tests pass
3. **Phase 3**: Extract step preparation logic (T021-T023) → Verify tests pass
4. **Phase 4**: Extract TTL expiration logic (T024) → Verify tests pass
5. **Phase 5**: Update kernel to use extracted modules (T025-T036) → Verify tests pass
6. **Phase 6**: Remove extracted methods from kernel (T037) → Verify LOC ≤800

### Testing Strategy

- **Unit Tests**: Test each orchestration module independently with mock inputs
- **Integration Tests**: Test kernel + orchestration modules together
- **Regression Tests**: Compare execution results before/after refactoring
- **Performance Tests**: Verify no performance degradation
- **Contract Tests**: Verify interface contracts are followed

### Success Criteria Validation

- ✅ **SC-001**: Kernel LOC ≤800 (target <750) - Verified by T038, T077
- ✅ **SC-002**: 100% of existing tests pass - Verified by T042, T078
- ✅ **SC-003**: Multi-pass execution identical behavior - Verified by T040, T046
- ✅ **SC-004**: Orchestration logs match pre-refactor - Verified by T041, T047
- ✅ **SC-005**: Extracted modules independently testable - Verified by T048-T059, T060-T063
- ✅ **SC-006**: Kernel contains zero phase/heuristic logic - Verified by T066
- ✅ **SC-007**: All interfaces documented - Verified by T068, T072
- ✅ **SC-008**: Before/after LOC documented - Verified by T007, T038, T070, T073
- ✅ **SC-009**: Unit tests for extracted logic - Verified by T048-T059
- ✅ **SC-010**: Kernel behavior matches pre-refactor - Verified by T039, T046, T079
- ✅ **SC-011**: Performance maintained - Verified by T076

---

## Summary

**Total Tasks**: 83 tasks
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 5 tasks
- **Phase 3 (US1)**: 27 tasks (13 tests + 14 implementation)
- **Phase 4 (US2)**: 9 tasks (3 tests + 6 implementation)
- **Phase 5 (US3)**: 19 tasks (12 tests + 7 implementation)
- **Phase 6 (US4)**: 9 tasks (4 tests + 5 implementation)
- **Phase 7 (Polish)**: 8 tasks

**Task Count per User Story**:
- **US1**: 27 tasks
- **US2**: 9 tasks
- **US3**: 19 tasks
- **US4**: 9 tasks

**Parallel Opportunities**: Multiple tasks can run in parallel within each phase (marked with [P])

**Independent Test Criteria**:
- **US1**: Measure kernel LOC ≤800 after refactoring
- **US2**: Run complete test suite, verify all tests pass without modification
- **US3**: Verify extracted modules are independently testable with no kernel dependencies
- **US4**: Verify all documentation exists and is complete

**Suggested MVP Scope**: User Story 1 only (Restore Constitutional Compliance) - 27 tasks

