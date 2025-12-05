# Data Model: Sprint 2 - Adaptive Reasoning Engine

**Date**: 2025-12-04  
**Feature**: Sprint 2 - Adaptive Reasoning Engine  
**Phase**: 1 - Design

## Overview

This document extends the Sprint 1 data model with new entities required for multi-pass execution, recursive planning, convergence detection, adaptive depth, and semantic validation. All entities maintain declarative, JSON/YAML-compatible structures.

## Extended Entities

### PlanStep (Extended)

Extends Sprint 1 PlanStep with new fields for multi-pass execution and step context.

**New Fields**:
- `step_index` (integer, required): 1-based step number within the plan
- `total_steps` (integer, required): Total number of steps in the plan
- `incoming_context` (string, optional): Context from previous steps (may be empty initially)
- `handoff_to_next` (string, optional): Context to pass to next step (may be empty initially)
- `clarity_state` (enum, optional): Clarity state returned by step execution LLM
  - Values: "CLEAR", "PARTIALLY_CLEAR", "BLOCKED"
  - Only present after step execution
- `step_output` (string, optional): Output from step execution
- `dependencies` (array of strings, optional): List of step IDs that must complete before this step
- `provides` (array of strings, optional): List of artifacts provided by this step

**Extended Status Enum**:
- Existing: "pending", "running", "complete", "failed"
- New: "invalid" - Step marked as invalid due to refinement inconsistency or clarity_state == BLOCKED

**Validation Rules**:
- step_index must be >= 1 and <= total_steps
- total_steps must equal the number of steps in the plan
- step_index must be unique within the plan
- If clarity_state == "BLOCKED", step status MUST be set to "invalid"
- dependencies must reference valid step_ids in the plan
- If step has dependencies, all dependency steps must have status "complete" before this step can execute

**State Transitions**:
- `pending` → `running`: When step execution begins
- `running` → `complete`: When step execution succeeds
- `running` → `failed`: When step execution fails
- `running` → `invalid`: When clarity_state == BLOCKED or refinement creates inconsistency
- `invalid` → `pending`: When refinement updates the step (only for unexecuted steps)

**Relationships**:
- Belongs to Plan (parent)
- References other PlanSteps via dependencies
- Referenced by RefinementAction

### ExecutionPass

A single iteration of the multi-pass loop containing all phase information for one pass.

**Fields**:
- `pass_number` (integer, required): Sequential pass identifier (0 for initial plan, 1..N for execution passes)
- `phase` (enum, required): Current phase of the pass
  - Values: "PLAN", "EXECUTE", "EVALUATE", "REFINE", "RE_EXECUTE"
- `plan_state` (Plan, required): Snapshot of plan at pass start
- `execution_results` (dict, required): Step outputs and tool results
  - Structure: `{step_id: {step_output: str, clarity_state: str, tool_result: dict}}`
- `evaluation_results` (dict, required): Convergence assessment and semantic validation report
  - Structure: `{validation_report: SemanticValidationReport, convergence: ConvergenceAssessment}`
- `refinement_changes` (array of RefinementAction, optional): Plan/step modifications if any
- `ttl_remaining` (integer, required): TTL cycles remaining at pass start
- `timing_information` (dict, required): Timing metadata
  - Structure: `{start_time: str (ISO 8601), end_time: str (ISO 8601), duration_seconds: float}`

**Validation Rules**:
- pass_number must be >= 0 and increment sequentially
- phase must be one of the enum values
- plan_state must be valid Plan structure
- ttl_remaining must be >= 0
- timing_information.start_time must be before end_time

**State Transitions**:
- Created: Pass begins, initialized with plan_state snapshot
- PLAN: Initial plan generation and pre-execution refinement (Pass 0 only)
- EXECUTE: Steps executed in batch
- EVALUATE: Semantic validation and convergence assessment
- REFINE: Plan refinement based on evaluation results
- Completed: Pass ends, results recorded in ExecutionHistory

**Relationships**:
- Contains Plan snapshot
- Contains SemanticValidationReport
- Contains ConvergenceAssessment
- Contains RefinementAction objects
- Belongs to ExecutionHistory

### ExecutionHistory

Structured history of completed multi-pass execution, stored in-memory only for Sprint 2.

**Fields**:
- `execution_id` (string, required): Unique identifier for the execution
- `task_input` (string, required): Original task description
- `configuration` (dict, required): Execution configuration
  - Structure: `{convergence_criteria: dict, ttl: int, adaptive_depth_settings: dict}`
- `passes` (array of ExecutionPass, required): Ordered list of execution passes
- `final_result` (dict, required): Final execution result
  - Structure: `{converged: bool, result_type: str, output: Any, metadata: dict}`
- `overall_statistics` (dict, required): Aggregate statistics
  - Structure: `{total_passes: int, total_refinements: int, convergence_achieved: bool, total_time_seconds: float}`

**Validation Rules**:
- execution_id must be unique
- passes array must be non-empty
- passes must be ordered by pass_number
- final_result must indicate converged status or TTL expiration
- overall_statistics must match actual pass data

**State Transitions**:
- Created: Execution begins, initialized with task_input and configuration
- Updated: Each pass adds ExecutionPass to passes array
- Completed: Execution ends (converged or TTL expired), final_result and overall_statistics computed

**Relationships**:
- Contains multiple ExecutionPass objects
- Returned as part of execution result (in-memory, no persistent storage)

### RefinementAction

A modification to plan or steps during refinement phase.

**Fields**:
- `action_type` (enum, required): Type of refinement action
  - Values: "ADD", "MODIFY", "REMOVE", "REPLACE", "SUBPLAN_CREATE", "STEP_MARK_INVALID"
- `target_step_id` (string, optional): Identifier of step being changed (required for MODIFY, REMOVE, REPLACE, STEP_MARK_INVALID)
- `new_step` (PlanStep, optional): New or modified step (required for ADD, MODIFY, REPLACE)
- `justification` (string, required): LLM-generated explanation of why refinement was needed
- `semantic_validation_input` (array of ValidationIssue, optional): Validation issues that triggered refinement
- `inconsistency_detected` (boolean, required): True if refinement creates inconsistency with executed steps

**Validation Rules**:
- action_type must be one of the enum values
- target_step_id required for MODIFY, REMOVE, REPLACE, STEP_MARK_INVALID
- new_step required for ADD, MODIFY, REPLACE
- justification must be non-empty string
- If inconsistency_detected == true, target_step must have status "pending" (not "complete" or "failed")

**State Transitions**:
- Created: Refinement action generated by recursive planner
- Applied: Action applied to plan, plan_state updated
- Rejected: Action cannot be applied (e.g., targets executed step), logged as advisory

**Relationships**:
- References PlanStep (by target_step_id)
- Triggered by ValidationIssue objects
- Applied to Plan

### ConvergenceAssessment

Result from convergence engine determining whether task is finished.

**Fields**:
- `converged` (boolean, required): True if convergence criteria met
- `reason_codes` (array of strings, required): Explanation of why convergence was/wasn't achieved
  - Values: "complete", "incoherent", "incomplete", "missing_step", "contradiction_detected", "inconsistent", etc.
- `scores` (dict, required): Evaluation scores
  - Structure: `{completeness_score: float (0.0-1.0), coherence_score: float (0.0-1.0), consistency_status: dict}`
- `explanation` (string, required): Human-readable summary from LLM
- `detected_issues` (array of strings, optional): List of specific issues detected (contradictions, omissions, hallucinations)

**Validation Rules**:
- converged must be boolean
- reason_codes must be non-empty array
- scores.completeness_score must be between 0.0 and 1.0
- scores.coherence_score must be between 0.0 and 1.0
- If converged == false, reason_codes must indicate which criteria failed

**State Transitions**:
- Created: Convergence engine generates assessment
- Used: Assessment used by orchestrator to decide next phase (terminate or refine)

**Relationships**:
- Generated by ConvergenceEngine
- Consumes SemanticValidationReport as input
- Referenced by ExecutionPass

### SemanticValidationReport

Output from semantic validation layer identifying semantic quality issues.

**Fields**:
- `validation_id` (string, required): Unique identifier for the validation run
- `artifact_type` (enum, required): Type of artifact validated
  - Values: "plan", "step", "execution_artifact", "cross_phase"
- `issues` (array of ValidationIssue, required): List of detected issues (may be empty)
- `overall_severity` (enum, required): Highest severity detected
  - Values: "LOW", "MEDIUM", "HIGH", "CRITICAL"
  - Default: "LOW" if no issues
- `issue_summary` (dict, required): Counts by issue type
  - Structure: `{specificity: int, relevance: int, consistency: int, hallucination: int, do_say_mismatch: int}`
- `proposed_repairs` (array of dict, optional): LLM-generated repair suggestions

**Validation Rules**:
- validation_id must be unique
- artifact_type must be one of the enum values
- issues array may be empty (no issues detected)
- overall_severity must match highest severity in issues array
- issue_summary counts must match actual issues

**State Transitions**:
- Created: Semantic validator generates report
- Used: Report consumed by convergence engine and recursive planner

**Relationships**:
- Contains ValidationIssue objects
- Generated by SemanticValidator
- Consumed by ConvergenceEngine
- Referenced by ExecutionPass

### ValidationIssue

Individual issue detected by semantic validation.

**Fields**:
- `issue_id` (string, required): Unique identifier for the issue
- `type` (enum, required): Category of issue
  - Values: "specificity", "relevance", "consistency", "hallucination", "do_say_mismatch"
- `severity` (enum, required): Severity level
  - Values: "LOW", "MEDIUM", "HIGH", "CRITICAL"
- `description` (string, required): Human-readable issue explanation (LLM-generated)
- `location` (dict, optional): Where issue was detected
  - Structure: `{step_id: str, artifact_reference: str}`
- `proposed_repair` (dict, optional): LLM-generated suggested fix
  - Structure: `{action: str, target: str, changes: dict}`

**Validation Rules**:
- issue_id must be unique within validation report
- type must be one of the enum values
- severity must be one of the enum values
- description must be non-empty string (LLM-generated)
- If location present, step_id must reference valid step

**State Transitions**:
- Created: Semantic validator detects issue
- Used: Issue triggers refinement or convergence assessment

**Relationships**:
- Belongs to SemanticValidationReport
- Triggers RefinementAction

### TaskProfile

Profile inferred for a task indicating complexity and resource requirements.

**Fields**:
- `profile_version` (integer, required): Version number for TaskProfile (increments on updates)
- `reasoning_depth` (integer, required): Ordinal scale 1-5 (1=very shallow, 2=shallow, 3=moderate, 4=deep, 5=very deep)
- `information_sufficiency` (float, required): Float 0.0-1.0 (0.0=insufficient, 1.0=sufficient)
- `expected_tool_usage` (enum, required): Expected tool usage level
  - Values: "none", "minimal", "moderate", "extensive"
- `output_breadth` (enum, required): Expected output breadth
  - Values: "narrow", "moderate", "broad"
- `confidence_requirement` (enum, required): Required confidence level
  - Values: "low", "medium", "high"
- `raw_inference` (string, required): Natural-language explanation of how dimensions were determined

**Validation Rules**:
- reasoning_depth must be between 1 and 5 (inclusive)
- information_sufficiency must be between 0.0 and 1.0 (inclusive)
- expected_tool_usage must be one of the enum values
- output_breadth must be one of the enum values
- confidence_requirement must be one of the enum values
- raw_inference must be non-empty string
- Tier stability: Repeated inference for same input must produce reasoning_depth within ±1 tier

**State Transitions**:
- Created: TaskProfile inferred at task start (Phase A)
- Updated: TaskProfile revised at pass boundaries when complexity mismatch detected
- Used: TaskProfile used to allocate TTL and reasoning depth

**Relationships**:
- Generated by AdaptiveDepth module
- Referenced by ExecutionPass
- Used by orchestrator for TTL allocation

### AdaptiveDepthConfiguration

Settings used by adaptive depth heuristics for a task.

**Fields**:
- `detected_complexity` (string, required): Complexity category detected
  - Values: "very_low", "low", "moderate", "high", "very_high"
- `ambiguity_score` (float, optional): Numeric ambiguity score (0.0-1.0)
- `uncertainty_score` (float, optional): Numeric uncertainty score (0.0-1.0)
- `allocated_ttl` (integer, required): TTL cycles allocated based on TaskProfile
- `reasoning_mode` (enum, required): Reasoning depth mode selected
  - Values: "deep", "shallow", "balanced"
- `adjustment_reason` (string, required): Explanation of why depth was adjusted
- `heuristics_used` (array of strings, optional): Which heuristics contributed to decision

**Validation Rules**:
- detected_complexity must be one of the enum values
- ambiguity_score must be between 0.0 and 1.0 if present
- uncertainty_score must be between 0.0 and 1.0 if present
- allocated_ttl must be >= 0 and <= global TTL limit
- reasoning_mode must be one of the enum values
- adjustment_reason must be non-empty string

**State Transitions**:
- Created: Adaptive depth configuration computed from TaskProfile
- Updated: Configuration revised when TaskProfile updated at pass boundaries
- Used: Configuration used by orchestrator for execution strategy

**Relationships**:
- Generated by AdaptiveDepth module
- Based on TaskProfile
- Referenced by ExecutionPass

### Subplan

A nested plan structure within a parent plan step.

**Fields**:
- `parent_step_id` (string, required): ID of step this subplan expands
- `subplan_goal` (string, required): Objective of the subplan
- `substeps` (array of PlanStep, required): Array of step objects following same structure as main plan steps
- `depth_level` (integer, required): Nesting depth (1 = first level of nesting)
- `created_by` (string, required): Which system component created it
  - Values: "recursive_planner", "refinement", etc.

**Validation Rules**:
- parent_step_id must reference valid step in parent plan
- subplan_goal must be non-empty string
- substeps must be non-empty array
- depth_level must be >= 1 and <= maximum allowed depth (5)
- If depth_level > 5, subplan creation must fail gracefully

**State Transitions**:
- Created: Recursive planner generates subplan for complex step
- Integrated: Subplan integrated into parent plan structure
- Executed: Subplan steps executed as part of parent plan execution

**Relationships**:
- References PlanStep (parent)
- Contains PlanStep objects (substeps)
- Generated by RecursivePlanner

### TTLExpirationResponse

Result returned when TTL expires before convergence.

**Fields**:
- `converged` (boolean, required): Always false for TTL expiration
- `result_type` (string, required): Always "ttl_expired"
- `latest_pass_result` (dict, optional): Output from most recent completed execution pass (null if no passes completed)
- `partial_result` (dict, optional): Output from current incomplete pass if TTL expired mid-phase and no passes completed
- `expiration_point` (enum, required): Where TTL expired
  - Values: "phase_boundary", "mid_phase"
- `ttl_expired_metadata` (dict, required): Metadata about expiration
  - Structure: `{completeness_score: float, coherence_score: float, consistency_status: dict, detected_issues: array, reason_codes: array, pass_number: int}`
- `termination_reason` (string, required): Always "ttl_expired"

**Validation Rules**:
- converged must be false
- result_type must be "ttl_expired"
- expiration_point must be one of the enum values
- If expiration_point == "phase_boundary", latest_pass_result must be present
- If expiration_point == "mid_phase" and no passes completed, partial_result must be present
- termination_reason must be "ttl_expired"

**State Transitions**:
- Created: TTL expires during execution
- Returned: Response returned to caller with execution history

**Relationships**:
- Contains ExecutionHistory
- Generated by Orchestrator
- Returned as execution result

## Entity Relationships

```
Plan
├── contains → PlanStep[] (1:N)
│   ├── extended with → step_index, total_steps, incoming_context, handoff_to_next, clarity_state
│   └── status can be → "invalid" (new)
└── referenced by → ExecutionPass

ExecutionHistory
├── contains → ExecutionPass[] (1:N)
└── returned as → execution result (in-memory)

ExecutionPass
├── contains → Plan (snapshot)
├── contains → SemanticValidationReport
├── contains → ConvergenceAssessment
├── contains → RefinementAction[]
└── contains → TaskProfile

SemanticValidationReport
├── contains → ValidationIssue[]
└── consumed by → ConvergenceEngine

ConvergenceAssessment
├── consumes → SemanticValidationReport
└── used by → Orchestrator (decision logic)

RefinementAction
├── references → PlanStep (target_step_id)
└── triggered by → ValidationIssue[]

TaskProfile
├── generated by → AdaptiveDepth
└── used by → Orchestrator (TTL allocation)

AdaptiveDepthConfiguration
├── based on → TaskProfile
└── used by → Orchestrator (execution strategy)

Subplan
├── references → PlanStep (parent)
└── contains → PlanStep[] (substeps)
```

## Validation Rules Summary

### PlanStep Extensions
- step_index: 1-based, unique, <= total_steps
- total_steps: Must match plan.steps length
- clarity_state == "BLOCKED" → status = "invalid"
- dependencies: All must be "complete" before execution

### ExecutionPass
- pass_number: Sequential, >= 0
- phase: Valid enum value
- ttl_remaining: >= 0

### RefinementAction
- Cannot target executed steps (status: "complete" or "failed")
- inconsistency_detected == true → target must be "pending"

### TaskProfile
- reasoning_depth: 1-5, tier stability ±1
- information_sufficiency: 0.0-1.0
- All enum fields must be valid values

### Subplan
- depth_level: 1-5 (max nesting depth)
- If depth_level > 5 → creation fails gracefully

## State Transition Summary

### Step Status
- `pending` → `running` → `complete` | `failed` | `invalid`
- `invalid` → `pending` (only via refinement, only for unexecuted steps)

### Execution Pass Phases
- PLAN → EXECUTE → EVALUATE → REFINE → RE_EXECUTE (next pass)
- Or: PLAN → EXECUTE → EVALUATE → TERMINATE (converged or TTL expired)

### TaskProfile
- Created (Phase A) → Updated (pass boundaries, if complexity mismatch) → Used (TTL allocation)

