# Tasks: Sprint 2 - Adaptive Reasoning Engine

**Input**: Design documents from `/specs/002-adaptive-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included to meet constitutional requirement for test coverage and behavioral validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/` package at repository root
- **Tests**: `tests/` at repository root
- All paths follow existing project structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Verify Python 3.11+ environment and dependencies in requirements.txt
- [ ] T002 [P] Review existing project structure in aeon/ package
- [ ] T003 [P] Verify test infrastructure (pytest, coverage) in tests/ directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MANDATORY kernel refactoring that MUST be complete before ANY Sprint 2 user story can be implemented

**⚠️ CRITICAL**: No Sprint 2 user story work can begin until this phase is complete

### Kernel Refactoring - Analysis Phase

- [ ] T004 Measure current LOC of aeon/kernel/orchestrator.py and aeon/kernel/executor.py
- [ ] T005 Audit aeon/kernel/orchestrator.py to identify non-orchestration logic
- [ ] T006 Audit aeon/kernel/executor.py to identify non-orchestration logic
- [ ] T007 Document extractable functions, classes, or modules that can be moved externally
- [ ] T008 Identify reduction targets to bring combined LOC below 700 lines

### Kernel Refactoring - Extraction Phase

- [ ] T009 [P] Move non-orchestration utility functions from orchestrator.py to appropriate external modules
- [ ] T010 [P] Move non-orchestration utility functions from executor.py to appropriate external modules
- [ ] T011 [P] Extract data transformation logic to external modules if found in kernel
- [ ] T012 [P] Extract validation helpers to external modules if found in kernel
- [ ] T013 Verify all extracted code maintains clean interfaces
- [ ] T014 Preserve all existing functionality and interfaces during extraction

### Kernel Refactoring - Validation Phase

- [ ] T015 Run full regression test suite in tests/ to confirm no behavioral changes
- [ ] T016 Verify combined LOC of aeon/kernel/orchestrator.py and aeon/kernel/executor.py is below 700 lines
- [ ] T017 Confirm all interfaces remain unchanged (no breaking changes)
- [ ] T018 Document refactoring changes with before/after LOC measurements

**Checkpoint**: Kernel refactoring complete - LOC < 700, all tests pass, no behavioral drift. Sprint 2 user story implementation can now begin.

---

## Phase 3: User Story 5 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

**Goal**: Implement semantic validation layer that validates step specificity, logical relevance, do/say mismatches, hallucinated tools, and consistency violations. This is foundational for other Sprint 2 features.

**Independent Test**: Generate a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verify that the semantic validation layer detects these issues, classifies them, assigns severity scores, and proposes semantic repairs.

### Implementation for User Story 5

- [ ] T019 [P] [US5] Create ValidationIssue model in aeon/validation/semantic_models.py
- [ ] T020 [P] [US5] Create SemanticValidationReport model in aeon/validation/semantic_models.py
- [ ] T021 [P] [US5] Create semantic validation interface in aeon/validation/semantic_interface.py
- [ ] T022 [US5] Implement step specificity validator in aeon/validation/semantic_validator.py
- [ ] T023 [US5] Implement logical relevance validator in aeon/validation/semantic_validator.py
- [ ] T024 [US5] Implement do/say mismatch detector in aeon/validation/semantic_validator.py
- [ ] T025 [US5] Implement hallucinated tool detector in aeon/validation/semantic_validator.py
- [ ] T026 [US5] Implement internal consistency checker in aeon/validation/semantic_validator.py
- [ ] T027 [US5] Implement cross-phase consistency validator in aeon/validation/semantic_validator.py
- [ ] T028 [US5] Implement issue classification and severity scoring in aeon/validation/semantic_validator.py
- [ ] T029 [US5] Implement semantic repair proposal generator in aeon/validation/semantic_validator.py
- [ ] T030 [US5] Integrate semantic validator with tool registry for tool existence checks
- [ ] T031 [US5] Add logging for semantic validation operations in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 5 should be fully functional and testable independently. Semantic validation can detect issues and produce validation reports.

---

## Phase 4: User Story 3 - Convergence Detection and Completion Assessment (Priority: P1)

**Goal**: Implement convergence engine that determines whether tasks are finished through completeness, coherence, and consistency checks. This directly controls termination condition for multi-pass execution.

**Independent Test**: Execute a task through multiple passes and verify that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met, returning convergence status (true/false), reason codes, and evaluation metadata.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Create ConvergenceAssessment model in aeon/convergence/models.py
- [ ] T033 [P] [US3] Create convergence engine interface in aeon/convergence/interface.py
- [ ] T034 [US3] Implement completeness checker in aeon/convergence/engine.py
- [ ] T035 [US3] Implement coherence checker in aeon/convergence/engine.py
- [ ] T036 [US3] Implement cross-artifact consistency checker in aeon/convergence/engine.py
- [ ] T037 [US3] Integrate convergence engine with semantic validation layer to consume validation reports
- [ ] T038 [US3] Implement contradiction, omission, and hallucination detection using semantic validation input
- [ ] T039 [US3] Implement configurable convergence criteria with sensible defaults in aeon/convergence/engine.py
- [ ] T040 [US3] Implement reason code generation for convergence status in aeon/convergence/engine.py
- [ ] T041 [US3] Implement evaluation metadata generation (completeness score, coherence score, detected issues) in aeon/convergence/engine.py
- [ ] T042 [US3] Handle conflicting convergence criteria (complete but incoherent, etc.) with reason codes
- [ ] T043 [US3] Add logging for convergence assessments in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently. Convergence engine can evaluate execution results and determine convergence status.

---

## Phase 5: User Story 1 - Multi-Pass Execution with Convergence (Priority: P1) 🎯 MVP

**Goal**: Implement multi-pass execution loop with deterministic phase boundaries (plan → execute → evaluate → refine → re-execute → converge → stop). This is the foundational transformation from single-pass to multi-pass execution.

**Independent Test**: Submit a complex, ambiguous task (e.g., "design a system architecture for a web application with user authentication") and verify that Aeon executes multiple passes (plan → execute → evaluate → refine → re-execute) until convergence is achieved or TTL expires.

### Implementation for User Story 1

- [ ] T044 [P] [US1] Create ExecutionPass model in aeon/kernel/multipass_models.py
- [ ] T045 [P] [US1] Create RefinementAction model in aeon/kernel/multipass_models.py
- [ ] T046 [US1] Upgrade existing orchestrator.py from single-pass to multi-pass loop architecture in aeon/kernel/orchestrator.py
- [ ] T047 [US1] Implement phase boundary management (plan → execute → evaluate → refine → re-execute) in aeon/kernel/orchestrator.py
- [ ] T048 [US1] Integrate convergence engine into evaluate phase in aeon/kernel/orchestrator.py
- [ ] T049 [US1] Integrate semantic validation into evaluate phase in aeon/kernel/orchestrator.py
- [ ] T050 [US1] Implement refinement phase with attempt limits (3 per fragment, 10 global) in aeon/kernel/orchestrator.py
- [ ] T051 [US1] Integrate supervisor repair into refinement phase in aeon/kernel/orchestrator.py
- [ ] T052 [US1] Implement TTL expiration handling at phase boundaries in aeon/kernel/orchestrator.py
- [ ] T053 [US1] Implement mid-phase TTL expiration at safe step boundaries in aeon/kernel/orchestrator.py
- [ ] T054 [US1] Implement termination logic (convergence OR TTL expiration) in aeon/kernel/orchestrator.py
- [ ] T055 [US1] Implement TTL-expired result formatting with metadata in aeon/kernel/orchestrator.py
- [ ] T056 [US1] Implement deterministic phase sequence enforcement in aeon/kernel/orchestrator.py
- [ ] T057 [US1] Handle supervisor repair failures during refinement phase in aeon/kernel/orchestrator.py
- [ ] T058 [US1] Preserve declarative plan nature during refinement in aeon/kernel/orchestrator.py
- [ ] T059 [US1] Add logging for multi-pass execution phases in aeon/observability/logger.py
- [ ] T060 [US1] Update kernel orchestrator to use multi-pass loop for complex tasks

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Multi-pass execution loop can iterate through passes until convergence or TTL expiration.

---

## Phase 6: User Story 2 - Recursive Planning and Plan Refinement (Priority: P1)

**Goal**: Implement recursive planning that detects missing details, generates follow-up questions, creates subplans for complex steps, and refines plan fragments without discarding the entire plan.

**Independent Test**: Submit an ambiguous task (e.g., "build a REST API") and verify that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments, and automatically incorporates semantic validation into the refinement process.

### Implementation for User Story 2

- [ ] T061 [P] [US2] Create Subplan model in aeon/plan/recursive_models.py
- [ ] T062 [P] [US2] Create recursive planner interface in aeon/plan/recursive_interface.py
- [ ] T063 [US2] Implement ambiguous fragment detector in aeon/plan/recursive_planner.py
- [ ] T064 [US2] Implement low-specificity fragment detector in aeon/plan/recursive_planner.py
- [ ] T065 [US2] Implement follow-up question generator in aeon/plan/recursive_planner.py
- [ ] T066 [US2] Implement subplan creator for complex steps in aeon/plan/recursive_planner.py
- [ ] T067 [US2] Implement nested step generator in aeon/plan/recursive_planner.py
- [ ] T068 [US2] Implement partial plan fragment rewrite in aeon/plan/recursive_planner.py
- [ ] T069 [US2] Integrate semantic validation into recursive planning flow in aeon/plan/recursive_planner.py
- [ ] T070 [US2] Implement plan structure preservation during refinement in aeon/plan/recursive_planner.py
- [ ] T071 [US2] Implement per-fragment refinement attempt limits (3 attempts) in aeon/plan/recursive_planner.py
- [ ] T072 [US2] Implement global refinement attempt limit (10 total) in aeon/plan/recursive_planner.py
- [ ] T073 [US2] Implement manual intervention marking for fragments at limit in aeon/plan/recursive_planner.py
- [ ] T074 [US2] Implement nesting depth limit enforcement of 5 levels in aeon/plan/recursive_planner.py
- [ ] T075 [US2] Implement graceful failure handling for depth limit exceeded in aeon/plan/recursive_planner.py
- [ ] T076 [US2] Implement conflict resolution between semantic validation and recursive planner refinements in aeon/plan/recursive_planner.py
- [ ] T077 [US2] Ensure plans remain declarative (JSON/YAML) during recursive planning in aeon/plan/recursive_planner.py
- [ ] T078 [US2] Add logging for recursive planning operations in aeon/observability/logger.py
- [ ] T079 [US2] Integrate recursive planner with multi-pass loop refinement phase

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently. Recursive planning can detect ambiguities, create subplans, and refine plan fragments.

---

## Phase 7: User Story 4 - Adaptive Reasoning Depth Based on Task Complexity (Priority: P2)

**Goal**: Implement adaptive depth heuristics that adjust reasoning depth, TTL allocations, and processing strategies based on detected complexity, ambiguity, or uncertainty levels.

**Independent Test**: Submit both simple tasks (e.g., "add two numbers") and complex tasks (e.g., "design a distributed system architecture") and verify that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on detected complexity.

### Implementation for User Story 4

- [ ] T080 [P] [US4] Create AdaptiveDepthConfiguration model in aeon/adaptive/models.py
- [ ] T081 [P] [US4] Create adaptive depth interface in aeon/adaptive/interface.py
- [ ] T082 [US4] Implement TaskProfile inference engine and define TaskProfile schema and interface contract in aeon/adaptive/heuristics.py
- [ ] T082a [US4] Create TaskProfile model with fields: profile_version, reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference in aeon/adaptive/models.py
- [ ] T082b [US4] Implement TaskProfile versioning and update triggers at pass boundaries in aeon/adaptive/heuristics.py
- [ ] T082c [US4] Add recording of TaskProfile version transitions to execution history, including initial_profile_version, updated_profile_versions[], and revision_reason metadata.
- [ ] T083 [US4] Implement information_sufficiency dimension extraction in aeon/adaptive/heuristics.py
- [ ] T085 [US4] Implement token-pattern analysis for complexity indicators in aeon/adaptive/heuristics.py
- [ ] T086 [US4] Implement TTL allocation based on TaskProfile reasoning_depth and information_sufficiency in aeon/adaptive/heuristics.py
- [ ] T087 [US4] Implement reasoning_depth selection based on TaskProfile in aeon/adaptive/heuristics.py
- [ ] T088 [US4] Implement global TTL and resource cap enforcement in aeon/adaptive/heuristics.py
- [ ] T089 [US4] Implement bidirectional TTL adjustment (increase and decrease) in aeon/adaptive/heuristics.py
- [ ] T090 [US4] Implement complexity assessment revision during execution in aeon/adaptive/heuristics.py
- [ ] T091 [US4] Integrate with semantic validation for complexity indicators in aeon/adaptive/heuristics.py
- [ ] T092 [US4] Integrate with convergence engine for depth decisions in aeon/adaptive/heuristics.py
- [ ] T093 [US4] Integrate with recursive planner for depth decisions in aeon/adaptive/heuristics.py
- [ ] T094 [US4] Implement adjustment reason tracking in aeon/adaptive/heuristics.py
- [ ] T095 [US4] Add logging for adaptive depth adjustments in aeon/observability/logger.py
- [ ] T096 [US4] Integrate adaptive depth with multi-pass loop for TTL allocation

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently. Adaptive depth can detect complexity and adjust reasoning depth and TTL allocations.

---

## Phase 8: User Story 6 - Inspect Multi-Pass Execution (Priority: P2)

**Goal**: Implement execution inspection capability that provides structured history of passes including plans, refinements, and convergence assessments for debugging and tuning.

**Independent Test**: Execute a multi-pass task, complete it (converged or TTL expired), and verify that developers can access and review a structured execution history containing: pass sequence with phase transitions, plan state snapshots per pass, refinement actions and changes, convergence assessments with scores and reason codes, and semantic validation reports.

### Implementation for User Story 6

- [ ] T097 [P] [US6] Create ExecutionHistory model in aeon/kernel/history_models.py
- [ ] T098 [P] [US6] Create execution history interface in aeon/kernel/history_interface.py
- [ ] T099 [US6] Implement pass sequence recording in aeon/kernel/history_recorder.py
- [ ] T100 [US6] Implement plan state snapshot capture per pass in aeon/kernel/history_recorder.py
- [ ] T101 [US6] Implement refinement action recording in aeon/kernel/history_recorder.py
- [ ] T102 [US6] Implement convergence assessment recording in aeon/kernel/history_recorder.py
- [ ] T103 [US6] Implement semantic validation report recording in aeon/kernel/history_recorder.py
- [ ] T104 [US6] Implement adaptive depth configuration recording, including TaskProfile snapshot and adjustment_reason, in execution history for each pass (FR-078), in aeon/kernel/history_recorder.py
- [ ] T105 [US6] Implement timing information capture in aeon/kernel/history_recorder.py
- [ ] T106 [US6] Implement execution history accessor/query interface in aeon/kernel/history_recorder.py
- [ ] T107 [US6] Integrate history recording with multi-pass loop in aeon/kernel/orchestrator.py
- [ ] T108 [US6] Add logging for execution history operations in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 6 should be fully functional and testable independently. Developers can inspect execution history for debugging and tuning.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration, testing, and improvements that affect multiple user stories

- [ ] T109 [P] Verify all Tier-1 features integrate seamlessly without circular dependencies
- [ ] T110 [P] Run integration tests for multi-pass execution with all features in tests/integration/
- [ ] T111 [P] Verify kernel LOC remains under 800 lines (should be <700 after refactoring)
- [ ] T112 [P] Update documentation in README.md and docs/ with Sprint 2 capabilities
- [ ] T113 [P] Add comprehensive integration tests in tests/integration/test_multipass_integration.py
- [ ] T114 [P] Add unit tests for new modules in tests/unit/
- [ ] T115 [P] Verify declarative plan purity maintained throughout all features
- [ ] T116 [P] Verify deterministic execution model maintained (same inputs produce same phase transitions)
- [ ] T117 [P] Performance testing and optimization across all Sprint 2 features
- [ ] T118 [P] Code cleanup and refactoring for consistency
- [ ] T119 [P] Security review for new interfaces and modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all Sprint 2 user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 5 (Semantic Validation) can start immediately after Foundational
  - User Story 3 (Convergence Engine) depends on User Story 5 (needs semantic validation)
  - User Story 1 (Multi-Pass Execution) depends on User Story 3 (needs convergence engine)
  - User Story 2 (Recursive Planning) depends on User Story 5 (needs semantic validation)
  - User Story 4 (Adaptive Depth) depends on User Stories 3 and 5 (needs convergence and semantic validation)
  - User Story 6 (Execution Inspection) depends on User Story 1 (needs multi-pass execution)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 5 (P1) - Semantic Validation**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1) - Convergence Engine**: Depends on User Story 5 (semantic validation)
- **User Story 1 (P1) - Multi-Pass Execution**: Depends on User Story 3 (convergence engine) and User Story 5 (semantic validation)
- **User Story 2 (P1) - Recursive Planning**: Depends on User Story 5 (semantic validation)
- **User Story 4 (P2) - Adaptive Depth**: Depends on User Stories 3 and 5 (convergence engine and semantic validation)
- **User Story 6 (P2) - Execution Inspection**: Depends on User Story 1 (multi-pass execution)

### Within Each User Story

- Models before services/interfaces
- Interfaces before implementations
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational extraction tasks marked [P] can run in parallel (within Phase 2)
- User Stories 5 and 2 can potentially start in parallel after Foundational (both depend only on Foundational)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (respecting dependencies)

---

## Parallel Example: User Story 5

```bash
# Launch all models for User Story 5 together:
Task: "Create ValidationIssue model in aeon/validation/semantic_models.py"
Task: "Create SemanticValidationReport model in aeon/validation/semantic_models.py"
Task: "Create semantic validation interface in aeon/validation/semantic_interface.py"
```

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create ExecutionPass model in aeon/kernel/multipass_models.py"
Task: "Create RefinementAction model in aeon/kernel/multipass_models.py"
```

---

## Implementation Strategy

### MVP First (Core Multi-Pass Execution)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (MANDATORY kernel refactoring - CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 5 (Semantic Validation)
4. Complete Phase 4: User Story 3 (Convergence Engine)
5. Complete Phase 5: User Story 1 (Multi-Pass Execution)
6. **STOP and VALIDATE**: Test multi-pass execution independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 5 (Semantic Validation) → Test independently
3. Add User Story 3 (Convergence Engine) → Test independently
4. Add User Story 1 (Multi-Pass Execution) → Test independently → Deploy/Demo (MVP!)
5. Add User Story 2 (Recursive Planning) → Test independently → Deploy/Demo
6. Add User Story 4 (Adaptive Depth) → Test independently → Deploy/Demo
7. Add User Story 6 (Execution Inspection) → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (MANDATORY)
2. Once Foundational is done:
   - Developer A: User Story 5 (Semantic Validation)
   - Developer B: (waiting for dependencies)
3. Once User Story 5 is done:
   - Developer A: User Story 3 (Convergence Engine)
   - Developer B: User Story 2 (Recursive Planning) - both depend on US5
4. Once User Story 3 is done:
   - Developer A: User Story 1 (Multi-Pass Execution)
   - Developer B: User Story 4 (Adaptive Depth) - depends on US3 and US5
5. Once User Story 1 is done:
   - Developer A: User Story 6 (Execution Inspection)
   - Developer B: Polish & Integration

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Phase 2 (kernel refactoring) MUST be completed before any Sprint 2 user story work begins
- Kernel LOC must remain under 800 lines (target <700 after refactoring)
- All Sprint 2 features must operate as modular components external to kernel

---

## Task Summary

- **Total Tasks**: 119
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational - Kernel Refactoring)**: 15 tasks
- **Phase 3 (User Story 5 - Semantic Validation)**: 13 tasks
- **Phase 4 (User Story 3 - Convergence Engine)**: 12 tasks
- **Phase 5 (User Story 1 - Multi-Pass Execution)**: 17 tasks
- **Phase 6 (User Story 2 - Recursive Planning)**: 19 tasks
- **Phase 7 (User Story 4 - Adaptive Depth)**: 17 tasks
- **Phase 8 (User Story 6 - Execution Inspection)**: 12 tasks
- **Phase 9 (Polish)**: 11 tasks

### Parallel Opportunities

- **Phase 1**: 3 parallel tasks
- **Phase 2**: 4 parallel extraction tasks
- **Phase 3**: 3 parallel model/interface tasks
- **Phase 4**: 2 parallel model/interface tasks
- **Phase 5**: 2 parallel model tasks
- **Phase 6**: 2 parallel model/interface tasks
- **Phase 7**: 2 parallel model/interface tasks
- **Phase 8**: 2 parallel model/interface tasks
- **Phase 9**: 11 parallel polish tasks

### Suggested MVP Scope

**MVP**: Phases 1-5 (Setup + Foundational + User Stories 5, 3, 1)
- This delivers core multi-pass execution with convergence detection and semantic validation
- Total MVP tasks: 60 tasks
- Can be delivered incrementally: Setup → Foundational → US5 → US3 → US1
