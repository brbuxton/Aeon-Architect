# Data Model: Kernel Refactor for Constitutional Thinness & LOC Compliance

**Date**: 2025-12-04  
**Feature**: Kernel Refactor for Constitutional Thinness & LOC Compliance  
**Phase**: 1 - Design

## Overview

This document defines the data models and entities for the extracted orchestration modules. These entities support the refactoring by providing structured interfaces between the kernel and orchestration strategy modules.

## Orchestration Module Entities

### PhaseResult

Structured result from phase orchestration methods, enabling kernel to handle success/error cases gracefully.

**Fields**:
- `success` (boolean, required): Whether the phase operation succeeded
- `result` (Any, optional): Operation result (type depends on phase method)
- `error` (string, optional): Error message if success is False

**Validation Rules**:
- If success is True, result must be present
- If success is False, error must be present
- Result type depends on phase method (see PhaseOrchestrator interface)

**Usage Pattern**:
```python
success, (task_profile, allocated_ttl), error = phase_orchestrator.phase_a_taskprofile_ttl(...)
if not success:
    # Kernel handles error (fallback, retry, or propagate)
    task_profile = TaskProfile.default()
    allocated_ttl = global_ttl
```

### RefinementResult

Structured result from plan refinement operations.

**Fields**:
- `success` (boolean, required): Whether refinement application succeeded
- `updated_plan` (Plan, optional): Updated plan after applying refinement actions
- `error` (string, optional): Error message if success is False

**Validation Rules**:
- If success is True, updated_plan must be present
- If success is False, error must be present
- updated_plan must be a valid Plan structure

**Usage Pattern**:
```python
success, updated_plan, error = plan_refinement.apply_actions(plan, refinement_actions)
if success:
    self.state.plan = updated_plan
else:
    # Kernel handles error (log, continue with original plan, or propagate)
    pass
```

### StepPreparationResult

Structured result from step preparation operations.

**Fields**:
- `success` (boolean, required): Whether step preparation succeeded
- `ready_steps` (List[PlanStep], optional): List of steps ready to execute
- `error` (string, optional): Error message if success is False

**Validation Rules**:
- If success is True, ready_steps must be present (may be empty list)
- If success is False, error must be present
- All steps in ready_steps must have dependencies satisfied

**Usage Pattern**:
```python
ready_steps = step_preparation.get_ready_steps(plan, memory)
# Returns List[PlanStep] directly (no error handling needed for dependency checking)
```

### TTLExpirationResult

Structured result from TTL expiration response generation.

**Fields**:
- `success` (boolean, required): Whether expiration response generation succeeded
- `response` (Dict[str, Any], optional): TTL expiration response dict
- `error` (string, optional): Error message if success is False

**Validation Rules**:
- If success is True, response must be present
- If success is False, error must be present
- response must contain: execution_history, status, ttl_expiration, ttl_remaining

**Usage Pattern**:
```python
success, response, error = ttl_strategy.create_expiration_response(
    expiration_type, phase, execution_pass, execution_passes, state
)
if success:
    return response
else:
    # Kernel handles error (fallback response or propagate)
    pass
```

## Interface Parameter Types

### PhaseOrchestrator Parameters

**phase_a_taskprofile_ttl**:
- `request` (string, required): Natural language request
- `adaptive_depth` (AdaptiveDepth, optional): AdaptiveDepth instance (may be None)
- `global_ttl` (integer, required): Global TTL limit

**phase_b_initial_plan_refinement**:
- `request` (string, required): Natural language request
- `plan` (Plan, required): Initial plan
- `task_profile` (TaskProfile, required): TaskProfile from Phase A
- `recursive_planner` (RecursivePlanner, optional): RecursivePlanner instance (may be None)
- `semantic_validator` (SemanticValidator, optional): SemanticValidator instance (may be None)
- `tool_registry` (ToolRegistry, optional): ToolRegistry instance (may be None)

**phase_c_execute_batch**:
- `plan` (Plan, required): Current plan
- `state` (OrchestrationState, required): Current orchestration state
- `step_executor` (StepExecutor, required): StepExecutor instance
- `tool_registry` (ToolRegistry, optional): ToolRegistry instance (may be None)
- `memory` (Memory, required): Memory interface
- `supervisor` (Supervisor, optional): Supervisor instance (may be None)

**phase_c_evaluate**:
- `plan` (Plan, required): Current plan
- `execution_results` (List[Dict[str, Any]], required): Execution results from batch
- `semantic_validator` (SemanticValidator, optional): SemanticValidator instance (may be None)
- `convergence_engine` (ConvergenceEngine, optional): ConvergenceEngine instance (may be None)
- `tool_registry` (ToolRegistry, optional): ToolRegistry instance (may be None)

**phase_c_refine**:
- `plan` (Plan, required): Current plan
- `evaluation_results` (Dict[str, Any], required): Results from evaluation phase
- `recursive_planner` (RecursivePlanner, optional): RecursivePlanner instance (may be None)

**phase_d_adaptive_depth**:
- `task_profile` (TaskProfile, required): Current TaskProfile
- `evaluation_results` (Dict[str, Any], required): Results from evaluation phase
- `plan` (Plan, required): Current plan
- `adaptive_depth` (AdaptiveDepth, optional): AdaptiveDepth instance (may be None)
- `state` (OrchestrationState, required): Current orchestration state
- `global_ttl` (integer, required): Global TTL limit
- `execution_passes` (List[ExecutionPass], required): Execution passes list

### PlanRefinement Parameters

**apply_actions**:
- `plan` (Plan, required): Current plan
- `refinement_actions` (List[RefinementAction], required): List of refinement actions to apply

### StepPreparation Parameters

**get_ready_steps**:
- `plan` (Plan, required): Current plan
- `memory` (Memory, required): Memory interface

**populate_incoming_context**:
- `step` (PlanStep, required): Step to populate context for
- `plan` (Plan, required): Current plan
- `memory` (Memory, required): Memory interface

**populate_step_indices**:
- `plan` (Plan, required): Plan to populate indices for

### TTLStrategy Parameters

**create_expiration_response**:
- `expiration_type` (Literal["phase_boundary", "mid_phase"], required): Where TTL expired
- `phase` (Literal["A", "B", "C", "D"], required): Phase where expiration occurred
- `execution_pass` (ExecutionPass, required): Last execution pass
- `execution_passes` (List[ExecutionPass], required): All execution passes
- `state` (OrchestrationState, optional): Current orchestration state (may be None)
- `execution_id` (string, required): Execution ID for ExecutionHistory
- `task_input` (string, required): Original task input

## Relationships

### Module Dependencies

**orchestration/phases.py**:
- Depends on: `aeon.plan.models`, `aeon.adaptive.models`, `aeon.convergence.models`, `aeon.validation.models`
- Does NOT depend on: `aeon.kernel` (no kernel imports)
- **Relationships**: Called by `kernel/orchestrator.py` for phase orchestration. Uses AdaptiveDepth, RecursivePlanner, SemanticValidator, ConvergenceEngine, ToolRegistry interfaces.

**orchestration/refinement.py**:
- Depends on: `aeon.plan.models`
- Does NOT depend on: `aeon.kernel` (no kernel imports)
- **Relationships**: Called by `kernel/orchestrator.py` for plan refinement. Uses Plan models only.

**orchestration/step_prep.py**:
- Depends on: `aeon.plan.models`, `aeon.memory.interface`
- Does NOT depend on: `aeon.kernel` (no kernel imports)
- **Relationships**: Called by `kernel/orchestrator.py` and `orchestration/phases.py` for step preparation. Uses Memory interface to read dependency outputs.

**orchestration/ttl.py**:
- Depends on: `aeon.kernel.state` (for ExecutionPass, ExecutionHistory, TTLExpirationResponse)
- Does NOT depend on: `aeon.kernel.orchestrator`, `aeon.kernel.executor` (no orchestration logic imports)
- **Relationships**: Called by `kernel/orchestrator.py` for TTL expiration responses. Uses state.py data structures only (no orchestration logic).

### Kernel Dependencies

**kernel/orchestrator.py**:
- Depends on: `aeon.orchestration.*` (calls orchestration modules)
- Does NOT contain: Phase orchestration logic, plan transformation logic, step preparation logic, TTL expiration logic
- **Relationships**: 
  - Calls `PhaseOrchestrator` for phase A/B/C/D orchestration
  - Calls `PlanRefinement` for plan refinement actions
  - Calls `StepPreparation` for step preparation (or via PhaseOrchestrator)
  - Calls `TTLStrategy` for TTL expiration responses
  - Coordinates LLM loop execution, plan creation/updates, state transitions, scheduling, tool invocation, TTL/token countdown, supervisor routing

**kernel/executor.py**:
- No changes (remains as step execution routing)
- **Relationships**: Called by `kernel/orchestrator.py` and `orchestration/phases.py` for step execution

### Dependency Graph

```
kernel/orchestrator.py
  ├── orchestration/phases.py
  │     ├── plan.models
  │     ├── adaptive.models
  │     ├── convergence.models
  │     ├── validation.models
  │     └── orchestration/step_prep.py
  │           ├── plan.models
  │           └── memory.interface
  ├── orchestration/refinement.py
  │     └── plan.models
  ├── orchestration/ttl.py
  │     └── kernel.state (data structures only)
  └── kernel/executor.py
```

**Key Dependency Rules**:
1. **Orchestration modules do NOT import kernel/orchestrator or kernel/executor**
2. **Orchestration modules may import kernel/state for data structures only**
3. **Kernel orchestrator calls orchestration modules through interfaces**
4. **Orchestration modules are independently testable without kernel**
5. **All orchestration logic flows from kernel → orchestration modules (one-way)**

## Validation Rules

### Interface Contract Validation

1. **All orchestration module methods MUST return structured results** (success/error tuples)
2. **All orchestration module methods MUST NOT raise exceptions** (return error results instead)
3. **All orchestration module methods MUST accept plan/state snapshots** (no direct kernel state access)
4. **All orchestration modules MUST NOT import kernel code** (except state.py for data structures)

### Data Validation

1. **PhaseResult**: success=True requires result, success=False requires error
2. **RefinementResult**: success=True requires updated_plan, success=False requires error
3. **StepPreparationResult**: success=True requires ready_steps, success=False requires error
4. **TTLExpirationResult**: success=True requires response, success=False requires error

## State Transitions

### Phase Orchestration State

- **Phase A → Phase B**: TaskProfile and TTL allocated
- **Phase B → Phase C**: Plan validated and refined
- **Phase C → Phase D**: Execution batch completed, evaluated, refined
- **Phase D → Phase C (next pass)**: TaskProfile updated, next pass begins

### Plan Refinement State

- **Before Refinement**: Plan with original steps
- **After Refinement**: Plan with applied refinement actions (ADD/MODIFY/REMOVE/REPLACE)

### Step Preparation State

- **Before Preparation**: Steps with pending status, no incoming_context
- **After Preparation**: Ready steps identified, incoming_context populated, step indices set

## Notes

- All orchestration module entities are pure data structures or result containers
- No orchestration logic resides in data model entities
- All entities maintain JSON/YAML compatibility for serialization
- Interface contracts ensure kernel and orchestration modules remain decoupled

