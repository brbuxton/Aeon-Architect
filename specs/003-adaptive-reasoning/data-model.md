# Data Model: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Date**: 2025-01-27  
**Feature**: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

## Overview

This document defines the data models for Sprint 2's multi-pass reasoning engine. All models are implemented as Pydantic models for validation and serialization. Models are organized by domain: TaskProfile, Execution, Refinement, Convergence, Validation, and Planning.

## Core Entities

### TaskProfile

Represents inferred task characteristics used for adaptive depth heuristics and TTL allocation.

**Fields**:
- `profile_version: int` - Version number for TaskProfile updates
- `reasoning_depth: int` - Ordinal scale 1-5 (1=very shallow, 2=shallow, 3=moderate, 4=deep, 5=very deep)
- `information_sufficiency: float` - Float 0.0-1.0 (0.0=insufficient, 1.0=sufficient)
- `expected_tool_usage: Literal["none", "minimal", "moderate", "extensive"]` - Expected tool usage level
- `output_breadth: Literal["narrow", "moderate", "broad"]` - Expected output breadth
- `confidence_requirement: Literal["low", "medium", "high"]` - Required confidence level
- `raw_inference: str` - Natural-language explanation summarizing how each dimension was determined

**Default Values** (when inference fails):
- `reasoning_depth = 3`
- `information_sufficiency = 0.5`
- `expected_tool_usage = "moderate"`
- `output_breadth = "moderate"`
- `confidence_requirement = "medium"`
- `raw_inference = "Default profile: moderate complexity assumed"`

**Validation Rules**:
- `reasoning_depth` must be in range [1, 5]
- `information_sufficiency` must be in range [0.0, 1.0]
- All enum fields must match defined literals
- `raw_inference` must be non-empty string

**State Transitions**:
- Created: During Phase A (TaskProfile inference)
- Updated: At pass boundaries when complexity mismatch detected (convergence failure AND validation issues AND clarity_state patterns)

### ExecutionPass

Represents a single iteration of the multi-pass loop.

**Fields**:
- `pass_number: int` - Sequential identifier (0 for initial plan, 1-N for execution passes)
- `phase: Literal["A", "B", "C", "D"]` - Current phase (A=TaskProfile, B=Initial Plan, C=Execution, D=Adaptive Depth)
- `plan_state: dict` - Snapshot of plan at pass start (JSON-serializable)
- `execution_results: list[dict]` - Step outputs and tool results (JSON-serializable)
- `evaluation_results: dict` - Convergence assessment and semantic validation report (JSON-serializable)
- `refinement_changes: list[dict]` - Plan/step modifications if any (JSON-serializable)
- `ttl_remaining: int` - TTL cycles remaining
- `timing_information: dict` - Contains start_time, end_time, duration (ISO 8601 timestamps)

**Validation Rules**:
- `pass_number` must be >= 0
- `phase` must be one of ["A", "B", "C", "D"]
- `ttl_remaining` must be >= 0
- All dict/list fields must be JSON-serializable

**State Transitions**:
- Created: At start of each pass
- Updated: During pass execution (execution_results, evaluation_results, refinement_changes)
- Completed: At end of pass (timing_information.end_time set)

### ExecutionHistory

Structured history of completed multi-pass execution.

**Fields**:
- `execution_id: str` - Unique identifier for execution
- `task_input: str` - Original task description
- `configuration: dict` - Convergence criteria, TTL, adaptive depth settings (JSON-serializable)
- `passes: list[ExecutionPass]` - Ordered list of execution passes
- `final_result: dict` - Converged or TTL-expired result (JSON-serializable)
- `overall_statistics: dict` - Contains total_passes, total_refinements, convergence_achieved, total_time

**Validation Rules**:
- `execution_id` must be non-empty string
- `task_input` must be non-empty string
- `passes` must be non-empty list
- All dict/list fields must be JSON-serializable

**Storage**: In-memory only for Sprint 2 (returned as part of execution result)

### RefinementAction

A modification to plan or steps during refinement phase.

**Fields**:
- `action_type: Literal["ADD", "MODIFY", "REMOVE", "REPLACE"]` - Type of refinement action
- `target_step_id: Optional[str]` - Identifier of step being changed (None for plan-level changes)
- `target_plan_section: Optional[str]` - Plan section being changed (None for step-level changes)
- `new_step: Optional[dict]` - New step content for ADD/MODIFY actions (JSON-serializable)
- `changes: dict` - Modified content description (JSON-serializable)
- `reason: str` - Explanation of why refinement was needed
- `semantic_validation_input: list[dict]` - Validation issues that triggered refinement (JSON-serializable)
- `inconsistency_detected: bool` - True if refinement creates inconsistency with executed steps

**Validation Rules**:
- `action_type` must match defined literals
- Either `target_step_id` or `target_plan_section` must be provided (not both, not neither)
- `new_step` required for ADD/MODIFY actions
- `reason` must be non-empty string
- All dict/list fields must be JSON-serializable

**Constraints**:
- Cannot target executed steps (status: complete or failed)
- Only targets pending or future steps

### ConvergenceAssessment

Result from convergence engine determining whether task execution has converged.

**Fields**:
- `converged: bool` - Whether convergence was achieved
- `reason_codes: list[str]` - Array of strings indicating why convergence was/wasn't achieved
- `completeness_score: float` - Numeric score 0.0-1.0
- `coherence_score: float` - Numeric score 0.0-1.0
- `consistency_status: dict` - Object with plan/step/answer/memory alignment status (JSON-serializable)
- `detected_issues: list[str]` - Array of issue descriptions
- `metadata: dict` - Additional evaluation data (JSON-serializable)

**Default Thresholds** (when no custom criteria provided):
- `completeness_score >= 0.95` → converged
- `coherence_score >= 0.90` → converged
- `consistency_status` must indicate alignment → converged

**Validation Rules**:
- `completeness_score` and `coherence_score` must be in range [0.0, 1.0]
- `reason_codes` must be non-empty list when converged == false
- All dict/list fields must be JSON-serializable

**State Transitions**:
- Created: After each execution pass during evaluate phase
- Used: By orchestrator to decide whether to continue or terminate

### SemanticValidationReport

Output from semantic validation layer identifying semantic quality issues.

**Fields**:
- `validation_id: str` - Unique identifier for validation run
- `artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"]` - Type of artifact validated
- `issues: list[ValidationIssue]` - Array of detected issues
- `overall_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]` - Highest severity detected
- `issue_summary: dict` - Counts by issue type (JSON-serializable)
- `proposed_repairs: list[dict]` - Array of repair suggestions (JSON-serializable)

**Validation Rules**:
- `validation_id` must be non-empty string
- `artifact_type` must match defined literals
- `issues` must be non-empty list when issues detected
- `overall_severity` must match defined literals
- All dict/list fields must be JSON-serializable

### ValidationIssue

Individual issue detected by semantic validation.

**Fields**:
- `issue_id: str` - Unique identifier for issue
- `type: Literal["specificity", "relevance", "consistency", "hallucination", "do_say_mismatch"]` - Issue type
- `severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]` - Severity (determined by LLM)
- `description: str` - Human-readable issue explanation
- `location: Optional[dict]` - Where issue was detected (step_id, artifact reference) (JSON-serializable)
- `proposed_repair: Optional[dict]` - Suggested fix generated by LLM (JSON-serializable)

**Validation Rules**:
- `issue_id` must be non-empty string
- `type` must match defined literals
- `severity` must match defined literals
- `description` must be non-empty string
- All dict fields must be JSON-serializable

### Step (Enhanced)

Enhanced step model with context propagation fields.

**Fields** (extending existing PlanStep):
- `step_index: int` - 1-based step number
- `total_steps: int` - Total number of steps in plan
- `incoming_context: Optional[str]` - Context from previous steps (may be empty initially)
- `handoff_to_next: Optional[str]` - Context to pass to next step (may be empty initially)
- `description: str` - Step goal/description (existing)
- `dependencies: list[str]` - Array of step IDs that must complete before this step (existing)
- `provides: list[str]` - Array of artifacts provided by this step (existing)
- `status: Literal["pending", "running", "complete", "failed", "invalid"]` - Step status (enhanced with "invalid")
- `step_output: Optional[str]` - Output from step execution
- `clarity_state: Optional[Literal["CLEAR", "PARTIALLY_CLEAR", "BLOCKED"]]` - Clarity state returned by step execution LLM

**Validation Rules**:
- `step_index` must be >= 1
- `total_steps` must be >= step_index
- `status` must match defined literals
- `clarity_state` must match defined literals when present

**State Transitions**:
- `pending` → `running` → `complete` (normal execution)
- `pending` → `running` → `failed` (execution failure)
- `pending` → `running` → `invalid` (when clarity_state == BLOCKED or refinement creates inconsistency)

**Constraints**:
- Steps with status `complete` or `failed` are immutable (cannot be refined)
- Steps with status `invalid` can be refined but output may be preserved

## Relationships

### TaskProfile → ExecutionPass
- One TaskProfile per ExecutionPass (snapshot at pass start)
- TaskProfile may be updated at pass boundaries (new version)

### ExecutionPass → ExecutionHistory
- Many ExecutionPass objects belong to one ExecutionHistory
- Ordered by pass_number

### RefinementAction → ExecutionPass
- Many RefinementAction objects may be generated during one ExecutionPass
- Applied to plan/step state for next pass

### ConvergenceAssessment → ExecutionPass
- One ConvergenceAssessment per ExecutionPass (generated during evaluate phase)
- Used to decide whether to continue or terminate

### SemanticValidationReport → ExecutionPass
- One SemanticValidationReport per ExecutionPass (generated during evaluate phase)
- Consumed by ConvergenceEngine for coherence/consistency assessments

### ValidationIssue → SemanticValidationReport
- Many ValidationIssue objects belong to one SemanticValidationReport
- Grouped by type in issue_summary

### Step → Plan
- Many Step objects belong to one Plan
- Ordered by step_index
- Connected via dependencies and provides fields

## Data Flow

1. **Phase A**: TaskProfile inferred → stored in ExecutionPass
2. **Phase B**: Plan generated → Steps created with step_index, total_steps, incoming_context, handoff_to_next
3. **Phase C**: Steps executed → step_output and clarity_state populated → SemanticValidationReport generated → ConvergenceAssessment generated
4. **Refinement**: ValidationIssue objects trigger RefinementAction generation → RefinementAction applied to plan/step state
5. **Phase D**: TaskProfile updated at pass boundaries when triggered → new version stored in next ExecutionPass

## Serialization

All models are JSON-serializable via Pydantic's `.model_dump()` method. ExecutionHistory is returned as part of execution result (in-memory only for Sprint 2).

