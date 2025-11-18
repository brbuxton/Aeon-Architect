# Tasks: Aeon Core

**Input**: Design documents from `/specs/001-aeon-core/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included to meet constitutional requirement for 100% test coverage of kernel core logic.

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

- [ ] T001 Create project structure per implementation plan in aeon/
- [ ] T002 Initialize Python 3.11+ project with pyproject.toml
- [ ] T003 [P] Configure pytest and coverage in pyproject.toml
- [ ] T004 [P] Create requirements.txt with pydantic dependency
- [ ] T005 [P] Setup .gitignore for Python project
- [ ] T006 [P] Create README.md with project overview

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create base exception hierarchy in aeon/exceptions.py
- [ ] T008 [P] Create LLM adapter interface in aeon/llm/interface.py
- [ ] T009 [P] Create Memory interface in aeon/memory/interface.py
- [ ] T010 [P] Create Tool interface in aeon/tools/interface.py
- [ ] T011 [P] Create Plan and PlanStep pydantic models in aeon/plan/models.py
- [ ] T012 [P] Create OrchestrationState dataclass in aeon/kernel/state.py
- [ ] T013 [P] Create ToolCall pydantic model in aeon/tools/models.py
- [ ] T014 [P] Create SupervisorAction pydantic model in aeon/supervisor/models.py
- [ ] T015 [P] Create LogEntry pydantic model in aeon/observability/models.py
- [ ] T016 Create ToolRegistry class in aeon/tools/registry.py
- [ ] T017 Create Validator base class in aeon/validation/schema.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Plan Generation from Natural Language (Priority: P1) 🎯 MVP

**Goal**: Enable developers to submit natural language requests and receive declarative multi-step plans

**Independent Test**: Submit a natural language request (e.g., "calculate the sum of 5 and 10") and verify Aeon Core produces a valid JSON plan structure with goal, steps array, step IDs, descriptions, and status flags.

### Tests for User Story 1

- [ ] T018 [P] [US1] Unit test for plan generation in tests/unit/plan/test_parser.py
- [ ] T019 [P] [US1] Integration test for plan generation from natural language in tests/integration/test_plan_generation.py

### Implementation for User Story 1

- [ ] T020 [US1] Implement PlanParser in aeon/plan/parser.py to parse JSON plan structures
- [ ] T021 [US1] Implement PlanValidator in aeon/plan/validator.py with pydantic validation
- [ ] T022 [US1] Create RemoteAPIAdapter in aeon/llm/adapters/remote_api.py with retry logic (3 attempts, exponential backoff)
- [ ] T023 [US1] Implement plan generation prompt construction in aeon/kernel/orchestrator.py
- [ ] T024 [US1] Add plan generation method to Orchestrator.execute() in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Can generate plans from natural language requests.

---

## Phase 4: User Story 2 - Step-by-Step Plan Execution with Status Updates (Priority: P1)

**Goal**: Execute plans step-by-step with deterministic status updates (pending → running → complete/failed)

**Independent Test**: Submit a valid plan and verify Aeon Core executes steps sequentially, updating each step's status from "pending" → "running" → "complete" (or "failed") in a deterministic manner.

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test for plan executor in tests/unit/plan/test_executor.py
- [ ] T026 [P] [US2] Unit test for state transitions in tests/unit/kernel/test_state.py
- [ ] T027 [P] [US2] Integration test for plan execution loop in tests/integration/test_plan_execution.py

### Implementation for User Story 2

- [ ] T028 [US2] Implement PlanExecutor in aeon/plan/executor.py with sequential step execution
- [ ] T029 [US2] Implement step status transition logic in aeon/plan/executor.py (pending → running → complete/failed)
- [ ] T030 [US2] Implement OrchestrationState management in aeon/kernel/state.py
- [ ] T031 [US2] Implement main orchestration loop in aeon/kernel/orchestrator.py
- [ ] T032 [US2] Add state update methods to Orchestrator in aeon/kernel/orchestrator.py
- [ ] T033 [US2] Implement get_state() method in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Can generate and execute plans with status updates.

---

## Phase 5: User Story 3 - Supervisor Error Correction (Priority: P2)

**Goal**: Automatically repair malformed JSON, tool calls, and plan fragments using supervisor without halting orchestration

**Independent Test**: Inject malformed JSON into the LLM output path and verify the Supervisor repairs it, returns corrected JSON, and the orchestration loop continues without interruption.

### Tests for User Story 3

- [ ] T034 [P] [US3] Unit test for supervisor JSON repair in tests/unit/supervisor/test_repair.py
- [ ] T035 [P] [US3] Unit test for supervisor retry logic (2 attempts) in tests/unit/supervisor/test_repair.py
- [ ] T036 [P] [US3] Integration test for supervisor error correction in tests/integration/test_supervisor_repair.py

### Implementation for User Story 3

- [ ] T037 [US3] Implement Supervisor class in aeon/supervisor/repair.py
- [ ] T038 [US3] Implement repair_json() method with 2 retry attempts in aeon/supervisor/repair.py
- [ ] T039 [US3] Implement repair_tool_call() method in aeon/supervisor/repair.py
- [ ] T040 [US3] Implement repair_plan() method in aeon/supervisor/repair.py
- [ ] T041 [US3] Integrate supervisor into validation layer in aeon/validation/schema.py
- [ ] T042 [US3] Add supervisor invocation on validation failures in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should work independently. System can self-correct malformed outputs.

---

## Phase 6: User Story 4 - Tool Registration and Invocation (Priority: P2)

**Goal**: Enable tool registration and deterministic tool invocation with validated arguments integrated into LLM reasoning cycles

**Independent Test**: Register a stub tool (e.g., echo tool), create a plan that calls the tool, and verify Aeon invokes the tool with validated arguments and incorporates the result into the next LLM cycle.

### Tests for User Story 4

- [ ] T043 [P] [US4] Contract test for Tool interface in tests/contract/test_tool_interface.py
- [ ] T044 [P] [US4] Unit test for ToolRegistry in tests/unit/tools/test_registry.py
- [ ] T045 [P] [US4] Unit test for tool invocation in tests/unit/tools/test_invocation.py
- [ ] T046 [P] [US4] Integration test for tool invocation in orchestration loop in tests/integration/test_tool_invocation.py

### Implementation for User Story 4

- [ ] T047 [US4] Implement ToolRegistry.register() and get() methods in aeon/tools/registry.py
- [ ] T047a [US4] Implement ToolRegistry.list_all() in aeon/tools/registry.py  
      **Purpose**  
      Satisfies FR-021: Aeon must support enumeration of all registered tools.

      **Description**  
      Add a `list_all()` method returning a deterministic list of:
      - tool name  
      - description  
      - input_schema  
      - output_schema  
      Sorted alphabetically by tool name.

      **Files Modified**  
      - aeon/tools/registry.py  
      - tests/unit/tools/test_registry.py
- [ ] T048 [US4] Implement tool input validation in aeon/tools/interface.py
- [ ] T049 [US4] Implement tool output validation in aeon/tools/interface.py
- [ ] T050 [US4] Create EchoTool stub in aeon/tools/stubs/echo.py
- [ ] T051 [US4] Create CalculatorTool stub in aeon/tools/stubs/calculator.py
- [ ] T052 [US4] Implement tool invocation in aeon/kernel/orchestrator.py
- [ ] T053 [US4] Add tool error handling (mark step failed, log error, continue) in aeon/kernel/orchestrator.py
- [ ] T054 [US4] Integrate tool results into LLM reasoning cycle in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1-4 should work independently. Complete thought → tool → thought loop is functional.

---

## Phase 7: User Story 5 - Key/Value Memory Operations (Priority: P3)

**Goal**: Enable storing and retrieving values from memory, with memory accessible during multi-step reasoning

**Independent Test**: Store a value with a key, retrieve it by key, and verify Aeon can read from memory during plan execution and use stored values in subsequent reasoning steps.

### Tests for User Story 5

- [ ] T055 [P] [US5] Contract test for Memory interface in tests/contract/test_memory_interface.py
- [ ] T056 [P] [US5] Unit test for InMemoryKVStore in tests/unit/memory/test_kv_store.py
- [ ] T057 [P] [US5] Integration test for memory operations in orchestration in tests/integration/test_memory.py

### Implementation for User Story 5

- [ ] T058 [US5] Implement InMemoryKVStore.write() in aeon/memory/kv_store.py
- [ ] T059 [US5] Implement InMemoryKVStore.read() in aeon/memory/kv_store.py
- [ ] T060 [US5] Implement InMemoryKVStore.search() with prefix matching in aeon/memory/kv_store.py
- [ ] T061 [US5] Integrate memory into Orchestrator initialization in aeon/kernel/orchestrator.py
- [ ] T062 [US5] Add memory read/write operations to orchestration loop in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1-5 should work independently. Memory subsystem is functional.

---

## Phase 8: User Story 6 - TTL Expiration Handling (Priority: P3)

**Goal**: Gracefully stop reasoning when TTL expires and return structured "TTL expired" response

**Independent Test**: Set a low TTL (e.g., 2 cycles), execute a plan that would normally take more cycles, and verify Aeon stops execution when TTL reaches zero and returns a structured expiration response.

### Tests for User Story 6

- [ ] T063 [P] [US6] Unit test for TTL counter in tests/unit/kernel/test_ttl.py
- [ ] T064 [P] [US6] Integration test for TTL expiration in tests/integration/test_ttl_expiration.py

### Implementation for User Story 6

- [ ] T065 [US6] Implement TTL counter in aeon/kernel/ttl.py
- [ ] T066 [US6] Add TTL initialization to Orchestrator in aeon/kernel/orchestrator.py
- [ ] T067 [US6] Implement TTL decrement after each LLM cycle in aeon/kernel/orchestrator.py
- [ ] T068 [US6] Add TTL expiration check and graceful termination in aeon/kernel/orchestrator.py
- [ ] T069 [US6] Implement structured "TTL expired" response in aeon/kernel/orchestrator.py

**Checkpoint**: At this point, User Stories 1-6 should work independently. TTL governance is functional.

---

## Phase 9: User Story 7 - Orchestration Cycle Logging (Priority: P2)

**Goal**: Generate JSONL logs for each orchestration cycle with all required fields

**Independent Test**: Execute a plan with multiple cycles and verify each cycle produces a JSONL log entry containing: step number, plan state, LLM output, supervisor actions (if any), tool calls, TTL remaining, and errors (if any).

### Tests for User Story 7

- [ ] T070 [P] [US7] Unit test for JSONL logger in tests/unit/observability/test_logger.py
- [ ] T071 [P] [US7] Integration test for cycle logging in tests/integration/test_logging.py

### Implementation for User Story 7

- [ ] T072 [US7] Implement JSONL logger in aeon/observability/logger.py
- [ ] T073 [US7] Create LogEntry formatter in aeon/observability/logger.py
- [ ] T074 [US7] Integrate logging into orchestration loop in aeon/kernel/orchestrator.py
- [ ] T075 [US7] Add cycle logging after each LLM cycle in aeon/kernel/orchestrator.py
- [ ] T076 [US7] Ensure logging is non-blocking in aeon/observability/logger.py

**Checkpoint**: At this point, all User Stories 1-7 should work independently. Complete observability is functional.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T077 [P] Add CLI interface in aeon/cli/main.py (optional Sprint 1)
- [ ] T078 [P] Create vLLM adapter in aeon/llm/adapters/vllm.py
- [ ] T079 [P] Create llama-cpp-python adapter in aeon/llm/adapters/llama_cpp.py
- [ ] T080 [P] Kernel LOC Verification Tooling
      **Purpose**  
      Enforces Constitution SC-008 requiring the kernel module to remain <800 LOC.

      **Description**  
      Implement a LOC check script:
      - scans `kernel/` directory
      - sums python source lines excluding blanks and comments
      - fails CI pipeline if >800 LOC
      - prints per-file LOC and total LOC

      Integrate with the CI workflow so every PR automatically checks LOC.

      **Files Added**  
      - tools/loc_check.py  
      - .github/workflows/ci.yml (update)

      **Constitutional Notes**  
      - Required by SC-008  
      - Kernel modifications MUST be monitored for regressions  
- [ ] T081 [P] Update README.md with usage examples
- [ ] T082 [P] Add docstrings to all public interfaces
- [ ] T083 [P] Run quickstart.md validation
- [ ] T084 [P] Ensure 100% test coverage for kernel core logic
- [ ] T085 [P] Code cleanup and refactoring
- [ ] T086 [P] Performance optimization if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 (needs plan generation)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (needs orchestration loop)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (needs orchestration loop)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Can work independently but integrates with US2
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (needs orchestration loop)
- **User Story 7 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 (needs orchestration loop)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Interfaces before implementations
- Core logic before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories can start in parallel (with dependency awareness)
- All tests for a user story marked [P] can run in parallel
- Interface implementations marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (respecting dependencies)

---

## Parallel Example: User Story 1

```bash
# Launch all foundational interfaces together:
Task: "Create LLM adapter interface in aeon/llm/interface.py"
Task: "Create Memory interface in aeon/memory/interface.py"
Task: "Create Tool interface in aeon/tools/interface.py"
Task: "Create Plan and PlanStep pydantic models in aeon/plan/models.py"

# Launch all tests for User Story 1 together:
Task: "Unit test for plan generation in tests/unit/plan/test_parser.py"
Task: "Integration test for plan generation from natural language in tests/integration/test_plan_generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Plan Generation)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Add User Story 6 → Test independently → Deploy/Demo
8. Add User Story 7 → Test independently → Deploy/Demo
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Plan Generation)
   - Developer B: User Story 2 (Plan Execution) - after US1
   - Developer C: User Story 3 (Supervisor) - after US2
   - Developer D: User Story 4 (Tools) - after US2
   - Developer E: User Story 5 (Memory) - can start independently
   - Developer F: User Story 6 (TTL) - after US2
   - Developer G: User Story 7 (Logging) - after US2

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Kernel must remain under 800 LOC (constitutional requirement)
- All components communicate through interfaces (constitutional requirement)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

