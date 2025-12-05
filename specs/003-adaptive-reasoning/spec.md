# Feature Specification: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Feature Branch**: `003-adaptive-reasoning`  
**Created**: 2025-12-04  
**Status**: Draft  
**Input**: User description: "Project: Aeon Architect — Sprint 2 Specification. Expand the Sprint 1 single-pass orchestration system into a deterministic, adaptive, multi-pass reasoning engine. The system must support recursive planning, refinement, semantic validation, convergence analysis, and adaptive depth while preserving Aeon's core architectural constraints: deterministic control flow, minimal kernel, strict LLM-only semantics, and JSON/YAML declarative plans."

## Clarifications

### Session 2025-01-27

- Q: What are the specific default threshold values for completeness, coherence, and consistency that should be used when no custom criteria are provided? → A: Numeric thresholds: completeness >= 0.95, coherence >= 0.90, consistency >= 0.90 (0.0-1.0 scale)
- Q: What are the specific default values for all TaskProfile dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) when inference fails? → A: Moderate values: reasoning_depth=3, information_sufficiency=0.5, expected_tool_usage=moderate, output_breadth=moderate, confidence_requirement=medium
- Q: Should the TTL mapping function be explicitly defined in the specification, or is it acceptable to defer the specific formula to the implementation/planning phase? → A: Defer to planning phase but require deterministic mapping with documented formula
- Q: Should observability requirements (what to log, what metrics to track, what events to emit) be explicitly specified in the functional requirements, or is it acceptable to defer these details to the planning/implementation phase? → A: Defer to planning phase but require key events to be observable
- Q: How should the system handle LLM API failures during multi-pass execution? Should it retry, fail the current pass, or fall back to a degraded mode? → A: Retry with exponential backoff (e.g., 3 attempts), then fail gracefully with error result

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Pass Execution with Deterministic Phase Control (Priority: P1)

As a developer, I can submit a complex task to Aeon, and the system automatically executes multiple reasoning passes following a deterministic phase sequence until it converges on a complete, coherent solution or reaches a termination condition.

**Why this priority**: This is the foundational transformation from single-pass to multi-pass execution. Without this capability, all other Sprint 2 features (recursive planning, convergence detection, adaptive depth) cannot function. The deterministic phase sequence ensures predictable, debuggable control flow even when LLM outputs vary.

**Independent Test**: Can be fully tested by submitting a complex, ambiguous task (e.g., "design a system architecture for a web application with user authentication") and verifying that Aeon executes multiple passes following the exact phase sequence (Phase A: TaskProfile & TTL → Phase B: Initial Plan & Pre-Execution Refinement → Phase C: Execution Passes → Phase D: Adaptive Depth) until convergence is achieved or TTL expires. The test delivers value by proving the system can iteratively improve its reasoning through multiple cycles with deterministic control flow.

**Acceptance Scenarios**:

1. **Given** a developer submits a complex task requiring multiple reasoning passes, **When** Aeon processes the task, **Then** it executes Phase A (TaskProfile & TTL allocation) before any planning occurs
2. **Given** Phase A completes successfully, **When** Aeon proceeds to Phase B, **Then** it executes the exact sequence: Plan → Validate → Refine (pre-execution refinement) before beginning step execution
3. **Given** Phase B completes, **When** Aeon enters Phase C (Execution Passes), **Then** for each pass it executes: Execute Batch → Evaluate (semantic validation + convergence) → Decide (converged/refine/expire) → Refine (if needed) → Next Pass
4. **Given** Aeon executes a multi-pass loop, **When** each pass completes, **Then** the system evaluates the current state using semantic validation and convergence analysis before determining whether refinement is needed
5. **Given** Aeon determines refinement is needed, **When** the refinement phase executes, **Then** only pending or future steps are modified while executed steps remain immutable
6. **Given** Aeon reaches convergence criteria, **When** convergence is detected, **Then** the loop terminates and returns a converged result with convergence metadata (reason codes, evaluation data)
7. **Given** Aeon executes a multi-pass loop, **When** TTL reaches zero during execution, **Then** the loop terminates gracefully: if TTL expires at a phase boundary, the current pass is considered completed; if TTL expires mid-phase at a safe boundary, the current pass is NOT completed and returns partial result
8. **Given** a developer submits the same task with the same configuration multiple times, **When** Aeon processes the task, **Then** the multi-pass loop follows the same deterministic sequence of phases even if LLM outputs differ between runs

---

### User Story 2 - TaskProfile Inference and TTL Allocation (Priority: P1)

As a developer, I can submit tasks of varying complexity, and Aeon automatically infers a TaskProfile that determines appropriate TTL allocation and reasoning depth before any planning occurs.

**Why this priority**: TaskProfile inference must occur before planning (Phase A) to ensure proper resource allocation. This is a prerequisite for all subsequent phases and enables adaptive depth heuristics. Without this, the system cannot optimize resource usage or adjust reasoning strategies.

**Independent Test**: Can be fully tested by submitting tasks of varying complexity (simple: "add two numbers", complex: "design a distributed system architecture") and verifying that Aeon infers appropriate TaskProfile dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) and allocates TTL accordingly before generating any plan. The test delivers value by proving the system can assess task complexity and allocate resources appropriately.

**Acceptance Scenarios**:

1. **Given** a developer submits a task, **When** Aeon processes the task, **Then** it infers a TaskProfile with all required dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) before any plan generation occurs
2. **Given** TaskProfile inference completes, **When** the system encounters JSON/schema errors, **Then** it repairs the errors using Sprint 1 supervisor's repair_json() method without re-running TaskProfile inference
3. **Given** TaskProfile inference fails, **When** the system cannot infer a profile, **Then** it falls back to a default profile and TTL allocation
4. **Given** a TaskProfile is inferred, **When** the system maps profile dimensions to TTL, **Then** it uses a deterministic function that does not introduce additional semantic decisions
5. **Given** TaskProfile inference occurs, **When** the LLM produces the profile, **Then** it includes a raw_inference natural-language explanation summarizing how each dimension was determined

---

### User Story 3 - Recursive Planning and Plan Refinement (Priority: P1)

As a developer, I can submit tasks with ambiguous or incomplete requirements, and Aeon automatically detects missing details, generates follow-up questions, creates subplans for complex steps, and refines plan fragments without discarding the entire plan.

**Why this priority**: Recursive planning is essential for handling real-world tasks that are inherently ambiguous or complex. This capability enables the system to improve plans incrementally and handle hierarchical problem decomposition. It directly supports the multi-pass execution loop and must operate correctly to prevent the failure modes identified in previous attempts.

**Independent Test**: Can be fully tested by submitting an ambiguous task (e.g., "build a REST API") and verifying that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments using delta-style operations (ADD/MODIFY/REMOVE), and automatically incorporates semantic validation into the refinement process. The test delivers value by proving the system can handle incomplete specifications and improve plans recursively.

**Acceptance Scenarios**:

1. **Given** a developer submits a task with ambiguous requirements, **When** Aeon generates an initial plan in Phase B, **Then** the system detects low-specificity plan fragments and generates follow-up questions or refines those fragments
2. **Given** Aeon encounters a complex step that requires decomposition, **When** recursive planning is triggered, **Then** the system creates subplans or nested steps that expand the complex step into detailed substeps
3. **Given** Aeon identifies plan fragments that need refinement, **When** refinement executes, **Then** only the affected fragments are rewritten using delta-style operations (ADD/MODIFY/REMOVE) while preserving the rest of the plan structure and stable step IDs
4. **Given** Aeon generates subplans or nested steps, **When** the recursive planner processes them, **Then** plans remain declarative (JSON/YAML structures without procedural logic)
5. **Given** recursive planning occurs, **When** plan fragments are refined, **Then** semantic validation is automatically integrated into the refinement flow to ensure refined fragments meet specificity and relevance requirements
6. **Given** refinement attempts to modify executed steps, **When** the system detects this, **Then** it prevents modification of executed steps (status: complete or failed) and only allows refinement of pending or future steps
7. **Given** recursive planning creates subplans with nested structures, **When** the nesting depth exceeds the maximum allowed depth limit (5 levels), **Then** the system fails gracefully, marks the fragment as requiring manual intervention, and preserves the existing plan structure without discarding work already completed
8. **Given** a plan fragment reaches its per-fragment refinement attempt limit (3 attempts), **When** the limit is reached, **Then** the system stops refining that fragment and marks it as requiring manual intervention while execution continues with the best available version

---

### User Story 4 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

As a developer, I can receive semantic validation reports for plans, steps, and execution artifacts that identify specificity issues, logical relevance problems, do/say mismatches, hallucinated tools, and consistency violations.

**Why this priority**: Semantic validation is the intelligence substrate that all other Tier-1 features depend on. It ensures plan quality, detects issues that require refinement, identifies convergence blockers, and informs adaptive depth decisions. Without semantic validation, recursive planning and convergence detection cannot function effectively. All semantic judgments must use LLM-based reasoning as the primary mechanism.

**Independent Test**: Can be fully tested by generating a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verifying that the semantic validation layer detects these issues, classifies them using LLM-based reasoning, assigns severity scores, and proposes semantic repairs. The test delivers value by proving the system can identify semantic quality issues that structural validation cannot catch.

**Acceptance Scenarios**:

1. **Given** Aeon generates or refines a plan, **When** semantic validation processes the plan, **Then** it validates step specificity (steps are concrete and actionable), logical relevance (steps contribute to goal), and detects do/say mismatches (step description doesn't match step actions) using LLM-based reasoning
2. **Given** Aeon processes a plan with tool references, **When** semantic validation checks tool references, **Then** it detects hallucinated tools (tools that don't exist) and nonexistent operations using LLM-based reasoning, flagging them as validation issues
3. **Given** semantic validation processes a plan, **When** it analyzes step sequences, **Then** it checks internal consistency (steps logically flow, no circular dependencies, dependencies are satisfied) using LLM-based reasoning
4. **Given** semantic validation operates across execution phases, **When** it performs cross-phase validation, **Then** it verifies consistency between plan, execution steps, final answer, and memory artifacts using LLM-based reasoning
5. **Given** semantic validation detects issues, **When** validation completes, **Then** it produces validation reports with issue classifications, severity scores (determined by LLM), and proposed semantic repairs (generated by LLM) for each detected issue
6. **Given** semantic validation produces validation reports, **When** a developer reviews the reports, **Then** they understand that validation is best-effort advisory (reports may miss issues or produce false positives) and should not be treated as authoritative truth oracles
7. **Given** semantic validation encounters LLM output that deviates from schema, **When** schema violations are detected, **Then** it uses the Sprint 1 supervisor repair_json() method for structured retry rather than repairing output heuristically

---

### User Story 5 - Convergence Detection and Completion Assessment (Priority: P1)

As a developer, I can receive a converged result from Aeon that indicates whether the task is complete, coherent, and consistent, with detailed metadata explaining why convergence was achieved or why additional passes were needed.

**Why this priority**: Convergence detection is critical for determining when the system has achieved a satisfactory solution. Without this capability, the multi-pass loop would run indefinitely or terminate arbitrarily. This directly controls the termination condition for Sprint 2's execution model. The convergence engine consumes semantic validator output directly as input for coherence and consistency assessments.

**Independent Test**: Can be fully tested by executing a task through multiple passes and verifying that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met using LLM-based reasoning, returning convergence status (true/false), reason codes, and evaluation metadata. The test delivers value by proving the system can reliably determine solution quality and completion.

**Acceptance Scenarios**:

1. **Given** Aeon completes an execution pass, **When** the convergence engine evaluates the result, **Then** it performs completeness checks (all goals addressed, no missing steps), coherence checks (logical consistency, no contradictions), and cross-artifact consistency checks (plan aligns with steps, steps align with final answer) using LLM-based reasoning
2. **Given** the convergence engine detects completeness, coherence, and consistency, **When** all criteria are met, **Then** it returns converged: true with reason codes indicating which criteria were satisfied
3. **Given** the convergence engine detects contradictions, omissions, or hallucinations, **When** these issues are identified, **Then** it returns converged: false with reason codes indicating the specific issues detected (e.g., "contradiction detected", "missing step", "hallucinated tool")
4. **Given** convergence criteria are configurable, **When** custom criteria are provided, **Then** the convergence engine evaluates results against the custom criteria in addition to default checks
5. **Given** a developer submits a task without specifying custom convergence criteria, **When** the convergence engine evaluates results, **Then** it uses default thresholds (completeness >= 0.95, coherence >= 0.90, consistency >= 0.90 on a 0.0-1.0 scale) for completeness, coherence, and consistency checks (custom criteria are optional, not required)
6. **Given** the convergence engine evaluates a result, **When** convergence assessment completes, **Then** it returns evaluation metadata (completeness score, coherence score, detected issues list, artifact consistency status)
7. **Given** semantic validation processes execution artifacts (plan, steps, answer), **When** the convergence engine performs coherence and consistency assessments, **Then** it consumes semantic validator output directly as input, using validation reports to detect contradictions, omissions, hallucinations, and consistency violations identified by semantic validation
8. **Given** convergence criteria conflict (e.g., complete but incoherent), **When** the convergence engine evaluates results, **Then** it returns converged: false with reason codes indicating which criteria failed, allowing the multi-pass loop to continue refinement

---

### User Story 6 - Adaptive Depth Integration (Priority: P2)

As a developer, I can submit tasks of varying complexity, and Aeon automatically adjusts its reasoning depth, TTL allocations, and processing strategies based on TaskProfile dimensions, with updates occurring only at pass boundaries.

**Why this priority**: Adaptive depth enables the system to efficiently handle both simple and complex tasks without over-allocating resources to simple problems or under-processing complex ones. This optimizes system efficiency and improves user experience. However, it is secondary to core execution capabilities (P1) since the system can function with fixed depth while this feature enhances it. TaskProfile updates occur only at pass boundaries when multiple indicators suggest a complexity mismatch.

**Independent Test**: Can be fully tested by submitting both simple tasks (e.g., "add two numbers") and complex tasks (e.g., "design a distributed system architecture") and verifying that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on TaskProfile dimensions, with updates occurring only at pass boundaries. The test delivers value by proving the system can optimize resource allocation and reasoning effort based on task characteristics.

**Acceptance Scenarios**:

1. **Given** a developer submits a simple, well-defined task, **When** Aeon processes the task, **Then** the adaptive depth heuristics detect that TaskProfile indicates low reasoning_depth and high information_sufficiency and allocate minimal TTL and shallow reasoning depth
2. **Given** a developer submits a complex, ambiguous task, **When** Aeon processes the task, **Then** the adaptive depth heuristics detect that TaskProfile indicates high reasoning_depth or low information_sufficiency and allocate increased TTL and deep reasoning strategies
3. **Given** Aeon executes multiple passes, **When** convergence analysis indicates a complexity mismatch (convergence failure AND validation issues AND clarity_state patterns suggest mismatch), **Then** the system updates TaskProfile at the pass boundary using LLM-based reasoning
4. **Given** adaptive depth heuristics operate, **When** TaskProfile dimensions are analyzed, **Then** they integrate with semantic validation, convergence engine, and recursive planner to inform depth decisions
5. **Given** adaptive depth heuristics detect high complexity and attempt to increase TTL allocation, **When** the calculated TTL would exceed global TTL limits configured by the user or system, **Then** the heuristics cap TTL at the configured maximum rather than exceeding it, and respect all resource caps
6. **Given** adaptive depth heuristics adjust reasoning depth or TTL for a task, **When** a developer inspects the execution metadata, **Then** they can see the reason for the adjustment (e.g., TaskProfile information_sufficiency dimension indicates low sufficiency, missing details, logical gaps)

---

### Edge Cases

- **What happens when TaskProfile inference fails and no default profile is available?** → System uses a default profile with moderate values (reasoning_depth=3, information_sufficiency=0.5, expected_tool_usage=moderate, output_breadth=moderate, confidence_requirement=medium) and proceeds with execution
- **What happens when the multi-pass loop detects convergence but semantic validation identifies new issues in the next pass?** → Convergence assessment is re-evaluated in the next pass; if new issues are detected, convergence status changes to false and refinement continues
- **How does the system handle recursive planning that creates deeply nested subplans (e.g., 10+ levels of nesting)?** → When nesting depth exceeds the maximum allowed depth limit (5 levels), the system fails gracefully, marks the fragment as requiring manual intervention, and preserves the existing plan structure without discarding work already completed
- **What happens when convergence criteria are never met within the TTL limit?** → System returns latest completed pass result clearly labeled as non-converged, with TTL-expired metadata including quality metrics from convergence engine
- **What happens when TTL expires mid-phase during individual step execution?** → TTL expiration is checked only at safe step boundaries (between tool invocations, before starting tool call, after tool completion) or for interruptible reasoning steps. Non-idempotent or side-effecting tool operations are never interrupted. When TTL expires at a safe boundary, system terminates the phase and abandons the pending step (marking it incomplete) without interrupting any atomic operation
- **How does adaptive depth handle tasks that start simple but become complex during execution?** → Adaptive depth MAY revise its complexity assessment during execution based on new information and adjust reasoning depth and TTL allocations within configured caps accordingly, but updates occur only at pass boundaries
- **What happens when semantic validation detects contradictions that cannot be resolved through refinement?** → System marks conflicting fragments for manual intervention, logs conflict in metadata, continues with best available state
- **How does the system handle partial plan rewrites that create inconsistencies with already-executed steps?** → System detects inconsistencies during refinement using LLM-based reasoning, marks conflicting executed steps as invalid, and allows refinement only for pending/future steps to preserve execution integrity
- **What happens when recursive planning generates an infinite refinement loop (same fragment refined repeatedly)?** → Per-fragment and global refinement attempt limits prevent infinite loops - fragment reaches limit after 3 attempts, global limit stops all refinement after 10 total attempts
- **How does convergence detection handle cases where completeness, coherence, and consistency conflict (e.g., complete but incoherent)?** → Convergence engine returns converged: false with reason codes indicating which criteria failed, allowing multi-pass loop to continue refinement
- **What happens when semantic validation proposes repairs that conflict with recursive planner refinements?** → The conflict is surfaced in execution metadata/logs and resolved deterministically by applying the recursive planner's refinement while logging the semantic validation repair as an advisory
- **How does the system handle supervisor repair failures during the refinement phase?** → When supervisor repair fails during the refinement phase after 2 repair attempts, the system treats it as an unrecoverable refinement failure, proceeds with the current plan state (best available version), and continues to the next pass without applying refinement changes

## Requirements *(mandatory)*

### Functional Requirements

#### Phase A - TaskProfile & TTL Allocation

- **FR-001**: The system SHALL implement Phase A: TaskProfile & TTL, calling the LLM once to infer a TaskProfile for the task before any planning occurs
- **FR-002**: TaskProfile inference SHALL be the ONLY semantic step for complexity/ambiguity assessment in Phase A
- **FR-003**: The LLM MUST return qualitative fields (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement) in the TaskProfile
- **FR-004**: Host-side code MAY map TaskProfile fields/principles to numeric TTL and iteration caps using a deterministic function, and this mapping MUST NOT introduce additional semantic decisions. The mapping function SHALL be deterministic (same TaskProfile inputs produce same TTL outputs) and the formula SHALL be documented in the implementation plan
- **FR-005**: For a given pass, TaskProfile inference MUST NOT be re-run just because of JSON/schema errors
- **FR-006**: JSON/schema issues SHALL be repaired using the Sprint 1 supervisor repair_json() method (aeon.supervisor.repair.Supervisor.repair_json()) without re-running TaskProfile inference
- **FR-007**: When TaskProfile inference fails, the system SHALL fall back to a default profile with values: reasoning_depth=3, information_sufficiency=0.5, expected_tool_usage=moderate, output_breadth=moderate, confidence_requirement=medium, and allocate TTL accordingly
- **FR-008**: TaskProfile inference SHALL include a raw_inference natural-language explanation summarizing how each dimension was determined

#### Phase B - Initial Plan & Pre-Execution Refinement

- **FR-009**: The system SHALL implement Phase B: Initial Plan & Pre-Execution Refinement, following this exact sequence for Pass 0: (1) PLAN PHASE: Invoke the recursive planner to generate an initial declarative plan; (2) PLAN VALIDATION: Invoke the semantic validator on the plan only; (3) PLAN REFINEMENT: Invoke the recursive planner in refinement mode using validation issues as hard constraints
- **FR-010**: Initial plan steps MUST include: step_index (1-based), total_steps, incoming_context (may be empty initially), handoff_to_next (may be empty initially), dependencies and provides fields
- **FR-011**: Plan refinement SHALL apply ONLY delta-style changes (ADD/MODIFY/REMOVE), preserving stable step IDs where possible
- **FR-012**: Only after the Plan → Validate → Refine sequence may the system begin executing steps

#### Phase C - Execution Passes (1..N)

- **FR-013**: The system SHALL implement Phase C: Execution Passes (1..N), where for each execution pass the orchestrator MUST: (1) EXECUTE BATCH: Select all steps that are status=pending and dependencies satisfied, then execute all selected steps in parallel; (2) EVALUATE: Run the semantic validator on the updated plan + executed steps + partial outputs, run the convergence engine using semantic validator output; (3) DECIDE: If converged == true → terminate, if converged == false AND TTL remains → move to REFINEMENT, if TTL expired → return TTL-expired result; (4) REFINEMENT: Collect refinement triggers, invoke recursive planner in refinement mode, produce delta-style RefinementActions targeting future/unexecuted steps, apply deltas, update plan, and continue to the next pass
- **FR-014**: Step execution prompts MUST include actual upstream context derived from dependency outputs: "You are executing step {step_index} of {total_steps}.", "Incoming context from previous steps: {incoming_context}.", "Your goal for this step: {description}.", "You should prepare handoff for the next step as: {handoff_to_next}."
- **FR-015**: The step execution LLM MUST return: step_output and clarity_state (one of {CLEAR, PARTIALLY_CLEAR, BLOCKED})
- **FR-016**: When a step's clarity_state == BLOCKED, the system SHALL preserve the step_output, mark the step status as invalid, and include the step in refinement triggers
- **FR-017**: Refinement SHALL operate only on pending or future steps; executed steps (status: complete or failed) are immutable and MUST NOT be modified during refinement
- **FR-018**: The LLM MUST NEVER directly control the loop; it only emits structured signals (ValidationIssue, ConvergenceAssessment, RefinementAction, clarity_state), and the orchestrator decides when to start a new pass based on TTL and convergence
- **FR-019**: TTL expiration SHALL be checked at phase boundaries (between passes or at phase transitions) for multi-pass execution, and MAY be checked mid-phase only at safe step boundaries (before tool call start or after tool completion) or for interruptible reasoning steps (LLM reasoning steps)
- **FR-020**: When TTL expires mid-phase during individual step execution, the system SHALL NOT interrupt non-idempotent or side-effecting tool operations
- **FR-021**: When TTL expires at a safe boundary, the system SHALL terminate the phase and abandon the pending step (marking it incomplete) without interrupting any atomic operation, and return the latest completed pass result with TTL-expired metadata (if a complete pass exists), or return a partial result from the current incomplete pass if no passes have completed

#### Phase D - Adaptive Depth Integration

- **FR-022**: TaskProfile SHALL be computed at the start of the lifecycle and MAY be updated only at pass boundaries when convergence analysis indicates a mismatch between expected and observed complexity
- **FR-023**: TaskProfile update trigger SHALL require multiple indicators: convergence failure (converged == false) AND validation issues present AND clarity_state patterns (BLOCKED states) indicate mismatch - all these signals must be present to trigger a TaskProfile update
- **FR-024**: Adaptive depth code MUST use LLM-based TaskProfile inference for semantic aspects and use deterministic functions to convert TaskProfile into numeric TTL and caps
- **FR-025**: Adaptive depth heuristics SHALL respect all global TTL and resource limits and MUST NOT silently exceed configured limits

#### Recursive Planning & Refinement

- **FR-026**: The system SHALL support creation of subplans and nested steps to decompose complex plan steps into detailed substeps
- **FR-027**: The system SHALL support partial plan rewrites that modify only specific plan fragments without discarding the entire plan structure
- **FR-028**: During refinement, when partial plan rewrites create inconsistencies with already-executed steps, the system SHALL detect these inconsistencies using LLM-based reasoning, mark conflicting executed steps as invalid (status: invalid), and allow refinement only for pending or future steps
- **FR-029**: The system SHALL NOT allow refinement to modify steps that have already been executed (status: complete or failed), preserving the immutability of executed step results
- **FR-030**: When a plan fragment reaches its per-fragment refinement attempt limit (e.g., 3 attempts), the system SHALL stop refining that fragment and either mark it as requiring manual intervention or proceed with the best available version of that fragment
- **FR-031**: When the global refinement attempt limit is reached (e.g., 10 total attempts across all fragments), the system SHALL stop all refinement attempts and proceed with the best available plan state
- **FR-032**: The system SHALL automatically generate follow-up questions when ambiguous or low-specificity requirements are detected in plan fragments using LLM-based reasoning
- **FR-033**: During recursive planning, the system SHALL integrate semantic validation directly into the recursion flow to validate refined fragments before acceptance
- **FR-034**: Plans generated through recursive planning SHALL remain declarative (JSON/YAML structures) and SHALL NOT contain procedural logic or executable code
- **FR-035**: When recursive planning exceeds the maximum allowed nesting depth of 5 levels, the system SHALL fail gracefully, mark the fragment as requiring manual intervention, and preserve the existing plan structure without discarding work already completed

#### Semantic Validation

- **FR-036**: The system SHALL implement a semantic validation layer that validates step specificity (concreteness and actionability of step descriptions) using LLM-based reasoning as the primary mechanism
- **FR-037**: The semantic validation layer SHALL validate logical relevance of steps to the overall goal using LLM-based reasoning as the primary mechanism
- **FR-038**: The semantic validation layer SHALL detect do/say mismatches where step descriptions don't match step actions or tool invocations using LLM-based reasoning as the primary mechanism
- **FR-039**: The semantic validation layer SHALL detect hallucinated tools (tools referenced that don't exist in the tool registry) and nonexistent operations using LLM-based reasoning as the primary mechanism
- **FR-040**: The semantic validation layer SHALL validate internal consistency of step sequences (logical flow, no circular dependencies, dependencies satisfied) using LLM-based reasoning as the primary mechanism
- **FR-041**: The semantic validation layer SHALL perform cross-phase validation to ensure consistency between plan, execution steps, final answer, and memory artifacts using LLM-based reasoning as the primary mechanism
- **FR-042**: The semantic validation layer SHALL produce validation reports containing detected issues, issue classifications (determined by LLM), severity scores (determined by LLM), and proposed semantic repairs (generated by LLM)
- **FR-043**: The semantic validation layer SHALL operate as a best-effort advisory system, not a truth oracle - validation reports provide suggestions and issue classifications but may miss issues or produce false positives
- **FR-044**: If the LLM deviates from schema during semantic validation, the validator MUST use the Sprint 1 supervisor repair_json() method for structured retry rather than repairing output heuristically

#### Convergence Engine

- **FR-045**: The system SHALL implement a convergence engine that determines whether the task is finished through completeness, coherence, and consistency checks using LLM-based reasoning as the primary mechanism
- **FR-046**: The convergence engine SHALL perform completeness checks to verify all goals are addressed and no required steps are missing using LLM-based reasoning as the primary mechanism
- **FR-047**: The convergence engine SHALL perform coherence checks to verify logical consistency and detect contradictions using LLM-based reasoning as the primary mechanism
- **FR-048**: The convergence engine SHALL perform cross-artifact consistency checks to verify alignment between plan, execution steps, and final answer using LLM-based reasoning as the primary mechanism
- **FR-049**: The convergence engine SHALL consume semantic validator output directly as input for coherence and consistency assessments
- **FR-050**: When no custom criteria are provided, the convergence engine SHALL use default thresholds: completeness >= 0.95, coherence >= 0.90, consistency >= 0.90 (on a 0.0-1.0 scale) for completeness, coherence, and consistency checks
- **FR-051**: The convergence engine SHALL return converged: true/false status indicating whether convergence was achieved
- **FR-052**: The convergence engine SHALL return reason codes explaining why convergence was or was not achieved
- **FR-053**: The convergence engine SHALL return evaluation metadata including completeness scores, coherence scores, detected issues lists, and artifact consistency status
- **FR-054**: When convergence criteria conflict (e.g., complete but incoherent), the convergence engine SHALL return converged: false with reason codes indicating which specific criteria failed

#### Integration Requirements

- **FR-055**: All Tier-1 features (multi-pass loop, recursive planning, convergence engine, adaptive depth, semantic validation) SHALL integrate seamlessly without creating circular dependencies
- **FR-056**: The multi-pass loop SHALL invoke semantic validation during the evaluate phase to identify issues requiring refinement
- **FR-057**: The recursive planner SHALL use semantic validation to validate refined plan fragments before accepting them
- **FR-058**: The convergence engine SHALL use semantic validation results as input for coherence and consistency assessments
- **FR-059**: When semantic validation proposes repairs that conflict with recursive planner refinements, the system SHALL surface the conflict in execution metadata/logs and apply a deterministic resolution strategy where the recursive planner's refinement takes precedence and the semantic validation repair is recorded as an advisory

#### Non-Functional Requirements

- **FR-060**: The system SHALL preserve declarative plan purity (all plans remain JSON/YAML data structures without procedural logic)
- **FR-061**: The system SHALL maintain deterministic execution model (same inputs produce same phase transitions, though LLM outputs may vary)
- **FR-062**: The kernel codebase (kernel/orchestrator.py and kernel/executor.py combined) SHALL remain under 800 lines of code
- **FR-063**: All Sprint 2 features SHALL operate as modular components that integrate with existing kernel without requiring kernel rewrites
- **FR-064**: All semantic classification and reasoning SHALL be LLM-based; all control flow SHALL be host-based
- **FR-065**: When LLM API calls fail during multi-pass execution (network errors, timeouts, rate limits, service unavailable), the system SHALL retry with exponential backoff (e.g., 3 attempts), then fail gracefully with an error result for the current pass if all retries are exhausted

### Key Entities *(include if feature involves data)*

- **TaskProfile**: Represents inferred task characteristics with dimensions: reasoning_depth (1-5 ordinal scale), information_sufficiency (0.0-1.0 float), expected_tool_usage (enum: none, minimal, moderate, extensive), output_breadth (enum: narrow, moderate, broad), confidence_requirement (enum: low, medium, high), raw_inference (string explanation)

- **Execution Pass**: A single iteration of the multi-pass loop containing: pass_number (sequential identifier), phase (A, B, C, D), plan_state (snapshot of plan at pass start), execution_results (step outputs, tool results), evaluation_results (convergence assessment, semantic validation report), refinement_changes (plan/step modifications if any), ttl_remaining (cycles left), timing_information (start_time, end_time, duration)

- **Refinement Action**: A modification to plan or steps during refinement phase containing: type (plan_update, step_add, step_remove, step_modify, subplan_create, step_mark_invalid), target (step_id or plan section), changes (modified content), reason (why refinement was needed), semantic_validation_input (validation issues that triggered refinement), inconsistency_detected (boolean, true if refinement creates inconsistency with executed steps)

- **Convergence Assessment**: Result from convergence engine containing: converged (boolean), reason_codes (array of strings indicating why convergence was/wasn't achieved), completeness_score (numeric or categorical), coherence_score (numeric or categorical), consistency_status (object with plan/step/answer/memory alignment status), detected_issues (array of issue descriptions), metadata (additional evaluation data)

- **Semantic Validation Report**: Output from semantic validation layer containing: validation_id (unique identifier), artifact_type (plan, step, execution_artifact, cross_phase), issues (array of ValidationIssue objects), overall_severity (highest severity detected), issue_summary (counts by type), proposed_repairs (array of repair suggestions)

- **Validation Issue**: Individual issue detected by semantic validation containing: issue_id (unique identifier), type (specificity, relevance, consistency, hallucination, do_say_mismatch), severity (high, medium, low - determined by LLM), description (human-readable issue explanation), location (where issue was detected - step_id, artifact reference), proposed_repair (suggested fix generated by LLM)

- **Step**: A single step in a plan containing: step_index (int, 1-based), total_steps (int), incoming_context (Optional[str] - context from previous steps), handoff_to_next (Optional[str] - context to pass to next step), description (step goal/description), dependencies (array of step IDs), provides (array of provided artifacts), status (pending, running, complete, failed, invalid), step_output (output from execution), clarity_state (CLEAR, PARTIALLY_CLEAR, BLOCKED - returned by step execution LLM)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can submit complex tasks requiring multiple reasoning passes and receive converged results within 5 minutes of submission for 90% of tasks (accounting for multi-pass execution time)
- **SC-002**: The multi-pass execution loop successfully converges on complete, coherent solutions for 85% of complex tasks that require multiple passes
- **SC-003**: TaskProfile inference completes before plan generation in 100% of task executions
- **SC-004**: Recursive planning successfully detects and refines ambiguous or low-specificity plan fragments for 80% of tasks where the semantic validator reports one or more validation issues
- **SC-005**: The convergence engine correctly identifies convergence status (true/false) with accuracy of 90% when evaluated against manual assessment by human reviewers
- **SC-006**: Semantic validation layer detects 90% of specificity issues, logical relevance problems, do/say mismatches, and hallucinated tools in test plans containing these issues
- **SC-007**: The kernel codebase (kernel/orchestrator.py and kernel/executor.py combined) remains under 800 lines of code after Sprint 2 implementation
- **SC-008**: Multi-pass loops terminate without infinite loops in 100% of cases (through convergence or TTL expiration)
- **SC-009**: Partial plan rewrites preserve plan structure and declarative nature in 100% of refinement operations
- **SC-010**: Cross-artifact consistency checks (plan ↔ steps ↔ answer) correctly detect inconsistencies in 85% of test cases containing inconsistency
- **SC-011**: Recursive planning generates subplans and nested steps that remain declarative (no procedural logic) in 100% of cases
- **SC-012**: Adaptive depth heuristics correctly adjust reasoning depth based on TaskProfile dimensions for 85% of tasks, as measured by alignment with expected depth for TaskProfile dimensions
- **SC-013**: Phase ordering is maintained correctly (Phase A → Phase B → Phase C → Phase D) in 100% of multi-pass executions
- **SC-014**: Executed steps remain immutable during refinement in 100% of refinement operations

## Assumptions

- The system builds upon Sprint 1 capabilities (plan generation, step execution, supervisor repair, tool invocation, memory operations, TTL governance) and these continue to function as before
- LLM API access remains available and continues to support the extended multi-pass execution model
- Semantic validation can effectively detect specificity, relevance, and consistency issues through LLM-based reasoning
- Convergence criteria can be reasonably defined and measured (completeness, coherence, consistency are quantifiable or assessable through LLM-based reasoning)
- Adaptive depth heuristics can reliably detect complexity and ambiguity through LLM-based linguistic and structural analysis
- Recursive planning can decompose complex steps into meaningful subplans without creating excessive nesting depth (within the 5-level limit)
- The system operates in a single-threaded, sequential execution model (no concurrency requirements for Sprint 2)
- Kernel <800 LOC constraint can be maintained by keeping Sprint 2 features as modular, external components
- Plans remain JSON/YAML declarative structures and do not require procedural logic injection
- Deterministic execution model refers to deterministic phase transitions and control flow, not deterministic LLM outputs
- Sprint 1 supervisor's repair_json() method is available and functional for all JSON/schema repair needs

## Dependencies

- All Sprint 1 capabilities must be fully functional (plan engine, executor, supervisor, validation, tools, memory, TTL, observability)
- LLM API access for extended multi-pass execution (may require higher rate limits or quotas due to multiple passes)
- LLM-based reasoning capabilities for semantic validation, convergence assessment, TaskProfile inference, and recursive planning
- Configuration system for convergence criteria customization
- Enhanced observability/logging to track multi-pass execution, refinement actions, convergence assessments, and semantic validation reports. The system SHALL make key events observable (phase transitions, pass boundaries, convergence assessments, refinement actions) with specific log formats and metrics to be defined in the implementation plan
- Sprint 1 supervisor repair_json() method (aeon.supervisor.repair.Supervisor.repair_json()) for all JSON/schema repair operations

## Out of Scope (Sprint 2)

The following capabilities are explicitly excluded from Sprint 2 and will be considered for future sprints:

- Long-term memory (persistent storage across sessions, embeddings-based retrieval, knowledge graphs)
- Multi-agent systems (spawning sub-agents, coordinator agents, distributed supervision)
- Web research tools (web search integration, fact-checking, multi-source aggregation)
- Knowledge graph memory (graph-based storage, node/edge relationships, graph queries)
- Concurrency (parallel execution, multi-threaded reasoning, concurrent agent execution)
- Advanced tool chaining heuristics (automatic tool workflow generation, tool recommendation engines)
- Persistent execution history storage (Sprint 2 uses in-memory only storage)
