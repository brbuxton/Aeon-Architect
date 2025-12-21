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

# 🔐 Architectural Progression Gates (Critical Path Checkpoints)

These gates replace the prior sprint-number–based gates.

They reflect the **actual critical path** required to realize the North Star, based on clarified definitions of validation, convergence, refinement, and control authority.

Each gate answers **one lightweight question**.  
If the answer is “no”, further architectural work should pause until the deficiency is resolved.

The gates are **ordered by dependency**, not by calendar sprint.

---

## **Gate 1 — Minimum Trustworthy Artifacts**

**Purpose:** Establish a reliable epistemic foundation.

**Question:**
> *Are TaskProfiles, Plans, Step Outputs, and ExecutionResults trustworthy enough that the system can reason about its own behavior without guessing?*

**This gate is satisfied when:**
- TaskProfile, Plan, Step Output, and ExecutionResult have explicit minimum contracts
- Boundary validation exists for each artifact
- Repair is attempted at most once and always re-validated
- Persistent invalid artifacts cause visible termination (not silent continuation)

**Why this matters:**
Without trustworthy artifacts:
- convergence is guesswork
- refinement thrashes
- deeper validation adds noise instead of insight

This gate is **blocking** for all downstream work.

---

## **Gate 2 — Reliable, Loud Validation**

**Purpose:** Make failures diagnosable and non-mysterious.

**Question:**
> *Does validation always run, always log, and never silently allow bad artifacts to pass?*

**This gate is satisfied when:**
- Validation executes at all phase boundaries where artifacts cross control points
- Every failure is logged with phase, execution_id, pass_number, and step_id (where applicable)
- Retry-once semantics are enforced consistently
- There are no silent bypasses or implicit “best effort” continuations

**Why this matters:**
Validation should be:
- boring
- predictable
- honest

Not clever, partial, or surprising.

---

## **Gate 3 — Honest Convergence Decisions**

**Purpose:** Restore convergence as a truthful control decision.

**Question:**
> *Can the system explicitly distinguish success, refine-worthy failure, stagnation, and budget exhaustion — and act accordingly?*

**This gate is satisfied when:**
- Convergence outcomes are explicit (e.g., success, refine, no-progress terminate, budget terminate)
- Convergence relies only on validated evidence artifacts
- Termination reasons are visible and explainable
- Convergence decisions are not conflated with TTL exhaustion

**Why this matters:**
Stopping is easy.  
Stopping **for the right reason** is the architectural challenge.

---

## **Gate 4 — Semantic Validation as Explanation (Not Control)**

**Purpose:** Turn semantic validation into an explanatory system.

**Question:**
> *Does semantic validation explain *why* convergence did not occur, without mutating artifacts or issuing commands?*

**This gate is satisfied when:**
- Semantic validation identifies gaps, contradictions, hallucinations, and mismatches
- Findings are descriptive, referenced, and severity-scored
- Validation does not block execution directly
- Validation does not mutate canonical artifacts

**Why this matters:**
Semantic validation is a **witness**, not a judge.
Its value is clarity, not authority.

---

## **Gate 5 — Governed Refinement**

**Purpose:** Ensure refinement is intentional, bounded, and effective.

**Question:**
> *Does refinement clearly communicate what the next pass must do differently, and only run when justified?*

**This gate is satisfied when:**
- Refinement consumes semantic findings and convergence context
- Refinement produces explicit next-pass guidance (not retroactive fixes)
- Refinement is bounded by convergence and TTL
- Repeated refinement without progress leads to termination, not looping

**Why this matters:**
Refinement without governance becomes hope-driven iteration.
Governed refinement becomes learning.

---

## **Gate 6 — Recursive Planning & Adaptive Depth**

**Purpose:** Safely enable advanced intelligence behaviors.

**Question:**
> *Can the system deepen planning or reasoning *only when justified by evidence*, without destabilizing control flow?*

**This gate is satisfied when:**
- Recursive planning operates on validated artifacts
- Semantic findings localize what must change
- Adaptive depth is triggered deliberately, not reflexively
- Golden Path 3 scenarios complete coherently

**Why this matters:**
Recursive planning without trustworthy signals is chaos.
With them, it becomes leverage.

---

## **Final Gate — North Star Realization**

**Final Question:**
> *Does Aeon reliably execute the Golden Paths and converge honestly on stable outputs for bounded tasks?*

This gate is satisfied when:
- Golden Path 1 (multi-pass convergence) passes reliably
- Golden Path 2 (memory-aware reasoning) passes deterministically
- Golden Path 3 (deep planning and adaptive depth) passes coherently

If yes: **the architecture epic is complete**.  
If no: revisit the earliest failed gate and correct foundations before proceeding.

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

