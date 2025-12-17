# Feature Specification: Memory Foundations

**Feature Branch**: `008-memory-foundations`  
**Created**: 2025-12-17  
**Status**: Draft  
**Input**: User description: "You are generating a specification for Sprint 8: 'Memory Foundations'. This sprint introduces Short-Term Memory (STM) only. STM is ephemeral, bounded, and scoped to a single Aeon session. A session may contain multiple executions (turns). STM is never persisted, promoted, or written to disk. Long-Term Memory (LTM), embeddings, persistence layers, and cross-session recall are explicitly out of scope."

## Clarifications

_No clarifications requested at this time._

## Terminology

The following terms are used consistently throughout this specification:

- **Session**: An in-memory, ephemeral context that may encompass one or more executions (turns). Sessions are requested by the host layer (CLI, FastAPI, UI, notebook). A session_id is issued by a dedicated Session subsystem. Sessions define the lifetime boundary for STM. Session data is never persisted and never survives process restart.

- **Execution (Turn)**: A single invocation of the Aeon reasoning engine spanning Phases A–E.

- **Pass**: One traversal of Phases A–D prior to convergence.

- **Session States**:
  - **active**: Session is currently active and available for operations
  - **expired**: Session has exhausted its TTL (Time-To-Live) and is no longer available for new operations
  - **closed/terminated**: Session has been gracefully closed by client/presentation request or host-defined termination policy before TTL expiration. This state represents intentional shutdown with cleanup, distinct from TTL expiration.

- **Autonomous Subsystem Architecture**: Session subsystem and STM are autonomous subsystems that manage their own TTL lifecycle independently. They do not observe wall-clock time but manage TTLs based on access patterns and execution events. Subsystems autonomously detect expiration, manage cleanup, and notify the orchestrator through interface responses. The orchestrator uses subsystem interfaces but has no knowledge of TTL internals, decrement logic, or expiration detection mechanisms.

- **TTL Types and Scopes** (CRITICAL DISTINCTION):
  - **Execution TTL (TaskProfile TTL)**: Orchestrator-level TTL that controls how many passes (LLM cycles) a single execution (turn) may perform. Decrements after each LLM cycle (pass boundary). When exhausted, the execution terminates gracefully. This TTL is managed by the orchestrator and is OUT OF SCOPE for this specification (defined in spec 001-aeon-core).
  - **Session TTL**: Session-level TTL that controls the lifetime of a session across potentially multiple executions (turns). Initial value: 3 (configurable static variable in Session subsystem). Decrements when orchestrator notifies Session subsystem that an execution completed (Phase E). Managed autonomously by Session subsystem. When exhausted, Session subsystem marks session as expired, cleans up session_id internally, and returns expired status to orchestrator. Orchestrator has no knowledge of Session TTL internals.
  - **Memory Entry TTL**: Individual memory entry TTL that controls how long a specific memory entry remains available for prompt injection. Initial value: 10 (configurable static variable in STM). Each entry has its own TTL value assigned by STM when created. Decrements autonomously by STM whenever STM is accessed (read, write, select operations) for that session_id - all entries for the session are decremented to preserve recency bias. STM has no concept of execution boundaries. When exhausted (TTL ≤ 0), STM autonomously excludes entries from query results and removes them from physical memory. Managed autonomously by STM, independent of session and execution TTLs. Orchestrator has no knowledge of Memory Entry TTL internals.

**Key Distinctions**:
- Execution TTL decrements on **pass boundaries** (LLM cycles), Session TTL decrements on **execution completion notification**, Memory Entry TTL decrements on **STM access** (any read/write/select operation)
- Execution TTL controls execution duration, Session TTL controls session duration, Memory Entry TTL controls individual entry relevance
- Session and Memory Entry TTLs are managed autonomously by their respective subsystems; orchestrator has no knowledge of TTL internals
- These TTLs operate independently and have different scopes, purposes, and decrement triggers

Memory lifetime is session-scoped, NOT execution-scoped.

- **Memory Ingest/Emit Asymmetry (CRITICAL)**: `write_entry()` ingests raw, phase-native execution artifacts, while `select_for_injection()` emits a deterministic, field-extracted contextual projection suitable for prompt injection, without semantic summarization, inference, or rewriting. STM performs field extraction, ordering, and light formatting only. STM MUST NOT perform semantic summarization, paraphrasing, inference, or rewriting at any stage.

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Session Lifecycle Management (Priority: P1)

As a developer using Aeon, I can create and manage sessions that provide unique identifiers and lifecycle boundaries, enabling the system to scope memory operations and coordinate execution across multiple turns within a single session context.

**Why this priority**: The Session subsystem is foundational infrastructure required before any session-scoped memory operations can function. Without session management, memory cannot be properly scoped, and the system cannot coordinate execution boundaries. This must be implemented before User Story 1 (Session-Scoped Memory Storage) can be realized.

**Independent Test**: Can be fully tested by requesting a new session, receiving a unique session_id, verifying session state tracking (active/expired/closed), enforcing session termination policies, and verifying session validity checks are exposed to the orchestrator. The test delivers value by proving the system can manage session lifecycles independently of memory operations.

**Acceptance Scenarios**:

1. **Given** a host layer requests a new session, **When** the Session subsystem processes the request, **Then** it issues a unique session_id that has not been used before
2. **Given** a session is created, **When** the Session subsystem tracks its state, **Then** the session state is correctly maintained as active, expired (TTL exhausted), or closed/terminated (client/presentation request)
3. **Given** a session exists, **When** host-defined termination policies are triggered, **Then** the Session subsystem enforces session termination
4. **Given** an orchestrator needs to validate a session, **When** it queries the Session subsystem, **Then** session validity checks are exposed and return accurate state information
5. **Given** the Session subsystem operates, **When** memory operations occur, **Then** the Session subsystem does not store memory, own STM, or depend on kernel internals
6. **Given** the Session subsystem operates, **When** system state is examined, **Then** the Session subsystem is in-memory only with no persistence operations
7. **Given** multiple sessions exist in the system, **When** the orchestrator requests a list of current sessions for audit, **Then** the Session subsystem returns a list of all active, expired, and closed sessions with their session_id and state information
8. **Given** a session exists (active or expired), **When** the orchestrator requests session closure due to presentation/client request or host-defined termination policy, **Then** the Session subsystem gracefully closes/terminates the session and releases all associated resources
9. **Given** a session's TTL is exhausted, **When** the orchestrator notifies Session subsystem that execution completed, **Then** Session subsystem autonomously detects expiration, marks the session as expired, cleans up session_id internally, and returns expired status to orchestrator
10. **Given** a session is closed/terminated, **When** the orchestrator queries the Session subsystem, **Then** the closed session is no longer accessible and does not appear in active session lists

---

### User Story 1 - Session-Scoped Memory Storage (Priority: P1)

As a developer using Aeon, I can store and retrieve contextual information within a session that persists across multiple executions (turns), enabling the system to maintain conversation context and build upon previous interactions without requiring explicit re-statement of information.

**Why this priority**: This is the foundational capability that enables all memory-related functionality. Without session-scoped storage, memory cannot provide value across multiple turns. It represents the entry point for all memory operations and is required before implementing memory retrieval, eviction, or prompt injection.

**Independent Test**: Can be fully tested by creating a session, storing memory entries across multiple executions, and verifying that entries from earlier executions are accessible in later executions within the same session. The test delivers value by proving the system can maintain context across turns without persistence.

**Acceptance Scenarios**:

1. **Given** a session is active, **When** memory entries are written during execution 1, **Then** those entries are accessible during execution 2 within the same session
2. **Given** a session is active, **When** memory entries are written with session_id, execution_id, and phase annotations, **Then** entries are correctly tagged with their origin context
3. **Given** memory entries exist in a session, **When** the session terminates, **Then** all memory entries are garbage-collectable and never written to disk
4. **Given** memory operations fail (read/write/validation), **When** execution continues, **Then** execution proceeds normally with memory failures logged but not blocking execution
5. **Given** memory entries exist in a session, **When** the orchestrator requests a list of current memory entries for audit, **Then** STM returns a list of all memory entries (with structural metadata only, no raw content) associated with the session
6. **Given** memory entries exist in a session, **When** the orchestrator requests deletion/removal of memory entries due to session closure (presentation/client request or termination policy), **Then** STM gracefully removes all memory entries associated with the session and releases associated resources
7. **Given** a session's TTL is exhausted and Session subsystem returns expired status, **When** the orchestrator receives expired status and requests STM cleanup, **Then** STM removes all memory entries associated with the expired session and releases associated resources
8. **Given** memory entries have been deleted/removed, **When** the orchestrator queries STM, **Then** the deleted entries are no longer accessible and do not appear in memory query results

---

### User Story 2 - Bounded Memory with Deterministic Eviction (Priority: P1)

As a developer using Aeon, I can rely on memory that respects both capacity limits and temporal bounds, ensuring memory usage remains predictable and bounded even during long-running sessions with many executions.

**Why this priority**: Memory bounds prevent unbounded growth and ensure system stability. Both capacity and TTL eviction must work together to maintain predictable behavior. This is essential for preventing resource exhaustion and ensuring deterministic memory behavior.

**Independent Test**: Can be fully tested by writing memory entries until capacity is exceeded, then verifying that eviction occurs deterministically according to defined rules. Similarly, by writing entries and advancing session progress (execution boundaries), verifying that TTL-based eviction occurs correctly. The test delivers value by proving memory remains bounded under all conditions.

**Acceptance Scenarios**:

1. **Given** memory is at capacity, **When** a new entry is written, **Then** the system performs deterministic soft eviction to make space
2. **Given** memory entries have TTL values, **When** the orchestrator accesses STM (read, write, select operations), **Then** STM autonomously decrements TTL values for all entries in that session to preserve recency bias
3. **Given** memory entries have expired TTL (reached zero), **When** memory is queried, **Then** expired entries are excluded from results
4. **Given** both capacity and TTL eviction apply, **When** eviction occurs, **Then** the system respects both bounds simultaneously
5. **Given** eviction occurs, **When** memory operations continue, **Then** eviction is transparent to execution (no exceptions, graceful degradation)

---

### User Story 3 - Memory-Aware Prompt Injection (Priority: P2)

As a developer using Aeon, I can configure prompts to optionally include relevant memory entries as contextual information, enabling the LLM to leverage previous session context when generating responses, while maintaining strict bounds on injection size and explicit opt-in behavior.

**Why this priority**: Memory only provides value if it can influence LLM reasoning. However, prompt injection must be explicit, bounded, and opt-in to maintain safety and predictability. This capability enables memory to enhance reasoning without compromising system control.

**Independent Test**: Can be fully tested by configuring a prompt to use memory injection, writing memory entries, and verifying that selected entries are injected into the prompt within the defined injection budget. The test delivers value by proving memory can enhance LLM reasoning while respecting safety constraints.

**Acceptance Scenarios**:

1. **Given** a prompt is configured for memory injection, **When** the prompt is rendered, **Then** relevant memory entries are selected and injected within the injection budget
2. **Given** memory injection is configured, **When** no relevant entries exist, **Then** the prompt renders without memory content (no errors, no empty sections)
3. **Given** memory entries exceed the injection budget, **When** injection occurs, **Then** entries are selected in order until the budget is exhausted, with remaining entries excluded (no truncation of individual entries)
4. **Given** memory injection fails (selection failure, validation failure), **When** prompt rendering continues, **Then** the prompt renders without memory content and execution proceeds normally
5. **Given** memory injection is not configured for a prompt, **When** the prompt is rendered, **Then** no memory content is included (explicit opt-in enforced)

---

### User Story 4 - Memory Usage Observability (Priority: P2)

As a developer debugging or monitoring Aeon, I can observe memory usage patterns through logs and Phase E metadata, enabling me to understand how memory is being used without exposing sensitive content.

**Why this priority**: Observability is essential for debugging and understanding system behavior. However, content-free observability maintains privacy and prevents log bloat. This capability enables developers to verify memory is working correctly without compromising safety guarantees.

**Independent Test**: Can be fully tested by performing memory operations and verifying that logs contain structural metadata (counts, operation types, session/execution IDs) but no raw content. Similarly, by verifying Phase E metadata includes memory usage statistics. The test delivers value by proving memory operations are observable without content exposure.

**Acceptance Scenarios**:

1. **Given** memory operations occur during execution, **When** logs are examined, **Then** logs contain structural metadata (operation type, entry count, session_id, execution_id) but no raw memory content
2. **Given** execution completes, **When** Phase E metadata is examined, **Then** metadata includes memory usage statistics (memory_used: bool, memory_entries_considered: int, memory_entries_injected: int, memory_failures: int)
3. **Given** memory failures occur, **When** logs are examined, **Then** failures are logged with error types and context but no content
4. **Given** memory operations succeed, **When** logs are examined, **Then** success is indicated with counts and metadata but no content

---

### Edge Cases

- What happens when memory capacity is zero? (Answer: All write operations degrade silently, reads return empty results, execution continues normally)
- What happens when TTL decrement logic fails? (Answer: TTL decrement failures are logged, entries are treated as expired, execution continues)
- What happens when memory selection for injection fails? (Answer: Injection degrades silently, prompt renders without memory, execution continues)
- What happens when memory validation fails during write? (Answer: Write operation degrades silently, entry is not stored, failure is logged, execution continues)
- What happens when session_id is missing or invalid? (Answer: Memory operations degrade silently, no entries are stored/retrieved, failure is logged)
- What happens when memory injection budget is zero? (Answer: No entries are injected, prompt renders without memory, execution continues normally)
- What happens when multiple phases attempt to write memory simultaneously? (Answer: Memory interface handles concurrency safely, writes are atomic, no data corruption)
- What happens when memory read operations timeout or hang? (Answer: Read operations have timeout protection, failures degrade silently, execution continues)
- How does the system handle memory entries with malformed annotations (missing phase, invalid execution_id)? (Answer: Validation rejects malformed entries, write degrades silently, failure is logged)
- When does the orchestrator create memory entries? (Answer: After LLM response for Phase A (Plan Generation, TaskProfile Inference), Phase B (Reasoning Steps), and Phase D (Recursive Planning/Refinement). For Phase C, metadata only after each response. Phase E does not create memory entries by default.)
- What does STM return from select_for_injection()? (Answer: Structured JSON with context_blocks (List[str]) containing formatted context strings and non_authoritative_marker (str) for marking context as optional. STM performs field extraction and ordering only, no semantic summarization.)
- How does STM craft context for different phases? (Answer: STM extracts phase-appropriate fields deterministically. Phase B gets prior user statements and assistant responses. Phase D gets refinement reasons and updated goals/steps. Phase A rarely uses memory. Phase C and E never inject memory.)
- What happens when memory storage structure becomes corrupted? (Answer: Memory interface detects corruption, operations degrade gracefully, execution continues with NullMemory-like behavior)
- What happens when the orchestrator requests a list of sessions but no sessions exist? (Answer: Session subsystem returns empty list, operation succeeds, execution continues)
- What happens when the orchestrator requests to close a session that does not exist? (Answer: Session subsystem returns failure result, operation degrades gracefully, execution continues)
- What happens when Session subsystem detects expiration while orchestrator is accessing STM? (Answer: Session subsystem marks session as expired and returns expired status when orchestrator notifies execution completion. Orchestrator receives expired status and requests STM cleanup. STM completes in-progress operations and then releases all memory entries when cleanup is requested, no data corruption)
- What happens when the orchestrator requests graceful closure for a session while memory operations are in progress? (Answer: Session subsystem marks session as closed when requested, STM completes in-progress operations and then releases all memory entries when cleanup is requested, no data corruption)
- How does Memory Entry TTL decrement work? (Answer: STM autonomously decrements Memory Entry TTL for all entries in a session_id whenever STM is accessed (read, write, select operations) for that session. This preserves recency bias - newer entries have higher TTLs than older entries. STM has no concept of execution boundaries and decrements based solely on access patterns. Orchestrator has no knowledge of TTL decrement logic. Initial TTL value is 10, configurable in STM.)
- How do the different TTL types relate? (Answer: Execution TTL (TaskProfile TTL) controls pass limits within a single execution and decrements on pass boundaries, managed by orchestrator. Session TTL controls session lifetime across multiple executions, initial value 3, decrements when orchestrator notifies Session subsystem of execution completion, managed autonomously by Session subsystem. Memory Entry TTL controls individual entry relevance, initial value 10, decrements autonomously by STM on STM access, managed autonomously by STM. These operate independently with different scopes, purposes, and decrement triggers. Orchestrator has no knowledge of Session or Memory Entry TTL internals.)
- What happens when the orchestrator requests a list of memory entries for a non-existent session? (Answer: STM returns empty list, operation succeeds, execution continues)
- What happens when the orchestrator requests deletion of memory entries for a session that has no entries? (Answer: STM returns success with entries_removed=0, operation succeeds, execution continues)
- What happens when session closure is requested while memory operations are in progress? (Answer: Session subsystem and STM handle concurrent operations safely, closure completes after in-progress operations, no data corruption)

## Requirements *(mandatory)*

### Implementation Restrictions

**CRITICAL**: Cursor (or any AI assistant implementing this specification) MUST NOT infer requirements, data structures, or implementation details that are not explicitly defined in this specification. If clarification is needed on any aspect of implementation, Cursor MUST request clarification rather than inferring a solution.

**CRITICAL**: Cursor MUST NOT infer internal engine structures (e.g., OrchestrationEngine internal state, execution pass structures, phase transition mechanics) that are not explicitly documented in this specification. Only the following are explicitly defined:
- Memory Access Interface (MAI) contract (defined in Key Entities section)
- Short-Term Memory (STM) behavior requirements (defined in Functional Requirements)
- Memory entry structure (defined in Key Entities section)
- Prompt injection integration points (defined in Functional Requirements)
- Phase E metadata structure (defined in Functional Requirements)

Any other internal structures, state management, or engine internals MUST be obtained from existing codebase inspection or explicit documentation, NOT inferred.

### Functional Requirements

#### Memory Access Interface (MAI) (P1)

- **FR-001**: System MUST provide a Memory Access Interface (MAI) that abstracts all memory operations behind a replaceable interface
- **FR-002**: System MUST support a NullMemory implementation that provides no-op behavior (all operations succeed but store/retrieve nothing)
- **FR-003**: System MUST ensure kernel execution remains valid with NullMemory implementation (no kernel dependencies on memory functionality)
- **FR-004**: All memory operations (read, write, search, select) MUST be accessed exclusively through the MAI
- **FR-005**: MAI MUST support graceful degradation: all operations MUST NOT raise exceptions that block execution
- **FR-006**: MAI operations MUST return structured results indicating success/failure without throwing exceptions
- **FR-007**: MAI MUST support session-scoped operations: all memory entries MUST be associated with a session_id
- **FR-008**: MAI MUST support execution-scoped annotations: memory entries MUST be annotated with execution_id and phase

#### Short-Term Memory (STM) Storage (P1)

- **FR-009**: System MUST implement Short-Term Memory (STM) that stores structured memory entries in-memory only
- **FR-010**: STM MUST NEVER write content to disk under any circumstance (including serialization for persistence, logging of content, or accidental file I/O)
- **FR-011**: STM MUST exist only in-process and be garbage-collectable at session termination
- **FR-012**: STM MUST store memory entries with the following required annotations:
  - session_id (string, required): Identifies the session owning the entry
  - execution_id (string, required): Identifies the execution (turn) that created the entry (used for recency ordering across executions)
  - phase (string, required): Identifies the phase (A, B, C, D, E) that created the entry (essential for phase-aware context crafting)
- **FR-013**: STM MUST support storing structured data (JSON-compatible) as memory entry content. Content structure MUST be phase-aware but use a uniform, JSON-compatible shape across phases.
- **FR-014**: STM MUST validate memory entries before storage (required annotations present, content serializable, phase-appropriate structure)
- **FR-015**: STM validation failures MUST degrade silently (entry not stored, failure logged, execution continues)
- **FR-126**: `write_entry()` MUST ingest raw, phase-native execution artifacts. STM MUST NOT pre-summarize, paraphrase, infer, or rewrite content at ingest time. STM decides later what to extract during `select_for_injection()`.
- **FR-127**: Memory creation triggers: Orchestrator MUST call `write_entry()` after LLM response for Phase A (Plan Generation, TaskProfile Inference), Phase B (Reasoning Steps), and Phase D (Recursive Planning/Refinement). For Phase C (Validation/Convergence), orchestrator MUST call `write_entry()` with metadata only after each response. Phase E (Answer Synthesis) MUST NOT create memory entries by default.
- **FR-128**: Phase-specific memory content ingestion rules (what to ingest, not exact structure):
  - **Phase A - Plan Generation**: Ingest plan goal and step descriptions only. DO NOT ingest step status, tool bindings, or full plan JSON.
  - **Phase A - TaskProfile Inference**: Ingest full TaskProfile inference output.
  - **Phase B - Reasoning Steps**: Ingest rendered user prompt (or key fields: user request, step description) and full LLM response text (verbatim). DO NOT ingest memory_context that was injected or internal orchestration metadata.
  - **Phase C - Validation/Convergence**: Ingest metadata only: convergence status, detected issues, reason codes, completeness score, coherence score. DO NOT ingest full validation artifacts, validator reasoning, or raw plan dumps.
  - **Phase D - Recursive Planning/Refinement**: Ingest refinement reason, updated goal, updated step descriptions. DO NOT ingest full recursive plan JSON or internal action details.
  - **Phase E - Answer Synthesis**: DO NOT ingest by default.

#### Memory Bounds and Eviction (P1)

- **FR-016**: STM MUST enforce a fixed, deterministic capacity limit (e.g., maximum number of entries or equivalent structural limit)
- **FR-017**: When capacity is exceeded, STM MUST perform deterministic soft eviction (eviction algorithm must be deterministic, not random)
- **FR-017A**: Deterministic eviction means that given the same sequence of memory writes, reads, and configuration values, STM will always evict the same memory entries in the same order. Eviction algorithm MUST produce identical results for identical input states (same entries, same capacity, same TTL states).
- **FR-018**: STM MUST support session-relative Memory Entry TTL (Time-To-Live) for each memory entry. This is distinct from Session TTL (session lifetime) and Execution TTL (TaskProfile TTL, pass limit).
- **FR-019**: Memory Entry TTL initial value MUST be 10 (configurable static variable in STM). TTL MUST be assigned by STM when creating new entries, not inferred or provided by callers. Orchestrator has no knowledge of TTL values or assignment logic.
- **FR-020**: TTL represents diminishing contextual relevance within a session (NOT semantic correctness, truth decay, or factual invalidation)
- **FR-021**: Memory Entry TTL MUST decrement autonomously by STM whenever STM is accessed (read, write, select operations) for a session_id. All memory entries for that session_id MUST be decremented to preserve recency bias (newer entries have higher TTLs than older entries). STM has no concept of execution boundaries and decrements based solely on access patterns. TTL decrement is transparent to the orchestrator.
- **FR-022**: Memory Entry TTL decrement MUST be performed autonomously by STM during any STM operation (read_entries, write_entry, select_for_injection) for a session_id. Orchestrator MUST NOT request TTL decrement and has no knowledge of TTL decrement logic. STM does not observe wall-clock time but manages TTL based on access patterns.
- **FR-023**: TTL expiration removes entries from STM eligibility (excluded from read and search operations)
- **FR-024**: STM MUST autonomously exclude expired entries (TTL reached zero) from all read and search operations. This filtering is performed by STM internally without requiring orchestrator intervention.
- **FR-025**: STM MUST respect both capacity and TTL bounds simultaneously (eviction considers both factors)
- **FR-026**: Eviction operations MUST be transparent to execution (no exceptions, graceful degradation)

#### Memory Selection and Retrieval (P2)

- **FR-027**: STM MUST support querying memory entries by session_id (required) and optional filters (execution_id, phase)
- **FR-028**: STM entries written during an execution MAY be visible to later passes within the same execution if selected for relevance by the STM
- **FR-029**: The structure and semantics of the memory selection context are owned and defined by the Short-Term Memory (STM) subsystem via the Memory Access Interface (MAI)
- **FR-030**: STM defines the schema for the memory selection context; the kernel (orchestrator) fills in only known execution facts required by that schema. Context parameter MUST include: `current_phase` (required), `current_execution_id` (optional, for excluding current execution), `injection_point` (required). Orchestrator MUST NOT supply task profile, plan state, validation results, or tool registry info.
- **FR-031**: Orchestrator MUST supply only raw execution facts required by the MAI interface for memory selection context
- **FR-032**: Orchestrator MUST NOT interpret, enrich, or apply policy to the memory selection context
- **FR-033**: STM MUST support relevance-based selection for prompt injection (selection algorithm must be deterministic)
- **FR-034**: Within this sprint, relevance is defined as deterministic contextual proximity, not semantic importance. Recency is the dominant signal. No semantic scoring or importance ranking.
- **FR-035**: STM MUST determine relevance using only: session scope, context metadata, and recency (creation order / TTL state). "Relevant" means: same session_id, most recent executions first, phase-appropriate.
- **FR-036**: STM MUST NOT perform semantic analysis or inference when determining relevance
- **FR-037**: `select_for_injection()` MUST emit a deterministic, field-extracted contextual projection suitable for prompt injection, NOT raw MemoryEntry objects. STM MUST perform field extraction, ordering, and light formatting only. STM MUST NOT perform semantic summarization, inference, or rewriting.
- **FR-129**: When `select_for_injection()` is invoked, STM MUST exclude expired entries (TTL ≤ 0) before selection
- **FR-129A**: STM MUST filter entries by session_id and phase matching. STM MUST prefer entries whose phase matches the current context phase. For Phase B: STM MUST prefer Phase B entries (primary), Phase D entries if recent (secondary). For Phase D: STM MUST prefer Phase D entries (primary), Phase B entries (secondary). For Phase A: STM MAY use Phase A entries (rare, optional). For Phase C and Phase E: STM MUST NEVER inject memory.
- **FR-129B**: STM MUST prefer entries from earlier executions over the current execution (if current_execution_id is provided in context)
- **FR-129C**: STM MUST order selected entries by recency (created_at, most recent first) with insertion order as stable tie-breaker
- **FR-129D**: STM MUST extract phase-appropriate fields from selected entries deterministically. For Phase B: Extract prior user statements (short), prior assistant response text (trimmed, verbatim), optional recent refinement reason. DO NOT extract plan JSON, task profile numeric fields, or validation artifacts. For Phase D: Extract refinement reason, updated goal, updated step descriptions, optionally most recent explanation text. For Phase A: Extract goal, task profile posture fields (reasoning_depth, output_breadth, confidence_requirement) if applicable.
- **FR-129E**: STM MUST apply injection budget as hard upper bound. Context blocks MUST be included in order until the injection budget is exhausted. Context blocks that would exceed the remaining budget MUST be skipped (no partial inclusion).
- **FR-130**: `select_for_injection()` MUST return a structured JSON object with the following structure:
  - `context_blocks` (List[str], required): List of formatted context strings/blocks ready for prompt injection
  - `non_authoritative_marker` (str, required): Single header/footer wrapper text marking the context as non-authoritative (e.g., "Non-authoritative context from this session (for reference only)")
- **FR-131**: STM MUST NOT perform semantic summarization, paraphrasing, inference, or rewriting when crafting context blocks. STM MUST only extract and present selected fields from prior execution artifacts deterministically.
- **FR-131A**: Light formatting refers to deterministic, presentation-only transformation that improves readability for prompt injection without altering content, meaning, or intent. Light formatting MUST include only: string concatenation, basic punctuation, line breaks, and field extraction. Light formatting MUST NOT include: semantic transformation, summarization, paraphrasing, inference, rewriting, or any LLM-based processing.
- **FR-132**: Prompt registry MUST insert STM context at defined injection points. STM returns render-ready content; prompt registry is responsible for formatting and inserting that content into prompt templates. STM MUST NOT be aware of prompt structure.
- **FR-038**: Memory selection failures MUST degrade silently (empty result set returned with empty context_blocks, failure logged, execution continues)
- **FR-039**: STM search operations MUST autonomously exclude expired entries (TTL-based filtering). This filtering is performed by STM internally without requiring orchestrator intervention.

#### Prompt Integration and Injection (P2)

- **FR-040**: Memory injection MUST only flow into LLM prompts through explicit, named, opt-in injection points in the prompt registry
- **FR-041**: Memory injection MUST be additive and bounded by an explicit injection budget (size or token-bound), independent of storage capacity
- **FR-042**: Memory injection MUST NOT be silently appended outside the prompt registry
- **FR-043**: Memory injection MUST NOT be injected into system prompts unless explicitly specified
- **FR-044**: Memory injection MUST NOT be injected into tool calls or non-LLM execution paths
- **FR-045**: Prompt registry MUST support configuring memory injection per prompt (opt-in behavior)
- **FR-046**: When memory injection is configured, prompt registry MUST call `select_for_injection()` and format/insert the returned context blocks into prompt templates. Prompt registry MUST apply the non-authoritative marker to ensure memory context is clearly marked as optional, non-authoritative context.
- **FR-047**: Memory injection failures (selection failure, budget exceeded, validation failure) MUST degrade silently (prompt renders without memory, execution continues)
- **FR-133**: Memory injection MUST be explicitly disabled for Phase C (Validation/Convergence) and Phase E (Answer Synthesis). Memory MUST NOT be injected into these phases under any circumstance.

#### Memory Safety Constraints (NON-NEGOTIABLE)

**Contract Protection (Non-Authoritative Memory)**:

- **FR-048**: Memory (STM/MAI) MUST be strictly observational and MUST NOT be treated as ground truth, instructions, or policy
- **FR-049**: Memory content MUST NOT override: user request, plan goal, step descriptions, tool outputs, convergence decisions, or validation decisions
- **FR-050**: Any component consuming memory MUST treat it as untrusted input, equivalent to user-provided text
- **FR-051**: Memory MUST NOT introduce instructions, tool invocations, or control-flow directives
- **FR-134**: Memory context injected into prompts MUST be clearly marked as non-authoritative using a single header/footer wrapper. The non-authoritative marker MUST be applied by the prompt registry when inserting STM context. The marker MUST clearly indicate that memory is optional context for reference only and must not be treated as authoritative.

**Routing Protection (Quarantined Injection)**:

- **FR-052**: Memory MUST only flow into LLM prompts through explicit, named, opt-in injection points
- **FR-053**: Memory injection MUST be bounded (size, selection, and ordering rules)
- **FR-054**: Memory MUST NOT be silently appended outside the prompt registry
- **FR-055**: Memory MUST NOT be injected into tool calls or non-LLM execution paths

**Interpretation Protection (Visibility Without Authority)**:

- **FR-056**: System MUST surface memory usage as metadata in Phase E (not content, only usage statistics)
- **FR-057**: Phase E metadata MUST include: memory_used (bool), memory_entries_considered (int), memory_entries_injected (int), memory_failures (int)
- **FR-058**: If memory operations fail, execution MUST continue (failures observable via logs and metadata, not exceptions)

**No-Disk Guarantee (Strict Ephemeral Storage)**:

- **FR-059**: STM MUST NEVER write content to disk under any circumstance
- **FR-060**: STM MUST exist only in-process and be garbage-collectable at session termination
- **FR-061**: In-memory serialization for validation is allowed (e.g., JSON-compatibility checks), but persistence is prohibited
- **FR-062**: Logs MUST be content-free with respect to memory: no raw memory content, no step_output echoes, no stored user text; only structural metadata and counters are permitted

#### Observability and Logging (P2)

- **FR-063**: Memory operations MUST be logged with structural metadata (operation type, entry count, session_id, execution_id, phase) but NO raw content
- **FR-064**: Memory failures MUST be logged with error types and context but NO content
- **FR-065**: Phase E MUST include memory usage metadata in the final answer metadata structure
- **FR-066**: Memory usage metadata MUST be content-free (counts and flags only, never content)

#### Session Subsystem (P1)

- **FR-067**: System MUST provide a Session subsystem that manages session lifecycle independently of STM
- **FR-068**: Session subsystem MUST issue unique session_id values for new sessions
- **FR-069**: Session subsystem MUST track session state (active / expired / closed). "expired" indicates Session TTL exhaustion (session lifetime exceeded), while "closed/terminated" indicates graceful shutdown via client/presentation request or termination policy before Session TTL expiration. Session TTL is distinct from Execution TTL (TaskProfile TTL) and Memory Entry TTL. Session subsystem MUST manage Session TTL autonomously.
- **FR-120**: Session TTL initial value MUST be 3 (configurable static variable in Session subsystem). Session subsystem MUST assign initial TTL when creating new sessions. Orchestrator has no knowledge of Session TTL values or assignment logic.
- **FR-121**: Session subsystem MUST support orchestrator notifying it when an execution completes (Phase E). When notified, Session subsystem MUST autonomously decrement Session TTL for that session_id.
- **FR-122**: Session subsystem MUST autonomously detect when Session TTL is exhausted (reaches zero). When Session TTL is exhausted, Session subsystem MUST mark session as expired, clean up session_id internally, and return expired status in the response to orchestrator. Orchestrator has no knowledge of Session TTL exhaustion detection logic.
- **FR-070**: Session subsystem MUST enforce session termination based on host-defined policies
- **FR-071**: Session subsystem MUST expose session validity checks to the orchestrator
- **FR-072**: Session subsystem MUST NOT store memory
- **FR-073**: Session subsystem MUST NOT own STM
- **FR-074**: Session subsystem MUST NOT depend on kernel internals
- **FR-075**: Session subsystem MUST be in-memory only
- **FR-076**: Session subsystem persistence is prohibited
- **FR-104**: Session subsystem MUST support the orchestrator requesting a list of all current sessions (active, expired, and closed) for audit purposes
- **FR-105**: Session subsystem list operations MUST return session metadata (session_id, state, creation time) but MUST NOT expose internal implementation details
- **FR-106**: Session subsystem MUST support the orchestrator gracefully closing/terminating sessions when triggered by presentation/client requests or host-defined termination policies (before TTL expiration)
- **FR-107**: When a session is gracefully closed/terminated (via FR-106), Session subsystem MUST release all associated resources and mark the session as no longer accessible
- **FR-108**: Session subsystem close/terminate operations MUST degrade gracefully (no exceptions that block execution) and MUST return structured results indicating success/failure
- **FR-123**: When Session subsystem detects Session TTL exhaustion and marks session as expired, it MUST return expired status in the response to orchestrator's execution completion notification. The response MUST include session state information indicating the session is expired.
- **FR-124**: When orchestrator receives expired session status from Session subsystem, orchestrator MUST immediately request STM to delete all memory entries for that session_id via `delete_session_entries(session_id)`. This cleanup is triggered by orchestrator based on Session subsystem response, not by orchestrator's knowledge of TTL state.

#### Session Integration (P1)

- **FR-077**: STM MUST NOT generate, manage, or terminate sessions
- **FR-078**: STM MUST NOT own or define session lifecycle behavior (sessions are owned by Session subsystem, not STM)
- **FR-079**: STM REQUIRES a valid session_id for all operations
- **FR-080**: STM entries MUST be associated with exactly one session_id
- **FR-081**: STM lifetime is bounded by session lifetime
- **FR-082**: STM MUST release all memory associated with a session when notified of session termination
- **FR-083**: STM MUST NOT manage session lifecycle logic
- **FR-084**: Orchestrator mediates between Session subsystem and STM
- **FR-085**: Orchestrator supplies session_id to STM
- **FR-086**: Orchestrator requests operations from subsystems through their interfaces but has no knowledge of subsystem internals (TTL values, decrement logic, expiration detection). Subsystems manage their own TTL lifecycle autonomously.
- **FR-125**: Orchestrator MUST NOT track, decrement, or detect TTL expiration for Session or Memory Entry TTLs. Orchestrator MUST NOT request TTL decrements from subsystems. TTL management is the exclusive responsibility of each subsystem.
- **FR-087**: STM autonomously excludes expired entries (TTL ≤ 0) from all query results (read, search, select operations). STM MUST autonomously remove expired entries from physical memory for security and resource management reasons. STM manages its own TTL-based cleanup without requiring orchestrator intervention. STM does not observe wall-clock time, proactively monitor expiration, or define session expiration.
- **FR-088**: STM MUST support multiple executions (turns) within a single session
- **FR-089**: Memory lifetime MUST be session-scoped, not execution-scoped (entries persist across executions within a session)
- **FR-109**: STM MUST support the orchestrator requesting a list of all current memory entries for a session for audit purposes
- **FR-110**: STM list operations MUST return memory entry metadata (session_id, execution_id, phase, created_at, ttl) but MUST NOT expose raw memory content
- **FR-111**: STM MUST support the orchestrator gracefully deleting/removing all memory entries associated with a session when the session is closed/terminated (via presentation/client request or termination policy, before TTL expiration)
- **FR-112**: When memory entries are deleted/removed due to graceful session closure, STM MUST release all associated resources and ensure deleted entries are no longer accessible through any memory operations
- **FR-113**: STM delete/remove operations MUST degrade gracefully (no exceptions that block execution) and MUST return structured results indicating success/failure and count of entries removed
- **FR-116**: STM MUST support the orchestrator deleting/removing all memory entries associated with a session when the orchestrator requests cleanup (triggered by Session subsystem returning expired status, or by client-requested session closure)
- **FR-117**: When the orchestrator requests cleanup of memory entries for a session (expired or closed), STM MUST release all associated resources and ensure deleted entries are no longer accessible through any memory operations

#### Integration & Testing

- **FR-090**: System MUST add tests proving memory cannot change plan, step, or tool decisions (non-authoritative constraint)
- **FR-091**: System MUST add tests proving memory only enters prompts via explicit injection points (routing protection)
- **FR-092**: System MUST add tests proving Phase E reports memory usage metadata (interpretation protection)
- **FR-093**: System MUST add tests proving STM performs no file I/O, including accidental serialization paths (no-disk guarantee)
- **FR-094**: System MUST add tests proving STM eviction obeys both capacity and TTL bounds deterministically
- **FR-095**: System MUST add tests proving STM functions correctly across multiple executions within a single session
- **FR-096**: System MUST ensure all phases (B/C/D/E) can operate with memory fully disabled (NullMemory)
- **FR-097**: System MUST ensure kernel receives no new business logic except wiring for memory access (kernel minimalism maintained)
- **FR-098**: System MUST add tests proving STM cannot operate without session_id
- **FR-099**: System MUST add tests proving session termination triggers STM cleanup
- **FR-100**: System MUST add tests proving multiple executions share STM within a session
- **FR-101**: System MUST add tests proving orchestrator functions with Session enabled but STM disabled
- **FR-102**: System MUST add tests proving STM functions correctly with Session enabled
- **FR-103**: System MUST add tests proving kernel logic remains unchanged

### Key Entities *(include if feature involves data)*

- **Memory Access Interface (MAI)**: Abstract interface defining all memory operations. Implementations include STM and NullMemory. Methods:
  - `write_entry(session_id: str, execution_id: str, phase: str, content: Dict[str, Any]) -> MemoryWriteResult`: Store a memory entry with annotations. Content MUST be phase-native, raw execution artifacts (no pre-summarization). STM assigns TTL using deterministic default from configuration. Returns result indicating success/failure without raising exceptions.
  - `read_entries(session_id: str, execution_id: Optional[str] = None, phase: Optional[str] = None) -> List[MemoryEntry]`: Retrieve memory entries matching filters. Returns empty list if no matches or on failure (never raises exceptions).
  - `select_for_injection(session_id: str, context: Dict[str, Any], budget: int) -> Dict[str, Any]`: Select relevant entries and emit a deterministic, field-extracted contextual projection for prompt injection. Context parameter MUST include: `current_phase` (required), `current_execution_id` (optional), `injection_point` (required). Returns structured JSON with `context_blocks` (List[str]) and `non_authoritative_marker` (str). Returns empty structure on failure (never raises exceptions). STM performs field extraction, ordering, and light formatting only - NO semantic summarization, inference, or rewriting.
  - `get_usage_stats(session_id: str) -> MemoryUsageStats`: Get memory usage statistics for observability. Returns stats with counts only, never content.
  - `list_entries(session_id: str) -> List[MemoryEntryMetadata]`: List all memory entries for a session for audit purposes. Returns metadata only (no raw content). Returns empty list on failure (never raises exceptions).
  - `delete_session_entries(session_id: str) -> MemoryDeleteResult`: Delete/remove all memory entries associated with a session. Returns result indicating success/failure and count of entries removed (never raises exceptions).

- **Short-Term Memory (STM)**: In-memory implementation of MAI that stores structured entries with capacity and TTL bounds. Behavior:
  - Stores entries in-memory only (never disk)
  - Enforces capacity limit with deterministic eviction
  - Assigns initial Memory Entry TTL value of 10 (configurable static variable) when creating new entries
  - Autonomously decrements Memory Entry TTL for all entries in a session_id whenever STM is accessed (read, write, select operations) to preserve recency bias
  - Has no concept of execution boundaries - TTL decrement is based solely on access patterns
  - Ingests raw, phase-native execution artifacts via `write_entry()` (no pre-summarization, paraphrasing, inference, or rewriting at ingest time)
  - Validates entries before storage (required annotations present, content serializable, phase-appropriate structure)
  - Autonomously excludes expired entries (TTL ≤ 0) from all query operations (read, search, select) without requiring orchestrator intervention
  - Autonomously removes expired entries from physical memory for security and resource management
  - Emits deterministic, field-extracted contextual projections via `select_for_injection()` (field extraction, ordering, light formatting only - NO semantic summarization, inference, or rewriting)
  - Orchestrator has no knowledge of TTL values, decrement logic, expiration detection, or context crafting internals
  - Garbage-collectable at session termination

- **NullMemory**: No-op implementation of MAI that provides empty behavior. Behavior:
  - All write operations succeed but store nothing
  - All read operations return empty results
  - All selection operations return empty results
  - Usage stats return zero counts
  - Enables execution with memory fully disabled

- **MemoryEntry**: Structured data representing a single memory entry. Fields:
  - `session_id` (str, required): Session owning the entry
  - `execution_id` (str, required): Execution (turn) that created the entry (used for recency ordering across executions)
  - `phase` (str, required): Phase (A, B, C, D, E) that created the entry (essential for phase-aware context crafting)
  - `content` (Dict[str, Any], required): Phase-native, raw execution artifacts (JSON-compatible, phase-aware structure). Content structure varies by phase but uses uniform JSON-compatible shape. Content MUST contain the phase-specific data as defined in FR-128 (plan goal and step descriptions for Phase A Plan Generation, full TaskProfile inference output for Phase A TaskProfile Inference, user request/step description/LLM response for Phase B, convergence metadata for Phase C, refinement reason/updated goal/step descriptions for Phase D).
  - `ttl` (int, required): Time-to-live (session-relative, decrements on STM access)
  - `created_at` (datetime, required): Entry creation timestamp (for eviction ordering and recency)

- **MemoryInjectionResult**: Result of `select_for_injection()` operation. Fields:
  - `context_blocks` (List[str], required): List of formatted context strings/blocks ready for prompt injection. Each block contains extracted, phase-appropriate fields from prior execution artifacts.
  - `non_authoritative_marker` (str, required): Single header/footer wrapper text marking the context as non-authoritative (e.g., "Non-authoritative context from this session (for reference only)"). Applied by prompt registry when inserting context.

- **MemoryWriteResult**: Result of a memory write operation. Fields:
  - `success` (bool, required): Whether write succeeded
  - `entry_id` (Optional[str]): Identifier of stored entry (if successful)
  - `evicted_count` (int, required): Number of entries evicted (if capacity exceeded)
  - `error` (Optional[str]): Error message (if failed, for logging only)

- **MemoryUsageStats**: Statistics about memory usage for observability. Fields:
  - `memory_used` (bool, required): Whether memory was used in this execution
  - `memory_entries_considered` (int, required): Number of entries considered for injection
  - `memory_entries_injected` (int, required): Number of entries actually injected
  - `memory_failures` (int, required): Number of memory operation failures
  - `total_entries` (int, required): Total entries in session (for debugging)
  - `expired_entries` (int, required): Number of expired entries (for debugging)

- **MemoryEntryMetadata**: Metadata about a memory entry for audit purposes (no raw content). Fields:
  - `session_id` (str, required): Session owning the entry
  - `execution_id` (str, required): Execution (turn) that created the entry
  - `phase` (str, required): Phase (A, B, C, D, E) that created the entry
  - `created_at` (datetime, required): Entry creation timestamp
  - `ttl` (int, required): Current TTL value

- **MemoryDeleteResult**: Result of a memory delete operation. Fields:
  - `success` (bool, required): Whether delete succeeded
  - `entries_removed` (int, required): Number of entries removed
  - `error` (Optional[str]): Error message (if failed, for logging only)

- **Session Subsystem**: Dedicated architectural component (not part of STM) that manages session lifecycle independently. Responsibilities:
  - Issues unique session_id values for new sessions
  - Assigns initial Session TTL value of 3 (configurable static variable) when creating new sessions
  - Tracks session state (active / expired / closed). "expired" indicates Session TTL exhaustion (session lifetime exceeded); "closed/terminated" indicates graceful shutdown via client/presentation request or termination policy before Session TTL expiration. Session TTL is distinct from Execution TTL (TaskProfile TTL) and Memory Entry TTL.
  - Autonomously manages Session TTL - decrements when orchestrator notifies that execution completed (Phase E)
  - Autonomously detects when Session TTL is exhausted and marks session as expired
  - When Session TTL is exhausted, cleans up session_id internally and returns expired status to orchestrator
  - Enforces session termination based on host-defined policies
  - Exposes session validity checks to the orchestrator
  - Supports orchestrator notifying it when execution completes (returns session state including expired status if applicable)
  - Supports listing all current sessions (active, expired, and closed) for audit purposes
  - Supports gracefully closing/terminating sessions when triggered by presentation/client requests or termination policies (before TTL expiration)
  - Orchestrator has no knowledge of Session TTL values, decrement logic, or expiration detection
  - Does NOT store memory
  - Does NOT own STM
  - Does NOT depend on kernel internals
  - Is in-memory only (persistence prohibited)
  - STM does NOT own or manage sessions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of memory operations are accessed exclusively through the MAI (verified by code review and automated detection of direct memory access)
- **SC-002**: Kernel execution remains valid with NullMemory implementation (verified by integration tests running full execution with NullMemory)
- **SC-003**: STM performs zero file I/O operations under all conditions (verified by automated tests monitoring file system access). In-memory serialization for validation is allowed (e.g., JSON-compatibility checks), but persistence is prohibited (FR-061)
- **SC-004**: Memory eviction obeys both capacity and TTL bounds deterministically (verified by automated tests with capacity exhaustion and TTL expiration scenarios). TTL support includes: STM assigns initial TTL value of 10 when creating entries (FR-018, FR-019), TTL decrements autonomously by STM whenever STM is accessed for a session_id (all entries decremented to preserve recency bias) (FR-021, FR-022), TTL expiration removes entries from eligibility and expired entries are autonomously excluded from all read and search operations and removed from physical memory (FR-023, FR-024, FR-087). STM manages TTL autonomously without orchestrator knowledge (FR-022, FR-125)
- **SC-005**: Memory injection only occurs through explicit, opt-in prompt registry injection points (verified by code review and automated detection of injection outside registry). Memory injection is bounded by an explicit injection budget that serves as a hard upper bound with no truncation of individual entries (FR-041, FR-037 step 5). Memory injection is not injected into system prompts unless explicitly specified (FR-043) and not injected into tool calls or non-LLM execution paths (FR-044). Prompt registry supports configuring memory injection per prompt (FR-045)
- **SC-006**: Phase E metadata includes memory usage statistics (memory_used, memory_entries_considered, memory_entries_injected, memory_failures) for 100% of executions (verified by integration tests)
- **SC-007**: Memory failures degrade silently without blocking execution (verified by tests injecting memory failures and verifying execution completion)
- **SC-008**: Memory entries persist across multiple executions within a single session (verified by integration tests writing entries in execution 1 and reading in execution 2). MAI supports session-scoped operations with all memory entries associated with a session_id (FR-007). STM entries written during an execution are visible to later passes within the same execution if selected for relevance (FR-028)
- **SC-009**: All memory safety constraints are enforced by automated tests (non-authoritative, routing protection, interpretation protection, no-disk guarantee)
- **SC-010**: Logs contain structural metadata but zero raw memory content (verified by automated log analysis)
- **SC-011**: All phases (B/C/D/E) operate correctly with memory fully disabled (NullMemory) (verified by integration tests)
- **SC-012**: Session subsystem issues unique session_id values with zero collisions across all session creation requests (verified by automated tests creating 10,000+ sessions and verifying uniqueness)
- **SC-013**: Session subsystem correctly tracks session state (active/expired/closed) for 100% of sessions, with clear distinction between "expired" (TTL exhausted) and "closed/terminated" (graceful shutdown via client/presentation request) (verified by integration tests creating sessions, transitioning states, and verifying state accuracy)
- **SC-014**: Session subsystem enforces termination policies for 100% of sessions meeting termination criteria (verified by automated tests with various termination policies and session scenarios)
- **SC-015**: Session subsystem exposes session validity checks that return accurate results for 100% of queries (verified by integration tests querying session validity across all session states)
- **SC-016**: Session subsystem performs zero memory storage operations (verified by automated tests monitoring Session subsystem operations and verifying no memory writes occur)
- **SC-017**: Session subsystem has zero dependencies on kernel internals (verified by code review and dependency analysis)
- **SC-018**: Session subsystem performs zero persistence operations (verified by automated tests monitoring file system access and verifying no disk writes occur)
- **SC-019**: STM implements session-relative TTL that represents diminishing contextual relevance (not semantic correctness, truth decay, or factual invalidation) (FR-020). TTL initial value is 10, assigned by STM when creating entries (FR-019). TTL decrements autonomously by STM whenever STM is accessed (read, write, select operations) for a session_id - all entries for the session are decremented to preserve recency bias (FR-021, FR-022). STM has no concept of execution boundaries and manages TTL based solely on access patterns (FR-022). STM autonomously removes expired entries from physical memory (FR-087). Orchestrator has no knowledge of TTL values, decrement logic, or expiration detection (FR-125). TTL expiration removes entries from STM eligibility and expired entries are excluded from all read and search operations (FR-023, FR-024) (verified by automated tests validating TTL assignment, autonomous decrement on access, and autonomous expiration cleanup)
- **SC-020**: STM supports querying memory entries by session_id (required) and optional filters (execution_id, phase) (FR-027). `write_entry()` ingests raw, phase-native execution artifacts without pre-summarization (FR-126, FR-128). `select_for_injection()` emits a deterministic, field-extracted contextual projection (NOT raw MemoryEntry objects) with context_blocks and non_authoritative_marker (FR-037, FR-129, FR-130). STM performs field extraction, ordering, and light formatting only - NO semantic summarization, inference, or rewriting (FR-131). STM determines relevance using only: session scope, context metadata, and recency (creation order / TTL state), with recency as the dominant signal (FR-033, FR-034, FR-035, FR-036). Phase-specific emission rules are enforced: Phase B gets prior user statements and assistant responses, Phase D gets refinement reasons and updated goals/steps, Phase A rarely uses memory, Phase C and E never inject (FR-129, FR-133) (verified by automated tests validating ingest/emit asymmetry, field extraction, and phase-specific rules)
- **SC-021**: The structure and semantics of the memory selection context are owned and defined by the Short-Term Memory (STM) subsystem via the Memory Access Interface (MAI) (FR-029). STM defines the schema for the memory selection context; the kernel (orchestrator) fills in only known execution facts required by that schema (FR-030). Orchestrator supplies only raw execution facts required by the MAI interface and does not interpret, enrich, or apply policy to the memory selection context (FR-031, FR-032) (verified by code review and integration tests validating context ownership boundaries)
- **SC-022**: STM requires a valid session_id for all operations and all STM entries are associated with exactly one session_id (FR-079, FR-080). STM lifetime is bounded by session lifetime and STM releases all memory associated with a session when notified of session termination (FR-081, FR-082). STM does not generate, manage, or terminate sessions and does not own or define session lifecycle behavior (sessions are owned by Session subsystem, not STM) (FR-077, FR-078, FR-083). Orchestrator mediates between Session subsystem and STM, supplies session_id to STM, and may trigger session cleanup (FR-084, FR-085, FR-086) (verified by integration tests and code review)
- **SC-023**: System implements Short-Term Memory (STM) that stores structured memory entries in-memory only with required annotations (session_id, execution_id, phase) (FR-009, FR-012). STM supports storing structured data (JSON-compatible) as memory entry content with phase-aware but uniform structure (FR-013). MAI supports execution-scoped annotations: memory entries are annotated with execution_id and phase (FR-008). Memory content is phase-native, raw execution artifacts ingested via write_entry() without pre-summarization (FR-126, FR-128). STM search operations exclude expired entries (TTL-based filtering) (FR-039) (verified by integration tests validating STM implementation, annotation structure, and phase-specific content schemas)
- **SC-024**: Session subsystem supports orchestrator requesting a list of all current sessions (active, expired, and closed) for audit purposes, returning session metadata (session_id, state, creation time) without exposing internal implementation details (FR-104, FR-105) (verified by integration tests querying session lists and verifying metadata structure)
- **SC-025**: Session subsystem supports orchestrator gracefully closing/terminating sessions when triggered by presentation/client requests or termination policies (before TTL expiration), releasing all associated resources and marking sessions as no longer accessible (FR-106, FR-107, FR-108) (verified by integration tests closing sessions through graceful closure triggers and verifying resource release)
- **SC-030**: Session subsystem autonomously manages Session TTL with initial value of 3 (FR-120). Session subsystem decrements Session TTL when orchestrator notifies it that execution completed (FR-121). Session subsystem autonomously detects when Session TTL is exhausted, marks session as expired, cleans up session_id internally, and returns expired status to orchestrator (FR-122, FR-123). Orchestrator has no knowledge of Session TTL values, decrement logic, or expiration detection (FR-125). When orchestrator receives expired status, it triggers STM cleanup (FR-124) (verified by integration tests with orchestrator notifying execution completion, Session subsystem autonomously detecting expiration, and verifying resource release)
- **SC-026**: STM supports orchestrator requesting a list of all current memory entries for a session for audit purposes, returning memory entry metadata (session_id, execution_id, phase, created_at, ttl) without exposing raw memory content (FR-109, FR-110) (verified by integration tests querying memory entry lists and verifying metadata-only responses)
- **SC-027**: STM supports orchestrator gracefully deleting/removing all memory entries associated with a session when the session is closed/terminated (via presentation/client request or termination policy, before TTL expiration), releasing all associated resources and ensuring deleted entries are no longer accessible (FR-111, FR-112, FR-113) (verified by integration tests deleting session memory entries through graceful closure and verifying entries are inaccessible after deletion)
- **SC-029**: STM supports orchestrator deleting/removing all memory entries associated with a session when the orchestrator requests cleanup for an expired session, releasing all associated resources and ensuring deleted entries are no longer accessible (FR-116, FR-117). STM does not observe time or proactively detect expiration (verified by integration tests with orchestrator triggering cleanup for expired sessions and verifying memory entries are inaccessible after cleanup)

## Assumptions

- Session subsystem is implemented and provides session_id to memory operations (Session subsystem implementation is part of Sprint 8 scope)
- Prompt registry supports extension for memory injection configuration (injection points can be added to existing registry)
- Memory selection algorithms can be deterministic without requiring complex relevance scoring (simple matching or ordering is sufficient)
- Capacity limits can be expressed as entry counts or equivalent structural limits (no need for byte-level limits in Sprint 8)
- TTL decrement events (execution boundaries) are observable and can trigger TTL updates
- Memory entry content is JSON-compatible (structured data, not arbitrary binary)
- Kernel can access MAI through dependency injection or similar mechanism without tight coupling
- Memory operations are infrequent enough that in-memory storage performance is sufficient (no need for optimization in Sprint 8)

## Dependencies

- Session subsystem must be implemented as part of Sprint 8 to provide session_id to memory operations
- Prompt registry must support injection point configuration (registry extension required)
- Existing Memory interface may need extension or replacement (compatibility assessment required)
- Phase E must support metadata extension (metadata structure extension required)
- No external storage dependencies (in-memory only)
- No embedding or vector store dependencies (out of scope)

## Non-Goals (Explicitly Out of Scope)

The following are explicitly NOT in scope for Sprint 8 and MUST NOT be introduced:

- **Cross-session memory**: No memory sharing or recall across different sessions
- **Persistence**: No memory persistence to disk, database, or any storage medium
- **Semantic summarization**: No semantic analysis, summarization, or content transformation of memory entries
- **Heuristic inference**: No heuristic-based inference, scoring, or decision-making based on memory content
- **Kernel ownership of sessions**: Kernel does not own or manage session lifecycle (sessions owned by Session subsystem)
- **Session logic in STM**: No coupling of session lifecycle logic into STM
- **Long-Term Memory (LTM)**: No embeddings, vector stores, or LTM capabilities
- **Memory-driven planning**: Memory does not drive planning, convergence decisions, or heuristic scoring
- **Memory optimization**: No compression, storage efficiency improvements, or performance optimizations beyond basic bounds
- **Data governance**: No private-mode, sensitivity enforcement, or governance beyond clean interfaces
- **Memory versioning**: No versioning or migration between sessions
- **Memory analytics**: No usage pattern analysis beyond basic observability (counts and flags)
- **Memory security**: No content encryption or security beyond interface boundaries
- **Distributed storage**: No memory replication or distributed storage mechanisms
- **Backup/recovery**: No memory backup or recovery mechanisms
