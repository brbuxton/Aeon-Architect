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

- [X] T001 [P] Verify Python 3.11+ environment and dependencies in requirements.txt
- [X] T002 [P] Review existing project structure in aeon/ package
- [X] T003 [P] Verify test infrastructure (pytest, coverage) in tests/ directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: MANDATORY kernel refactoring that MUST be complete before ANY Sprint 2 user story can be implemented

**⚠️ CRITICAL**: No Sprint 2 user story work can begin until this phase is complete

### Kernel Refactoring - Analysis Phase

- [X] T004 Measure current LOC of aeon/kernel/orchestrator.py and aeon/kernel/executor.py
- [X] T005 Audit aeon/kernel/orchestrator.py to identify non-orchestration logic
- [X] T006 Audit aeon/kernel/executor.py to identify non-orchestration logic
- [X] T007 Document extractable functions, classes, or modules that can be moved externally
- [X] T008 Identify reduction targets to bring combined LOC below 700 lines

### Kernel Refactoring - Extraction Phase

- [X] T009 [P] Move non-orchestration utility functions from orchestrator.py to appropriate external modules
- [X] T010 [P] Move non-orchestration utility functions from executor.py to appropriate external modules
- [X] T011 [P] Extract data transformation logic to external modules if found in kernel
- [X] T012 [P] Extract validation helpers to external modules if found in kernel
- [X] T013 Verify all extracted code maintains clean interfaces
- [X] T014 Preserve all existing functionality and interfaces during extraction

### Kernel Refactoring - Validation Phase

- [X] T015 Run full regression test suite in tests/ to confirm no behavioral changes
- [X] T016 Verify combined LOC of aeon/kernel/orchestrator.py and aeon/kernel/executor.py is below 700 lines
- [X] T017 Confirm all interfaces remain unchanged (no breaking changes)
- [X] T018 Document refactoring changes with before/after LOC measurements

**Checkpoint**: Kernel refactoring complete - LOC < 700, all tests pass, no behavioral drift. Sprint 2 user story implementation can now begin.

---

## Phase 3: User Story 5 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

**Goal**: Implement semantic validation layer that validates step specificity, logical relevance, do/say mismatches, hallucinated tools, and consistency violations. This is foundational for other Sprint 2 features.

**Master Constraint**: All semantic validation MUST use LLM-based reasoning as the primary mechanism. Heuristics MAY only detect structural defects (duplicate IDs, malformed objects). Validation MUST produce deterministic JSON outputs parsed into ValidationIssue.

**Independent Test**: Generate a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verify that the semantic validation layer detects these issues, classifies them, assigns severity scores, and proposes semantic repairs.

### Implementation for User Story 5

- [ ] T019 [P] [US5] Create ValidationIssue model in aeon/validation/semantic_models.py
- [ ] T020 [P] [US5] Create SemanticValidationReport model in aeon/validation/semantic_models.py
- [ ] T021 [P] [US5] Create semantic validation interface in aeon/validation/semantic_interface.py
- [ ] T022 [US5] Implement LLM-based step specificity validator using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T023 [US5] Implement LLM-based logical relevance validator using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T024 [US5] Implement LLM-based do/say mismatch detector using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T025 [US5] Implement LLM-based hallucinated tool detector using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T026 [US5] Implement LLM-based internal consistency checker using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T027 [US5] Implement LLM-based cross-phase consistency validator using structured JSON output in aeon/validation/semantic_validator.py
- [ ] T028 [US5] Implement LLM-based issue classification and severity scoring with structured JSON output in aeon/validation/semantic_validator.py
- [ ] T029 [US5] Implement LLM-based semantic repair proposal generator with structured JSON output in aeon/validation/semantic_validator.py
- [ ] T030 [US5] Implement structural defect detection (duplicate IDs, malformed objects, missing attributes) as pre-validation filter in aeon/validation/semantic_validator.py
- [ ] T031 [US5] Integrate semantic validator with tool registry for tool existence checks
- [ ] T032 [US5] Implement supervisor-friendly hooks: get_issues() method returning ValidationIssue list in aeon/validation/semantic_validator.py
- [ ] T033 [US5] Implement supervisor-friendly hooks: get_rationale() method returning LLM reasoning explanations in aeon/validation/semantic_validator.py
- [ ] T034 [US5] Implement supervisor-friendly hooks: summarize() method for execution history integration in aeon/validation/semantic_validator.py
- [ ] T035 [US5] Add logging for semantic validation operations in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 5 should be fully functional and testable independently. Semantic validation can detect issues and produce validation reports.

---

## Phase 4: User Story 3 - Convergence Detection and Completion Assessment (Priority: P1)

**Goal**: Implement convergence engine that determines whether tasks are finished through completeness, coherence, and consistency checks. This directly controls termination condition for multi-pass execution.

**Master Constraint**: Convergence criteria MUST be judged by LLM-based explanation. Completeness/coherence/consistency MUST use LLM-internal reasoning, not lexical-fuzzy matching. LLM MUST return structured reason-code set. Convergence MUST NEVER be calculated via keyword overlap, empty-issue lists, or rule-based scoring only.

**Independent Test**: Execute a task through multiple passes and verify that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met, returning convergence status (true/false), reason codes, and evaluation metadata.

### Implementation for User Story 3

- [ ] T036 [P] [US3] Create ConvergenceAssessment model in aeon/convergence/models.py
- [ ] T037 [P] [US3] Create convergence engine interface in aeon/convergence/interface.py
- [ ] T038 [US3] Implement LLM-based completeness checker with structured reason codes in aeon/convergence/engine.py
- [ ] T039 [US3] Implement LLM-based coherence checker with structured reason codes in aeon/convergence/engine.py
- [ ] T040 [US3] Implement LLM-based cross-artifact consistency checker with structured reason codes in aeon/convergence/engine.py
- [ ] T041 [US3] Integrate convergence engine with semantic validation layer to consume validation reports
- [ ] T042 [US3] Implement LLM-based contradiction, omission, and hallucination detection using semantic validation input in aeon/convergence/engine.py
- [ ] T043 [US3] Implement configurable convergence criteria with sensible defaults in aeon/convergence/engine.py
- [ ] T044 [US3] Implement LLM-based reason code generation for convergence status with structured output in aeon/convergence/engine.py
- [ ] T045 [US3] Implement LLM-based evaluation metadata generation (completeness score, coherence score, detected issues) with structured output in aeon/convergence/engine.py
- [ ] T046 [US3] Handle conflicting convergence criteria (complete but incoherent, etc.) with LLM-generated reason codes in aeon/convergence/engine.py
- [ ] T047 [US3] Implement supervisor-friendly hooks: get_issues() method returning detected issues list in aeon/convergence/engine.py
- [ ] T048 [US3] Implement supervisor-friendly hooks: get_rationale() method returning LLM reasoning explanations in aeon/convergence/engine.py
- [ ] T049 [US3] Implement supervisor-friendly hooks: summarize() method for execution history integration in aeon/convergence/engine.py
- [ ] T050 [US3] Add logging for convergence assessments in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently. Convergence engine can evaluate execution results and determine convergence status.

---

## Phase 5: User Story 1 - Multi-Pass Execution with Convergence (Priority: P1) 🎯 MVP

**Goal**: Implement multi-pass execution loop with deterministic phase boundaries (plan → execute → evaluate → refine → re-execute → converge → stop). This is the foundational transformation from single-pass to multi-pass execution.

**Independent Test**: Submit a complex, ambiguous task (e.g., "design a system architecture for a web application with user authentication") and verify that Aeon executes multiple passes (plan → execute → evaluate → refine → re-execute) until convergence is achieved or TTL expires.

### Implementation for User Story 1

**Master Constraint**: Refinement MUST be driven by structured LLM feedback only. The loop MUST treat the LLM as the cognitive core. Refinement MUST be targeted (modify only steps flagged by validator). No heuristic-based convergence shortcuts allowed.

- [ ] T051 [P] [US1] Create ExecutionPass model in aeon/kernel/multipass_models.py
- [ ] T052 [P] [US1] Create RefinementAction model in aeon/kernel/multipass_models.py
- [ ] T053 [US1] Upgrade existing orchestrator.py from single-pass to multi-pass loop architecture in aeon/kernel/orchestrator.py
- [ ] T054 [US1] Implement phase boundary management (plan → execute → evaluate → refine → re-execute) with LLM-driven phase transitions in aeon/kernel/orchestrator.py
- [ ] T055 [US1] Integrate convergence engine into evaluate phase in aeon/kernel/orchestrator.py
- [ ] T056 [US1] Integrate semantic validation into evaluate phase in aeon/kernel/orchestrator.py
- [ ] T057 [US1] Implement LLM-driven refinement phase with attempt limits (3 per fragment, 10 global) in aeon/kernel/orchestrator.py
- [ ] T058 [US1] Implement targeted refinement (modify only steps flagged by validator, not wholesale regeneration) in aeon/kernel/orchestrator.py
- [ ] T059 [US1] Integrate supervisor repair pipeline into refinement phase in aeon/kernel/orchestrator.py
- [ ] T060 [US1] Implement TTL expiration handling at phase boundaries in aeon/kernel/orchestrator.py
- [ ] T061 [US1] Implement mid-phase TTL expiration at safe step boundaries in aeon/kernel/orchestrator.py
- [ ] T062 [US1] Implement termination logic (convergence OR TTL expiration) in aeon/kernel/orchestrator.py
- [ ] T063 [US1] Implement TTL-expired result formatting with metadata in aeon/kernel/orchestrator.py
- [ ] T064 [US1] Implement deterministic phase sequence enforcement in aeon/kernel/orchestrator.py
- [ ] T065 [US1] Handle supervisor repair failures during refinement phase in aeon/kernel/orchestrator.py
- [ ] T066 [US1] Preserve declarative plan nature during refinement in aeon/kernel/orchestrator.py
- [ ] T067 [US1] Add logging for multi-pass execution phases in aeon/observability/logger.py
- [ ] T068 [US1] Update kernel orchestrator to use multi-pass loop for complex tasks

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Multi-pass execution loop can iterate through passes until convergence or TTL expiration.

---

## Phase 6: User Story 2 - Recursive Planning and Plan Refinement (Priority: P1)

**Goal**: Implement recursive planning that detects missing details, generates follow-up questions, creates subplans for complex steps, and refines plan fragments without discarding the entire plan.

**Independent Test**: Submit an ambiguous task (e.g., "build a REST API") and verify that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments, and automatically incorporates semantic validation into the refinement process.

### Implementation for User Story 2

**Master Constraint**: Subplans MUST be generated by LLM decomposition, not heuristic splitting. Refinements MUST be delta-style edits, not full-plan rewrites. Planner MUST output structured graph with rationale. Planner MUST preserve stable IDs between passes. Planner MUST produce explainable changes. Planner MUST consider validator issues as constraints.

- [ ] T069 [P] [US2] Create Subplan model in aeon/plan/recursive_models.py
- [ ] T070 [P] [US2] Create recursive planner interface in aeon/plan/recursive_interface.py
- [ ] T071 [US2] Implement LLM-based ambiguous fragment detector with structured output in aeon/plan/recursive_planner.py
- [ ] T072 [US2] Implement LLM-based low-specificity fragment detector with structured output in aeon/plan/recursive_planner.py
- [ ] T073 [US2] Implement LLM-based follow-up question generator with structured output in aeon/plan/recursive_planner.py
- [ ] T074 [US2] Implement LLM-based subplan creator for complex steps with structured graph output and rationale in aeon/plan/recursive_planner.py
- [ ] T075 [US2] Implement LLM-based nested step generator with structured graph output in aeon/plan/recursive_planner.py
- [ ] T076 [US2] Implement delta-style partial plan fragment rewrite (add, modify, remove operations) in aeon/plan/recursive_planner.py
- [ ] T077 [US2] Implement stable ID preservation across refinement operations in aeon/plan/recursive_planner.py
- [ ] T078 [US2] Implement explainable changes with LLM-generated rationale for each refinement in aeon/plan/recursive_planner.py
- [ ] T079 [US2] Integrate semantic validation into recursive planning flow, treating validator issues as constraints in aeon/plan/recursive_planner.py
- [ ] T080 [US2] Implement plan structure preservation during refinement in aeon/plan/recursive_planner.py
- [ ] T081 [US2] Implement per-fragment refinement attempt limits (3 attempts) in aeon/plan/recursive_planner.py
- [ ] T082 [US2] Implement global refinement attempt limit (10 total) in aeon/plan/recursive_planner.py
- [ ] T083 [US2] Implement manual intervention marking for fragments at limit in aeon/plan/recursive_planner.py
- [ ] T084 [US2] Implement nesting depth limit enforcement of 5 levels in aeon/plan/recursive_planner.py
- [ ] T085 [US2] Implement graceful failure handling for depth limit exceeded in aeon/plan/recursive_planner.py
- [ ] T086 [US2] Implement conflict resolution between semantic validation and recursive planner refinements in aeon/plan/recursive_planner.py
- [ ] T087 [US2] Ensure plans remain declarative (JSON/YAML) during recursive planning in aeon/plan/recursive_planner.py
- [ ] T088 [US2] Implement supervisor-friendly hooks: get_delta() method returning structured refinement operations in aeon/plan/recursive_planner.py
- [ ] T089 [US2] Implement supervisor-friendly hooks: get_rationale() method returning LLM reasoning explanations in aeon/plan/recursive_planner.py
- [ ] T090 [US2] Implement supervisor-friendly hooks: summarize() method for execution history integration in aeon/plan/recursive_planner.py
- [ ] T091 [US2] Add logging for recursive planning operations in aeon/observability/logger.py
- [ ] T092 [US2] Integrate recursive planner with multi-pass loop refinement phase

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently. Recursive planning can detect ambiguities, create subplans, and refine plan fragments.

---

## Phase 7: User Story 4 - Adaptive Reasoning Depth Based on Task Complexity (Priority: P2)

**Goal**: Implement adaptive depth heuristics that adjust reasoning depth, TTL allocations, and processing strategies based on detected complexity, ambiguity, or uncertainty levels.

**Independent Test**: Submit both simple tasks (e.g., "add two numbers") and complex tasks (e.g., "design a distributed system architecture") and verify that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on detected complexity.

### Implementation for User Story 4

**Master Constraint**: Depth decisions MUST use LLM-based "task complexity self-assessment." TTL increases/decreases MUST be determined by LLM analysis of ambiguity, uncertainty, dependency depth, reasoning complexity. No "word count," "token length," or heuristic approximations allowed.

- [ ] T093 [P] [US4] Create AdaptiveDepthConfiguration model in aeon/adaptive/models.py
- [ ] T094 [P] [US4] Create adaptive depth interface in aeon/adaptive/interface.py
- [ ] T095 [US4] Implement LLM-based TaskProfile inference engine and define TaskProfile schema and interface contract in aeon/adaptive/heuristics.py
- [ ] T095a [US4] Create TaskProfile model with fields: profile_version, reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference in aeon/adaptive/models.py
- [ ] T095b [US4] Implement TaskProfile versioning and update triggers at pass boundaries in aeon/adaptive/heuristics.py
- [ ] T095c [US4] Add recording of TaskProfile version transitions to execution history, including initial_profile_version, updated_profile_versions[], and revision_reason metadata.
- [ ] T096 [US4] Implement LLM-based information_sufficiency dimension extraction in aeon/adaptive/heuristics.py
- [ ] T097 [US4] Implement token-pattern analysis as secondary signal (not primary) for complexity indicators in aeon/adaptive/heuristics.py
- [ ] T098 [US4] Implement LLM-based TTL allocation based on TaskProfile reasoning_depth and information_sufficiency in aeon/adaptive/heuristics.py
- [ ] T099 [US4] Implement LLM-based reasoning_depth selection based on TaskProfile in aeon/adaptive/heuristics.py
- [ ] T100 [US4] Implement global TTL and resource cap enforcement in aeon/adaptive/heuristics.py
- [ ] T101 [US4] Implement LLM-based bidirectional TTL adjustment (increase and decrease) in aeon/adaptive/heuristics.py
- [ ] T102 [US4] Implement LLM-based complexity assessment revision during execution in aeon/adaptive/heuristics.py
- [ ] T103 [US4] Integrate with semantic validation for complexity indicators (as secondary signals) in aeon/adaptive/heuristics.py
- [ ] T104 [US4] Integrate with convergence engine for depth decisions in aeon/adaptive/heuristics.py
- [ ] T105 [US4] Integrate with recursive planner for depth decisions in aeon/adaptive/heuristics.py
- [ ] T106 [US4] Implement LLM-based adjustment reason tracking in aeon/adaptive/heuristics.py
- [ ] T107 [US4] Implement supervisor-friendly hooks: get_rationale() method returning LLM reasoning explanations in aeon/adaptive/heuristics.py
- [ ] T108 [US4] Implement supervisor-friendly hooks: summarize() method for execution history integration in aeon/adaptive/heuristics.py
- [ ] T109 [US4] Add logging for adaptive depth adjustments in aeon/observability/logger.py
- [ ] T110 [US4] Integrate adaptive depth with multi-pass loop for TTL allocation

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently. Adaptive depth can detect complexity and adjust reasoning depth and TTL allocations.

---

## Phase 8: User Story 6 - Inspect Multi-Pass Execution (Priority: P2)

**Goal**: Implement execution inspection capability that provides structured history of passes including plans, refinements, and convergence assessments for debugging and tuning.

**Independent Test**: Execute a multi-pass task, complete it (converged or TTL expired), and verify that developers can access and review a structured execution history containing: pass sequence with phase transitions, plan state snapshots per pass, refinement actions and changes, convergence assessments with scores and reason codes, and semantic validation reports.

### Implementation for User Story 6

- [ ] T111 [P] [US6] Create ExecutionHistory model in aeon/kernel/history_models.py
- [ ] T112 [P] [US6] Create execution history interface in aeon/kernel/history_interface.py
- [ ] T113 [US6] Implement pass sequence recording in aeon/kernel/history_recorder.py
- [ ] T114 [US6] Implement plan state snapshot capture per pass in aeon/kernel/history_recorder.py
- [ ] T115 [US6] Implement refinement action recording in aeon/kernel/history_recorder.py
- [ ] T116 [US6] Implement convergence assessment recording in aeon/kernel/history_recorder.py
- [ ] T117 [US6] Implement semantic validation report recording in aeon/kernel/history_recorder.py
- [ ] T118 [US6] Implement adaptive depth configuration recording, including TaskProfile snapshot and adjustment_reason, in execution history for each pass (FR-078), in aeon/kernel/history_recorder.py
- [ ] T119 [US6] Implement timing information capture in aeon/kernel/history_recorder.py
- [ ] T120 [US6] Implement execution history accessor/query interface in aeon/kernel/history_recorder.py
- [ ] T121 [US6] Integrate history recording with multi-pass loop in aeon/kernel/orchestrator.py
- [ ] T122 [US6] Add logging for execution history operations in aeon/observability/logger.py

**Checkpoint**: At this point, User Story 6 should be fully functional and testable independently. Developers can inspect execution history for debugging and tuning.

---

## Phase 9: Supervisor Integration & Repair Pipeline (Mandatory)

**Purpose**: Implement supervisor integration requirements ensuring all cognitive modules expose supervisor-friendly hooks and the supervisor orchestrates semantic repair workflows.

**Master Constraint**: Supervisor MUST NOT perform any semantic reasoning. Supervisor MUST delegate all semantic judgments to LLM-backed modules. Supervisor MUST use only structured signals (issues, deltas, rationale).

### Supervisor Integration Requirements

- [ ] T123 [P] Create SupervisorAssessment model in aeon/supervisor/models.py
- [ ] T124 [P] Create SupervisorRepairPipeline class in aeon/supervisor/repair_pipeline.py
- [ ] T125 [SUP] Implement SupervisorRepairPipeline.supervise(plan, artifacts) → SupervisorAssessment method in aeon/supervisor/repair_pipeline.py
- [ ] T126 [SUP] Implement SupervisorRepairPipeline.apply_repairs(plan, repairs) → RefinedPlan method in aeon/supervisor/repair_pipeline.py
- [ ] T127 [SUP] Implement SupervisorRepairPipeline.log_pass(pass_context) method in aeon/supervisor/repair_pipeline.py
- [ ] T128 [SUP] Implement SupervisorRepairPipeline.should_continue(pass_context) → bool method in aeon/supervisor/repair_pipeline.py
- [ ] T129 [SUP] Implement SupervisorRepairPipeline.finalize(plan, artifacts) → FinalResult method in aeon/supervisor/repair_pipeline.py
- [ ] T130 [SUP] Implement supervisor consumption of SemanticValidationReport in aeon/supervisor/repair_pipeline.py
- [ ] T131 [SUP] Implement supervisor application of targeted refinement actions (delta-style, not full-plan regeneration) in aeon/supervisor/repair_pipeline.py
- [ ] T132 [SUP] Implement structured repair log per pass in aeon/supervisor/repair_pipeline.py
- [ ] T133 [SUP] Implement supervisor update of ExecutionHistory with repair deltas in aeon/supervisor/repair_pipeline.py
- [ ] T134 [SUP] Implement supervisor integration of all cognitive outputs (SemanticValidationReport, RecursivePlanner deltas, ConvergenceAssessment, AdaptiveDepth decisions) in aeon/supervisor/repair_pipeline.py
- [ ] T135 [SUP] Implement unified SupervisorAssessment object generation each pass in aeon/supervisor/repair_pipeline.py
- [ ] T136 [SUP] Implement multi-pass iteration tracking (passes, refinements, corrections) in aeon/supervisor/repair_pipeline.py
- [ ] T137 [SUP] Implement termination condition detection in supervisor in aeon/supervisor/repair_pipeline.py
- [ ] T138 [SUP] Implement escalation of blocking issues to caller via structured output in aeon/supervisor/repair_pipeline.py
- [ ] T139 [SUP] Ensure supervisor uses only structured signals (no semantic inference) in aeon/supervisor/repair_pipeline.py
- [ ] T140 [SUP] Verify all cognitive modules expose required supervisor hooks (get_issues, get_delta, get_rationale, summarize) in aeon/supervisor/repair_pipeline.py
- [ ] T141 [SUP] Integrate SupervisorRepairPipeline with multi-pass loop refinement phase in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, supervisor integration is complete. All cognitive modules expose supervisor-friendly hooks, and supervisor orchestrates semantic repair workflows without performing semantic reasoning.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Integration, testing, and improvements that affect multiple user stories

- [ ] T142 [P] Verify all Tier-1 features integrate seamlessly without circular dependencies
- [ ] T143 [P] Run integration tests for multi-pass execution with all features in tests/integration/
- [ ] T144 [P] Verify kernel LOC remains under 800 lines (should be <700 after refactoring)
- [ ] T145 [P] Update documentation in README.md and docs/ with Sprint 2 capabilities
- [ ] T146 [P] Add comprehensive integration tests in tests/integration/test_multipass_integration.py
- [ ] T147 [P] Add unit tests for new modules in tests/unit/
- [ ] T148 [P] Verify declarative plan purity maintained throughout all features
- [ ] T149 [P] Verify deterministic execution model maintained (same inputs produce same phase transitions)
- [ ] T150 [P] Verify all semantic/cognitive/evaluative functionality uses LLM-based reasoning (Master Constraint compliance)
- [ ] T151 [P] Verify all cognitive modules expose supervisor-friendly hooks
- [ ] T152 [P] Verify supervisor uses only structured signals (no semantic inference)
- [ ] T153 [P] Performance testing and optimization across all Sprint 2 features
- [ ] T154 [P] Code cleanup and refactoring for consistency
- [ ] T155 [P] Security review for new interfaces and modules
- [ ] T156 [P] Verify declarative plan compliance
- [ ] T157 [P] Verify deterministic execution
- [ ] T158 [P] Verify kernel LOC remains <800
- [ ] T159 [P] Verify modular integration boundaries
- [ ] T160 [P] Measure convergence rate
- [ ] T161 [P] Evaluate refinement efficiency
- [ ] T162 [P] Validate semantic-issue detection accuracy
- [ ] T163 [P] Measure taskprofile stability accuracy

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
- **Supervisor Integration (Phase 9)**: Depends on User Stories 1, 2, 3, 4, 5 (needs all cognitive modules)
- **Polish (Phase 10)**: Depends on all desired user stories and supervisor integration being complete

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
- **MASTER CONSTRAINT**: All semantic, cognitive, or evaluative functionality MUST use LLM-based reasoning as primary mechanism
- **SUPERVISOR INTEGRATION**: All cognitive modules MUST expose supervisor-friendly hooks (get_issues, get_delta, get_rationale, summarize)
- **ALGORITHMIC GUIDANCE**: Refinements MUST be delta-style edits, not full-plan rewrites. All outputs MUST be structured JSON, not free-form text

---

## Task Summary

- **Total Tasks**: 143
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational - Kernel Refactoring)**: 15 tasks
- **Phase 3 (User Story 5 - Semantic Validation)**: 17 tasks (added supervisor hooks)
- **Phase 4 (User Story 3 - Convergence Engine)**: 15 tasks (added supervisor hooks, LLM-based requirements)
- **Phase 5 (User Story 1 - Multi-Pass Execution)**: 18 tasks (added LLM-driven refinement requirements)
- **Phase 6 (User Story 2 - Recursive Planning)**: 24 tasks (added delta-style edits, supervisor hooks)
- **Phase 7 (User Story 4 - Adaptive Depth)**: 18 tasks (added LLM-based complexity assessment, supervisor hooks)
- **Phase 8 (User Story 6 - Execution Inspection)**: 12 tasks
- **Phase 9 (Supervisor Integration)**: 19 tasks (new phase)
- **Phase 10 (Polish)**: 14 tasks (added Master Constraint compliance checks)

### Parallel Opportunities

- **Phase 1**: 3 parallel tasks
- **Phase 2**: 4 parallel extraction tasks
- **Phase 3**: 3 parallel model/interface tasks
- **Phase 4**: 2 parallel model/interface tasks
- **Phase 5**: 2 parallel model tasks
- **Phase 6**: 2 parallel model/interface tasks
- **Phase 7**: 2 parallel model/interface tasks
- **Phase 8**: 2 parallel model/interface tasks
- **Phase 9**: 2 parallel supervisor model tasks
- **Phase 10**: 14 parallel polish tasks

### Suggested MVP Scope

**MVP**: Phases 1-5 (Setup + Foundational + User Stories 5, 3, 1)
- This delivers core multi-pass execution with convergence detection and semantic validation
- Total MVP tasks: 68 tasks (updated with Master Constraint and supervisor hooks)
- Can be delivered incrementally: Setup → Foundational → US5 → US3 → US1
