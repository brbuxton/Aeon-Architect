# Interface Contracts: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Date**: 2025-12-04  
**Feature**: Kernel Refactor for Constitutional Thinness & LOC Compliance  
**Phase**: 1 - Design

## Overview

This document defines the interface contracts for all orchestration modules extracted from the kernel. These interfaces ensure clean separation between kernel coordination logic and orchestration strategy logic, enabling independent testing and maintenance.

## Interface Design Principles

1. **Structured Results**: All methods return success/error tuples, not exceptions
2. **State Snapshots**: Methods accept plan/state snapshots, not direct kernel state access
3. **No Kernel Dependencies**: Orchestration modules do not import kernel code (except state.py for data structures)
4. **Independent Testability**: Interfaces enable testing without kernel dependencies

## PhaseOrchestrator Interface

**Module**: `aeon.orchestration.phases`

**Purpose**: Orchestrate Phase A/B/C/D logic for multi-pass execution.

### phase_a_taskprofile_ttl

**Signature**:
```python
def phase_a_taskprofile_ttl(
    request: str,
    adaptive_depth: Optional[AdaptiveDepth],
    global_ttl: int
) -> Tuple[bool, Tuple[Optional[TaskProfile], int], Optional[str]]:
    """
    Phase A: TaskProfile inference and TTL allocation.
    
    Args:
        request: Natural language request
        adaptive_depth: AdaptiveDepth instance (may be None for fallback)
        global_ttl: Global TTL limit
    
    Returns:
        Tuple of (success, (task_profile, allocated_ttl), error_message)
        - success: True if operation succeeded, False otherwise
        - task_profile: TaskProfile instance or None if failed
        - allocated_ttl: Allocated TTL or global_ttl if failed
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- If adaptive_depth is None, returns default TaskProfile and global_ttl
- If adaptive_depth.infer_task_profile() fails, returns (False, (None, global_ttl), error)
- If adaptive_depth.allocate_ttl() fails, returns (False, (task_profile, global_ttl), error)
- On success, returns (True, (task_profile, allocated_ttl), None)

**Error Handling**:
- Returns error result instead of raising exception
- Kernel handles fallback (default TaskProfile, global_ttl)

### phase_b_initial_plan_refinement

**Signature**:
```python
def phase_b_initial_plan_refinement(
    request: str,
    plan: Plan,
    task_profile: TaskProfile,
    recursive_planner: Optional[RecursivePlanner],
    semantic_validator: Optional[SemanticValidator],
    tool_registry: Optional[ToolRegistry]
) -> Tuple[bool, Plan, Optional[str]]:
    """
    Phase B: Initial Plan & Pre-Execution Refinement.
    
    Args:
        request: Natural language request
        plan: Initial plan
        task_profile: TaskProfile from Phase A
        recursive_planner: RecursivePlanner instance (may be None)
        semantic_validator: SemanticValidator instance (may be None)
        tool_registry: ToolRegistry instance (may be None)
    
    Returns:
        Tuple of (success, refined_plan, error_message)
        - success: True if operation succeeded, False otherwise
        - refined_plan: Refined plan or original plan if failed
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- If recursive_planner is None, skips plan regeneration
- If semantic_validator is None, skips validation
- If validation issues found and recursive_planner available, refines plan
- On success, returns (True, refined_plan, None)
- On failure, returns (False, original_plan, error)

**Error Handling**:
- Returns error result instead of raising exception
- Kernel handles fallback (continue with original plan)

### phase_c_execute_batch

**Signature**:
```python
def phase_c_execute_batch(
    plan: Plan,
    state: OrchestrationState,
    step_executor: StepExecutor,
    tool_registry: Optional[ToolRegistry],
    memory: Memory,
    supervisor: Optional[Supervisor]
) -> List[Dict[str, Any]]:
    """
    Phase C: Execute batch of ready steps.
    
    Args:
        plan: Current plan
        state: Current orchestration state
        step_executor: StepExecutor instance
        tool_registry: ToolRegistry instance (may be None)
        memory: Memory interface
        supervisor: Supervisor instance (may be None)
    
    Returns:
        List of execution results (dicts with step_id, status, output, clarity_state)
    """
```

**Behavior**:
- Gets ready steps (dependencies satisfied)
- Executes each ready step using step_executor
- Decrements TTL after each step execution
- Returns list of execution results

**Error Handling**:
- Individual step failures are captured in execution results
- Method does not raise exceptions (errors in execution results)

### phase_c_evaluate

**Signature**:
```python
def phase_c_evaluate(
    plan: Plan,
    execution_results: List[Dict[str, Any]],
    semantic_validator: Optional[SemanticValidator],
    convergence_engine: Optional[ConvergenceEngine],
    tool_registry: Optional[ToolRegistry]
) -> Dict[str, Any]:
    """
    Phase C: Evaluate execution results (semantic validation + convergence).
    
    Args:
        plan: Current plan
        execution_results: Execution results from batch
        semantic_validator: SemanticValidator instance (may be None)
        convergence_engine: ConvergenceEngine instance (may be None)
        tool_registry: ToolRegistry instance (may be None)
    
    Returns:
        Evaluation results dict with:
        - converged: bool
        - needs_refinement: bool
        - semantic_validation: dict (SemanticValidationReport.model_dump())
        - convergence_assessment: dict (ConvergenceAssessment.model_dump())
        - validation_issues: List[ValidationIssue]
        - convergence_reason_codes: List[str]
    """
```

**Behavior**:
- Calls semantic_validator.validate() if available
- Calls convergence_engine.assess() if available
- Checks if all steps are complete (automatic convergence)
- Determines if refinement is needed
- Returns evaluation results dict

**Error Handling**:
- If semantic validation fails, continues with empty report
- If convergence assessment fails, creates conservative assessment
- Method does not raise exceptions (errors handled internally)

### phase_c_refine

**Signature**:
```python
def phase_c_refine(
    plan: Plan,
    evaluation_results: Dict[str, Any],
    recursive_planner: Optional[RecursivePlanner]
) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """
    Phase C: Refine plan based on evaluation results.
    
    Args:
        plan: Current plan
        evaluation_results: Results from evaluation phase
        recursive_planner: RecursivePlanner instance (may be None)
    
    Returns:
        Tuple of (success, refinement_changes, error_message)
        - success: True if operation succeeded, False otherwise
        - refinement_changes: List of refinement changes (RefinementAction.model_dump())
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- Extracts validation issues, convergence reason codes, blocked steps
- Gets executed step IDs
- Calls recursive_planner.refine_plan() if available
- Returns refinement changes list

**Error Handling**:
- If recursive_planner is None, returns (True, [], None)
- If refinement fails, returns (False, [], error)
- Kernel handles error (continue without refinement)

### phase_d_adaptive_depth

**Signature**:
```python
def phase_d_adaptive_depth(
    task_profile: TaskProfile,
    evaluation_results: Dict[str, Any],
    plan: Plan,
    adaptive_depth: Optional[AdaptiveDepth],
    state: OrchestrationState,
    global_ttl: int,
    execution_passes: List[ExecutionPass]
) -> Tuple[bool, Optional[TaskProfile], Optional[str]]:
    """
    Phase D: Adaptive Depth - update TaskProfile at pass boundaries.
    
    Args:
        task_profile: Current TaskProfile
        evaluation_results: Results from evaluation phase
        plan: Current plan
        adaptive_depth: AdaptiveDepth instance (may be None)
        state: Current orchestration state
        global_ttl: Global TTL limit
        execution_passes: Execution passes list
    
    Returns:
        Tuple of (success, updated_task_profile, error_message)
        - success: True if operation succeeded, False otherwise
        - updated_task_profile: Updated TaskProfile or None if no update
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- Extracts convergence assessment and semantic validation report
- Collects clarity states from plan steps
- Calls adaptive_depth.update_task_profile() if available
- If profile updated, adjusts TTL bidirectionally
- Updates state TTL and records adjustment in execution pass

**Error Handling**:
- If adaptive_depth is None, returns (True, None, None) (no update)
- If update fails, returns (False, None, error)
- Kernel handles error (continue with original profile)

## PlanRefinement Interface

**Module**: `aeon.orchestration.refinement`

**Purpose**: Apply refinement actions to plans.

### apply_actions

**Signature**:
```python
def apply_actions(
    plan: Plan,
    refinement_actions: List[RefinementAction]
) -> Tuple[bool, Plan, Optional[str]]:
    """
    Apply refinement actions to plan.
    
    Args:
        plan: Current plan
        refinement_actions: List of RefinementAction objects
    
    Returns:
        Tuple of (success, updated_plan, error_message)
        - success: True if operation succeeded, False otherwise
        - updated_plan: Updated plan after applying actions
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- Applies ADD actions: Creates new PlanStep and appends to plan.steps
- Applies MODIFY actions: Updates step fields from new_step dict
- Applies REMOVE actions: Removes step from plan.steps
- Applies REPLACE actions: Replaces step with new step
- Returns updated plan

**Error Handling**:
- If action is invalid, skips it and continues
- If action application fails, returns (False, original_plan, error)
- Kernel handles error (continue with original plan)

## StepPreparation Interface

**Module**: `aeon.orchestration.step_prep`

**Purpose**: Prepare steps for execution (dependency checking, context population, index population).

### get_ready_steps

**Signature**:
```python
def get_ready_steps(
    plan: Plan,
    memory: Memory
) -> List[PlanStep]:
    """
    Get steps that are ready to execute (dependencies satisfied).
    
    Args:
        plan: Current plan
        memory: Memory interface
    
    Returns:
        List of PlanStep objects ready to execute
    """
```

**Behavior**:
- Iterates through plan.steps with status PENDING
- Checks if all dependencies are satisfied (dependency steps have status COMPLETE)
- Populates incoming_context for each ready step
- Returns list of ready steps

**Error Handling**:
- If dependency step not found, treats as unsatisfied
- If memory read fails, continues without that context
- Method does not raise exceptions (errors handled gracefully)

### populate_incoming_context

**Signature**:
```python
def populate_incoming_context(
    step: PlanStep,
    plan: Plan,
    memory: Memory
) -> None:
    """
    Populate incoming_context from dependency step outputs.
    
    Args:
        step: PlanStep to populate context for
        plan: Current plan
        memory: Memory interface
    """
```

**Behavior**:
- Gets step dependencies
- Reads dependency outputs from memory
- Checks for handoff_to_next from dependency steps
- Populates step.incoming_context with context from dependencies

**Error Handling**:
- If memory read fails, continues without that context
- Method does not raise exceptions (errors handled gracefully)

### populate_step_indices

**Signature**:
```python
def populate_step_indices(
    plan: Plan
) -> None:
    """
    Populate step_index and total_steps for all steps in plan.
    
    Args:
        plan: Plan to populate indices for
    """
```

**Behavior**:
- Calculates total_steps = len(plan.steps)
- Sets step.step_index = idx (1-based) for each step
- Sets step.total_steps = total_steps for each step

**Error Handling**:
- Method does not raise exceptions (simple index assignment)

## TTLStrategy Interface

**Module**: `aeon.orchestration.ttl`

**Purpose**: Generate TTL expiration responses.

### create_expiration_response

**Signature**:
```python
def create_expiration_response(
    expiration_type: Literal["phase_boundary", "mid_phase"],
    phase: Literal["A", "B", "C", "D"],
    execution_pass: ExecutionPass,
    execution_passes: List[ExecutionPass],
    state: Optional[OrchestrationState],
    execution_id: str,
    task_input: str
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """
    Create TTL expiration response.
    
    Args:
        expiration_type: Where TTL expired (phase_boundary or mid_phase)
        phase: Phase where expiration occurred
        execution_pass: Last execution pass
        execution_passes: All execution passes
        state: Current orchestration state (may be None)
        execution_id: Execution ID for ExecutionHistory
        task_input: Original task input
    
    Returns:
        Tuple of (success, response_dict, error_message)
        - success: True if operation succeeded, False otherwise
        - response_dict: TTL expiration response dict
        - error_message: Error message if success is False, None otherwise
    """
```

**Behavior**:
- Creates TTLExpirationResponse object
- Builds ExecutionHistory with partial results
- Returns response dict with execution_history, status, ttl_expiration, ttl_remaining

**Error Handling**:
- If state is None, uses default values
- Returns error result instead of raising exception
- Kernel handles error (fallback response or propagate)

## Interface Constraints

### Kernel Constraints

1. **Kernel MUST call orchestration modules through interfaces only**
2. **Kernel MUST NOT embed orchestration strategy logic**
3. **Kernel MUST handle orchestration module errors gracefully** (fallback, retry, or propagate)
4. **Kernel MUST pass plan/state snapshots, not direct state access**

### Orchestration Module Constraints

1. **Modules MUST NOT import kernel code** (except state.py for data structures)
2. **Modules MUST return structured results** (success/error tuples)
3. **Modules MUST NOT raise exceptions** (return error results instead)
4. **Modules MUST accept plan/state snapshots** (no direct kernel state access)

## Testing Contracts

### Unit Testing

All orchestration modules MUST be independently testable:
- Test with mock plan/state objects
- Test with mock external modules (AdaptiveDepth, RecursivePlanner, etc.)
- Test error handling (None parameters, failed operations)
- Test success cases (normal operation)

### Integration Testing

Kernel + orchestration modules MUST be tested together:
- Test multi-pass execution with extracted modules
- Test error handling (orchestration module failures)
- Test performance (no degradation)
- Test behavioral preservation (identical results before/after refactoring)

## Versioning

**Current Version**: 1.0.0 (initial refactoring)

**Stability**: Interfaces are stable for this refactoring. Future enhancements may extend interfaces but MUST maintain backward compatibility.

**Future Changes**: If interfaces evolve, semantic versioning will be applied (major.minor.patch).

