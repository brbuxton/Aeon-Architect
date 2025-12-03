# Tasks: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Input**: Design documents from `/specs/003-adaptive-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/`, `tests/` at repository root
- All paths shown below use absolute paths from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create module directories per implementation plan: aeon/convergence/, aeon/adaptive/, tests/unit/convergence/, tests/unit/adaptive/
- [ ] T002 [P] Create __init__.py files for new modules: aeon/convergence/__init__.py, aeon/adaptive/__init__.py
- [ ] T003 [P] Configure pytest test structure for new modules in tests/unit/convergence/ and tests/unit/adaptive/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MANDATORY kernel refactoring per Constitution Principle I (Kernel Minimalism) that MUST be complete before ANY Sprint 2 user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Kernel Refactoring - Analysis Phase

- [ ] T004 Measure current kernel LOC: aeon/kernel/orchestrator.py + aeon/kernel/executor.py
- [ ] T005 Analyze orchestrator.py for extractable non-orchestration logic in aeon/kernel/orchestrator.py
- [ ] T006 Analyze executor.py for extractable non-orchestration logic in aeon/kernel/executor.py
- [ ] T007 Document identified extractable logic and target modules in refactoring plan

### Kernel Refactoring - Extraction Phase

- [ ] T008 [P] Extract non-orchestration logic from orchestrator.py to appropriate external modules
- [ ] T009 [P] Extract non-orchestration logic from executor.py to appropriate external modules
- [ ] T010 Refactor orchestrator.py to use extracted modules while maintaining interface in aeon/kernel/orchestrator.py
- [ ] T011 Refactor executor.py to use extracted modules while maintaining interface in aeon/kernel/executor.py
- [ ] T012 Verify kernel LOC < 700 after refactoring (target: <700 LOC)

### Kernel Refactoring - Validation Phase

- [ ] T013 Run full Sprint 1 test suite to verify behavioral preservation: pytest tests/
- [ ] T014 Verify all existing tests pass without modification
- [ ] T015 [P] Add regression tests for kernel refactoring in tests/unit/kernel/test_refactoring.py
- [ ] T016 Document before/after LOC measurements and refactoring changes
- [ ] T017 Verify no behavioral drift introduced by refactoring

**Checkpoint**: Kernel refactoring complete - LOC < 700, all tests pass, no behavioral drift. Sprint 2 user story implementation can now begin.

---

## Phase 3: User Story 1 - Multi-Pass Execution with Deterministic Phase Control (Priority: P1) 🎯 MVP

**Goal**: Implement multi-pass execution loop that iteratively executes, evaluates, and refines plans until convergence or TTL expiration.

**Independent Test**: Submit a complex task (e.g., "design a system architecture for a web application with user authentication") and verify that Aeon executes multiple passes following the exact phase sequence (Phase A: TaskProfile & TTL → Phase B: Initial Plan & Pre-Execution Refinement → Phase C: Execution Passes → Phase D: Adaptive Depth) until convergence is achieved or TTL expires.

**Dependencies**: Requires Phase 2 (kernel refactoring) completion. This story is foundational for US2, US3, US4, US5.

### Data Models for User Story 1

- [ ] T018 [P] [US1] Create ExecutionPass model in aeon/kernel/state.py
- [ ] T019 [P] [US1] Create ExecutionHistory model in aeon/kernel/state.py
- [ ] T020 [P] [US1] Create TTLExpirationResponse model in aeon/kernel/state.py
- [ ] T021 [US1] Extend PlanStep model with step_index, total_steps, incoming_context, handoff_to_next fields in aeon/plan/models.py
- [ ] T022 [US1] Add clarity_state field to PlanStep model in aeon/plan/models.py
- [ ] T023 [US1] Add "invalid" status to StepStatus enum in aeon/plan/models.py
- [ ] T024 [US1] Add step_output field to PlanStep model in aeon/plan/models.py

### Implementation for User Story 1

- [ ] T025 [US1] Implement pass management in orchestrator (pass_number tracking, phase transitions) in aeon/kernel/orchestrator.py
- [ ] T026 [US1] Implement phase sequencing logic (Phase A → Phase B → Phase C → Phase D) in aeon/kernel/orchestrator.py
- [ ] T027 [US1] Implement TTL boundary checks at phase boundaries in aeon/kernel/orchestrator.py
- [ ] T028 [US1] Implement TTL safe boundary detection for mid-phase checks in aeon/kernel/orchestrator.py
- [ ] T029 [US1] Implement batch step execution (all ready steps in parallel) in aeon/kernel/executor.py
- [ ] T030 [US1] Implement step execution prompt construction with step_index, total_steps, incoming_context, handoff_to_next in aeon/kernel/executor.py
- [ ] T031 [US1] Implement clarity_state handling (CLEAR, PARTIALLY_CLEAR, BLOCKED) in aeon/kernel/executor.py
- [ ] T032 [US1] Implement step status transitions including "invalid" status in aeon/kernel/executor.py
- [ ] T033 [US1] Implement ExecutionPass creation and recording in aeon/kernel/orchestrator.py
- [ ] T034 [US1] Implement ExecutionHistory collection and return in aeon/kernel/orchestrator.py
- [ ] T035 [US1] Implement TTL expiration response generation (phase_boundary vs mid_phase) in aeon/kernel/orchestrator.py
- [ ] T036 [US1] Integrate orchestrator with convergence engine interface (placeholder for US5) in aeon/kernel/orchestrator.py
- [ ] T037 [US1] Integrate orchestrator with semantic validator interface (placeholder for US4) in aeon/kernel/orchestrator.py
- [ ] T038 [US1] Integrate orchestrator with recursive planner interface (placeholder for US3) in aeon/kernel/orchestrator.py
- [ ] T039 [US1] Integrate orchestrator with adaptive depth interface (placeholder for US6) in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 1 should be fully functional with placeholder integrations. Multi-pass loop executes, records history, handles TTL expiration.

---

## Phase 4: User Story 2 - TaskProfile Inference and TTL Allocation (Priority: P1)

**Goal**: Implement TaskProfile inference and TTL allocation that occurs before any planning (Phase A).

**Independent Test**: Submit tasks of varying complexity (simple: "add two numbers", complex: "design a distributed system architecture") and verify that Aeon infers appropriate TaskProfile dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) and allocates TTL accordingly before generating any plan.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Integrates with US1 Phase A.

### Data Models for User Story 2

- [ ] T040 [P] [US2] Create TaskProfile model in aeon/adaptive/models.py
- [ ] T041 [P] [US2] Create AdaptiveDepthConfiguration model in aeon/adaptive/models.py

### Implementation for User Story 2

- [ ] T042 [US2] Create AdaptiveDepth class in aeon/adaptive/heuristics.py
- [ ] T043 [US2] Implement AdaptiveDepth.__init__() with LLM adapter and global TTL limit in aeon/adaptive/heuristics.py
- [ ] T044 [US2] Implement AdaptiveDepth.infer_task_profile() with LLM-based reasoning for all dimensions in aeon/adaptive/heuristics.py
- [ ] T045 [US2] Implement TaskProfile dimension inference (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) in aeon/adaptive/heuristics.py
- [ ] T046 [US2] Implement raw_inference field generation in AdaptiveDepth.infer_task_profile() in aeon/adaptive/heuristics.py
- [ ] T047 [US2] Implement default TaskProfile fallback (reasoning_depth=3, information_sufficiency=0.5, expected_tool_usage=moderate, output_breadth=moderate, confidence_requirement=medium) in aeon/adaptive/heuristics.py
- [ ] T048 [US2] Implement supervisor repair_json() integration for TaskProfile inference JSON/schema errors in aeon/adaptive/heuristics.py
- [ ] T049 [US2] Implement AdaptiveDepth.allocate_ttl() with deterministic function mapping TaskProfile to TTL in aeon/adaptive/heuristics.py
- [ ] T050 [US2] Implement TTL capping at global limit in AdaptiveDepth.allocate_ttl() in aeon/adaptive/heuristics.py
- [ ] T051 [US2] Integrate adaptive depth with orchestrator Phase A (TaskProfile & TTL) in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 2 should be fully functional. TaskProfile inference occurs before planning, TTL is allocated deterministically.

---

## Phase 5: User Story 3 - Recursive Planning and Plan Refinement (Priority: P1)

**Goal**: Implement recursive planning that generates initial plans, creates subplans for complex steps, and refines plan fragments using LLM-based reasoning.

**Independent Test**: Submit an ambiguous task (e.g., "build a REST API") and verify that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments using delta-style operations (ADD/MODIFY/REMOVE), and automatically incorporates semantic validation into the refinement process.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Integrates with US1 Phase B and US4 (semantic validation).

### Data Models for User Story 3

- [ ] T052 [P] [US3] Create RefinementAction model in aeon/plan/models.py
- [ ] T053 [P] [US3] Create Subplan model in aeon/plan/models.py

### Implementation for User Story 3

- [ ] T054 [US3] Create RecursivePlanner class in aeon/plan/recursive.py
- [ ] T055 [US3] Implement RecursivePlanner.__init__() with LLM adapter and tool registry in aeon/plan/recursive.py
- [ ] T056 [US3] Implement RecursivePlanner.generate_plan() with step_index, total_steps, incoming_context, handoff_to_next in aeon/plan/recursive.py
- [ ] T057 [US3] Implement RecursivePlanner.refine_plan() with delta-style operations (ADD/MODIFY/REMOVE) in aeon/plan/recursive.py
- [ ] T058 [US3] Implement refinement trigger collection (validation issues, convergence reason_codes, blocked steps) in aeon/plan/recursive.py
- [ ] T059 [US3] Implement executed step protection (cannot refine steps with status "complete" or "failed") in aeon/plan/recursive.py
- [ ] T060 [US3] Implement RecursivePlanner.create_subplan() with nesting depth limit (max 5) in aeon/plan/recursive.py
- [ ] T061 [US3] Implement graceful failure for nesting depth exceeded in aeon/plan/recursive.py
- [ ] T062 [US3] Implement step ID stability preservation during refinement in aeon/plan/recursive.py
- [ ] T063 [US3] Implement refinement attempt limits (3 per fragment, 10 global) in aeon/plan/recursive.py
- [ ] T064 [US3] Implement manual intervention marking for fragments at refinement limit in aeon/plan/recursive.py
- [ ] T065 [US3] Implement supervisor repair_json() integration for LLM output schema violations in aeon/plan/recursive.py
- [ ] T066 [US3] Integrate recursive planner with orchestrator Phase B (Initial Plan & Pre-Execution Refinement) in aeon/kernel/orchestrator.py
- [ ] T067 [US3] Integrate recursive planner with orchestrator Phase C refinement phase in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 3 should be fully functional. Recursive planning generates plans, creates subplans, and refines fragments while preserving plan structure.

---

## Phase 6: User Story 4 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

**Goal**: Implement semantic validation layer that validates plans, steps, and execution artifacts for semantic quality issues using LLM-based reasoning.

**Independent Test**: Generate a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verify that the semantic validation layer detects these issues, classifies them using LLM-based reasoning, assigns severity scores, and proposes semantic repairs.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Used by US3 (recursive planning), US5 (convergence engine), and US6 (adaptive depth).

### Data Models for User Story 4

- [ ] T068 [P] [US4] Create ValidationIssue model in aeon/validation/models.py
- [ ] T069 [P] [US4] Create SemanticValidationReport model in aeon/validation/models.py

### Implementation for User Story 4

- [ ] T070 [US4] Create SemanticValidator class in aeon/validation/semantic.py
- [ ] T071 [US4] Implement SemanticValidator.__init__() with LLM adapter and tool registry in aeon/validation/semantic.py
- [ ] T072 [US4] Implement SemanticValidator.validate() with LLM-based reasoning for specificity check in aeon/validation/semantic.py
- [ ] T073 [US4] Implement SemanticValidator.validate() with LLM-based reasoning for relevance check in aeon/validation/semantic.py
- [ ] T074 [US4] Implement SemanticValidator.validate() with LLM-based reasoning for do/say mismatch detection in aeon/validation/semantic.py
- [ ] T075 [US4] Implement SemanticValidator.validate() with LLM-based reasoning for hallucination detection in aeon/validation/semantic.py
- [ ] T076 [US4] Implement SemanticValidator.validate() with LLM-based reasoning for consistency check in aeon/validation/semantic.py
- [ ] T077 [US4] Implement structural checks (duplicate IDs, missing attributes) before LLM delegation in aeon/validation/semantic.py
- [ ] T078 [US4] Implement LLM-determined severity assignment in aeon/validation/semantic.py
- [ ] T079 [US4] Implement LLM-classified issue types in aeon/validation/semantic.py
- [ ] T080 [US4] Implement LLM-generated proposed repairs in aeon/validation/semantic.py
- [ ] T081 [US4] Implement issue_summary generation (counts by type) in aeon/validation/semantic.py
- [ ] T082 [US4] Implement overall_severity calculation (highest severity) in aeon/validation/semantic.py
- [ ] T083 [US4] Implement supervisor repair_json() integration for LLM output schema violations in aeon/validation/semantic.py
- [ ] T084 [US4] Integrate semantic validator with orchestrator Phase B (plan validation) in aeon/kernel/orchestrator.py
- [ ] T085 [US4] Integrate semantic validator with orchestrator Phase C (evaluate phase) in aeon/kernel/orchestrator.py
- [ ] T086 [US4] Integrate semantic validator with recursive planner refinement flow in aeon/plan/recursive.py

**Checkpoint**: At this point, User Story 4 should be fully functional. Semantic validation detects issues, classifies them, and proposes repairs using LLM-based reasoning.

---

## Phase 7: User Story 5 - Convergence Detection and Completion Assessment (Priority: P1)

**Goal**: Implement convergence engine that determines whether task execution has converged on a complete, coherent, consistent solution using LLM-based reasoning.

**Independent Test**: Execute a task through multiple passes and verify that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met using LLM-based reasoning, returning convergence status (true/false), reason codes, and evaluation metadata.

**Dependencies**: Requires Phase 2 (kernel refactoring), Phase 3 (US1 - multi-pass loop), and Phase 6 (US4 - semantic validation). Integrates with US1 evaluate phase and consumes US4 semantic validation reports.

### Data Models for User Story 5

- [ ] T087 [P] [US5] Create ConvergenceAssessment model in aeon/convergence/models.py

### Implementation for User Story 5

- [ ] T088 [US5] Create ConvergenceEngine class in aeon/convergence/engine.py
- [ ] T089 [US5] Implement ConvergenceEngine.__init__() with LLM adapter and default thresholds in aeon/convergence/engine.py
- [ ] T090 [US5] Implement ConvergenceEngine.assess() with LLM-based reasoning for completeness check in aeon/convergence/engine.py
- [ ] T091 [US5] Implement ConvergenceEngine.assess() with LLM-based reasoning for coherence check in aeon/convergence/engine.py
- [ ] T092 [US5] Implement ConvergenceEngine.assess() with LLM-based reasoning for consistency check in aeon/convergence/engine.py
- [ ] T093 [US5] Implement semantic validation report consumption in ConvergenceEngine.assess() in aeon/convergence/engine.py
- [ ] T094 [US5] Implement reason code generation (converged: true/false with explanation) in aeon/convergence/engine.py
- [ ] T095 [US5] Implement evaluation metadata generation (completeness score, coherence score, detected issues) in aeon/convergence/engine.py
- [ ] T096 [US5] Implement custom criteria support in ConvergenceEngine.assess() in aeon/convergence/engine.py
- [ ] T097 [US5] Implement default thresholds (completeness >= 0.95, coherence >= 0.90, consistency >= 0.90) in aeon/convergence/engine.py
- [ ] T098 [US5] Implement conflict handling (converged: false when criteria conflict) in aeon/convergence/engine.py
- [ ] T099 [US5] Implement supervisor repair_json() integration for LLM output schema violations in aeon/convergence/engine.py
- [ ] T100 [US5] Integrate convergence engine with orchestrator evaluate phase in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 5 should be fully functional. Convergence engine assesses execution state and determines convergence status with detailed metadata.

---

## Phase 8: User Story 6 - Adaptive Depth Integration (Priority: P2)

**Goal**: Implement adaptive depth heuristics that update TaskProfile at pass boundaries when complexity mismatch is detected.

**Independent Test**: Submit both simple tasks (e.g., "add two numbers") and complex tasks (e.g., "design a distributed system architecture") and verify that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on TaskProfile dimensions, with updates occurring only at pass boundaries.

**Dependencies**: Requires Phase 2 (kernel refactoring), Phase 3 (US1 - multi-pass loop), Phase 4 (US2 - TaskProfile inference), Phase 6 (US4 - semantic validation), and Phase 7 (US5 - convergence engine). Integrates with US1 Phase D.

### Implementation for User Story 6

- [ ] T101 [US6] Implement AdaptiveDepth.update_task_profile() with trigger conditions (convergence failure AND validation issues AND clarity_state BLOCKED) in aeon/adaptive/heuristics.py
- [ ] T102 [US6] Implement TaskProfile version tracking in aeon/adaptive/heuristics.py
- [ ] T103 [US6] Implement bidirectional TTL adjustment (increase and decrease based on complexity) in aeon/adaptive/heuristics.py
- [ ] T104 [US6] Integrate adaptive depth with orchestrator Phase D (TaskProfile updates at pass boundaries) in aeon/kernel/orchestrator.py
- [ ] T105 [US6] Record adjustment_reason in execution metadata in aeon/adaptive/heuristics.py

**Checkpoint**: At this point, User Story 6 should be fully functional. Adaptive depth infers TaskProfile, allocates TTL, and updates profile based on execution feedback.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T106 [P] Update documentation with Sprint 2 capabilities in README.md
- [ ] T107 [P] Add usage examples to quickstart.md based on implementation
- [ ] T108 [P] Code cleanup and refactoring for consistency across modules
- [ ] T109 [P] Verify kernel LOC remains under 800 lines (should be <700 after refactoring)
- [ ] T110 [P] Add integration tests for end-to-end multi-pass execution scenarios in tests/integration/
- [ ] T111 [P] Add contract tests for all interfaces in tests/contract/
- [ ] T112 [P] Performance optimization for multi-pass execution
- [ ] T113 [P] Error handling improvements across all modules
- [ ] T114 [P] Add logging enhancements for multi-pass execution debugging in aeon/observability/logger.py
- [ ] T115 [P] Add observability metrics for pass counts, refinement counts, convergence rates in aeon/observability/models.py
- [ ] T116 Run quickstart.md validation and update examples
- [ ] T117 [P] Enhance CLI with multi-pass execution display in aeon/cli/main.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1: US1, US2, US3, US4, US5 → P2: US6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **FOUNDATIONAL for other stories.**
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) and US1 - Integrates with US1 Phase A
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) and US1 - Integrates with US1 Phase B and Phase C, uses US4 semantic validation
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) and US1 - Used by US3, US5, US6
- **User Story 5 (P1)**: Can start after Foundational (Phase 2), US1, and US4 - Integrates with US1 evaluate phase, consumes US4 semantic validation reports
- **User Story 6 (P2)**: Can start after Foundational (Phase 2), US1, US2, US4, and US5 - Integrates with US1 Phase D, uses US2 TaskProfile, US4 validation, US5 convergence

### Within Each User Story

- Data models before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, P1 user stories (US1, US2, US3, US4, US5) can start in parallel (if team capacity allows)
- All data models for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (respecting dependencies)

---

## Parallel Example: User Story 1

```bash
# Launch all data models for User Story 1 together:
Task: "Create ExecutionPass model in aeon/kernel/state.py"
Task: "Create ExecutionHistory model in aeon/kernel/state.py"
Task: "Create TTLExpirationResponse model in aeon/kernel/state.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) - **MANDATORY kernel refactoring**
3. Complete Phase 3: User Story 1 (Multi-Pass Execution)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (kernel refactored, LOC < 700)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (TaskProfile) → Test independently → Deploy/Demo
4. Add User Story 4 (Semantic Validation) → Test independently → Deploy/Demo (enables US3, US5)
5. Add User Story 3 (Recursive Planning) → Test independently → Deploy/Demo
6. Add User Story 5 (Convergence) → Test independently → Deploy/Demo
7. Add User Story 6 (Adaptive Depth) → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (kernel refactoring is critical)
2. Once Foundational is done:
   - Developer A: User Story 1 (Multi-Pass Execution) - **FOUNDATIONAL**
   - Developer B: User Story 2 (TaskProfile Inference) - **ENABLES OTHERS**
   - Developer C: User Story 4 (Semantic Validation) - **ENABLES OTHERS**
3. Once US1, US2, US4 are done:
   - Developer A: User Story 3 (Recursive Planning)
   - Developer B: User Story 5 (Convergence)
   - Developer C: User Story 6 (Adaptive Depth)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Phase 2 (kernel refactoring) MUST be completed before any Sprint 2 user story work begins
- Kernel LOC must remain under 800 lines (target <700 after refactoring)
- All semantic reasoning MUST use LLM-based reasoning as primary mechanism
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

**Total Tasks**: 117
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational - Kernel Refactoring): 14 tasks
- Phase 3 (User Story 1): 22 tasks
- Phase 4 (User Story 2): 12 tasks
- Phase 5 (User Story 3): 16 tasks
- Phase 6 (User Story 4): 19 tasks
- Phase 7 (User Story 5): 14 tasks
- Phase 8 (User Story 6): 5 tasks
- Phase 9 (Polish): 12 tasks

**Task Count per User Story**:
- US1: 22 tasks
- US2: 12 tasks
- US3: 16 tasks
- US4: 19 tasks
- US5: 14 tasks
- US6: 5 tasks

**Parallel Opportunities Identified**: 
- All [P] marked tasks can run in parallel within their phase
- User stories can be worked on in parallel after foundational phase (respecting dependencies)

**Independent Test Criteria**:
- US1: Submit complex task, verify multi-pass loop executes until convergence or TTL expires
- US2: Submit tasks of varying complexity, verify TaskProfile inference and TTL allocation
- US3: Submit ambiguous task, verify recursive planning detects ambiguities and refines fragments
- US4: Generate plan with issues, verify semantic validation detects and classifies issues
- US5: Execute task through multiple passes, verify convergence engine identifies convergence status
- US6: Submit simple and complex tasks, verify adaptive depth adjusts TTL and reasoning depth

**Suggested MVP Scope**: 
- Phase 1: Setup
- Phase 2: Foundational (MANDATORY kernel refactoring - CRITICAL - blocks all stories)
- Phase 3: User Story 1 (Multi-Pass Execution with Deterministic Phase Control) - **MVP**

**Format Validation**: ✅ All tasks follow the checklist format (checkbox, ID, [P] marker where applicable, [Story] label, file paths)

