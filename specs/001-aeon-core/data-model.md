# Data Model: Aeon Core

**Date**: 2025-11-18  
**Feature**: Aeon Core  
**Phase**: 1 - Design

## Core Entities

### Plan

A declarative JSON data structure representing a multi-step execution strategy.

**Fields**:
- `goal` (string, required): The objective or goal of the plan
- `steps` (array of PlanStep, required): Ordered list of execution steps

**Validation Rules**:
- Goal must be non-empty string
- Steps array must contain at least one step
- Step IDs must be unique within the plan
- Steps must be in sequential order (no gaps or reordering allowed)

**State Transitions**:
- Plan created: All steps have status "pending"
- Plan executing: Steps transition sequentially: pending → running → complete/failed
- Plan completed: All steps have status "complete" or "failed"
- Plan failed: Critical step failed or TTL expired

**Relationships**:
- Contains multiple PlanStep objects
- Referenced by OrchestrationState

### PlanStep

A single step within a plan execution.

**Fields**:
- `step_id` (string, required): Unique identifier for the step within the plan
- `description` (string, required): Human-readable description of what the step does
- `status` (enum, required): Current execution state
  - Values: "pending", "running", "complete", "failed"
  - Default: "pending"
- `tool` (string, optional): Name of registered tool for tool-based execution
- `agent` (string, optional): Execution agent type ("llm" for explicit LLM reasoning)
- `errors` (array of strings, optional): List of error messages. Populated by validator when validation fails (e.g., missing tool, invalid tool reference). Cleared by supervisor on successful repair or when step status transitions to "complete" or "failed"

**Validation Rules**:
- step_id must be non-empty string
- step_id must be unique within parent plan
- description must be non-empty string
- status must be one of the enum values
- Status transitions must follow: pending → running → (complete | failed)
- Status cannot transition backwards (e.g., complete → running)
- If `tool` is present, it must reference a tool registered in the tool registry
- If `agent` is present, it must be "llm"
- If both `tool` and `agent` are present, `tool` takes precedence (tool-based execution)
- If neither `tool` nor `agent` is present, step is treated as missing-tool step
- `errors` is populated by validator when validation fails (e.g., missing tool, invalid tool reference)
- `errors` is cleared by supervisor on successful repair or when step status transitions to "complete" or "failed"
- `errors` and `status` are independent: a step can have errors while status is "pending" or "running"

**State Transitions**:
- `pending` → `running`: When step execution begins
- `running` → `complete`: When step execution succeeds
- `running` → `failed`: When step execution fails (tool error, validation error, etc.)

**Relationships**:
- Belongs to Plan (parent)
- Referenced by OrchestrationState.current_step_id

### OrchestrationState

The current execution context maintained by the kernel.

**Fields**:
- `plan` (Plan, required): Current plan being executed
- `current_step_id` (string, optional): Identifier of the currently executing step (None if no step is running)
- `tool_history` (array of ToolCall, required): Log of all tool calls and their results
- `llm_outputs` (array of dict, required): History of LLM responses (raw)
- `supervisor_actions` (array of SupervisorAction, required): Log of supervisor repair attempts
- `ttl_remaining` (integer, required): Number of cycles remaining before expiration

**Validation Rules**:
- current_step_id must reference a valid step_id in plan.steps (if not None)
- tool_history is append-only (never modified, only appended)
- llm_outputs is append-only
- supervisor_actions is append-only
- ttl_remaining must be >= 0
- ttl_remaining decrements by 1 after each LLM cycle

**State Transitions**:
- Initialization: plan created, current_step_id=None, empty arrays, ttl_remaining=initial value
- Step start: current_step_id set to step.step_id, step.status="running"
- Step complete: current_step_id set to next step or None, step.status="complete"
- Step failed: current_step_id set to next step or None, step.status="failed"
- TTL expiration: Orchestration terminates, state preserved

**Relationships**:
- Contains Plan
- Contains multiple ToolCall objects
- Contains multiple SupervisorAction objects

### Tool

An external capability that can be invoked by the kernel.

**Fields**:
- `name` (string, required): Unique identifier for the tool
- `description` (string, required): Human-readable description of what the tool does
- `input_schema` (dict, required): JSON schema defining valid inputs
- `output_schema` (dict, required): JSON schema defining expected outputs
- `invoke` (function, required): Callable that executes the tool logic

**Validation Rules**:
- name must be non-empty string
- name must be unique within tool registry
- description must be non-empty string
- input_schema must be valid JSON schema
- output_schema must be valid JSON schema
- invoke must be callable
- invoke must be deterministic (same inputs → same outputs)

**State Transitions**:
- Registered: Tool added to registry, available for use
- Invoked: Tool called with validated inputs
- Completed: Tool returns result matching output_schema
- Failed: Tool throws exception or returns error

**Relationships**:
- Referenced by ToolCall
- Registered in ToolRegistry

### ToolCall

A record of a tool invocation during plan execution.

**Fields**:
- `tool_name` (string, required): Name of the tool that was called
- `arguments` (dict, required): Arguments passed to the tool (validated against input_schema)
- `result` (dict, optional): Result returned by the tool (validated against output_schema)
- `error` (dict, optional): Error information if tool invocation failed
- `timestamp` (string, required): ISO 8601 timestamp of the call
- `step_id` (string, required): ID of the plan step that triggered this tool call

**Validation Rules**:
- tool_name must reference a registered tool
- arguments must validate against tool.input_schema
- result must validate against tool.output_schema (if present)
- error and result are mutually exclusive (one or the other, not both)
- timestamp must be valid ISO 8601 format
- step_id must reference a valid step in the current plan

**State Transitions**:
- Created: Tool call initiated, arguments validated
- Executing: Tool invoke() function called
- Completed: Result received and validated
- Failed: Exception caught or error returned

**Relationships**:
- References Tool (by name)
- References PlanStep (by step_id)
- Stored in OrchestrationState.tool_history

### MemoryEntry

A key/value pair stored in the memory subsystem.

**Fields**:
- `key` (string, required): Unique identifier for the entry
- `value` (Any, required): Stored data (format depends on implementation)
- `metadata` (dict, optional): Optional metadata (timestamps, access counts, etc.)

**Validation Rules**:
- key must be non-empty string
- key must be unique within memory store
- value can be any serializable type
- metadata is optional and implementation-specific

**State Transitions**:
- Created: Entry written via Memory.write()
- Accessed: Entry read via Memory.read()
- Searched: Entry matched via Memory.search(prefix)
- Deleted: Not supported in Sprint 1 (optional future feature)

**Relationships**:
- Stored in Memory implementation
- Referenced by kernel during plan execution

### SupervisorAction

A record of a supervisor repair attempt.

**Fields**:
- `action_type` (enum, required): Type of repair action
  - Values: "json_repair", "tool_call_repair", "plan_repair"
- `original_output` (dict, required): The malformed output that triggered repair
- `repaired_output` (dict, optional): The corrected output (if repair succeeded)
- `error` (dict, optional): Error information if repair failed
- `attempt_number` (integer, required): Which repair attempt this was (1 or 2)
- `timestamp` (string, required): ISO 8601 timestamp of the action

**Validation Rules**:
- action_type must be one of the enum values
- original_output must be present
- repaired_output or error must be present (not both)
- attempt_number must be 1 or 2 (max 2 attempts per FR-050)
- timestamp must be valid ISO 8601 format

**State Transitions**:
- Created: Validation failure detected, supervisor invoked
- Repair attempt 1: First repair attempt made
- Repair attempt 2: Second repair attempt made (if first failed)
- Succeeded: repaired_output present, validation passes
- Failed: error present, declared unrecoverable

**Relationships**:
- Stored in OrchestrationState.supervisor_actions
- Triggered by ValidationError

### LogEntry

A JSONL record of a single orchestration cycle.

**Fields**:
- `step_number` (integer, required): Sequential cycle identifier
- `plan_state` (dict, required): Snapshot of plan at cycle start
- `llm_output` (dict, required): Raw LLM response
- `supervisor_actions` (array of SupervisorAction, required): Supervisor repairs in this cycle (empty if none)
- `tool_calls` (array of ToolCall, required): Tool invocations in this cycle (empty if none)
- `ttl_remaining` (integer, required): Cycles left before expiration
- `errors` (array of dict, required): Errors in this cycle (empty if none)
- `timestamp` (string, required): ISO 8601 timestamp of the cycle

**Validation Rules**:
- step_number must be >= 1 and increment sequentially
- plan_state must be valid Plan structure
- llm_output must be present (even if empty dict)
- supervisor_actions, tool_calls, errors are arrays (may be empty)
- ttl_remaining must be >= 0
- timestamp must be valid ISO 8601 format

**State Transitions**:
- Created: Cycle begins, log entry initialized
- Updated: Events added (tool calls, supervisor actions, errors)
- Finalized: Cycle completes, log entry written to JSONL file

**Relationships**:
- References OrchestrationState (snapshot)
- Written to JSONL log file

## Entity Relationships Diagram

```
Plan
├── contains → PlanStep (1:N)
└── referenced by → OrchestrationState (1:1)

OrchestrationState
├── contains → Plan (1:1)
├── contains → ToolCall[] (1:N)
├── contains → SupervisorAction[] (1:N)
└── references → PlanStep (via current_step_id)

ToolCall
├── references → Tool (by name)
└── references → PlanStep (by step_id)

SupervisorAction
└── stored in → OrchestrationState

MemoryEntry
└── stored in → Memory implementation

LogEntry
└── snapshot of → OrchestrationState
```

## Data Flow

1. **Plan Creation**: User request → LLM → Plan (with PlanSteps)
2. **Plan Execution**: Plan → Kernel → OrchestrationState initialized
3. **Step Execution**: PlanStep → Kernel → ToolCall → Tool.invoke() → Result
4. **State Update**: ToolCall result → OrchestrationState.tool_history
5. **LLM Cycle**: OrchestrationState → LLM → LLM output → Validation
6. **Supervisor Repair**: ValidationError → Supervisor → SupervisorAction
7. **Logging**: OrchestrationState → LogEntry → JSONL file

## Validation Summary

- All entities use pydantic models for validation
- JSON schemas exported for external tooling
- State transitions enforced in kernel logic
- Immutability not required for Sprint 1 (can be added later)

