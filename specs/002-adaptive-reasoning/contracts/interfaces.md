# Interface Contracts: Sprint 2 - Adaptive Reasoning Engine

**Date**: 2025-01-27  
**Feature**: Sprint 2 - Adaptive Reasoning Engine  
**Phase**: 1 - Design

## Overview

This document defines the interface contracts for all external modules that integrate with the kernel for Sprint 2 capabilities. All interfaces follow clean separation of concerns, enabling independent development and testing.

## Interface Principles

1. **Type Safety**: All interfaces use typed inputs/outputs (Pydantic models or type hints)
2. **Dependency Injection**: Modules receive dependencies (LLM adapter, tool registry) through constructor
3. **Error Handling**: Interfaces define expected exceptions and error conditions
4. **Immutability**: Inputs are not modified in-place (outputs are new objects)
5. **Testability**: Interfaces enable mocking for unit testing

## ConvergenceEngine Interface

**Module**: `aeon.convergence.engine`  
**Class**: `ConvergenceEngine`

### Purpose

Determines whether task execution has converged on a complete, coherent, consistent solution through LLM-based reasoning.

### Constructor

```python
def __init__(
    self,
    llm: LLMAdapter,
    default_thresholds: Optional[Dict[str, float]] = None
) -> None:
    """
    Initialize convergence engine.
    
    Args:
        llm: LLM adapter for convergence assessment
        default_thresholds: Optional custom thresholds
            - completeness: float (default 0.95)
            - coherence: float (default 0.90)
            - consistency: float (default 0.90)
    """
```

### Methods

#### assess

```python
def assess(
    self,
    validation_report: SemanticValidationReport,
    plan: Plan,
    steps: List[PlanStep],
    outputs: Dict[str, Any],
    custom_criteria: Optional[Dict[str, Any]] = None
) -> ConvergenceAssessment:
    """
    Assess whether execution has converged.
    
    Uses LLM-based reasoning as primary mechanism for completeness,
    coherence, and consistency checks. Consumes semantic validation
    report directly for coherence and consistency assessments.
    
    Args:
        validation_report: Semantic validation report (required input)
        plan: Current plan state
        steps: List of plan steps with status and outputs
        outputs: Step outputs dictionary {step_id: output}
        custom_criteria: Optional custom convergence criteria
        
    Returns:
        ConvergenceAssessment with:
            - converged: bool
            - reason_codes: List[str]
            - scores: Dict[str, float]
            - explanation: str
            - detected_issues: List[str]
            
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match ConvergenceAssessment schema
    """
```

### Contract Requirements

- MUST use LLM-based reasoning as primary mechanism
- MUST consume SemanticValidationReport as input
- MUST return ConvergenceAssessment conforming to schema
- MUST handle LLM errors gracefully (raise LLMError, don't crash)
- MUST validate LLM output against ConvergenceAssessment schema
- MUST use supervisor repair_json() if LLM output violates schema
- MUST use default thresholds if custom_criteria not provided
- MUST return converged: false with reason_codes if criteria conflict

## AdaptiveDepth Interface

**Module**: `aeon.adaptive.heuristics`  
**Class**: `AdaptiveDepth`

### Purpose

Infers TaskProfile for tasks and adjusts reasoning depth, TTL allocations, and processing strategies based on task complexity.

### Constructor

```python
def __init__(
    self,
    llm: LLMAdapter,
    global_ttl_limit: int = 100,
    global_resource_caps: Optional[Dict[str, Any]] = None
) -> None:
    """
    Initialize adaptive depth heuristics.
    
    Args:
        llm: LLM adapter for TaskProfile inference
        global_ttl_limit: Maximum TTL allocation (must respect)
        global_resource_caps: Optional resource limits
    """
```

### Methods

#### infer_task_profile

```python
def infer_task_profile(
    self,
    task_description: str,
    context: Optional[Dict[str, Any]] = None
) -> TaskProfile:
    """
    Infer TaskProfile for a task using LLM-based reasoning.
    
    Args:
        task_description: Task description string
        context: Optional context (previous attempts, memory, etc.)
        
    Returns:
        TaskProfile with all dimensions:
            - profile_version: int
            - reasoning_depth: int (1-5)
            - information_sufficiency: float (0.0-1.0)
            - expected_tool_usage: str
            - output_breadth: str
            - confidence_requirement: str
            - raw_inference: str
            
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match TaskProfile schema
        
    Note:
        Must satisfy tier stability: repeated inference for same input
        must produce reasoning_depth within ±1 tier.
    """
```

#### allocate_ttl

```python
def allocate_ttl(
    self,
    task_profile: TaskProfile,
    base_ttl: int = 10
) -> int:
    """
    Allocate TTL cycles based on TaskProfile dimensions.
    
    Uses deterministic function to map TaskProfile to numeric TTL.
    Does NOT introduce additional semantic decisions.
    
    Args:
        task_profile: TaskProfile instance
        base_ttl: Base TTL value
        
    Returns:
        Allocated TTL (must be <= global_ttl_limit)
        
    Note:
        Higher reasoning_depth or lower information_sufficiency
        should result in higher TTL allocation.
    """
```

#### update_task_profile

```python
def update_task_profile(
    self,
    current_profile: TaskProfile,
    convergence_failure: bool,
    validation_issues: List[ValidationIssue],
    clarity_states: List[str],
    task_description: str
) -> Optional[TaskProfile]:
    """
    Update TaskProfile at pass boundaries when complexity mismatch detected.
    
    Update triggered only when ALL signals present:
        - convergence_failure == True
        - validation_issues non-empty
        - clarity_states contains "BLOCKED"
    
    Args:
        current_profile: Current TaskProfile
        convergence_failure: True if convergence failed
        validation_issues: List of validation issues
        clarity_states: List of clarity_state values from steps
        task_description: Original task description
        
    Returns:
        Updated TaskProfile if update triggered, None otherwise
        
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match TaskProfile schema
    """
```

### Contract Requirements

- MUST use LLM-based reasoning for TaskProfile inference
- MUST respect global_ttl_limit in allocate_ttl()
- MUST satisfy tier stability requirement (±1 tier for reasoning_depth)
- MUST only update TaskProfile when all trigger signals present
- MUST use deterministic function for TTL allocation (no semantic decisions)
- MUST handle LLM errors gracefully
- MUST validate LLM output against TaskProfile schema
- MUST use supervisor repair_json() if LLM output violates schema

## SemanticValidator Interface

**Module**: `aeon.validation.semantic`  
**Class**: `SemanticValidator`

### Purpose

Validates plans, steps, and execution artifacts for semantic quality issues (specificity, relevance, consistency, hallucination, do/say mismatch) using LLM-based reasoning.

### Constructor

```python
def __init__(
    self,
    llm: LLMAdapter,
    tool_registry: Optional[ToolRegistry] = None
) -> None:
    """
    Initialize semantic validator.
    
    Args:
        llm: LLM adapter for semantic validation
        tool_registry: Optional tool registry for hallucination detection
    """
```

### Methods

#### validate

```python
def validate(
    self,
    artifact_type: str,
    plan: Optional[Plan] = None,
    steps: Optional[List[PlanStep]] = None,
    outputs: Optional[Dict[str, Any]] = None,
    memory_artifacts: Optional[Dict[str, Any]] = None
) -> SemanticValidationReport:
    """
    Validate artifacts for semantic quality issues.
    
    Uses LLM-based reasoning as primary mechanism for all semantic
    judgments. Performs structural checks (duplicate IDs, missing
    attributes) before delegating to LLM.
    
    Args:
        artifact_type: Type of artifact ("plan", "step", "execution_artifact", "cross_phase")
        plan: Optional plan to validate
        steps: Optional list of steps to validate
        outputs: Optional step outputs for cross-phase validation
        memory_artifacts: Optional memory artifacts for consistency checks
        
    Returns:
        SemanticValidationReport with:
            - validation_id: str
            - artifact_type: str
            - issues: List[ValidationIssue]
            - overall_severity: str
            - issue_summary: Dict[str, int]
            - proposed_repairs: List[Dict]
            
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match SemanticValidationReport schema
        
    Note:
        All semantic judgments (specificity, relevance, consistency,
        hallucination, do/say mismatch) MUST be LLM-based.
        No semantic rules, keyword lists, or pattern matching as
        primary decision-makers.
    """
```

### Contract Requirements

- MUST use LLM-based reasoning as primary mechanism for all semantic judgments
- MUST NOT use semantic rules, keyword lists, or pattern matching as primary decision-makers
- MUST perform structural checks (duplicate IDs, missing attributes) before LLM delegation
- MUST return SemanticValidationReport conforming to schema
- MUST handle LLM errors gracefully
- MUST validate LLM output against SemanticValidationReport schema
- MUST use supervisor repair_json() if LLM output violates schema
- MUST operate as best-effort advisory (not truth oracle)
- MUST detect hallucinated tools if tool_registry provided

## RecursivePlanner Interface

**Module**: `aeon.plan.recursive`  
**Class**: `RecursivePlanner`

### Purpose

Generates initial plans, creates subplans for complex steps, and refines plan fragments using LLM-based reasoning.

### Constructor

```python
def __init__(
    self,
    llm: LLMAdapter,
    tool_registry: Optional[ToolRegistry] = None,
    max_nesting_depth: int = 5
) -> None:
    """
    Initialize recursive planner.
    
    Args:
        llm: LLM adapter for plan generation and refinement
        tool_registry: Optional tool registry for plan generation
        max_nesting_depth: Maximum nesting depth for subplans (default 5)
    """
```

### Methods

#### generate_plan

```python
def generate_plan(
    self,
    task_description: str,
    context: Optional[Dict[str, Any]] = None
) -> Plan:
    """
    Generate initial declarative plan for a task.
    
    Args:
        task_description: Task description
        context: Optional context (memory, previous attempts, etc.)
        
    Returns:
        Plan with steps including:
            - step_index (1-based)
            - total_steps
            - incoming_context (may be empty)
            - handoff_to_next (may be empty)
            - dependencies
            - provides
            
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match Plan schema
        PlanError: If plan generation fails
        
    Note:
        Plans MUST remain declarative (JSON/YAML structures).
        No procedural logic allowed.
    """
```

#### refine_plan

```python
def refine_plan(
    self,
    current_plan: Plan,
    validation_issues: List[ValidationIssue],
    convergence_reason_codes: List[str],
    blocked_steps: List[str],
    executed_step_ids: List[str]
) -> List[RefinementAction]:
    """
    Refine plan fragments based on validation issues and convergence failures.
    
    Uses LLM-based reasoning to generate delta-style refinement actions.
    Only targets future/unexecuted steps or fragments that don't invalidate
    executed work.
    
    Args:
        current_plan: Current plan state
        validation_issues: Validation issues triggering refinement
        convergence_reason_codes: Convergence failure reason codes
        blocked_steps: List of step IDs with clarity_state == "BLOCKED"
        executed_step_ids: List of step IDs that have been executed (cannot modify)
        
    Returns:
        List of RefinementAction objects (ADD/MODIFY/REMOVE/REPLACE)
        
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match RefinementAction schema
        PlanError: If refinement fails
        
    Note:
        RefinementActions MUST target only pending/future steps.
        Cannot modify executed steps (status: "complete" or "failed").
        Must preserve plan structure and declarative nature.
    """
```

#### create_subplan

```python
def create_subplan(
    self,
    parent_step: PlanStep,
    parent_plan: Plan,
    current_depth: int
) -> Subplan:
    """
    Create subplan for complex step requiring decomposition.
    
    Args:
        parent_step: Step to decompose
        parent_plan: Parent plan context
        current_depth: Current nesting depth
        
    Returns:
        Subplan with substeps
        
    Raises:
        LLMError: If LLM call fails
        ValidationError: If LLM output doesn't match Subplan schema
        PlanError: If current_depth > max_nesting_depth (fail gracefully)
        
    Note:
        If current_depth > max_nesting_depth, must fail gracefully,
        mark fragment as requiring manual intervention, preserve
        existing plan structure.
    """
```

### Contract Requirements

- MUST use LLM-based reasoning for plan generation and refinement
- MUST generate declarative plans (JSON/YAML, no procedural logic)
- MUST only refine pending/future steps (not executed steps)
- MUST use delta-style refinement (ADD/MODIFY/REMOVE/REPLACE)
- MUST preserve step ID stability where possible
- MUST fail gracefully if nesting depth exceeds max_nesting_depth
- MUST handle LLM errors gracefully
- MUST validate LLM output against Plan/RefinementAction/Subplan schemas
- MUST use supervisor repair_json() if LLM output violates schema

## Integration Patterns

### Orchestrator Integration

```python
# Orchestrator coordinates all components
class Orchestrator:
    def __init__(
        self,
        llm: LLMAdapter,
        convergence_engine: ConvergenceEngine,
        semantic_validator: SemanticValidator,
        recursive_planner: RecursivePlanner,
        adaptive_depth: AdaptiveDepth,
        ...
    ):
        self.convergence_engine = convergence_engine
        self.semantic_validator = semantic_validator
        self.recursive_planner = recursive_planner
        self.adaptive_depth = adaptive_depth
```

### Phase Sequence

1. **Phase A**: `adaptive_depth.infer_task_profile()` → `adaptive_depth.allocate_ttl()`
2. **Phase B**: `recursive_planner.generate_plan()` → `semantic_validator.validate()` → `recursive_planner.refine_plan()`
3. **Phase C**: Execute → `semantic_validator.validate()` → `convergence_engine.assess()` → `recursive_planner.refine_plan()`

## Error Handling

All interfaces MUST handle errors gracefully:

1. **LLM Errors**: Catch LLMError, use supervisor repair_json() for JSON issues, fallback to previous state for semantic errors
2. **Validation Errors**: Raise ValidationError with detailed message, use supervisor repair_json() for schema violations
3. **Plan Errors**: Raise PlanError for plan-specific failures (nesting depth exceeded, invalid refinement)

## Testing Requirements

All interfaces MUST be testable with mocked dependencies:

1. **Unit Tests**: Mock LLM adapter, verify interface behavior
2. **Contract Tests**: Verify interface contracts (inputs/outputs, error handling)
3. **Integration Tests**: Test with real or mocked LLM, verify end-to-end behavior

