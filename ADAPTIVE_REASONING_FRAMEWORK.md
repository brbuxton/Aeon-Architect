# Aeon Architect — Architecture Epic Documentation

This document captures the **North Star**, **Golden Path Demos**, and **Sprint Gates** that define and govern the Aeon Architect architectural epic. These artifacts clarify the intended end-state capability, provide concrete behavioral demonstrations of success, and specify the checkpoints that ensure the multi‑sprint roadmap remains aligned with architectural intent.

---

# 🧭 North Star (Architectural Capability)

> **Aeon must be able to execute a multi-pass reasoning cycle where each step may modify the plan, memory, or depth, and converge deterministically on stable outputs for tasks of bounded complexity.**

---

# 🔄 Reasoning Loop (A → B → C → D → E)

Aeon's reasoning cycle follows a five-phase pipeline:

- **Phase A**: TaskProfile & TTL allocation
- **Phase B**: Initial Plan & Pre-Execution Refinement
- **Phase C**: Execution Passes (Execute Batch → Evaluate → Decide → Refine)
- **Phase D**: Adaptive Depth (TaskProfile updates at pass boundaries)
- **Phase E**: Final Answer Synthesis (Minimal Layer)

## Phase E – Final Answer Synthesis (Minimal Layer) ✅ IMPLEMENTED

**Purpose:** Convert internal reasoning artifacts into a coherent final answer.

**Implementation:** Single LLM synthesis prompt that aggregates step outputs after Phase D completion. Implemented in `aeon/orchestration/phases.py` as `execute_phase_e()` function.

**Output:** `final_answer` — a structured answer with minimal metadata (answer_text, confidence, used_step_ids, notes, ttl_exhausted, metadata).

**Status:** ✅ **COMPLETED** (Sprint 7)
- Phase E integrated at C-loop exit point in `OrchestrationEngine.run_multipass()`
- Executes unconditionally (even on TTL expiration)
- Comprehensive degraded mode handling (missing state, TTL expiration, zero passes, LLM errors)
- Always produces valid FinalAnswer, never raises exceptions
- CLI integration for FinalAnswer display (human-readable and JSON)

**Scope:** Internal reasoning only. Phase E synthesizes the final answer from execution results but does not include presentation-layer abstractions.

**Non-goals:**
- No UI or user-facing presentation layer
- No presentation abstraction (Layer 2)
- No kernel-level output governance (Layer 3)

---

# 🌟 Golden Path Demos (Epic-Level End-to-End Scenarios)
Golden Paths are demonstration scenarios that validate Aeon's architectural capability. They are run throughout the epic but are expected to fully pass only at the end.

Each Golden Path tests a different dimension of the North Star.

---

## **Golden Path 1 — Multi-Pass Reasoning with Convergence**
**Purpose:** Validate stable plan → execute → evaluate → refine → re-execute → converge loops.  
**Must Pass By:** Sprint 9

**Scenario Input:**
> "Explain how photosynthesis works, then revise your explanation to make it understandable for a 10-year-old."

**Expected Behavior:**
- Initial plan generation (explain → simplify → validate)
- Execution of steps
- Semantic evaluation of clarity/accuracy
- Partial plan mutation or refinement application
- Re-execution in revised form
- Deterministic convergence

**Capability Proven:**
- Multi-pass loop stability
- Deterministic convergence
- Plan mutation correctness
- Evaluation + refinement cohesion

---

## **Golden Path 2 — Memory-Aware Reasoning and Context Propagation**
**Purpose:** Validate correct reading, writing, and retrieval of short-term memory.  
**Must Pass By:** Sprint 10

**Scenario Inputs:**
1. "My dog Dimitri is a miniature Dachshund. He chews cables."  
2. "What strategies should I use to prevent the behavior?"  
3. "Rewrite your previous plan for someone who is new to dog training."

**Expected Behavior:**
- Aeon stores structured memory about Dimitri (breed, issue)
- Memory retrieval influences follow-up reasoning
- Refinement incorporates memory context
- Output adapts but preserves correctness across interactions

**Capability Proven:**
- Deterministic memory read/write behavior
- Relevance scoring
- Context propagation across steps
- Memory → plan → execution coherence

---

## **Golden Path 3 — Deep Planning, Semantic Validation, and Adaptive Depth**
**Purpose:** Validate recursive planning and adaptive reasoning.  
**Must Pass By:** Sprint 11

**Scenario Input:**
> "Design a three-phase study project to prepare for the CCNP ENCOR exam, including tools for labs, expected milestones, and weekly review cycles."

**Expected Behavior:**
- Structured multi-level plan creation
- Execution of detailed study program
- Semantic Validator identifies missing or inconsistent elements
- Recursive planner updates only necessary fragments
- Adaptive Depth increases when complexity requires it
- Convergence yields a complete, coherent artifact

**Capability Proven:**
- Recursive planning correctness
- Semantic Validator and Convergence cooperation
- Adaptive depth triggering
- Plan schema evolution handling

---

# ✔ How Golden Path Demos Are Used
Golden Paths are **epic-level**, not sprint-level checkpoints. They:
- do **not** need to pass early in the epic,
- signal architectural alignment when partial behavior begins working,
- must all pass by the end of Sprint 11 to declare architectural success.

Each sprint has a smaller "Sprint Demo" for local functionality; Golden Paths validate *global* capability.

---

# 🔐 Sprint Gates (Lightweight Architectural Checkpoints)
These gates protect against architectural drift and prevent starting a sprint whose foundations are not ready.

Each gate is a single question. If the answer is "no", do not continue.

---

## **Gate after Sprint 5 — Observability**
**Question:**
> *Do I now have enough observability and test coverage to understand any failure in the next sprint?*

---

## **Gate after Sprint 6 — Phase Integration**
**Question:**
> *Are A→B→C→D transitions coherent, logged, and deterministic enough for prompt consolidation?*

---

## **Gate after Sprint 7 — Prompt Governance** ✅ PASSED
**Question:**
> *Do all system prompts follow stable schemas and invariants, so the memory and reasoning modules can rely on their structure?*

**Answer**: ✅ **YES** - Sprint 7 completed successfully:
- All 23 system prompts consolidated in centralized registry
- All prompts have typed input models (Pydantic)
- JSON-producing prompts have typed output models
- Unified JSON extraction handles all LLM response formats
- Location invariant verified: zero inline prompts outside registry
- Schema invariant verified: all prompts have input models
- Registration invariant verified: all PromptIds have registry entries

**Note:** Sprint 7 includes Phase E (Final Answer Synthesis), which completes the A→B→C→D→E reasoning loop. This enables Golden Paths to synthesize final answers, but does not include presentation-layer work (Layer 2) or kernel output governance (Layer 3).

---

## **Gate after Sprint 8 — Memory Stability**
**Question:**
> *Does memory read/write deterministically and show correct traces without corrupting the reasoning loop?*

---

## **Gate after Sprint 9 — Convergence Stability**
**Question:**
> *Does convergence behave consistently under simple, repeatable tasks, without premature stopping or infinite loops?*

---

## **Gate after Sprint 10 — Validation Reliability**
**Question:**
> *Does the Semantic Validator correctly identify contradictions, omissions, and hallucinations in realistic plans?*

---

## **Gate after Sprint 11 — North Star Realization**
**Final Question:**
> *Does Aeon successfully run Golden Paths 1, 2, and 3?*

If yes: **the architecture epic is complete**.  
If no: revise specs, revisit modules, or redesign where needed.

---

# 📌 How These Artifacts Fit the Project
- The **North Star** defines the architectural goal.  
- **Golden Paths** validate system-wide capability.  
- **Sprint Gates** prevent building unstable layers atop incomplete foundations.

Together, they turn a multi-sprint roadmap into a coherent, testable architecture transformation.

---

# 🔮 Future Layers Beyond Phase E (Post-Epic Work)

The following layers are **explicitly deferred** to post-epic work and are **NOT** part of the current architecture epic (Sprints 5–11). They are documented here for clarity but will be implemented in future architecture work.

## Layer 2 — Presentation Layer Abstraction (Deferred, Post-Epic)

**Purpose:** Provide structured result objects and user-facing presentation abstractions.

**Components:**
- Structured Result object
- Verbosity modes
- Stable API for CLI/Web/MCP
- Output formatting policies
- User-facing presentation abstraction

**Status:** NOT included in Sprints 5–11. This layer will be implemented as post-epic work.

## Layer 3 — Kernel Output Governance & Deep Integration (Deferred, Post-Epic)

**Purpose:** Establish kernel-level output schema invariants and deep integration with memory, convergence, and validation systems.

**Components:**
- Kernel-level output schema invariants
- Integrating final answers with memory, convergence, and validation
- Deterministic output contracts
- Output versioning and governance

**Status:** NOT part of current epic. This layer belongs to future architecture work.

---

# 📝 Golden Paths and Phase E

Golden Paths require Aeon to synthesize final answers, which is enabled by **Phase E**. However, Golden Paths do **NOT** require:
- Layer 2 (Presentation Layer Abstraction)
- Layer 3 (Kernel Output Governance & Deep Integration)

Phase E provides the minimal synthesis capability needed to complete the reasoning loop (A→B→C→D→E) and satisfy Golden Path requirements.

---

(End of Architecture Epic Documentation)

