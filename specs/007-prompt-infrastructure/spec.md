# Feature Specification: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Feature Branch**: `007-prompt-infrastructure`  
**Created**: 2025-12-07  
**Status**: Draft  
**Input**: User description: "Sprint 7 — Prompt Infrastructure, Prompt Contracts & Phase E Synthesis: Establish a unified, contract-driven prompt subsystem and implement Phase E (Answer Synthesis) to complete the conceptual A→B→C→D→E reasoning loop. This sprint eliminates all inline prompts, enforces schema-backed prompt contracts, and introduces minimal answer synthesis that integrates correctly with Aeon's actual execution flow."

## Clarifications

### Session 2025-12-07

- Q: Where should the prompt registry be located within the codebase structure? → A: New top-level module `aeon/prompts/registry.py` (alongside `aeon/kernel/`, `aeon/supervisor/`, etc.)
- Q: What template mechanism should be used for prompt rendering with input data? → A: Python f-strings with Pydantic model field access (e.g., `f"Goal: {input.goal}"`)
- Q: Where exactly should Phase E be integrated in the codebase? → A: In engine.py main execution loop (after C-loop completes in `run_multipass`, before engine returns final result)
- Q: How should prompt definitions and their Pydantic contracts be organized in the registry file? → A: Single file `registry.py` containing both prompt definitions and their input/output Pydantic models together
- Q: How should prompt contract versioning be handled for backward compatibility? → A: No explicit versioning in Sprint 7; contracts are mutable and changes apply immediately (acceptable for <100 prompts)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Centralized Prompt Management (Priority: P1)

As a developer maintaining Aeon, I can access all system prompts from a single registry, ensuring consistency, versioning, and easier maintenance across the codebase.

**Why this priority**: This is the foundational capability that enables all other prompt-related work. Without centralized prompt management, the system cannot enforce contracts, track changes, or maintain consistency. It represents the entry point for all prompt-related operations and is required before implementing contracts or Phase E.

**Independent Test**: Can be fully tested by querying the prompt registry for all known prompt identifiers and verifying that each prompt can be retrieved with its associated input/output schemas. The test delivers value by proving the system can locate and access all prompts from a single source, eliminating scattered inline prompt strings.

**Acceptance Scenarios**:

1. **Given** a prompt registry exists, **When** a developer queries for a prompt by identifier, **Then** the registry returns the complete prompt definition including input schema, output schema (if applicable), and rendering utilities
2. **Given** all inline prompts have been extracted, **When** a developer searches the codebase for prompt strings, **Then** no inline prompt strings remain outside the registry
3. **Given** a new prompt needs to be added, **When** a developer registers it in the prompt registry, **Then** it becomes available system-wide with proper schema definitions
4. **Given** a prompt is used in multiple locations, **When** the prompt definition is updated in the registry, **Then** all locations using that prompt automatically receive the updated version

---

### User Story 2 - Schema-Backed Prompt Contracts (Priority: P2)

As a developer using Aeon's prompt system, I can rely on typed input and output contracts for all prompts, ensuring data validation and preventing runtime errors from malformed prompt inputs or outputs.

**Why this priority**: Schema-backed contracts provide type safety and validation, preventing errors before they reach the LLM. This reduces debugging time and improves system reliability. However, prompt consolidation (P1) must be complete before contracts can be enforced.

**Independent Test**: Can be fully tested by creating a prompt contract with defined input and output models, then verifying that invalid inputs are rejected and valid inputs produce correctly structured outputs. The test delivers value by proving the system can validate prompt data at compile-time and runtime, catching errors early.

**Acceptance Scenarios**:

1. **Given** a prompt has a defined input model, **When** a developer attempts to use the prompt with invalid input data, **Then** the system rejects the input with clear validation errors before the prompt is rendered
2. **Given** a prompt produces JSON output, **When** the LLM returns a response, **Then** the system validates the response against the prompt's output model and rejects malformed responses
3. **Given** a prompt contract is defined, **When** a developer uses the prompt, **Then** they receive type hints and autocomplete support for input fields
4. **Given** all prompts have contracts, **When** the system validates prompt usage, **Then** every prompt identifier has a corresponding contract definition

---

### User Story 3 - Final Answer Synthesis (Priority: P1)

As a user submitting requests to Aeon, I receive a synthesized final answer that consolidates all execution results, plan state, and convergence information into a coherent response, even when execution terminates early or encounters issues.

**Why this priority**: This completes the reasoning loop and provides users with usable output. Without answer synthesis, users receive raw execution data without interpretation. This is essential for delivering value from the orchestration system.

**Independent Test**: Can be fully tested by executing a request through the full A→B→C→D cycle, then verifying that Phase E produces a structured final answer containing the synthesized response, confidence indicators, and metadata about the execution. The test delivers value by proving users receive coherent, actionable answers rather than raw execution traces.

**Acceptance Scenarios**:

1. **Given** execution completes through the C-loop (with or without Phase D on the final pass), **When** Phase E executes, **Then** it produces a final answer containing synthesized text, confidence level, and execution metadata
2. **Given** execution terminates due to TTL expiration, **When** Phase E executes, **Then** it produces a final answer indicating TTL exhaustion while still synthesizing available results
3. **Given** execution completes successfully with convergence, **When** Phase E executes, **Then** it produces a final answer with high confidence and references to the steps that contributed to the solution
4. **Given** execution encounters errors during execution passes, **When** Phase E executes, **Then** it produces a final answer that acknowledges errors while synthesizing partial results where possible
5. **Given** Phase E receives execution state, **When** it synthesizes the answer, **Then** it uses all available context including plan state, execution results, convergence assessment, and task profile information

---

### Edge Cases

- What happens when a prompt registry lookup fails for a required prompt? (Answer: System raises an error indicating the prompt is missing from the registry)
- How does the system handle prompts that have no output model (non-JSON prompts)? (Answer: Output model is optional; prompts without output models skip JSON validation)
- What happens when Phase E receives incomplete execution state (e.g., missing convergence assessment)? (Answer: Phase E produces a final answer with available data, marking missing fields as unavailable in metadata)
- How does the system handle prompt rendering when input data is missing required fields? (Answer: Validation fails before rendering, returning clear error messages about missing fields)
- What happens when Phase E synthesis fails (LLM error during synthesis)? (Answer: System produces a degraded final answer with available raw data and error indication)
- How does the system handle backward compatibility when prompt contracts change? (Answer: Contracts are mutable; changes apply immediately to all usages. No explicit versioning in Sprint 7; acceptable for <100 prompts. Versioning can be added later if needed.)
- What happens when multiple prompts reference the same input field with different validation rules? (Answer: Each prompt contract defines its own input model; no shared validation conflicts)
- How does Phase E handle synthesis when execution results are empty or malformed? (Answer: Phase E produces a final answer indicating insufficient data, with available partial information in metadata)

## Requirements *(mandatory)*

### Functional Requirements

#### Prompt Consolidation & Registry (P1)

- **FR-001**: System MUST maintain a centralized prompt registry containing all system prompts
- **FR-002**: System MUST provide a unique identifier (PromptId) for each prompt in the registry
- **FR-003**: System MUST support retrieving prompts by identifier from the registry
- **FR-004**: System MUST remove all inline prompt strings from kernel, supervisor, phases, and tools modules
- **FR-005**: System MUST extract prompts from validation/semantic.py, convergence/engine.py, adaptive/heuristics.py, plan/recursive.py (contains subplan + refinement prompts), kernel/executor.py (contains execution reasoning prompt), supervisor/repair.py, and plan/prompts.py.
- **FR-006**: System MUST locate the prompt registry outside the kernel (per Constitution Principle II) in a new top-level module `aeon/prompts/registry.py`
- **FR-007**: System MUST support prompt rendering utilities that populate prompt templates with input data using Python f-strings with Pydantic model field access
- **FR-008**: System MUST keep all prompt definitions and their Pydantic input/output models in a single file `aeon/prompts/registry.py` unless prompt count exceeds approximately 100 prompts

#### Prompt Contracts (P2)

- **FR-009**: System MUST define a typed input model (Pydantic) for every prompt in the registry
- **FR-010**: System MUST define a typed output model (Pydantic) for prompts that produce JSON-structured responses
- **FR-011**: System MUST make output models optional for prompts that do not produce structured JSON
- **FR-012**: System MUST validate prompt input data against the input model before prompt rendering
- **FR-013**: System MUST validate prompt output data against the output model (when defined) after LLM response
- **FR-014**: System MUST use Pydantic API surface compatible with both v1 and v2
- **FR-015**: System MUST keep contract constraints minimal and structural (not business-logic validation)
- **FR-016**: System MUST enforce the Location Invariant: no inline prompts exist outside the registry
- **FR-017**: System MUST enforce the Schema Invariant: every prompt has a typed input model; JSON-producing prompts must have typed output models
- **FR-018**: System MUST enforce the Registration Invariant: every PromptId has a corresponding entry in PromptRegistry

#### Phase E (Answer Synthesis) (P3)

- **FR-019**: System MUST implement Phase E as a synthesis module that runs after the Phase C loop terminates
- **FR-020**: System MUST invoke Phase E at the exit of the C-loop in `OrchestrationEngine.run_multipass()` (after `_execute_phase_c_loop` returns, before building final execution result), not after Phase D, because D may not run on the final pass
- **FR-021**: System MUST pass complete final state to Phase E including: request, execution results, plan state, convergence assessment, execution passes, semantic validation, task profile, correlation ID, execution start timestamp, convergence status, total passes, total refinements, and TTL remaining
- **FR-022**: System MUST define PhaseEInput model with all required fields from final execution state
- **FR-023**: System MUST define FinalAnswer model containing: answer_text, confidence (optional), used_step_ids (optional), notes (optional), ttl_exhausted (optional), and metadata dictionary
- **FR-024**: System MUST always produce a final_answer even in degraded conditions (errors, TTL expiration, incomplete data)
- **FR-025**: System MUST register Phase E in the phases system
- **FR-026**: System MUST attach final_answer to the execution result returned by the engine
- **FR-027**: System MUST create synthesis prompts (ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER) in the prompt registry
- **FR-028**: System MUST ensure Phase E does not perform presentation-layer work (Layer 2/3 concerns are out of scope)

#### Integration & Testing

- **FR-029**: System MUST add Level 1 prompt tests validating: model instantiation from sample data, prompt rendering (no missing fields), output-model loading for JSON prompts, and invariant enforcement (location, schema, registration)
- **FR-030**: System MUST ensure kernel receives no new business logic except wiring for Phase E invocation
- **FR-031**: System MUST maintain kernel minimalism (Principle I) - only prompt removal and Phase E wiring allowed in kernel
- **FR-032**: System MUST ensure prompt logic resides outside the kernel per Constitution requirements

### Key Entities *(include if feature involves data)*

- **PromptRegistry**: Central repository containing all prompt definitions, accessible by PromptId. Contains PromptDefinition objects with input/output models and rendering utilities.

- **PromptId**: Enumeration of all unique prompt identifiers used throughout the system. Each identifier maps to exactly one PromptDefinition.

- **PromptDefinition**: Object containing a prompt's template, input model (required), output model (optional for non-JSON prompts), and rendering function. Defines the contract for prompt usage.

- **PromptInput**: Base class for all prompt input models. Each prompt defines its own input model extending this base, specifying required fields and validation rules.

- **PromptOutput**: Base class for all prompt output models. Only JSON-producing prompts define output models extending this base.

- **PhaseEInput**: Input model for Phase E synthesis, containing: request, execution_results, plan_state, convergence_assessment, execution_passes (optional), semantic_validation (optional), task_profile (optional), correlation_id, execution_start_timestamp, convergence_status, total_passes, total_refinements, ttl_remaining.

- **FinalAnswer**: Output model for Phase E synthesis, containing: answer_text (required), confidence (optional float), used_step_ids (optional list), notes (optional string), ttl_exhausted (optional boolean), metadata (dictionary).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of inline prompts are removed from kernel, supervisor, phases, and tools modules (verified by automated search with zero matches)
- **SC-002**: 100% of prompts have typed input models defined in the registry (every PromptId has corresponding input model)
- **SC-003**: 100% of JSON-producing prompts have typed output models defined in the registry (verified by checking all prompts that return structured data)
- **SC-004**: All three invariants pass automated tests: Location Invariant (no inline prompts), Schema Invariant (all prompts have input models), Registration Invariant (all PromptIds have registry entries)
- **SC-005**: Phase E successfully produces final_answer for 100% of execution scenarios including: successful convergence, TTL expiration, partial execution, and error conditions
- **SC-006**: All Level 1 prompt tests pass: input model validation, prompt rendering checks, output model validation for JSON prompts, and invariant tests
- **SC-007**: Kernel code changes are limited to prompt removal and Phase E wiring only (no new business logic added to kernel)
- **SC-008**: Phase E integration completes within the C-loop exit point, correctly receiving final execution state regardless of whether Phase D ran on the final pass

## Assumptions

- Pydantic v1/v2 compatibility can be achieved using a common API surface without requiring separate implementations
- Prompt count will remain under 100, allowing single-file registry implementation
- Existing ModelClient abstraction can be used for Phase E LLM calls without modification
- Phase E synthesis prompts can be defined using the same contract system as other prompts
- Kernel wiring for Phase E invocation is minimal and does not violate kernel LOC limits
- All prompts can be extracted from their current locations without breaking existing functionality during migration
- Prompt rendering utilities can handle all current prompt template patterns (f-strings, concatenation, etc.)

## Dependencies

- P1 (Prompt Consolidation) must complete before P2 (Prompt Contracts) can begin
- P2 (Prompt Contracts) must complete before P3 (Phase E) can begin, as Phase E prompts must use the contract system
- No memory subsystem dependencies required for this sprint
- Existing ModelClient/LLMAdapter abstraction is sufficient (no modifications needed)
- Constitution compliance must be maintained throughout (kernel minimalism, separation of concerns)

## Out of Scope

- A/B testing of prompts
- Memory retrieval/write for prompts
- Prompt optimization or performance tuning
- Layer 2 (presentation) concerns
- Layer 3 (output governance) concerns
- Golden Path automation
- Multi-model routing
- Reasoning-quality evaluation beyond basic synthesis
- Prompt versioning beyond basic registry structure
- Prompt analytics or usage tracking
