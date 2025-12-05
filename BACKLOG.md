# BACKLOG.md  
Aeon Architect — Backlog of Future Enhancements  
(High-level, non-committal, unordered, no sprint assignments)

**Legend**: `[Category: core|feature|infrastructure|security|quality-of-life] [Impact: critical|high|medium|low]`

---

## [Category: core] [Impact: high] Aeon Adaptive Reasoning Framework Epic

**Note**: This large body of work has been broken down into prioritized sprints below. See "Sprint Breakdown" section for phased approach.

### Sprint Breakdown (Recommended Phasing)

#### Sprint 5 — Foundation & Observability ✓ COMPLETED
**Status**: ✅ **COMPLETED** - Merged to master on 2025-01-27  
**Dependencies**: None (foundational)  
**Impact**: Enables all other improvements  
**Effort**: Medium

**Components**:
- **Error Logging Infrastructure** (blocks debugging of other improvements)
  - Structured error logging for refinement failures ✓
  - Error context capture and reporting ✓
  - Error recovery tracking and metrics ✓
  - Integration with observability layer ✓
- **Test Coverage Gaps** (enables safe refactoring)
  - Edge cases in convergence assessment ✓
  - Error paths in refinement logic ✓
  - TTL expiration edge cases ✓
  - Phase transition error scenarios ✓
  - Memory context propagation edge cases ✓
  - Target: 55% → 80%+ coverage ✓

**Rationale**: Without error logging, you can't effectively debug issues in other components. Without test coverage, refactoring is risky. These are prerequisites for safe optimization.

**Implementation Summary**:
- Implemented comprehensive observability and logging system (US1-US4)
- Phase-aware structured logging with correlation IDs
- Actionable error logging with error codes and severity levels
- Refinement and execution debug visibility
- Comprehensive test coverage with 20+ new integration tests
- Performance validation, backward compatibility, and determinism preservation
- See `specs/005-observability-logging/` for full documentation

---

#### Sprint 6 — Integration & Phase Transition Stabilization
**Dependencies**: Sprint 5 ✓ (completed - error logging available)  
**Impact**: Direct user experience improvement  
**Effort**: Medium-High

**Components**:
- **Integration & Phase Transition Improvements**
  - Phase A→B→C→D transitions need smoother handoffs
  - Error handling and recovery paths need enhancement
  - Memory context propagation between phases needs improvement
  - TTL boundary checks need refinement
  - Execution pass metadata collection needs enhancement
  - Error recovery and graceful degradation need improvement

**Rationale**: These improvements directly affect system reliability and user experience. They're cross-cutting concerns that benefit from Sprint 5's observability.

---

#### Sprint 7 — Prompt Infrastructure + Prompt Contracts
**Dependencies**: None (but blocks Sprint 9-11 prompt optimization work)  
**Impact**: Enables systematic prompt improvements  
**Effort**: Medium

**Components**:
- **Prompt Consolidation & Management** (see separate section below)
  - Consolidate all system prompts into dedicated `prompts.py` files
  - Create centralized prompt registry/manager
  - Extract inline prompts from executor.py and recursive.py
  - Standardize prompt structure and formatting
  - Enable prompt versioning and rollback capabilities
- **Prompt Contracts**
  - Define interface contracts for prompt inputs/outputs
  - Establish prompt validation and schema enforcement
  - Create prompt testing framework

**Rationale**: Must be done before optimizing prompts in ConvergenceEngine, SemanticValidator, etc. Enables A/B testing and systematic improvement.

---

#### Sprint 8 — Memory Foundations
**Dependencies**: Sprint 5 ✓, Sprint 6-7 (needs observability ✓, integration stability, and prompt infrastructure)  
**Impact**: Enables memory-aware reasoning and context propagation  
**Effort**: Medium-High

**Components**:
- **Short-Term Memory Engine (Working Memory)**
  - Automatic storage of intermediate results
  - Relevance scoring for recent results
  - Expiration rules based on TTL
  - Dynamic injection of relevant short-term memory into LLM prompts
  - Running summaries of state
  - Plan-step-oriented storage structure (per-step memory slots)
  - Memory prioritization and eviction policies
- **Memory-Oriented Heuristics**
  - Decide what gets written to short-term vs long-term
  - Prioritize memory based on importance, novelty, recurrence
  - Identify redundant or trivial memory entries
  - Summarize memory when it grows too large
  - Handle conflicting memories with resolution logic
  - Memory compression and optimization

**Rationale**: Memory foundations enable better context propagation between phases and support the refinement work in subsequent sprints. Addresses Gap 4 — Memory Timing.

---

#### Sprint 9 — Convergence Engine Refinement
**Dependencies**: Sprint 5 ✓, Sprints 6-8 (needs observability ✓, integration stability, prompt infrastructure, and memory foundations)  
**Impact**: Quality improvements, requires empirical data  
**Effort**: High (iterative, data-driven)

**Components**:
- Convergence assessment logic refinement and tuning
- Score thresholds (0.95 completeness, 0.90 coherence) adjustment based on empirical data
- LLM-based reasoning prompts optimization (requires Sprint 7)
- Consistency alignment checks strengthening
- Conflict detection and resolution logic improvement
- Integration with SemanticValidator for cross-validation (addresses Gap 3)

**Rationale**: These are optimization tasks that require:
1. Empirical data from production use
2. A/B testing capabilities (from Sprint 7)
3. Error logging to identify failure patterns (from Sprint 5)
4. Stable integration layer (from Sprint 6)
5. Memory context for better convergence assessment (from Sprint 8)

---

#### Sprint 10 — Semantic Validator Depth Expansion
**Dependencies**: Sprint 5 ✓, Sprints 6-9 (needs all foundational work)  
**Impact**: Quality improvements, requires empirical data  
**Effort**: High (iterative, data-driven)

**Components**:
- Issue detection algorithms refinement
- Severity assessment tuning based on impact analysis
- Do/say mismatch detection improvement
- Hallucination detection enhancement
- Cross-artifact consistency checks strengthening
- Validation report quality and actionability improvement
- Integration with ConvergenceEngine for bidirectional feedback (addresses Gap 3)

**Rationale**: These optimizations benefit from the full foundation and can leverage convergence data for better validation.

---

#### Sprint 11 — Recursive Planner & Adaptive Depth Enhancements
**Dependencies**: Sprint 5 ✓, Sprints 6-10 (needs complete foundation)  
**Impact**: Quality improvements, requires empirical data  
**Effort**: High (iterative, data-driven)

**Components**:
- **RecursivePlanner Enhancement**
  - Fragment identification algorithms enhancement
  - Delta-style operations refinement
  - Validation integration with semantic validator strengthening
  - Subplan generation and nesting depth handling improvement
  - Refinement action quality and relevance optimization
  - Plan schema evolution support (addresses Gap 6)
- **AdaptiveDepth Heuristics Tuning**
  - TaskProfile inference heuristics improvement
  - TTL allocation and adjustment logic tuning
  - Profile update triggers refinement
  - Bidirectional TTL adjustment optimization
  - Complexity detection algorithms improvement
  - Confidence/uncertainty estimation refinement

**Rationale**: These are the final optimization tasks that can leverage all previous improvements and empirical data.

---

## Architectural Gaps Incorporated

This backlog now addresses the following architectural gaps identified in the system analysis:

**Gap 1 — Interface Governance** ✓ RESOLVED
- Addressed through Sprint 5's error logging infrastructure and test coverage improvements ✓
- Interface contracts enforced through comprehensive testing and observability ✓
- Structured error handling ensures interface violations are caught and reported ✓

**Gap 4 — Memory Timing**
- Resolved in Sprint 8 (Memory Foundations)
- Establishes short-term memory engine with proper timing for context injection
- Memory prioritization and eviction policies ensure optimal memory usage across phases
- Addresses when and how memory is accessed during phase transitions

**Gap 7 — Prompt Contracts**
- Addressed in Sprint 7 (Prompt Infrastructure + Prompt Contracts)
- Defines interface contracts for prompt inputs/outputs
- Establishes prompt validation and schema enforcement
- Creates prompt testing framework for systematic improvement

**Gap 3 — Convergence ↔ Validator Interaction**
- Addressed in Sprints 9-10 through bidirectional integration
- ConvergenceEngine Refinement (Sprint 9) includes integration with SemanticValidator
- Semantic Validator Depth Expansion (Sprint 10) includes integration with ConvergenceEngine
- Cross-validation enables better quality assessment and refinement decisions

**Gap 6 — Plan Schema Evolution**
- Addressed in Sprint 11 (Recursive Planner & Adaptive Depth Enhancements)
- RecursivePlanner enhancements include plan schema evolution support
- Delta-style operations refined to handle schema changes gracefully
- Validation integration ensures schema changes are validated properly

---

### Original Component List (Reference)

#### ConvergenceEngine Refinement
- Convergence assessment logic needs refinement and tuning
- Score thresholds (0.95 completeness, 0.90 coherence) may need adjustment based on empirical data
- LLM-based reasoning prompts need optimization for better accuracy
- Consistency alignment checks (plan_aligned, step_aligned, answer_aligned, memory_aligned) need strengthening
- Conflict detection and resolution logic needs improvement

#### RecursivePlanner Enhancement
- Fragment identification algorithms need enhancement for better precision
- Delta-style operations (ADD/MODIFY/REMOVE) need refinement for more accurate plan updates
- Validation integration with semantic validator needs strengthening
- Subplan generation and nesting depth handling needs improvement
- Refinement action quality and relevance need optimization

#### SemanticValidator Depth
- Issue detection algorithms need refinement for better accuracy
- Severity assessment (CRITICAL/MEDIUM/LOW) needs tuning based on impact analysis
- Do/say mismatch detection needs improvement
- Hallucination detection (tools, facts, outputs) needs enhancement
- Cross-artifact consistency checks need strengthening
- Validation report quality and actionability need improvement

#### AdaptiveDepth Heuristics Tuning
- TaskProfile inference heuristics need better accuracy
- TTL allocation and adjustment logic needs tuning based on empirical data
- Profile update triggers need refinement for more responsive adaptation
- Bidirectional TTL adjustment needs optimization
- Complexity detection algorithms need improvement
- Confidence/uncertainty estimation needs refinement

#### Integration & Phase Transition Improvements
- Phase A→B→C→D transitions need smoother handoffs
- Error handling and recovery paths need enhancement
- Memory context propagation between phases needs improvement
- TTL boundary checks need refinement
- Execution pass metadata collection needs enhancement
- Error recovery and graceful degradation need improvement

#### Error Logging Infrastructure
- Structured error logging for refinement failures (TODO in orchestrator.py line 820)
- Error context capture and reporting
- Error recovery tracking and metrics
- Integration with observability layer

#### Test Coverage Gaps
- Edge cases in convergence assessment need coverage
- Error paths in refinement logic need testing
- TTL expiration edge cases need validation
- Phase transition error scenarios need coverage
- Memory context propagation edge cases need testing
- Current coverage: 55% - target: 80%+

---

## [Category: infrastructure] [Impact: high] Prompt Consolidation & Management
- **Issue**: System prompts are currently dispersed across multiple modules
- **Current State**: 
  - Prompts exist in: `aeon/validation/semantic.py`, `aeon/convergence/engine.py`, `aeon/adaptive/heuristics.py`, `aeon/supervisor/repair.py`, `aeon/kernel/executor.py`, `aeon/plan/recursive.py`
  - Only `aeon/plan/prompts.py` has dedicated prompt management
- **Action Needed**:
  - Consolidate all system prompts into dedicated `prompts.py` files per module
  - Create centralized prompt registry/manager for versioning and A/B testing
  - Extract inline prompts from executor.py and recursive.py
  - Standardize prompt structure and formatting
  - Enable prompt versioning and rollback capabilities
- **Benefits**: Easier maintenance, versioning, testing, and optimization of prompts

---

## [Category: feature] [Impact: medium] Tool Intelligence Upgrades
- Tool ranking algorithms
- Tool selection heuristics based on context
- Tool recommendations for refinement steps
- Automatic tool chaining (multi-step tool workflows)
- Detect missing tools and suggest alternatives
- Tool usage prediction based on context
- Tool effectiveness metrics and feedback loops

---

## [Category: feature] [Impact: medium] Supervisor Enhancements (Partially Graduated - Sprint 2)
- Semantic repair, not only structural repair (deferred to Tier-2)
- Multi-round self-correction
- Plan quality analysis
- Detect low-information or low-utility steps
- Ability to refine poorly formed steps ✓ (Sprint 2 - Supervisor integrated into refinement loop, FR-004)
- Fallback mechanism for incomplete reasoning
- Enhanced error recovery strategies

---

## Additional Backlog (Unassigned)

Items below are not currently assigned to the 7-sprint refinement sequence but remain in the backlog for future consideration.

---

## [Category: feature] [Impact: medium] Long-Term Memory Engine
- Persistent storage of general knowledge
- Retrieval based on embeddings or semantic search
- Memory ranking / scoring
- Cross-session memory persistence
- Episodic memory for conversations
- Task-specific memory buckets
- Automatic forgetting and summarization policies
- Snapshot system ("memory frames") for debugging

---

## [Category: feature] [Impact: medium] Reflection & Self-Interrogation
- "What am I missing?" reasoning pass
- "What assumptions did I make?" pass
- "Does this answer fully satisfy the goal?" pass
- Error introspection (root cause analysis)
- Detect when additional research or tool usage is needed
- Self-critique and quality assessment loops

---

## [Category: feature] [Impact: medium] Semantic Search Over Artifacts (Partially Graduated - Sprint 2)
- Cross-artifact consistency checks ✓ (Sprint 2 - Convergence Engine & Semantic Validation)
- Automated alignment between plan, prompt, answer, and memory ✓ (Sprint 2 - Cross-phase validation)
- Multi-document reasoning
- Artifact-level diff reasoning
- Detect changes that require re-planning ✓ (Sprint 2 - Refinement detection)
- Semantic search and retrieval across execution history

---

## [Category: infrastructure] [Impact: medium] Expanded Observability / Telemetry (Partially Graduated - Sprint 2)
- Per-step reasoning traces
- Confidence or uncertainty metadata
- Execution heatmaps
- Metrics dashboard (cycles, convergence, tool effectiveness)
- Plan evolution history ✓ (Sprint 2 - Execution Inspection and History)
- Memory evolution history
- Performance profiling and bottleneck identification
- Cost tracking (token usage, API calls)

---

## [Category: infrastructure] [Impact: medium] LLM Prompt Pipeline Improvements
- Dynamic prompt templates based on task complexity
- Multi-pass LLM pipelines with sub-prompts
- Specialized prompts for refinement, introspection, validation
- Plug-in model for additional prompt types (planning, review, rewrite, expand)
- Prompt A/B testing framework (note: foundational work in Sprint 7, advanced features unassigned)
- Prompt effectiveness metrics

---

## [Category: feature] [Impact: medium] Knowledge Tools + Research Tools
- Web search integration (configurable)
- Fact-checking passes
- Skeptical mode for validating claims
- Multi-source aggregation
- Providing citations in responses
- Source credibility assessment

---

## [Category: feature] [Impact: low] Multi-Agent Foundations
(future sprint, not immediate)

- Spawn sub-agents for isolated reasoning tasks
- Coordinator agent with meta-reasoning
- Specialized agents (research, planning, critic, tester)
- Shared memory between agents
- Round-based collaborative reasoning
- Agent communication protocols

---

## [Category: infrastructure] [Impact: low] Advanced Memory Persistence (optional)
- SQLite or LiteFS backend
- Graph-based memory (nodes = concepts, edges = relations)
- Versioned memory trees
- AI-assisted memory cleanup / compaction
- Server mode (memory available across AEON sessions)
- Memory backup and restore capabilities

---

## [Category: quality-of-life] [Impact: low] CLI Enhancements
- Run interactive sessions with incremental planning
- Visualize step trees
- Inspect memory stores
- Inspect cycle logs in real time
- Replay modes for debugging
- Benchmark mode (speed, cost, convergence)
- Interactive debugging and step-through execution

---

## [Category: quality-of-life] [Impact: low] Configuration & Profiles
- Profiles for:
  - "shallow reasoning"
  - "balanced reasoning"
  - "deep research"
  - "stepwise explain"
- Adjustable heuristic parameters
- Per-request override flags
- Configuration validation and schema
- Profile templates and presets

---

## [Category: quality-of-life] [Impact: low] Quality-of-Life Improvements
- Better error reporting with actionable messages
- Color-coded CLI output
- Auto-formatting of plans
- Verbose vs minimal modes
- Streaming output support
- Progress indicators and status updates
- User-friendly error messages

---

# Archive

## Resolved Issues

### [Category: core] [Impact: high] Sprint 5 — Foundation & Observability ✓ COMPLETED
- **Status**: ✅ **COMPLETED** - Merged to master on 2025-01-27
- **Branch**: `005-observability-logging`
- **Commit**: `1f77915` - "feat(observability): Implement comprehensive observability, logging, and test coverage"
- **Components Delivered**:
  - **US1 - Phase-Aware Structured Logging**: Correlation ID generation, phase entry/exit logging, state transitions, ExecutionContext integration
  - **US2 - Actionable Error Logging**: Error codes (AEON.<COMPONENT>.<CODE>), severity levels, structured error records, error recovery logging
  - **US3 - Refinement and Execution Debug Visibility**: Refinement outcome logging, execution result logging, convergence assessment logging
  - **US4 - Comprehensive Test Coverage**: 20+ new integration tests, expanded unit test coverage, phase transitions, error paths, TTL boundaries, context propagation, deterministic convergence
  - **Phase 7 - Polish**: Performance validation (<10ms latency), backward compatibility, determinism preservation, schema validation, diagnostic capability (≥90%)
- **Test Coverage**: Expanded from 55% to 80%+ with comprehensive integration and unit tests
- **Files Changed**: 35 files modified, 18 new test files created, 6,961 insertions
- **Documentation**: Complete specification in `specs/005-observability-logging/` including quickstart, tasks, and coverage summary
- **Impact**: Enables all future improvements with comprehensive observability and debugging capabilities

---

### [Category: core] [Impact: critical] Kernel LOC Violation (Constitutional Issue) ✓ RESOLVED
- **Status**: ✅ **RESOLVED** - Sprint 4 (004-kernel-refactor) completed successfully
- **Issue**: Kernel was 1351 LOC (orchestrator.py: 1092, executor.py: 259), exceeded 800 LOC constitutional limit
- **Resolution**: Kernel refactored to 635 LOC (orchestrator.py: 453, executor.py: 182) - 53% reduction
- **Action Taken**: Extracted all orchestration strategy logic to `aeon/orchestration/` modules:
  - `phases.py`: Phase A/B/C/D orchestration logic (537 LOC)
  - `refinement.py`: Plan refinement action application (100 LOC)
  - `step_prep.py`: Step preparation and dependency checking (137 LOC)
  - `ttl.py`: TTL expiration response generation (106 LOC)
- **Result**: Kernel now constitutional compliant (635 LOC < 800 LOC limit)
- **Verification**: All 289 tests passing, 100% behavioral preservation, performance maintained

---

## Graduated Features

### Recursive Planning & Re-Planning ✓ (Sprint 2 - GRADUATED)
- Multi-pass plan refinement  ✓
- Step expansion when ambiguity is detected  ✓
- Automatic follow-up question generation  ✓
- Detect missing details and regenerate plan fragments  ✓
- Partial plan revision without discarding entire plan  ✓
- Hierarchical and nested subplans  ✓
- Integrate supervisor into plan refinement loop  ✓

### Adaptive Depth Heuristics ✓ (Sprint 2 - GRADUATED)
- Automatic detection of task complexity  ✓
- Escalate reasoning depth when required  ✓
- Reduce depth for simple tasks  ✓
- Adaptive TTL scaling based on complexity  ✓
- Confidence/uncertainty estimation  ✓
- Token-level or structural heuristics (ambiguity, lack of specificity, missing gradients)  ✓

### Convergence Engine ✓ (Sprint 2 - GRADUATED)
- Detect whether the task is complete  ✓
- Determine whether additional reasoning is needed  ✓
- Identify inconsistencies or gaps in final answer  ✓
- Retry reasoning until convergence threshold is met  ✓
- Configurable convergence criteria (completeness, coherence, correctness)  ✓

### Semantic Validation Layer ✓ (Sprint 2 - GRADUATED)
- Validate step descriptions for specificity  ✓
- Detect vague steps, contradictions, or irrelevant steps  ✓
- Validate that step outputs contribute to goal  ✓
- Perform "do/say mismatch" analysis  ✓
- Detect hallucinations (tools, facts, outputs)  ✓
- Logical consistency checks across plan + answer + memory  ✓

### Multi-Pass Execution Loop ✓ (Sprint 2 - GRADUATED)
Replace single-pass execution with:
1. plan  ✓
2. execute  ✓
3. evaluate  ✓
4. refine  ✓
5. re-execute (if needed)  ✓
6. converge  ✓
7. stop  ✓

- Persistent loop until convergence or TTL exhaustion  ✓
- Each cycle may modify plan, memory, or step definitions  ✓

---

## [Category: infrastructure] [Impact: medium] Legacy Logging Migration

**Issue**: Legacy logging methods need refactoring for consistency
- `format_entry` is still used by `orchestrator.execute()` (single-pass mode)
- `log_multipass_entry` is unused dead code

**Current State**:
- `format_entry`: Creates LogEntry with `event="cycle"` for legacy cycle-based logging (Sprint 1)
- `log_multipass_entry`: Unused method from Sprint 2, creates raw dicts instead of LogEntry models

**Action Needed**:
1. **Remove `log_multipass_entry`** (dead code, never used)
2. **Migrate `orchestrator.execute()` to phase-aware logging**:
   - Replace `format_entry` calls with phase-aware logging methods
   - Use `log_phase_entry` / `log_phase_exit` for phase transitions
   - Use `log_state_transition` for state changes
   - Ensure correlation_id is included in all entries
3. **Deprecate `format_entry`** after migration:
   - Mark as deprecated with warning
   - Remove after migration complete
   - Maintain backward compatibility during transition (FR-009)

**Benefits**:
- Consistent logging architecture across all execution modes
- Better traceability with correlation IDs
- Cleaner codebase without dead code
- Full phase-aware logging coverage

**Dependencies**: None (can be done independently)
**Effort**: Low-Medium (mostly refactoring existing code)

**Note**: This addresses the gap identified in TEST_US1_US3_ANALYSIS.md regarding legacy method coverage.

---

*(End of BACKLOG.md)*
