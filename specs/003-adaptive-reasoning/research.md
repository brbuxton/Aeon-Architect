# Research: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Date**: 2025-12-04  
**Feature**: Sprint 2 - Adaptive Multi-Pass Reasoning Engine  
**Phase**: 0 - Research & Technology Decisions

## Technology Decisions

### Decision 1: Multi-Pass Loop Control Architecture

**Decision**: Implement multi-pass loop control in orchestrator with minimal additions (~100-150 LOC). All semantic reasoning (convergence, validation, planning) lives in external modules.

**Rationale**: 
- Kernel must remain minimal and domain-agnostic (Principle I)
- Phase sequencing and pass management are core orchestration logic, not domain-specific
- Externalizing semantic reasoning enables independent testing and replacement
- Aligns with constitutional Principle II (Separation of Concerns)

**Alternatives Considered**:
- Full externalization of multi-pass control: Rejected - phase sequencing is core orchestration logic that belongs in kernel
- Complete kernel rewrite: Rejected - violates kernel stability principle, unnecessary for adding multi-pass capability

**Implementation Approach**:
- Add pass_number tracking and phase state management to orchestrator
- Implement deterministic phase transitions (A → B → C → D)
- Delegate semantic operations to external modules via interfaces
- Maintain TTL boundary checks at phase boundaries and safe step boundaries

### Decision 2: TTL Mapping Function Design

**Decision**: Defer specific TTL mapping formula to implementation phase but require deterministic mapping with documented formula.

**Rationale**:
- Mapping formula depends on empirical testing and resource constraints
- Formula must be deterministic (same TaskProfile → same TTL) to maintain deterministic execution model
- Documentation requirement ensures transparency and testability

**Alternatives Considered**:
- Specify exact formula in spec: Rejected - premature optimization, formula needs empirical validation
- Leave completely to implementation: Rejected - violates requirement for deterministic mapping

**Implementation Approach**:
- Design formula during implementation based on:
  - TaskProfile dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement)
  - Resource constraints (global TTL limits, rate limits)
  - Empirical testing with sample tasks
- Document formula in implementation plan and code comments
- Ensure formula is deterministic (no randomness, no semantic decisions beyond TaskProfile)

### Decision 3: Semantic Validation Architecture

**Decision**: Implement semantic validation as external module (aeon/validation/semantic.py) using LLM-based reasoning for all semantic judgments.

**Rationale**:
- Semantic validation is not core orchestration logic - it's a quality assessment capability
- External module enables independent testing and replacement
- LLM-based approach aligns with spec requirement for LLM-only semantic reasoning
- Keeps kernel minimal (Principle I)

**Alternatives Considered**:
- Embed semantic validation in kernel: Rejected - violates kernel minimalism, adds domain logic
- Use rule-based heuristics: Rejected - violates spec requirement for LLM-based semantic reasoning

**Implementation Approach**:
- Create SemanticValidator class in aeon/validation/semantic.py
- Use LLM adapter for all semantic judgments (specificity, relevance, consistency, hallucination detection)
- Return structured SemanticValidationReport with ValidationIssue objects
- Use Sprint 1 supervisor repair_json() for schema violations

### Decision 4: Convergence Engine Architecture

**Decision**: Implement convergence engine as external module (aeon/convergence/engine.py) using LLM-based reasoning for completeness, coherence, and consistency assessments.

**Rationale**:
- Convergence assessment is semantic reasoning, not orchestration logic
- External module enables independent testing and replacement
- LLM-based approach aligns with spec requirement for LLM-only semantic reasoning
- Consumes semantic validation reports as input (separation of concerns)

**Alternatives Considered**:
- Embed convergence logic in orchestrator: Rejected - violates kernel minimalism, adds semantic reasoning to kernel
- Use rule-based scoring: Rejected - violates spec requirement for LLM-based reasoning

**Implementation Approach**:
- Create ConvergenceEngine class in aeon/convergence/engine.py
- Use LLM adapter for completeness, coherence, and consistency checks
- Consume SemanticValidationReport as input for coherence/consistency assessments
- Return structured ConvergenceAssessment with converged flag, reason codes, and scores
- Use default thresholds: completeness >= 0.95, coherence >= 0.90, consistency >= 0.90

### Decision 5: Recursive Planning Architecture

**Decision**: Implement recursive planning as extension to existing plan module (aeon/plan/recursive.py) with delta-style refinement operations.

**Rationale**:
- Recursive planning is plan generation/refinement logic, not orchestration logic
- Extends existing plan module without kernel changes
- Delta-style operations (ADD/MODIFY/REMOVE) preserve plan structure and step IDs
- Integrates with semantic validation for refinement validation

**Alternatives Considered**:
- New top-level module: Considered but rejected - recursive planning is plan-related, belongs in plan module
- Kernel-based planning: Rejected - violates kernel minimalism, adds domain logic

**Implementation Approach**:
- Create RecursivePlanner class in aeon/plan/recursive.py
- Implement generate_plan() for initial plan generation
- Implement refine_plan() for delta-style refinement (ADD/MODIFY/REMOVE)
- Implement create_subplan() for nested step decomposition
- Enforce nesting depth limit (5 levels) and refinement attempt limits (3 per fragment, 10 global)
- Integrate with semantic validator for refinement validation

### Decision 6: Adaptive Depth Architecture

**Decision**: Implement adaptive depth heuristics as external module (aeon/adaptive/heuristics.py) with TaskProfile inference and TTL allocation.

**Rationale**:
- Adaptive depth is complexity assessment and resource allocation, not orchestration logic
- External module enables independent testing and replacement
- LLM-based TaskProfile inference aligns with spec requirement for LLM-only semantic reasoning
- Deterministic TTL mapping function maintains deterministic execution model

**Alternatives Considered**:
- Embed adaptive depth in orchestrator: Rejected - violates kernel minimalism, adds semantic reasoning to kernel
- Rule-based complexity assessment: Rejected - violates spec requirement for LLM-based reasoning

**Implementation Approach**:
- Create AdaptiveDepth class in aeon/adaptive/heuristics.py
- Implement infer_task_profile() using LLM adapter for all TaskProfile dimensions
- Implement allocate_ttl() using deterministic mapping function (formula to be designed in implementation)
- Implement update_task_profile() for pass-boundary updates (triggered by convergence failure + validation issues + clarity_state patterns)
- Use default TaskProfile on inference failure: reasoning_depth=3, information_sufficiency=0.5, expected_tool_usage=moderate, output_breadth=moderate, confidence_requirement=medium

### Decision 7: Execution History Storage

**Decision**: Store execution history in-memory only for Sprint 2, return as part of execution result.

**Rationale**:
- In-memory storage is sufficient for Sprint 2 scope
- Avoids persistence complexity and storage dependencies
- Execution history is returned programmatically, enabling inspection without file I/O
- Aligns with spec requirement (FR-095)

**Alternatives Considered**:
- Persistent file storage: Rejected - out of scope for Sprint 2, adds complexity
- Database storage: Rejected - out of scope for Sprint 2, adds dependencies

**Implementation Approach**:
- Create ExecutionHistory model in aeon/kernel/state.py (data structure only)
- Store ExecutionPass objects in-memory during multi-pass execution
- Return ExecutionHistory as part of execution result
- Include pass sequence, plan snapshots, refinement actions, convergence assessments, semantic validation reports

### Decision 8: LLM Failure Handling Strategy

**Decision**: Retry LLM API calls with exponential backoff (3 attempts), then fail gracefully with error result.

**Rationale**:
- Aligns with Sprint 1 patterns (mentioned in 001-aeon-core spec)
- Handles transient failures (network errors, timeouts) while providing clear failure signals for persistent issues
- Exponential backoff prevents overwhelming failed services
- Graceful failure preserves execution state and enables error reporting

**Alternatives Considered**:
- Fail immediately without retry: Rejected - too brittle, doesn't handle transient failures
- Retry indefinitely: Rejected - could hang indefinitely, violates TTL constraints
- Degraded mode fallback: Rejected - adds complexity, unclear what degraded mode means for multi-pass execution

**Implementation Approach**:
- Implement retry logic in LLM adapter layer (existing aeon/llm/adapters/)
- Use exponential backoff: initial delay 1s, backoff factor 2, max 3 attempts
- On all retries exhausted, return error result for current pass
- Log retry attempts and final failure in observability layer

### Decision 9: Observability Requirements

**Decision**: Defer detailed observability formats to implementation phase but require key events to be observable.

**Rationale**:
- Key events (phase transitions, pass boundaries, convergence assessments, refinement actions) are critical for debugging
- Specific log formats and metrics can be designed during implementation based on actual needs
- Requirement ensures observability without premature specification

**Alternatives Considered**:
- Specify detailed log formats in spec: Rejected - premature, formats need empirical validation
- Leave completely to implementation: Rejected - violates requirement for key event observability

**Implementation Approach**:
- Design log formats during implementation for:
  - Phase transitions (A → B → C → D)
  - Pass boundaries (pass start/end, TTL remaining)
  - Convergence assessments (converged flag, reason codes, scores)
  - Refinement actions (type, target, changes)
- Use existing observability infrastructure (aeon/observability/)
- Ensure logs are non-blocking and don't affect kernel determinism

### Decision 10: Step Context Propagation

**Decision**: Add step_index, total_steps, incoming_context, handoff_to_next fields to Step model for context propagation between steps.

**Rationale**:
- Enables step execution prompts to include actual upstream context from dependency outputs
- Supports deterministic dataflow between steps
- Prevents previous failure mode of missing dataflow between steps
- Minimal schema change, preserves declarative plan structure

**Alternatives Considered**:
- Implicit context propagation: Rejected - violates requirement for explicit upstream context in step prompts
- Global context object: Rejected - adds complexity, unclear ownership

**Implementation Approach**:
- Extend PlanStep model in aeon/plan/models.py with:
  - step_index: int (1-based)
  - total_steps: int
  - incoming_context: Optional[str] (context from previous steps)
  - handoff_to_next: Optional[str] (context to pass to next step)
- Update step execution prompts to include these fields
- Populate incoming_context from dependency outputs during execution
- Populate handoff_to_next from step execution LLM output

## Integration Patterns

### Pattern 1: Multi-Pass Loop Integration

**Pattern**: Orchestrator manages phase sequencing and pass boundaries. External modules (convergence, validation, planner) are invoked at specific phase points.

**Flow**:
1. Phase A: Orchestrator invokes AdaptiveDepth.infer_task_profile()
2. Phase B: Orchestrator invokes RecursivePlanner.generate_plan(), then SemanticValidator.validate(), then RecursivePlanner.refine_plan()
3. Phase C: Orchestrator executes steps, then invokes SemanticValidator.validate(), then ConvergenceEngine.assess()
4. Phase D: Orchestrator invokes AdaptiveDepth.update_task_profile() at pass boundaries when triggered

**Interface Contracts**:
- All external modules receive plan state and execution results as data structures
- All external modules return structured results (TaskProfile, SemanticValidationReport, ConvergenceAssessment, RefinementAction)
- No direct kernel internals access

### Pattern 2: Refinement Integration

**Pattern**: Recursive planner integrates with semantic validator for refinement validation.

**Flow**:
1. Semantic validator identifies issues in plan
2. Recursive planner receives validation issues as refinement triggers
3. Recursive planner generates refinement actions (ADD/MODIFY/REMOVE)
4. Semantic validator validates refined fragments before acceptance
5. Orchestrator applies validated refinements to plan

**Interface Contracts**:
- RecursivePlanner.refine_plan() accepts ValidationIssue[] as input
- RecursivePlanner.refine_plan() returns RefinementAction[]
- SemanticValidator.validate() accepts plan/step artifacts and returns SemanticValidationReport

### Pattern 3: Convergence Integration

**Pattern**: Convergence engine consumes semantic validation reports for coherence and consistency assessments.

**Flow**:
1. Semantic validator processes execution artifacts (plan, steps, answer)
2. Convergence engine receives SemanticValidationReport as input
3. Convergence engine performs completeness, coherence, and consistency checks
4. Convergence engine returns ConvergenceAssessment with converged flag and reason codes

**Interface Contracts**:
- ConvergenceEngine.assess() accepts plan state, execution results, and SemanticValidationReport
- ConvergenceEngine.assess() returns ConvergenceAssessment
- SemanticValidationReport is consumed as input, not modified

## Unresolved Items

None. All technical decisions have been made and documented.

