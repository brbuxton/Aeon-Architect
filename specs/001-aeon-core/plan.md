# Implementation Plan: Multi-Mode Step Execution for Aeon Core

**Branch**: `001-aeon-core` | **Date**: 2025-11-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification additions for User Story 8 - Multi-Mode Step Execution

## Summary

This plan implements three forms of step execution: tool-based steps, explicit LLM reasoning steps, and missing-tool steps with repair/fallback. The implementation extends the existing Aeon Core orchestration kernel to support:
- Tool-based execution (steps with "tool" field)
- LLM reasoning steps (steps with "agent: llm" field)  
- Missing-tool detection, supervisor repair, and fallback to LLM reasoning
- LLM tool awareness during plan generation and repair
- CLI enhancements for displaying execution modes and results

**Technical Approach**: Extend existing PlanStep model with optional `tool` and `agent` fields, enhance orchestrator step execution logic, add missing-tool validation and repair flows, update LLM prompts to include tool registry, and enhance CLI output.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0, jsonschema>=4.0.0, requests>=2.31.0, pyyaml>=6.0.0  
**Storage**: Memory subsystem (ephemeral for Sprint 1, via K/V interface)  
**Testing**: pytest with coverage  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Plan generation <10s, step execution <5s per step, 95% success rate for multi-mode execution  
**Constraints**: Kernel <800 LOC, deterministic execution, no domain logic in kernel  
**Scale/Scope**: Sprint 1 - minimal viable orchestration kernel with multi-mode step execution

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, step execution mode detection and routing logic must be in orchestrator. This is core orchestration logic, not domain-specific. The logic is minimal (if/else routing) and does not add domain knowledge.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Estimated addition: ~150-200 LOC for step execution routing, missing-tool detection, and fallback logic. Current kernel is ~312 LOC, total will be ~462-512 LOC, well under 800.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Step execution routing is orchestration logic, not domain logic. Tool validation uses registry interface, supervisor repair uses existing supervisor interface, LLM reasoning uses existing LLM interface.

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Missing-tool repair uses existing supervisor module. LLM reasoning uses existing LLM adapter. No new tools or supervisors required.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. All interactions use existing interfaces: ToolRegistry, LLMAdapter, Supervisor, Memory, Validator.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. External modules continue to interact through defined interfaces only.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: Yes. PlanStep gains optional `tool` (string) and `agent` (string) fields. These are declarative data, not procedural logic.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: No. The `tool` and `agent` fields are declarative metadata indicating execution mode.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: No, but kernel changes are minimal and justified. Step execution routing is core orchestration responsibility. Changes are limited to orchestrator step execution logic.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. This is a deliberate extension of core orchestration capability, well-documented in spec and plan.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: Yes. Multi-mode step execution is core orchestration functionality, explicitly within Sprint 1 scope per User Story 8.

## Project Structure

### Documentation (this feature)

```text
specs/001-aeon-core/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (updated with multi-mode decisions)
├── data-model.md        # Phase 1 output (updated with tool/agent fields)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (interfaces.md updated)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
aeon/
├── kernel/
│   ├── orchestrator.py  # Main orchestration loop, step execution routing, fallback handling
│   ├── executor.py      # Step execution logic (tool, LLM, fallback)
│   ├── state.py         # OrchestrationState model
│   └── __init__.py
├── validation/          # External module (NOT kernel)
│   └── schema.py        # Plan + tool-call validation logic
├── supervisor/          # External module (NOT kernel)
│   └── repair.py        # LLM-based JSON + structure repair
├── plan/
│   ├── models.py        # Plan, PlanStep (updated with tool/agent fields)
│   ├── parser.py        # Plan parsing (existing)
│   └── validator.py     # Plan validation (existing)
├── llm/
│   ├── interface.py     # LLMAdapter interface (existing)
│   └── adapters/        # LLM adapters (existing)
├── memory/
│   ├── interface.py     # Memory interface (existing)
│   └── kv_store.py      # In-memory K/V store (existing)
├── tools/
│   ├── interface.py     # Tool interface (existing)
│   ├── registry.py      # Tool registry (existing, enhanced for tool list export)
│   └── models.py        # Tool models (existing)
├── observability/
│   └── models.py        # LogEntry model (existing)
├── cli/
│   └── main.py          # CLI interface (enhanced for multi-mode display)
└── config.py            # Configuration (existing)

tests/
├── unit/
│   ├── kernel/
│   │   ├── test_orchestrator.py      # Test step execution modes
│   │   ├── test_executor.py          # Test executor logic
│   │   └── test_validator.py         # Test missing-tool detection
│   ├── plan/
│   │   └── test_models.py            # Test PlanStep with tool/agent fields
│   └── tools/
│       └── test_registry.py          # Test tool list export
├── integration/
│   ├── test_multi_mode_execution.py  # End-to-end multi-mode tests
│   ├── test_missing_tool_repair.py  # Test supervisor repair
│   └── test_fallback_reasoning.py   # Test LLM fallback
└── contract/
    └── test_interfaces.py           # Interface contract tests
```

**Structure Decision**: Single Python package structure. All modules in `aeon/` package. Tests mirror source structure. No new top-level directories required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All changes are justified and within constitutional bounds.

## Implementation Details

### Phase 0: Research & Technology Decisions

**New Research Decisions Required**:

1. **Step Execution Mode Detection**
   - **Decision**: Use optional fields in PlanStep: `tool` (string, tool name) and `agent` (string, "llm" for explicit reasoning)
   - **Rationale**: Declarative approach, minimal schema change, clear execution mode indication
   - **Priority**: Tool field takes precedence over agent field if both present

2. **Missing-Tool Detection Strategy**
   - **Decision**: Validator checks tool registry before step execution. Missing/invalid tools populate step.errors field with error messages.
   - **Rationale**: Early detection prevents invalid execution attempts, enables repair before execution. Using errors field (List[str]) allows multiple error messages and clear semantics.
   - **Implementation**: Validator method `validate_step_tool(step: PlanStep, registry: ToolRegistry) -> ValidationResult` populates step.errors in-place when validation fails

3. **Supervisor Repair Prompt for Missing Tools**
   - **Decision**: Supervisor receives: available tools list with schemas, step context, plan goal. Prompt: "Repair this step to reference a valid tool from the available list. Do not invent tools."
   - **Rationale**: Tool-aware repair enables supervisor to correct tool references using actual registry
   - **Implementation**: Supervisor method `repair_missing_tool_step(step: PlanStep, tools: List[Tool], plan_goal: str) -> PlanStep`

4. **Fallback Reasoning Prompt**
   - **Decision**: Use step description as prompt, include Memory subsystem context, invoke LLM adapter directly
   - **Rationale**: Simple fallback when tools unavailable, leverages existing LLM interface
   - **Implementation**: Executor method `execute_llm_reasoning_step(step: PlanStep, memory: Memory, llm: LLMAdapter) -> Dict`

5. **LLM Tool Awareness**
   - **Decision**: Plan generation and supervisor repair prompts include complete tool registry (names, descriptions, schemas, examples)
   - **Rationale**: Prevents LLM from inventing tools, ensures tool references are valid
   - **Implementation**: Orchestrator methods `_build_plan_prompt()` and supervisor `_build_repair_prompt()` include tool registry export

### Phase 1: Design & Contracts

**Data Model Updates**:

1. **PlanStep Model Extension**:
   ```python
   class PlanStep(BaseModel):
       step_id: str
       description: str
       status: StepStatus
       tool: Optional[str] = None  # Tool name for tool-based execution
       agent: Optional[str] = None  # "llm" for explicit LLM reasoning
       errors: Optional[List[str]] = None  # Error messages populated by validator
   ```
   - Validation: If `tool` present, must reference registered tool. If `agent` present, must be "llm". If both present, `tool` takes precedence.
   - Errors: Populated by validator when validation fails (e.g., missing tool). Cleared by supervisor on successful repair.

2. **OrchestrationState Updates**:
   - No structural changes. Existing fields sufficient for multi-mode execution tracking.

3. **ToolRegistry Enhancement**:
   - Add method `export_tools_for_llm() -> List[Dict]` that returns tool list with schemas and examples for LLM prompts.

**Interface Contracts**:

1. **Executor Interface** (new module):
   ```python
   class StepExecutor:
       def execute_step(
           self,
           step: PlanStep,
           registry: ToolRegistry,
           memory: Memory,
           llm: LLMAdapter,
           supervisor: Supervisor
       ) -> StepExecutionResult
   ```
   - Handles routing: tool-based → tool execution, LLM step → LLM reasoning, missing-tool → repair → fallback

2. **Validator Enhancement**:
   ```python
   def validate_step_tool(step: PlanStep, registry: ToolRegistry) -> ValidationResult
   ```
   - Populates step.errors field (List[str]) with error messages if tool missing/invalid
   - Returns ValidationResult indicating validation status
   - Modifies step object in-place (step.errors is set)

3. **Supervisor Enhancement**:
   ```python
   def repair_missing_tool_step(
       self,
       step: PlanStep,
       tools: List[Tool],
       plan_goal: str
   ) -> PlanStep
   ```
   - Attempts to repair step with valid tool reference

**Execution Flow**:

1. **Orchestrator receives step for execution**
2. **Executor determines execution mode**:
   - If `step.tool` present and valid → tool-based execution
   - Else if `step.agent == "llm"` → LLM reasoning execution
   - Else → missing-tool path
3. **Missing-tool path**:
   - Validator populates step.errors with error messages
   - Supervisor attempts repair (up to 2 attempts), reading step.errors and clearing it on success
   - If repair succeeds → step.errors cleared, execute as tool-based step
   - If repair fails → step.errors remains, execute as LLM reasoning step (fallback)
4. **All execution paths**:
   - Store results in the Memory subsystem
   - Update step status (complete/failed)
   - Log to observability system

### Phase 2: Implementation Tasks

**Core Implementation** (to be broken down by `/speckit.tasks`):

1. **Update PlanStep Model**:
   - Add optional `tool` and `agent` fields
   - Add validation for tool references
   - Add validation for agent field values

2. **Enhance Validator**:
   - Implement `validate_step_tool()` method
   - Integrate with orchestrator step execution

3. **Create StepExecutor**:
   - Implement step execution routing logic
   - Implement tool-based execution
   - Implement LLM reasoning execution
   - Implement fallback execution

4. **Enhance Supervisor**:
   - Implement `repair_missing_tool_step()` method
   - Update repair prompts to include tool registry

5. **Enhance Orchestrator**:
   - Integrate StepExecutor
   - Update plan generation prompts to include tool registry
   - Handle missing-tool repair flow
   - Handle fallback execution

6. **Enhance ToolRegistry**:
   - Implement `export_tools_for_llm()` method
   - Format tool schemas for LLM consumption

7. **Enhance CLI**:
   - Display execution mode for each step
   - Display warnings for missing/invalid tools
   - Display repaired steps
   - Display fallback steps
   - Preserve Plan object identity

8. **Testing**:
   - Unit tests for each execution mode
   - Integration tests for missing-tool repair
   - Integration tests for fallback reasoning
   - Contract tests for interfaces

## Success Criteria

- [x] PlanStep model supports optional `tool` and `agent` fields
- [x] Validator detects missing/invalid tool references
- [x] Supervisor repairs missing-tool steps with tool registry awareness
- [x] Executor routes steps to correct execution mode
- [x] Fallback execution uses LLM reasoning when tools unavailable
- [x] LLM prompts include tool registry during plan generation and repair
- [x] CLI displays execution modes, warnings, repairs, and fallbacks
- [x] All execution paths store results in the Memory subsystem
- [x] All execution paths log to observability system
- [x] Kernel LOC remains under 800
- [x] 95% success rate for multi-mode execution in tests
- [x] 100% tool registry compliance (no invented tools)

## Dependencies

- Existing Aeon Core modules (orchestrator, validator, supervisor, tools, memory, LLM)
- pydantic for model validation
- jsonschema for tool schema validation
- pytest for testing

## Risks & Mitigations

1. **Risk**: Kernel LOC exceeds 800
   - **Mitigation**: Extract executor to separate module, keep orchestrator minimal

2. **Risk**: LLM invents tools despite registry inclusion
   - **Mitigation**: Strict validation, supervisor repair, clear prompt instructions

3. **Risk**: Fallback execution too slow
   - **Mitigation**: Monitor performance, optimize prompts, consider caching

4. **Risk**: Missing-tool repair success rate too low
   - **Mitigation**: Improve repair prompts, add examples, test with various scenarios

## Next Steps

1. Run `/speckit.tasks` to break down implementation into specific tasks
2. Update `research.md` with multi-mode execution decisions
3. Update `data-model.md` with PlanStep field additions
4. Update `contracts/interfaces.md` with new executor interface
5. Begin implementation following TDD approach
