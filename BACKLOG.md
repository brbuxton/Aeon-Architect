# BACKLOG.md  
Aeon Architect — Backlog of Future Enhancements  
(High-level, non-committal, unordered, no sprint assignments)

**Legend**: `[Category: core|feature|infrastructure|security|quality-of-life] [Impact: critical|high|medium|low]`

---

## [Category: core] [Impact: critical] Kernel LOC Violation (Constitutional Issue)
- **Status**: Identified in Sprint 2, not resolved
- **Issue**: Kernel currently 1300 LOC (orchestrator.py: 1041, executor.py: 259), exceeds 800 LOC constitutional limit
- **Impact**: Violates Constitution Principle I (Kernel Minimalism)
- **Action**: Additional kernel refactoring required to extract logic to external modules
- **Priority**: Must be addressed before further kernel expansion

---

## [Category: core] [Impact: high] Sprint 2 Refinement & Optimization (Post-Implementation)

### ConvergenceEngine Refinement
- Convergence assessment logic needs refinement and tuning
- Score thresholds (0.95 completeness, 0.90 coherence) may need adjustment based on empirical data
- LLM-based reasoning prompts need optimization for better accuracy
- Consistency alignment checks (plan_aligned, step_aligned, answer_aligned, memory_aligned) need strengthening
- Conflict detection and resolution logic needs improvement

### RecursivePlanner Enhancement
- Fragment identification algorithms need enhancement for better precision
- Delta-style operations (ADD/MODIFY/REMOVE) need refinement for more accurate plan updates
- Validation integration with semantic validator needs strengthening
- Subplan generation and nesting depth handling needs improvement
- Refinement action quality and relevance need optimization

### SemanticValidator Depth
- Issue detection algorithms need refinement for better accuracy
- Severity assessment (CRITICAL/MEDIUM/LOW) needs tuning based on impact analysis
- Do/say mismatch detection needs improvement
- Hallucination detection (tools, facts, outputs) needs enhancement
- Cross-artifact consistency checks need strengthening
- Validation report quality and actionability need improvement

### AdaptiveDepth Heuristics Tuning
- TaskProfile inference heuristics need better accuracy
- TTL allocation and adjustment logic needs tuning based on empirical data
- Profile update triggers need refinement for more responsive adaptation
- Bidirectional TTL adjustment needs optimization
- Complexity detection algorithms need improvement
- Confidence/uncertainty estimation needs refinement

### Integration & Phase Transition Improvements
- Phase A→B→C→D transitions need smoother handoffs
- Error handling and recovery paths need enhancement
- Memory context propagation between phases needs improvement
- TTL boundary checks need refinement
- Execution pass metadata collection needs enhancement
- Error recovery and graceful degradation need improvement

### Error Logging Infrastructure
- Structured error logging for refinement failures (TODO in orchestrator.py line 820)
- Error context capture and reporting
- Error recovery tracking and metrics
- Integration with observability layer

### Test Coverage Gaps
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

## [Category: feature] [Impact: medium] Short-Term Memory Engine (Working Memory)
- Automatic storage of intermediate results
- Relevance scoring for recent results
- Expiration rules based on TTL
- Dynamic injection of relevant short-term memory into LLM prompts
- Running summaries of state
- Plan-step-oriented storage structure (per-step memory slots)
- Memory prioritization and eviction policies

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

## [Category: feature] [Impact: medium] Memory-Oriented Heuristics
- Decide what gets written to short-term vs long-term
- Prioritize memory based on importance, novelty, recurrence
- Identify redundant or trivial memory entries
- Summarize memory when it grows too large
- Handle conflicting memories with resolution logic
- Memory compression and optimization

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
- Prompt A/B testing framework
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

## Graduated Features (Sprint 2 - Complete)

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

*(End of BACKLOG.md)*
