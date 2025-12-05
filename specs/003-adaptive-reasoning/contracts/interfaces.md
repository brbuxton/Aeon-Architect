# Interface Contracts: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Date**: 2025-12-04  
**Feature**: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

## Overview

This document defines the interface contracts for Sprint 2's multi-pass reasoning engine components. All interfaces are Python abstract base classes or protocols that external modules must implement. The kernel interacts with these modules only through these interfaces.

## Core Interfaces

### ConvergenceEngine

Interface for convergence detection and completion assessment.

**Location**: `aeon/convergence/engine.py`

**Methods**:

```python
def assess(
    self,
    plan_state: dict,
    execution_results: list[dict],
    semantic_validation_report: SemanticValidationReport,
    custom_criteria: Optional[dict] = None
) -> ConvergenceAssessment:
    """
    Assess whether task execution has converged on a complete, coherent, consistent solution.
    
    Args:
        plan_state: Current plan state (JSON-serializable dict)
        execution_results: Step outputs and tool results (list of JSON-serializable dicts)
        semantic_validation_report: Semantic validation report from validation layer
        custom_criteria: Optional custom convergence criteria (dict with thresholds)
    
    Returns:
        ConvergenceAssessment with converged flag, reason codes, scores, and metadata
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
    """
```

**Input Validation**:
- `plan_state` must be JSON-serializable dict
- `execution_results` must be list of JSON-serializable dicts
- `semantic_validation_report` must be valid SemanticValidationReport instance
- `custom_criteria` must be dict with optional keys: completeness_threshold, coherence_threshold, consistency_threshold

**Output Guarantees**:
- Returns valid ConvergenceAssessment instance
- `converged` is boolean
- `reason_codes` is non-empty list when converged == false
- `completeness_score` and `coherence_score` are in range [0.0, 1.0]

**Error Handling**:
- Uses LLM adapter with retry logic (exponential backoff, 3 attempts)
- On LLM failure, raises LLMError with error details
- Uses supervisor repair_json() for schema violations

### SemanticValidator

Interface for semantic validation of plans and execution artifacts.

**Location**: `aeon/validation/semantic.py`

**Methods**:

```python
def validate(
    self,
    artifact: dict,
    artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"],
    tool_registry: Optional[ToolRegistry] = None
) -> SemanticValidationReport:
    """
    Validate semantic quality of plan, step, or execution artifact.
    
    Args:
        artifact: Artifact to validate (plan, step, or execution artifact as JSON-serializable dict)
        artifact_type: Type of artifact being validated
        tool_registry: Optional tool registry for hallucination detection
    
    Returns:
        SemanticValidationReport with detected issues, severity, and proposed repairs
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
    """
```

**Input Validation**:
- `artifact` must be JSON-serializable dict
- `artifact_type` must match defined literals
- `tool_registry` must be ToolRegistry instance if provided

**Output Guarantees**:
- Returns valid SemanticValidationReport instance
- `issues` is list of ValidationIssue objects (may be empty if no issues)
- `overall_severity` is highest severity from issues (or "LOW" if no issues)
- All semantic judgments (specificity, relevance, consistency, hallucination) use LLM-based reasoning

**Error Handling**:
- Uses LLM adapter with retry logic (exponential backoff, 3 attempts)
- On LLM failure, raises LLMError with error details
- Uses supervisor repair_json() for schema violations
- Performs structural checks (duplicate IDs, missing attributes) before LLM delegation

### AdaptiveDepth

Interface for adaptive depth heuristics and TaskProfile inference.

**Location**: `aeon/adaptive/heuristics.py`

**Methods**:

```python
def infer_task_profile(
    self,
    task_description: str,
    context: Optional[dict] = None
) -> TaskProfile:
    """
    Infer TaskProfile for a task using LLM-based reasoning.
    
    Args:
        task_description: Natural language task description
        context: Optional context (previous attempts, user preferences, etc.)
    
    Returns:
        TaskProfile with all dimensions inferred
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
    """

def allocate_ttl(
    self,
    task_profile: TaskProfile,
    global_ttl_limit: Optional[int] = None
) -> int:
    """
    Allocate TTL based on TaskProfile dimensions using deterministic function.
    
    Args:
        task_profile: TaskProfile instance
        global_ttl_limit: Optional global TTL limit to cap allocation
    
    Returns:
        Allocated TTL (integer, >= 1)
    
    Raises:
        ValueError: If task_profile is invalid
    """

def update_task_profile(
    self,
    current_profile: TaskProfile,
    convergence_assessment: ConvergenceAssessment,
    semantic_validation_report: SemanticValidationReport,
    clarity_states: list[Literal["CLEAR", "PARTIALLY_CLEAR", "BLOCKED"]]
) -> Optional[TaskProfile]:
    """
    Update TaskProfile at pass boundary when complexity mismatch detected.
    
    Args:
        current_profile: Current TaskProfile instance
        convergence_assessment: Convergence assessment from current pass
        semantic_validation_report: Semantic validation report from current pass
        clarity_states: List of clarity states from step executions
    
    Returns:
        Updated TaskProfile if update triggered, None otherwise
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
    """
```

**Input Validation**:
- `task_description` must be non-empty string
- `task_profile` must be valid TaskProfile instance
- `global_ttl_limit` must be >= 1 if provided
- All inputs for `update_task_profile` must be valid instances

**Output Guarantees**:
- `infer_task_profile` returns valid TaskProfile with all dimensions set
- `allocate_ttl` returns integer >= 1, capped at global_ttl_limit if provided
- `update_task_profile` returns TaskProfile or None (None if update not triggered)
- TTL allocation is deterministic (same TaskProfile → same TTL)

**Error Handling**:
- Uses LLM adapter with retry logic (exponential backoff, 3 attempts)
- On LLM failure, raises LLMError with error details
- Uses supervisor repair_json() for schema violations
- Falls back to default TaskProfile on inference failure

### RecursivePlanner

Interface for recursive planning and plan refinement.

**Location**: `aeon/plan/recursive.py`

**Methods**:

```python
def generate_plan(
    self,
    task_description: str,
    task_profile: TaskProfile,
    tool_registry: ToolRegistry
) -> Plan:
    """
    Generate initial declarative plan for a task.
    
    Args:
        task_description: Natural language task description
        task_profile: TaskProfile for the task
        tool_registry: Tool registry for tool awareness
    
    Returns:
        Plan with steps including step_index, total_steps, incoming_context, handoff_to_next
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
    """

def refine_plan(
    self,
    current_plan: Plan,
    validation_issues: list[ValidationIssue],
    convergence_reason_codes: list[str],
    blocked_steps: list[str],
    executed_step_ids: set[str]
) -> list[RefinementAction]:
    """
    Generate refinement actions for plan fragments using delta-style operations.
    
    Args:
        current_plan: Current plan state
        validation_issues: Validation issues that triggered refinement
        convergence_reason_codes: Reason codes from convergence assessment
        blocked_steps: List of step IDs with clarity_state == BLOCKED
        executed_step_ids: Set of step IDs that have been executed (immutable)
    
    Returns:
        List of RefinementAction objects (ADD/MODIFY/REMOVE operations)
    
    Raises:
        LLMError: If LLM API calls fail after retries
        ValidationError: If inputs are invalid
        RefinementLimitError: If refinement attempt limits exceeded
    """

def create_subplan(
    self,
    parent_step_id: str,
    parent_step_description: str,
    current_depth: int,
    max_depth: int = 5
) -> Plan:
    """
    Create subplan for complex step decomposition.
    
    Args:
        parent_step_id: ID of parent step being decomposed
        parent_step_description: Description of parent step
        current_depth: Current nesting depth
        max_depth: Maximum allowed nesting depth (default 5)
    
    Returns:
        Subplan (Plan instance) with nested steps
    
    Raises:
        LLMError: If LLM API calls fail after retries
        NestingDepthError: If current_depth >= max_depth
        ValidationError: If inputs are invalid
    """
```

**Input Validation**:
- `task_description` must be non-empty string
- `task_profile` must be valid TaskProfile instance
- `tool_registry` must be ToolRegistry instance
- `current_plan` must be valid Plan instance
- `executed_step_ids` must be set of step ID strings

**Output Guarantees**:
- `generate_plan` returns valid Plan with declarative structure (JSON/YAML)
- `refine_plan` returns list of RefinementAction objects targeting only pending/future steps
- `create_subplan` returns valid Plan with nesting depth <= max_depth
- All plans remain declarative (no procedural logic)

**Error Handling**:
- Uses LLM adapter with retry logic (exponential backoff, 3 attempts)
- On LLM failure, raises LLMError with error details
- Uses supervisor repair_json() for schema violations
- Enforces refinement attempt limits (3 per fragment, 10 global)
- Enforces nesting depth limit (5 levels)
- Marks fragments for manual intervention when limits exceeded

## Integration Contracts

### Orchestrator → External Modules

**Phase A (TaskProfile & TTL)**:
- Orchestrator invokes `AdaptiveDepth.infer_task_profile(task_description)`
- Orchestrator invokes `AdaptiveDepth.allocate_ttl(task_profile, global_ttl_limit)`

**Phase B (Initial Plan & Pre-Execution Refinement)**:
- Orchestrator invokes `RecursivePlanner.generate_plan(task_description, task_profile, tool_registry)`
- Orchestrator invokes `SemanticValidator.validate(plan, "plan", tool_registry)`
- Orchestrator invokes `RecursivePlanner.refine_plan(plan, validation_issues, [], [], set())`

**Phase C (Execution Passes)**:
- Orchestrator executes steps (batch execution)
- Orchestrator invokes `SemanticValidator.validate(execution_artifacts, "execution_artifact", tool_registry)`
- Orchestrator invokes `ConvergenceEngine.assess(plan_state, execution_results, semantic_validation_report)`
- Orchestrator invokes `RecursivePlanner.refine_plan(plan, validation_issues, convergence_reason_codes, blocked_steps, executed_step_ids)`

**Phase D (Adaptive Depth)**:
- Orchestrator invokes `AdaptiveDepth.update_task_profile(current_profile, convergence_assessment, semantic_validation_report, clarity_states)` at pass boundaries when triggered

### Data Flow Contracts

**Plan State**:
- Orchestrator passes plan state as JSON-serializable dict
- External modules receive plan state, do not modify in-place
- External modules return structured results (RefinementAction, etc.)
- Orchestrator applies changes to plan state

**Execution Results**:
- Orchestrator passes execution results as list of JSON-serializable dicts
- External modules consume execution results, do not modify
- External modules return structured assessments (ConvergenceAssessment, SemanticValidationReport)

**Validation Reports**:
- SemanticValidator returns SemanticValidationReport
- ConvergenceEngine consumes SemanticValidationReport as input
- RecursivePlanner consumes ValidationIssue objects from SemanticValidationReport

## Error Handling Contracts

**LLM Errors**:
- All modules use LLM adapter with retry logic (exponential backoff, 3 attempts)
- On retry exhaustion, modules raise LLMError with error details
- Orchestrator handles LLMError and fails gracefully for current pass

**Schema Violations**:
- All modules use supervisor repair_json() for LLM output schema violations
- On repair failure (2 attempts), modules raise ValidationError
- Orchestrator handles ValidationError and proceeds with best available state

**Refinement Limits**:
- RecursivePlanner enforces per-fragment limit (3 attempts) and global limit (10 attempts)
- On limit exceeded, RecursivePlanner raises RefinementLimitError
- Orchestrator handles RefinementLimitError and marks fragment for manual intervention

**Nesting Depth**:
- RecursivePlanner enforces nesting depth limit (5 levels)
- On limit exceeded, RecursivePlanner raises NestingDepthError
- Orchestrator handles NestingDepthError and marks fragment for manual intervention

## Versioning

All interfaces follow semantic versioning:
- **MAJOR**: Breaking changes to method signatures or return types
- **MINOR**: New methods added, optional parameters added
- **PATCH**: Bug fixes, documentation updates

Current version: **1.0.0** (initial Sprint 2 interfaces)

