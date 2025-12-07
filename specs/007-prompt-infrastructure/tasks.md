# Tasks: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Input**: Design documents from `/specs/007-prompt-infrastructure/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Level 1 prompt tests are included per spec requirement FR-029.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `aeon/` at repository root
- **Tests**: `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `aeon/prompts/` directory structure with `__init__.py` in `aeon/prompts/__init__.py`
- [ ] T002 [P] Create test directory structure `tests/unit/prompts/` with `__init__.py` in `tests/unit/prompts/__init__.py`
- [ ] T003 [P] Create test directory structure `tests/integration/` for Phase E tests (if not exists)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create base exception classes in `aeon/prompts/registry.py`: `PromptNotFoundError`, `NoOutputModelError`, `RenderingError`
- [ ] T005 Create base `PromptInput` class in `aeon/prompts/registry.py` (Pydantic BaseModel)
- [ ] T006 Create base `PromptOutput` class in `aeon/prompts/registry.py` (Pydantic BaseModel)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Centralized Prompt Management (Priority: P1) 🎯 MVP

**Goal**: Establish a centralized prompt registry containing all system prompts, accessible by unique identifiers, with all inline prompts extracted and removed from source modules.

**Independent Test**: Query the prompt registry for all known prompt identifiers and verify that each prompt can be retrieved with its associated input/output schemas. Search codebase for inline prompt strings and verify zero matches outside the registry.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Create test for prompt registry initialization in `tests/unit/prompts/test_registry.py`
- [ ] T008 [P] [US1] Create test for prompt retrieval by identifier in `tests/unit/prompts/test_registry.py`
- [ ] T009 [P] [US1] Create test for location invariant (no inline prompts) in `tests/unit/prompts/test_registry.py`
- [ ] T010 [P] [US1] Create test for registration invariant (all PromptIds have entries) in `tests/unit/prompts/test_registry.py`

### Implementation for User Story 1

- [ ] T011 [US1] Create `PromptId` enum in `aeon/prompts/registry.py` with all prompt identifiers (PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, REASONING_STEP_SYSTEM, REASONING_STEP_USER, VALIDATION_SEMANTIC_SYSTEM, VALIDATION_SEMANTIC_USER, CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER, TASKPROFILE_INFERENCE_SYSTEM, TASKPROFILE_INFERENCE_USER, TASKPROFILE_UPDATE_SYSTEM, TASKPROFILE_UPDATE_USER, RECURSIVE_PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_SYSTEM, RECURSIVE_REFINEMENT_USER, SUPERVISOR_REPAIR_SYSTEM, SUPERVISOR_REPAIR_JSON_USER, SUPERVISOR_REPAIR_TOOLCALL_USER, SUPERVISOR_REPAIR_PLAN_USER, SUPERVISOR_REPAIR_MISSINGTOOL_USER, ANSWER_SYNTHESIS_SYSTEM, ANSWER_SYNTHESIS_USER)
- [ ] T012 [US1] Create `PromptDefinition` class in `aeon/prompts/registry.py` with fields: prompt_id, template, input_model, output_model (optional), render_fn
- [ ] T013 [US1] Create `PromptRegistry` class in `aeon/prompts/registry.py` with `_registry: Dict[PromptId, PromptDefinition]` and `__init__()` method
- [ ] T014 [US1] Implement `get_prompt(prompt_id: PromptId, input_data: PromptInput) -> str` method in `PromptRegistry` class in `aeon/prompts/registry.py`
- [ ] T015 [US1] Implement `list_prompts() -> List[PromptId]` method in `PromptRegistry` class in `aeon/prompts/registry.py`
- [ ] T016 [US1] Create module-level `get_prompt()` convenience function in `aeon/prompts/registry.py` that uses global registry instance
- [ ] T017 [US1] Extract plan generation prompts from `aeon/plan/prompts.py` and register in `aeon/prompts/registry.py` (PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, REASONING_STEP_USER)
- [ ] T018 [US1] Extract all recursive planning prompts from `aeon/plan/recursive.py` and register them in `aeon/prompts/registry.py` (RECURSIVE_PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_USER, RECURSIVE_REFINEMENT_SYSTEM)
- [ ] T019 [US1] Extract semantic validation prompts from `aeon/validation/semantic.py` and register in `aeon/prompts/registry.py` (VALIDATION_SEMANTIC_SYSTEM, VALIDATION_SEMANTIC_USER)
- [ ] T020 [US1] Extract convergence assessment prompts from `aeon/convergence/engine.py` and register in `aeon/prompts/registry.py` (CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER)
- [ ] T021 [US1] Extract TaskProfile prompts from `aeon/adaptive/heuristics.py` and register in `aeon/prompts/registry.py` (TASKPROFILE_INFERENCE_SYSTEM, TASKPROFILE_INFERENCE_USER, TASKPROFILE_UPDATE_SYSTEM, TASKPROFILE_UPDATE_USER)
- [ ] T022 [US1] Extract ALL repair-related prompts from `aeon/supervisor/repair.py` (SUPERVISOR_REPAIR_SYSTEM, SUPERVISOR_REPAIR_JSON_USER, SUPERVISOR_REPAIR_TOOLCALL_USER, SUPERVISOR_REPAIR_PLAN_USER, SUPERVISOR_REPAIR_MISSINGTOOL_USER) and register each with its own PromptId in `aeon/prompts/registry.py`.
- [ ] T082 [US1] Extract ALL repair-related prompts from `aeon/kernel/executor.py` (REASONING_STEP_SYSTEM) and register each with its own PromptId in `aeon/prompts/registry.py`.
- [ ] T023 [US1] Remove inline prompt imports from `aeon/kernel/executor.py` and replace with registry lookups
- [ ] T024 [US1] Remove inline prompt imports from `aeon/kernel/orchestrator.py` and replace with registry lookups
- [ ] T025 [US1] Remove inline prompts from `aeon/plan/prompts.py` and update to use registry
- [ ] T026 [US1] Remove inline prompts from `aeon/validation/semantic.py` and update to use registry
- [ ] T027 [US1] Remove inline prompts from `aeon/convergence/engine.py` and update to use registry
- [ ] T028 [US1] Remove inline prompts from `aeon/adaptive/heuristics.py` and update to use registry
- [ ] T029 [US1] Remove inline prompts from `aeon/supervisor/repair.py` and update to use registry
- [ ] T030 [US1] Initialize global `PromptRegistry` instance at module level in `aeon/prompts/registry.py`
- [ ] T031 [US1] Verify location invariant: run automated search for inline prompts and confirm zero matches outside registry

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. All prompts are centralized in the registry, and all inline prompts have been removed.

---

## Phase 4: User Story 2 - Schema-Backed Prompt Contracts (Priority: P2)

**Goal**: Define typed input and output models (Pydantic) for all prompts, enabling validation of prompt inputs before rendering and prompt outputs after LLM responses.

**Independent Test**: Create a prompt contract with defined input and output models, then verify that invalid inputs are rejected and valid inputs produce correctly structured outputs. Verify all prompts have input models and JSON-producing prompts have output models.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T032 [P] [US2] Create test for input model validation (reject invalid inputs) in `tests/unit/prompts/test_registry.py`
- [ ] T033 [P] [US2] Create test for prompt rendering with validated input in `tests/unit/prompts/test_registry.py`
- [ ] T034 [P] [US2] Create test for output model validation for JSON prompts in `tests/unit/prompts/test_registry.py`
- [ ] T035 [P] [US2] Create test for schema invariant (all prompts have input models) in `tests/unit/prompts/test_registry.py`

### Implementation for User Story 2

- [ ] T036 [US2] Create input models for plan generation prompts (`PlanGenerationInput`) in `aeon/prompts/registry.py`
- [ ] T037 [US2] Create input models for semantic validation prompts (`SemanticValidationInput`) in `aeon/prompts/registry.py`
- [ ] T038 [US2] Create input models for convergence assessment prompts (`ConvergenceAssessmentInput`) in `aeon/prompts/registry.py`
- [ ] T039 [US2] Create input models for TaskProfile prompts (`TaskProfileInferenceInput`, `TaskProfileUpdateInput`) in `aeon/prompts/registry.py`
- [ ] T040 [US2] Create input models for repair prompts (`RepairInput`) in `aeon/prompts/registry.py`
- [ ] T041 [US2] Create input models for reasoning prompts (`ReasoningInput`) in `aeon/prompts/registry.py`
- [ ] T042 [US2] Create output models for JSON-producing prompts: `ConvergenceAssessmentOutput` in `aeon/prompts/registry.py`
- [ ] T043 [US2] Create output models for JSON-producing prompts: `TaskProfileInferenceOutput` in `aeon/prompts/registry.py`
- [ ] T044 [US2] Create output models for JSON-producing prompts: `TaskProfileUpdateOutput` in `aeon/prompts/registry.py`
- [ ] T045 [US2] Update `PromptDefinition.render()` method in `aeon/prompts/registry.py` to validate input_data against input_model before rendering
- [ ] T046 [US2] Implement `validate_output(prompt_id: PromptId, llm_response: str) -> PromptOutput` method in `PromptRegistry` class in `aeon/prompts/registry.py`
- [ ] T047 [US2] Update all prompt definitions in `aeon/prompts/registry.py` to include input_model for each prompt
- [ ] T048 [US2] Update JSON-producing prompt definitions in `aeon/prompts/registry.py` to include output_model
- [ ] T049 [US2] Update prompt rendering functions in `aeon/prompts/registry.py` to use f-strings with Pydantic model field access
- [ ] T050 [US2] Update all modules using prompts to pass typed input models instead of raw dictionaries
- [ ] T051 [US2] Verify schema invariant: all prompts have input models, JSON-producing prompts have output models

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. All prompts have typed contracts with validation.

---

## Phase 5: User Story 3 - Final Answer Synthesis (Priority: P1)

**Goal**: Implement Phase E (Answer Synthesis) that consolidates execution results, plan state, and convergence information into a coherent final answer, integrated at the C-loop exit point in the orchestration engine.

**Independent Test**: Execute a request through the full A→B→C→D cycle, then verify that Phase E produces a structured final answer containing synthesized text, confidence indicators, and metadata about the execution.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T052 [P] [US3] Create test for Phase E successful synthesis in `tests/integration/test_phase_e.py`
- [ ] T053 [P] [US3] Create test for Phase E with TTL expiration in `tests/integration/test_phase_e.py`
- [ ] T054 [P] [US3] Create test for Phase E with incomplete data in `tests/integration/test_phase_e.py`
- [ ] T055 [P] [US3] Create test for Phase E integration at C-loop exit in `tests/integration/test_phase_e.py`

### Implementation for User Story 3

- [ ] T056 [US3] Create `PhaseEInput` model in `aeon/orchestration/phases.py` with all required fields (request, execution_results, plan_state, convergence_assessment, correlation_id, execution_start_timestamp, convergence_status, total_passes, total_refinements, ttl_remaining) and optional fields (execution_passes, semantic_validation, task_profile)
- [ ] T057 [US3] Create `FinalAnswer` model in `aeon/orchestration/phases.py` with required field (answer_text) and optional fields (confidence, used_step_ids, notes, ttl_exhausted, metadata)
- [ ] T058 [US3] Create input models for Phase E synthesis prompts (`AnswerSynthesisInput`) in `aeon/prompts/registry.py`
- [ ] T059 [US3] Create output model for Phase E synthesis prompts (`FinalAnswerOutput`) in `aeon/prompts/registry.py` (maps to FinalAnswer)
- [ ] T060 [US3] Register ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER prompts in `aeon/prompts/registry.py` with AnswerSynthesisInput and FinalAnswerOutput models
- [ ] T061 [US3] Implement `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer` function in `aeon/orchestration/phases.py`
- [ ] T062 [US3] Implement prompt retrieval and rendering for Phase E synthesis in `execute_phase_e()` function in `aeon/orchestration/phases.py`
- [ ] T063 [US3] Implement LLM call for synthesis in `execute_phase_e()` function in `aeon/orchestration/phases.py`
- [ ] T064 [US3] Implement output validation against FinalAnswer model in `execute_phase_e()` function in `aeon/orchestration/phases.py`
- [ ] T065 [US3] Implement degraded mode handling (errors, TTL expiration, incomplete data) in `execute_phase_e()` function in `aeon/orchestration/phases.py`
- [ ] T066 [US3] Register Phase E in phases system (if phase registration is required) in `aeon/orchestration/phases.py`
- [ ] T067 [US3] Wire Phase E invocation at C-loop exit point in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py` (after `_execute_phase_c_loop` returns, before building final execution result)
- [ ] T068 [US3] Build PhaseEInput from final execution state in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py`
- [ ] T069 [US3] Call `execute_phase_e()` with PhaseEInput in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py`
- [ ] T070 [US3] Attach FinalAnswer to execution result in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py`
- [ ] T071 [US3] Verify Phase E produces final_answer in all scenarios (successful convergence, TTL expiration, partial execution, error conditions)

**Checkpoint**: At this point, all three user stories should be independently functional. Phase E completes the A→B→C→D→E reasoning loop.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, validation, and cleanup

- [ ] T072 [P] Run all Level 1 prompt tests to verify: model instantiation, prompt rendering, output-model loading, invariant enforcement in `tests/unit/prompts/test_registry.py`
- [ ] T073 [P] Run all Phase E integration tests in `tests/integration/test_phase_e.py`
- [ ] T074 [P] Verify kernel LOC remains under 800 (Constitution Principle I) by checking `aeon/kernel/` module sizes
- [ ] T075 [P] Verify kernel minimalism: only prompt removal and Phase E wiring in kernel, no new business logic in `aeon/kernel/`
- [ ] T076 [P] Verify separation of concerns: prompt registry and Phase E are outside kernel per Constitution Principle II
- [ ] T077 [P] Run quickstart.md validation scenarios from `specs/007-prompt-infrastructure/quickstart.md`
- [ ] T078 [P] Verify all three invariants pass automated tests: Location Invariant, Schema Invariant, Registration Invariant
- [ ] T079 [P] Code cleanup and refactoring: remove unused imports, fix linting issues
- [ ] T080 [P] Documentation updates: add docstrings to all new classes and functions in `aeon/prompts/registry.py` and `aeon/orchestration/phases.py`
- [ ] T081 [P] Verify backward compatibility: existing execution flows still work with new prompt registry

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (P1 must complete before P2 can begin per spec dependencies)
- **User Story 3 (Phase 5)**: Depends on User Story 2 completion (P2 must complete before P3 can begin per spec dependencies, as Phase E prompts must use contract system)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Prompt Consolidation**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2) - Prompt Contracts**: MUST start after User Story 1 completes - Requires centralized registry to exist before contracts can be enforced
- **User Story 3 (P1) - Phase E**: MUST start after User Story 2 completes - Requires contract system for Phase E prompts

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services/implementations
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Prompt extraction tasks (T017-T022) can run in parallel (different source files)
- Prompt removal tasks (T023-T029) can run in parallel (different source files)
- Input model creation tasks (T036-T041) can run in parallel (different models)
- Output model creation tasks (T042-T044) can run in parallel (different models)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Create test for prompt registry initialization in tests/unit/prompts/test_registry.py"
Task: "Create test for prompt retrieval by identifier in tests/unit/prompts/test_registry.py"
Task: "Create test for location invariant (no inline prompts) in tests/unit/prompts/test_registry.py"
Task: "Create test for registration invariant (all PromptIds have entries) in tests/unit/prompts/test_registry.py"

# Launch all prompt extraction tasks together (different source files):
Task: "Extract plan generation prompts from aeon/plan/prompts.py"
Task: "Extract semantic validation prompts from aeon/validation/semantic.py"
Task: "Extract convergence assessment prompts from aeon/convergence/engine.py"
Task: "Extract TaskProfile prompts from aeon/adaptive/heuristics.py"
Task: "Extract repair prompts from aeon/supervisor/repair.py"

# Launch all prompt removal tasks together (different source files):
Task: "Remove inline prompts from aeon/plan/prompts.py"
Task: "Remove inline prompts from aeon/validation/semantic.py"
Task: "Remove inline prompts from aeon/convergence/engine.py"
Task: "Remove inline prompts from aeon/adaptive/heuristics.py"
Task: "Remove inline prompts from aeon/supervisor/repair.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch all input model creation tasks together (different models):
Task: "Create input models for plan generation prompts in aeon/prompts/registry.py"
Task: "Create input models for semantic validation prompts in aeon/prompts/registry.py"
Task: "Create input models for convergence assessment prompts in aeon/prompts/registry.py"
Task: "Create input models for TaskProfile prompts in aeon/prompts/registry.py"
Task: "Create input models for repair prompts in aeon/prompts/registry.py"
Task: "Create input models for reasoning prompts in aeon/prompts/registry.py"

# Launch all output model creation tasks together (different models):
Task: "Create output models for JSON-producing prompts: ConvergenceAssessmentOutput"
Task: "Create output models for JSON-producing prompts: TaskProfileInferenceOutput"
Task: "Create output models for JSON-producing prompts: TaskProfileUpdateOutput"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Prompt Consolidation)
4. **STOP and VALIDATE**: Test User Story 1 independently - verify all prompts are centralized, no inline prompts remain
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - centralized prompts!)
3. Add User Story 2 → Test independently → Deploy/Demo (Contracts enabled)
4. Add User Story 3 → Test independently → Deploy/Demo (Complete reasoning loop)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Prompt Consolidation)
   - Developer B: Prepares for User Story 2 (waits for US1)
3. Once User Story 1 is done:
   - Developer A: User Story 2 (Prompt Contracts)
   - Developer B: Prepares for User Story 3 (waits for US2)
4. Once User Story 2 is done:
   - Developer A: User Story 3 (Phase E)
   - Developer B: Polish & validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: User Story 2 MUST wait for User Story 1 (contracts require registry)
- **Critical**: User Story 3 MUST wait for User Story 2 (Phase E prompts require contracts)
- **Constitution Compliance**: Keep kernel changes minimal (prompt removal + Phase E wiring only, ~10-20 LOC net change)
- **Constitution Compliance**: Prompt registry and Phase E must be outside kernel (Principle II)

---

## Summary

- **Total Tasks**: 81
- **Tasks per User Story**:
  - User Story 1: 25 tasks (T007-T031)
  - User Story 2: 20 tasks (T032-T051)
  - User Story 3: 20 tasks (T052-T071)
  - Setup: 3 tasks (T001-T003)
  - Foundational: 3 tasks (T004-T006)
  - Polish: 10 tasks (T072-T081)
- **Parallel Opportunities**: Many extraction, removal, and model creation tasks can run in parallel
- **Independent Test Criteria**: Each user story has clear independent test criteria
- **Suggested MVP Scope**: User Story 1 only (centralized prompt management)
- **Format Validation**: All tasks follow checklist format with checkbox, ID, labels, and file paths
