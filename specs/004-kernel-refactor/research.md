# Research: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Date**: 2025-12-04  
**Feature**: Kernel Refactor for Constitutional Thinness & LOC Compliance  
**Branch**: `004-kernel-refactor`

## Overview

This research document consolidates technical decisions, patterns, and implementation approaches for extracting orchestration strategy logic from the Aeon kernel to restore constitutional compliance. The kernel currently violates Principle I (Kernel Minimalism) with 1351 LOC (1092 in orchestrator.py + 259 in executor.py), exceeding the 800 LOC limit by 551 lines (68.9% over limit).

## Current State Analysis

### Kernel LOC Breakdown

**orchestrator.py**: 1092 LOC
- Core coordination methods: ~200 LOC (generate_plan, execute, execute_multipass, get_state, _execute_step, _log_cycle)
- Phase orchestration methods: ~450 LOC (_phase_a_taskprofile_ttl, _phase_b_initial_plan_refinement, _phase_c_execute_batch, _phase_c_evaluate, _phase_c_refine, _phase_d_adaptive_depth)
- Plan transformation methods: ~50 LOC (_apply_refinement_actions)
- Step preparation methods: ~100 LOC (_get_ready_steps, _populate_incoming_context, _populate_step_indices)
- TTL/expiration methods: ~80 LOC (_check_ttl_at_phase_boundary, _create_ttl_expiration_response)
- Initialization and state management: ~212 LOC (__init__, state management)

**executor.py**: 259 LOC
- Step execution routing: ~150 LOC (execute_step, execute_tool_step, execute_llm_reasoning_step)
- Validation and error handling: ~109 LOC

**Total**: 1351 LOC (target: <750 LOC, reduction needed: ~600 LOC)

### Extractable Logic Identification

**Phase Orchestration Logic** (~450 LOC):
- `_phase_a_taskprofile_ttl()`: TaskProfile inference and TTL allocation
- `_phase_b_initial_plan_refinement()`: Initial plan validation and refinement
- `_phase_c_execute_batch()`: Batch step execution coordination
- `_phase_c_evaluate()`: Evaluation coordination (semantic validation + convergence)
- `_phase_c_refine()`: Refinement coordination
- `_phase_d_adaptive_depth()`: TaskProfile update coordination

**Plan Transformation Logic** (~50 LOC):
- `_apply_refinement_actions()`: Applying RefinementAction objects to Plan

**Step Preparation Logic** (~100 LOC):
- `_get_ready_steps()`: Dependency checking and ready step identification
- `_populate_incoming_context()`: Context population from dependency outputs
- `_populate_step_indices()`: Step index and total_steps population

**TTL/Expiration Logic** (~80 LOC):
- `_create_ttl_expiration_response()`: TTL expiration response generation

**Total Extractable**: ~680 LOC (target extraction: ~600 LOC to reach <750 LOC)

## Technical Decisions

### Decision 1: Orchestration Module Structure

**Decision**: Create new `aeon/orchestration/` namespace with modules:
- `phases.py`: Phase A/B/C/D orchestration logic
- `refinement.py`: Plan refinement action application
- `ttl.py`: TTL expiration response generation
- `step_prep.py`: Step preparation and context population

**Rationale**:
- Clear separation of concerns: each module handles a specific orchestration responsibility
- Enables independent testing of orchestration strategies
- Maintains kernel thinness by extracting all strategy logic
- Follows existing module organization patterns (plan/, validation/, convergence/)

**Alternatives Considered**:
- Single orchestration.py file: Rejected - too large, violates single responsibility
- Integration into existing modules (plan/, adaptive/): Rejected - orchestration logic is distinct from plan generation and adaptive heuristics
- No new namespace, extract to kernel/helpers: Rejected - violates kernel minimalism, helpers would still count as kernel

**Implementation Pattern**:
```python
# aeon/orchestration/phases.py
class PhaseOrchestrator:
    def phase_a_taskprofile_ttl(self, request: str, adaptive_depth: AdaptiveDepth, global_ttl: int) -> tuple[TaskProfile, int]:
        """Phase A: TaskProfile inference and TTL allocation."""
        # Extracted from orchestrator._phase_a_taskprofile_ttl()
        pass
    
    def phase_b_initial_plan_refinement(self, request: str, plan: Plan, task_profile: TaskProfile, 
                                         recursive_planner: RecursivePlanner, semantic_validator: SemanticValidator,
                                         tool_registry: ToolRegistry) -> Plan:
        """Phase B: Initial plan validation and refinement."""
        # Extracted from orchestrator._phase_b_initial_plan_refinement()
        pass
    
    # ... other phase methods
```

### Decision 2: Interface Contract Design

**Decision**: Define interface contracts for all orchestration modules that return structured results (success/error tuples) for kernel processing.

**Rationale**:
- Enables kernel to handle errors gracefully without embedding error handling logic
- Maintains separation: orchestration modules return results, kernel decides on fallbacks/retries
- Supports independent testing: modules can be tested with mock kernel state
- Follows spec requirement FR-009a: "System MUST design interfaces to return structured error results"

**Alternatives Considered**:
- Exceptions only: Rejected - kernel would need extensive try/except blocks, violates thinness
- Callback functions: Rejected - adds complexity, not needed for synchronous orchestration
- Result objects with success/error fields: Accepted - clean, explicit, testable

**Implementation Pattern**:
```python
# aeon/orchestration/phases.py
from typing import Tuple, Optional
from aeon.plan.models import Plan
from aeon.adaptive.models import TaskProfile

class PhaseResult:
    """Structured result from phase orchestration."""
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None):
        self.success = success
        self.result = result
        self.error = error

class PhaseOrchestrator:
    def phase_a_taskprofile_ttl(self, ...) -> Tuple[bool, Tuple[TaskProfile, int], Optional[str]]:
        """
        Returns: (success, (task_profile, allocated_ttl), error_message)
        """
        try:
            task_profile = adaptive_depth.infer_task_profile(...)
            allocated_ttl = adaptive_depth.allocate_ttl(...)
            return (True, (task_profile, allocated_ttl), None)
        except Exception as e:
            return (False, (None, global_ttl), str(e))
```

### Decision 3: Kernel State Access Pattern

**Decision**: Orchestration modules receive plan/state snapshots through interface parameters, not direct kernel state access.

**Rationale**:
- Maintains separation: orchestration modules don't depend on kernel internals
- Enables independent testing: modules can be tested with mock plan/state objects
- Prevents circular dependencies: kernel calls orchestration, not vice versa
- Follows spec requirement FR-011: "System MUST ensure extracted modules do not import kernel code"

**Alternatives Considered**:
- Direct kernel state access: Rejected - violates separation, creates circular dependencies
- Kernel state passed as parameter: Accepted - clean interface, testable
- State manager service: Rejected - over-engineering for refactoring scope

**Implementation Pattern**:
```python
# Kernel calls orchestration module
phase_orchestrator = PhaseOrchestrator()
success, (task_profile, allocated_ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(
    request=request,
    adaptive_depth=self._adaptive_depth,
    global_ttl=self.ttl
)

if not success:
    # Kernel handles error (fallback, retry, or propagate)
    task_profile = TaskProfile.default()
    allocated_ttl = self.ttl
```

### Decision 4: Plan Refinement Action Application

**Decision**: Extract `_apply_refinement_actions()` to `orchestration/refinement.py` as `PlanRefinement.apply_actions()`.

**Rationale**:
- Plan transformation logic is orchestration strategy, not kernel coordination
- Enables independent testing of refinement application logic
- Reduces kernel LOC by ~50 lines
- Maintains clean interface: kernel passes plan and actions, receives updated plan

**Alternatives Considered**:
- Keep in kernel: Rejected - violates kernel minimalism, plan transformation is strategy logic
- Move to plan/ module: Rejected - refinement application is orchestration, not plan generation
- New orchestration/refinement.py: Accepted - clear separation, testable

**Implementation Pattern**:
```python
# aeon/orchestration/refinement.py
class PlanRefinement:
    def apply_actions(self, plan: Plan, refinement_actions: List[RefinementAction]) -> Tuple[bool, Plan, Optional[str]]:
        """
        Apply refinement actions to plan.
        
        Returns: (success, updated_plan, error_message)
        """
        try:
            updated_plan = plan  # Copy or modify
            for action in refinement_actions:
                # Apply ADD/MODIFY/REMOVE/REPLACE actions
                pass
            return (True, updated_plan, None)
        except Exception as e:
            return (False, plan, str(e))
```

### Decision 5: Step Preparation Logic Extraction

**Decision**: Extract step preparation methods (`_get_ready_steps()`, `_populate_incoming_context()`, `_populate_step_indices()`) to `orchestration/step_prep.py`.

**Rationale**:
- Step preparation involves dependency checking and context population (strategy logic)
- Reduces kernel LOC by ~100 lines
- Enables independent testing of step preparation logic
- Maintains clean interface: kernel passes plan/state, receives ready steps

**Alternatives Considered**:
- Keep in kernel: Rejected - violates kernel minimalism, preparation is strategy logic
- Move to plan/ module: Rejected - step preparation is orchestration, not plan structure
- New orchestration/step_prep.py: Accepted - clear separation, testable

**Implementation Pattern**:
```python
# aeon/orchestration/step_prep.py
class StepPreparation:
    def get_ready_steps(self, plan: Plan, memory: Memory) -> List[PlanStep]:
        """Get steps ready to execute (dependencies satisfied)."""
        ready_steps = []
        for step in plan.steps:
            if self._dependencies_satisfied(step, plan):
                self._populate_incoming_context(step, plan, memory)
                ready_steps.append(step)
        return ready_steps
    
    def populate_step_indices(self, plan: Plan) -> None:
        """Populate step_index and total_steps for all steps."""
        total_steps = len(plan.steps)
        for idx, step in enumerate(plan.steps, start=1):
            step.step_index = idx
            step.total_steps = total_steps
```

### Decision 6: TTL Expiration Response Generation

**Decision**: Extract `_create_ttl_expiration_response()` to `orchestration/ttl.py` as `TTLStrategy.create_expiration_response()`.

**Rationale**:
- TTL expiration response generation is strategy logic, not kernel coordination
- Reduces kernel LOC by ~80 lines
- Enables independent testing of TTL expiration logic
- Maintains clean interface: kernel passes state, receives response dict

**Alternatives Considered**:
- Keep in kernel: Rejected - violates kernel minimalism, response generation is strategy
- Move to adaptive/ module: Rejected - TTL expiration is orchestration, not adaptive heuristics
- New orchestration/ttl.py: Accepted - clear separation, testable

**Implementation Pattern**:
```python
# aeon/orchestration/ttl.py
class TTLStrategy:
    def create_expiration_response(self, expiration_type: str, phase: str, 
                                   execution_pass: ExecutionPass, 
                                   execution_passes: List[ExecutionPass],
                                   state: OrchestrationState) -> Dict[str, Any]:
        """Create TTL expiration response with ExecutionHistory."""
        expiration_response = TTLExpirationResponse(...)
        execution_history = ExecutionHistory(...)
        return {
            "execution_history": execution_history.model_dump(),
            "status": "ttl_expired",
            "ttl_expiration": expiration_response.model_dump(),
            "ttl_remaining": state.ttl_remaining if state else 0,
        }
```

### Decision 7: Kernel Coordination Responsibilities

**Decision**: Kernel retains only core coordination responsibilities:
- LLM loop execution coordination (calling LLM adapter)
- Plan creation/updates (calling external modules, not implementing creation/update logic)
- State transitions (managing state object lifecycle)
- Scheduling (determining execution order and sequencing)
- Tool invocation (calling tool registry interfaces)
- TTL/token countdown (tracking and decrementing TTL)
- Supervisor routing (calling supervisor interfaces)

**Rationale**:
- These are fundamental orchestration coordination responsibilities
- Cannot be extracted without breaking kernel's core purpose
- Thin coordination logic is appropriate for kernel minimalism
- All strategy decisions are delegated to external modules

**Alternatives Considered**:
- Extract more coordination logic: Rejected - would break kernel's core purpose
- Keep some strategy logic: Rejected - violates kernel minimalism, prevents LOC reduction
- Extract all logic including coordination: Rejected - kernel must coordinate execution flow

### Decision 8: Testing Strategy

**Decision**: Use comprehensive test suite to verify no behavioral changes:
1. All existing tests pass without modification
2. Integration tests verify identical multi-pass execution behavior
3. Regression tests confirm no behavioral drift
4. Unit tests for extracted orchestration modules

**Rationale**:
- Spec requirement FR-006: "System MUST preserve all existing functionality - all tests must pass without modification"
- Spec requirement SC-002: "100% of existing tests pass without modification after refactoring"
- Ensures refactoring is structural only, no functional changes
- Provides confidence that extracted logic behaves identically

**Alternatives Considered**:
- Minimal testing: Rejected - violates spec requirements, risks behavioral changes
- Test modifications: Rejected - violates spec requirement FR-006
- Comprehensive testing: Accepted - ensures behavioral preservation

**Implementation Pattern**:
```python
# tests/integration/test_kernel_refactor.py
def test_multipass_execution_identical_behavior():
    """Verify multi-pass execution produces identical results before/after refactoring."""
    # Run same test case with pre-refactor and post-refactor kernel
    # Compare execution history, plan states, convergence results
    pass

# tests/unit/orchestration/test_phases.py
def test_phase_a_taskprofile_ttl():
    """Test Phase A orchestration logic independently."""
    phase_orchestrator = PhaseOrchestrator()
    success, (task_profile, ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(...)
    assert success
    assert isinstance(task_profile, TaskProfile)
    assert ttl > 0
```

### Decision 9: LOC Measurement and Documentation

**Decision**: Document before/after LOC measurements showing reduction from 1351 to <750 LOC, with breakdown by file and method.

**Rationale**:
- Spec requirement FR-016: "System MUST measure and document before/after LOC counts"
- Spec requirement SC-008: "Before/after LOC measurements are documented showing reduction from ~1351 to ≤800 lines"
- Provides transparency and verification of LOC reduction
- Enables tracking of extraction effectiveness

**Alternatives Considered**:
- No LOC documentation: Rejected - violates spec requirements
- High-level LOC only: Rejected - insufficient detail for verification
- Detailed LOC breakdown: Accepted - provides transparency and verification

**Implementation Pattern**:
```markdown
## LOC Reduction Summary

**Before Refactoring**:
- orchestrator.py: 1092 LOC
- executor.py: 259 LOC
- **Total**: 1351 LOC

**After Refactoring**:
- orchestrator.py: ~450 LOC (reduced by ~642 LOC)
- executor.py: ~250 LOC (reduced by ~9 LOC)
- orchestration/phases.py: ~450 LOC (extracted)
- orchestration/refinement.py: ~50 LOC (extracted)
- orchestration/step_prep.py: ~100 LOC (extracted)
- orchestration/ttl.py: ~80 LOC (extracted)
- **Kernel Total**: ~700 LOC (reduced by ~651 LOC)

**Target**: <750 LOC ✅
```

### Decision 10: Performance Preservation

**Decision**: Maintain current performance levels with no degradation allowed.

**Rationale**:
- Spec requirement FR-017: "System MUST maintain current performance levels (no performance degradation allowed)"
- Spec requirement SC-011: "System performance matches or exceeds pre-refactor performance levels (no degradation)"
- Refactoring is structural only, should not impact performance
- Interface calls add minimal overhead (function call vs. inline code)

**Alternatives Considered**:
- Allow minor performance degradation: Rejected - violates spec requirements
- Optimize for performance: Rejected - premature optimization, refactoring focus is structure
- Maintain current performance: Accepted - structural refactoring should not degrade performance

**Implementation Pattern**:
```python
# Performance verification in integration tests
def test_performance_maintained():
    """Verify refactoring does not degrade performance."""
    import time
    start = time.time()
    result = orchestrator.execute_multipass(request)
    duration = time.time() - start
    # Compare with pre-refactor baseline
    assert duration <= baseline_duration * 1.05  # Allow 5% variance
```

## Implementation Approach

### Extraction Strategy

1. **Phase 1: Extract Phase Orchestration Logic**
   - Create `orchestration/phases.py` with PhaseOrchestrator class
   - Extract all `_phase_*` methods from orchestrator.py
   - Update kernel to call PhaseOrchestrator methods
   - Verify tests pass

2. **Phase 2: Extract Plan Refinement Logic**
   - Create `orchestration/refinement.py` with PlanRefinement class
   - Extract `_apply_refinement_actions()` from orchestrator.py
   - Update kernel to call PlanRefinement.apply_actions()
   - Verify tests pass

3. **Phase 3: Extract Step Preparation Logic**
   - Create `orchestration/step_prep.py` with StepPreparation class
   - Extract `_get_ready_steps()`, `_populate_incoming_context()`, `_populate_step_indices()` from orchestrator.py
   - Update kernel to call StepPreparation methods
   - Verify tests pass

4. **Phase 4: Extract TTL Expiration Logic**
   - Create `orchestration/ttl.py` with TTLStrategy class
   - Extract `_create_ttl_expiration_response()` from orchestrator.py
   - Update kernel to call TTLStrategy.create_expiration_response()
   - Verify tests pass

5. **Phase 5: Final Verification**
   - Measure kernel LOC (target: <750 LOC)
   - Run full test suite (all tests must pass)
   - Run integration tests (verify identical behavior)
   - Document LOC reduction

### Interface Contracts

All orchestration modules will define interfaces that:
- Accept plan/state snapshots as parameters (no direct kernel state access)
- Return structured results (success/error tuples)
- Handle errors gracefully (return error results, don't raise exceptions)
- Are independently testable (no kernel dependencies)

### Testing Strategy

1. **Unit Tests**: Test each orchestration module independently with mock inputs
2. **Integration Tests**: Test kernel + orchestration modules together
3. **Regression Tests**: Compare execution results before/after refactoring
4. **Performance Tests**: Verify no performance degradation

## Summary

This refactoring extracts ~600 LOC from the kernel to restore constitutional compliance. All extracted logic is moved to `aeon/orchestration/` modules with clean interface contracts. The kernel retains only thin coordination logic, reducing from 1351 LOC to <750 LOC while preserving all existing functionality and maintaining performance.

