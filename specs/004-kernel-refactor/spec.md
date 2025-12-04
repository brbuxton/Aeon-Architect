# Feature Specification: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Feature Branch**: `004-kernel-refactor`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "# **Project: Aeon Architect — Kernel Refactor for Constitutional Thinness & LOC Compliance**"

## Clarifications

### Session 2025-01-27

- Q: Where should the new orchestration modules be placed in the codebase structure? → A: Create new `aeon/orchestration/` namespace (e.g., `aeon/orchestration/phases.py`, `aeon/orchestration/refinement.py`)
- Q: How should the kernel handle errors from extracted orchestration modules? → A: Extracted modules return structured error results (success/error tuples) that the kernel processes
- Q: What kernel responsibilities should explicitly remain in the kernel and not be extracted? → A: Core coordination responsibilities only: LLM loop execution, plan creation/updates, state transitions, scheduling, tool invocation, TTL/token countdown, supervisor routing
- Q: Should the refactoring maintain, improve, or allow some performance degradation? → A: Maintain current performance (no degradation allowed)
- Q: Should new orchestration module interfaces follow semantic versioning from the start, or is stability sufficient? → A: Stability sufficient for this refactoring (versioning can be added later if interfaces evolve)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Restore Constitutional Compliance (Priority: P1)

As a system architect, I need the kernel to comply with constitutional LOC limits so that the architecture remains maintainable, testable, and stable.

**Why this priority**: This is a constitutional violation that blocks future development and threatens architectural integrity. The kernel must be restored to compliance before any new features can be safely added.

**Independent Test**: Can be fully tested by measuring kernel LOC after refactoring and verifying it is ≤800 LOC. Delivers constitutional compliance and architectural stability.

**Acceptance Scenarios**:

1. **Given** the kernel currently exceeds 800 LOC, **When** the refactoring is complete, **Then** the kernel LOC is ≤800 (target <750)
2. **Given** the kernel contains orchestration strategy logic, **When** the refactoring extracts this logic, **Then** the kernel contains only thin coordination logic
3. **Given** the refactoring is complete, **When** LOC is measured, **Then** only `orchestrator.py` and `executor.py` count toward the limit

---

### User Story 2 - Preserve System Behavior (Priority: P1)

As a developer, I need all existing functionality to continue working after refactoring so that no features are broken and all tests pass.

**Why this priority**: Refactoring must not introduce regressions. All existing behavior must be preserved to maintain system reliability.

**Independent Test**: Can be fully tested by running the complete test suite and verifying all tests pass without modification. Delivers confidence that refactoring did not break functionality.

**Acceptance Scenarios**:

1. **Given** all existing tests pass before refactoring, **When** refactoring is complete, **Then** all tests continue to pass without modification
2. **Given** multi-pass execution workflows exist, **When** refactoring extracts phase logic, **Then** multi-pass execution behavior remains identical
3. **Given** orchestration logs exist, **When** refactoring is complete, **Then** logs at orchestration boundaries match pre-refactor logs

---

### User Story 3 - Establish Clean Module Boundaries (Priority: P2)

As a maintainer, I need strategy-level orchestration logic to be in external modules with clear interfaces so that the kernel remains thin and future enhancements can be added without kernel changes.

**Why this priority**: Clean boundaries enable independent development and testing of orchestration strategies while keeping the kernel stable.

**Independent Test**: Can be fully tested by verifying extracted modules are independently testable, have no kernel dependencies, and expose stable interfaces. Delivers architectural separation and extensibility.

**Acceptance Scenarios**:

1. **Given** phase orchestration logic exists in the kernel, **When** it is extracted to external modules, **Then** the kernel calls these modules through interfaces without embedding strategy logic
2. **Given** extracted modules are created, **When** they are tested, **Then** they can be tested independently without kernel dependencies
3. **Given** new orchestration modules exist, **When** the kernel uses them, **Then** the kernel contains no direct orchestration logic beyond sequencing interface calls

---

### User Story 4 - Document Refactoring Architecture (Priority: P3)

As a developer, I need clear documentation of what was extracted and where it lives so that I can understand the new architecture and maintain it effectively.

**Why this priority**: Documentation ensures the refactoring is maintainable and helps future developers understand the architecture.

**Independent Test**: Can be fully tested by verifying specification documents, interface contracts, and module design documents exist and are complete. Delivers architectural clarity and maintainability.

**Acceptance Scenarios**:

1. **Given** logic is extracted from the kernel, **When** refactoring is complete, **Then** a specification document lists all extracted logic and new module boundaries
2. **Given** new orchestration modules are created, **When** refactoring is complete, **Then** interface contracts are documented for all new modules
3. **Given** refactoring is complete, **When** LOC is measured, **Then** before/after LOC measurements are documented

---

### Edge Cases

- What happens when extracted modules fail or return errors? Extracted modules return structured error results (success/error tuples), and the kernel processes these results to decide on fallbacks, retries, or error propagation without breaking orchestration flow.
- How does the system handle missing external modules? The kernel should have appropriate fallback behavior.
- What happens if extracted logic requires kernel state that is no longer directly accessible? Interfaces must provide necessary state access.
- How does the system handle backward compatibility if interfaces change? All interfaces must remain stable for this refactoring. Semantic versioning can be added later if interfaces evolve in future sprints.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST reduce kernel LOC from ~1351 to ≤800 (target <750)
- **FR-002**: System MUST extract all phase orchestration logic (Phase A/B/C/D) from the kernel to external modules in the `aeon/orchestration/` namespace
- **FR-003**: System MUST extract all plan transformation and refinement logic from the kernel to external modules in the `aeon/orchestration/` namespace
- **FR-004**: System MUST extract all heuristic decision logic from the kernel to external modules in the `aeon/orchestration/` namespace
- **FR-005**: System MUST extract all TTL/expiration decision logic from the kernel to external modules in the `aeon/orchestration/` namespace
- **FR-006**: System MUST preserve all existing functionality - all tests must pass without modification
- **FR-007**: System MUST maintain identical multi-pass execution semantics after refactoring
- **FR-008**: System MUST maintain identical orchestration logs at boundaries after refactoring
- **FR-017**: System MUST maintain current performance levels (no performance degradation allowed)
- **FR-009**: System MUST expose extracted logic through stable interfaces that the kernel calls
- **FR-009a**: System MUST design interfaces to return structured error results (success/error tuples) that the kernel processes
- **FR-010**: System MUST ensure extracted modules are independently testable
- **FR-011**: System MUST ensure extracted modules do not import kernel code
- **FR-012**: System MUST ensure the kernel contains only thin coordination logic after refactoring (core coordination: LLM loop execution, plan creation/updates, state transitions, scheduling, tool invocation, TTL/token countdown, supervisor routing)
- **FR-013**: System MUST document all extracted logic and new module boundaries
- **FR-014**: System MUST document interface contracts for all new orchestration modules
- **FR-015**: System MUST include unit tests for extracted logic in new modules
- **FR-016**: System MUST measure and document before/after LOC counts

### Out of Scope

The following kernel responsibilities MUST remain in the kernel and MUST NOT be extracted:

- LLM loop execution coordination
- Plan creation and plan updates (calling external modules, not implementing creation/update logic)
- State transitions (managing state object lifecycle)
- Scheduling (determining execution order and sequencing)
- Tool invocation (calling tool registry interfaces)
- TTL/token countdown (tracking and decrementing TTL)
- Supervisor routing (calling supervisor interfaces)

These are core coordination responsibilities that define the kernel's minimal role as a thin coordinator.

### Key Entities

- **Kernel**: The core orchestrator consisting of `orchestrator.py` and `executor.py` that coordinates LLM loop execution, plan operations, state transitions, and tool invocation
- **Orchestration Modules**: External modules in the `aeon/orchestration/` namespace containing strategy-level orchestration logic (phase logic, refinement heuristics, plan operations, TTL strategies)
- **Interface Contracts**: Well-defined contracts between kernel and orchestration modules that specify inputs, outputs, and behavior
- **Execution State**: The orchestration state managed by the kernel that tracks plan execution, TTL, and execution history

## Refactoring Summary

### Extracted Logic and Module Boundaries

The refactoring successfully extracted all orchestration strategy logic from the kernel to external modules in the `aeon/orchestration/` namespace:

#### Phase Orchestration Logic (aeon/orchestration/phases.py)
- **Phase A - TaskProfile & TTL Allocation**: `phase_a_taskprofile_ttl()` - Extracted from `_phase_a_taskprofile_ttl()` in orchestrator.py
- **Phase B - Initial Plan Refinement**: `phase_b_initial_plan_refinement()` - Extracted from `_phase_b_initial_plan_refinement()` in orchestrator.py
- **Phase C - Execute Batch**: `phase_c_execute_batch()` - Extracted from `_phase_c_execute_batch()` in orchestrator.py
- **Phase C - Evaluate**: `phase_c_evaluate()` - Extracted from `_phase_c_evaluate()` in orchestrator.py
- **Phase C - Refine**: `phase_c_refine()` - Extracted from `_phase_c_refine()` in orchestrator.py
- **Phase D - Adaptive Depth**: `phase_d_adaptive_depth()` - Extracted from `_phase_d_adaptive_depth()` in orchestrator.py

#### Plan Refinement Logic (aeon/orchestration/refinement.py)
- **Apply Refinement Actions**: `apply_actions()` - Extracted from `_apply_refinement_actions()` in orchestrator.py
- Handles ADD, MODIFY, REMOVE, and REPLACE refinement actions on plan steps

#### Step Preparation Logic (aeon/orchestration/step_prep.py)
- **Get Ready Steps**: `get_ready_steps()` - Extracted from `_get_ready_steps()` in orchestrator.py
- **Populate Incoming Context**: `populate_incoming_context()` - Extracted from `_populate_incoming_context()` in orchestrator.py
- **Populate Step Indices**: `populate_step_indices()` - Extracted from `_populate_step_indices()` in orchestrator.py

#### TTL/Expiration Logic (aeon/orchestration/ttl.py)
- **Create Expiration Response**: `create_expiration_response()` - Extracted from `_create_ttl_expiration_response()` in orchestrator.py
- Generates structured TTL expiration responses with execution history

### Module Boundaries

**Kernel (aeon/kernel/)**:
- `orchestrator.py`: Thin coordination logic only - calls orchestration modules through interfaces
- `executor.py`: Step execution routing - unchanged
- `state.py`: Data structures only - unchanged

**Orchestration Modules (aeon/orchestration/)**:
- `phases.py`: Phase A/B/C/D orchestration strategy logic
- `refinement.py`: Plan refinement action application
- `step_prep.py`: Step preparation and dependency checking
- `ttl.py`: TTL expiration response generation

All orchestration modules are independently testable and have no kernel dependencies (except state.py for data structures).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kernel LOC is reduced to ≤800 lines (target <750 lines) as measured by counting only `orchestrator.py` and `executor.py`
- **SC-002**: 100% of existing tests pass without modification after refactoring
- **SC-003**: All multi-pass execution workflows produce identical results before and after refactoring
- **SC-004**: All orchestration logs at phase boundaries match pre-refactor logs exactly
- **SC-005**: Extracted orchestration modules are 100% independently testable (no kernel dependencies)
- **SC-006**: Kernel contains zero lines of phase orchestration logic, plan transformation logic, or heuristic decision logic
- **SC-007**: All extracted modules have documented interface contracts specifying inputs, outputs, and behavior
- **SC-008**: Before/after LOC measurements are documented showing reduction from ~1351 to ≤800 lines
- **SC-009**: New unit tests cover 100% of extracted logic in orchestration modules
- **SC-010**: Kernel behavior matches pre-refactor behavior in all execution scenarios
- **SC-011**: System performance matches or exceeds pre-refactor performance levels (no degradation)
