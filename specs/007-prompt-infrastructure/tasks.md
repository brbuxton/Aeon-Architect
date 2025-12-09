# Tasks: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Input**: Design documents from `/specs/007-prompt-infrastructure/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Level 1 prompt tests are included per spec requirement FR-047.

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

- [X] T001 Create `aeon/prompts/` directory structure with `__init__.py` in `aeon/prompts/__init__.py`
- [X] T002 [P] Create test directory structure `tests/unit/prompts/` with `__init__.py` in `tests/unit/prompts/__init__.py`
- [X] T003 [P] Create test directory structure `tests/integration/orchestration/` for Phase E tests (if not exists) with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base exception classes in `aeon/prompts/registry.py`: `PromptNotFoundError`, `NoOutputModelError`, `RenderingError`, `JSONExtractionError`
- [X] T005 Create base `PromptInput` class in `aeon/prompts/registry.py` (Pydantic BaseModel)
- [X] T006 Create base `PromptOutput` class in `aeon/prompts/registry.py` (Pydantic BaseModel)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Centralized Prompt Management (Priority: P1) 🎯 MVP

**Goal**: Establish a centralized prompt registry containing all system prompts, accessible by unique identifiers, with all inline prompts extracted and removed from source modules.

**Independent Test**: Query the prompt registry for all known prompt identifiers and verify that each prompt can be retrieved with its associated input/output schemas. Search codebase for inline prompt strings and verify zero matches outside the registry.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Create test for prompt registry initialization in `tests/unit/prompts/test_registry.py`
- [X] T008 [P] [US1] Create test for prompt retrieval by identifier in `tests/unit/prompts/test_registry.py`
- [X] T009 [P] [US1] Create test for location invariant (no inline prompts) in `tests/unit/prompts/test_registry.py`
- [X] T010 [P] [US1] Create test for registration invariant (all PromptIds have entries) in `tests/unit/prompts/test_registry.py`

### Implementation for User Story 1

- [X] T011 [US1] Create `PromptId` enum in `aeon/prompts/registry.py` with all 23 prompt identifiers from FR-005: PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, REASONING_STEP_SYSTEM, REASONING_STEP_USER, VALIDATION_SEMANTIC_SYSTEM, VALIDATION_SEMANTIC_USER, CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER, TASKPROFILE_INFERENCE_SYSTEM, TASKPROFILE_INFERENCE_USER, TASKPROFILE_UPDATE_SYSTEM, TASKPROFILE_UPDATE_USER, RECURSIVE_PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_SYSTEM, RECURSIVE_REFINEMENT_USER, SUPERVISOR_REPAIR_SYSTEM, SUPERVISOR_REPAIR_JSON_USER, SUPERVISOR_REPAIR_TOOLCALL_USER, SUPERVISOR_REPAIR_PLAN_USER, SUPERVISOR_REPAIR_MISSINGTOOL_USER, ANSWER_SYNTHESIS_SYSTEM, ANSWER_SYNTHESIS_USER. Verify all 23 prompts are included.
- [X] T012 [US1] Create `PromptDefinition` class in `aeon/prompts/registry.py` with fields: prompt_id, template, input_model, output_model (optional), render_fn
- [X] T013 [US1] Create `PromptRegistry` class in `aeon/prompts/registry.py` with `_registry: Dict[PromptId, PromptDefinition]` and `__init__()` method
- [X] T014 [US1] Implement `get_prompt(prompt_id: PromptId, input_data: PromptInput) -> str` method in `PromptRegistry` class in `aeon/prompts/registry.py`
- [X] T015 [US1] Implement `list_prompts() -> List[PromptId]` method in `PromptRegistry` class in `aeon/prompts/registry.py`
- [X] T016 [US1] Create module-level `get_prompt()` convenience function in `aeon/prompts/registry.py` that uses global registry instance
- [X] T017 [P] [US1] Extract plan generation prompts from `aeon/plan/prompts.py` (source: FR-005) and register in `aeon/prompts/registry.py` with PromptIds: PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, REASONING_STEP_USER
- [X] T018 [P] [US1] Extract all recursive planning prompts from `aeon/plan/recursive.py` (source: FR-005) and register them in `aeon/prompts/registry.py` with PromptIds: RECURSIVE_PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_USER, RECURSIVE_REFINEMENT_SYSTEM
- [X] T019 [P] [US1] Extract semantic validation prompts from `aeon/validation/semantic.py` (source: FR-005) and register in `aeon/prompts/registry.py` with PromptIds: VALIDATION_SEMANTIC_SYSTEM, VALIDATION_SEMANTIC_USER
- [X] T020 [P] [US1] Extract convergence assessment prompts from `aeon/convergence/engine.py` (source: FR-005) and register in `aeon/prompts/registry.py` with PromptIds: CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER
- [X] T021 [P] [US1] Extract TaskProfile prompts from `aeon/adaptive/heuristics.py` (source: FR-005) and register in `aeon/prompts/registry.py` with PromptIds: TASKPROFILE_INFERENCE_SYSTEM, TASKPROFILE_INFERENCE_USER, TASKPROFILE_UPDATE_SYSTEM, TASKPROFILE_UPDATE_USER
- [X] T022 [P] [US1] Extract ALL repair-related prompts from `aeon/supervisor/repair.py` (source: FR-005) and register each with its own PromptId in `aeon/prompts/registry.py`: SUPERVISOR_REPAIR_SYSTEM, SUPERVISOR_REPAIR_JSON_USER, SUPERVISOR_REPAIR_TOOLCALL_USER, SUPERVISOR_REPAIR_PLAN_USER, SUPERVISOR_REPAIR_MISSINGTOOL_USER
- [X] T023 [P] [US1] Extract REASONING_STEP_SYSTEM prompt from `aeon/kernel/executor.py` (source: FR-005) and register in `aeon/prompts/registry.py` with PromptId: REASONING_STEP_SYSTEM
- [X] T024 [US1] Remove inline prompt imports from `aeon/kernel/executor.py` and replace with registry lookups using `aeon/prompts/registry.py`
- [X] T025 [US1] Remove inline prompt imports from `aeon/kernel/orchestrator.py` and replace with registry lookups using `aeon/prompts/registry.py`
- [X] T026 [P] [US1] Remove inline prompts from `aeon/plan/prompts.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T027 [P] [US1] Remove inline prompts from `aeon/plan/recursive.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T028 [P] [US1] Remove inline prompts from `aeon/validation/semantic.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T029 [P] [US1] Remove inline prompts from `aeon/convergence/engine.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T030 [P] [US1] Remove inline prompts from `aeon/adaptive/heuristics.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T031 [P] [US1] Remove inline prompts from `aeon/supervisor/repair.py` and update to use registry from `aeon/prompts/registry.py`
- [X] T032 [US1] Initialize global `PromptRegistry` instance at module level in `aeon/prompts/registry.py`
- [X] T033A [US1] Implement automated verification test in `tests/unit/prompts/test_registry.py` that searches codebase for inline prompt string patterns (per FR-005A). The test should search for common prompt patterns (e.g., strings containing "You are", "System:", "User:", etc.) and verify zero matches outside the prompt registry module.
- [X] T033B [US1] Run automated verification to confirm zero inline prompts outside registry (satisfies SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. All prompts are centralized in the registry, and all inline prompts have been removed.

---

## Phase 4: User Story 2 - Schema-Backed Prompt Contracts with JSON Extraction (Priority: P2)

**Goal**: Define typed input and output models (Pydantic) for all prompts, enabling validation of prompt inputs before rendering and prompt outputs after LLM responses. Implement unified JSON extraction that handles LLM responses in any format (dictionary with "text" key, markdown code blocks, embedded JSON, or raw JSON strings).

**Independent Test**: Create a prompt contract with defined input and output models, then verify that invalid inputs are rejected and valid inputs produce correctly structured outputs. Verify JSON extraction works correctly for all response formats (dictionary with "text" key, markdown code blocks, embedded JSON, raw JSON). Verify all prompts have input models and JSON-producing prompts have output models.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T034 [P] [US2] Create test for input model validation (reject invalid inputs) in `tests/unit/prompts/test_registry.py`
- [X] T035 [P] [US2] Create test for prompt rendering with validated input in `tests/unit/prompts/test_registry.py`
- [X] T036 [P] [US2] Create test for output model validation for JSON prompts in `tests/unit/prompts/test_registry.py`
- [X] T037 [P] [US2] Create test for schema invariant (all prompts have input models) in `tests/unit/prompts/test_registry.py`
- [X] T038A [P] [US2] Create test for JSON extraction from dictionary with "text" key in `tests/unit/prompts/test_registry.py` (per FR-013C)
- [X] T038B [P] [US2] Create test for JSON extraction from markdown code blocks (```json ... ``` and ``` ... ```) in `tests/unit/prompts/test_registry.py` (per FR-013D)
- [X] T038C [P] [US2] Create test for JSON extraction from embedded JSON using brace matching in `tests/unit/prompts/test_registry.py` (per FR-013E)
- [X] T038D [P] [US2] Create test for JSON extraction from raw JSON string (direct parsing fallback) in `tests/unit/prompts/test_registry.py` (per FR-013F)
- [X] T038E [P] [US2] Create test for JSONExtractionError when no valid JSON can be extracted in `tests/unit/prompts/test_registry.py` (per FR-013G)
- [X] T038F [P] [US2] Create test for ValidationError when JSON extraction succeeds but validation fails in `tests/unit/prompts/test_registry.py` (per FR-013J)
- [X] T038G [P] [US2] Create test for JSON extraction edge cases (empty "text" key, multiple JSON objects, trailing text, nested JSON in "text" key, missing "text" key, non-string "text" value, unclosed code blocks) in `tests/unit/prompts/test_registry.py` (per FR-013K)
- [X] T090 [P] [US2] Create test for Pydantic v1/v2 compatibility in `tests/unit/prompts/test_registry.py` (verify prompt input/output models can be instantiated and validated under both Pydantic v1 and v2) (FR-014A)

### Implementation for User Story 2

- [X] T039 [US2] Create input models for plan generation prompts (`PlanGenerationInput`) in `aeon/prompts/registry.py`
- [X] T040 [P] [US2] Create input models for semantic validation prompts (`SemanticValidationInput`) in `aeon/prompts/registry.py`
- [X] T041 [P] [US2] Create input models for convergence assessment prompts (`ConvergenceAssessmentInput`) in `aeon/prompts/registry.py`
- [X] T042 [P] [US2] Create input models for TaskProfile prompts (`TaskProfileInferenceInput`, `TaskProfileUpdateInput`) in `aeon/prompts/registry.py`
- [X] T043 [P] [US2] Create input models for repair prompts (`RepairInput`) in `aeon/prompts/registry.py`
- [X] T044 [P] [US2] Create input models for reasoning prompts (`ReasoningInput`) in `aeon/prompts/registry.py`
- [X] T045 [P] [US2] Create input models for recursive planning prompts (`RecursivePlanGenerationInput`, `RecursiveSubplanGenerationInput`, `RecursiveRefinementInput`) in `aeon/prompts/registry.py`
- [X] T046 [P] [US2] Create output models for JSON-producing prompts: `PlanGenerationOutput` in `aeon/prompts/registry.py`
- [X] T047 [P] [US2] Create output models for JSON-producing prompts: `ConvergenceAssessmentOutput` in `aeon/prompts/registry.py`
- [X] T048 [P] [US2] Create output models for JSON-producing prompts: `TaskProfileInferenceOutput` in `aeon/prompts/registry.py`
- [X] T049 [P] [US2] Create output models for JSON-producing prompts: `TaskProfileUpdateOutput` in `aeon/prompts/registry.py`
- [X] T050 [P] [US2] Create output models for JSON-producing prompts: `RecursiveSubplanGenerationOutput` in `aeon/prompts/registry.py`
- [X] T051 [P] [US2] Create output models for JSON-producing prompts: `RecursiveRefinementOutput` in `aeon/prompts/registry.py`
- [X] T052 [P] [US2] Create output models for JSON-producing prompts: `SupervisorRepairJSONOutput` in `aeon/prompts/registry.py`
- [X] T053 [US2] Update `PromptDefinition.render()` method in `aeon/prompts/registry.py` to validate input_data against input_model before rendering
- [X] T054 [US2] Update method signature for `validate_output()` in `PromptRegistry` class in `aeon/prompts/registry.py` to accept `Union[str, Dict[str, Any]]` for `llm_response` parameter (per FR-013B)
- [X] T055 [US2] Implement dictionary "text" key extraction in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013C): extract value from "text" key if llm_response is dict, raise JSONExtractionError if "text" key missing or value is not string
- [X] T056 [US2] Implement markdown code block extraction in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013D): extract JSON from first complete ```json ... ``` or ``` ... ``` block, handle unclosed code blocks
- [X] T057 [US2] Implement embedded JSON extraction using brace matching in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013E): identify first complete JSON object with balanced braces, handle nested JSON structures
- [X] T058 [US2] Implement direct JSON parsing fallback in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013F): attempt to parse entire response as JSON after all extraction methods fail
- [X] T059 [US2] Implement JSONExtractionError raising in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013G): raise exception with context about which extraction methods were attempted when no valid JSON found
- [X] T060 [US2] Implement output validation against output model in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013J): after successful JSON extraction, validate against output model using Pydantic, raise ValidationError (not JSONExtractionError) if validation fails
- [X] T061 [US2] Implement edge case handling in `validate_output()` method in `PromptRegistry` class in `aeon/prompts/registry.py` (per FR-013K): handle empty "text" key values, multiple JSON objects (select first), trailing text after JSON (ignore), nested JSON in "text" key (extract then process through pipeline)
- [X] T062 [US2] Update all prompt definitions in `aeon/prompts/registry.py` to include input_model for each prompt
- [X] T063 [US2] Update JSON-producing prompt definitions in `aeon/prompts/registry.py` to include output_model (per FR-005 JSON vs. Free Form output clarification: PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_SYSTEM, RECURSIVE_REFINEMENT_USER, CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER, SUPERVISOR_REPAIR_JSON_USER, ANSWER_SYNTHESIS_SYSTEM, ANSWER_SYNTHESIS_USER)
- [X] T064 [US2] Update prompt rendering functions in `aeon/prompts/registry.py` to use f-strings with Pydantic model field access (e.g., `f"Goal: {input.goal}"` where `input` is the Pydantic model instance). Ensure all prompt templates use this pattern for field substitution (per FR-007, FR-052)
- [X] T065 [US2] Update all modules using prompts to pass typed input models instead of raw dictionaries in `aeon/kernel/executor.py`, `aeon/kernel/orchestrator.py`, `aeon/plan/prompts.py`, `aeon/plan/recursive.py`, `aeon/validation/semantic.py`, `aeon/convergence/engine.py`, `aeon/adaptive/heuristics.py`, `aeon/supervisor/repair.py` (All system prompts and simple user prompts use typed models. Complex context-dependent prompts remain dynamically constructed per registry design notes.)
- [X] T066 [US2] Verify schema invariant: all prompts have input models, JSON-producing prompts have output models in `aeon/prompts/registry.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. All prompts have typed contracts with validation and unified JSON extraction.

---

## Phase 5: User Story 3 - Final Answer Synthesis (Priority: P1)

**Goal**: Implement Phase E (Answer Synthesis) that consolidates execution results, plan state, and convergence information into a coherent final answer, integrated at the C-loop exit point in the orchestration engine.

**Independent Test**: Execute a request through three distinct scenarios: (1) successful synthesis with complete data, (2) TTL expiration scenario, and (3) incomplete data scenario. Verify Phase E produces a structured final answer containing synthesized text, confidence indicators, and metadata about the execution.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

> **CRITICAL**: Per FR-051, tests MUST be limited to exactly 3 scenarios only

- [X] T067 [P] [US3] Create test for Phase E successful synthesis with complete execution state in `tests/integration/orchestration/test_phase_e.py`. Test MUST call `execute_phase_e()` directly with mocked LLM adapter (not end-to-end through OrchestrationEngine). Mock LLM to return valid FinalAnswer JSON. Verify all PhaseEInput fields populated and FinalAnswer contains synthesized text, confidence, and metadata (per FR-051).
- [X] T068 [P] [US3] Create test for Phase E with TTL expiration scenario in `tests/integration/orchestration/test_phase_e.py`. Test MUST call `execute_phase_e()` directly with mocked LLM adapter. Set ttl_remaining=0 or ttl_exhausted=True in PhaseEInput. Mock LLM to return degraded FinalAnswer. Verify degraded answer indicates TTL exhaustion in metadata (per FR-051).
- [X] T069 [P] [US3] Create test for Phase E with incomplete data scenario in `tests/integration/orchestration/test_phase_e.py`. Test MUST call `execute_phase_e()` directly with mocked LLM adapter. Create PhaseEInput with one or more optional fields missing (plan_state, execution_results, task_profile, execution_passes, convergence_assessment, or semantic_validation). Mock LLM to return degraded FinalAnswer. Verify degraded answer has metadata indicating which fields were missing (per FR-051).

### Implementation for User Story 3

- [X] T070 [US3] Create `PhaseEInput` model in `aeon/orchestration/phases.py` with required fields (request, correlation_id, execution_start_timestamp, convergence_status, total_passes, total_refinements, ttl_remaining) and optional fields (plan_state, execution_results, convergence_assessment, execution_passes, semantic_validation, task_profile) using Optional[] type hints (per FR-037, FR-039)
- [X] T071 [US3] Create `FinalAnswer` model in `aeon/orchestration/phases.py` with required field (answer_text, metadata) and optional fields (confidence, used_step_ids, notes, ttl_exhausted) using Optional[] type hints (per FR-038, FR-039)
- [X] T072 [US3] Create input models for Phase E synthesis prompts (`AnswerSynthesisInput`) in `aeon/prompts/registry.py` (derived from PhaseEInput, per FR-041)
- [X] T073 [US3] Create output model for Phase E synthesis prompts (`FinalAnswerOutput`) in `aeon/prompts/registry.py` (maps to FinalAnswer, per FR-041)
- [X] T074 [US3] Register ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER prompts in `aeon/prompts/registry.py` with AnswerSynthesisInput and FinalAnswerOutput models (per FR-041)
- [X] T075 [US3] Implement `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer` function in `aeon/orchestration/phases.py` (per FR-019, FR-021)
- [X] T076 [US3] Implement prompt retrieval and rendering for Phase E synthesis in `execute_phase_e()` function in `aeon/orchestration/phases.py` using ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER from prompt registry
- [X] T077 [US3] Implement LLM call for synthesis in `execute_phase_e()` function in `aeon/orchestration/phases.py` using llm_adapter
- [X] T078 [US3] Implement output validation against FinalAnswer model in `execute_phase_e()` function in `aeon/orchestration/phases.py` using prompt registry's validate_output() method
- [X] T079 [US3] Implement degraded mode handling in `execute_phase_e()` function in `aeon/orchestration/phases.py` covering all scenarios from spec edge cases: (1) missing/incomplete execution state (missing plan_state, execution_results, task_profile, execution_passes, convergence_assessment, or semantic_validation), (2) TTL expiration (ttl_remaining=0 or ttl_exhausted=True), (3) zero passes (total_passes=0), (4) LLM synthesis errors. MUST always produce degraded FinalAnswer with metadata indicating missing fields, never raise exceptions (per FR-025, FR-027, FR-032). Degraded answer must conform to FinalAnswer schema with answer_text explaining the situation and metadata indicating which PhaseEInput fields were missing/incomplete (per FR-026, FR-028, FR-033, FR-034)
- [X] T080 [US3] Wire Phase E invocation at C-loop exit point in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py` (or `aeon/kernel/orchestrator.py` if that's where run_multipass is located). Insert Phase E call after `_execute_phase_c_loop` returns and TTLExpiredError handling, but before any `build_execution_result` calls. Phase E must execute unconditionally regardless of convergence status, TTL expiration, or execution state completeness (per FR-020, FR-024)
- [X] T081 [US3] Build PhaseEInput from final execution state in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py` (or `aeon/kernel/orchestrator.py`) - handle optional fields gracefully (may be None), map upstream artifacts to PhaseEInput fields (per FR-028)
- [X] T082 [US3] Call `execute_phase_e()` with PhaseEInput in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py` (or `aeon/kernel/orchestrator.py`)
- [X] T083 [US3] Attach FinalAnswer to execution result under key "final_answer" in `OrchestrationEngine.run_multipass()` method in `aeon/orchestration/engine.py` (or `aeon/kernel/orchestrator.py`) (per FR-040)
- [X] T084 [US3] Verify Phase E produces final_answer in all scenarios (successful convergence, TTL expiration, partial execution, error conditions, zero passes) (per SC-005)
- [X] T085 [US3] Update CLI command `aeon execute` in `aeon/cli/main.py` to display FinalAnswer when available in execution result (FR-043)
- [X] T086 [US3] Implement human-readable FinalAnswer display in CLI when `--json` flag is NOT used in `aeon/cli/main.py` (display answer_text prominently, confidence if present, ttl_exhausted warning if True, notes if present, metadata summary if non-empty) (FR-044)
- [X] T087 [US3] Implement JSON FinalAnswer output in CLI when `--json` flag IS used in `aeon/cli/main.py` (include final_answer as top-level key with all fields serialized) (FR-045)
- [X] T088 [US3] Implement graceful handling of missing final_answer in CLI in `aeon/cli/main.py` (display message or omit section, do not crash) (FR-046)
- [X] T089 [P] [US3] Create integration test for CLI human-readable FinalAnswer display in `tests/cli/test_final_answer_display.py`. Test executes `aeon execute` command (without `--json` flag) with execution result containing final_answer. Verify CLI output contains: answer_text prominently displayed, confidence if present, ttl_exhausted warning if True, notes if present, metadata summary if non-empty (per FR-053 scenario 1).
- [X] T090A [P] [US3] Create integration test for CLI JSON FinalAnswer output in `tests/cli/test_final_answer_display.py`. Test executes `aeon execute` command with `--json` flag and execution result containing final_answer. Verify JSON output contains final_answer as top-level key with all FinalAnswer fields serialized (answer_text, confidence, used_step_ids, notes, ttl_exhausted, metadata) (per FR-053 scenario 2).
- [X] T090B [P] [US3] Create integration test for CLI graceful handling of missing final_answer in `tests/cli/test_final_answer_display.py`. Test executes `aeon execute` command with execution result missing final_answer key. Verify CLI displays message "No final answer available" or omits final_answer section entirely, and does not crash (per FR-053 scenario 3).

**Checkpoint**: At this point, all three user stories should be independently functional. Phase E completes the A→B→C→D→E reasoning loop.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, validation, and cleanup

- [X] T091 [P] Run all Level 1 prompt tests to verify: model instantiation, prompt rendering, output-model loading, invariant enforcement in `tests/unit/prompts/test_registry.py`
- [X] T092 [P] Run all Phase E integration tests in `tests/integration/orchestration/test_phase_e.py`
- [X] T093 [P] Verify kernel LOC remains under 800 (Constitution Principle I) by checking `aeon/kernel/` module sizes
- [X] T094 [P] Verify kernel minimalism: only prompt removal and Phase E wiring in kernel, no new business logic in `aeon/kernel/`
- [X] T095 [P] Verify separation of concerns: prompt registry and Phase E are outside kernel per Constitution Principle II
- [X] T096 [P] Run quickstart.md validation scenarios from `specs/007-prompt-infrastructure/quickstart.md`
- [X] T097 [P] Verify all three invariants pass automated tests: Location Invariant, Schema Invariant, Registration Invariant
- [X] T098 [P] Code cleanup and refactoring: remove unused imports, fix linting issues in `aeon/prompts/registry.py`, `aeon/orchestration/phases.py`, `aeon/kernel/orchestrator.py`, `aeon/kernel/executor.py`
- [X] T099 [P] Documentation updates: add docstrings to all new classes and functions in `aeon/prompts/registry.py` and `aeon/orchestration/phases.py`
- [X] T100 [P] Verify backward compatibility: existing execution flows still work with new prompt registry
- [X] T101 [P] Verify prompt count constraint: validate that total number of prompts in `aeon/prompts/registry.py` is under 100 (per FR-008 requirement that single-file registry is acceptable for <100 prompts). If count exceeds 100, document need for multi-file registry refactoring.

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
- Prompt extraction tasks (T017-T023) can run in parallel (different source files)
- Prompt removal tasks (T026-T031) can run in parallel (different source files)
- Input model creation tasks (T039-T045) can run in parallel (different models)
- Output model creation tasks (T046-T052) can run in parallel (different models)
- JSON extraction test tasks (T038A-T038G) can run in parallel (different test scenarios)

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
Task: "Extract REASONING_STEP_SYSTEM prompt from aeon/kernel/executor.py"

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
Task: "Create input models for recursive planning prompts in aeon/prompts/registry.py"

# Launch all output model creation tasks together (different models):
Task: "Create output models for JSON-producing prompts: PlanGenerationOutput"
Task: "Create output models for JSON-producing prompts: ConvergenceAssessmentOutput"
Task: "Create output models for JSON-producing prompts: TaskProfileInferenceOutput"
Task: "Create output models for JSON-producing prompts: TaskProfileUpdateOutput"
Task: "Create output models for JSON-producing prompts: RecursiveSubplanGenerationOutput"
Task: "Create output models for JSON-producing prompts: RecursiveRefinementOutput"
Task: "Create output models for JSON-producing prompts: SupervisorRepairJSONOutput"

# Launch all JSON extraction test tasks together (different scenarios):
Task: "Create test for JSON extraction from dictionary with 'text' key"
Task: "Create test for JSON extraction from markdown code blocks"
Task: "Create test for JSON extraction from embedded JSON"
Task: "Create test for JSON extraction from raw JSON string"
Task: "Create test for JSONExtractionError when no valid JSON can be extracted"
Task: "Create test for ValidationError when JSON extraction succeeds but validation fails"
Task: "Create test for JSON extraction edge cases"
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
- **Constitution Compliance**: Keep kernel changes minimal (prompt removal + Phase E wiring only, ~20-30 LOC net change)
- **Constitution Compliance**: Prompt registry and Phase E must be outside kernel (Principle II)
- **Phase E Tests**: Limited to exactly 3 scenarios per FR-051 (successful synthesis, TTL expiration, incomplete data)
- **Phase E Degraded Mode**: MUST always produce FinalAnswer even with missing/incomplete state (FR-025, FR-027, FR-028)
- **JSON Extraction**: Centralized in `validate_output()` method, handles all LLM response formats (FR-013A through FR-013L)

---

## Summary

- **Total Tasks**: 101
- **Tasks per User Story**:
  - User Story 1: 28 tasks (T007-T033B)
  - User Story 2: 35 tasks (T034-T066, T090)
  - User Story 3: 25 tasks (T067-T090B)
  - Setup: 3 tasks (T001-T003)
  - Foundational: 3 tasks (T004-T006)
  - Polish: 11 tasks (T091-T101)
- **Parallel Opportunities**: Many extraction, removal, model creation, and test tasks can run in parallel
- **Independent Test Criteria**: Each user story has clear independent test criteria
- **Suggested MVP Scope**: User Story 1 only (centralized prompt management)
- **Format Validation**: All tasks follow checklist format with checkbox, ID, labels, and file paths