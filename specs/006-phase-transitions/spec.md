# Feature Specification: Phase Transition Stabilization & Deterministic Context Propagation

**Feature Branch**: `006-phase-transitions`  
**Created**: 2025-12-05  
**Status**: Draft  
**Input**: User description: "Project: Aeon Architect — Sprint 6

Title: Phase Transition Stabilization & Deterministic Context Propagation

Goal:

Strengthen and stabilize the A→B→C→D orchestration loop by defining explicit phase transition contracts, ensuring deterministic and complete context propagation into each LLM call, correcting TTL boundary behavior, and enforcing consistent error-handling semantics. This sprint prepares Aeon for Sprint 7 (Prompt Contracts) by ensuring that all phases operate coherently and predictably with correct contextual inputs. No new reasoning heuristics, fallback strategies, or architectural subsystems may be introduced."

## Clarifications

### Session 2025-01-27

- Q: How should LLM call failures (network errors, API rate limits, malformed responses) be handled? → A: Abort with structured error unless explicitly retryable, retry once if retryable
- Q: How should retryable vs non-retryable failures be classified? → A: Explicit enumeration in phase transition contracts (each contract lists retryable conditions)
- Q: What structure should the Context Propagation Specification use? → A: Structured document with per-phase field requirements (must-have, must-pass-unchanged, may-modify)
- Q: When exactly should TTL be checked (timing within phases)? → A: Before phase entry AND after each LLM call within phase
- Q: What format and uniqueness rules apply to correlation_id? → A: UUID v4, unique per execution, immutable

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explicit Phase Transition Contracts (Priority: P1)

As a developer maintaining the orchestration loop, I can rely on explicit, testable contracts for each phase transition (A→B, B→C, C→D, D→A/B) that define required inputs, guaranteed outputs, invariants, and enumerated failure conditions.

**Why this priority**: Without explicit contracts, phase transitions are ambiguous and error-prone. Developers cannot verify correctness or diagnose failures. This is foundational for all subsequent work in Sprint 7 (Prompt Contracts) and later sprints.

**Independent Test**: Can be fully tested by executing phase transitions with valid and invalid inputs, verifying that contracts are enforced (valid inputs produce valid outputs, invalid inputs produce structured errors), and confirming that all failure conditions are enumerated and handled. The test delivers value by proving phase transitions are deterministic and testable.

**Acceptance Scenarios**:

1. **Given** Phase A completes successfully with task_profile and TTL > 0, **When** transitioning to Phase B, **Then** Phase B receives task_profile, initial_plan, and TTL > 0 as required inputs, and produces refined_plan as output
2. **Given** Phase B completes successfully with refined_plan containing valid step fragments, **When** transitioning to Phase C, **Then** Phase C receives refined_plan with valid step fragments as required input, and produces ExecutionPass with execution_results as output
3. **Given** Phase C completes successfully with execution_results and evaluation_results, **When** transitioning to Phase D, **Then** Phase D receives execution_results + evaluation_results as required inputs, and produces depth decision (continue, escalate, or halt) as output
4. **Given** Phase D completes successfully with updated TTL and adaptive depth decision, **When** transitioning to next cycle (A/B), **Then** the next cycle receives updated TTL and adaptive depth decision as required inputs, and produces initial state for next pass as output
5. **Given** Phase A fails with incomplete profile or malformed plan, **When** the failure is detected, **Then** a structured error is logged with error code, severity, and failure condition, and execution aborts or retries once if the failure is classified as retryable
6. **Given** Phase B fails with missing steps or invalid plan fragments, **When** the failure is detected, **Then** a structured error is logged with error code, severity, and failure condition, and execution aborts or retries once if the failure is classified as retryable
7. **Given** Phase C fails with malformed evaluation signals, **When** the failure is detected, **Then** a structured error is logged with error code, severity, and failure condition, and execution aborts or retries once if the failure is classified as retryable
8. **Given** Phase D fails with TTL exhausted or invalid depth transition, **When** the failure is detected, **Then** a structured error is logged with error code, severity, and failure condition, and execution aborts (no retry for TTL exhaustion)

---

### User Story 2 - Deterministic Context Propagation (Priority: P1)

As a developer debugging LLM call failures, I can verify that every LLM call receives complete and accurate context including task profile, plan goal and step metadata, previous outputs, refinement changes, evaluation results, pass_number, phase, TTL remaining, correlation_id, and adaptive depth decision inputs.

**Why this priority**: Incomplete context propagation causes LLM reasoning failures and makes debugging impossible. All LLM prompts must receive complete context to produce correct outputs. This is foundational for Sprint 7 (Prompt Contracts) which will standardize prompt schemas.

**Independent Test**: Can be fully tested by instrumenting LLM calls to capture all context passed to prompts, verifying that required fields (task_profile, plan goal, step metadata, previous outputs, refinement changes, evaluation results, pass_number, phase, TTL remaining, correlation_id, adaptive depth inputs) are present and non-null, and confirming that context is correctly propagated between phases. The test delivers value by proving LLM calls have complete context for correct reasoning.

**Acceptance Scenarios**:

1. **Given** Phase A completes and transitions to Phase B, **When** Phase B makes LLM calls, **Then** all LLM prompts receive task_profile, initial_plan goal and step metadata, pass_number=0, phase="B", TTL remaining, and correlation_id
2. **Given** Phase B completes and transitions to Phase C, **When** Phase C makes LLM calls, **Then** all LLM prompts receive task_profile, refined_plan goal and step metadata, pass_number, phase="C", TTL remaining, correlation_id, and any refinement changes from Phase B
3. **Given** Phase C completes execution and evaluation, **When** Phase C makes LLM calls for refinement, **Then** all LLM prompts receive task_profile, current plan state, execution_results, evaluation_results (convergence assessment, validation issues), pass_number, phase="C", TTL remaining, correlation_id, and previous outputs
4. **Given** Phase D completes and transitions to next cycle, **When** the next cycle makes LLM calls, **Then** all LLM prompts receive updated task_profile, updated TTL, adaptive depth decision, pass_number, phase, correlation_id, and context from previous pass
5. **Given** context is propagated between phases, **When** reviewing context fields, **Then** fields that must be passed unchanged (correlation_id, execution_start_timestamp) are identical across all phases, and fields that may be modified (task_profile, TTL, plan state) are correctly updated
6. **Given** a phase produces new context fields, **When** transitioning to the next phase, **Then** the new fields are correctly propagated and available to the next phase's LLM calls

---

### User Story 3 - Prompt Context Alignment (Priority: P2)

As a developer reviewing prompt schemas, I can verify that all prompt schema keys are either populated by the orchestrator/phases or removed as unused, and no prompt carries null semantic inputs that would cause reasoning failures.

**Why this priority**: Null or unpopulated prompt keys cause LLM reasoning failures and make debugging difficult. All prompt schemas must be aligned with actual context propagation. This is secondary to context propagation (P1) but critical for Sprint 7 (Prompt Contracts) which will standardize prompt schemas.

**Independent Test**: Can be fully tested by reviewing all prompt schemas, verifying that all required keys are populated by orchestrator/phases, identifying unused keys that should be removed, and confirming that no prompt contains null semantic inputs. The test delivers value by proving prompt schemas are correct and complete.

**Acceptance Scenarios**:

1. **Given** a prompt schema defines required keys, **When** the orchestrator/phases construct the prompt, **Then** all required keys are populated with non-null values
2. **Given** a prompt schema contains unused keys, **When** reviewing the schema, **Then** unused keys are either removed or documented as optional/future use
3. **Given** a prompt schema contains keys that are never populated, **When** reviewing the schema, **Then** the keys are either removed or the orchestrator/phases are updated to populate them
4. **Given** all prompt schemas are reviewed, **When** executing a multi-pass reasoning task, **Then** no prompt contains null semantic inputs that would cause reasoning failures

---

### User Story 4 - TTL Boundary Behavior (Priority: P1)

As a developer debugging TTL expiration, I can verify that TTL decrements exactly once per cycle, TTL behavior at boundaries (1, 0, expiration) is specified and correct, and TTLExpirationResponse is used as the error mechanism.

**Why this priority**: Incorrect TTL behavior causes premature termination or infinite loops. TTL must be deterministic and correct at all boundaries. This is foundational for system reliability.

**Independent Test**: Can be fully tested by executing tasks with various TTL values (1, 2, 10), verifying that TTL decrements exactly once per cycle, confirming correct behavior at TTL=1, TTL=0, and expiration boundaries, and validating that TTLExpirationResponse is used for all expiration cases. The test delivers value by proving TTL behavior is deterministic and correct.

**Acceptance Scenarios**:

1. **Given** execution starts with TTL=N, **When** a complete cycle (A→B→C→D) executes, **Then** TTL decrements exactly once to N-1
2. **Given** TTL reaches 1, **When** the next cycle begins, **Then** TTL is checked before phase entry, and if TTL=1, the cycle is allowed to complete before expiration
3. **Given** TTL reaches 0, **When** checking TTL at phase boundary, **Then** TTLExpirationResponse is generated with expiration_type="phase_boundary", phase, pass_number, ttl_remaining=0, plan_state, execution_results, and message
4. **Given** TTL reaches 0 during phase execution (mid-phase), **When** checking TTL mid-phase, **Then** TTLExpirationResponse is generated with expiration_type="mid_phase", phase, pass_number, ttl_remaining=0, plan_state, partial execution_results, and message
5. **Given** TTL expires, **When** handling expiration, **Then** no heuristic TTL adjustments are made, and TTLExpirationResponse is the only error mechanism used

---

### User Story 5 - ExecutionPass Consistency (Priority: P2)

As a developer reviewing execution history, I can verify that ExecutionPass objects are consistent across the loop, with required fields populated before each phase, required fields populated after each phase, and invariants maintained for merging execution_results and evaluation_results.

**Why this priority**: Inconsistent ExecutionPass objects cause debugging failures and make execution history unreliable. ExecutionPass must be consistent and complete. This is secondary to phase transitions (P1) but critical for observability and debugging.

**Independent Test**: Can be fully tested by executing a multi-pass task, verifying that each ExecutionPass has required fields populated before phase entry, required fields populated after phase exit, and invariants maintained (execution_results and evaluation_results are correctly merged, refinement_changes are correctly applied). The test delivers value by proving ExecutionPass consistency and completeness.

**Acceptance Scenarios**:

1. **Given** Phase C begins execution, **When** ExecutionPass is created, **Then** required fields (pass_number, phase, plan_state, ttl_remaining, timing_information.start_time) are populated
2. **Given** Phase C completes execution batch, **When** execution_results are generated, **Then** execution_results are added to ExecutionPass.execution_results, and ExecutionPass remains consistent
3. **Given** Phase C completes evaluation, **When** evaluation_results are generated, **Then** evaluation_results are merged into ExecutionPass.evaluation_results, and ExecutionPass remains consistent
4. **Given** Phase C completes refinement, **When** refinement_changes are generated, **Then** refinement_changes are added to ExecutionPass.refinement_changes, and ExecutionPass remains consistent
5. **Given** Phase C completes, **When** ExecutionPass is finalized, **Then** required fields (timing_information.end_time, timing_information.duration) are populated, and ExecutionPass is complete and consistent
6. **Given** execution_results and evaluation_results are merged, **When** reviewing ExecutionPass, **Then** invariants are maintained (execution_results contain step outputs, evaluation_results contain convergence assessment and validation report, no conflicts between results)

---

### User Story 6 - Phase Boundary Logging (Priority: P2)

As a developer debugging phase transitions, I can review logs showing phase entry, phase exit, deterministic state snapshots, TTL snapshots, and structured error logs for every phase boundary.

**Why this priority**: Without phase boundary logging, developers cannot trace failures through phase transitions. All phase boundaries must be logged for debugging. This is secondary to phase transitions (P1) but critical for observability.

**Independent Test**: Can be fully tested by executing a multi-pass task, verifying that every phase boundary produces phase entry log, phase exit log, deterministic state snapshot, TTL snapshot, and structured error log (if failure occurs), and confirming that all logs use existing logging schema. The test delivers value by proving phase transitions are fully observable.

**Acceptance Scenarios**:

1. **Given** Phase A begins, **When** phase entry occurs, **Then** a phase entry log is generated with phase="A", event="phase_entry", correlation_id, pass_number, and timestamp
2. **Given** Phase A completes successfully, **When** phase exit occurs, **Then** a phase exit log is generated with phase="A", event="phase_exit", correlation_id, pass_number, duration, outcome="success", and timestamp
3. **Given** Phase A fails, **When** phase exit occurs, **Then** a phase exit log is generated with phase="A", event="phase_exit", correlation_id, pass_number, duration, outcome="failure", and a structured error log is generated with error_code, severity, affected_component, and error context
4. **Given** a phase transition occurs, **When** reviewing logs, **Then** deterministic state snapshots are logged showing plan state, TTL remaining, and phase state before and after transition
5. **Given** TTL changes during phase execution, **When** reviewing logs, **Then** TTL snapshots are logged showing TTL before phase entry, TTL after phase exit, and TTL at phase boundaries

---

### Edge Cases

- What happens when Phase A fails with incomplete profile but TTL > 0? System must abort with structured error, no retry (incomplete profile is not retryable)
- What happens when Phase B fails with malformed plan but TTL > 0? System must abort with structured error, retry once if malformed plan is classified as retryable (e.g., JSON parsing error)
- What happens when Phase C fails with malformed evaluation signals but TTL > 0? System must abort with structured error, retry once if malformed evaluation is classified as retryable (e.g., missing required fields)
- What happens when Phase D fails with TTL exhausted? System must abort with TTLExpirationResponse, no retry (TTL exhaustion is not retryable)
- What happens when context propagation fails (e.g., correlation_id is None)? System must abort with structured error, no retry (context propagation failure is not retryable)
- What happens when TTL decrements to 0 mid-phase? System must generate TTLExpirationResponse with expiration_type="mid_phase" and abort execution
- What happens when TTL decrements to 0 at phase boundary? System must generate TTLExpirationResponse with expiration_type="phase_boundary" and abort execution
- What happens when ExecutionPass consistency check fails? System must abort with structured error, no retry (consistency failure is not retryable)
- What happens when phase boundary logging fails? System must continue execution but log the logging failure as a warning (logging failures must not block execution)
- What happens when an LLM call fails (network error, API rate limit, malformed response)? System must abort with structured error unless the failure is explicitly classified as retryable (e.g., transient network error), then retry once. If retry fails, abort with structured error.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase Transition Contracts

- **FR-001**: The system MUST define explicit input requirements, output guarantees, invariants, and failure modes for A→B transition (Profiling → Refinement). Required inputs: task_profile, initial_plan, TTL > 0. Required output: refined_plan. Enumerated failure conditions: incomplete profile (non-retryable), malformed plan (retryable if JSON parsing error, non-retryable if structural invalidity).
- **FR-002**: The system MUST define explicit input requirements, output guarantees, invariants, and failure modes for B→C transition (Refinement → Execution). Required inputs: refined plan with valid step fragments. Required output: ExecutionPass with execution_results. Enumerated failure conditions: missing steps (non-retryable), invalid plan fragments (retryable if missing required fields, non-retryable if structural invalidity).
- **FR-003**: The system MUST define explicit input requirements, output guarantees, invariants, and failure modes for C→D transition (Execution → Adaptive Depth). Required inputs: execution_results + evaluation_results. Required output: depth decision (continue, escalate, or halt). Enumerated failure conditions: malformed evaluation signals (retryable if missing required fields, non-retryable if structural invalidity).
- **FR-004**: The system MUST define explicit input requirements, output guarantees, invariants, and failure modes for D→A/B transition (Depth → Next Cycle). Required inputs: updated TTL, adaptive depth decision. Required output: initial state for next pass. Enumerated failure conditions: TTL exhausted (non-retryable), invalid depth transition (non-retryable).
- **FR-005**: All phase transition contracts MUST be explicit and testable. The system MUST NOT invent additional phase types or flexible heuristics beyond the four defined phases (A, B, C, D).

#### Phase Transition Invariants (FR-001–FR-004)

For all phase transitions (A→B, B→C, C→D, D→A/B), the following invariants MUST hold:

- `correlation_id` MUST remain unchanged.
- `execution_start_timestamp` MUST remain unchanged.
- `TTL_remaining` MUST be > 0 at phase entry.
- The active plan reference (plan identifier) MUST remain consistent unless the phase explicitly replaces the plan as part of its contract.
- No memory context or external state MAY be implicitly introduced into the phase context.


#### Phase Transition Failure Contracts

- **FR-006**: Each phase transition contract MUST explicitly enumerate all failure conditions and classify each as retryable or non-retryable. The contract MUST define valid inputs, valid outputs, enumerated failure conditions with retryability classification, and allowed responses (abort execution with structured error, or retry once ONLY if the failure is explicitly classified as retryable in the contract).
- **FR-007**: The system MUST NOT introduce new fallback or recovery frameworks, "graceful degradation" paths, partial-success semantics, or new decision or classification engines in this sprint.
- **FR-008**: All failure semantics MUST use existing models (ExecutionPass, ExecutionHistory, TTLExpirationResponse, etc.) without expansion or modification beyond fixing bugs.
- **FR-009**: When a phase transition fails, the system MUST log a structured error with error_code (format: "AEON.PHASE_TRANSITION.<CODE>"), severity (CRITICAL/ERROR/WARNING/INFO), affected_component, failure_condition, and correlation_id.
- **FR-010**: When a phase transition fails with a retryable condition, the system MUST retry the transition exactly once. If the retry fails, the system MUST abort with structured error.
- **FR-011**: For every LLM call or in transition between phases, the system MUST detect provider failures (network errors, TTL exhaustion, incomplete profile, timeouts, rate limits, malformed responses) and MUST abort the current phase with a structured error unless the failure is explicitly classified as retryable in the phase contract. If the failure is classified as retryable, the system MUST retry the LLM call exactly once. If the retry also fails, the system MUST abort with a structured error using the standard logging and error format.

#### Context Propagation

- **FR-012**: The system MUST define a unified Context Propagation Specification as a structured document that specifies, for each phase (A, B, C, D), what fields must be constructed before phase entry (must-have), what fields must be passed unchanged between phases (must-pass-unchanged), and what fields may be produced/modified only by specific phases (may-modify). The specification MUST be explicit and testable, enabling validation that all required fields are present before LLM calls.

##### Context Propagation Specification (FR-012)

The following table defines the required context fields for each phase.  
- **Must-Have**: MUST be present and non-null before entering the phase.  
- **Must-Pass-Unchanged**: MUST retain the same value across all phases.  
- **May-Modify**: MAY be added or modified only by the listed phase.  
- **Prohibited**: MUST NOT appear in this phase’s input context.

| Phase | Must-Have | Must-Pass-Unchanged | May-Modify | Prohibited |
|-------|------------|----------------------|-------------|-------------|
| **A → B** | request, pass_number, phase="A", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | task_profile, initial_plan | execution_results, evaluation_results, refinement_changes |
| **B → C** | request, task_profile, initial_plan, pass_number, phase="B", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | refined_plan, refinement_changes | execution_results |
| **C1 (Execute)** | request, task_profile, refined_plan, pass_number, phase="C", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | execution_results | evaluation_results, refinement_changes |
| **C2 (Evaluate)** | request, task_profile, plan_state, execution_results, pass_number, phase="C", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | evaluation_results | refinement_changes if evaluation not complete |
| **C3 (Refine)** | request, task_profile, plan_state, execution_results, evaluation_results, pass_number, phase="C", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | refinement_changes | None |
| **D → Next Cycle** | request, task_profile, plan_state, evaluation_results, pass_number, phase="D", TTL_remaining, correlation_id, execution_start_timestamp | correlation_id, execution_start_timestamp | adaptive_depth_decision, updated_TTL | initial_plan, refined_plan |

##### Global Invariants
- **correlation_id** MUST remain identical across all phases.  
- **execution_start_timestamp** MUST remain identical across all phases.  
- **TTL_remaining** MAY only decrement once per complete cycle (A→B→C→D).  
- Each field MAY only be modified by the phase(s) listed under **May-Modify**.

##### Request Definition (FR-012)
- For all phases, `request` MUST be the original user input string passed into Aeon for this execution.  
- No phase MAY replace or structurally transform `request`; derived representations (profiles, plans, summaries) MUST be stored in separate fields.

#### Phase Transition Requisite Context

- **FR-013**: For Phase A LLM calls, the system MUST provide minimal context: request, pass_number=0, phase="A", TTL remaining, correlation_id, execution_start_timestamp.
- **FR-014**: For Phase B LLM calls, the system MUST provide minimal context: request, task_profile, initial_plan goal and step metadata, pass_number=0, phase="B", TTL remaining, correlation_id, execution_start_timestamp.
- **FR-015**: For Phase C LLM calls (execution), the system MUST provide minimal context: request, task_profile, refined_plan goal and step metadata, pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp, previous outputs (if relevant), refinement changes (if relevant).
- **FR-016**: For Phase C LLM calls (evaluation), the system MUST provide minimal context: request, task_profile, current plan state, execution_results, pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp.
- **FR-017**: For Phase C LLM calls (refinement), the system MUST provide minimal context: request, task_profile, current plan state, execution_results, evaluation_results (convergence assessment, validation issues), pass_number, phase="C", TTL remaining, correlation_id, execution_start_timestamp, previous outputs.
- **FR-018**: For Phase D LLM calls, the system MUST provide minimal context: request, task_profile, evaluation_results, plan state, pass_number, phase="D", TTL remaining, correlation_id, execution_start_timestamp, adaptive depth decision inputs.
- **FR-019**: The system MUST ensure that correlation_id and execution_start_timestamp are passed unchanged between all phases (never modified). The correlation_id MUST be a UUID v4, unique per execution, and immutable throughout the execution lifecycle.
- **FR-020**: The system MUST ensure that task_profile, TTL, plan state, execution_results, evaluation_results, and adaptive depth inputs are correctly propagated between phases according to the Context Propagation Specification.
- **FR-021**: The system MUST NOT introduce memory propagation, historical summarization, or other narrative heuristics in this sprint. Context propagation refers only to process context (task_profile, plan state, execution state, evaluation state, TTL, correlation_id).

#### Prompt Context Alignment

- **FR-022**: All prompt schemas MUST be reviewed and updated to remove unused keys OR ensure the orchestrator/phases populate them.
- **FR-023**: All keys required for reasoning MUST be populated; no prompt may carry null semantic inputs.
- **FR-024**: The system MUST NOT introduce memory propagation, historical summarization, or other narrative heuristics in prompt schemas in this sprint.

#### TTL Boundary Behavior

- **FR-025**: TTL MUST decrement exactly once per cycle (A→B→C→D completes one cycle).
- **FR-026**: TTL behavior at boundaries (TTL=1, TTL=0, expiration) MUST be explicitly specified and implemented correctly.
- **FR-027**: When TTL reaches 0, the system MUST use TTLExpirationResponse as the error mechanism, with expiration_type ("phase_boundary" or "mid_phase"), phase, pass_number, ttl_remaining=0, plan_state, execution_results, and message.
- **FR-028**: The system MUST NOT introduce heuristic TTL adjustments in this sprint. TTL decrements deterministically once per cycle.
- **FR-029**: When TTL reaches 0 at phase boundary, the system MUST check TTL before phase entry and generate TTLExpirationResponse with expiration_type="phase_boundary".
- **FR-030**: When TTL reaches 0 mid-phase, the system MUST check TTL after each LLM call within the phase and generate TTLExpirationResponse with expiration_type="mid_phase" if TTL=0 is detected.
- **FR-030a**: The system MUST check TTL before phase entry (to catch phase_boundary expiration) AND after each LLM call within a phase (to catch mid_phase expiration).

#### ExecutionPass Consistency

- **FR-031**: The system MUST define required fields before each phase: pass_number, phase, plan_state, ttl_remaining, timing_information.start_time.
- **FR-032**: The system MUST define required fields after each phase: execution_results (if Phase C), evaluation_results (if Phase C), refinement_changes (if Phase C refinement occurred), timing_information.end_time, timing_information.duration.
- **FR-033**: The system MUST define invariants for merging execution_results and evaluation_results: execution_results contain step outputs and status, evaluation_results contain convergence assessment and validation report, no conflicts between results.
- **FR-034**: ExecutionPass MUST NOT be expanded with new reasoning or memory fields in this sprint. Only bug fixes and consistency improvements are permitted.

##### ExecutionPass Timing Information Structure

- `timing_information` MUST be a nested object with the following fields:

   - `start_time`: ISO 8601 timestamp (string).
   - `end_time`: ISO 8601 timestamp (string).
   - `duration_seconds`: float representing (end_time - start_time) in seconds.
- No additional fields are required for Sprint 6.


#### Logging Requirements

- **FR-035**: Every phase boundary MUST produce phase entry log with fields: phase, event="phase_entry", correlation_id, pass_number, timestamp.
- **FR-036**: Every phase boundary MUST produce phase exit log with fields: phase, event="phase_exit", correlation_id, pass_number, duration, outcome (success/failure), timestamp.
- **FR-037**: Every phase boundary MUST produce deterministic state snapshot with fields: plan_state, ttl_remaining, phase_state (before and after transition).
- **FR-038**: Every phase boundary MUST produce TTL snapshot with fields: ttl_before, ttl_after, ttl_at_boundary.
- **FR-039**: Every phase boundary failure MUST produce structured error log with fields: error_code, severity, affected_component, failure_condition, correlation_id, phase, pass_number.
- **FR-040**: All logging MUST use existing logging schema from Sprint 5. No new logging subsystems may be introduced in this sprint.

### Key Entities

- **PhaseTransitionContract**: Explicit contract defining input requirements, output guarantees, invariants, and failure modes for a phase transition (A→B, B→C, C→D, D→A/B). Contracts are testable and deterministic.
- **ContextPropagationSpecification**: Structured document defining, for each phase (A, B, C, D), what fields must be constructed before phase entry (must-have), what fields must be passed unchanged between phases (must-pass-unchanged), and what fields may be produced/modified only by specific phases (may-modify). This is process context only (not memory). The specification must be explicit and testable, enabling validation that all required fields are present before LLM calls.
- **ExecutionPass**: Represents a single iteration of the multi-pass loop with required fields (pass_number, phase, plan_state, execution_results, evaluation_results, refinement_changes, ttl_remaining, timing_information). Must be consistent across the loop with invariants maintained.
- **TTLExpirationResponse**: Response structure when TTL expires during execution, with expiration_type ("phase_boundary" or "mid_phase"), phase, pass_number, ttl_remaining=0, plan_state, execution_results, and message. Used as the error mechanism for TTL expiration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All A→B→C→D transitions are deterministic, logged, and testable. 100% of phase transitions produce phase entry/exit logs with correlation_id, and all transitions can be verified with unit tests.
- **SC-002**: All LLM prompts see complete and accurate context. 100% of LLM calls receive all required context fields (task_profile, plan goal and step metadata, previous outputs if relevant, refinement changes if relevant, evaluation results if relevant, pass_number, phase, TTL remaining, correlation_id, adaptive depth decision inputs) with no null semantic inputs.
- **SC-003**: TTL behavior is correct and fully observable. TTL decrements exactly once per cycle in 100% of cases, TTL behavior at boundaries (1, 0, expiration) is correct in 100% of cases, and TTLExpirationResponse is used for all expiration cases.
- **SC-004**: ExecutionPass consistency is guaranteed across the loop. 100% of ExecutionPass objects have required fields populated before phase entry, required fields populated after phase exit, and invariants maintained for merging execution_results and evaluation_results.
- **SC-005**: Failure handling follows explicit contracts with no new heuristics. 100% of phase transition failures produce structured error logs with error_code, severity, affected_component, and failure_condition, and all failures follow explicit contracts (abort or retry once if retryable).
- **SC-006**: Gate Condition Met: Phase integration is sufficiently stable for Sprint 7 (Prompt Contracts). All phase transitions are deterministic and logged, all context propagation is complete and accurate, and all prompt schemas are aligned with context propagation.

## Out of Scope

To prevent scope creep and maintain focus, the following are explicitly excluded from this sprint:

- **Memory semantics or memory propagation** (deferred to Sprint 8)
- **Prompt consolidation or schema governance** (deferred to Sprint 7)
- **Convergence threshold changes** (deferred to Sprint 9)
- **Validator logic or scoring changes** (deferred to Sprint 10)
- **Recursive planning or subplan discovery** (deferred to Sprint 11)
- **New phases, orchestration engines, or decision-making subsystems** (not in scope)
- **New heuristic frameworks** (not in scope)
- **New fallback or recovery frameworks** (not in scope)
- **Partial-success semantics** (not in scope)
- **New decision or classification engines** (not in scope)
- **Heuristic TTL adjustments** (not in scope)
- **Memory read/write semantics** (deferred to Sprint 8)
- **Historical summarization or narrative heuristics** (not in scope)
- **New logging subsystems** (not in scope - use existing Sprint 5 logging)

## Assumptions

- Phase transitions follow the existing four-phase model (A: Profiling, B: Refinement, C: Execution, D: Adaptive Depth) without modification
- Context propagation refers only to process context (task_profile, plan state, execution state, evaluation state, TTL, correlation_id), not memory subsystem integration
- TTL decrements once per complete cycle (A→B→C→D), not per phase
- ExecutionPass consistency improvements are limited to bug fixes and ensuring required fields are populated; no new fields are added
- Prompt context alignment is limited to ensuring existing prompt schemas are populated correctly; no new prompt schemas are introduced
- Failure handling uses existing models (ExecutionPass, ExecutionHistory, TTLExpirationResponse) without expansion beyond bug fixes
- Logging uses existing Sprint 5 logging schema without modification
- Kernel remains thin; no orchestration logic moves into kernel modules
- All behavior is deterministic for identical inputs

## Dependencies

- **Sprint 5 Observability & Logging**: Phase-aware structured logging, correlation IDs, error logging infrastructure must be complete and functional
- **Existing phase orchestration**: `aeon/orchestration/phases.py` provides phase transition logic that must be stabilized
- **Existing state management**: `aeon/kernel/state.py` provides ExecutionContext, ExecutionPass, ExecutionHistory, TTLExpirationResponse models
- **Existing logging infrastructure**: `aeon/observability/logger.py` provides JSONLLogger with phase entry/exit logging methods

## Notes

- This sprint focuses on stabilization and correctness, not new features. All work must be deterministic and testable.
- Phase transition contracts must be explicit and testable. No flexible heuristics or additional phase types may be introduced.
- Context propagation is process context only (not memory). Memory semantics are deferred to Sprint 8.
- Prompt context alignment prepares for Sprint 7 (Prompt Contracts) but does not introduce prompt consolidation or schema governance.
- TTL behavior must be deterministic and correct at all boundaries. No heuristic adjustments are permitted.
- ExecutionPass consistency ensures execution history is reliable and debuggable.
- All logging must use existing Sprint 5 logging schema. No new logging subsystems may be introduced.
