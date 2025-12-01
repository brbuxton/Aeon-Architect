# Feature Specification: Sprint 2 - Adaptive Reasoning Engine

**Feature Branch**: `002-adaptive-reasoning`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Sprint 2 Specification (Aeon Architect) - Evolve Aeon from a deterministic single-pass orchestrator into a recursive, adaptive, semantically-aware intelligent reasoning engine with five Tier-1 capabilities: Multi-Pass Execution Loop, Recursive Planning & Re-Planning, Convergence Engine, Adaptive Depth Heuristics, and Semantic Validation Layer."

## Clarifications

### Session 2025-01-27

- Q: When TTL expires before convergence, what should Aeon return as the "best available result"? → A: Latest completed pass result with quality metrics (latest pass + completeness/coherence scores from convergence engine)
- Q: When can TTL expiration be detected in the multi-pass loop - only at phase boundaries or at any time during execution? → A: At phase boundaries for passes, and mid-phase only at safe step boundaries (between tool invocations, before starting tool call, after tool completion) or for interruptible reasoning steps (LLM reasoning steps). Must not interrupt running tool operations.
- Q: How should refinement attempt limits be configured to prevent infinite loops - global maximum, per-pass, per-fragment, or no limit? → A: Per-plan-fragment with global maximum (e.g., 3 attempts per fragment, max 10 total across all fragments)
- Q: How should the multi-pass loop handle supervisor repair failures during the refinement phase? → A: Treat as unrecoverable refinement failure and proceed with current plan state (best available version)
- Q: How should convergence detection handle cases where completeness, coherence, and consistency conflict (e.g., complete but incoherent)? → A: Return converged: false with reason codes indicating which criteria failed, allowing multi-pass loop to continue refinement
- Q: How should the system handle partial plan rewrites that create inconsistencies with already-executed steps? → A: Detect inconsistency during refinement, mark conflicting executed steps as invalid, and allow refinement only for pending/future steps
- Q: Should mid-phase TTL termination be allowed to interrupt non-idempotent or side-effecting tool operations? → A: No - mid-phase TTL checks apply only at safe step boundaries (between tool invocations, before starting tool call, after tool completion) or for interruptible reasoning steps (LLM reasoning steps). Must not interrupt running tool operations to preserve determinism and safety.
- Q: Should User Story 1 explicitly mention deterministic control-flow behavior? → A: Yes - added explanation that multi-pass loop follows deterministic phase sequence for given configuration and input, even if LLM outputs vary, ensuring predictable and debuggable control flow
- Q: How should execution inspection capability be added - as acceptance scenario to User Story 1 or as new User Story 6? → A: Add new User Story 6 - Inspect Multi-Pass Execution (Priority: P2)
- Q: Should User Story 3 explicitly mention that convergence criteria have sensible defaults? → A: Yes - when no custom criteria are provided, convergence engine uses sensible default thresholds for completeness, coherence, and consistency
- Q: Should adaptive depth heuristics be constrained to respect global TTL and resource caps? → A: Yes - adaptive depth SHALL respect global TTL and resource caps and MUST NOT silently exceed configured limits
- Q: Can adaptive depth revise its complexity assessment during execution? → A: Yes - adaptive depth MAY revise its complexity assessment during execution and adjust depth/TTL within configured caps accordingly
- Q: Should the spec explicitly state that semantic validation is "best-effort advisory" rather than a truth oracle? → A: Yes - semantic validation is best-effort advisory and not a truth oracle; validation reports are suggestions, not authoritative determinations
- Q: Should User Story 1 explicitly distinguish between TTL expiration at phase boundary (completed pass) vs mid-phase (partial pass)? → A: Yes - if TTL expires at phase boundary, current pass is completed; if TTL expires mid-phase at safe boundary, current pass is NOT completed and returns partial result
- Q: Should User Story 2 include an acceptance scenario describing behavior when recursive planning exceeds nesting depth limits? → A: Yes - when nesting depth exceeds maximum allowed depth limit, system fails gracefully, marks fragment as requiring manual intervention, and preserves existing plan structure
- Q: Should User Story 3 explicitly mention that the convergence engine consumes semantic validator output directly? → A: Yes - convergence engine consumes semantic validator output directly as input for coherence and consistency assessments, enabling detection of contradictions, omissions, and hallucinations identified by semantic validation
- Q: Should User Story 4 explicitly state that adaptive depth can reduce TTL allocations or reasoning depth when tasks are simpler than estimated? → A: Yes - adaptive depth MAY also reduce TTL allocations or reasoning depth when tasks are detected to be simpler than previously estimated, not only increase them when complexity is high
- Q: What does "mark fragment as requiring manual intervention" mean in FR-065? → A: When a fragment is marked as requiring manual intervention, system includes advisory metadata in execution results indicating fragment needs human review, but does NOT halt execution or throw an error - refinement stops for that fragment while execution continues with best available version
- Q: How should FR-064 clarify "terminate the current step" to avoid conflict with safety rules? → A: Update wording to "terminate the phase and abandon the pending step (marking it incomplete) without interrupting any atomic operation" to clarify safety preservation
- Q: Should developers be able to see why adaptive depth adjusted reasoning depth or TTL? → A: Yes - add acceptance scenario showing execution metadata reveals adjustment reason (e.g., high ambiguity, missing details)
- Q: How should conflicts between semantic validation repairs and recursive planner refinements be handled? → A: Surface the conflict in metadata and apply a deterministic resolution strategy (recursive planner output wins, semantic validation logs advisory)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Pass Execution with Convergence (Priority: P1)

As a developer, I can submit a complex task to Aeon, and the system automatically executes multiple reasoning passes until it converges on a complete, coherent solution or reaches a termination condition.

**Why this priority**: This is the foundational transformation from single-pass to multi-pass execution. Without this capability, all other Sprint 2 features (recursive planning, convergence detection, adaptive depth) cannot function. It represents the core evolution of the system architecture. The multi-pass loop follows a deterministic sequence of phases for a given configuration and input, even if LLM outputs vary - ensuring predictable, debuggable control flow.

**Independent Test**: Can be fully tested by submitting a complex, ambiguous task (e.g., "design a system architecture for a web application with user authentication") and verifying that Aeon executes multiple passes (plan → execute → evaluate → refine → re-execute) until convergence is achieved or TTL expires. The test delivers value by proving the system can iteratively improve its reasoning through multiple cycles.

**Acceptance Scenarios**:

1. **Given** a developer submits a complex task requiring multiple reasoning passes, **When** Aeon processes the task, **Then** it executes the multi-pass loop (plan → execute → evaluate → refine → re-execute) and terminates when convergence is detected or TTL expires
2. **Given** Aeon executes a multi-pass loop, **When** each pass completes, **Then** the system evaluates the current state and determines whether refinement is needed before the next pass
3. **Given** Aeon determines refinement is needed, **When** the refinement phase executes, **Then** the plan or steps are updated while preserving the overall plan structure and declarative nature
4. **Given** Aeon reaches convergence criteria, **When** convergence is detected, **Then** the loop terminates and returns a converged result with convergence metadata (reason codes, evaluation data)
5. **Given** Aeon executes a multi-pass loop, **When** TTL reaches zero during execution, **Then** the loop terminates gracefully regardless of convergence status: if TTL expires at a phase boundary (between passes), the current pass is considered completed and the system returns the latest completed pass result; if TTL expires mid-phase at a safe boundary, the current pass is NOT considered completed and the system returns a partial pass result from the incomplete pass (if no passes have completed) or the latest completed pass result (if a complete pass exists), all clearly labeled as non-converged with TTL-expired metadata including completeness and coherence scores from the convergence engine
6. **Given** a developer submits the same task with the same configuration multiple times, **When** Aeon processes the task, **Then** the multi-pass loop follows the same deterministic sequence of phases (plan → execute → evaluate → refine → re-execute) even if LLM outputs differ between runs, ensuring predictable and debuggable control flow

---

### User Story 2 - Recursive Planning and Plan Refinement (Priority: P1)

As a developer, I can submit tasks with ambiguous or incomplete requirements, and Aeon automatically detects missing details, generates follow-up questions, creates subplans for complex steps, and refines plan fragments without discarding the entire plan.

**Why this priority**: Recursive planning is essential for handling real-world tasks that are inherently ambiguous or complex. This capability enables the system to improve plans incrementally and handle hierarchical problem decomposition. It directly supports the multi-pass execution loop.

**Independent Test**: Can be fully tested by submitting an ambiguous task (e.g., "build a REST API") and verifying that Aeon detects ambiguities, generates subplans or nested steps, refines specific plan fragments, and automatically incorporates semantic validation into the refinement process. The test delivers value by proving the system can handle incomplete specifications and improve plans recursively.

**Acceptance Scenarios**:

1. **Given** a developer submits a task with ambiguous requirements, **When** Aeon generates an initial plan, **Then** the system detects low-specificity plan fragments and generates follow-up questions or refines those fragments
2. **Given** Aeon encounters a complex step that requires decomposition, **When** recursive planning is triggered, **Then** the system creates subplans or nested steps that expand the complex step into detailed substeps
3. **Given** Aeon identifies plan fragments that need refinement, **When** refinement executes, **Then** only the affected fragments are rewritten while preserving the rest of the plan structure
4. **Given** Aeon generates subplans or nested steps, **When** the recursive planner processes them, **Then** plans remain declarative (JSON/YAML structures without procedural logic)
5. **Given** recursive planning occurs, **When** plan fragments are refined, **Then** semantic validation is automatically integrated into the refinement flow to ensure refined fragments meet specificity and relevance requirements
6. **Given** semantic validation proposes repairs that conflict with recursive planner refinements, **When** the conflict is detected, **Then** the system surfaces the conflict in execution metadata and applies a deterministic resolution strategy where the recursive planner's refinement is applied while the semantic validation repair is logged as an advisory
7. **Given** recursive planning creates subplans with nested structures, **When** the nesting depth exceeds the maximum allowed depth limit, **Then** the system fails gracefully, marks the fragment as requiring manual intervention, and preserves the existing plan structure without discarding work already completed

---

### User Story 3 - Convergence Detection and Completion Assessment (Priority: P1)

As a developer, I can receive a converged result from Aeon that indicates whether the task is complete, coherent, and consistent, with detailed metadata explaining why convergence was achieved or why additional passes were needed.

**Why this priority**: Convergence detection is critical for determining when the system has achieved a satisfactory solution. Without this capability, the multi-pass loop would run indefinitely or terminate arbitrarily. This directly controls the termination condition for Sprint 2's execution model. The convergence engine consumes semantic validator output directly as input for coherence and consistency assessments, enabling detection of contradictions, omissions, and hallucinations identified by semantic validation.

**Independent Test**: Can be fully tested by executing a task through multiple passes and verifying that the convergence engine correctly identifies when completeness, coherence, and consistency criteria are met, returning convergence status (true/false), reason codes, and evaluation metadata. The test delivers value by proving the system can reliably determine solution quality and completion.

**Acceptance Scenarios**:

1. **Given** Aeon completes an execution pass, **When** the convergence engine evaluates the result, **Then** it performs completeness checks (all goals addressed, no missing steps), coherence checks (logical consistency, no contradictions), and cross-artifact consistency checks (plan aligns with steps, steps align with final answer)
2. **Given** the convergence engine detects completeness, coherence, and consistency, **When** all criteria are met, **Then** it returns converged: true with reason codes indicating which criteria were satisfied
3. **Given** the convergence engine detects contradictions, omissions, or hallucinations, **When** these issues are identified, **Then** it returns converged: false with reason codes indicating the specific issues detected (e.g., "contradiction detected", "missing step", "hallucinated tool")
4. **Given** convergence criteria are configurable, **When** custom criteria are provided, **Then** the convergence engine evaluates results against the custom criteria in addition to default checks
5. **Given** a developer submits a task without specifying custom convergence criteria, **When** the convergence engine evaluates results, **Then** it uses sensible default thresholds for completeness, coherence, and consistency checks (custom criteria are optional, not required)
6. **Given** the convergence engine evaluates a result, **When** convergence assessment completes, **Then** it returns evaluation metadata (completeness score, coherence score, detected issues list, artifact consistency status)
7. **Given** semantic validation processes execution artifacts (plan, steps, answer), **When** the convergence engine performs coherence and consistency assessments, **Then** it consumes semantic validator output directly as input, using validation reports to detect contradictions, omissions, hallucinations, and consistency violations identified by semantic validation

---

### User Story 4 - Adaptive Reasoning Depth Based on Task Complexity (Priority: P2)

As a developer, I can submit tasks of varying complexity, and Aeon automatically adjusts its reasoning depth, TTL allocations, and processing strategies based on TaskProfile dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement).

**Why this priority**: Adaptive depth enables the system to efficiently handle both simple and complex tasks without over-allocating resources to simple problems or under-processing complex ones. This optimizes system efficiency and improves user experience. Adaptive depth MAY adjust TTL allocations and reasoning depth both upward (when TaskProfile indicates high reasoning_depth or low information_sufficiency) and downward (when TaskProfile indicates low reasoning_depth and high information_sufficiency), enabling efficient resource utilization. However, it is secondary to core execution capabilities (P1) since the system can function with fixed depth while this feature enhances it.

**Independent Test**: Can be fully tested by submitting both tasks requiring shallow reasoning as inferred from the TaskProfile (e.g., "add two numbers") and tasks requiring deep reasoning as inferred from the TaskProfile (e.g., "design a distributed system architecture") and verifying that Aeon adjusts TTL, reasoning depth, and processing strategies appropriately based on TaskProfile dimensions. The test delivers value by proving the system can optimize resource allocation and reasoning effort based on task characteristics.

**Acceptance Scenarios**:

1. **Given** a developer submits a simple, well-defined task, **When** Aeon processes the task, **Then** the adaptive depth heuristics detect that TaskProfile indicates low reasoning_depth and high information_sufficiency and allocate minimal TTL and shallow reasoning depth
2. **Given** a developer submits a complex, ambiguous task, **When** Aeon processes the task, **Then** the adaptive depth heuristics detect that TaskProfile indicates high reasoning_depth or low information_sufficiency and allocate increased TTL and deep reasoning strategies
3. **Given** Aeon detects ambiguity or uncertainty during execution, **When** TaskProfile information_sufficiency dimension indicates low sufficiency, **Then** the system dynamically adjusts TTL upward and switches to deeper reasoning modes; conversely, when TaskProfile indicates a task is simpler than previously estimated, adaptive depth MAY also reduce TTL allocations or reasoning depth accordingly (adaptive depth MAY revise TaskProfile dimensions during execution and adjust depth/TTL bidirectionally within configured caps)
4. **Given** adaptive depth heuristics operate, **When** TaskProfile dimensions are analyzed, **Then** they integrate with semantic validation, convergence engine, and recursive planner to inform depth decisions
5. **Given** heuristics analyze task characteristics, **When** token patterns, vague language, missing details, or logical gaps are detected, **Then** these indicators contribute to TaskProfile information_sufficiency dimension
6. **Given** adaptive depth heuristics detect high complexity and attempt to increase TTL allocation, **When** the calculated TTL would exceed global TTL limits configured by the user or system, **Then** the heuristics cap TTL at the configured maximum rather than exceeding it, and respect all resource caps
7. **Given** adaptive depth heuristics adjust reasoning depth or TTL for a task, **When** a developer inspects the execution metadata (e.g., execution history), **Then** they can see the reason for the adjustment (e.g., TaskProfile information_sufficiency dimension indicates low sufficiency, missing details, logical gaps)

---

### User Story 5 - Semantic Validation of Plans and Execution Artifacts (Priority: P1)

As a developer, I can receive semantic validation reports for plans, steps, and execution artifacts that identify specificity issues, logical relevance problems, do/say mismatches, hallucinated tools, and consistency violations.

**Why this priority**: Semantic validation is the intelligence substrate that all other Tier-1 features depend on. It ensures plan quality, detects issues that require refinement, identifies convergence blockers, and informs adaptive depth decisions. Without semantic validation, recursive planning and convergence detection cannot function effectively. Semantic validation operates as a best-effort advisory system, not a truth oracle - validation reports provide suggestions and issue classifications, but may miss issues or produce false positives, and should not be treated as authoritative determinations.

**Independent Test**: Can be fully tested by generating a plan with vague steps, irrelevant steps, steps that don't match their descriptions, or references to non-existent tools, and verifying that the semantic validation layer detects these issues, classifies them, assigns severity scores, and proposes semantic repairs. The test delivers value by proving the system can identify semantic quality issues that structural validation cannot catch.

**Acceptance Scenarios**:

1. **Given** Aeon generates or refines a plan, **When** semantic validation processes the plan, **Then** it validates step specificity (steps are concrete and actionable), logical relevance (steps contribute to goal), and detects do/say mismatches (step description doesn't match step actions)
2. **Given** Aeon processes a plan with tool references, **When** semantic validation checks tool references, **Then** it detects hallucinated tools (tools that don't exist) and nonexistent operations, flagging them as validation issues
3. **Given** semantic validation processes a plan, **When** it analyzes step sequences, **Then** it checks internal consistency (steps logically flow, no circular dependencies, dependencies are satisfied)
4. **Given** semantic validation operates across execution phases, **When** it performs cross-phase validation, **Then** it verifies consistency between plan, execution steps, final answer, and memory artifacts
5. **Given** semantic validation detects issues, **When** validation completes, **Then** it produces validation reports with issue classifications, severity scores, and proposed semantic repairs for each detected issue
6. **Given** the semantic validation layer operates, **When** it processes artifacts, **Then** it functions as a modular, independent component separate from the kernel (respecting kernel <800 LOC constraint)
7. **Given** semantic validation produces validation reports, **When** a developer reviews the reports, **Then** they understand that validation is best-effort advisory (reports may miss issues or produce false positives) and should not be treated as authoritative truth oracles

---

### User Story 6 - Inspect Multi-Pass Execution (Priority: P2)

As a developer, I can inspect a completed multi-pass execution and see a structured history of passes including plans, refinements, and convergence assessments for debugging and tuning.

**Why this priority**: Inspection and debugging capabilities are essential for understanding how the multi-pass execution evolved, identifying why convergence was or wasn't achieved, and tuning system parameters (convergence criteria, refinement limits, adaptive depth heuristics). However, this is secondary to core execution capabilities (P1) since the system can function without detailed inspection, though inspection significantly improves developer productivity and system understanding.

**Independent Test**: Can be fully tested by executing a multi-pass task, completing it (converged or TTL expired), and verifying that developers can access and review a structured execution history containing: pass sequence with phase transitions, plan state snapshots per pass, refinement actions and changes, convergence assessments with scores and reason codes, and semantic validation reports. The test delivers value by proving developers can debug execution issues and optimize system behavior through inspection.

**Acceptance Scenarios**:

1. **Given** a developer completes a multi-pass execution (converged or TTL expired), **When** they inspect the execution result, **Then** they can access a structured history showing all execution passes with pass numbers, phase transitions, and timing information
2. **Given** a developer inspects multi-pass execution history, **When** they review a specific pass, **Then** they can see the plan state snapshot for that pass (initial plan, any refinements applied, step statuses)
3. **Given** a developer inspects multi-pass execution history, **When** they review refinement actions, **Then** they can see what plan fragments were refined, why refinements were needed (semantic validation issues), and what changes were made
4. **Given** a developer inspects multi-pass execution history, **When** they review convergence assessments, **Then** they can see completeness scores, coherence scores, consistency status, reason codes, and detected issues for each pass
5. **Given** a developer inspects multi-pass execution history, **When** they review semantic validation reports, **Then** they can see issue classifications, severity scores, and proposed repairs for each pass
6. **Given** a developer inspects multi-pass execution history, **When** they analyze the execution, **Then** they can identify patterns (e.g., which fragments required multiple refinements, convergence blockers, effectiveness of adaptive depth adjustments) to inform tuning decisions

---

### Edge Cases

- What happens when the multi-pass loop detects convergence but semantic validation identifies new issues in the next pass?
- How does the system handle recursive planning that creates deeply nested subplans (e.g., 10+ levels of nesting)? (Answer: When nesting depth exceeds the maximum allowed depth limit, the system fails gracefully, marks the fragment as requiring manual intervention with advisory metadata in execution results (execution continues, refinement stops for that fragment), and preserves the existing plan structure without discarding work already completed)
- What happens when convergence criteria are never met within the TTL limit? (Answer: System returns latest completed pass result clearly labeled as non-converged, with TTL-expired metadata including quality metrics from convergence engine)
- What happens when TTL expires mid-phase during individual step execution? (Answer: TTL expiration is checked only at safe step boundaries or for interruptible reasoning steps. Non-idempotent or side-effecting tool operations are never interrupted. When TTL expires at a safe boundary, system terminates the phase and abandons the pending step (marking it incomplete) without interrupting any atomic operation, and returns latest completed pass result if available, or partial result from current incomplete pass if no passes have completed)
- How does adaptive depth handle tasks that start simple but become complex during execution? (Answer: Adaptive depth MAY revise its complexity assessment during execution based on new information and adjust reasoning depth and TTL allocations within configured caps accordingly)
- What happens when semantic validation detects contradictions that cannot be resolved through refinement?
- How does the system handle partial plan rewrites that create inconsistencies with already-executed steps? (Answer: System detects inconsistencies during refinement, marks conflicting executed steps as invalid, and allows refinement only for pending/future steps to preserve execution integrity)
- What happens when recursive planning generates an infinite refinement loop (same fragment refined repeatedly)? (Answer: Per-fragment and global refinement attempt limits prevent infinite loops - fragment reaches limit after 3 attempts, global limit stops all refinement after 10 total attempts)
- How does convergence detection handle cases where completeness, coherence, and consistency conflict (e.g., complete but incoherent)? (Answer: Convergence engine returns converged: false with reason codes indicating which criteria failed, allowing multi-pass loop to continue refinement)
- What happens when semantic validation identifies hallucinations in the convergence engine's own assessments?
- How does the system handle adaptive depth adjustments that exceed maximum TTL limits? (Answer: Adaptive depth heuristics cap TTL allocations at the configured maximum rather than exceeding it. When heuristics would exceed limits, TTL is set to the configured maximum and all resource caps are respected)
- What happens when semantic validation proposes repairs that conflict with recursive planner refinements? (Answer: The conflict is surfaced in execution metadata/logs and resolved deterministically by applying the recursive planner's refinement while logging the semantic validation repair as an advisory)
- How does the multi-pass loop handle supervisor repair failures during the refinement phase? (Answer: Supervisor repair failures are treated as unrecoverable refinement failures; system proceeds with current plan state and continues to next pass without applying refinement changes)

## Mandatory Kernel Refactoring Requirement

Before any Sprint 2 User Stories implementation begins, the kernel codebase MUST undergo a mandatory structural refactoring to ensure compliance with constitutional LOC limits and maintain architectural purity.

### Refactoring Constraints

1. **LOC Measurement and Reduction**: Before other Sprint 2 User Stories implementation begins, the combined LOC of `orchestrator.py` and `executor.py` MUST be measured and brought below 700 LOC if higher, to ensure headroom under the 800 LOC constitutional limit.

2. **Structural-Only Refactoring**: The refactor MUST be structural only — no behavior changes, no interface changes. All existing functionality must remain identical in behavior and external interface.

3. **Logic Extraction**: Any non-orchestration logic found in `orchestrator.py` or `executor.py` MUST be moved into appropriate external modules. Supporting kernel modules may contain only pure data structures and simple containers, and may NOT be used to circumvent kernel LOC limits.

4. **Behavioral Preservation**: After refactoring, Sprint 1 behavior MUST remain identical. Regression tests MUST confirm no behavioral drift. All existing tests must pass without modification, and no new behavioral differences must be introduced.

### Refactoring Scope

This refactoring is a prerequisite for Sprint 2 implementation and must be completed and validated before any functional requirements from Sprint 2 User Stories are implemented.

## Requirements *(mandatory)*

### Functional Requirements

#### Multi-Pass Execution Loop

- **FR-001**: The system SHALL implement a multi-pass execution loop with deterministic phase boundaries: plan → execute → evaluate → refine → re-execute → converge → stop
- **FR-002**: The multi-pass loop SHALL execute each phase sequentially and deterministically, with clear boundaries between phases
- **FR-003**: The multi-pass loop SHALL safely refine plans and steps without creating infinite loops through refinement attempt limits (e.g., 3 attempts per plan fragment with a global maximum of 10 total refinement attempts across all fragments) and convergence detection
- **FR-004**: During the refinement phase, the system SHALL integrate supervisor functionality to repair structural or semantic issues before re-execution
- **FR-067**: When supervisor repair fails during the refinement phase (e.g., after 2 repair attempts), the system SHALL treat it as an unrecoverable refinement failure, proceed with the current plan state (best available version), and continue to the next pass without applying refinement changes
- **FR-005**: During the refinement phase, the system SHALL allow updates to plan structure and step definitions while preserving the declarative nature of plans
- **FR-006**: The multi-pass loop SHALL terminate when convergence is detected OR when TTL reaches zero, whichever occurs first
- **FR-062**: When TTL expires before convergence is achieved, the system SHALL return the latest completed pass result (the most recent execution pass output), clearly labeled as non-converged, along with TTL-expired metadata including completeness score, coherence score, and other convergence assessment data from the convergence engine
- **FR-063**: TTL expiration SHALL be checked at phase boundaries (between passes or at phase transitions) for multi-pass execution, and MAY be checked mid-phase only at safe step boundaries or for interruptible reasoning steps (LLM reasoning steps) to enable early termination during long-running steps
- **FR-064**: When TTL expires mid-phase during individual step execution, the system SHALL NOT interrupt non-idempotent or side-effecting tool operations. Mid-phase TTL checks SHALL apply only at safe step boundaries (between tool invocations, before starting a tool call, or after tool completion) or for interruptible reasoning steps (LLM reasoning steps that can be safely terminated). When TTL expires at a safe boundary, the system SHALL terminate the phase and abandon the pending step (marking it incomplete) without interrupting any atomic operation, and return the latest completed pass result with TTL-expired metadata (if a complete pass exists), or return a partial result from the current incomplete pass if no passes have completed
- **FR-007**: After each pass, the system SHALL evaluate the current state and determine whether another pass is needed before proceeding to refinement
- **FR-008**: The kernel codebase SHALL remain under 800 lines of code (LOC) as measured by kernel/orchestrator.py and kernel/executor.py combined

#### Recursive Planning & Re-Planning

- **FR-009**: The system SHALL support creation of subplans and nested steps to decompose complex plan steps into detailed substeps
- **FR-010**: The system SHALL support partial plan rewrites that modify only specific plan fragments without discarding the entire plan structure
- **FR-069**: During refinement, when partial plan rewrites create inconsistencies with already-executed steps, the system SHALL detect these inconsistencies, mark conflicting executed steps as invalid (status: invalid), and allow refinement only for pending or future steps (steps with status: pending)
- **FR-070**: The system SHALL NOT allow refinement to modify steps that have already been executed (status: complete or failed), preserving the immutability of executed step results
- **FR-065**: When a plan fragment reaches its per-fragment refinement attempt limit (e.g., 3 attempts), the system SHALL stop refining that fragment and either mark it as requiring manual intervention or proceed with the best available version of that fragment. When a fragment is marked as requiring manual intervention, the system SHALL include advisory metadata in execution results indicating the fragment needs human review, but SHALL NOT halt execution or throw an error - refinement stops for that fragment while execution continues with the best available version
- **FR-066**: When the global refinement attempt limit is reached (e.g., 10 total attempts across all fragments), the system SHALL stop all refinement attempts and proceed with the best available plan state
- **FR-011**: The system SHALL automatically generate follow-up questions when ambiguous or low-specificity requirements are detected in plan fragments
- **FR-012**: The system SHALL detect ambiguous or low-specificity plan fragments and trigger refinement or question generation for those fragments
- **FR-013**: During recursive planning, the system SHALL integrate semantic validation directly into the recursion flow to validate refined fragments before acceptance
- **FR-014**: Plans generated through recursive planning SHALL remain declarative (JSON/YAML structures) and SHALL NOT contain procedural logic or executable code
- **FR-015**: The recursive planner SHALL preserve plan structure and relationships when refining fragments (e.g., step dependencies, goal alignment)
- **FR-016**: The recursive planner SHALL respect kernel minimalism and purity constraints, operating as a modular component external to the kernel core
- **FR-082**: When recursive planning exceeds the maximum allowed nesting depth of 5 levels, the system SHALL fail gracefully, mark the fragment as requiring manual intervention (including advisory metadata in execution results, execution continues, refinement stops for that fragment), and preserve the existing plan structure without discarding work already completed

#### Convergence Engine

- **FR-017**: The system SHALL implement a convergence engine that determines whether the task is finished through completeness, coherence, and consistency checks
- **FR-018**: The convergence engine SHALL perform completeness checks to verify all goals are addressed and no required steps are missing
- **FR-019**: The convergence engine SHALL perform coherence checks to verify logical consistency and detect contradictions
- **FR-020**: The convergence engine SHALL perform cross-artifact consistency checks to verify alignment between plan, execution steps, and final answer
- **FR-021**: The convergence engine SHALL detect contradictions, omissions, and hallucinations in execution artifacts
- **FR-068**: When convergence criteria conflict (e.g., complete but incoherent, or coherent but incomplete), the convergence engine SHALL return converged: false with reason codes indicating which specific criteria failed (e.g., "incomplete", "incoherent", "inconsistent"), allowing the multi-pass loop to continue refinement in subsequent passes
- **FR-022**: The convergence engine SHALL support configurable convergence criteria that can be customized per task or use case. When no custom criteria are provided, the convergence engine SHALL use sensible default thresholds for completeness, coherence, and consistency checks
- **FR-023**: The convergence engine SHALL return converged: true/false status indicating whether convergence was achieved
- **FR-024**: The convergence engine SHALL return reason codes explaining why convergence was or was not achieved (e.g., "complete", "incoherent", "missing step", "contradiction detected")
- **FR-025**: The convergence engine SHALL return evaluation metadata including completeness scores, coherence scores, detected issues lists, and artifact consistency status

#### Adaptive Depth Heuristics

- **FR-026**: Adaptive depth SHALL consume the TaskProfile to adjust reasoning depth using reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, and confidence_requirement
- **FR-027**: The system SHALL infer all TaskProfile dimensions using LLM-driven analysis of the task’s linguistic, structural, and contextual cues.
- **FR-NEW-004**: The TaskProfile inference SHALL assign concrete values to all five dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement).
- **FR-NEW-005**: The TaskProfile inference SHALL include a raw_inference natural-language explanation summarizing how each dimension was determined.
- **FR-NEW-006**: The TaskProfile inference SHALL produce dimension values that are internally coherent and non-contradictory.
- **FR-NEW-007**: The TaskProfile inference for identical input within a single pass SHALL remain stable within one tier of variation.
- **FR-NEW-008**: The TaskProfile inference SHALL only be recomputed or revised at pass boundaries.
- **FR-NEW-009**: The system SHALL implement TaskProfile inference via an LLM-driven mechanism whose input and output adhere to the TaskProfile interface, and whose output satisfies all TaskProfile acceptance criteria.
- **FR-NEW-010**: The TaskProfile inference mechanism SHALL accept a task description plus context and SHALL return a TaskProfile instance that conforms to the TaskProfile entity schema and satisfies the TaskProfile acceptance criteria.
- **FR-028**: Ambiguity and uncertainty indicators SHALL be incorporated into the information_sufficiency dimension of the TaskProfile
- **FR-029**: TTL allocation SHALL derive from TaskProfile dimensions, giving higher TTL to tasks with higher reasoning_depth or lower information_sufficiency
- **FR-030**: Reasoning depth strategies SHALL be selected based on TaskProfile dimensions, not fixed complexity categories
- **FR-NEW-001**: The system SHALL maintain versioned TaskProfile metadata across passes, updating dimensions only at pass boundaries
- **FR-NEW-002**: The system SHALL record TaskProfile version transitions in execution history
- **FR-NEW-003**: The system SHALL revise TaskProfile dimensions when validators, convergence analysis, or recursive planning reveal new information
- **FR-077**: The adaptive depth heuristics SHALL respect global TTL and resource caps and MUST NOT silently exceed configured limits. When adaptive heuristics would exceed limits, they SHALL cap TTL allocations at the configured maximum rather than exceeding it
- **FR-080**: The adaptive depth heuristics MAY revise their complexity assessment during execution based on new information (e.g., semantic validation results, convergence failures, recursive planner needs) and adjust reasoning depth and TTL allocations within configured caps accordingly. Adaptive depth MAY reduce TTL allocations or reasoning depth when tasks are detected to be simpler than previously estimated, not only increase them when complexity is high
- **FR-031**: The adaptive depth heuristics SHALL integrate with semantic validation layer to inform complexity detection (e.g., using validation issue counts as complexity indicators)
- **FR-032**: The adaptive depth heuristics SHALL integrate with convergence engine to inform depth decisions (e.g., deeper reasoning when convergence fails)
- **FR-033**: The adaptive depth heuristics SHALL integrate with recursive planner to inform depth decisions (e.g., deeper reasoning when recursive refinement is needed)
- **FR-034**: The adaptive depth heuristics MAY include token-pattern analysis to detect complexity indicators (vague language, weak verbs/nouns, logical gaps)
- **FR-035**: The adaptive depth heuristics MAY detect missing details or gradients in task specifications and increase depth accordingly

#### Semantic Validation Layer

- **FR-036**: The system SHALL implement a semantic validation layer that validates step specificity (concreteness and actionability of step descriptions)
- **FR-037**: The semantic validation layer SHALL validate logical relevance of steps to the overall goal (each step contributes meaningfully to goal achievement)
- **FR-038**: The semantic validation layer SHALL detect do/say mismatches where step descriptions don't match step actions or tool invocations
- **FR-039**: The semantic validation layer SHALL detect hallucinated tools (tools referenced that don't exist in the tool registry) and nonexistent operations
- **FR-040**: The semantic validation layer SHALL validate internal consistency of step sequences (logical flow, no circular dependencies, dependencies satisfied)
- **FR-041**: The semantic validation layer SHALL perform cross-phase validation to ensure consistency between plan, execution steps, final answer, and memory artifacts
- **FR-042**: The semantic validation layer SHALL produce validation reports containing detected issues, issue classifications, severity scores, and proposed semantic repairs
- **FR-043**: The semantic validation layer SHALL classify validation issues by type (specificity, relevance, consistency, hallucination, do/say mismatch)
- **FR-044**: The semantic validation layer SHALL assign severity scores to detected issues to prioritize repairs (e.g., high severity for contradictions, low severity for minor specificity issues)
- **FR-045**: The semantic validation layer SHALL propose semantic repairs for detected issues (suggested step rewrites, tool replacements, logical corrections)
- **FR-046**: The semantic validation layer SHALL be modular and independent of the kernel, operating through well-defined interfaces without direct kernel dependencies
- **FR-081**: The semantic validation layer SHALL operate as a best-effort advisory system, not a truth oracle. Validation reports provide suggestions and issue classifications but may miss issues or produce false positives and should not be treated as authoritative determinations of correctness

#### Integration Requirements

- **FR-047**: All Tier-1 features (multi-pass loop, recursive planning, convergence engine, adaptive depth, semantic validation) SHALL integrate seamlessly without creating circular dependencies
- **FR-048**: The multi-pass loop SHALL invoke semantic validation during the evaluate phase to identify issues requiring refinement
- **FR-049**: The recursive planner SHALL use semantic validation to validate refined plan fragments before accepting them
- **FR-050**: The convergence engine SHALL use semantic validation results as input for coherence and consistency assessments
- **FR-051**: The adaptive depth heuristics SHALL use semantic validation issue counts and severity scores as complexity indicators
- **FR-079**: When semantic validation proposes repairs that conflict with recursive planner refinements, the system SHALL surface the conflict in execution metadata/logs and apply a deterministic resolution strategy where the recursive planner's refinement takes precedence and the semantic validation repair is recorded as an advisory

#### Non-Functional Requirements

- **FR-052**: The system SHALL preserve declarative plan purity (all plans remain JSON/YAML data structures without procedural logic)
- **FR-053**: The system SHALL maintain deterministic execution model (same inputs produce same phase transitions, though LLM outputs may vary)
- **FR-054**: The kernel codebase (kernel/orchestrator.py and kernel/executor.py combined) SHALL remain under 800 lines of code
- **FR-055**: All Sprint 2 features SHALL operate as modular components that integrate with existing kernel without requiring kernel rewrites

#### Execution Inspection and History

- **FR-071**: The system SHALL provide a structured execution history for completed multi-pass executions containing: pass sequence with pass numbers, phase transitions, timing information, plan state snapshots per pass, refinement actions and changes, convergence assessments with scores and reason codes, and semantic validation reports
- **FR-072**: The execution history SHALL include plan state snapshots for each pass showing: initial plan state, any refinements applied, step statuses (pending, running, complete, failed, invalid), and step outputs
- **FR-073**: The execution history SHALL include refinement actions showing: which plan fragments were refined, why refinements were needed (semantic validation issues that triggered refinement), and what changes were made (before/after state or change description)
- **FR-074**: The execution history SHALL include convergence assessments for each pass showing: completeness scores, coherence scores, consistency status, reason codes, and detected issues
- **FR-075**: The execution history SHALL include semantic validation reports for each pass showing: issue classifications, severity scores, and proposed repairs
- **FR-076**: The execution history SHALL enable developers to identify patterns across passes (e.g., fragments requiring multiple refinements, convergence blockers, effectiveness of adaptive depth adjustments) for debugging and tuning
- **FR-078**: The execution history SHALL record adaptive depth configuration details for each pass, including adjustment_reason indicating why reasoning depth or TTL was adjusted (e.g., high ambiguity, missing details, logical gaps), so developers can inspect adjustment causes

#### Excluded Capabilities for Sprint 2

- **FR-056**: Sprint 2 SHALL NOT include long-term memory capabilities (deferred to future sprints)
- **FR-057**: Sprint 2 SHALL NOT include multi-agent systems or distributed supervision (deferred to future sprints)
- **FR-058**: Sprint 2 SHALL NOT include web research tools or knowledge graph memory (deferred to future sprints)
- **FR-059**: Sprint 2 SHALL NOT include concurrency features (deferred to future sprints)
- **FR-060**: Sprint 2 SHALL NOT include advanced tool chaining heuristics (deferred to future sprints)
- **FR-061**: Sprint 2 SHALL NOT require Short-Term Memory Engine, Supervisor Semantic Enhancements, Prompt Pipeline Enhancements, or Tool Introspection as Tier-1 features (these are Tier-2 supporting features that may be included if time permits)

### Key Entities

- **Execution Pass**: A single iteration of the multi-pass loop containing: pass_number (sequential identifier), phase (plan, execute, evaluate, refine), plan_state (snapshot of plan at pass start), execution_results (step outputs, tool results), evaluation_results (convergence assessment, semantic validation report), refinement_changes (plan/step modifications if any), ttl_remaining (cycles left), timing_information (start_time, end_time, duration)

- **Execution History**: Structured history of completed multi-pass execution containing: execution_id (unique identifier), task_input (original task description), configuration (convergence criteria, TTL, adaptive depth settings), passes (array of Execution Pass objects), final_result (converged or TTL expired result), overall_statistics (total_passes, total_refinements, convergence_achieved, total_time)

- **Refinement Action**: A modification to plan or steps during refinement phase containing: type (plan_update, step_add, step_remove, step_modify, subplan_create, step_mark_invalid), target (step_id or plan section), changes (modified content), reason (why refinement was needed), semantic_validation_input (validation issues that triggered refinement), inconsistency_detected (boolean, true if refinement creates inconsistency with executed steps)

- **Convergence Assessment**: Result from convergence engine containing: converged (boolean), reason_codes (array of strings indicating why convergence was/wasn't achieved), completeness_score (numeric or categorical), coherence_score (numeric or categorical), consistency_status (object with plan/step/answer/memory alignment status), detected_issues (array of issue descriptions), metadata (additional evaluation data)

- **Semantic Validation Report**: Output from semantic validation layer containing: validation_id (unique identifier), artifact_type (plan, step, execution_artifact, cross_phase), issues (array of issue objects), overall_severity (highest severity detected), issue_summary (counts by type), proposed_repairs (array of repair suggestions)

- **Validation Issue**: Individual issue detected by semantic validation containing: issue_id (unique identifier), type (specificity, relevance, consistency, hallucination, do_say_mismatch), severity (high, medium, low), description (human-readable issue explanation), location (where issue was detected - step_id, artifact reference), proposed_repair (suggested fix)

- **Adaptive Depth Configuration**: Settings used by adaptive depth heuristics containing: detected_complexity (score or category), ambiguity_score (numeric), uncertainty_score (numeric), allocated_ttl (cycles allocated), reasoning_mode (deep, shallow, balanced), adjustment_reason (why depth was adjusted), heuristics_used (which heuristics contributed to decision)

- **Subplan**: A nested plan structure within a parent plan step containing: parent_step_id (which step this subplan expands), subplan_goal (objective of the subplan), substeps (array of step objects following same structure as main plan steps), depth_level (nesting depth), created_by (which system component created it - recursive_planner, refinement, etc.)

- **TTL Expiration Response**: Result returned when TTL expires before convergence containing: converged (false), result_type (ttl_expired), latest_pass_result (output from the most recent completed execution pass, or null if no passes completed), partial_result (output from current incomplete pass if TTL expired mid-phase and no passes completed), expiration_point (phase_boundary or mid_phase), ttl_expired_metadata (object containing completeness_score, coherence_score, consistency_status, detected_issues, reason_codes indicating why convergence was not achieved, pass_number indicating which pass was the latest or current), termination_reason ("ttl_expired")

- **TaskProfile Schema**:  TaskProfile defined later in the fuctional requirements should use the following initial schema -
    * profile_version: integer
    * reasoning_depth: enum(low, medium, high)
    * information_sufficiency: enum(low, medium, high)
    * expected_tool_usage: enum(none, minimal, moderate, extensive)
    * output_breadth: enum(narrow, moderate, broad)
    * confidence_requirement: enum(low, medium, high)
    * raw_inference: string

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can submit tasks with high reasoning_depth or low information_sufficiency and receive converged results within 5 minutes of submission for 90% of tasks (accounting for multi-pass execution time)
- **SC-002**: The multi-pass execution loop successfully converges on complete, coherent solutions for 85% of complex tasks that require multiple passes
- **SC-003**: Recursive planning successfully detects and refines ambiguous or low-specificity plan fragments for 80% of tasks where the semantic validator reports one or more WARNING or ERROR issues
- **SC-004**: The convergence engine correctly identifies convergence status (true/false) with accuracy of 90% when evaluated against manual assessment by human reviewers
- **SC-005**: Adaptive depth heuristics correctly adjust reasoning depth based on TaskProfile dimensions for 85% of tasks, as measured by alignment with expected depth for TaskProfile dimensions
- **SC-006**: Semantic validation layer detects 90% of specificity issues, logical relevance problems, do/say mismatches, and hallucinated tools in test plans containing these issues
- **SC-007**: The kernel codebase (kernel/orchestrator.py and kernel/executor.py combined) remains under 800 lines of code after Sprint 2 implementation
- **SC-008**: Multi-pass loops terminate without infinite loops in 100% of cases (through convergence or TTL expiration)
- **SC-009**: Partial plan rewrites preserve plan structure and declarative nature in 100% of refinement operations
- **SC-010**: Cross-artifact consistency checks (plan ↔ steps ↔ answer) correctly detect inconsistencies in 85% of test cases containing inconsistency
- **SC-011**: Recursive planning generates subplans and nested steps that remain declarative (no procedural logic) in 100% of cases
- **SC-012**: Semantic validation reports include issue classifications and severity scores for 100% of detected issues
- **SC-013**: Adaptive depth heuristics integrate with semantic validation, convergence engine, and recursive planner to inform depth decisions in 100% of multi-pass executions
- **SC-014**: Developers can inspect execution history and access structured pass information (plans, refinements, convergence assessments, semantic validation reports) for 100% of completed multi-pass executions

## Assumptions

- The system builds upon Sprint 1 capabilities (plan generation, step execution, supervisor repair, tool invocation, memory operations, TTL governance) and these continue to function as before
- LLM API access remains available and continues to support the extended multi-pass execution model
- Semantic validation heuristics can effectively detect specificity, relevance, and consistency issues through pattern analysis and logical reasoning
- Convergence criteria can be reasonably defined and measured (completeness, coherence, consistency are quantifiable or assessable)
- Adaptive depth heuristics can reliably detect complexity and ambiguity through linguistic and structural analysis
- Recursive planning can decompose complex steps into meaningful subplans without creating excessive nesting depth
- The system operates in a single-threaded, sequential execution model (no concurrency requirements for Sprint 2)
- Kernel <800 LOC constraint can be maintained by keeping Sprint 2 features as modular, external components
- Plans remain JSON/YAML declarative structures and do not require procedural logic injection
- Deterministic execution model refers to deterministic phase transitions and control flow, not deterministic LLM outputs

## Dependencies

- All Sprint 1 capabilities must be fully functional (plan engine, executor, supervisor, validation, tools, memory, TTL, observability)
- LLM API access for extended multi-pass execution (may require higher rate limits or quotas due to multiple passes)
- Semantic analysis capabilities (pattern recognition, linguistic analysis, logical reasoning) for semantic validation and adaptive depth
- Configuration system for convergence criteria customization
- Enhanced observability/logging to track multi-pass execution, refinement actions, convergence assessments, and semantic validation reports

## Out of Scope (Sprint 2)

The following capabilities are explicitly excluded from Sprint 2 and will be considered for future sprints:

- Long-term memory (persistent storage across sessions, embeddings-based retrieval, knowledge graphs)
- Multi-agent systems (spawning sub-agents, coordinator agents, distributed supervision)
- Web research tools (web search integration, fact-checking, multi-source aggregation)
- Knowledge graph memory (graph-based storage, node/edge relationships, graph queries)
- Concurrency (parallel execution, multi-threaded reasoning, concurrent agent execution)
- Advanced tool chaining heuristics (automatic tool workflow generation, tool recommendation engines)
- Short-Term Memory Engine (Tier-2 supporting feature, included only if time permits)
- Supervisor Semantic Enhancements (Tier-2 supporting feature, included only if time permits)
- Prompt Pipeline Enhancements (Tier-2 supporting feature, included only if time permits)
- Tool Introspection / Selection Heuristics (Tier-2 supporting feature, included only if time permits)
