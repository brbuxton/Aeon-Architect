# Tasks: Phase Transition Stabilization & Deterministic Context Propagation

**Input**: Design documents from `/specs/006-phase-transitions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Success criteria validation tests are included in Phase 9 to ensure all requirements are met. This sprint focuses on stabilization and correctness improvements to existing code.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/` package at repository root
- **Tests**: `tests/` at repository root
- All paths follow plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Verify project structure exists per implementation plan in aeon/
- [ ] T002 [P] Verify Python 3.11+ project configuration in pyproject.toml
- [ ] T003 [P] Verify pydantic>=2.0.0 dependency in requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create PhaseTransitionContract Pydantic model in aeon/orchestration/phases.py
- [ ] T005 [P] Create ContextPropagationSpecification Pydantic model in aeon/orchestration/phases.py
- [ ] T006 [P] Add PhaseTransitionError exception class in aeon/exceptions.py
- [ ] T007 [P] Add ContextPropagationError exception class in aeon/exceptions.py
- [ ] T008 [P] Add TTLExpiredError exception class in aeon/exceptions.py (if not exists)
- [ ] T008a [P] Verify ExecutionPass validation logic separation: Ensure ExecutionPass validation functions are implemented in aeon/validation/execution_pass.py (new module), NOT in aeon/kernel/state.py, per Constitution Principle I (Kernel Minimalism)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Explicit Phase Transition Contracts (Priority: P1) 🎯 MVP

**Goal**: Define explicit, testable contracts for each phase transition (A→B, B→C, C→D, D→A/B) that define required inputs, guaranteed outputs, invariants, and enumerated failure conditions.

**Independent Test**: Can be fully tested by executing phase transitions with valid and invalid inputs, verifying that contracts are enforced (valid inputs produce valid outputs, invalid inputs produce structured errors), and confirming that all failure conditions are enumerated and handled. The test delivers value by proving phase transitions are deterministic and testable.

### Implementation for User Story 1

- [ ] T009 [US1] Define A→B phase transition contract constant in aeon/orchestration/phases.py
- [ ] T010 [US1] Define B→C phase transition contract constant in aeon/orchestration/phases.py
- [ ] T011 [US1] Define C→D phase transition contract constant in aeon/orchestration/phases.py
- [ ] T012 [US1] Define D→A/B phase transition contract constant in aeon/orchestration/phases.py
- [ ] T013 [US1] Implement get_phase_transition_contract function in aeon/orchestration/phases.py
- [ ] T014 [US1] Implement validate_phase_transition_contract function in aeon/orchestration/phases.py
- [ ] T015 [US1] Implement enforce_phase_transition_contract function in aeon/orchestration/phases.py
- [ ] T016 [US1] Integrate contract validation into A→B transition in aeon/orchestration/phases.py
- [ ] T017 [US1] Integrate contract validation into B→C transition in aeon/orchestration/phases.py
- [ ] T018 [US1] Integrate contract validation into C→D transition in aeon/orchestration/phases.py
- [ ] T019 [US1] Integrate contract validation into D→A/B transition in aeon/orchestration/phases.py
- [ ] T020 [US1] Add retry logic for retryable phase transition errors in aeon/orchestration/phases.py
- [ ] T020a [US1] Implement LLM provider failure handling per FR-011 by detecting provider errors at every LLM call site, retrying once for retryable errors, and aborting with structured error for non-retryable errors in aeon/orchestration/phases.py.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Deterministic Context Propagation (Priority: P1)

**Goal**: Ensure every LLM call receives complete and accurate context including task profile, plan goal and step metadata, previous outputs, refinement changes, evaluation results, pass_number, phase, TTL remaining, correlation_id, and adaptive depth decision inputs.

**Independent Test**: Can be fully tested by instrumenting LLM calls to capture all context passed to prompts, verifying that required fields (task_profile, plan goal, step metadata, previous outputs, refinement changes, evaluation results, pass_number, phase, TTL remaining, correlation_id, adaptive depth inputs) are present and non-null, and confirming that context is correctly propagated between phases. The test delivers value by proving LLM calls have complete context for correct reasoning.

### Implementation for User Story 2

- [ ] T021 [US2] Define Phase A context propagation specification constant in aeon/orchestration/phases.py
- [ ] T022 [US2] Define Phase B context propagation specification constant in aeon/orchestration/phases.py
- [ ] T023 [US2] Define Phase C context propagation specification constant in aeon/orchestration/phases.py
- [ ] T024 [US2] Define Phase D context propagation specification constant in aeon/orchestration/phases.py
- [ ] T025 [US2] Implement get_context_propagation_specification function in aeon/orchestration/phases.py
- [ ] T026 [US2] Implement validate_context_propagation function in aeon/orchestration/phases.py
- [ ] T027 [US2] Implement build_llm_context function in aeon/orchestration/phases.py
- [ ] T028 [US2] Integrate context validation before Phase A LLM calls in aeon/orchestration/phases.py
- [ ] T029 [US2] Integrate context validation before Phase B LLM calls in aeon/orchestration/phases.py
- [ ] T030 [US2] Integrate context validation before Phase C LLM calls in aeon/orchestration/phases.py
- [ ] T031 [US2] Integrate context validation before Phase D LLM calls in aeon/orchestration/phases.py
- [ ] T032 [US2] Ensure correlation_id and execution_start_timestamp are passed unchanged in aeon/orchestration/phases.py
- [ ] T033 [US2] Update Phase A to propagate minimal context (request, pass_number=0, phase="A", TTL remaining, correlation_id, execution_start_timestamp) in aeon/orchestration/phases.py
- [ ] T034 [US2] Update Phase B to propagate context (request, task_profile, initial_plan goal and step metadata, pass_number=0, phase="B", TTL remaining, correlation_id, execution_start_timestamp) in aeon/orchestration/phases.py
- [ ] T035 [US2] Update Phase C execution to propagate context (request, task_profile, refined_plan goal and step metadata, pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp, previous outputs, refinement changes) in aeon/orchestration/phases.py
- [ ] T036 [US2] Update Phase C evaluation to propagate context (request, task_profile, current plan state, execution_results, pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp) in aeon/orchestration/phases.py
- [ ] T037 [US2] Update Phase C refinement to propagate context (request, task_profile, current plan state, execution_results, evaluation_results, pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp, previous outputs) in aeon/orchestration/phases.py
- [ ] T038 [US2] Update Phase D to propagate context (request, task_profile, evaluation_results, plan state, pass_number, phase="D", TTL remaining, correlation_id, execution_start_timestamp, adaptive depth decision inputs) in aeon/orchestration/phases.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Prompt Context Alignment (Priority: P2)

**Goal**: Verify that all prompt schema keys are either populated by the orchestrator/phases or removed as unused, and no prompt carries null semantic inputs that would cause reasoning failures.

**Independent Test**: Can be fully tested by reviewing all prompt schemas, verifying that all required keys are populated by orchestrator/phases, identifying unused keys that should be removed, and confirming that no prompt contains null semantic inputs. The test delivers value by proving prompt schemas are correct and complete.

### Implementation for User Story 3

- [ ] T039 [US3] Review all prompt schemas in aeon/plan/prompts.py
- [ ] T040 [US3] Review all prompt schemas in aeon/orchestration/phases.py
- [ ] T041 [US3] Review all prompt schemas in aeon/orchestration/refinement.py
- [ ] T042 [US3] Identify unused keys in prompt schemas across all modules
- [ ] T043 [US3] Remove unused keys or document as optional/future use in aeon/plan/prompts.py
- [ ] T044 [US3] Remove unused keys or document as optional/future use in aeon/orchestration/phases.py
- [ ] T045 [US3] Remove unused keys or document as optional/future use in aeon/orchestration/refinement.py
- [ ] T046 [US3] Ensure orchestrator/phases populate all required keys in prompt schemas
- [ ] T047 [US3] Add validation to prevent null semantic inputs in prompt construction

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - TTL Boundary Behavior (Priority: P1)

**Goal**: Verify that TTL decrements exactly once per cycle, TTL behavior at boundaries (1, 0, expiration) is specified and correct, and TTLExpirationResponse is used as the error mechanism.

**Independent Test**: Can be fully tested by executing tasks with various TTL values (1, 2, 10), verifying that TTL decrements exactly once per cycle, confirming correct behavior at TTL=1, TTL=0, and expiration boundaries, and validating that TTLExpirationResponse is used for all expiration cases. The test delivers value by proving TTL behavior is deterministic and correct.

### Implementation for User Story 4

- [ ] T048 [US4] Implement TTL decrement behavior so TTL_remaining decrements exactly once at the end of each complete A→B→C→D cycle per FR-025.
- [ ] T049 [US4] Implement check_ttl_before_phase_entry function in aeon/orchestration/ttl.py
- [ ] T050 [US4] Implement check_ttl_after_llm_call function in aeon/orchestration/ttl.py
- [ ] T051 [US4] Implement decrement_ttl_per_cycle function in aeon/orchestration/ttl.py
- [ ] T052 [US4] Integrate TTL check before phase entry in aeon/orchestration/phases.py
- [ ] T053 [US4] Integrate TTL check after each LLM call within phase in aeon/orchestration/phases.py
- [ ] T054 [US4] Ensure TTLExpirationResponse is generated with expiration_type="phase_boundary" when TTL=0 at phase boundary in aeon/orchestration/ttl.py
- [ ] T055 [US4] Ensure TTLExpirationResponse is generated with expiration_type="mid_phase" when TTL=0 mid-phase in aeon/orchestration/ttl.py
- [ ] T056 [US4] Fix TTL behavior at TTL=1 boundary (allow cycle to complete) in aeon/orchestration/ttl.py
- [ ] T057 [US4] Remove any heuristic TTL adjustments in aeon/orchestration/ttl.py
- [ ] T058 [US4] Ensure TTL decrement occurs in Phase D completion in aeon/orchestration/phases.py

**Checkpoint**: At this point, User Stories 1, 2, 3, AND 4 should all work independently

---

## Phase 7: User Story 5 - ExecutionPass Consistency (Priority: P2)

**Goal**: Verify that ExecutionPass objects are consistent across the loop, with required fields populated before each phase, required fields populated after each phase, and invariants maintained for merging execution_results and evaluation_results.

**Independent Test**: Can be fully tested by executing a multi-pass task, verifying that each ExecutionPass has required fields populated before phase entry, required fields populated after phase exit, and invariants maintained (execution_results and evaluation_results are correctly merged, refinement_changes are correctly applied). The test delivers value by proving ExecutionPass consistency and completeness.

### Implementation for User Story 5

- [ ] T059 [US5] Ensure ExecutionPass and ExecutionHistory remain data-only models in aeon/kernel/state.py with no validation or orchestration logic.
- [ ] T060 [US5] Add ExecutionPass validation functions (before-phase and after-phase) in aeon/validation/execution_pass.py.
- [ ] T061 [US5] Add ExecutionPass invariant validation functions in aeon/validation/execution_pass.py.
- [ ] T062 [US5] Wire ExecutionPass validation calls into phase transitions from aeon/orchestration/phases.py using aeon/validation/execution_pass.py.
- [ ] T063 [US5] Ensure all ExecutionPass validation errors surface as structured errors without adding logic to aeon/kernel/state.py.
- [ ] T064 [US5] Integrate ExecutionPass validation before Phase A entry in aeon/orchestration/phases.py
- [ ] T065 [US5] Integrate ExecutionPass validation before Phase B entry in aeon/orchestration/phases.py
- [ ] T066 [US5] Integrate ExecutionPass validation before Phase C entry in aeon/orchestration/phases.py
- [ ] T067 [US5] Integrate ExecutionPass validation before Phase D entry in aeon/orchestration/phases.py
- [ ] T068 [US5] Integrate ExecutionPass validation after Phase A exit in aeon/orchestration/phases.py
- [ ] T069 [US5] Integrate ExecutionPass validation after Phase B exit in aeon/orchestration/phases.py
- [ ] T070 [US5] Integrate ExecutionPass validation after Phase C exit in aeon/orchestration/phases.py
- [ ] T071 [US5] Integrate ExecutionPass validation after Phase D exit in aeon/orchestration/phases.py
- [ ] T072 [US5] Ensure execution_results and evaluation_results are correctly merged in aeon/orchestration/phases.py
- [ ] T073 [US5] Ensure refinement_changes are correctly applied to plan_state in aeon/orchestration/phases.py

**Checkpoint**: At this point, User Stories 1, 2, 3, 4, AND 5 should all work independently

---

## Phase 8: User Story 6 - Phase Boundary Logging (Priority: P2)

**Goal**: Review logs showing phase entry, phase exit, deterministic state snapshots, TTL snapshots, and structured error logs for every phase boundary.

**Independent Test**: Can be fully tested by executing a multi-pass task, verifying that every phase boundary produces phase entry log, phase exit log, deterministic state snapshot, TTL snapshot, and structured error log (if failure occurs), and confirming that all logs use existing logging schema. The test delivers value by proving phase transitions are fully observable.

### Implementation for User Story 6

- [ ] T074 [US6] Implement log_phase_entry function in aeon/observability/logger.py
- [ ] T075 [US6] Implement log_phase_exit function in aeon/observability/logger.py
- [ ] T076 [US6] Implement log_state_snapshot function in aeon/observability/logger.py
- [ ] T077 [US6] Implement log_ttl_snapshot function in aeon/observability/logger.py
- [ ] T078 [US6] Implement log_phase_transition_error function in aeon/observability/logger.py
- [ ] T079 [US6] Add PhaseEntryLog model to aeon/observability/models.py (if needed)
- [ ] T080 [US6] Add PhaseExitLog model to aeon/observability/models.py (if needed)
- [ ] T081 [US6] Add StateSnapshotLog model to aeon/observability/models.py (if needed)
- [ ] T082 [US6] Add TTLSnapshotLog model to aeon/observability/models.py (if needed)
- [ ] T083 [US6] Add PhaseTransitionErrorLog model to aeon/observability/models.py (if needed)
- [ ] T084 [US6] Integrate phase entry logging in Phase A in aeon/orchestration/phases.py
- [ ] T085 [US6] Integrate phase entry logging in Phase B in aeon/orchestration/phases.py
- [ ] T086 [US6] Integrate phase entry logging in Phase C in aeon/orchestration/phases.py
- [ ] T087 [US6] Integrate phase entry logging in Phase D in aeon/orchestration/phases.py
- [ ] T088 [US6] Integrate phase exit logging in Phase A in aeon/orchestration/phases.py
- [ ] T089 [US6] Integrate phase exit logging in Phase B in aeon/orchestration/phases.py
- [ ] T090 [US6] Integrate phase exit logging in Phase C in aeon/orchestration/phases.py
- [ ] T091 [US6] Integrate phase exit logging in Phase D in aeon/orchestration/phases.py
- [ ] T092 [US6] Integrate state snapshot logging before and after Phase A transition in aeon/orchestration/phases.py
- [ ] T093 [US6] Integrate state snapshot logging before and after Phase B transition in aeon/orchestration/phases.py
- [ ] T094 [US6] Integrate state snapshot logging before and after Phase C transition in aeon/orchestration/phases.py
- [ ] T095 [US6] Integrate state snapshot logging before and after Phase D transition in aeon/orchestration/phases.py
- [ ] T096 [US6] Integrate TTL snapshot logging at Phase A boundary in aeon/orchestration/phases.py
- [ ] T097 [US6] Integrate TTL snapshot logging at Phase B boundary in aeon/orchestration/phases.py
- [ ] T098 [US6] Integrate TTL snapshot logging at Phase C boundary in aeon/orchestration/phases.py
- [ ] T099 [US6] Integrate TTL snapshot logging at Phase D boundary in aeon/orchestration/phases.py
- [ ] T100 [US6] Integrate structured error logging for Phase A failures in aeon/orchestration/phases.py
- [ ] T101 [US6] Integrate structured error logging for Phase B failures in aeon/orchestration/phases.py
- [ ] T102 [US6] Integrate structured error logging for Phase C failures in aeon/orchestration/phases.py
- [ ] T103 [US6] Integrate structured error logging for Phase D failures in aeon/orchestration/phases.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 9: Validation & Success Criteria

**Purpose**: Validate that all success criteria (SC-001 through SC-006) are met through comprehensive testing

- [ ] T116 Add test ensuring identical inputs produce identical A→B→C→D phase sequences across two executions.
- [ ] T117 Add test ensuring identical inputs produce identical phase outputs (excluding timestamps and UUIDv4) across two executions.
- [ ] T118 Add test ensuring identical invalid inputs produce identical failure phase and identical structured error outputs.
- [ ] T119 Add test asserting all MUST-HAVE context fields are present and non-null in every LLM call.
- [ ] T120 Add test asserting all MUST-PASS-UNCHANGED fields remain unchanged through A→B→C→D transitions.
- [ ] T121 Add test asserting no PROHIBITED fields are present in any phase context.
- [ ] T122 Add test asserting TTL decrements exactly once after a complete A→B→C→D cycle.
- [ ] T123 Add test asserting TTL=1 halts execution at the next cycle boundary with TTLExpirationResponse.
- [ ] T124 Add test asserting TTL expiration mid-phase immediately halts execution and emits TTLExpirationResponse.
- [ ] T125 Add test asserting ExecutionPass contains all required before-phase fields for each phase.
- [ ] T126 Add test asserting ExecutionPass contains all required after-phase fields following each phase.
- [ ] T127 Add test asserting all ExecutionPass invariant fields remain unchanged throughout the pass.
- [ ] T128 Add test asserting each enumerated failure condition triggers the correct structured error defined in the phase contract.
- [ ] T129 Add test asserting unenumerated or malformed failures still produce the standard structured error format.
- [ ] T130 Add golden-path integration test asserting a simple task completes the full A→B→C→D loop without errors.
- [ ] T131 Add golden-path failure test asserting a controlled failure triggers the correct phase's structured error and valid logs.

**Checkpoint**: All success criteria validated - feature ready for Sprint 7 gate

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Code cleanup, refactoring, and improvements that affect multiple user stories

- [ ] T104 [P] Verify all phase transitions use explicit contracts
- [ ] T105 [P] Verify all LLM calls receive complete context
- [ ] T106 [P] Verify TTL behavior is correct at all boundaries
- [ ] T107 [P] Verify ExecutionPass consistency across all phases
- [ ] T108 [P] Verify phase boundary logging is complete
- [ ] T109 [P] Code cleanup and refactoring in aeon/orchestration/phases.py
- [ ] T110 [P] Code cleanup and refactoring in aeon/orchestration/ttl.py
- [ ] T111 [P] Code cleanup and refactoring in aeon/orchestration/refinement.py
- [ ] T112 [P] Code cleanup and refactoring in aeon/observability/logger.py
- [ ] T113 [P] Code cleanup and refactoring in aeon/exceptions.py
- [ ] T114 [P] Code cleanup and refactoring in aeon/kernel/state.py
- [ ] T115 Run quickstart.md validation examples


---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 9)**: Depends on all desired user stories being complete - Validates success criteria
- **Polish (Phase 10)**: Depends on Validation phase completion - Final cleanup and improvements

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on User Story 2 (context propagation must be complete before prompt alignment)
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Models/contracts before validation functions
- Validation functions before integration
- Integration before error handling
- Core implementation before logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1, 2, 4 can start in parallel (all P1, no dependencies)
- User Stories 3, 5, 6 can start after their dependencies are met
- All contract definitions within a story marked [P] can run in parallel
- All logging integrations within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all contract definitions together:
Task: "Define A→B phase transition contract constant in aeon/orchestration/phases.py"
Task: "Define B→C phase transition contract constant in aeon/orchestration/phases.py"
Task: "Define C→D phase transition contract constant in aeon/orchestration/phases.py"
Task: "Define D→A/B phase transition contract constant in aeon/orchestration/phases.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all specification definitions together:
Task: "Define Phase A context propagation specification constant in aeon/orchestration/phases.py"
Task: "Define Phase B context propagation specification constant in aeon/orchestration/phases.py"
Task: "Define Phase C context propagation specification constant in aeon/orchestration/phases.py"
Task: "Define Phase D context propagation specification constant in aeon/orchestration/phases.py"
```

---

## Parallel Example: User Story 6

```bash
# Launch all logging function implementations together:
Task: "Implement log_phase_entry function in aeon/observability/logger.py"
Task: "Implement log_phase_exit function in aeon/observability/logger.py"
Task: "Implement log_state_snapshot function in aeon/observability/logger.py"
Task: "Implement log_ttl_snapshot function in aeon/observability/logger.py"
Task: "Implement log_phase_transition_error function in aeon/observability/logger.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 4 Only - All P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Phase Transition Contracts)
4. Complete Phase 4: User Story 2 (Context Propagation)
5. Complete Phase 6: User Story 4 (TTL Boundary Behavior)
6. Complete Phase 9: Validation & Success Criteria (validate P1 stories)
7. **STOP and VALIDATE**: All P1 success criteria met
8. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Phase Contracts MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Context Propagation MVP!)
4. Add User Story 4 → Test independently → Deploy/Demo (TTL Behavior MVP!)
5. Add User Story 3 → Test independently → Deploy/Demo (Prompt Alignment)
6. Add User Story 5 → Test independently → Deploy/Demo (ExecutionPass Consistency)
7. Add User Story 6 → Test independently → Deploy/Demo (Phase Boundary Logging)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Phase Transition Contracts)
   - Developer B: User Story 2 (Context Propagation)
   - Developer C: User Story 4 (TTL Boundary Behavior)
3. After P1 stories complete:
   - Developer A: User Story 3 (Prompt Context Alignment)
   - Developer B: User Story 5 (ExecutionPass Consistency)
   - Developer C: User Story 6 (Phase Boundary Logging)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All improvements remain outside the kernel and use existing models without expansion beyond bug fixes
- No new heuristic frameworks, fallback strategies, or architectural subsystems may be introduced
- All behavior must be deterministic for identical inputs

---

## Summary

**Total Task Count**: 131 tasks

**Task Count Per User Story**:
- User Story 1 (P1): 13 tasks
- User Story 2 (P1): 18 tasks
- User Story 3 (P2): 9 tasks
- User Story 4 (P1): 11 tasks
- User Story 5 (P2): 15 tasks
- User Story 6 (P2): 30 tasks
- Setup: 3 tasks
- Foundational: 5 tasks
- Validation: 16 tasks
- Polish: 12 tasks

**Parallel Opportunities Identified**:
- Setup phase: 2 tasks can run in parallel
- Foundational phase: 4 tasks can run in parallel
- User Story 1: 4 contract definitions can run in parallel
- User Story 2: 4 specification definitions can run in parallel
- User Story 6: 5 logging function implementations can run in parallel
- User Stories 1, 2, 4 can be worked on in parallel after Foundational phase (all P1, no dependencies)

**Independent Test Criteria for Each Story**:
- US1: Execute phase transitions with valid/invalid inputs, verify contracts enforced
- US2: Instrument LLM calls, verify all required context fields present and non-null
- US3: Review all prompt schemas, verify keys populated or removed, no null inputs
- US4: Execute tasks with various TTL values, verify decrement once per cycle, correct boundary behavior
- US5: Execute multi-pass task, verify ExecutionPass fields populated before/after phases, invariants maintained
- US6: Execute multi-pass task, verify all phase boundaries produce required logs

**Suggested MVP Scope**: User Stories 1, 2, and 4 (all P1 priorities) - Phase Transition Contracts, Context Propagation, and TTL Boundary Behavior. These three stories provide the foundational stabilization needed for Sprint 7 (Prompt Contracts).

**Format Validation**: ✅ All tasks follow the checklist format (checkbox, ID, labels where appropriate, file paths)

