# Research: Phase Transition Stabilization & Deterministic Context Propagation

**Date**: 2025-12-05  
**Feature**: Phase Transition Stabilization & Deterministic Context Propagation  
**Phase**: 0 - Research

## Overview

This document consolidates research findings and technical decisions for implementing explicit phase transition contracts, deterministic context propagation, TTL boundary behavior fixes, ExecutionPass consistency, and phase boundary logging. All decisions are based on requirements from `spec.md` and constitutional constraints.

## Research Decisions

### Decision 1: Phase Transition Contract Design

**Decision**: Define explicit phase transition contracts as structured data models with input requirements, output guarantees, invariants, and enumerated failure conditions with retryability classification.

**Rationale**:
- Explicit contracts enable testability and verification (FR-001 through FR-005)
- Enumerated failure conditions enable deterministic error handling (FR-006 through FR-011)
- Retryability classification enables correct retry logic (retry once if retryable, abort if non-retryable)
- Structured contracts enable validation before phase transitions
- Contracts are testable and deterministic (constitutional requirement)

**Alternatives Considered**:
- Implicit contracts (documentation only): Rejected - not testable, ambiguous, error-prone
- Flexible heuristics: Rejected - violates spec requirement (FR-005: "MUST NOT invent additional phase types or flexible heuristics")
- Separate contract files: Rejected - adds complexity, contracts should be code-embedded for testability

**Implementation Approach**:
- Define `PhaseTransitionContract` Pydantic model with fields:
  - `transition_name`: Literal["A→B", "B→C", "C→D", "D→A/B"]
  - `required_inputs`: Dict[str, Any] (field name → validation rule)
  - `guaranteed_outputs`: Dict[str, Any] (field name → validation rule)
  - `invariants`: List[str] (invariant descriptions)
  - `failure_conditions`: List[Dict[str, Any]] (condition → retryable boolean)
- Contracts are defined as constants in `orchestration/phases.py`
- Validation functions check contracts before/after phase transitions
- Error codes follow format: `AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>`

**Contract Examples**:
- A→B: Required inputs: `task_profile`, `initial_plan`, `ttl > 0`. Guaranteed outputs: `refined_plan`. Failure conditions: incomplete profile (non-retryable), malformed plan (retryable if JSON parsing error, non-retryable if structural invalidity).
- B→C: Required inputs: `refined_plan` with valid step fragments. Guaranteed outputs: `ExecutionPass` with `execution_results`. Failure conditions: missing steps (non-retryable), invalid plan fragments (retryable if missing required fields, non-retryable if structural invalidity).

### Decision 2: Context Propagation Specification Design

**Decision**: Define unified Context Propagation Specification as structured document with per-phase field requirements (must-have, must-pass-unchanged, may-modify).

**Rationale**:
- Unified specification enables validation that all required fields are present before LLM calls (FR-012 through FR-021)
- Field classification (must-have, must-pass-unchanged, may-modify) enables correct context propagation
- Process context only (not memory) aligns with spec requirement (FR-021)
- Specification is explicit and testable (FR-012)

**Alternatives Considered**:
- Implicit context propagation: Rejected - not testable, error-prone, causes incomplete context
- Memory-based context propagation: Rejected - violates spec requirement (FR-021: "MUST NOT introduce memory propagation")
- Flexible context heuristics: Rejected - violates spec requirement (FR-021: "MUST NOT introduce... narrative heuristics")

**Implementation Approach**:
- Define `ContextPropagationSpecification` Pydantic model with fields:
  - `phase`: Literal["A", "B", "C", "D"]
  - `must_have_fields`: List[str] (required fields before phase entry)
  - `must_pass_unchanged_fields`: List[str] (fields that must be identical across phases)
  - `may_modify_fields`: List[str] (fields that may be produced/modified by this phase)
- Specifications are defined as constants in `orchestration/phases.py`
- Validation functions check context before LLM calls
- Context validation ensures all must-have fields are present and non-null

**Specification Examples**:
- Phase A: Must-have: `request`, `pass_number=0`, `phase="A"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`. Must-pass-unchanged: `correlation_id`, `execution_start_timestamp`. May-modify: None (Phase A produces initial context).
- Phase B: Must-have: `request`, `task_profile`, `initial_plan` goal and step metadata, `pass_number=0`, `phase="B"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`. Must-pass-unchanged: `correlation_id`, `execution_start_timestamp`. May-modify: `refined_plan` (Phase B produces refined plan).

### Decision 3: TTL Boundary Behavior Specification

**Decision**: TTL decrements exactly once per cycle (A→B→C→D), checked before phase entry AND after each LLM call within phase. TTLExpirationResponse used for all expiration cases.

**Rationale**:
- Deterministic TTL behavior enables correct expiration handling (FR-025 through FR-030a)
- Checking TTL before phase entry catches phase_boundary expiration (FR-029)
- Checking TTL after each LLM call catches mid_phase expiration (FR-030)
- TTLExpirationResponse provides structured error mechanism (FR-027)
- No heuristic TTL adjustments (FR-028: "MUST NOT introduce heuristic TTL adjustments")

**Alternatives Considered**:
- TTL decrement per phase: Rejected - violates spec requirement (FR-025: "MUST decrement exactly once per cycle")
- TTL check only at phase boundaries: Rejected - violates spec requirement (FR-030a: "MUST check TTL before phase entry AND after each LLM call")
- Heuristic TTL adjustments: Rejected - violates spec requirement (FR-028: "MUST NOT introduce heuristic TTL adjustments")

**Implementation Approach**:
- TTL decrement occurs once per complete cycle (A→B→C→D) in Phase D completion
- TTL check before phase entry: if TTL=0, generate TTLExpirationResponse with `expiration_type="phase_boundary"`
- TTL check after each LLM call within phase: if TTL=0, generate TTLExpirationResponse with `expiration_type="mid_phase"`
- TTLExpirationResponse contains: `expiration_type`, `phase`, `pass_number`, `ttl_remaining=0`, `plan_state`, `execution_results`, `message`
- TTL behavior at boundaries:
  - TTL=1: Allow cycle to complete, then decrement to 0
  - TTL=0 at phase boundary: Generate TTLExpirationResponse, abort execution
  - TTL=0 mid-phase: Generate TTLExpirationResponse, abort execution

### Decision 4: ExecutionPass Consistency Requirements

**Decision**: Define required fields before/after each phase with invariants for merging execution_results and evaluation_results.

**Rationale**:
- ExecutionPass consistency enables reliable execution history (FR-031 through FR-034)
- Required fields ensure ExecutionPass is complete and consistent
- Invariants ensure correct merging of execution_results and evaluation_results
- Consistency enables debugging and observability

**Alternatives Considered**:
- Flexible ExecutionPass structure: Rejected - causes debugging failures, makes execution history unreliable
- No invariants for merging: Rejected - causes conflicts between execution_results and evaluation_results
- Expand ExecutionPass with new fields: Rejected - violates spec requirement (FR-034: "MUST NOT be expanded with new reasoning or memory fields")

**Implementation Approach**:
- Required fields before phase entry: `pass_number`, `phase`, `plan_state`, `ttl_remaining`, `timing_information.start_time`
- Required fields after phase exit: `execution_results` (if Phase C), `evaluation_results` (if Phase C), `refinement_changes` (if Phase C refinement occurred), `timing_information.end_time`, `timing_information.duration`
- Invariants for merging:
  - `execution_results` contain step outputs and status
  - `evaluation_results` contain convergence assessment and validation report
  - No conflicts between execution_results and evaluation_results
  - Refinement_changes are correctly applied to plan_state
- Validation functions check ExecutionPass consistency before/after phase transitions

### Decision 5: Phase Boundary Logging Design

**Decision**: Extend existing logging infrastructure with phase entry/exit logs, deterministic state snapshots, TTL snapshots, and structured error logs.

**Rationale**:
- Phase boundary logging enables debugging phase transitions (FR-035 through FR-040)
- State snapshots enable trace reconstruction (FR-037)
- TTL snapshots enable TTL behavior verification (FR-038)
- Structured error logs enable error diagnosis (FR-039)
- Uses existing logging schema (FR-040: "MUST use existing logging schema from Sprint 5")

**Alternatives Considered**:
- Separate logging subsystem: Rejected - violates spec requirement (FR-040: "No new logging subsystems may be introduced")
- External monitoring integrations: Rejected - violates spec requirement (FR-040: "No new logging subsystems")
- Async logging: Rejected - violates spec requirement (FR-040: "Logging must remain synchronous and lightweight")

**Implementation Approach**:
- Phase entry log: `phase`, `event="phase_entry"`, `correlation_id`, `pass_number`, `timestamp`
- Phase exit log: `phase`, `event="phase_exit"`, `correlation_id`, `pass_number`, `duration`, `outcome` (success/failure), `timestamp`
- Deterministic state snapshot: `plan_state`, `ttl_remaining`, `phase_state` (before and after transition)
- TTL snapshot: `ttl_before`, `ttl_after`, `ttl_at_boundary`
- Structured error log (if failure): `error_code`, `severity`, `affected_component`, `failure_condition`, `correlation_id`, `phase`, `pass_number`
- All logs use existing JSONLLogger interface from Sprint 5
- Logging remains synchronous and lightweight (<10ms latency target)

### Decision 6: Error Classification Strategy

**Decision**: Classify errors as retryable (transient network errors, JSON parsing errors, missing required fields) or non-retryable (TTL exhaustion, incomplete profile, context propagation failure, structural invalidity).

**Rationale**:
- Error classification enables correct retry logic (FR-006 through FR-011)
- Retryable errors: transient issues that may succeed on retry
- Non-retryable errors: permanent issues that will not succeed on retry
- Classification is explicit in phase transition contracts (FR-006)

**Alternatives Considered**:
- Retry all errors: Rejected - causes infinite loops for permanent failures
- Never retry: Rejected - causes failures for transient issues that could succeed on retry
- Heuristic retry logic: Rejected - violates spec requirement (FR-007: "MUST NOT introduce new fallback or recovery frameworks")

**Implementation Approach**:
- Retryable conditions:
  - Transient network errors (LLM API rate limits, network timeouts)
  - JSON parsing errors (malformed JSON that supervisor can repair)
  - Missing required fields (fields that can be added by supervisor)
- Non-retryable conditions:
  - TTL exhaustion (permanent, cannot be retried)
  - Incomplete profile (permanent, cannot be retried)
  - Context propagation failure (permanent, cannot be retried)
  - Structural invalidity (permanent, cannot be retried)
- Retry logic: retry exactly once if retryable, abort immediately if non-retryable
- Error codes follow format: `AEON.PHASE_TRANSITION.<TRANSITION>.<CODE>`

### Decision 7: LLM Call Context Requirements

**Decision**: Define minimal context requirements per phase with validation that all required fields are present and non-null before LLM calls.

**Rationale**:
- Complete context enables correct LLM reasoning (FR-012 through FR-021)
- Minimal context per phase reduces prompt size and improves performance
- Context validation prevents null semantic inputs (FR-023)
- Validation enables debugging incomplete context issues

**Alternatives Considered**:
- Maximum context (all fields always): Rejected - increases prompt size, reduces performance, violates minimal context requirement
- No context validation: Rejected - causes null semantic inputs, reasoning failures
- Flexible context heuristics: Rejected - violates spec requirement (FR-021: "MUST NOT introduce... narrative heuristics")

**Implementation Approach**:
- Phase A context: `request`, `pass_number=0`, `phase="A"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`
- Phase B context: `request`, `task_profile`, `initial_plan` goal and step metadata, `pass_number=0`, `phase="B"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`
- Phase C context (execution): `request`, `task_profile`, `refined_plan` goal and step metadata, `pass_number`, `phase="C"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`, previous outputs (if relevant), refinement changes (if relevant)
- Phase C context (evaluation): `request`, `task_profile`, current plan state, `execution_results`, `pass_number`, `phase="C"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`
- Phase C context (refinement): `request`, `task_profile`, current plan state, `execution_results`, `evaluation_results` (convergence assessment, validation issues), `pass_number`, `phase="C"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`, previous outputs
- Phase D context: `request`, `task_profile`, `evaluation_results`, plan state, `pass_number`, `phase="D"`, `ttl_remaining`, `correlation_id`, `execution_start_timestamp`, adaptive depth decision inputs
- Context validation: check all required fields are present and non-null before LLM calls
- Context validation errors are non-retryable (context propagation failure)

### Decision 8: Prompt Schema Alignment Strategy

**Decision**: Review all prompt schemas, remove unused keys or ensure orchestrator/phases populate them. Ensure no prompt contains null semantic inputs.

**Rationale**:
- Prompt schema alignment prevents null semantic inputs (FR-022 through FR-024)
- Unused keys cause confusion and maintenance issues
- Null semantic inputs cause LLM reasoning failures
- Alignment prepares for Sprint 7 (Prompt Contracts)

**Alternatives Considered**:
- Keep unused keys: Rejected - causes confusion, maintenance issues
- Remove all unused keys: Rejected - may break future features, better to document as optional/future use
- No schema review: Rejected - causes null semantic inputs, reasoning failures

**Implementation Approach**:
- Review all prompt schemas in `plan/prompts.py` and orchestration modules
- For each key in schema:
  - If key is required for reasoning: ensure orchestrator/phases populate it
  - If key is unused: remove it or document as optional/future use
  - If key is never populated: remove it or update orchestrator/phases to populate it
- Validation: ensure no prompt contains null semantic inputs
- Schema alignment is manual review process (no automated tooling required)

## Summary

All research decisions align with spec requirements and constitutional constraints. Phase transition contracts, context propagation specifications, TTL boundary behavior, ExecutionPass consistency, phase boundary logging, error classification, LLM call context requirements, and prompt schema alignment are all designed to be explicit, testable, and deterministic. No new heuristic frameworks, fallback strategies, or architectural subsystems are introduced. All improvements remain outside the kernel and use existing models without expansion beyond bug fixes.

