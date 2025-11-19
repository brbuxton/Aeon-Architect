# BACKLOG.md  
Aeon Architect — Backlog of Future Enhancements  
(High-level, non-committal, unordered, no sprint assignments)

---

## 1. Recursive Planning & Re-Planning
- Multi-pass plan refinement  
- Step expansion when ambiguity is detected  
- Automatic follow-up question generation  
- Detect missing details and regenerate plan fragments  
- Partial plan revision without discarding entire plan  
- Hierarchical and nested subplans  
- Integrate supervisor into plan refinement loop  

---

## 2. Adaptive Depth Heuristics
- Automatic detection of task complexity  
- Escalate reasoning depth when required  
- Reduce depth for simple tasks  
- Adaptive TTL scaling based on complexity  
- Confidence/uncertainty estimation  
- Token-level or structural heuristics (ambiguity, lack of specificity, missing gradients)  

---

## 3. Convergence Engine
- Detect whether the task is complete  
- Determine whether additional reasoning is needed  
- Identify inconsistencies or gaps in final answer  
- Retry reasoning until convergence threshold is met  
- Configurable convergence criteria (completeness, coherence, correctness)  

---

## 4. Semantic Validation Layer
- Validate step descriptions for specificity  
- Detect vague steps, contradictions, or irrelevant steps  
- Validate that step outputs contribute to goal  
- Perform “do/say mismatch” analysis  
- Detect hallucinations (tools, facts, outputs)  
- Logical consistency checks across plan + answer + memory  

---

## 5. Multi-Pass Execution Loop
Replace single-pass execution with:
1. plan  
2. execute  
3. evaluate  
4. refine  
5. re-execute (if needed)  
6. converge  
7. stop  

- Persistent loop until convergence or TTL exhaustion  
- Each cycle may modify plan, memory, or step definitions  

---

## 6. Tool Intelligence Upgrades
- Tool ranking  
- Tool selection heuristics  
- Tool recommendations for refinement steps  
- Automatic tool chaining (multi-step tool workflows)  
- Detect missing tools and suggest alternatives  
- Tool usage prediction based on context  

---

## 7. Supervisor Enhancements
- Semantic repair, not only structural repair  
- Multi-round self-correction  
- Plan quality analysis  
- Detect low-information or low-utility steps  
- Ability to refine poorly formed steps  
- Fallback mechanism for incomplete reasoning  

---

## 8. Short-Term Memory Engine (Working Memory)
- Automatic storage of intermediate results  
- Relevance scoring for recent results  
- Expiration rules based on TTL  
- Dynamic injection of relevant short-term memory into LLM prompts  
- Running summaries of state  
- Plan-step-oriented storage structure (per-step memory slots)  

---

## 9. Long-Term Memory Engine
- Persistent storage of general knowledge  
- Retrieval based on embeddings or semantic search  
- Memory ranking / scoring  
- Cross-session memory persistence  
- Episodic memory for conversations  
- Task-specific memory buckets  
- Automatic forgetting and summarization policies  
- Snapshot system (“memory frames”) for debugging  

---

## 10. Memory-Oriented Heuristics
- Decide what gets written to short-term vs long-term  
- Prioritize memory based on importance, novelty, recurrence  
- Identify redundant or trivial memory entries  
- Summarize memory when it grows too large  
- Handle conflicting memories with resolution logic  

---

## 11. Reflection & Self-Interrogation
- “What am I missing?” reasoning pass  
- “What assumptions did I make?” pass  
- “Does this answer fully satisfy the goal?” pass  
- Error introspection (root cause analysis)  
- Detect when additional research or tool usage is needed  

---

## 12. Semantic Search Over Artifacts
- Cross-artifact consistency checks  
- Automated alignment between plan, prompt, answer, and memory  
- Multi-document reasoning  
- Artifact-level diff reasoning  
- Detect changes that require re-planning  

---

## 13. Expanded Observability / Telemetry
- Per-step reasoning traces  
- Confidence or uncertainty metadata  
- Execution heatmaps  
- Metrics dashboard (cycles, convergence, tool effectiveness)  
- Plan evolution history  
- Memory evolution history  

---

## 14. LLM Prompt Pipeline Improvements
- Dynamic prompt templates based on task complexity  
- Multi-pass LLM pipelines with sub-prompts  
- Specialized prompts for refinement, introspection, validation  
- Plug-in model for additional prompt types (planning, review, rewrite, expand)  

---

## 15. Knowledge Tools + Research Tools
- Web search integration (configurable)  
- Fact-checking passes  
- Skeptical mode for validating claims  
- Multi-source aggregation  
- Providing citations in responses  

---

## 16. Multi-Agent Foundations
(future sprint, not immediate)

- Spawn sub-agents for isolated reasoning tasks  
- Coordinator agent with meta-reasoning  
- Specialized agents (research, planning, critic, tester)  
- Shared memory between agents  
- Round-based collaborative reasoning  

---

## 17. Advanced Memory Persistence (optional)
- SQLite or LiteFS backend  
- Graph-based memory (nodes = concepts, edges = relations)  
- Versioned memory trees  
- AI-assisted memory cleanup / compaction  
- Server mode (memory available across AEON sessions)  

---

## 18. CLI Enhancements
- Run interactive sessions with incremental planning  
- Visualize step trees  
- Inspect memory stores  
- Inspect cycle logs in real time  
- Replay modes for debugging  
- Benchmark mode (speed, cost, convergence)  

---

## 19. Configuration & Profiles
- Profiles for:
  - “shallow reasoning”
  - “balanced reasoning”
  - “deep research”
  - “stepwise explain”
- Adjustable heuristic parameters  
- Per-request override flags  

---

## 20. Quality-of-Life Improvements
- Better error reporting  
- Color-coded CLI output  
- Auto-formatting of plans  
- Verbose vs minimal modes  
- Streaming output support  

---

*(End of BACKLOG.md)*  
