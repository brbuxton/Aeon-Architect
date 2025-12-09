# Research: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis

**Date**: 2025-12-07  
**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Phase**: 0 - Research & Technology Decisions

## Technology Decisions

### Decision 1: Prompt Registry Location and Structure

**Decision**: Create a new top-level module `aeon/prompts/registry.py` containing all prompt definitions, input/output Pydantic models, and rendering utilities in a single file until prompt count exceeds ~100 prompts.

**Rationale**: 
- Per Constitution Principle II (Separation of Concerns), prompts must live outside the kernel
- Single-file registry simplifies maintenance and ensures all prompts are in one place
- Pydantic models co-located with prompts enable type safety and validation
- Single file is acceptable for <100 prompts; can be split later if needed
- Follows existing codebase pattern of module-level organization

**Alternatives Considered**:
- Separate files per prompt: Rejected - too many files for <100 prompts, harder to maintain
- Database-backed registry: Rejected - adds persistence complexity, in-memory is sufficient for Sprint 7
- YAML/JSON configuration files: Rejected - loses type safety, harder to validate, Python-native approach preferred

**Implementation Approach**:
- Define `PromptId` enum with all prompt identifiers
- Define `PromptDefinition` class containing template, input model, output model (optional), rendering function
- Define `PromptRegistry` class with `get_prompt()` and `validate_output()` methods
- Use Python f-strings with Pydantic model field access for rendering (e.g., `f"Goal: {input.goal}"`)

### Decision 2: JSON Extraction and Normalization Strategy

**Decision**: Implement unified JSON extraction in `validate_output()` method that handles multiple LLM response formats: dictionary with "text" key, markdown code blocks, embedded JSON, and raw JSON strings. Extraction methods are tried in priority order, and `JSONExtractionError` is raised if no valid JSON is found.

**Rationale**:
- LLMs return JSON in various formats (wrapped in "text" key, markdown code blocks, embedded in text, raw JSON)
- Unified extraction ensures consistent behavior regardless of LLM response format
- Centralized logic in prompt registry prevents duplication
- Clear error handling (`JSONExtractionError` vs `ValidationError`) improves debugging
- No supervisor repair attempts for JSON extraction failures (per spec FR-013G)

**Alternatives Considered**:
- Per-prompt extraction logic: Rejected - violates DRY, harder to maintain
- Supervisor repair for extraction failures: Rejected - per spec FR-013G, extraction failures should raise `JSONExtractionError` without repair attempts
- Regex-based extraction: Rejected - brace matching is more reliable for nested JSON structures

**Implementation Approach**:
- Priority order: (1) dictionary "text" key extraction, (2) markdown code block extraction, (3) embedded JSON extraction (brace matching), (4) direct JSON parsing
- Raise `JSONExtractionError` if all methods fail (include context about which methods were attempted)
- After successful extraction, validate against output model using Pydantic (raises `ValidationError` if validation fails)

### Decision 3: Pydantic v1/v2 Compatibility

**Decision**: Use Pydantic API surface compatible with both v1 and v2, ensuring prompt input/output models work under both versions without separate implementations.

**Rationale**:
- Codebase may use either Pydantic v1 or v2
- Compatibility ensures prompt infrastructure works regardless of Pydantic version
- Common API surface exists between v1 and v2 for basic model definition and validation
- Reduces maintenance burden of supporting two implementations

**Alternatives Considered**:
- Pydantic v2 only: Rejected - may break compatibility with existing codebase
- Separate implementations for v1/v2: Rejected - adds complexity, maintenance burden
- Version detection and conditional logic: Rejected - common API surface is sufficient

**Implementation Approach**:
- Use `BaseModel` from `pydantic` (works in both v1 and v2)
- Use `Field()` for field definitions (works in both versions)
- Use `model_dump()` for serialization (v2) with fallback to `dict()` (v1) if needed
- Add automated tests that validate compatibility under both versions (FR-014A)

### Decision 4: Phase E Integration Point

**Decision**: Implement Phase E as a first-class phase function `execute_phase_e()` in `aeon/orchestration/phases.py`, invoked from `OrchestrationEngine.run_multipass()` at the C-loop exit point (after `_execute_phase_c_loop` returns, before building final execution result).

**Rationale**:
- Per spec FR-019, Phase E must be a first-class phase, not a helper function in OrchestrationEngine
- C-loop exit point ensures Phase E receives final execution state regardless of whether Phase D ran on the final pass
- Integration at C-loop exit (not after Phase D) is correct because D may not run on the final pass
- First-class phase function maintains separation of concerns (Phase E logic outside OrchestrationEngine)

**Alternatives Considered**:
- Helper function in OrchestrationEngine: Rejected - violates spec FR-019 and FR-022 (no helper functions for Phase E in OrchestrationEngine)
- Integration after Phase D: Rejected - Phase D may not run on final pass, Phase E would miss execution state
- Integration in kernel: Rejected - violates kernel minimalism, Phase E is synthesis logic (not core orchestration)

**Implementation Approach**:
- Define `execute_phase_e()` function in `aeon/orchestration/phases.py` with signature: `execute_phase_e(phase_e_input: PhaseEInput, llm_adapter: LLMAdapter, prompt_registry: PromptRegistry) -> FinalAnswer`
- Define `PhaseEInput` and `FinalAnswer` Pydantic models in `aeon/orchestration/phases.py`
- In `OrchestrationEngine.run_multipass()`, after `_execute_phase_c_loop` returns, build `PhaseEInput` from execution state and call `execute_phase_e()`
- Attach `final_answer` (serialized FinalAnswer dict) to execution result under key "final_answer"

### Decision 5: Degraded FinalAnswer Handling

**Decision**: Phase E MUST execute unconditionally even when execution state is missing or incomplete, producing a degraded FinalAnswer that conforms to the FinalAnswer schema with `answer_text` explaining the situation and `metadata` indicating missing fields.

**Rationale**:
- Per spec FR-025, Phase E must execute unconditionally regardless of state completeness
- Degraded answers provide value to users even when execution is incomplete
- Schema conformance ensures consistent API regardless of state completeness
- Metadata field enables debugging and understanding of degradation reasons

**Alternatives Considered**:
- Raise exceptions for missing state: Rejected - violates spec FR-025 and FR-032 (Phase E must not raise exceptions for missing upstream artifacts)
- Skip Phase E when state is incomplete: Rejected - violates spec FR-025 (Phase E must execute unconditionally)
- Alternative schema for degraded answers: Rejected - violates spec FR-026 (degraded FinalAnswer must conform exactly to FinalAnswer schema)

**Implementation Approach**:
- Phase E checks for missing optional fields in PhaseEInput
- Builds degraded FinalAnswer with `answer_text` explaining available data and reason for degradation
- Sets `metadata["missing_fields"]` to list of missing field names
- Sets `metadata["degraded"] = True` and `metadata["reason"]` to degradation reason
- Ensures `answer_text` is never None or empty (minimum length 1, explains situation even in degraded mode)

### Decision 6: Prompt Contract Versioning

**Decision**: No explicit versioning in Sprint 7. Contracts are mutable and changes apply immediately to all usages. Acceptable for <100 prompts. Versioning can be added later if needed.

**Rationale**:
- Per spec clarification, no explicit versioning required for Sprint 7
- <100 prompts is manageable without versioning
- Immediate application of changes simplifies maintenance
- Versioning adds complexity that is not needed at current scale
- Can be added later if prompt count grows or backward compatibility becomes important

**Alternatives Considered**:
- Semantic versioning per prompt: Rejected - adds complexity, not needed for <100 prompts
- Versioned prompt registry: Rejected - adds complexity, immediate changes are acceptable for current scale
- Immutable prompt contracts: Rejected - too restrictive, prevents prompt improvements

**Implementation Approach**:
- Prompt contracts are defined as Pydantic models in registry
- Changes to contracts apply immediately to all usages
- No version tracking or migration logic
- Document that versioning can be added later if needed
