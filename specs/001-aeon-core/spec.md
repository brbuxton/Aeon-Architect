# Feature Specification: Aeon Core

**Feature Branch**: `001-aeon-core`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "Generate a formal requirements specification for a project named Aeon Core. Aeon Core is a minimal LLM orchestration kernel whose goal in Sprint 1 is to reliably run a structured thought → tool → thought loop using a declarative plan, supervised validation, state management, and deterministic execution."

## Clarifications

### Session 2025-01-27

- Q: How should the system handle LLM API failures (network errors, timeouts, rate limits, service unavailable)? → A: Retry with exponential backoff (e.g., 3 attempts), then fail gracefully
- Q: How many repair attempts should the supervisor make before declaring an error unrecoverable? → A: 2 repair attempts, then declare unrecoverable
- Q: Must plan steps execute in strict sequential order, or can the LLM update/reorder steps during execution? → A: Strict sequential order (step N must complete before step N+1 starts)
- Q: What format should the memory search pattern support? → A: Prefix match (keys starting with pattern)
- Q: When a tool invocation fails (exception or error return), how should the kernel handle it? → A: Mark step as failed, log error, continue to next step

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan Generation from Natural Language (Priority: P1)

As a developer, I can submit a natural language request, and Aeon Core generates a declarative multi-step plan describing how it will solve the task.

**Why this priority**: This is the foundational capability that enables all other orchestration. Without plan generation, the system cannot begin reasoning. It represents the entry point for all user interactions.

**Independent Test**: Can be fully tested by submitting a natural language request (e.g., "calculate the sum of 5 and 10") and verifying that Aeon Core produces a valid JSON plan structure containing: goal, list of steps with IDs, descriptions, and status flags. The test delivers value by proving the system can translate user intent into structured execution plans.

**Acceptance Scenarios**:

1. **Given** a developer submits a natural language request, **When** Aeon Core processes the request, **Then** it generates a valid JSON plan with required fields (goal, steps array, step IDs, descriptions, status flags)
2. **Given** a developer submits a complex multi-step request, **When** Aeon Core processes the request, **Then** it generates a plan with multiple steps that logically sequence the solution
3. **Given** a developer submits an ambiguous request, **When** Aeon Core processes the request, **Then** it generates a plan that represents a reasonable interpretation of the request

---

### User Story 2 - Step-by-Step Plan Execution with Status Updates (Priority: P1)

As a developer, I can observe Aeon executing the plan step-by-step, with each step's status (pending, running, complete, failed) updated deterministically.

**Why this priority**: This demonstrates the core orchestration loop functionality. Status updates provide visibility into execution progress and enable debugging. This is essential for proving the system can reliably execute structured reasoning.

**Independent Test**: Can be fully tested by submitting a plan and verifying that Aeon Core executes steps sequentially, updating each step's status from "pending" → "running" → "complete" (or "failed") in a deterministic manner. The test delivers value by proving the orchestration engine works correctly.

**Acceptance Scenarios**:

1. **Given** a valid plan with multiple steps, **When** Aeon Core executes the plan, **Then** each step transitions through status states (pending → running → complete) in order
2. **Given** a plan with a step that fails, **When** Aeon Core executes the plan, **Then** the step status updates to "failed" and subsequent steps are handled according to plan logic
3. **Given** a plan execution in progress, **When** a developer queries the current state, **Then** they receive accurate status for all steps

---

### User Story 3 - Supervisor Error Correction (Priority: P2)

As a developer, when Aeon produces malformed JSON, inconsistent tool calls, or structurally invalid plans, Aeon routes the output to the Supervisor and receives corrected JSON without halting the orchestration loop.

**Why this priority**: LLM outputs are inherently non-deterministic and may contain syntax errors. The supervisor enables graceful error recovery, which is critical for reliability. However, this is secondary to basic execution (P1) since the system should work with valid outputs first.

**Independent Test**: Can be fully tested by injecting malformed JSON into the LLM output path and verifying that the Supervisor repairs it, returns corrected JSON, and the orchestration loop continues without interruption. The test delivers value by proving the system can self-correct and maintain execution continuity.

**Acceptance Scenarios**:

1. **Given** the LLM produces malformed JSON, **When** the validation layer detects the error, **Then** the Supervisor is invoked, repairs the JSON, and returns corrected output without halting execution
2. **Given** the LLM produces a tool call with invalid schema, **When** the validation layer detects the error, **Then** the Supervisor repairs the tool call structure and returns a valid call
3. **Given** the LLM produces a plan update with missing required fields, **When** the validation layer detects the error, **Then** the Supervisor adds missing fields or corrects structure and returns a valid plan update
4. **Given** the Supervisor cannot repair an error after attempts, **When** the Supervisor determines the error is unrecoverable, **Then** it declares an unrecoverable error and the system handles it gracefully

---

### User Story 4 - Tool Registration and Invocation (Priority: P2)

As a developer, I can define simple stub tools (e.g., echo, dummy calculator) and Aeon will call them with validated arguments and integrate their results into the next LLM reasoning cycle.

**Why this priority**: Tools are essential for extending system capabilities beyond pure reasoning. However, basic orchestration (P1) must work first. This enables the system to demonstrate the complete thought → tool → thought loop.

**Independent Test**: Can be fully tested by registering a stub tool (e.g., echo tool that returns its input), creating a plan that calls the tool, and verifying that Aeon invokes the tool with validated arguments and incorporates the result into the next LLM cycle. The test delivers value by proving the tool interface works and integrates with the orchestration loop.

**Acceptance Scenarios**:

1. **Given** a developer registers a tool with a defined schema (name, description, input_schema, output_schema, invoke function), **When** Aeon Core processes the registration, **Then** the tool is available for use in plans
2. **Given** a plan contains a step that calls a registered tool, **When** Aeon Core executes that step, **Then** it validates the tool call arguments against the tool's input_schema, invokes the tool, and receives the result
3. **Given** a tool returns a result, **When** Aeon Core processes the result, **Then** it integrates the result into the plan state and passes it to the next LLM reasoning cycle
4. **Given** a tool call with invalid arguments, **When** Aeon Core validates the call, **Then** it rejects the call and routes to Supervisor for correction

---

### User Story 5 - Key/Value Memory Operations (Priority: P3)

As a developer, I can store and retrieve values from Aeon's key/value memory, and Aeon can use that memory during multi-step reasoning.

**Why this priority**: Memory enables state persistence across reasoning cycles, which is valuable for complex multi-step tasks. However, basic orchestration can function without memory for simple tasks, making this a lower priority than core execution capabilities.

**Independent Test**: Can be fully tested by storing a value with a key, retrieving it by key, and verifying that Aeon can read from memory during plan execution and use stored values in subsequent reasoning steps. The test delivers value by proving the memory subsystem works and integrates with orchestration.

**Acceptance Scenarios**:

1. **Given** a developer stores a value with a key using write(key, value), **When** they retrieve it using read(key), **Then** the correct value is returned
2. **Given** multiple values stored in memory, **When** a developer searches using a pattern, **Then** matching keys and values are returned
3. **Given** values stored in memory during plan execution, **When** Aeon executes subsequent steps, **Then** it can read from memory and use stored values in reasoning
4. **Given** a read operation for a non-existent key, **When** the memory system processes the request, **Then** it returns an appropriate "not found" response

---

### User Story 6 - TTL Expiration Handling (Priority: P3)

As a developer, when Aeon exceeds its TTL, it gracefully stops reasoning and returns a structured "TTL expired" response.

**Why this priority**: TTL prevents infinite loops and resource exhaustion, which is important for production use. However, for Sprint 1, proving basic orchestration works is more critical than handling edge cases like expiration.

**Independent Test**: Can be fully tested by setting a low TTL (e.g., 2 cycles), executing a plan that would normally take more cycles, and verifying that Aeon stops execution when TTL reaches zero and returns a structured expiration response. The test delivers value by proving the system can gracefully handle resource limits.

**Acceptance Scenarios**:

1. **Given** a plan execution with TTL set to N cycles, **When** the execution reaches N cycles, **Then** the loop terminates and returns a structured "TTL expired" response
2. **Given** TTL is decremented after each LLM cycle, **When** monitoring the TTL counter, **Then** it accurately reflects remaining cycles
3. **Given** execution stops due to TTL expiration, **When** the system processes the expiration, **Then** it saves current state and provides a clear expiration message

---

### User Story 7 - Orchestration Cycle Logging (Priority: P2)

As a developer, I can review a JSONL log showing each orchestration cycle, including decisions, tool calls, supervisor actions, and state updates.

**Why this priority**: Observability is critical for debugging and understanding system behavior. However, the system must execute correctly (P1) before detailed logging becomes essential. This enables developers to diagnose issues and verify correct operation.

**Independent Test**: Can be fully tested by executing a plan with multiple cycles and verifying that each cycle produces a JSONL log entry containing: step number, plan state, LLM output, supervisor actions (if any), tool calls, TTL remaining, and errors (if any). The test delivers value by proving developers can audit and debug orchestration behavior.

**Acceptance Scenarios**:

1. **Given** Aeon Core executes an orchestration cycle, **When** the cycle completes, **Then** a JSONL log entry is generated containing all required fields (step number, plan state, LLM output, supervisor actions, tool calls, TTL, errors)
2. **Given** multiple orchestration cycles execute, **When** reviewing the log file, **Then** each cycle has a corresponding log entry in chronological order
3. **Given** a supervisor action occurs during a cycle, **When** reviewing the log entry, **Then** the supervisor action details are included in the log
4. **Given** an error occurs during execution, **When** reviewing the log entry, **Then** error details are captured in the log

---

### Edge Cases

- What happens when the LLM produces a plan with circular dependencies between steps? (Note: Sequential execution order prevents true circular dependencies, but step descriptions may reference later steps)
- How does the system handle a tool that throws an exception or returns an error? (Answer: Step marked as failed, error logged, execution continues to next step)
- What happens when memory storage fails or becomes unavailable?
- How does the system handle supervisor failures (supervisor cannot repair an error)?
- What happens when TTL expires mid-tool-call?
- How does the system handle malformed tool schemas during registration?
- What happens when the LLM produces a plan that references non-existent tools?
- How does the system handle concurrent access to memory (if applicable in Sprint 1)?
- What happens when validation fails and supervisor also fails to repair after 2 attempts?
- How does the system handle plan updates that would create invalid state transitions?
- What happens when the LLM API is unavailable after retry attempts are exhausted?

## Requirements *(mandatory)*

### Functional Requirements

#### Kernel Execution Loop

- **FR-001**: The system SHALL run an iterative LLM interaction loop that processes plans, tool results, and TTL state
- **FR-002**: The loop SHALL pass the current plan state, tool results from previous cycles, and remaining TTL to the LLM on each iteration
- **FR-003**: The loop SHALL parse and validate the LLM's structured response before proceeding
- **FR-004**: The loop SHALL terminate when the plan reaches a completed state (all steps complete or marked failed)
- **FR-005**: The loop SHALL terminate when TTL reaches zero, regardless of plan completion status
- **FR-048**: When LLM API calls fail (network errors, timeouts, rate limits, service unavailable), the system SHALL retry with exponential backoff up to 3 attempts before failing gracefully
- **FR-049**: After exhausting retry attempts for LLM API failures, the system SHALL log the error, update the current step status to "failed", and terminate the orchestration loop with a structured error response

#### Plan Engine

- **FR-006**: The system SHALL support creation of a declarative plan in JSON format from LLM output
- **FR-007**: The plan SHALL contain the following required fields: goal (string), steps (array), where each step contains: step_id (string), description (string), status (enum: pending, running, complete, failed)
- **FR-008**: The system SHALL update plan steps and their status flags as execution proceeds through each step
- **FR-009**: The plan SHALL be a pure data structure (JSON/YAML) and SHALL NOT contain executable code or procedural logic
- **FR-010**: The system SHALL reject or route to Supervisor any malformed plan structures that do not conform to the required schema
- **FR-052**: Plan steps SHALL execute in strict sequential order: step N must reach status "complete" or "failed" before step N+1 can transition from "pending" to "running"
- **FR-053**: The LLM SHALL NOT be permitted to reorder steps or change step sequence during execution; step order is fixed at plan creation

#### State Manager

- **FR-011**: The system SHALL maintain orchestration state including: current plan, current step identifier, tool call history, LLM outputs, supervisor actions log, and TTL counters
- **FR-012**: State SHALL be stored in memory for the full duration of the orchestration session
- **FR-013**: The system SHALL provide optional state persistence to disk or file (deferred to Sprint 2, not required in Sprint 1)

#### Minimal Memory Subsystem

- **FR-014**: The system SHALL include a simple key/value memory store external to the kernel
- **FR-015**: Memory SHALL support write(key, value) operation that stores a value associated with a key
- **FR-016**: Memory SHALL support read(key) operation that retrieves a value by key
- **FR-017**: Memory SHALL support search(pattern) operation that finds all keys starting with the provided pattern (prefix match)
- **FR-018**: Memory SHALL be accessed by the kernel only through a well-defined interface, with no direct internal access

#### Tool Interface and Registry

- **FR-019**: The system SHALL define a tool schema with the following required fields: name (string), description (string), input_schema (JSON schema), output_schema (JSON schema), and invoke() function
- **FR-020**: The system SHALL allow the kernel to register tools through the tool registry interface
- **FR-021**: The system SHALL allow the kernel to list all registered tools
- **FR-022**: The kernel SHALL be able to call registered tools deterministically through the tool interface
- **FR-023**: Sprint 1 SHALL include only stub/dummy tools (e.g., echo, simple calculator) with no domain-specific logic
- **FR-054**: When a tool invocation fails (throws exception or returns error), the kernel SHALL mark the current step status as "failed", log the error, and continue execution to the next step in the plan
- **FR-055**: Tool errors SHALL be logged in the orchestration cycle log entry with error details, and the error SHALL be included in the state passed to the next LLM cycle

#### Validation Layer

- **FR-024**: The system SHALL validate LLM output against a structured schema before processing
- **FR-025**: The system SHALL validate tool calls against their registered tool definitions (input_schema validation)
- **FR-026**: The system SHALL validate plan updates for required fields and structural correctness
- **FR-027**: Validation failures SHALL route to the Supervisor for repair attempts before rejection

#### Supervisor Layer

- **FR-028**: The supervisor SHALL use the same LLM as the main orchestration loop but with a reduced system prompt focused on repair
- **FR-029**: The supervisor SHALL repair malformed JSON structures in LLM outputs
- **FR-030**: The supervisor SHALL repair tool calls that do not conform to tool schemas
- **FR-031**: The supervisor SHALL repair plan fragments that are structurally invalid
- **FR-032**: The supervisor SHALL NOT introduce new tools, new semantic meaning, or modify the intent of the original output
- **FR-033**: The supervisor SHALL return corrected JSON structures or declare an unrecoverable error if repair is not possible
- **FR-050**: The supervisor SHALL make up to 2 repair attempts for a given validation failure before declaring the error unrecoverable
- **FR-051**: After 2 failed repair attempts, the supervisor SHALL declare an unrecoverable error and return a structured error response to the kernel

#### TTL and Governance

- **FR-034**: The system SHALL implement a Time-To-Live (TTL) counter for the orchestration loop
- **FR-035**: The TTL SHALL decrement by one after each complete LLM cycle (after LLM response is processed)
- **FR-036**: When TTL reaches zero, the loop SHALL exit cleanly and return a structured response indicating TTL expiration

#### Observability

- **FR-037**: The system SHALL log each orchestration cycle to a JSONL format log file
- **FR-038**: Each log entry SHALL include: step number, current plan state, LLM output, supervisor actions (if any), tool calls made, TTL remaining, and errors (if any)
- **FR-039**: Logs SHALL be generated for every orchestration cycle, including cycles that result in errors

#### Excluded Capabilities for Sprint 1

- **FR-040**: The Sprint 1 codebase SHALL NOT include diagram generation capabilities
- **FR-041**: The Sprint 1 codebase SHALL NOT include Infrastructure as Code (IaC) generation capabilities
- **FR-042**: The Sprint 1 codebase SHALL NOT include cloud-specific logic (Azure, AWS, etc.)
- **FR-043**: The Sprint 1 codebase SHALL NOT include pattern libraries or pattern matching beyond basic validation
- **FR-044**: The Sprint 1 codebase SHALL NOT include RAG (Retrieval Augmented Generation) systems
- **FR-045**: The Sprint 1 codebase SHALL NOT include embeddings or vector search capabilities
- **FR-046**: The Sprint 1 codebase SHALL NOT include advanced memory ranking or retrieval beyond simple key/value operations
- **FR-047**: The Sprint 1 codebase SHALL NOT include multi-agent spawning or concurrency features

### Key Entities

- **Plan**: A declarative JSON data structure representing a multi-step execution strategy. Contains: goal (the objective), steps (array of step objects), where each step has: step_id (unique identifier), description (what the step does), status (current execution state: pending, running, complete, failed)

- **Orchestration State**: The current execution context maintained by the kernel. Contains: plan (current plan being executed), current_step (identifier of the active step), tool_history (log of tool calls and results), llm_outputs (history of LLM responses), supervisor_actions (log of supervisor repairs), ttl_remaining (cycles left before expiration)

- **Tool**: An external capability that can be invoked by the kernel. Defined by: name (unique identifier), description (what the tool does), input_schema (JSON schema defining valid inputs), output_schema (JSON schema defining expected outputs), invoke (function that executes the tool logic)

- **Memory Entry**: A key/value pair stored in the memory subsystem. Contains: key (unique identifier string), value (stored data, format depends on implementation), and optional metadata (timestamps, access counts, etc.)

- **Log Entry**: A JSONL record of a single orchestration cycle. Contains: step_number (sequential cycle identifier), plan_state (snapshot of plan at cycle start), llm_output (raw LLM response), supervisor_actions (array of repair actions if any), tool_calls (array of tool invocations), ttl_remaining (cycles left), errors (array of error objects if any), timestamp (when the cycle occurred)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can submit a natural language request and receive a valid, structured plan within 10 seconds of submission
- **SC-002**: The system successfully executes plans with up to 10 steps without errors in 95% of test cases
- **SC-003**: When the Supervisor is invoked for malformed JSON, it successfully repairs and returns corrected output in 90% of cases
- **SC-004**: Tool calls are validated and executed with 100% schema compliance (all tool calls match their registered schemas)
- **SC-005**: Memory operations (write, read, search) complete successfully in 99% of operations
- **SC-006**: When TTL expires, the system gracefully terminates and returns a structured response in 100% of cases
- **SC-007**: Every orchestration cycle produces a complete JSONL log entry with all required fields in 100% of cycles
- **SC-008**: The kernel codebase remains under 800 lines of code (LOC) as measured by the primary kernel module
- **SC-009**: The system demonstrates a complete thought → tool → thought loop: plan generation, tool invocation with results, and state update based on tool results, in a single end-to-end test

## Assumptions

- The system will use an existing LLM API (e.g., OpenAI, Anthropic) and does not need to implement LLM functionality
- JSON and YAML parsing libraries are available in the chosen implementation language
- The system operates in a single-threaded, sequential execution model for Sprint 1 (no concurrency requirements)
- File I/O operations are available for optional state persistence and logging
- Error handling and logging infrastructure (basic exception handling, file writing) is available in the implementation environment
- The system assumes valid, well-formed input from developers (natural language requests) and focuses on handling LLM output inconsistencies
- Memory operations are expected to be fast (in-memory storage) and failures are rare; basic error handling is sufficient for Sprint 1

## Dependencies

- LLM API access (OpenAI, Anthropic, or similar) for both main orchestration and supervisor
- JSON/YAML parsing library for plan and schema handling
- File system access for logging (JSONL file writing)
- Programming language runtime with basic I/O, data structures, and exception handling

## Out of Scope (Sprint 1)

The following capabilities are explicitly excluded from Sprint 1 and will be considered for future sprints:

- Diagram generation (network diagrams, architecture diagrams, flowcharts)
- Infrastructure as Code (IaC) generation (Terraform, CloudFormation, etc.)
- Cloud-specific integrations (Azure, AWS, GCP APIs)
- Pattern libraries or advanced pattern matching
- RAG (Retrieval Augmented Generation) systems
- Embeddings and vector search
- Advanced memory features (ranking, semantic search, embeddings-based retrieval)
- Multi-agent orchestration or concurrent agent execution
- State persistence to disk (optional in Sprint 2)
- Advanced error recovery beyond supervisor-based JSON repair
- Tool discovery or automatic tool generation
- Plan optimization or automatic plan improvement
