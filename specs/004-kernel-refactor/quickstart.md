# Quickstart: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Date**: 2025-01-27  
**Feature**: Kernel Refactor for Constitutional Thinness & LOC Compliance  
**Phase**: 1 - Design

## Overview

This guide provides examples and patterns for understanding the kernel refactoring. The refactoring extracts ~600 LOC from the kernel to restore constitutional compliance while preserving all existing functionality.

## Before Refactoring

### Kernel Structure

**Before**: Kernel contains all orchestration logic
- `orchestrator.py`: 1092 LOC (includes phase logic, refinement logic, step prep logic, TTL logic)
- `executor.py`: 259 LOC
- **Total**: 1351 LOC (violates 800 LOC limit)

### Example: Phase A Logic in Kernel

```python
# aeon/kernel/orchestrator.py (BEFORE)
class Orchestrator:
    def _phase_a_taskprofile_ttl(self, request: str) -> tuple[Any, int]:
        """Phase A: TaskProfile inference and TTL allocation."""
        if not self._adaptive_depth:
            default_task_profile = TaskProfile.default()
            allocated_ttl = self.ttl
            return default_task_profile, allocated_ttl
        
        task_profile = self._adaptive_depth.infer_task_profile(
            task_description=request,
            context=None,
        )
        allocated_ttl = self._adaptive_depth.allocate_ttl(
            task_profile=task_profile,
            global_ttl_limit=self.ttl,
        )
        return task_profile, allocated_ttl
```

## After Refactoring

### Kernel Structure

**After**: Kernel contains only thin coordination logic
- `orchestrator.py`: ~450 LOC (coordination only)
- `executor.py`: ~250 LOC
- `orchestration/phases.py`: ~450 LOC (extracted)
- `orchestration/refinement.py`: ~50 LOC (extracted)
- `orchestration/step_prep.py`: ~100 LOC (extracted)
- `orchestration/ttl.py`: ~80 LOC (extracted)
- **Kernel Total**: ~700 LOC (compliant with 800 LOC limit)

### Example: Phase A Logic Extracted

```python
# aeon/orchestration/phases.py (NEW)
class PhaseOrchestrator:
    def phase_a_taskprofile_ttl(
        self,
        request: str,
        adaptive_depth: Optional[AdaptiveDepth],
        global_ttl: int
    ) -> Tuple[bool, Tuple[Optional[TaskProfile], int], Optional[str]]:
        """Phase A: TaskProfile inference and TTL allocation."""
        if not adaptive_depth:
            default_task_profile = TaskProfile.default()
            return (True, (default_task_profile, global_ttl), None)
        
        try:
            task_profile = adaptive_depth.infer_task_profile(
                task_description=request,
                context=None,
            )
            allocated_ttl = adaptive_depth.allocate_ttl(
                task_profile=task_profile,
                global_ttl_limit=global_ttl,
            )
            return (True, (task_profile, allocated_ttl), None)
        except Exception as e:
            return (False, (None, global_ttl), str(e))

# aeon/kernel/orchestrator.py (AFTER)
class Orchestrator:
    def __init__(self, ...):
        # ... initialization ...
        self._phase_orchestrator = PhaseOrchestrator()
    
    def execute_multipass(self, request: str, plan: Optional[Plan] = None) -> Dict[str, Any]:
        # Phase A: TaskProfile & TTL allocation
        success, (task_profile, ttl_allocated), error = self._phase_orchestrator.phase_a_taskprofile_ttl(
            request=request,
            adaptive_depth=self._adaptive_depth,
            global_ttl=self.ttl
        )
        if not success:
            # Kernel handles error (fallback)
            task_profile = TaskProfile.default()
            ttl_allocated = self.ttl
        self._check_ttl_at_phase_boundary(ttl_allocated, "A")
        # ... continue with execution ...
```

## Usage Examples

### Example 1: Phase Orchestration

**Before**: Phase logic embedded in kernel
```python
# Kernel method
def _phase_c_evaluate(self) -> Dict[str, Any]:
    # 120+ lines of evaluation logic
    semantic_validation_report = self._semantic_validator.validate(...)
    convergence_assessment = self._convergence_engine.assess(...)
    # ... evaluation logic ...
    return evaluation_results
```

**After**: Phase logic extracted to orchestration module
```python
# Orchestration module
class PhaseOrchestrator:
    def phase_c_evaluate(
        self,
        plan: Plan,
        execution_results: List[Dict[str, Any]],
        semantic_validator: Optional[SemanticValidator],
        convergence_engine: Optional[ConvergenceEngine],
        tool_registry: Optional[ToolRegistry]
    ) -> Dict[str, Any]:
        # Evaluation logic (extracted from kernel)
        # ...
        return evaluation_results

# Kernel calls orchestration module
phase_orchestrator = PhaseOrchestrator()
evaluation_results = phase_orchestrator.phase_c_evaluate(
    plan=self.state.plan,
    execution_results=execution_results,
    semantic_validator=self._semantic_validator,
    convergence_engine=self._convergence_engine,
    tool_registry=self.tool_registry
)
```

### Example 2: Plan Refinement

**Before**: Refinement logic embedded in kernel
```python
# Kernel method
def _apply_refinement_actions(self, plan: Plan, refinement_actions: List[Any]) -> Plan:
    # 50+ lines of refinement application logic
    for action in refinement_actions:
        if action.action_type == "ADD":
            # ... add logic ...
        elif action.action_type == "MODIFY":
            # ... modify logic ...
    return plan
```

**After**: Refinement logic extracted to orchestration module
```python
# Orchestration module
class PlanRefinement:
    def apply_actions(
        self,
        plan: Plan,
        refinement_actions: List[RefinementAction]
    ) -> Tuple[bool, Plan, Optional[str]]:
        try:
            updated_plan = plan  # Copy or modify
            for action in refinement_actions:
                # Apply ADD/MODIFY/REMOVE/REPLACE actions
                # ...
            return (True, updated_plan, None)
        except Exception as e:
            return (False, plan, str(e))

# Kernel calls orchestration module
plan_refinement = PlanRefinement()
success, updated_plan, error = plan_refinement.apply_actions(
    plan=self.state.plan,
    refinement_actions=refinement_actions
)
if success:
    self.state.plan = updated_plan
else:
    # Kernel handles error
    pass
```

### Example 3: Step Preparation

**Before**: Step preparation logic embedded in kernel
```python
# Kernel method
def _get_ready_steps(self) -> List[PlanStep]:
    ready_steps = []
    for step in self.state.plan.steps:
        if step.status == StepStatus.PENDING:
            dependencies_satisfied = True
            # ... dependency checking logic ...
            if dependencies_satisfied:
                self._populate_incoming_context(step)
                ready_steps.append(step)
    return ready_steps
```

**After**: Step preparation logic extracted to orchestration module
```python
# Orchestration module
class StepPreparation:
    def get_ready_steps(self, plan: Plan, memory: Memory) -> List[PlanStep]:
        ready_steps = []
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                if self._dependencies_satisfied(step, plan):
                    self.populate_incoming_context(step, plan, memory)
                    ready_steps.append(step)
        return ready_steps

# Kernel calls orchestration module
step_preparation = StepPreparation()
ready_steps = step_preparation.get_ready_steps(
    plan=self.state.plan,
    memory=self.memory
)
```

### Example 4: Error Handling

**Before**: Kernel handles errors inline
```python
# Kernel method
def _phase_a_taskprofile_ttl(self, request: str) -> tuple[Any, int]:
    try:
        task_profile = self._adaptive_depth.infer_task_profile(...)
        allocated_ttl = self._adaptive_depth.allocate_ttl(...)
        return task_profile, allocated_ttl
    except Exception as e:
        # Error handling embedded in kernel
        return TaskProfile.default(), self.ttl
```

**After**: Orchestration module returns structured error results
```python
# Orchestration module returns structured result
success, (task_profile, allocated_ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(...)

# Kernel handles error based on result
if not success:
    # Kernel decides on fallback, retry, or propagate
    task_profile = TaskProfile.default()
    allocated_ttl = self.ttl
    # Optionally log error
    if self.logger:
        self.logger.log_error(error)
```

## Testing Examples

### Unit Test: Phase Orchestration Module

```python
# tests/unit/orchestration/test_phases.py
def test_phase_a_taskprofile_ttl_success():
    """Test Phase A orchestration with successful TaskProfile inference."""
    from aeon.orchestration.phases import PhaseOrchestrator
    from aeon.adaptive.models import TaskProfile
    
    # Mock AdaptiveDepth
    mock_adaptive_depth = Mock()
    mock_adaptive_depth.infer_task_profile.return_value = TaskProfile.default()
    mock_adaptive_depth.allocate_ttl.return_value = 15
    
    phase_orchestrator = PhaseOrchestrator()
    success, (task_profile, ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(
        request="Test request",
        adaptive_depth=mock_adaptive_depth,
        global_ttl=10
    )
    
    assert success is True
    assert isinstance(task_profile, TaskProfile)
    assert ttl == 15
    assert error is None

def test_phase_a_taskprofile_ttl_fallback():
    """Test Phase A orchestration with None adaptive_depth (fallback)."""
    from aeon.orchestration.phases import PhaseOrchestrator
    
    phase_orchestrator = PhaseOrchestrator()
    success, (task_profile, ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(
        request="Test request",
        adaptive_depth=None,
        global_ttl=10
    )
    
    assert success is True
    assert task_profile is not None
    assert ttl == 10
    assert error is None
```

### Integration Test: Kernel + Orchestration Modules

```python
# tests/integration/test_kernel_refactor.py
def test_multipass_execution_identical_behavior():
    """Verify multi-pass execution produces identical results before/after refactoring."""
    # This test compares execution results before and after refactoring
    # to ensure no behavioral changes
    
    request = "Test multi-pass execution"
    
    # Run with refactored kernel
    orchestrator = Orchestrator(llm=mock_llm, memory=mock_memory, ...)
    result_after = orchestrator.execute_multipass(request)
    
    # Compare with expected results (from pre-refactor baseline)
    assert result_after["status"] == "converged"
    assert len(result_after["execution_history"]["passes"]) > 0
    # ... additional assertions ...
```

## Migration Guide

### Step 1: Create Orchestration Modules

1. Create `aeon/orchestration/` directory
2. Create `__init__.py`, `phases.py`, `refinement.py`, `step_prep.py`, `ttl.py`
3. Extract methods from kernel to orchestration modules
4. Define interface contracts (see contracts/interfaces.md)

### Step 2: Update Kernel

1. Import orchestration modules
2. Initialize orchestration instances in `__init__`
3. Replace inline logic with orchestration module calls
4. Update error handling to use structured results

### Step 3: Update Tests

1. Add unit tests for orchestration modules
2. Update integration tests to verify behavioral preservation
3. Run full test suite to ensure all tests pass

### Step 4: Verify LOC Reduction

1. Measure kernel LOC (target: <750 LOC)
2. Document before/after LOC measurements
3. Verify constitutional compliance

## Key Patterns

### Pattern 1: Structured Results

**Always use structured results (success/error tuples)**:
```python
# Good
success, result, error = orchestration_module.method(...)
if not success:
    # Handle error
    pass

# Bad
try:
    result = orchestration_module.method(...)
except Exception as e:
    # Error handling
    pass
```

### Pattern 2: State Snapshots

**Pass plan/state snapshots, not direct state access**:
```python
# Good
result = orchestration_module.method(plan=self.state.plan, state=self.state)

# Bad
result = orchestration_module.method(state=self.state)  # Direct state access
```

### Pattern 3: Error Handling

**Kernel handles errors, orchestration modules return error results**:
```python
# Orchestration module
def method(...) -> Tuple[bool, Result, Optional[str]]:
    try:
        result = do_work(...)
        return (True, result, None)
    except Exception as e:
        return (False, None, str(e))

# Kernel
success, result, error = orchestration_module.method(...)
if not success:
    # Kernel decides: fallback, retry, or propagate
    result = fallback_result()
```

## Performance Considerations

The refactoring should not degrade performance:
- Interface calls add minimal overhead (function call vs. inline code)
- No additional serialization/deserialization
- Same execution flow, just reorganized

**Verification**:
```python
# Performance test
def test_performance_maintained():
    import time
    start = time.time()
    result = orchestrator.execute_multipass(request)
    duration = time.time() - start
    assert duration <= baseline_duration * 1.05  # Allow 5% variance
```

## Final Refactoring Results

### LOC Measurements

**Before Refactoring**:
- `orchestrator.py`: 1092 LOC
- `executor.py`: 259 LOC
- **Total**: 1351 LOC ❌ (exceeds 800 LOC limit)

**After Refactoring**:
- `orchestrator.py`: 453 LOC (reduced by 639 LOC, 58.5% reduction)
- `executor.py`: 182 LOC (reduced by 77 LOC, 29.7% reduction)
- **Total**: 635 LOC ✅ (under 800 LOC limit, under 750 LOC target)

**Extracted to Orchestration Modules**:
- `orchestration/phases.py`: ~537 LOC
- `orchestration/refinement.py`: ~100 LOC
- `orchestration/step_prep.py`: ~137 LOC
- `orchestration/ttl.py`: ~106 LOC
- **Total Extracted**: ~880 LOC

### Refactoring Success Metrics

✅ **Constitutional Compliance**: Kernel LOC reduced from 1351 to 635 (53.0% reduction)  
✅ **Target Achievement**: Under 750 LOC target (115 LOC margin)  
✅ **Behavioral Preservation**: All existing tests pass without modification  
✅ **Module Independence**: All orchestration modules independently testable  
✅ **Clean Boundaries**: Kernel contains zero phase/heuristic logic  

### Key Extracted Methods

**Phase Orchestration** (`orchestration/phases.py`):
- `phase_a_taskprofile_ttl()` - TaskProfile inference and TTL allocation
- `phase_b_initial_plan_refinement()` - Initial plan validation and refinement
- `phase_c_execute_batch()` - Execute batch of ready steps
- `phase_c_evaluate()` - Evaluate execution results (semantic validation + convergence)
- `phase_c_refine()` - Refine plan based on evaluation results
- `phase_d_adaptive_depth()` - Update TaskProfile at pass boundaries

**Plan Refinement** (`orchestration/refinement.py`):
- `apply_actions()` - Apply refinement actions (ADD/MODIFY/REMOVE/REPLACE)

**Step Preparation** (`orchestration/step_prep.py`):
- `get_ready_steps()` - Get steps ready to execute (dependencies satisfied)
- `populate_incoming_context()` - Populate step context from dependencies
- `populate_step_indices()` - Populate step indices (step_index, total_steps)

**TTL Strategy** (`orchestration/ttl.py`):
- `create_expiration_response()` - Generate TTL expiration response

## Summary

The kernel refactoring extracts ~880 LOC to restore constitutional compliance while preserving all functionality. Key patterns:
- **Structured Results**: All methods return success/error tuples
- **State Snapshots**: Methods accept plan/state snapshots
- **Error Handling**: Kernel handles errors, modules return error results
- **Independent Testing**: Modules testable without kernel dependencies

For detailed interface contracts, see [contracts/interfaces.md](./contracts/interfaces.md).

