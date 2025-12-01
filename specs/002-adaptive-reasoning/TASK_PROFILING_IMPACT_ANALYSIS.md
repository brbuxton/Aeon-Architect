# Task Profiling Layer - Structural Impact Analysis

**Date**: 2025-01-27  
**Feature**: Introduction of Task Profiling Layer (versioned metadata structure inferred at runtime)  
**Scope**: Analysis of spec.md, plan.md, and tasks.md

## Executive Summary

The introduction of a Task Profiling Layer that replaces boolean complexity notions with a multi-dimensional, versioned metadata structure will require **moderate to significant changes** across all three documents. The impact is **concentrated in User Story 4 (Adaptive Depth)** and **Adaptive Depth Heuristics functional requirements**, but has **ripple effects** throughout the specification due to cross-cutting dependencies.

**Key Finding**: The current specification uses **implicit boolean complexity** (simple vs complex, low vs high) rather than explicit boolean flags, but the underlying model is still threshold-based and binary in nature. A Task Profile would transform this into a **multi-dimensional, continuous assessment** that evolves during execution.

---

## 1. Boolean Complexity Dependencies Identified

### 1.1 Explicit Boolean/Threshold References

#### spec.md

**User Story 4 - Adaptive Reasoning Depth Based on Task Complexity** (Lines 95-112):
- **Line 105**: "detect **low complexity**" → binary threshold
- **Line 106**: "detect **high complexity/ambiguity**" → binary threshold
- **Line 107**: "uncertainty is scored as **high**" → threshold-based
- **Line 110**: "detect **high complexity**" → binary threshold

**Functional Requirements - Adaptive Depth Heuristics** (Lines 236-250):
- **FR-026**: "adjust reasoning depth based on **detected task complexity**" → implicit boolean (complex vs not)
- **FR-027**: "detect task complexity through analysis" → produces boolean-like assessment
- **FR-029**: "adjust TTL allocations based on **detected complexity (higher complexity → higher TTL)**" → threshold-based binary decision
- **FR-030**: "select between **deep reasoning and shallow reasoning** strategies based on complexity and ambiguity scores" → binary choice (deep vs shallow)
- **FR-244**: "MAY revise their complexity assessment" → suggests single-dimensional assessment

**Success Criteria** (Line 329):
- **SC-005**: "correctly adjust reasoning depth (**shallow vs deep**) based on task complexity" → binary classification

**Key Entities - Adaptive Depth Configuration** (Line 315):
- `detected_complexity (score or category)` → could be boolean category
- `reasoning_mode (deep, shallow, balanced)` → ternary but still discrete categories

**Edge Cases** (Line 160):
- "tasks that start **simple** but become **complex**" → binary transition

#### plan.md

**Line 80**: "95% of **complex tasks** completed within 5 minutes" → binary classification

#### tasks.md

**Phase 7 - User Story 4** (Lines 181-207):
- **Line 183**: "based on detected **complexity, ambiguity, or uncertainty levels**" → threshold-based
- **Line 185**: "both **simple tasks** (e.g., 'add two numbers') and **complex tasks**" → binary examples
- **Line 191**: "Implement task **complexity detector**" → produces boolean-like output
- **Line 196**: "Implement reasoning mode selection (**deep/shallow/balanced**)" → discrete categories
- **Line 207**: "detect complexity and adjust reasoning depth" → binary decision model

### 1.2 Implicit Boolean Dependencies

**Multi-Pass Execution Logic**:
- **FR-060** (tasks.md line 143): "Update kernel orchestrator to use multi-pass loop for **complex tasks**" → implies boolean gate
- **User Story 1** (spec.md line 38): "submit a **complex task**" → assumes binary classification exists

**Recursive Planning**:
- **FR-009** (spec.md line 209): "decompose **complex plan steps**" → threshold-based trigger
- **User Story 2** (spec.md line 66): "encounters a **complex step**" → binary detection

**Convergence Engine Integration**:
- **FR-032** (spec.md line 246): "deeper reasoning when convergence fails" → binary response (fail vs succeed)
- **FR-033** (spec.md line 247): "deeper reasoning when recursive refinement is needed" → binary trigger

---

## 2. Functional Requirements Requiring Semantic Changes

### 2.1 Must Change (Core Impact)

#### FR-026: Adaptive Depth Heuristics - Complexity Detection
**Current**: "The system SHALL implement adaptive depth heuristics that adjust reasoning depth based on detected task complexity"

**Impact**: Must change from "detected task complexity" (single boolean/threshold) to "Task Profile dimensions" (reasoning_depth, information_sufficiency, tool_usage, output_breadth, confidence_requirements)

**Required Change**: Replace single-dimensional complexity detection with multi-dimensional profile inference

#### FR-027: Task Complexity Analysis
**Current**: "The adaptive depth heuristics SHALL detect task complexity through analysis of task characteristics (ambiguity, specificity, logical structure)"

**Impact**: Must expand to capture all Task Profile dimensions, not just complexity indicators

**Required Change**: Rewrite to describe Task Profile inference process that captures all five dimensions

#### FR-028: Ambiguity/Uncertainty Scoring
**Current**: "The adaptive depth heuristics SHALL calculate ambiguity or uncertainty scores for tasks and use these scores to inform depth decisions"

**Impact**: Ambiguity/uncertainty become one dimension of Task Profile, not standalone scores

**Required Change**: Reframe as Task Profile dimension extraction, where ambiguity contributes to information_sufficiency dimension

#### FR-029: TTL Allocation Based on Complexity
**Current**: "The adaptive depth heuristics SHALL adjust TTL allocations based on detected complexity (higher complexity → higher TTL)"

**Impact**: TTL allocation must consider multiple profile dimensions, not just complexity

**Required Change**: Rewrite to describe TTL allocation based on composite profile assessment

#### FR-030: Reasoning Mode Selection
**Current**: "The adaptive depth heuristics SHALL select between deep reasoning and shallow reasoning strategies based on complexity and ambiguity scores"

**Impact**: Reasoning mode selection must consider all profile dimensions, not just complexity/ambiguity

**Required Change**: Expand to multi-dimensional decision based on Task Profile

#### FR-080: Complexity Assessment Revision
**Current**: "The adaptive depth heuristics MAY revise their complexity assessment during execution"

**Impact**: Must revise entire Task Profile, not just complexity assessment

**Required Change**: Rewrite to describe Task Profile versioning and revision during execution

### 2.2 Should Change (Strong Recommendation)

#### FR-031: Semantic Validation Integration
**Current**: "The adaptive depth heuristics SHALL integrate with semantic validation layer to inform complexity detection"

**Impact**: Semantic validation should inform Task Profile dimensions, not just complexity

**Required Change**: Reframe as semantic validation informing profile dimension updates

#### FR-032: Convergence Engine Integration
**Current**: "The adaptive depth heuristics SHALL integrate with convergence engine to inform depth decisions (e.g., deeper reasoning when convergence fails)"

**Impact**: Convergence failures should update Task Profile dimensions (e.g., information_sufficiency), not just trigger binary depth increase

**Required Change**: Describe how convergence engine feedback updates Task Profile

#### FR-033: Recursive Planner Integration
**Current**: "The adaptive depth heuristics SHALL integrate with recursive planner to inform depth decisions (e.g., deeper reasoning when recursive refinement is needed)"

**Impact**: Recursive planning needs should update Task Profile (e.g., information_sufficiency, expected_tool_usage)

**Required Change**: Describe recursive planner feedback updating Task Profile dimensions

#### FR-078: Execution History - Adjustment Reason
**Current**: "The execution history SHALL record adaptive depth configuration details for each pass, including adjustment_reason indicating why reasoning depth or TTL was adjusted"

**Impact**: Must record Task Profile version history and dimension changes, not just adjustment reasons

**Required Change**: Expand to include Task Profile version tracking in execution history

### 2.3 May Change (Optional but Beneficial)

#### FR-034: Token-Pattern Analysis
**Current**: "The adaptive depth heuristics MAY include token-pattern analysis to detect complexity indicators"

**Impact**: Token patterns should inform multiple profile dimensions, not just complexity

**Optional Change**: Reframe as token-pattern analysis informing profile dimension inference

#### FR-035: Missing Details Detection
**Current**: "The adaptive depth heuristics MAY detect missing details or gradients in task specifications and increase depth accordingly"

**Impact**: Missing details directly map to information_sufficiency dimension

**Optional Change**: Explicitly map to information_sufficiency dimension

---

## 3. Success Criteria Requiring Changes

### 3.1 Must Change

#### SC-005: Reasoning Depth Adjustment Accuracy
**Current**: "Adaptive depth heuristics correctly adjust reasoning depth (shallow vs deep) based on task complexity for 85% of tasks"

**Impact**: Measurement must account for multi-dimensional profile, not binary complexity classification

**Required Change**: Rewrite to measure alignment with Task Profile dimensions (e.g., reasoning_depth dimension accuracy, information_sufficiency accuracy)

### 3.2 Should Change

#### SC-001: Complex Task Completion Time
**Current**: "Developers can submit complex, ambiguous tasks and receive converged results within 5 minutes"

**Impact**: "Complex tasks" definition becomes profile-based, not boolean

**Recommended Change**: Reframe as "tasks with high reasoning_depth and low information_sufficiency profiles"

#### SC-002: Multi-Pass Convergence Rate
**Current**: "The multi-pass execution loop successfully converges on complete, coherent solutions for 85% of complex tasks"

**Impact**: "Complex tasks" classification must be profile-based

**Recommended Change**: Reframe using Task Profile dimensions

---

## 4. User Stories Requiring Changes

### 4.1 Must Change

#### User Story 4: Adaptive Reasoning Depth Based on Task Complexity
**Current Title**: "Adaptive Reasoning Depth Based on Task Complexity"

**Impact**: Title and entire story assume boolean complexity model

**Required Changes**:
- **Title**: Change to "Adaptive Reasoning Depth Based on Task Profile"
- **Description** (Line 97): Replace "varying complexity" with "varying task profiles"
- **Acceptance Scenario 1** (Line 105): Replace "detect low complexity" with "infer Task Profile with low reasoning_depth requirement"
- **Acceptance Scenario 2** (Line 106): Replace "detect high complexity/ambiguity" with "infer Task Profile with high reasoning_depth and low information_sufficiency"
- **Acceptance Scenario 3** (Line 107): Replace "uncertainty is scored as high" with "Task Profile information_sufficiency dimension indicates high uncertainty"
- **Acceptance Scenario 5** (Line 109): Reframe token pattern analysis as contributing to profile dimensions
- **Acceptance Scenario 7** (Line 111): Replace "adjustment reason (e.g., high ambiguity score, missing details)" with "Task Profile dimension changes (e.g., information_sufficiency decreased, expected_tool_usage increased)"

**Independent Test** (Line 101): Replace "simple tasks" and "complex tasks" with tasks exhibiting different profile characteristics

### 4.2 Should Change

#### User Story 1: Multi-Pass Execution with Convergence
**Impact**: References to "complex task" assume boolean classification

**Recommended Changes**:
- **Line 38**: Replace "complex task" with "task requiring multiple reasoning passes" (profile-agnostic)
- **Line 42**: Replace "complex, ambiguous task" with "task with high reasoning_depth and low information_sufficiency profile"
- **Acceptance Scenario 1** (Line 46): Replace "complex task" with "task requiring multiple passes"

#### User Story 2: Recursive Planning and Plan Refinement
**Impact**: References to "complex step" assume boolean classification

**Recommended Changes**:
- **Line 57**: Replace "complex steps" with "steps requiring decomposition" (profile-agnostic)
- **Acceptance Scenario 2** (Line 66): Replace "complex step" with "step with high expected_tool_usage or low information_sufficiency"

---

## 5. New Functional Requirements Required

### 5.1 Required (Core Task Profile Support)

#### FR-NEW-001: Task Profile Inference
**The system SHALL infer a Task Profile at runtime for each request, capturing:**
- `reasoning_depth`: LLM's initial assessment of required reasoning depth (shallow, moderate, deep)
- `information_sufficiency`: Assessment of whether sufficient information is available (sufficient, partial, insufficient)
- `expected_tool_usage`: Expected number and types of tool invocations (none, minimal, moderate, extensive)
- `output_breadth`: Expected scope of output (narrow, moderate, broad)
- `confidence_requirements`: Required confidence level for completion (low, moderate, high)

#### FR-NEW-002: Task Profile Versioning
**The system SHALL maintain versioned Task Profile metadata throughout execution, allowing profile dimensions to be revised as new information becomes available during multi-pass execution.**

#### FR-NEW-003: Task Profile Persistence
**The system SHALL persist Task Profile versions in execution history, enabling inspection of profile evolution across passes.**

#### FR-NEW-004: Task Profile Integration with Adaptive Depth
**The adaptive depth heuristics SHALL consume Task Profile dimensions (not boolean complexity) to make reasoning depth, TTL allocation, and processing strategy decisions.**

#### FR-NEW-005: Task Profile Inference Timing
**The system SHALL infer the initial Task Profile during the planning phase, before execution begins, based on LLM analysis of the task description and context.**

#### FR-NEW-006: Task Profile Revision Triggers
**The system SHALL revise Task Profile dimensions when:**
- Semantic validation identifies information gaps (updates `information_sufficiency`)
- Convergence engine detects missing steps (updates `expected_tool_usage`, `output_breadth`)
- Recursive planning identifies decomposition needs (updates `reasoning_depth`, `expected_tool_usage`)
- Tool execution reveals unexpected complexity (updates relevant dimensions)

### 5.2 Strongly Recommended

#### FR-NEW-007: Task Profile Dimension Weighting
**The adaptive depth heuristics SHALL apply configurable weights to Task Profile dimensions when making depth decisions, allowing different dimensions to have different influence on TTL allocation and reasoning mode selection.**

#### FR-NEW-008: Task Profile Validation
**The system SHALL validate that inferred Task Profile dimensions are internally consistent (e.g., high reasoning_depth should correlate with extensive expected_tool_usage for complex tasks).**

### 5.3 Optional but Beneficial

#### FR-NEW-009: Task Profile Templates
**The system MAY support Task Profile templates for common task patterns (e.g., "data processing", "system design", "debugging") to accelerate profile inference.**

#### FR-NEW-010: Task Profile Metrics
**The system MAY track Task Profile accuracy metrics (e.g., how often initial profile predictions match actual execution characteristics) for continuous improvement.**

---

## 6. Conflicts with Dynamic, Inferred Profile-Based Model

### 6.1 Direct Conflicts

#### Conflict 1: Binary Reasoning Mode Selection
**Location**: FR-030, User Story 4 Acceptance Scenario 1-2, Adaptive Depth Configuration entity

**Issue**: Current spec assumes discrete reasoning modes (deep/shallow/balanced). Task Profile suggests continuous reasoning_depth dimension.

**Resolution Required**: Either:
- Keep discrete modes but derive from continuous profile dimension (e.g., reasoning_depth > 0.7 → deep)
- Replace with continuous reasoning_depth parameter

#### Conflict 2: Static Complexity Assessment
**Location**: Multiple FRs assume complexity is "detected" once at task start

**Issue**: Task Profile is versioned and evolves. Current spec allows revision (FR-080) but doesn't emphasize versioning.

**Resolution Required**: Emphasize versioned profile model throughout, not one-time detection

#### Conflict 3: Threshold-Based Decisions
**Location**: FR-029, FR-030, Acceptance Scenarios use "high/low" thresholds

**Issue**: Task Profile dimensions are continuous. Thresholds still needed but should be explicit and configurable.

**Resolution Required**: Define explicit thresholds for profile dimensions (e.g., information_sufficiency < 0.3 → insufficient)

### 6.2 Conceptual Conflicts

#### Conflict 4: Complexity as Single Dimension
**Location**: Throughout spec, "complexity" is treated as single attribute

**Issue**: Task Profile decomposes complexity into five dimensions. "Complexity" becomes emergent property, not direct dimension.

**Resolution Required**: Replace "complexity" references with specific profile dimensions or composite complexity metric derived from dimensions

#### Conflict 5: Simple vs Complex Binary
**Location**: User Story 4 Independent Test, Edge Cases, examples

**Issue**: Binary classification contradicts multi-dimensional profile model

**Resolution Required**: Replace binary examples with profile-based examples (e.g., "task with reasoning_depth=0.2, information_sufficiency=0.9" vs "task with reasoning_depth=0.8, information_sufficiency=0.3")

---

## 7. Minimum Required Edits (Grouped by Priority)

### 7.1 Required Changes (Must Implement)

#### spec.md

**Section: User Story 4** (Lines 95-112)
- Rewrite title: "Adaptive Reasoning Depth Based on Task Profile"
- Rewrite description to reference Task Profile dimensions
- Rewrite all 7 acceptance scenarios to use profile dimensions
- Rewrite Independent Test to use profile-based examples
- Add new acceptance scenario: "Given a Task Profile is inferred, When profile dimensions are extracted, Then all five dimensions (reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirements) are captured"

**Section: Functional Requirements - Adaptive Depth Heuristics** (Lines 236-250)
- **FR-026**: Rewrite to reference Task Profile inference
- **FR-027**: Rewrite as "Task Profile dimension inference through analysis"
- **FR-028**: Reframe as profile dimension extraction
- **FR-029**: Rewrite TTL allocation to use composite profile assessment
- **FR-030**: Expand reasoning mode selection to consider all profile dimensions
- **FR-080**: Rewrite as "Task Profile versioning and revision during execution"
- Add **FR-NEW-001** through **FR-NEW-006** (new requirements listed in Section 5.1)

**Section: Key Entities - Adaptive Depth Configuration** (Line 315)
- Replace `detected_complexity` with `task_profile` (reference to Task Profile entity)
- Add `task_profile_version` field
- Replace `reasoning_mode` with `reasoning_depth` (continuous or derived from profile)
- Update `adjustment_reason` to `profile_dimension_changes` (list of dimension updates)

**Section: Success Criteria** (Line 329)
- **SC-005**: Rewrite to measure Task Profile dimension accuracy

**Section: New Key Entity**
- Add **Task Profile** entity definition:
  - `profile_id` (unique identifier)
  - `profile_version` (version number, increments on revision)
  - `reasoning_depth` (numeric 0.0-1.0 or categorical)
  - `information_sufficiency` (numeric 0.0-1.0 or categorical)
  - `expected_tool_usage` (object: count_range, tool_types)
  - `output_breadth` (numeric 0.0-1.0 or categorical)
  - `confidence_requirements` (numeric 0.0-1.0 or categorical)
  - `inferred_at` (timestamp)
  - `inference_method` (how profile was inferred - LLM analysis, heuristics, etc.)

#### plan.md

**Section: Technical Context** (Line 80)
- Replace "complex tasks" with "tasks with high reasoning_depth profiles"

**Section: Implementation Phases**
- Add Task Profile inference to Phase 0 (Research) or Phase 1 (Design)
- Update Phase 7 (User Story 4) description to reference Task Profile

#### tasks.md

**Phase 7 - User Story 4** (Lines 181-207)
- **T080**: Change "Create AdaptiveDepthConfiguration model" to include Task Profile reference
- **T082**: Change "Implement task complexity detector" to "Implement Task Profile inference engine"
- Add new task: "T082a [US4] Implement Task Profile model with five dimensions in aeon/adaptive/profile_models.py"
- Add new task: "T082b [US4] Implement Task Profile versioning system in aeon/adaptive/profile_models.py"
- **T083-T084**: Reframe as "Implement [dimension] extraction from Task Profile"
- **T086**: Change "TTL allocation adjustment based on complexity" to "TTL allocation based on Task Profile composite assessment"
- **T087**: Change "reasoning mode selection" to "reasoning depth selection from Task Profile reasoning_depth dimension"
- **T090**: Change "complexity assessment revision" to "Task Profile dimension revision and versioning"
- **T091-T093**: Update integration tasks to describe profile dimension updates, not complexity indicators
- **T094**: Change "adjustment reason tracking" to "Task Profile version history tracking"

### 7.2 Strongly Recommended Changes

#### spec.md

**Section: User Story 1** (Lines 36-52)
- Replace "complex task" references with profile-agnostic language or specific profile characteristics

**Section: User Story 2** (Lines 55-72)
- Replace "complex step" with profile-based or decomposition-based language

**Section: Functional Requirements - Integration** (Lines 266-274)
- **FR-031**: Reframe semantic validation integration as profile dimension updates
- **FR-032**: Reframe convergence engine integration as profile dimension feedback
- **FR-033**: Reframe recursive planner integration as profile dimension updates
- **FR-078**: Expand execution history to include Task Profile version history

**Section: Assumptions** (Line 346)
- Update: "Adaptive depth heuristics can reliably infer Task Profile dimensions through linguistic and structural analysis"

#### plan.md

**Section: Implementation Phases - Phase 7**
- Add research task: "Research Task Profile inference methods and dimension extraction techniques"

#### tasks.md

**Phase 3-8**: Add profile-aware integration tasks where adaptive depth interacts with other components

### 7.3 Optional but Beneficial Changes

#### spec.md

**Section: Functional Requirements**
- Add **FR-NEW-007** through **FR-NEW-010** (optional requirements from Section 5.3)

**Section: Key Entities**
- Add Task Profile template entity (if FR-NEW-009 is included)

#### plan.md

**Section: Implementation Phases**
- Add optional phase for Task Profile template system (if FR-NEW-009 is included)

#### tasks.md

**Phase 9: Polish**
- Add optional tasks for Task Profile templates and metrics (if included)

---

## 8. Regeneration vs Surgical Patching Assessment

### 8.1 spec.md: **Surgical Patching Possible**

**Rationale**: 
- Core structure remains valid (user stories, FRs, SCs, entities)
- Changes are localized to Adaptive Depth sections and cross-references
- No fundamental architectural changes to other Tier-1 features

**Patching Strategy**:
1. Patch User Story 4 section (lines 95-112)
2. Patch Adaptive Depth Heuristics FRs (lines 236-250)
3. Patch Adaptive Depth Configuration entity (line 315)
4. Add new Task Profile entity definition
5. Patch SC-005 (line 329)
6. Patch cross-references in User Stories 1-2
7. Add new FRs (FR-NEW-001 through FR-NEW-006)

**Estimated Effort**: Moderate (15-20 targeted edits)

### 8.2 plan.md: **Surgical Patching Possible**

**Rationale**:
- High-level structure (phases, dependencies) remains unchanged
- Only technical context and phase descriptions need updates
- No structural reorganization required

**Patching Strategy**:
1. Patch Technical Context line 80
2. Update Phase 7 description
3. Add Task Profile research/design tasks to appropriate phases

**Estimated Effort**: Low (3-5 targeted edits)

### 8.3 tasks.md: **Surgical Patching Possible**

**Rationale**:
- Task structure and dependencies remain valid
- Only Phase 7 (User Story 4) tasks need modification
- Task numbering can be preserved with insertions (T082a, T082b)

**Patching Strategy**:
1. Patch Phase 7 task descriptions (T080-T096)
2. Insert new tasks (T082a, T082b) after T082
3. Update task descriptions to reference Task Profile

**Estimated Effort**: Moderate (10-15 task edits + 2 new tasks)

### 8.4 Conclusion: **All Documents Can Be Surgically Patched**

No regeneration required. All changes are localized and can be applied as targeted edits while preserving document structure, cross-references, and task dependencies.

---

## 9. Downstream Architectural Implications

### 9.1 Planner Component

**Impact**: **Moderate**

**Changes Required**:
- Planner must invoke Task Profile inference during initial plan generation
- Plan generation strategy must consider Task Profile dimensions (e.g., high expected_tool_usage → plan includes more tool steps)
- Plan structure may need metadata field for associated Task Profile version

**New Dependencies**:
- Planner → Task Profile Inference Engine

**Interface Changes**:
- `generate_plan(task_description, context)` → may return `(plan, task_profile)`

### 9.2 Validator Component

**Impact**: **Low to Moderate**

**Changes Required**:
- Semantic validator should contribute to Task Profile dimension updates (e.g., information gaps → update information_sufficiency)
- Validation reports may include profile dimension impact assessments

**New Dependencies**:
- Validator → Task Profile (for dimension updates)

**Interface Changes**:
- `validate(artifact)` → may return `(validation_report, profile_dimension_updates)`

### 9.3 Convergence Engine

**Impact**: **Moderate**

**Changes Required**:
- Convergence engine should update Task Profile when detecting missing information (information_sufficiency), unexpected tool needs (expected_tool_usage), or scope changes (output_breadth)
- Convergence criteria may be profile-aware (e.g., higher confidence_requirements → stricter convergence criteria)

**New Dependencies**:
- Convergence Engine → Task Profile (for dimension updates)

**Interface Changes**:
- `evaluate_convergence(execution_state)` → may return `(convergence_assessment, profile_dimension_updates)`

### 9.4 Adaptive Depth Heuristics

**Impact**: **High (Core Component)**

**Changes Required**:
- **Complete rewrite** of complexity detection logic to consume Task Profile dimensions
- TTL allocation algorithm must use composite profile assessment (all five dimensions)
- Reasoning depth selection must use reasoning_depth dimension (or derive from multiple dimensions)
- Must implement profile version tracking and revision logic

**New Dependencies**:
- Adaptive Depth → Task Profile (primary consumer)
- Adaptive Depth → Task Profile Inference Engine (for initial profile)
- Adaptive Depth → Task Profile Versioning (for revisions)

**Interface Changes**:
- `adjust_depth(task_profile, execution_context)` → replaces `adjust_depth(complexity_score, ambiguity_score)`
- Returns `(depth_config, profile_revision)` instead of `(depth_config, adjustment_reason)`

### 9.5 Execution History

**Impact**: **Moderate**

**Changes Required**:
- Execution history must store Task Profile versions for each pass
- History queries must support profile-based filtering (e.g., "show executions with high reasoning_depth")
- Profile evolution visualization in inspection interface

**New Dependencies**:
- Execution History → Task Profile (storage)
- Execution History → Task Profile Versioning (tracking)

**Interface Changes**:
- `record_pass(pass_data, task_profile_version)` → includes profile version
- `get_history(execution_id)` → returns profile version history
- New: `query_by_profile(profile_criteria)` → profile-based queries

### 9.6 Entity Models

**Impact**: **High**

**Changes Required**:

**ExecutionPass Model**:
- Add `task_profile_version` field (reference to Task Profile version at pass start)
- Add `profile_dimension_changes` field (track dimension updates during pass)

**Adaptive Depth Configuration Model**:
- Replace `detected_complexity` with `task_profile` (reference)
- Replace `reasoning_mode` with `reasoning_depth` (from profile)
- Replace `adjustment_reason` with `profile_dimension_changes`
- Add `profile_version` field

**Execution History Model**:
- Add `task_profile_history` field (array of Task Profile versions)
- Add `initial_profile` field (first profile version)
- Add `final_profile` field (last profile version)

**New Models Required**:
- **Task Profile Model** (see Section 7.1 for structure)
- **Task Profile Version Model** (version metadata, dimension values, revision reason)

### 9.7 Multi-Pass Orchestrator

**Impact**: **Low to Moderate**

**Changes Required**:
- Orchestrator must invoke Task Profile inference at loop start
- Must pass Task Profile version to adaptive depth heuristics
- Must track profile version changes across passes
- May use profile dimensions for loop termination decisions (e.g., if information_sufficiency becomes sufficient, may skip refinement)

**New Dependencies**:
- Orchestrator → Task Profile Inference Engine
- Orchestrator → Task Profile Versioning

**Interface Changes**:
- `execute_multipass(task, context)` → internally infers and tracks Task Profile
- Pass data includes `task_profile_version` field

### 9.8 Recursive Planner

**Impact**: **Low to Moderate**

**Changes Required**:
- Recursive planner should update Task Profile when detecting decomposition needs (reasoning_depth, expected_tool_usage)
- Subplan generation may consider parent task's profile dimensions

**New Dependencies**:
- Recursive Planner → Task Profile (for dimension updates)

**Interface Changes**:
- `refine_fragment(fragment, context)` → may return `(refined_fragment, profile_dimension_updates)`

### 9.9 Supervisor

**Impact**: **Low**

**Changes Required**:
- Supervisor repair actions may consider Task Profile dimensions (e.g., high confidence_requirements → stricter repair validation)

**New Dependencies**:
- Supervisor → Task Profile (optional, for context)

**Interface Changes**:
- `repair(issue, context, task_profile)` → optional profile parameter

### 9.10 Summary of Architectural Impact

| Component | Impact Level | Core Changes | New Dependencies |
|-----------|--------------|--------------|------------------|
| Adaptive Depth Heuristics | **High** | Complete rewrite to consume profile | Task Profile, Inference Engine, Versioning |
| Entity Models | **High** | New models, field replacements | Task Profile models |
| Execution History | **Moderate** | Profile version storage, queries | Task Profile, Versioning |
| Convergence Engine | **Moderate** | Profile dimension updates | Task Profile |
| Planner | **Moderate** | Profile inference, profile-aware planning | Task Profile Inference Engine |
| Multi-Pass Orchestrator | **Low-Moderate** | Profile inference, version tracking | Task Profile Inference Engine, Versioning |
| Recursive Planner | **Low-Moderate** | Profile dimension updates | Task Profile |
| Validator | **Low-Moderate** | Profile dimension updates | Task Profile |
| Supervisor | **Low** | Optional profile context | Task Profile (optional) |

---

## 10. Risk Assessment

### 10.1 High Risk Areas

1. **Adaptive Depth Heuristics Rewrite**: Complete logic change from boolean complexity to multi-dimensional profile. Risk of introducing bugs or performance regressions.

2. **Profile Inference Accuracy**: New inference engine must accurately extract five dimensions. Risk of poor initial profiles leading to incorrect depth decisions.

3. **Profile Versioning Complexity**: Versioning adds state management complexity. Risk of version inconsistencies or performance overhead.

4. **Backward Compatibility**: Existing tests and integrations assume boolean complexity. Risk of breaking changes.

### 10.2 Medium Risk Areas

1. **Entity Model Changes**: Field replacements may break serialization/deserialization. Risk of data migration needs.

2. **Integration Points**: Multiple components need profile integration. Risk of integration bugs.

3. **Performance Impact**: Profile inference and versioning add overhead. Risk of latency increases.

### 10.3 Low Risk Areas

1. **Documentation Updates**: Spec/plan/tasks changes are localized. Low risk of structural issues.

2. **Optional Features**: FR-NEW-007 through FR-NEW-010 are optional. Can be deferred if needed.

---

## 11. Implementation Recommendations

### 11.1 Phased Introduction Strategy

**Phase 1: Foundation** (Low Risk)
- Implement Task Profile model and basic inference engine
- Add profile to execution history (without using it for decisions)
- Validate profile inference accuracy

**Phase 2: Adaptive Depth Integration** (High Risk)
- Rewrite adaptive depth heuristics to consume profile
- Implement profile-based TTL allocation
- Test depth decisions against boolean model for consistency

**Phase 3: Profile Versioning** (Medium Risk)
- Implement versioning system
- Add profile revision triggers
- Validate version consistency

**Phase 4: Full Integration** (Medium Risk)
- Integrate profile updates from all components
- Enable profile-based queries in execution history
- Performance optimization

### 11.2 Migration Strategy

1. **Dual-Mode Support**: Initially support both boolean complexity and Task Profile, allowing gradual migration
2. **Feature Flag**: Use feature flag to enable/disable Task Profile usage
3. **Validation**: Compare profile-based decisions with boolean-based decisions during transition
4. **Deprecation**: Remove boolean complexity model after validation period

### 11.3 Testing Strategy

1. **Profile Inference Tests**: Validate accurate dimension extraction for known task types
2. **Profile Versioning Tests**: Validate version consistency and revision logic
3. **Integration Tests**: Test profile updates from all components
4. **Regression Tests**: Ensure profile-based decisions match or improve upon boolean-based decisions
5. **Performance Tests**: Measure inference and versioning overhead

---

## 12. Conclusion

The introduction of a Task Profiling Layer represents a **significant architectural evolution** from a boolean complexity model to a multi-dimensional, versioned metadata structure. While the impact is **concentrated in Adaptive Depth Heuristics**, it has **ripple effects** throughout the system.

**Key Takeaways**:

1. **All documents can be surgically patched** - no regeneration required
2. **Core impact is in User Story 4 and Adaptive Depth FRs** - these require substantial rewrites
3. **New requirements needed** - 6 required FRs for Task Profile support
4. **Architectural changes are moderate** - most components need integration, not rewrites
5. **Risk is manageable** - phased introduction and dual-mode support can mitigate risks

**Recommended Next Steps**:

1. Review and approve this impact analysis
2. Create detailed Task Profile model specification
3. Design Task Profile inference engine architecture
4. Update spec.md with required changes (Section 7.1)
5. Update plan.md and tasks.md with implementation tasks
6. Begin Phase 1 implementation (foundation)

---

**Document Status**: Analysis Complete  
**Next Action**: Review and decision on implementation approach

