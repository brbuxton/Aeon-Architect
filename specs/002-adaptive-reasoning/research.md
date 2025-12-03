# Research: Sprint 2 - Adaptive Reasoning Engine

**Date**: 2025-01-27  
**Feature**: Sprint 2 - Adaptive Reasoning Engine  
**Branch**: `002-adaptive-reasoning`

## Overview

This research document consolidates technical decisions, patterns, and implementation approaches for the five Tier-1 capabilities: Multi-Pass Execution Loop, Recursive Planning & Re-Planning, Convergence Engine, Adaptive Depth Heuristics, and Semantic Validation Layer.

## Prerequisites

### Mandatory Kernel Refactoring (MUST BE COMPLETED FIRST)

**Decision**: Kernel refactoring is a mandatory prerequisite before any Sprint 2 User Stories implementation.

**Rationale**: 
- Spec requirement: "Before any Sprint 2 User Stories implementation begins, the kernel codebase MUST undergo a mandatory structural refactoring"
- Ensures compliance with constitutional LOC limits (<800 LOC)
- Maintains architectural purity by extracting non-orchestration logic
- Provides headroom for Sprint 2 kernel additions (~100-150 LOC)

**Refactoring Constraints**:
1. LOC Measurement and Reduction: Measure and reduce to <700 LOC if higher (current: 561 LOC)
2. Structural-Only: No behavior changes, no interface changes
3. Logic Extraction: Move non-orchestration logic to external modules
4. Behavioral Preservation: All Sprint 1 tests must pass without modification

**Implementation Approach**:
- Analyze kernel code for extractable logic
- Identify non-orchestration code for extraction
- Refactor while maintaining interfaces
- Run full test suite to verify behavioral preservation
- Document before/after LOC measurements

**Alternatives Considered**:
- Skip refactoring: Rejected - violates spec requirement, risks exceeding LOC limit
- Refactor during Sprint 2: Rejected - spec requires completion before Sprint 2 implementation
- Partial refactoring: Rejected - spec requires full structural refactoring

## Technical Decisions

### Decision 1: Multi-Pass Loop Architecture

**Decision**: Implement multi-pass loop as deterministic phase sequence (plan → execute → evaluate → refine → re-execute) with orchestrator coordination.

**Rationale**: 
- Deterministic phase transitions ensure predictable, debuggable control flow
- Orchestrator manages sequencing, TTL checks, and pass boundaries
- External modules (convergence, validation, recursive planner) handle semantic reasoning
- Preserves kernel minimalism while enabling adaptive execution

**Alternatives Considered**:
- LLM-controlled loop: Rejected - violates deterministic control flow requirement
- Event-driven architecture: Rejected - adds complexity without clear benefit for sequential passes
- State machine library: Rejected - simple phase enum sufficient, avoids external dependency

**Implementation Pattern**:
```python
# Orchestrator coordinates phases
for pass_num in range(max_passes):
    if ttl_expired():
        return ttl_expired_result()
    
    # Phase: EXECUTE
    execute_batch(ready_steps)
    
    # Phase: EVALUATE
    validation_report = semantic_validator.validate(plan, steps, outputs)
    convergence = convergence_engine.assess(validation_report, plan, steps)
    
    # Phase: DECIDE
    if convergence.converged:
        return converged_result()
    
    # Phase: REFINE
    if ttl_remaining:
        refinement_actions = recursive_planner.refine(validation_report, convergence)
        apply_refinements(refinement_actions)
```

### Decision 2: LLM-Only Semantic Reasoning

**Decision**: All semantic judgments (convergence, validation, adaptive depth, recursive planning) MUST use LLM-based reasoning as primary mechanism.

**Rationale**:
- Spec constraint: "Master Constraint: LLM-Based Reasoning Requirement"
- Ensures system leverages full reasoning capabilities of LLMs
- Avoids brittle pattern-matching approaches
- Handles nuanced, context-dependent semantic understanding

**Alternatives Considered**:
- Heuristic keyword matching: Rejected - violates spec constraint, too brittle
- Rule-based logic: Rejected - violates spec constraint, insufficient for semantic understanding
- Hybrid approach: Rejected - spec requires LLM as primary, heuristics only as secondary signals

**Implementation Pattern**:
```python
# All semantic modules use LLM adapter
class ConvergenceEngine:
    def assess(self, validation_report, plan, steps):
        prompt = construct_convergence_prompt(validation_report, plan, steps)
        response = self.llm.generate(prompt)
        return parse_convergence_assessment(response)  # Structured JSON output
```

### Decision 3: Modular External Components

**Decision**: Implement convergence engine, adaptive depth, semantic validation, and recursive planner as separate modules outside kernel.

**Rationale**:
- Preserves kernel minimalism (<800 LOC)
- Enables independent testing and development
- Maintains separation of concerns
- Allows future enhancements without kernel changes

**Alternatives Considered**:
- Kernel-integrated: Rejected - would violate kernel LOC limit and separation of concerns
- Single monolithic module: Rejected - violates separation of concerns, harder to test
- Tool-based: Rejected - these are orchestration capabilities, not domain tools

**Module Structure**:
```
aeon/
├── convergence/engine.py      # ConvergenceAssessment logic
├── adaptive/heuristics.py      # TaskProfile inference, TTL allocation
├── validation/semantic.py      # SemanticValidationReport logic
└── plan/recursive.py           # Recursive planning and refinement
```

### Decision 4: Declarative Plan Refinement

**Decision**: Plan refinements use delta-style operations (ADD/MODIFY/REMOVE) on declarative plan structures.

**Rationale**:
- Preserves declarative plan purity (Principle III)
- Enables incremental refinement without full plan regeneration
- Maintains step ID stability where possible
- Supports partial plan updates

**Alternatives Considered**:
- Full plan regeneration: Rejected - inefficient, loses execution context
- Procedural refinement scripts: Rejected - violates declarative plan constraint
- Graph-based refinement: Rejected - over-engineered for declarative JSON/YAML structures

**RefinementAction Pattern**:
```python
@dataclass
class RefinementAction:
    action_type: Literal["ADD", "MODIFY", "REMOVE", "REPLACE"]
    target_step_id: Optional[str]
    new_step: Optional[PlanStep]
    justification: str  # LLM-generated explanation
```

### Decision 5: In-Memory Execution History

**Decision**: ExecutionHistory stored in-memory only for Sprint 2, returned as part of execution result.

**Rationale**:
- Spec requirement: "ExecutionHistory SHALL be stored in-memory only for Sprint 2"
- Simplifies implementation, avoids persistence complexity
- Enables programmatic inspection without file I/O
- Can be extended to persistent storage in future sprints

**Alternatives Considered**:
- Persistent file storage: Rejected - out of scope for Sprint 2
- Database storage: Rejected - out of scope, adds dependency
- Streaming JSONL logs: Rejected - different use case (observability vs. inspection)

**ExecutionHistory Structure**:
```python
@dataclass
class ExecutionHistory:
    execution_id: str
    task_input: str
    configuration: Dict[str, Any]
    passes: List[ExecutionPass]
    final_result: Any
    overall_statistics: Dict[str, Any]
```

### Decision 6: TaskProfile Tier Stability

**Decision**: TaskProfile reasoning_depth must remain within ±1 tier across repeated inferences for same input.

**Rationale**:
- Spec requirement: "Tier stability requires that repeated LLM-based TaskProfile inference for the same input MUST produce reasoning_depth values within ±1 tier"
- Ensures consistent resource allocation
- Prevents oscillation between very different complexity assessments
- Maintains predictable system behavior

**Alternatives Considered**:
- No stability requirement: Rejected - would cause inconsistent TTL allocation
- Exact match requirement: Rejected - too strict, LLM outputs have natural variation
- ±2 tier tolerance: Rejected - too permissive, allows large swings

**Implementation Approach**:
- Track initial TaskProfile reasoning_depth
- On subsequent inferences, validate tier stability
- If violation detected, use previous value or apply tier constraint

### Decision 7: TTL Boundary Safety

**Decision**: TTL expiration checks occur at phase boundaries and safe step boundaries only, never interrupting non-idempotent tool operations.

**Rationale**:
- Spec requirement: "Mid-phase TTL checks SHALL apply only at safe step boundaries"
- Preserves determinism and safety
- Prevents corruption of tool state
- Enables early termination during long-running steps

**Alternatives Considered**:
- TTL checks only at phase boundaries: Rejected - too restrictive, prevents early termination
- TTL checks at any point: Rejected - violates safety, could interrupt tool operations
- Interruptible tool operations: Rejected - adds complexity, not in Sprint 2 scope

**Safe Boundary Detection**:
```python
def is_safe_ttl_check_boundary(step_state):
    return (
        step_state.status == StepStatus.PENDING or  # Before tool call
        step_state.status == StepStatus.COMPLETE or  # After tool completion
        step_state.execution_mode == "llm_reasoning"  # Interruptible reasoning
    )
```

### Decision 8: Convergence Engine Integration

**Decision**: Convergence engine consumes semantic validator output directly for coherence and consistency assessments.

**Rationale**:
- Spec requirement: "convergence engine consumes semantic validator output directly as input"
- Enables detection of contradictions, omissions, hallucinations identified by validation
- Avoids duplicate LLM calls for same semantic analysis
- Improves efficiency and consistency

**Alternatives Considered**:
- Independent convergence assessment: Rejected - misses validation insights, less efficient
- Convergence before validation: Rejected - validation provides critical input for convergence
- Single combined LLM call: Rejected - violates separation of concerns, harder to test

**Integration Pattern**:
```python
# Evaluate phase sequence
validation_report = semantic_validator.validate(plan, steps, outputs)
convergence = convergence_engine.assess(
    validation_report=validation_report,  # Direct consumption
    plan=plan,
    steps=steps,
    outputs=outputs
)
```

### Decision 9: Supervisor Repair Integration

**Decision**: Use Sprint 1 supervisor repair_json() method for all JSON/schema repair needs, do not create duplicate repair implementations.

**Rationale**:
- Spec requirement: "The system SHALL NOT create duplicate or parallel JSON repair implementations"
- Reuses proven Sprint 1 functionality
- Maintains consistency across repair operations
- Avoids code duplication

**Alternatives Considered**:
- New repair implementation: Rejected - violates spec, duplicates existing functionality
- Module-specific repair: Rejected - violates spec, creates inconsistency
- No repair: Rejected - system needs JSON repair capability

**Usage Pattern**:
```python
from aeon.supervisor.repair import Supervisor

supervisor = Supervisor(llm_adapter)
try:
    task_profile = parse_task_profile(llm_response)
except ValidationError:
    repaired_response = supervisor.repair_json(llm_response, TaskProfileSchema)
    task_profile = parse_task_profile(repaired_response)
```

### Decision 10: Refinement Attempt Limits

**Decision**: Implement per-fragment (3 attempts) and global (10 total) refinement attempt limits to prevent infinite loops.

**Rationale**:
- Spec requirement: "refinement attempt limits (e.g., 3 attempts per plan fragment with a global maximum of 10 total refinement attempts)"
- Prevents infinite refinement loops
- Ensures system terminates even with persistent validation issues
- Balances refinement effort with execution progress

**Alternatives Considered**:
- No limits: Rejected - risk of infinite loops
- Only global limit: Rejected - allows single fragment to consume all attempts
- Only per-fragment limit: Rejected - allows many fragments to each hit limit
- Higher limits: Rejected - spec provides specific guidance (3 per fragment, 10 global)

**Implementation Pattern**:
```python
@dataclass
class RefinementTracker:
    fragment_attempts: Dict[str, int]  # step_id -> attempt count
    global_attempts: int
    
    def can_refine_fragment(self, step_id: str) -> bool:
        return (
            self.fragment_attempts.get(step_id, 0) < 3 and
            self.global_attempts < 10
        )
```

## Best Practices

### LLM Prompt Engineering

1. **Structured Output**: All LLM calls for semantic reasoning MUST request structured JSON output conforming to defined schemas (TaskProfile, ConvergenceAssessment, SemanticValidationReport, RefinementAction).

2. **Context Preservation**: Prompts MUST include relevant context (plan state, step outputs, validation issues) to enable informed semantic judgments.

3. **Schema Validation**: LLM outputs MUST be validated against schemas. On schema violation, use supervisor repair_json() for retry.

4. **Error Handling**: LLM errors (timeouts, API failures) MUST be handled gracefully with fallback behavior (e.g., use previous assessment, mark as uncertain).

### Interface Design

1. **Clean Interfaces**: All external modules (convergence, adaptive, validation, recursive planner) MUST define clear interfaces with typed inputs/outputs.

2. **Interface Contracts**: Interfaces MUST be documented with expected behavior, error conditions, and side effects.

3. **Dependency Injection**: Modules receive dependencies (LLM adapter, tool registry) through constructor injection, not global state.

4. **Testability**: Interfaces MUST enable independent unit testing with mock dependencies.

### State Management

1. **Immutable Snapshots**: ExecutionHistory captures immutable snapshots of plan state, validation reports, and convergence assessments per pass.

2. **State Transitions**: Step status transitions (pending → running → complete/failed/invalid) MUST be deterministic and logged.

3. **Refinement Safety**: Refinement MUST NOT modify executed steps (status: complete or failed). Only pending/future steps can be refined.

4. **TTL Tracking**: TTL MUST be tracked per pass and decremented at phase boundaries. Mid-phase TTL checks use remaining TTL from current pass.

### Testing Strategy

1. **Unit Tests**: Each module (convergence, adaptive, validation, recursive planner) MUST have comprehensive unit tests with mocked LLM.

2. **Integration Tests**: Multi-pass execution MUST be tested end-to-end with real or mocked LLM, verifying phase transitions, convergence detection, and refinement.

3. **Contract Tests**: Interface contracts MUST be verified through contract tests ensuring modules interact correctly.

4. **Edge Cases**: Tests MUST cover edge cases: TTL expiration, refinement limits, convergence conflicts, invalid refinements.

## Integration Patterns

### Multi-Pass Loop Integration

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
        # All components injected through interfaces
```

### Phase Sequence

1. **Phase A: TaskProfile & TTL** - Adaptive depth infers TaskProfile, maps to TTL
2. **Phase B: Initial Plan & Pre-Execution Refinement** - Recursive planner generates plan, semantic validator validates, recursive planner refines
3. **Phase C: Execution Passes (1..N)** - Execute → Evaluate → Decide → Refine loop
4. **Phase D: Adaptive Depth Integration** - TaskProfile updates at pass boundaries when complexity mismatch detected

### Error Handling

1. **LLM Errors**: Catch LLM errors, use supervisor repair for JSON issues, fallback to previous state for semantic errors
2. **Validation Errors**: Surface validation errors in ExecutionHistory, continue execution with best available state
3. **Refinement Errors**: Track refinement failures, respect attempt limits, proceed with current plan state
4. **Convergence Errors**: If convergence assessment fails, treat as non-converged, continue to refinement

## Open Questions Resolved

All technical questions from the spec have been resolved through clarifications documented in spec.md. No outstanding "NEEDS CLARIFICATION" items remain in Technical Context.

## Next Steps

1. **Phase 1: Design & Contracts** - Generate data-model.md, contracts/, quickstart.md
2. **Phase 2: Task Breakdown** - Create tasks.md with implementation tasks
3. **Implementation** - Implement modules following research decisions and patterns

