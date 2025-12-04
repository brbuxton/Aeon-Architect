# Tasks: Sprint 2 - Adaptive Reasoning Engine

**Input**: Design documents from `/specs/002-adaptive-reasoning/`
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

- [ ] T004 Measure current kernel LOC: aeon/kernel/orchestrator.py + aeon/kernel/executor.py (baseline: 561 LOC)
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

## Phase 3: User Story 1 - Multi-Pass Execution with Convergence (Priority: P1) 🎯 MVP

**Goal**: Implement multi-pass execution loop that iteratively executes, evaluates, and refines plans until convergence or TTL expiration.

**Independent Test**: Submit a complex task (e.g., "design a system architecture for a web application with user authentication") and verify that Aeon executes multiple passes (plan → execute → evaluate → refine → re-execute) until convergence is achieved or TTL expires.

**Dependencies**: Requires Phase 2 (kernel refactoring) completion. This story is foundational for US2, US3, US5.

### Tests for User Story 1

- [ ] T018 [P] [US1] Integration test for multi-pass execution loop in tests/integration/test_multi_pass_execution.py
- [ ] T019 [P] [US1] Integration test for TTL expiration at phase boundary in tests/integration/test_ttl_expiration.py
- [ ] T020 [P] [US1] Integration test for TTL expiration mid-phase at safe boundary in tests/integration/test_ttl_expiration.py
- [ ] T021 [P] [US1] Integration test for deterministic phase sequence in tests/integration/test_deterministic_phases.py

### Data Models for User Story 1

- [ ] T022 [P] [US1] Create ExecutionPass model in aeon/kernel/models.py (or new models file)
- [ ] T023 [P] [US1] Create ExecutionHistory model in aeon/kernel/models.py
- [ ] T024 [P] [US1] Create TTLExpirationResponse model in aeon/kernel/models.py
- [ ] T025 [US1] Extend PlanStep model with step_index, total_steps, incoming_context, handoff_to_next fields in aeon/plan/models.py
- [ ] T026 [US1] Add clarity_state field to PlanStep model in aeon/plan/models.py
- [ ] T027 [US1] Add "invalid" status to StepStatus enum in aeon/plan/models.py
- [ ] T028 [US1] Add step_output field to PlanStep model in aeon/plan/models.py
- [ ] T029 [US1] Add dependencies and provides fields to PlanStep model in aeon/plan/models.py

### Implementation for User Story 1

- [ ] T030 [US1] Implement pass management in orchestrator (pass_number tracking, phase transitions) in aeon/kernel/orchestrator.py
- [ ] T031 [US1] Implement phase sequencing logic (EXECUTE → EVALUATE → REFINE → RE_EXECUTE) in aeon/kernel/orchestrator.py
- [ ] T032 [US1] Implement TTL boundary checks at phase boundaries in aeon/kernel/orchestrator.py
- [ ] T033 [US1] Implement TTL safe boundary detection for mid-phase checks in aeon/kernel/orchestrator.py
- [ ] T034 [US1] Implement batch step execution (all ready steps in parallel) in aeon/kernel/executor.py
- [ ] T035 [US1] Implement step execution prompt construction with step_index, total_steps, incoming_context, handoff_to_next in aeon/kernel/executor.py
- [ ] T036 [US1] Implement clarity_state handling (CLEAR, PARTIALLY_CLEAR, BLOCKED) in aeon/kernel/executor.py
- [ ] T037 [US1] Implement step status transitions including "invalid" status in aeon/kernel/executor.py
- [ ] T038 [US1] Implement ExecutionPass creation and recording in aeon/kernel/orchestrator.py
- [ ] T039 [US1] Implement ExecutionHistory collection and return in aeon/kernel/orchestrator.py
- [ ] T040 [US1] Implement TTL expiration response generation (phase_boundary vs mid_phase) in aeon/kernel/orchestrator.py
- [ ] T041 [US1] Integrate orchestrator with convergence engine interface (placeholder for US3) in aeon/kernel/orchestrator.py
- [ ] T042 [US1] Integrate orchestrator with semantic validator interface (placeholder for US5) in aeon/kernel/orchestrator.py
- [ ] T043 [US1] Integrate orchestrator with recursive planner interface (placeholder for US2) in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 1 should be fully functional with placeholder integrations. Multi-pass loop executes, records history, handles TTL expiration.

---

## Phase 4: User Story 2 - Recursive Planning and Plan Refinement (Priority: P1)

**Goal**: Implement recursive planning that generates initial plans, creates subplans for complex steps, and refines plan fragments using LLM-based reasoning.

**Independent Test**: Submit an ambiguous task (e.g., "build a REST API") and verify that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments, and automatically incorporates semantic validation into the refinement process.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Integrates with US5 (semantic validation).

### Tests for User Story 2

- [ ] T044 [P] [US2] Unit test for RecursivePlanner.generate_plan() in tests/unit/plan/test_recursive.py
- [ ] T045 [P] [US2] Unit test for RecursivePlanner.refine_plan() in tests/unit/plan/test_recursive.py
- [ ] T046 [P] [US2] Unit test for RecursivePlanner.create_subplan() in tests/unit/plan/test_recursive.py
- [ ] T047 [P] [US2] Integration test for recursive planning with ambiguous tasks in tests/integration/test_recursive_planning.py
- [ ] T048 [P] [US2] Integration test for plan refinement with validation issues in tests/integration/test_plan_refinement.py
- [ ] T049 [P] [US2] Integration test for nesting depth limit handling in tests/integration/test_nesting_depth.py

### Data Models for User Story 2

- [ ] T050 [P] [US2] Create RefinementAction model in aeon/plan/models.py
- [ ] T051 [P] [US2] Create Subplan model in aeon/plan/models.py

### Implementation for User Story 2

- [ ] T052 [US2] Create RecursivePlanner class in aeon/plan/recursive.py
- [ ] T053 [US2] Implement RecursivePlanner.__init__() with LLM adapter and tool registry in aeon/plan/recursive.py
- [ ] T054 [US2] Implement RecursivePlanner.generate_plan() with step_index, total_steps, incoming_context, handoff_to_next in aeon/plan/recursive.py
- [ ] T055 [US2] Implement RecursivePlanner.refine_plan() with delta-style operations (ADD/MODIFY/REMOVE), supervisor repair integration for structural/semantic issues before re-execution (FR-004), and unrecoverable failure handling after 2 repair attempts (FR-067) in aeon/plan/recursive.py
- [ ] T056 [US2] Implement refinement trigger collection (validation issues, convergence reason_codes, blocked steps) in aeon/plan/recursive.py
- [ ] T057 [US2] Implement executed step protection (cannot refine steps with status "complete" or "failed") in aeon/plan/recursive.py
- [ ] T058 [US2] Implement RecursivePlanner.create_subplan() with nesting depth limit (max 5) in aeon/plan/recursive.py
- [ ] T059 [US2] Implement graceful failure for nesting depth exceeded in aeon/plan/recursive.py
- [ ] T060 [US2] Implement step ID stability preservation during refinement in aeon/plan/recursive.py
- [ ] T061 [US2] Integrate recursive planner with orchestrator multi-pass loop in aeon/kernel/orchestrator.py
- [ ] T062 [US2] Implement Phase B: Initial Plan & Pre-Execution Refinement (Plan → Validate → Refine) in aeon/kernel/orchestrator.py
- [ ] T063 [US2] Implement refinement attempt limits (3 per fragment, 10 global) in aeon/plan/recursive.py
- [ ] T064 [US2] Implement manual intervention marking for fragments at refinement limit in aeon/plan/recursive.py

**Checkpoint**: At this point, User Story 2 should be fully functional. Recursive planning generates plans, creates subplans, and refines fragments while preserving plan structure.

---

## Phase 5: User Story 3 - Convergence Detection and Completion Assessment (Priority: P1)

**Goal**: Implement convergence engine that determines whether task execution has converged on a complete, coherent, consistent solution using LLM-based reasoning.

**Independent Test**: Execute a task through multiple passes and verify that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met, returning convergence status (true/false), reason codes, and evaluation metadata.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Integrates with US5 (semantic validation - consumes validation report).

### Tests for User Story 3

- [ ] T065 [P] [US3] Unit test for ConvergenceEngine.assess() with converged result in tests/unit/convergence/test_engine.py
- [ ] T066 [P] [US3] Unit test for ConvergenceEngine.assess() with non-converged result in tests/unit/convergence/test_engine.py
- [ ] T067 [P] [US3] Unit test for default thresholds in tests/unit/convergence/test_engine.py
- [ ] T068 [P] [US3] Unit test for custom convergence criteria in tests/unit/convergence/test_engine.py
- [ ] T069 [P] [US3] Integration test for convergence detection in multi-pass execution in tests/integration/test_convergence.py
- [ ] T070 [P] [US3] Integration test for convergence with conflicting criteria in tests/integration/test_convergence.py

### Data Models for User Story 3

- [ ] T071 [P] [US3] Create ConvergenceAssessment model in aeon/convergence/models.py

### Implementation for User Story 3

- [ ] T072 [US3] Create ConvergenceEngine class in aeon/convergence/engine.py
- [ ] T073 [US3] Implement ConvergenceEngine.__init__() with LLM adapter and default thresholds in aeon/convergence/engine.py
- [ ] T074 [US3] Implement ConvergenceEngine.assess() with LLM-based reasoning for completeness check in aeon/convergence/engine.py
- [ ] T075 [US3] Implement ConvergenceEngine.assess() with LLM-based reasoning for coherence check in aeon/convergence/engine.py
- [ ] T076 [US3] Implement ConvergenceEngine.assess() with LLM-based reasoning for consistency check in aeon/convergence/engine.py
- [ ] T077 [US3] Implement semantic validation report consumption in ConvergenceEngine.assess() in aeon/convergence/engine.py
- [ ] T078 [US3] Implement reason code generation (converged: true/false with explanation) in aeon/convergence/engine.py
- [ ] T079 [US3] Implement evaluation metadata generation (completeness score, coherence score, detected issues) in aeon/convergence/engine.py
- [ ] T080 [US3] Implement custom criteria support in ConvergenceEngine.assess() in aeon/convergence/engine.py
- [ ] T081 [US3] Implement default thresholds (completeness >= 0.95, coherence >= 0.90, consistency >= 0.90) in aeon/convergence/engine.py
- [ ] T082 [US3] Implement conflict handling (converged: false when criteria conflict) in aeon/convergence/engine.py
- [ ] T083 [US3] Integrate convergence engine with orchestrator evaluate phase in aeon/kernel/orchestrator.py
- [ ] T084 [US3] Implement supervisor repair_json() integration for LLM output schema violations in aeon/convergence/engine.py

**Checkpoint**: At this point, User Story 3 should be fully functional. Convergence engine assesses execution state and determines convergence status with detailed metadata.

---

## Phase 6: User Story 4 - Adaptive Reasoning Depth Based on Task Complexity (Priority: P2)

**Goal**: Implement adaptive depth heuristics that infer TaskProfile for tasks and adjust reasoning depth, TTL allocations, and processing strategies based on task complexity.

**Independent Test**: Submit both simple tasks (e.g., "add two numbers") and complex tasks (e.g., "design a distributed system architecture") and verify that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on TaskProfile dimensions.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Integrates with US3 (convergence) and US5 (semantic validation) for TaskProfile updates.

### Tests for User Story 4

- [ ] T085 [P] [US4] Unit test for AdaptiveDepth.infer_task_profile() in tests/unit/adaptive/test_heuristics.py
- [ ] T086 [P] [US4] Unit test for AdaptiveDepth.allocate_ttl() in tests/unit/adaptive/test_heuristics.py
- [ ] T087 [P] [US4] Unit test for AdaptiveDepth.update_task_profile() in tests/unit/adaptive/test_heuristics.py
- [ ] T088 [P] [US4] Unit test for tier stability requirement (±1 tier) in tests/unit/adaptive/test_heuristics.py
- [ ] T089 [P] [US4] Integration test for adaptive depth with simple tasks in tests/integration/test_adaptive_depth.py
- [ ] T090 [P] [US4] Integration test for adaptive depth with complex tasks in tests/integration/test_adaptive_depth.py
- [ ] T091 [P] [US4] Integration test for TaskProfile update at pass boundaries in tests/integration/test_adaptive_depth.py

### Data Models for User Story 4

- [ ] T092 [P] [US4] Create TaskProfile model in aeon/adaptive/models.py
- [ ] T093 [P] [US4] Create AdaptiveDepthConfiguration model in aeon/adaptive/models.py

### Implementation for User Story 4

- [ ] T094 [US4] Create AdaptiveDepth class in aeon/adaptive/heuristics.py
- [ ] T095 [US4] Implement AdaptiveDepth.__init__() with LLM adapter and global TTL limit in aeon/adaptive/heuristics.py
- [ ] T096 [US4] Implement AdaptiveDepth.infer_task_profile() with LLM-based reasoning for all dimensions in aeon/adaptive/heuristics.py
- [ ] T097 [US4] Implement TaskProfile dimension inference (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) in aeon/adaptive/heuristics.py
- [ ] T098 [US4] Implement raw_inference field generation in AdaptiveDepth.infer_task_profile() in aeon/adaptive/heuristics.py
- [ ] T099 [US4] Implement tier stability validation (±1 tier for reasoning_depth) in aeon/adaptive/heuristics.py
- [ ] T100 [US4] Implement AdaptiveDepth.allocate_ttl() with deterministic function mapping TaskProfile to TTL in aeon/adaptive/heuristics.py
- [ ] T101 [US4] Implement TTL capping at global limit in AdaptiveDepth.allocate_ttl() in aeon/adaptive/heuristics.py
- [ ] T102 [US4] Implement AdaptiveDepth.update_task_profile() with trigger conditions (convergence failure AND validation issues AND clarity_state BLOCKED) in aeon/adaptive/heuristics.py
- [ ] T103 [US4] Implement bidirectional TTL adjustment (increase and decrease based on complexity) in aeon/adaptive/heuristics.py
- [ ] T104 [US4] Implement TaskProfile version tracking in aeon/adaptive/heuristics.py
- [ ] T105 [US4] Integrate adaptive depth with orchestrator Phase A (TaskProfile & TTL) in aeon/kernel/orchestrator.py
- [ ] T106 [US4] Integrate adaptive depth with orchestrator Phase D (TaskProfile updates at pass boundaries) in aeon/kernel/orchestrator.py
- [ ] T107 [US4] Implement supervisor repair_json() integration for LLM output schema violations in aeon/adaptive/heuristics.py
- [ ] T108 [US4] Record adjustment_reason in execution metadata in aeon/adaptive/heuristics.py

**Checkpoint**: At this point, User Story 4 should be fully functional. Adaptive depth infers TaskProfile, allocates TTL, and updates profile based on execution feedback.

---

## Phase 7: User Story 5 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

**Goal**: Implement semantic validation layer that validates plans, steps, and execution artifacts for semantic quality issues using LLM-based reasoning.

**Independent Test**: Generate a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verify that the semantic validation layer detects these issues, classifies them, assigns severity scores, and proposes semantic repairs.

**Dependencies**: Requires Phase 2 (kernel refactoring) and Phase 3 (US1 - multi-pass loop). Used by US2 (recursive planning), US3 (convergence engine), and US4 (adaptive depth).

### Tests for User Story 5

- [ ] T109 [P] [US5] Unit test for SemanticValidator.validate() with plan artifact in tests/unit/validation/test_semantic.py
- [ ] T110 [P] [US5] Unit test for SemanticValidator.validate() with step artifact in tests/unit/validation/test_semantic.py
- [ ] T111 [P] [US5] Unit test for SemanticValidator.validate() with execution artifact in tests/unit/validation/test_semantic.py
- [ ] T112 [P] [US5] Unit test for SemanticValidator.validate() with cross-phase validation in tests/unit/validation/test_semantic.py
- [ ] T113 [P] [US5] Unit test for hallucinated tool detection in tests/unit/validation/test_semantic.py
- [ ] T114 [P] [US5] Integration test for semantic validation in plan refinement flow in tests/integration/test_semantic_validation.py
- [ ] T115 [P] [US5] Integration test for semantic validation in convergence assessment in tests/integration/test_semantic_validation.py

### Data Models for User Story 5

- [ ] T116 [P] [US5] Create ValidationIssue model in aeon/validation/models.py
- [ ] T117 [P] [US5] Create SemanticValidationReport model in aeon/validation/models.py

### Implementation for User Story 5

- [ ] T118 [US5] Create SemanticValidator class in aeon/validation/semantic.py
- [ ] T119 [US5] Implement SemanticValidator.__init__() with LLM adapter and tool registry in aeon/validation/semantic.py
- [ ] T120 [US5] Implement SemanticValidator.validate() with LLM-based reasoning for specificity check in aeon/validation/semantic.py
- [ ] T121 [US5] Implement SemanticValidator.validate() with LLM-based reasoning for relevance check in aeon/validation/semantic.py
- [ ] T122 [US5] Implement SemanticValidator.validate() with LLM-based reasoning for do/say mismatch detection in aeon/validation/semantic.py
- [ ] T123 [US5] Implement SemanticValidator.validate() with LLM-based reasoning for hallucination detection in aeon/validation/semantic.py
- [ ] T124 [US5] Implement SemanticValidator.validate() with LLM-based reasoning for consistency check in aeon/validation/semantic.py
- [ ] T125 [US5] Implement structural checks (duplicate IDs, missing attributes) before LLM delegation in aeon/validation/semantic.py
- [ ] T126 [US5] Implement LLM-determined severity assignment in aeon/validation/semantic.py
- [ ] T127 [US5] Implement LLM-classified issue types in aeon/validation/semantic.py
- [ ] T128 [US5] Implement LLM-generated proposed repairs in aeon/validation/semantic.py
- [ ] T129 [US5] Implement issue_summary generation (counts by type) in aeon/validation/semantic.py
- [ ] T130 [US5] Implement overall_severity calculation (highest severity) in aeon/validation/semantic.py
- [ ] T131 [US5] Integrate semantic validator with orchestrator evaluate phase in aeon/kernel/orchestrator.py
- [ ] T132 [US5] Integrate semantic validator with recursive planner refinement flow in aeon/plan/recursive.py
- [ ] T133 [US5] Implement conflict resolution (recursive planner wins, semantic validation logged as advisory) in aeon/plan/recursive.py
- [ ] T134 [US5] Implement supervisor repair_json() integration for LLM output schema violations in aeon/validation/semantic.py

**Checkpoint**: At this point, User Story 5 should be fully functional. Semantic validation detects issues, classifies them, and proposes repairs using LLM-based reasoning.

---

## Phase 8: User Story 6 - Inspect Multi-Pass Execution (Priority: P2)

**Goal**: Implement execution history inspection that provides structured history of passes including plans, refinements, and convergence assessments.

**Independent Test**: Execute a multi-pass task, complete it (converged or TTL expired), and verify that developers can access and review a structured execution history containing: pass sequence with phase transitions, plan state snapshots per pass, refinement actions and changes, convergence assessments with scores and reason codes, and semantic validation reports.

**Dependencies**: Requires Phase 2 (kernel refactoring), Phase 3 (US1 - ExecutionHistory), Phase 4 (US2 - RefinementAction), Phase 5 (US3 - ConvergenceAssessment), Phase 7 (US5 - SemanticValidationReport).

### Tests for User Story 6

- [ ] T135 [P] [US6] Integration test for execution history access in tests/integration/test_execution_history.py
- [ ] T136 [P] [US6] Integration test for execution history pass sequence in tests/integration/test_execution_history.py
- [ ] T137 [P] [US6] Integration test for execution history plan snapshots in tests/integration/test_execution_history.py
- [ ] T138 [P] [US6] Integration test for execution history refinement actions in tests/integration/test_execution_history.py
- [ ] T139 [P] [US6] Integration test for execution history convergence assessments in tests/integration/test_execution_history.py
- [ ] T140 [P] [US6] Integration test for execution history semantic validation reports in tests/integration/test_execution_history.py

### Implementation for User Story 6

- [ ] T141 [US6] Enhance ExecutionHistory model with overall_statistics calculation in aeon/kernel/models.py
- [ ] T142 [US6] Implement execution history serialization for inspection in aeon/kernel/orchestrator.py
- [ ] T143 [US6] Implement execution history pass filtering and querying in aeon/kernel/orchestrator.py
- [ ] T144 [US6] Add execution history inspection helpers (get_pass, get_refinements, get_convergence) in aeon/kernel/orchestrator.py
- [ ] T145 [US6] Document execution history inspection API in quickstart.md examples

**Checkpoint**: At this point, User Story 6 should be fully functional. Developers can inspect execution history with all pass details, refinements, and assessments.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T146 [P] Update documentation with Sprint 2 capabilities in README.md
- [ ] T147 [P] Add usage examples to quickstart.md based on implementation
- [ ] T148 [P] Code cleanup and refactoring for consistency across modules
- [ ] T149 [P] Verify kernel LOC remains under 800 lines (should be <700 after refactoring)
- [ ] T150 [P] Add integration tests for end-to-end multi-pass execution scenarios in tests/integration/
- [ ] T151 [P] Add contract tests for all interfaces in tests/contract/
- [ ] T152 [P] Performance optimization for multi-pass execution
- [ ] T153 [P] Error handling improvements across all modules
- [ ] T154 [P] Code cleanup and refactoring for consistency
- [ ] T155 Run quickstart.md validation and update examples
- [ ] T156 [P] Add logging enhancements for multi-pass execution debugging
- [ ] T157 [P] Add observability metrics for pass counts, refinement counts, convergence rates

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1: US1, US2, US3, US5 → P2: US4, US6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **FOUNDATIONAL for other stories.**
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) and US1 - Integrates with US1 multi-pass loop, uses US5 semantic validation
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) and US1 - Integrates with US1 multi-pass loop, consumes US5 semantic validation
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) and US1 - Integrates with US1, US3, US5 for TaskProfile updates
- **User Story 5 (P1)**: Can start after Foundational (Phase 2) and US1 - Used by US2, US3, US4
- **User Story 6 (P2)**: Can start after Foundational (Phase 2) and US1, US2, US3, US5 - Depends on ExecutionHistory from US1, RefinementAction from US2, ConvergenceAssessment from US3, SemanticValidationReport from US5

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data models before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, P1 user stories (US1, US2, US3, US5) can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Data models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (respecting dependencies)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Integration test for multi-pass execution loop in tests/integration/test_multi_pass_execution.py"
Task: "Integration test for TTL expiration at phase boundary in tests/integration/test_ttl_expiration.py"
Task: "Integration test for TTL expiration mid-phase at safe boundary in tests/integration/test_ttl_expiration.py"
Task: "Integration test for deterministic phase sequence in tests/integration/test_deterministic_phases.py"

# Launch all data models for User Story 1 together:
Task: "Create ExecutionPass model in aeon/kernel/models.py"
Task: "Create ExecutionHistory model in aeon/kernel/models.py"
Task: "Create TTLExpirationResponse model in aeon/kernel/models.py"
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
3. Add User Story 5 (Semantic Validation) → Test independently → Deploy/Demo (enables US2, US3)
4. Add User Story 2 (Recursive Planning) → Test independently → Deploy/Demo
5. Add User Story 3 (Convergence) → Test independently → Deploy/Demo
6. Add User Story 4 (Adaptive Depth) → Test independently → Deploy/Demo
7. Add User Story 6 (Inspection) → Test independently → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (kernel refactoring is critical)
2. Once Foundational is done:
   - Developer A: User Story 1 (Multi-Pass Execution) - **FOUNDATIONAL**
   - Developer B: User Story 5 (Semantic Validation) - **ENABLES OTHERS**
3. Once US1 and US5 are done:
   - Developer A: User Story 2 (Recursive Planning)
   - Developer B: User Story 3 (Convergence)
   - Developer C: User Story 4 (Adaptive Depth)
4. Once US2, US3, US4 are done:
   - Developer A: User Story 6 (Inspection)
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Phase 2 (kernel refactoring) MUST be completed before any Sprint 2 user story work begins
- Kernel LOC must remain under 800 lines (target <700 after refactoring)
- All semantic reasoning MUST use LLM-based reasoning as primary mechanism
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Summary

**Total Tasks**: 157
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational - Kernel Refactoring): 14 tasks
- Phase 3 (User Story 1): 22 tasks
- Phase 4 (User Story 2): 21 tasks
- Phase 5 (User Story 3): 20 tasks
- Phase 6 (User Story 4): 24 tasks
- Phase 7 (User Story 5): 26 tasks
- Phase 8 (User Story 6): 11 tasks
- Phase 9 (Polish): 12 tasks

**Task Count per User Story**:
- US1: 22 tasks
- US2: 21 tasks
- US3: 20 tasks
- US4: 24 tasks
- US5: 26 tasks
- US6: 11 tasks

**Parallel Opportunities Identified**: 
- All [P] marked tasks can run in parallel within their phase
- User stories can be worked on in parallel after foundational phase (respecting dependencies)

**Independent Test Criteria**:
- US1: Submit complex task, verify multi-pass loop executes until convergence or TTL expires
- US2: Submit ambiguous task, verify recursive planning detects ambiguities and refines fragments
- US3: Execute task through multiple passes, verify convergence engine identifies convergence status
- US4: Submit simple and complex tasks, verify adaptive depth adjusts TTL and reasoning depth
- US5: Generate plan with issues, verify semantic validation detects and classifies issues
- US6: Execute multi-pass task, verify execution history provides structured pass information

**Suggested MVP Scope**: 
- Phase 1: Setup
- Phase 2: Foundational (MANDATORY kernel refactoring - CRITICAL - blocks all stories)
- Phase 3: User Story 1 (Multi-Pass Execution with Convergence) - **MVP**

**Format Validation**: ✅ All tasks follow the checklist format (checkbox, ID, [P] marker where applicable, [Story] label, file paths)
