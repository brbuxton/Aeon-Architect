<!--
Sync Impact Report:
- Version change: N/A → 1.0.0 (initial constitution)
- Modified principles: N/A (new constitution)
- Added sections: Core Principles (10), Architecture Constraints, Development Rules, Sprint 1 Scope, Governance
- Removed sections: N/A (replaced previous constitution)
- Templates requiring updates: ⚠ plan-template.md (Constitution Check section), ⚠ spec-template.md (may need kernel-specific guidance)
- Follow-up TODOs: None
-->

# Aeon Constitution

## Core Principles

### I. Kernel Minimalism (NON-NEGOTIABLE)
The kernel is the orchestrator and MUST remain small, deterministic, and domain-agnostic. The kernel handles ONLY: LLM loop execution, plan creation, plan updates, state transitions, scheduling, tool invocation, TTL/token governance, and supervisor routing. The kernel MUST never contain domain logic (Azure, cloud patterns, diagrams, IaC, validation rules, etc.). The kernel MUST be stable, testable, and under 800 LOC in the first release. Rationale: A minimal kernel ensures maintainability, testability, and prevents architectural drift toward domain-specific concerns.

### II. Strict Separation of Concerns
Tools, supervisors, memory engines, validators, pattern libraries, RAG systems, and domain logic MUST all live outside the kernel and interact through clean interfaces. The kernel knows interfaces, not internals. The kernel MUST communicate with external modules only through well-defined contracts. Rationale: Separation enables independent development, testing, and replacement of components without kernel changes.

### III. Declarative Plans
Plans are JSON/YAML declarative data structures created/updated by the LLM. The kernel executes plans; the LLM creates them. No procedural logic is allowed in plans. Plans MUST be pure data structures that describe what to do, not how to do it. Rationale: Declarative plans enable the kernel to remain deterministic and domain-agnostic while allowing the LLM to express complex orchestration logic.

### IV. Tools as First-Class Modules
Tools MUST be independent, deterministic, and schema-defined. Tools MUST not access kernel internals or contain orchestration logic. Tools encapsulate domain knowledge (in future sprints), not the kernel. Each tool MUST have a clear schema defining inputs, outputs, and side effects. Rationale: First-class tools enable extensibility without kernel mutation, allowing new capabilities through composition rather than modification.

### V. Supervisors
A supervisor is a separate module (using the same LLM) that repairs malformed JSON, tool calls, or plans. The kernel MUST invoke the supervisor when validation fails. Supervisors MUST not add new tools or meaning—only correction. Supervisors operate on syntax and structure, not semantics. Rationale: Supervisors handle LLM output inconsistencies without polluting the kernel with repair logic.

### VI. Memory Subsystem
Sprint 1 memory is a simple key/value store with a minimal API. Memory MUST be outside the kernel and replaceable with embeddings/vector search in future versions. The memory interface MUST be abstracted such that implementations can be swapped without kernel changes. Rationale: Starting simple enables rapid iteration while maintaining architectural flexibility for future enhancements.

### VII. Validation
Validation modules MUST enforce schema correctness for plans, LLM outputs, and tool calls. The kernel MUST run validation before tool invocation, memory writes, and plan updates. Validation failures MUST trigger supervisor invocation or error handling, never silent failures. Rationale: Validation ensures system integrity and prevents invalid state propagation through the orchestration loop.

### VIII. Observability
Every orchestration cycle MUST log: step number, plan state, LLM output, supervisor actions, tool calls, TTL countdown, and errors. Logs are JSONL format. Logging MUST be non-blocking and MUST not affect kernel determinism. Rationale: Comprehensive observability enables debugging, monitoring, and understanding of LLM orchestration behavior in production.

### IX. Extensibility Without Mutation
New capabilities MUST be added through new tools or supervisors, not by modifying kernel internals. Kernel changes MUST be rare, deliberate, and well-documented. When kernel changes are necessary, they MUST maintain backward compatibility or follow semantic versioning for breaking changes. Rationale: Extensibility through composition preserves kernel stability and enables independent evolution of system capabilities.

### X. Sprint 1 Scope Constraints
Sprint 1 MUST NOT include: diagram generation, IaC generation, RAG, cloud logic, embeddings, multi-agent concurrency, or advanced memory ranking. Sprint 1 ONLY delivers: kernel, plan engine, state manager, simple memory K/V, tool interface, supervisor, and validation layer. The goal of Sprint 1 is to produce a minimal but functional reasoning loop that can create plans, call stub tools, and update state reliably. Rationale: Focused scope ensures delivery of a working foundation before adding advanced features.

## Architecture Constraints

### Kernel Boundaries
- The kernel MUST NOT exceed 800 LOC in Sprint 1
- The kernel MUST NOT import or depend on domain-specific modules
- The kernel MUST NOT contain business logic, validation rules, or pattern matching beyond orchestration
- All domain knowledge MUST reside in tools, supervisors, or external modules

### Interface Contracts
- All external modules (tools, supervisors, memory, validators) MUST implement well-defined interfaces
- Interfaces MUST be versioned and backward-compatible within major versions
- The kernel MUST communicate with external modules only through interface contracts
- Interface changes MUST follow semantic versioning

### Plan Structure
- Plans MUST be valid JSON or YAML
- Plans MUST NOT contain executable code or procedural logic
- Plans MUST be schema-validated before execution
- Plan schemas MUST be versioned and documented

## Development Rules

### Code Organization
- Kernel code MUST be in a dedicated kernel module/package
- Tools MUST be in separate modules with no kernel dependencies
- Supervisors MUST be separate modules that can be swapped
- Memory implementations MUST be pluggable through interfaces

### Testing Requirements
- Kernel MUST have 100% test coverage for core orchestration logic
- All interfaces MUST have contract tests
- Tools MUST be independently testable without kernel
- Integration tests MUST verify kernel-external module interactions

### Documentation Requirements
- Kernel API MUST be fully documented
- Interface contracts MUST be specified with schemas
- Plan format MUST be documented with examples
- Architecture decisions MUST be recorded in ADRs

## Sprint 1 Deliverables

### Required Components
1. **Kernel**: Core orchestrator (<800 LOC) handling LLM loop, plan execution, state management
2. **Plan Engine**: JSON/YAML plan parser, validator, and executor
3. **State Manager**: Manages orchestration state transitions
4. **Simple Memory K/V**: Basic key-value store with minimal API
5. **Tool Interface**: Schema-defined interface for tool registration and invocation
6. **Supervisor**: LLM-based repair module for malformed outputs
7. **Validation Layer**: Schema validation for plans, LLM outputs, tool calls

### Out of Scope (Sprint 1)
- Diagram generation tools
- Infrastructure as Code (IaC) generation
- RAG (Retrieval Augmented Generation) systems
- Cloud-specific logic (Azure, AWS, etc.)
- Embeddings and vector search
- Multi-agent concurrency
- Advanced memory ranking/retrieval

### Success Criteria
- Kernel executes a complete reasoning loop: plan creation → tool invocation → state update
- Supervisor successfully repairs malformed JSON/tool calls
- Validation layer rejects invalid plans and tool calls
- Memory K/V stores and retrieves state correctly
- All orchestration cycles are logged in JSONL format

## Governance

This constitution supersedes all other development practices and architectural guidelines. All code, designs, and documentation MUST comply with these principles.

### Amendment Process
- Amendments to this constitution require:
  1. Documentation of the proposed change and rationale
  2. Impact analysis on kernel stability and existing modules
  3. Approval from project maintainers
  4. Version increment following semantic versioning:
     - MAJOR: Backward incompatible principle removals or kernel architecture changes
     - MINOR: New principle/section added or materially expanded guidance
     - PATCH: Clarifications, wording fixes, non-semantic refinements
  5. Update of all dependent templates, interfaces, and documentation

### Compliance Verification
- All pull requests MUST verify constitutional compliance, especially kernel size and separation of concerns
- Automated checks MUST validate kernel LOC limits and interface contracts
- Non-compliance MUST block code integration
- Kernel changes MUST be reviewed with extra scrutiny

### Kernel Change Justification
- Any kernel change MUST be justified against Principle I (Kernel Minimalism)
- Kernel changes that increase LOC beyond 800 MUST include a plan to refactor back under limit
- Kernel changes that add domain logic MUST be rejected
- Proposed kernel changes MUST demonstrate that the functionality cannot be achieved through tools or supervisors

**Version**: 1.0.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
