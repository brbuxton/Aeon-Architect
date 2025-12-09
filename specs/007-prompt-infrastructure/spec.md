# Feature Specification: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Feature Branch**: `007-prompt-infrastructure`  
**Created**: 2025-12-07  
**Status**: Draft  
**Input**: User description: "Sprint 7 — Prompt Infrastructure, Prompt Contracts & Phase E Synthesis: Establish a unified, contract-driven prompt subsystem and implement Phase E (Answer Synthesis) to complete the conceptual A→B→C→D→E reasoning loop. This sprint eliminates all inline prompts, enforces schema-backed prompt contracts, and introduces minimal answer synthesis that integrates correctly with Aeon's actual execution flow."

## Clarifications

### Session 2025-12-07

- Q: Where should the prompt registry be located within the codebase structure? → A: New top-level module `aeon/prompts/registry.py` (alongside `aeon/kernel/`, `aeon/supervisor/`, etc.)
- Q: What template mechanism should be used for prompt rendering with input data? → A: Python f-strings with Pydantic model field access (e.g., `f"Goal: {input.goal}"`)
- Q: Where exactly should Phase E be integrated in the codebase? → A: Phase E is a first-class phase in `aeon/orchestration/phases.py`, invoked from `OrchestrationEngine.run_multipass()` at the C-loop exit point (after `_execute_phase_c_loop` returns, before building final execution result). Phase E logic MUST NOT be implemented as a helper function in OrchestrationEngine.
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

### User Story 2 - Schema-Backed Prompt Contracts with JSON Extraction (Priority: P2)

As a developer using Aeon's prompt system, I can rely on typed input and output contracts for all prompts, with unified JSON extraction behavior that handles LLM responses in any format (dictionary with "text" key, markdown code blocks, embedded JSON, or raw JSON strings), ensuring data validation and preventing runtime errors from malformed prompt inputs or outputs.

**Why this priority**: Schema-backed contracts provide type safety and validation, preventing errors before they reach the LLM. Unified JSON extraction ensures consistent behavior regardless of LLM response format, reducing debugging time and improving system reliability. However, prompt consolidation (P1) must be complete before contracts can be enforced.

**Independent Test**: Can be fully tested by creating a prompt contract with defined input and output models, then verifying that: (1) invalid inputs are rejected, (2) valid inputs produce correctly structured outputs, and (3) JSON extraction works correctly for all response formats (dictionary with "text" key, markdown code blocks, embedded JSON, raw JSON). The test delivers value by proving the system can validate prompt data at compile-time and runtime, catch errors early, and handle LLM response format variations consistently.

**Acceptance Scenarios**:

1. **Given** a prompt has a defined input model, **When** a developer attempts to use the prompt with invalid input data, **Then** the system rejects the input with clear validation errors before the prompt is rendered
2. **Given** a prompt produces JSON output, **When** the LLM returns a dictionary response containing a "text" key with JSON content, **Then** the system extracts the value from the "text" key and validates it against the prompt's output model
3. **Given** a prompt produces JSON output, **When** the LLM returns a response with JSON wrapped in markdown code blocks (```json ... ``` or ``` ... ```), **Then** the system extracts JSON from the first complete code block and validates it against the prompt's output model
4. **Given** a prompt produces JSON output, **When** the LLM returns a response with JSON embedded in free text, **Then** the system extracts the first complete JSON object using brace matching and validates it against the prompt's output model
5. **Given** a prompt produces JSON output, **When** the LLM returns a raw JSON string response, **Then** the system parses the JSON directly and validates it against the prompt's output model
6. **Given** an LLM response contains no extractable JSON, **When** the system attempts to validate the output, **Then** it raises a clear `JSONExtractionError` exception rather than attempting recovery or supervisor repair
7. **Given** a prompt contract is defined, **When** a developer uses the prompt, **Then** they receive type hints and autocomplete support for input fields
8. **Given** all prompts have contracts, **When** the system validates prompt usage, **Then** every prompt identifier has a corresponding contract definition
9. **Given** JSON extraction succeeds but validation against the output model fails, **When** the system processes the response, **Then** it raises `ValidationError` (not `JSONExtractionError`) with clear messages about which fields are invalid

---

### User Story 3 - Final Answer Synthesis (Priority: P1)

As a user submitting requests to Aeon, I receive a synthesized final answer that consolidates all execution results, plan state, and convergence information into a coherent response, even when execution terminates early or encounters issues.

**Why this priority**: This completes the reasoning loop and provides users with usable output. Without answer synthesis, users receive raw execution data without interpretation. This is essential for delivering value from the orchestration system.

**Independent Test**: Can be fully tested by executing requests through three distinct scenarios: (1) successful synthesis with complete data, (2) TTL expiration scenario, and (3) incomplete data scenario. The test delivers value by proving users receive coherent, actionable answers rather than raw execution traces.

**Acceptance Scenarios**:

1. **Given** execution completes successfully with convergence, **When** Phase E executes, **Then** it produces a final answer containing synthesized text, confidence level, and execution metadata
2. **Given** execution terminates due to TTL expiration, **When** Phase E executes, **Then** it produces a final answer indicating TTL exhaustion while still synthesizing available results with degraded confidence
3. **Given** execution state is incomplete (missing plan_state, execution_results, task_profile, or execution_passes), **When** Phase E executes, **Then** it produces a degraded final answer using only available data, with metadata indicating which fields were missing
4. **Given** execution completes with zero passes (no execution passes occurred), **When** Phase E executes, **Then** it still produces a final answer indicating that no execution occurred, synthesizing from request and any available plan state

---

### Edge Cases

- What happens when a prompt registry lookup fails for a required prompt? (Answer: System raises an error indicating the prompt is missing from the registry)
- How does the system handle prompts that have no output model (non-JSON prompts)? (Answer: Output model is optional; prompts without output models skip JSON validation)
- What happens when Phase E receives incomplete execution state (e.g., missing convergence assessment, plan_state, execution_results, task_profile, or execution_passes)? (Answer: Phase E MUST still execute and produce a degraded final answer using available data, with metadata indicating which required or optional fields were missing. Phase E MUST NOT raise exceptions for missing upstream artifacts.)
- How does the system handle prompt rendering when input data is missing required fields? (Answer: Validation fails before rendering, returning clear error messages about missing fields)
**JSON Extraction Edge Cases**:

- How does the system handle LLM responses that wrap JSON in a "text" key (e.g., `{"text": "{\"key\": \"value\"}"}`)? (Answer: `validate_output()` extracts the value from the "text" key and processes it as the candidate JSON string. The extraction pipeline then processes this string to extract the nested JSON)
- How does the system handle LLM responses that wrap JSON in markdown code blocks (e.g., ```json ... ``` or ``` ... ```)? (Answer: `validate_output()` extracts JSON from the first markdown code block found. Code blocks are identified by triple backticks followed by optional language identifier, and content is extracted between matching closing triple backticks)
- How does the system handle LLM responses with JSON embedded in free text? (Answer: `validate_output()` uses brace matching to identify and extract the first complete JSON object. The system handles nested JSON structures and selects the first complete JSON object with balanced braces)
- What happens when multiple JSON objects are present in the response? (Answer: System extracts the first complete JSON object found. Subsequent JSON objects are ignored)
- What happens when no valid JSON can be extracted from the response? (Answer: System raises `JSONExtractionError` exception with context about which extraction methods were attempted. No supervisor repair or recovery attempts are made)
- How does the system handle empty "text" key values in dictionary responses? (Answer: System treats empty string as candidate JSON and attempts extraction/parsing through all extraction methods. If no valid JSON is found, raises `JSONExtractionError`)
- How does the system handle nested JSON in "text" key (e.g., `{"text": "{\"key\": \"value\"}"}`)? (Answer: System extracts the "text" value as a string, then processes it through the extraction pipeline (markdown code blocks, embedded JSON, direct parsing) to find the nested JSON)
- What happens when a dictionary response is missing the "text" key? (Answer: System raises `JSONExtractionError` indicating that dictionary responses must contain a "text" key)
- What happens when the "text" key contains a non-string value? (Answer: System raises `JSONExtractionError` indicating that the "text" key value must be a string)
- How does the system handle markdown code blocks with language identifiers other than "json"? (Answer: System extracts content from any code block (```json ... ``` or ``` ... ```), regardless of language identifier)
- What happens when a markdown code block is not properly closed (missing closing triple backticks)? (Answer: System treats the unclosed code block as invalid and proceeds to next extraction method. If all methods fail, raises `JSONExtractionError`)
- How does the system handle JSON with trailing text after the closing brace? (Answer: System extracts the first complete JSON object and ignores trailing text. The extracted JSON is validated against the output model)
- What happens when JSON extraction succeeds but validation against the output model fails? (Answer: System raises `ValidationError` (not `JSONExtractionError`) with Pydantic validation error messages indicating which fields are invalid)
- How does the system handle responses containing both markdown code blocks and embedded JSON? (Answer: System prioritizes extraction methods in order: (1) dictionary "text" key, (2) markdown code blocks, (3) embedded JSON, (4) direct parsing. First successful extraction is used)
- What happens when multiple markdown code blocks are present? (Answer: System extracts JSON from the first complete markdown code block found)
- What happens when Phase E synthesis fails (LLM error during synthesis)? (Answer: System produces a degraded final answer with available raw data and error indication in metadata. The degraded answer MUST contain at minimum: answer_text (explaining the error), ttl_exhausted (if applicable), and metadata indicating the synthesis failure)
- How does the system handle backward compatibility when prompt contracts change? (Answer: Contracts are mutable; changes apply immediately to all usages. No explicit versioning in Sprint 7; acceptable for <100 prompts. Versioning can be added later if needed.)
- What happens when multiple prompts reference the same input field with different validation rules? (Answer: Each prompt contract defines its own input model; no shared validation conflicts)
- How does Phase E handle synthesis when execution results are empty or malformed? (Answer: Phase E produces a degraded final answer indicating insufficient data, with available partial information in metadata. The answer_text MUST explain that data is insufficient.)
- What happens when execution completes with zero passes? (Answer: Phase E MUST still execute and produce a final answer indicating that no execution passes occurred, synthesizing from the original request and any available plan state)

## Requirements *(mandatory)*

### Implementation Restrictions

**CRITICAL**: Cursor (or any AI assistant implementing this specification) MUST NOT infer requirements, data structures, or implementation details that are not explicitly defined in this specification. If clarification is needed on any aspect of implementation, Cursor MUST request clarification rather than inferring a solution.

**CRITICAL**: Cursor MUST NOT infer internal engine structures (e.g., OrchestrationEngine internal state, execution pass structures, phase transition mechanics) that are not explicitly documented in this specification. Only the following are explicitly defined:
- PhaseEInput model schema (defined in Key Entities section)
- FinalAnswer model schema (defined in Key Entities section)
- Phase E invocation point: C-loop exit in `OrchestrationEngine.run_multipass()` (after `_execute_phase_c_loop` returns)
- Phase E function signature: `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer`
- Phase E location: `aeon/orchestration/phases.py` (first-class phase, not a helper function)

Any other internal structures, state management, or engine internals MUST be obtained from existing codebase inspection or explicit documentation, NOT inferred.

### Functional Requirements

#### Prompt Consolidation & Registry (P1)

- **FR-001**: System MUST maintain a centralized prompt registry containing all system prompts
- **FR-002**: System MUST provide a unique identifier (PromptId) for each prompt in the registry
- **FR-003**: System MUST support retrieving prompts by identifier from the registry
- **FR-004**: System MUST remove all inline prompt strings from kernel, supervisor, phases, and tools modules
- **FR-005**: System MUST extract prompts from validation/semantic.py, convergence/engine.py, adaptive/heuristics.py, plan/recursive.py (contains subplan + refinement prompts), kernel/executor.py (contains execution reasoning prompt), supervisor/repair.py, and plan/prompts.py. The PromptId enum MUST include all extracted prompts including: PLAN_GENERATION_SYSTEM, PLAN_GENERATION_USER, REASONING_STEP_SYSTEM, REASONING_STEP_USER, VALIDATION_SEMANTIC_SYSTEM, VALIDATION_SEMANTIC_USER, CONVERGENCE_ASSESSMENT_SYSTEM, CONVERGENCE_ASSESSMENT_USER, TASKPROFILE_INFERENCE_SYSTEM, TASKPROFILE_INFERENCE_USER, TASKPROFILE_UPDATE_SYSTEM, TASKPROFILE_UPDATE_USER, RECURSIVE_PLAN_GENERATION_USER, RECURSIVE_SUBPLAN_GENERATION_USER, RECURSIVE_REFINEMENT_SYSTEM, RECURSIVE_REFINEMENT_USER, SUPERVISOR_REPAIR_SYSTEM, SUPERVISOR_REPAIR_JSON_USER, SUPERVISOR_REPAIR_TOOLCALL_USER, SUPERVISOR_REPAIR_PLAN_USER, SUPERVISOR_REPAIR_MISSINGTOOL_USER, ANSWER_SYNTHESIS_SYSTEM, ANSWER_SYNTHESIS_USER.
- **FR-005A**: System MUST implement automated verification (script or test) that searches the codebase for inline prompt string patterns and confirms zero matches outside the prompt registry, satisfying SC-001
- **FR-006**: System MUST locate the prompt registry outside the kernel (per Constitution Principle II) in a new top-level module `aeon/prompts/registry.py`
- **FR-007**: System MUST support prompt rendering utilities that populate prompt templates with input data using Python f-strings with Pydantic model field access
- **FR-008**: System MUST keep all prompt definitions and their Pydantic input/output models in a single file `aeon/prompts/registry.py` unless prompt count exceeds approximately 100 prompts

##### FR-005 JSON vs. Free Form output clarification
For each PromptId listed in FR-005, the specification MUST identify whether the
prompt produces JSON output or free-form natural language output.

Prompts that produce JSON MUST define a corresponding Pydantic output model
(see FR-010). Prompts that do not produce JSON MUST NOT define an output model
(see FR-011).

JSON-producing prompts are:

- PLAN_GENERATION_SYSTEM
- PLAN_GENERATION_USER
- RECURSIVE_SUBPLAN_GENERATION_USER
- RECURSIVE_REFINEMENT_SYSTEM
- RECURSIVE_REFINEMENT_USER
- CONVERGENCE_ASSESSMENT_SYSTEM
- CONVERGENCE_ASSESSMENT_USER
- SUPERVISOR_REPAIR_JSON_USER
- ANSWER_SYNTHESIS_SYSTEM
- ANSWER_SYNTHESIS_USER

All other prompts produce free-form natural language output.

#### Prompt Contracts (P2)

- **FR-009**: System MUST define a typed input model (Pydantic) for every prompt in the registry
- **FR-010**: System MUST define a typed output model (Pydantic) for prompts that produce JSON-structured responses
- **FR-011**: System MUST make output models optional for prompts that do not produce structured JSON
- **FR-012**: System MUST validate prompt input data against the input model before prompt rendering
- **FR-013**: System MUST validate prompt output data against the output model (when defined) after LLM response

#### JSON Extraction and Normalization (P2)

**Method Contract for `validate_output()`**:

- **FR-013A**: System MUST implement JSON extraction and normalization in `validate_output()` method to handle LLM responses that wrap JSON in various formats before validation
- **FR-013B**: System MUST update `validate_output()` method signature to accept `Union[str, Dict[str, Any]]` for `llm_response` parameter, allowing both raw string responses and dictionary responses containing a "text" key
- **FR-013C**: When `llm_response` is a dictionary, System MUST extract the value from the "text" key as the candidate JSON string before attempting extraction. If the "text" key is missing or its value is not a string, System MUST raise `JSONExtractionError`
- **FR-013D**: System MUST extract JSON from markdown code blocks of the form ```json ... ``` or ``` ... ```, selecting the first complete JSON object found. The system MUST identify code blocks by the presence of triple backticks followed by optional language identifier and extract content between matching closing triple backticks
- **FR-013E**: System MUST extract JSON from raw text containing embedded JSON by identifying the first complete JSON object using brace matching. The system MUST handle nested JSON structures and MUST select the first complete JSON object (balanced braces) found in the text
- **FR-013F**: System MUST attempt to parse the entire response as JSON if no extraction method succeeds (fallback to direct parsing). This fallback MUST occur after all extraction methods (dictionary "text" key, markdown code blocks, embedded JSON) have been attempted
- **FR-013G**: System MUST raise a domain-specific `JSONExtractionError` exception if no valid JSON can be extracted from the response, rather than attempting supervisor repair or other recovery mechanisms. The exception MUST include context about which extraction methods were attempted
- **FR-013H**: System MUST centralize all JSON extraction logic within the prompt registry's `validate_output()` method, ensuring no duplicate extraction logic remains in other modules for new prompt-contract-based output validation. All new prompt-contract-based output validation MUST rely exclusively on the registry's extraction rules
- **FR-013I**: System MUST NOT modify existing custom parsing logic in other modules (parser, repair, semantic, engine, recursive, heuristics) during this sprint. Migration of existing modules to use the new extraction logic is explicitly out of scope
- **FR-013J**: After successful JSON extraction, System MUST validate the extracted JSON against the prompt's output model using Pydantic validation. If validation fails, System MUST raise `ValidationError` (not `JSONExtractionError`)
- **FR-013K**: System MUST handle edge cases: empty "text" key values (treat as empty string candidate), multiple JSON objects in response (select first complete object), trailing text after JSON (ignore trailing text), and nested JSON in "text" key (extract "text" value then process through extraction pipeline)
- **FR-013L**: The specification MUST define method-level expectations, error cases, and success conditions for JSON extraction, but MUST NOT prescribe implementation details such as algorithms, helper functions, or refactoring strategies
- **FR-014**: System MUST use Pydantic API surface compatible with both v1 and v2
- **FR-014A**: System MUST include automated tests that validate Pydantic v1 and v2 compatibility by instantiating prompt input/output models and performing validation operations under both versions
- **FR-015**: System MUST keep contract constraints minimal and structural (not business-logic validation)
- **FR-016**: System MUST enforce the Location Invariant: no inline prompts exist outside the registry
- **FR-017**: System MUST enforce the Schema Invariant: every prompt has a typed input model; JSON-producing prompts must have typed output models
- **FR-018**: System MUST enforce the Registration Invariant: every PromptId has a corresponding entry in PromptRegistry

#### Phase E (Answer Synthesis) (P3)

**Phase E Architecture**:

- **FR-019**: System MUST implement Phase E as a first-class orchestration phase in `aeon/orchestration/phases.py` (not as a helper function in OrchestrationEngine)
- **FR-020**: System MUST invoke Phase E at the exit of the C-loop in `OrchestrationEngine.run_multipass()` (after `_execute_phase_c_loop` returns, before building final execution result), not after Phase D, because D may not run on the final pass
- **FR-021**: Phase E function signature MUST be: `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer` in `aeon/orchestration/phases.py`
- **FR-022**: Phase E MUST NOT move logic into the kernel or OrchestrationEngine except for invocation wiring (building PhaseEInput and calling execute_phase_e)
- **FR-023**: No helper functions for Phase E may be added to OrchestrationEngine
- **FR-024**: Phase E MUST execute unconditionally after C-loop terminates, regardless of: number of passes (including zero passes), completion status of upstream phases, TTL expiration, errors, or missing/incomplete state

**Phase E Behavior with Missing/Incomplete State**:

- **FR-025**: Phase E MUST execute unconditionally even when execution state is missing or incomplete (missing plan_state, execution_results, task_profile, execution_passes, convergence_assessment, or semantic_validation), when total_passes is zero, or when TTL expires. Phase E MUST NOT raise exceptions for missing or incomplete upstream artifacts.
- **FR-026**: Degraded FinalAnswer MUST conform exactly to the FinalAnswer schema; no alternative schemas or additional fields are permitted.
- **FR-027**: When state is missing or incomplete, Phase E MUST produce a degraded FinalAnswer using only available data. Degraded FinalAnswer MUST contain at minimum:
  - answer_text (str, required): Must explain the situation, available data, and reason for degradation (e.g., "Unable to synthesize complete answer due to missing execution results. Based on available request and plan state: [synthesis of available data]")
  - metadata (dict, required): Must indicate which PhaseEInput fields were missing or incomplete (e.g., {"missing_fields": ["execution_results", "plan_state"], "degraded": True, "reason": "incomplete_state"})
  - ttl_exhausted (Optional[bool]): Must be True if TTL was exhausted, None otherwise
- **FR-028**: "Available raw data" MUST be drawn exclusively from upstream execution artifacts and MUST NOT include inferred or reconstructed fields. The mapping from upstream artifacts to FinalAnswer fields MUST be:
  - plan_state → summarized in answer_text, raw structure (if present) in metadata["plan_state"]
  - execution_results → summarized in answer_text, raw structure (if present) in metadata["execution_results"]
  - execution_passes → summarized in answer_text, list structure (if present) in metadata["execution_passes"]
  - convergence_assessment → summarized in answer_text, raw structure (if present) in metadata["convergence_assessment"]
  - task_profile → summarized in answer_text, raw structure (if present) in metadata["task_profile"]
  - semantic_validation → summarized in answer_text, raw structure (if present) in metadata["semantic_validation"]
  - convergence_status → reflected in answer_text synthesis
  - ttl_remaining → reflected in ttl_exhausted field and answer_text
- **FR-029**: "Available raw data" MUST be placed only into `answer_text` (summarized) or `metadata` (structured) and MUST NOT modify the FinalAnswer schema.
- **FR-030**: When upstream data is incomplete, Phase E MUST still produce a degraded FinalAnswer using available data and MUST indicate early exit before convergence within `answer_text`.
- **FR-031**: Phase E MUST execute even when total_passes is zero (no execution passes occurred)
- **FR-032**: Phase E MUST NOT raise exceptions for missing or incomplete upstream artifacts
- **FR-033**: Degraded FinalAnswer MUST NOT contain speculative fields beyond the defined schema (answer_text, confidence, used_step_ids, notes, ttl_exhausted, metadata). No additional fields may be added even if they seem useful.
- **FR-034**: Degraded FinalAnswer MUST be valid FinalAnswer model instance (passes Pydantic validation) regardless of state completeness

**Phase E Input/Output Models**:

- **FR-037**: System MUST define PhaseEInput model in `aeon/orchestration/phases.py` with explicit field requirements:
  - Required fields: request (str), correlation_id (str), execution_start_timestamp (datetime), convergence_status (str), total_passes (int), total_refinements (int), ttl_remaining (int)
  - Optional fields (must use Optional[] type hints): plan_state (Optional[Dict[str, Any]]), execution_results (Optional[Dict[str, Any]]), convergence_assessment (Optional[Dict[str, Any]]), execution_passes (Optional[List[Dict[str, Any]]]), semantic_validation (Optional[Dict[str, Any]]), task_profile (Optional[Dict[str, Any]])
- **FR-038**: System MUST define FinalAnswer model in `aeon/orchestration/phases.py` with explicit field requirements:
  - Required field: answer_text (str, must never be None or empty, must explain the situation even in degraded mode)
  - Optional fields (must use Optional[] type hints): confidence (Optional[float]), used_step_ids (Optional[List[str]]), notes (Optional[str]), ttl_exhausted (Optional[bool])
  - Required field: metadata (Dict[str, Any], must never be None, may be empty dict, used to indicate missing/incomplete fields in degraded mode with structure: {"missing_fields": List[str], "degraded": bool, "reason": str, ...})
- **FR-039**: PhaseEInput and FinalAnswer models MUST use Pydantic BaseModel with explicit Optional[] type hints for optional fields

**Phase E Integration**:

- **FR-040**: System MUST attach final_answer (FinalAnswer model, serialized to dict) to the execution result returned by the engine under key "final_answer"
- **FR-041**: System MUST create synthesis prompts (ANSWER_SYNTHESIS_SYSTEM and ANSWER_SYNTHESIS_USER) in the prompt registry with AnswerSynthesisInput model (derived from PhaseEInput) and FinalAnswerOutput model (maps to FinalAnswer)
- **FR-042**: System MUST ensure Phase E does not perform presentation-layer work (Layer 2/3 concerns are out of scope)

**CLI Display Requirements**:

- **FR-043**: CLI command `aeon execute` MUST display FinalAnswer when available in execution result
- **FR-044**: When `--json` flag is NOT used, CLI MUST display FinalAnswer in human-readable format:
  - Display answer_text prominently (e.g., "Answer: {answer_text}")
  - Display confidence if present (e.g., "Confidence: {confidence}")
  - Display ttl_exhausted warning if True (e.g., "⚠️  Time limit reached")
  - Display notes if present (e.g., "Note: {notes}")
  - Display metadata summary if present and non-empty (e.g., "Metadata: {key-value pairs}")
- **FR-045**: When `--json` flag IS used, CLI MUST include final_answer as a top-level key in JSON output with all FinalAnswer fields serialized
- **FR-046**: CLI MUST handle missing final_answer gracefully (display message "No final answer available" or omit section, do not crash)

#### Integration & Testing

- **FR-047**: System MUST add Level 1 prompt tests validating: model instantiation from sample data, prompt rendering (no missing fields), output-model loading for JSON prompts, and invariant enforcement (location, schema, registration)
  - **Level 1 prompt tests** are unit tests that validate prompt infrastructure components in isolation: (1) Pydantic model instantiation and validation from sample data, (2) prompt template rendering with input models (verifying no missing fields), (3) output model loading and validation for JSON-producing prompts, and (4) invariant enforcement tests (Location Invariant, Schema Invariant, Registration Invariant). These tests do NOT require LLM calls or full orchestration execution.
- **FR-048**: System MUST ensure kernel receives no new business logic except wiring for Phase E invocation
- **FR-049**: System MUST maintain kernel minimalism (Principle I) - only prompt removal and Phase E wiring allowed in kernel
- **FR-050**: System MUST ensure prompt logic resides outside the kernel per Constitution requirements
- **FR-051**: User Story 3 (Phase E) tests MUST be strictly limited to three integration test scenarios only. These are integration tests that call `execute_phase_e()` directly with mocked LLM adapter (not end-to-end tests through OrchestrationEngine):
  1. Test successful synthesis with complete execution state (all PhaseEInput fields populated) - mocks LLM adapter to return valid FinalAnswer JSON
  2. Test TTL expiration scenario (TTL exhausted during execution, ttl_remaining=0 or ttl_exhausted=True) - mocks LLM adapter to return degraded FinalAnswer
  3. Test incomplete data scenario (missing one or more optional PhaseEInput fields: plan_state, execution_results, task_profile, execution_passes, convergence_assessment, or semantic_validation) - mocks LLM adapter to return degraded FinalAnswer with metadata indicating missing fields
- **FR-052**: User Story 3 tests MUST NOT include tests for: integration at C-loop exit (implementation detail), engine wiring (implementation detail), CLI display (separate concern), or other scenarios beyond the three specified above
- **FR-053**: System MUST add automated tests for CLI display of FinalAnswer that verify: (1) human-readable format when `--json` flag is NOT used (answer_text, confidence, ttl_exhausted warning, notes, metadata summary), (2) JSON format when `--json` flag IS used (final_answer as top-level key with all fields), and (3) graceful handling when final_answer is missing (displays message or omits section without crashing)

### Key Entities *(include if feature involves data)*

- **PromptRegistry**: Central repository containing all prompt definitions, accessible by PromptId. Contains PromptDefinition objects with input/output models and rendering utilities.

- **PromptId**: Enumeration of all unique prompt identifiers used throughout the system. Each identifier maps to exactly one PromptDefinition.

- **PromptDefinition**: Object containing a prompt's template, input model (required), output model (optional for non-JSON prompts), and rendering function. Defines the contract for prompt usage.

- **PromptInput**: Base class for all prompt input models. Each prompt defines its own input model extending this base, specifying required fields and validation rules.

- **PromptOutput**: Base class for all prompt output models. Only JSON-producing prompts define output models extending this base.

- **JSONExtractionError**: Domain-specific exception raised by `validate_output()` when no valid JSON can be extracted from an LLM response. This exception is raised instead of attempting supervisor repair or other recovery mechanisms. The exception MUST include context about which extraction methods were attempted (dictionary "text" key extraction, markdown code block extraction, embedded JSON extraction, direct parsing). Defined in `aeon/prompts/registry.py` or appropriate exceptions module. This exception is distinct from `ValidationError`, which is raised when JSON extraction succeeds but validation against the output model fails.

- **PhaseEInput**: Input model for Phase E synthesis, defined in `aeon/orchestration/phases.py` using Pydantic BaseModel with explicit Optional[] type hints. Fields:
  - **Required fields** (must not be None): `request` (str), `correlation_id` (str), `execution_start_timestamp` (datetime), `convergence_status` (str), `total_passes` (int, must be >= 0, must accept 0), `total_refinements` (int, must be >= 0, must accept 0), `ttl_remaining` (int, must be >= 0)
  - **Optional fields** (must use Optional[] type hints with concrete types): `plan_state` (Optional[Dict[str, Any]]), `execution_results` (Optional[Dict[str, Any]]), `convergence_assessment` (Optional[Dict[str, Any]]), `execution_passes` (Optional[List[Dict[str, Any]]]), `semantic_validation` (Optional[Dict[str, Any]]), `task_profile` (Optional[Dict[str, Any]])
  - PhaseEInput MUST accept None values for optional fields and MUST NOT raise validation errors when optional fields are missing
  - PhaseEInput MUST accept total_passes=0 and total_refinements=0 (zero passes scenario)

- **FinalAnswer**: Output model for Phase E synthesis, defined in `aeon/orchestration/phases.py` using Pydantic BaseModel with explicit Optional[] type hints. Fields:
  - **Required field** (must never be None or empty string): `answer_text` (str, minimum length 1, must explain the situation even in degraded mode, must never be None or empty)
  - **Optional fields** (must use Optional[] type hints): `confidence` (Optional[float], range 0.0-1.0 if present), `used_step_ids` (Optional[List[str]], may be empty list), `notes` (Optional[str], may be empty string), `ttl_exhausted` (Optional[bool])
  - **Required field** (must never be None, may be empty dict): `metadata` (Dict[str, Any], must never be None, used to indicate missing/incomplete fields in degraded mode with structure: {"missing_fields": List[str], "degraded": bool, "reason": str, ...}). The metadata field may also contain raw upstream artifact data (plan_state, execution_results, etc.) when available, as specified in FR-028.
  - FinalAnswer MUST NOT contain fields beyond the defined schema (answer_text, confidence, used_step_ids, notes, ttl_exhausted, metadata). No speculative fields allowed.
  - Degraded FinalAnswer MUST use metadata to indicate which PhaseEInput fields were missing or incomplete (e.g., {"missing_fields": ["execution_results"], "degraded": True, "reason": "incomplete_state"})
  - Degraded FinalAnswer MUST always pass Pydantic validation regardless of state completeness

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of inline prompts are removed from kernel, supervisor, phases, and tools modules (verified by automated search with zero matches)
- **SC-002**: 100% of prompts have typed input models defined in the registry (every PromptId has corresponding input model)
- **SC-003**: 100% of JSON-producing prompts have typed output models defined in the registry (verified by checking all prompts that return structured data)
- **SC-003A**: `validate_output()` successfully extracts and validates JSON from all response formats: dictionary with "text" key (including nested JSON), markdown code blocks (with and without "json" language identifier), raw JSON strings, and text with embedded JSON (verified by automated tests covering all extraction scenarios including edge cases: empty "text" values, multiple JSON objects, trailing text, unclosed code blocks, missing "text" key, non-string "text" values)
- **SC-003B**: `validate_output()` raises `JSONExtractionError` (not `ValidationError`) when no valid JSON can be extracted, and raises `ValidationError` (not `JSONExtractionError`) when JSON extraction succeeds but validation against output model fails (verified by automated tests)
- **SC-003C**: All JSON extraction logic is centralized in the prompt registry's `validate_output()` method with no duplicate extraction logic in other modules for new prompt-contract-based output validation (verified by code review and automated detection of duplicate extraction patterns)
- **SC-004**: All three invariants pass automated tests: Location Invariant (no inline prompts), Schema Invariant (all prompts have input models), Registration Invariant (all PromptIds have registry entries)
- **SC-005**: Phase E successfully produces final_answer for 100% of execution scenarios including: successful convergence with complete data, TTL expiration, incomplete/missing data (degraded mode), zero passes, and error conditions. Phase E must never raise exceptions for missing state.
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
- Migration of existing modules (parser, repair, semantic, engine, recursive, heuristics) to use the new JSON extraction logic in `validate_output()`. Existing custom parsing logic remains unchanged in this sprint
