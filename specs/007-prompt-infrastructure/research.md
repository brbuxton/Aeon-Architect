# Research & Technical Decisions: Prompt Infrastructure & Phase E

**Feature**: Prompt Infrastructure, Prompt Contracts & Phase E Synthesis  
**Date**: 2025-12-07  
**Status**: Complete

## Overview

This document consolidates research findings and technical decisions for implementing a centralized prompt registry with schema-backed contracts and Phase E answer synthesis.

## Decision 1: Pydantic v1/v2 Compatibility

**Decision**: Use Pydantic v2 API surface with compatibility shims if needed, but target v2 directly since requirements.txt specifies `pydantic>=2.0.0`.

**Rationale**: 
- Codebase already uses Pydantic >= 2.0.0
- Pydantic v2 provides better performance and type safety
- No need for v1 compatibility if codebase is already on v2
- If compatibility is needed later, can use `pydantic.v1` imports

**Alternatives Considered**:
- Pydantic v1 only: Rejected - codebase already on v2
- Dual compatibility layer: Rejected - unnecessary complexity for current needs

**Implementation Notes**:
- Use standard Pydantic v2 BaseModel for input/output models
- Use `Field()` for field definitions with descriptions
- Use `model_validate()` for input validation
- Use `model_dump()` for serialization

## Decision 2: Prompt Rendering Mechanism

**Decision**: Use Python f-strings with Pydantic model field access (e.g., `f"Goal: {input.goal}") for prompt template rendering.

**Rationale**:
- Simple, native Python approach
- Type-safe when using Pydantic models
- Easy to read and maintain
- No external template engine dependencies
- Matches existing codebase patterns (current prompts use f-strings)

**Alternatives Considered**:
- Jinja2 templates: Rejected - adds dependency, overkill for current needs
- String.format(): Rejected - less readable than f-strings
- Template engine (Mako, etc.): Rejected - unnecessary complexity

**Implementation Notes**:
- Each prompt definition includes a `render(input: PromptInput) -> str` method
- Input models provide type-safe field access
- Validation happens before rendering (Pydantic validates input model)

## Decision 3: Prompt Registry Organization

**Decision**: Single-file registry (`aeon/prompts/registry.py`) containing both prompt definitions and their Pydantic input/output models together, until prompt count exceeds ~100.

**Rationale**:
- Current scale: ~20-30 prompts (well under 100)
- Single file simplifies navigation and maintenance
- Co-location of prompt and contracts improves maintainability
- Can refactor to multi-file structure later if needed

**Alternatives Considered**:
- Separate files per prompt: Rejected - too many files for current scale
- Separate models file: Rejected - co-location improves maintainability
- Database-backed registry: Rejected - overkill, no persistence requirements

**Implementation Notes**:
- Registry structure: `PromptRegistry` class with `get_prompt(prompt_id: PromptId, input_data: PromptInput) -> str`
- PromptId enum for type-safe prompt identifiers
- PromptDefinition class containing template, input model, output model (optional), render function

## Decision 4: Phase E Integration Point

**Decision**: Integrate Phase E at the exit of the C-loop in `OrchestrationEngine.run_multipass()`, after `_execute_phase_c_loop` returns, before building final execution result.

**Rationale**:
- Phase D may not run on the final pass (per spec requirement FR-020)
- C-loop exit point has complete execution state regardless of Phase D execution
- Matches spec requirement: "after C-loop completes, before engine returns final result"
- Ensures Phase E always receives final state

**Alternatives Considered**:
- After Phase D: Rejected - Phase D may not run on final pass
- Inside C-loop: Rejected - Phase E should run once after all passes complete
- Separate orchestration method: Rejected - adds unnecessary complexity

**Implementation Notes**:
- Phase E method: `execute_phase_e(phase_e_input: PhaseEInput) -> FinalAnswer`
- Integration point: After line 177 in `engine.py` (after C-loop, before build_execution_result)
- Phase E receives complete final state including: request, execution_results, plan_state, convergence_assessment, execution_passes, semantic_validation, task_profile, correlation_id, execution_start_timestamp, convergence_status, total_passes, total_refinements, ttl_remaining

## Decision 5: Prompt Extraction Strategy

**Decision**: Extract prompts from identified modules (kernel, supervisor, phases, tools, validation, convergence, adaptive) and register them in the prompt registry. Remove inline prompt strings and replace with registry lookups.

**Rationale**:
- Centralized management enables contract enforcement
- Single source of truth for all prompts
- Easier to maintain and update prompts
- Enables schema validation before/after LLM calls

**Alternatives Considered**:
- Keep prompts inline: Rejected - violates spec requirement FR-004
- Gradual migration: Rejected - spec requires complete removal of inline prompts

**Implementation Notes**:
- Modules to extract from:
  - `aeon/plan/prompts.py`: Plan generation prompts
  - `aeon/validation/semantic.py`: Validation prompts
  - `aeon/convergence/engine.py`: Convergence assessment prompts
  - `aeon/adaptive/heuristics.py`: TaskProfile prompts
  - `aeon/supervisor/repair.py`: Repair prompts
  - `aeon/kernel/executor.py`: Uses prompts from plan/prompts.py (remove import)
  - `aeon/kernel/orchestrator.py`: Uses prompts from plan/prompts.py (remove import)
- Each extracted prompt becomes a PromptId enum value
- Each prompt gets an input model (required) and optional output model (if JSON-producing)

## Decision 6: Output Model Optionality

**Decision**: Output models are optional - only JSON-producing prompts require output models. Non-JSON prompts skip output validation.

**Rationale**:
- Not all prompts produce structured JSON
- Some prompts produce free-form text
- Output validation only needed for structured responses
- Matches spec requirement FR-011

**Alternatives Considered**:
- Require output models for all prompts: Rejected - unnecessary for free-form text prompts
- No output models: Rejected - JSON-producing prompts need validation

**Implementation Notes**:
- PromptDefinition.output_model: Optional[Type[PromptOutput]]
- If output_model is None, skip JSON validation after LLM response
- If output_model is provided, validate LLM response against model before returning

## Decision 7: Phase E Synthesis Prompt Design

**Decision**: Create two prompts for Phase E: ANSWER_SYNTHESIS_SYSTEM (system prompt) and ANSWER_SYNTHESIS_USER (user prompt with execution state).

**Rationale**:
- Matches existing pattern (system + user prompts)
- System prompt defines synthesis role and guidelines
- User prompt contains execution state for synthesis
- Enables contract-based validation

**Alternatives Considered**:
- Single prompt: Rejected - system/user separation improves clarity
- Multiple prompts per synthesis aspect: Rejected - overcomplicated for current needs

**Implementation Notes**:
- ANSWER_SYNTHESIS_SYSTEM: Defines synthesis assistant role, guidelines for producing final answers
- ANSWER_SYNTHESIS_USER: Contains execution state (request, results, plan, convergence, etc.) formatted for synthesis
- Both prompts registered in prompt registry with PhaseEInput model
- Output validated against FinalAnswer model

## Decision 8: Kernel Changes Scope

**Decision**: Kernel changes limited to: (1) removing inline prompt imports, (2) wiring Phase E invocation (~10-20 LOC total).

**Rationale**:
- Maintains kernel minimalism (Principle I)
- Phase E logic resides outside kernel (in orchestration module)
- Prompt registry is outside kernel
- Only orchestration wiring remains in kernel

**Alternatives Considered**:
- Move Phase E into kernel: Rejected - violates separation of concerns
- Keep prompts in kernel: Rejected - violates kernel minimalism

**Implementation Notes**:
- Remove `from aeon.plan.prompts import ...` from kernel modules
- Replace with `from aeon.prompts.registry import get_prompt`
- Add Phase E invocation after C-loop in `engine.py` (outside kernel, but engine is called from kernel)
- Kernel orchestrator calls engine.run_multipass(), engine handles Phase E internally

## Decision 9: Contract Versioning

**Decision**: No explicit versioning in Sprint 7. Contracts are mutable and changes apply immediately. Acceptable for <100 prompts.

**Rationale**:
- Current scale: ~20-30 prompts
- Versioning adds complexity without immediate benefit
- Can add versioning later if needed (per spec clarification)
- Matches spec requirement: "No explicit versioning in Sprint 7"

**Alternatives Considered**:
- Semantic versioning per prompt: Rejected - unnecessary complexity for current scale
- Registry versioning: Rejected - overkill for <100 prompts

**Implementation Notes**:
- Prompt contracts can be updated in-place
- Changes apply immediately to all usages
- Document breaking changes in commit messages
- Consider versioning in future if prompt count grows or breaking changes become frequent

## Decision 10: Testing Strategy

**Decision**: Level 1 prompt tests: model instantiation, prompt rendering, output model validation, invariant enforcement.

**Rationale**:
- Validates contract system works correctly
- Ensures prompts render without errors
- Verifies input/output validation
- Confirms invariants are enforced

**Alternatives Considered**:
- Integration tests only: Rejected - need unit tests for prompt contracts
- End-to-end tests only: Rejected - need focused tests for prompt infrastructure

**Implementation Notes**:
- Unit tests in `tests/unit/prompts/test_registry.py`:
  - Test input model validation (reject invalid inputs)
  - Test prompt rendering (no missing fields, correct output)
  - Test output model validation for JSON prompts
  - Test invariant enforcement (location, schema, registration)
- Integration tests in `tests/integration/test_phase_e.py`:
  - Test Phase E produces final_answer in all scenarios
  - Test Phase E integration with execution flow

## Summary

All technical decisions are resolved. Implementation can proceed with:
1. Pydantic v2 for contract models
2. F-string rendering for prompt templates
3. Single-file registry for current scale
4. Phase E at C-loop exit point
5. Complete prompt extraction from identified modules
6. Optional output models for JSON-producing prompts
7. System/user prompt pattern for Phase E
8. Minimal kernel changes (prompt removal + Phase E wiring)
9. No versioning in Sprint 7
10. Level 1 prompt tests + Phase E integration tests
