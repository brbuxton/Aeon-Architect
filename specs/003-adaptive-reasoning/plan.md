# Implementation Plan: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Branch**: `003-adaptive-reasoning` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-adaptive-reasoning/spec.md`

## Summary

This plan implements a deterministic, adaptive, multi-pass reasoning engine that extends Sprint 1's single-pass orchestration system. The implementation adds five Tier-1 capabilities: Multi-Pass Execution Loop, Recursive Planning & Re-Planning, Convergence Engine, Adaptive Depth Heuristics, and Semantic Validation Layer.

**Technical Approach**: Extend the existing orchestrator with multi-pass loop control, create new modular components (convergence engine, semantic validator, adaptive depth heuristics, recursive planner) outside the kernel, and integrate them through well-defined interfaces. All semantic reasoning uses LLM-based approaches; all control flow remains host-based and deterministic.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: pydantic>=2.0.0 (existing), jsonschema>=4.0.0 (existing), requests>=2.31.0 (existing), pyyaml>=6.0.0 (existing)  
**Storage**: Memory subsystem (ephemeral for Sprint 2, via K/V interface from Sprint 1)  
**Testing**: pytest with coverage (existing)  
**Target Platform**: Linux/macOS (Python runtime)  
**Project Type**: Single Python package/library  
**Performance Goals**: Multi-pass execution completes within 5 minutes for 90% of complex tasks, convergence detection <2s per pass, semantic validation <3s per artifact  
**Constraints**: Kernel <800 LOC (orchestrator.py + executor.py combined), deterministic phase transitions, no domain logic in kernel, all semantic reasoning LLM-based  
**Scale/Scope**: Sprint 2 - multi-pass reasoning with adaptive depth, recursive planning, semantic validation, and convergence detection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Kernel Minimalism (Principle I)**: 
- [x] Does this feature add code to the kernel? If yes, justify why it cannot be a tool/supervisor.
  - **Answer**: Yes, minimal additions to orchestrator for multi-pass loop control (phase sequencing, pass management, TTL boundary checks). This is core orchestration logic, not domain-specific. Estimated addition: ~100-150 LOC for pass management and phase transitions. All semantic reasoning (TaskProfile inference, convergence assessment, semantic validation, recursive planning) lives in external modules.
- [x] Will kernel LOC remain under 800 after this feature?
  - **Answer**: Yes. Current kernel is ~561 LOC (orchestrator.py + executor.py). Estimated addition: ~100-150 LOC for multi-pass control flow. Total will be ~661-711 LOC, well under 800. All Sprint 2 features (convergence engine, semantic validator, adaptive depth, recursive planner) are external modules.
- [x] Does this feature add domain logic to the kernel? (MUST be NO)
  - **Answer**: No. Kernel only handles deterministic phase sequencing, pass management, and TTL boundary checks. All semantic reasoning, complexity assessment, and validation logic lives in external modules (convergence/, validation/, adaptive/, plan/).

**Separation of Concerns (Principle II)**:
- [x] Are new capabilities implemented as tools/supervisors, not kernel changes?
  - **Answer**: Yes. Convergence engine (aeon/convergence/), semantic validator (aeon/validation/), adaptive depth heuristics (aeon/adaptive/), and recursive planner (aeon/plan/recursive.py) are all external modules that interact through interfaces.
- [x] Do new modules interact through clean interfaces only?
  - **Answer**: Yes. All new modules define interfaces (ConvergenceEngine, SemanticValidator, AdaptiveDepth, RecursivePlanner) that the orchestrator uses without knowing internals.
- [x] Are kernel internals accessed by external modules? (MUST be NO)
  - **Answer**: No. External modules receive plan state, execution results, and validation reports as data structures. They return structured results (ConvergenceAssessment, SemanticValidationReport, TaskProfile, RefinementAction) without accessing kernel internals.

**Declarative Plans (Principle III)**:
- [x] If this feature affects plans, are they JSON/YAML declarative structures?
  - **Answer**: Yes. Plans remain JSON/YAML declarative structures. Recursive planner generates/refines plans as JSON/YAML. No procedural logic is added to plans.
- [x] Is any procedural logic added to plans? (MUST be NO)
  - **Answer**: No. Plans remain pure data structures. Refinement actions (ADD/MODIFY/REMOVE) operate on plan structure, not executable code.

**Extensibility (Principle IX)**:
- [x] Can this feature be added without kernel mutation?
  - **Answer**: Partially. Minimal kernel changes required for multi-pass loop control (~100-150 LOC), but all semantic reasoning capabilities are external modules that can be extended/replaced without kernel changes.
- [x] If kernel changes are required, are they rare, deliberate, and documented?
  - **Answer**: Yes. Kernel changes are limited to orchestrator pass management and phase sequencing logic. All changes are documented in this plan and justified as core orchestration logic.

**Sprint 1 Scope (Principle X)**:
- [x] Is this feature within Sprint 1 scope? (No diagrams, IaC, RAG, cloud logic, embeddings, multi-agent, advanced memory)
  - **Answer**: N/A - This is Sprint 2, not Sprint 1. Sprint 2 extends Sprint 1 capabilities with multi-pass reasoning while maintaining constitutional constraints.

## Project Structure

### Documentation (this feature)

```text
specs/003-adaptive-reasoning/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
aeon/
├── kernel/
│   ├── orchestrator.py  # Enhanced with multi-pass loop control, phase sequencing, pass management (~100-150 LOC addition)
│   ├── executor.py      # Enhanced with batch execution, clarity_state handling, step context propagation (~50 LOC addition)
│   ├── state.py         # Enhanced with ExecutionPass, ExecutionHistory models (data structures only)
│   └── __init__.py
├── convergence/         # NEW: Convergence engine module (external to kernel)
│   ├── __init__.py
│   ├── engine.py        # ConvergenceEngine class - LLM-based convergence assessment
│   └── models.py        # ConvergenceAssessment model
├── adaptive/           # NEW: Adaptive depth heuristics module (external to kernel)
│   ├── __init__.py
│   ├── heuristics.py    # AdaptiveDepth class - TaskProfile inference and TTL allocation
│   └── models.py        # TaskProfile, AdaptiveDepthConfiguration models
├── validation/         # Enhanced: Semantic validation layer (external to kernel)
│   ├── __init__.py
│   ├── schema.py       # Existing structural validation
│   └── semantic.py     # NEW: SemanticValidator class - LLM-based semantic validation
├── plan/               # Enhanced: Recursive planning capabilities
│   ├── models.py       # Enhanced with Step fields (step_index, total_steps, incoming_context, handoff_to_next, clarity_state)
│   ├── parser.py       # Existing plan parsing
│   ├── validator.py    # Existing plan validation
│   ├── executor.py     # Existing plan execution
│   ├── prompts.py      # Existing prompts
│   └── recursive.py    # NEW: RecursivePlanner class - recursive planning and refinement
├── llm/                # Existing LLM adapter interface
│   ├── interface.py
│   └── adapters/
├── memory/             # Existing memory interface
│   ├── interface.py
│   └── kv_store.py
├── supervisor/         # Existing supervisor (used for JSON repair)
│   ├── repair.py       # repair_json() method used by all modules
│   └── models.py
├── tools/              # Existing tool interface
│   ├── interface.py
│   ├── registry.py
│   └── models.py
├── observability/      # Enhanced: Multi-pass execution logging
│   ├── logger.py       # Enhanced with pass-level logging
│   └── models.py       # Enhanced with ExecutionPass, ExecutionHistory models
├── cli/
│   └── main.py         # Enhanced with multi-pass execution display
└── config.py           # Existing configuration

tests/
├── unit/
│   ├── kernel/
│   │   ├── test_orchestrator.py    # Test multi-pass loop, phase sequencing
│   │   ├── test_executor.py        # Test batch execution, clarity_state
│   │   └── test_state.py           # Test ExecutionPass, ExecutionHistory models
│   ├── convergence/
│   │   └── test_engine.py          # Test convergence engine
│   ├── adaptive/
│   │   └── test_heuristics.py       # Test adaptive depth, TaskProfile inference
│   ├── validation/
│   │   └── test_semantic.py        # Test semantic validation
│   └── plan/
│       └── test_recursive.py       # Test recursive planning
├── integration/
│   ├── test_multi_pass_execution.py    # End-to-end multi-pass tests
│   ├── test_convergence.py             # Convergence detection tests
│   ├── test_recursive_planning.py      # Recursive planning tests
│   ├── test_semantic_validation.py     # Semantic validation tests
│   ├── test_adaptive_depth.py          # Adaptive depth tests
│   └── test_ttl_expiration.py          # TTL expiration tests
└── contract/
    └── test_interfaces.py              # Interface contract tests
```

**Structure Decision**: Single Python package structure. All modules in `aeon/` package. New modules (convergence/, adaptive/) are external to kernel. Enhanced modules (validation/, plan/, observability/) extend existing functionality. Tests mirror source structure. Kernel remains minimal with only orchestration control flow.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All changes are justified and within constitutional bounds. Kernel additions are minimal (~100-150 LOC) and limited to orchestration control flow. All semantic reasoning lives in external modules.
