# Quickstart: Sprint 2 - Adaptive Reasoning Engine

**Date**: 2025-01-27  
**Feature**: Sprint 2 - Adaptive Reasoning Engine

## Overview

Sprint 2 extends Aeon with five Tier-1 capabilities for adaptive, multi-pass reasoning:

1. **Multi-Pass Execution Loop**: Iterative execution with plan → execute → evaluate → refine cycles
2. **Recursive Planning & Re-Planning**: Automatic plan refinement and subplan generation
3. **Convergence Engine**: LLM-based detection of complete, coherent solutions
4. **Adaptive Depth Heuristics**: Task complexity inference and resource allocation
5. **Semantic Validation Layer**: Semantic quality checks for plans and execution artifacts

## Basic Usage

### Simple Multi-Pass Execution

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.convergence.engine import ConvergenceEngine
from aeon.validation.semantic import SemanticValidator
from aeon.plan.recursive import RecursivePlanner
from aeon.adaptive.heuristics import AdaptiveDepth
from aeon.llm.adapters.remote_api import RemoteAPIAdapter

# Initialize LLM adapter
llm = RemoteAPIAdapter(api_key="your-key", model="gpt-4")

# Initialize Sprint 2 components
convergence_engine = ConvergenceEngine(llm)
semantic_validator = SemanticValidator(llm)
recursive_planner = RecursivePlanner(llm)
adaptive_depth = AdaptiveDepth(llm, global_ttl_limit=100)

# Initialize orchestrator with Sprint 2 components
orchestrator = Orchestrator(
    llm=llm,
    convergence_engine=convergence_engine,
    semantic_validator=semantic_validator,
    recursive_planner=recursive_planner,
    adaptive_depth=adaptive_depth,
    ttl=10  # Base TTL (may be adjusted by adaptive depth)
)

# Execute task with multi-pass loop
task = "Design a system architecture for a web application with user authentication"
result = orchestrator.execute(task)

# Check result
if result.converged:
    print(f"Converged after {result.execution_history.overall_statistics['total_passes']} passes")
    print(f"Final output: {result.output}")
else:
    print(f"TTL expired or non-converged")
    print(f"Latest pass result: {result.latest_pass_result}")

# Inspect execution history
history = result.execution_history
for pass_obj in history.passes:
    print(f"Pass {pass_obj.pass_number}: {pass_obj.phase}")
    print(f"  Convergence: {pass_obj.evaluation_results['convergence'].converged}")
    print(f"  Validation issues: {len(pass_obj.evaluation_results['validation_report'].issues)}")
```

## Advanced Usage

### Custom Convergence Criteria

```python
# Define custom convergence thresholds
custom_criteria = {
    "completeness": 0.98,  # Higher threshold
    "coherence": 0.95,
    "consistency": 0.95
}

# Use in convergence assessment
convergence = convergence_engine.assess(
    validation_report=validation_report,
    plan=plan,
    steps=steps,
    outputs=outputs,
    custom_criteria=custom_criteria
)
```

### Inspecting Execution History

```python
# Access execution history
history = result.execution_history

# Iterate through passes
for pass_obj in history.passes:
    print(f"\n=== Pass {pass_obj.pass_number} ===")
    print(f"Phase: {pass_obj.phase}")
    print(f"TTL Remaining: {pass_obj.ttl_remaining}")
    
    # Check validation issues
    validation_report = pass_obj.evaluation_results['validation_report']
    if validation_report.issues:
        print(f"Validation Issues ({len(validation_report.issues)}):")
        for issue in validation_report.issues:
            print(f"  - {issue.type}: {issue.description} (severity: {issue.severity})")
    
    # Check convergence
    convergence = pass_obj.evaluation_results['convergence']
    print(f"Converged: {convergence.converged}")
    if not convergence.converged:
        print(f"Reason codes: {convergence.reason_codes}")
        print(f"Scores: completeness={convergence.scores['completeness_score']:.2f}, "
              f"coherence={convergence.scores['coherence_score']:.2f}")
    
    # Check refinements
    if pass_obj.refinement_changes:
        print(f"Refinements ({len(pass_obj.refinement_changes)}):")
        for action in pass_obj.refinement_changes:
            print(f"  - {action.action_type} on step {action.target_step_id}: {action.justification}")
```

### TaskProfile Inspection

```python
# Access TaskProfile from execution history
for pass_obj in history.passes:
    if hasattr(pass_obj, 'taskprofile'):
        profile = pass_obj.taskprofile
        print(f"Pass {pass_obj.pass_number} TaskProfile:")
        print(f"  Reasoning Depth: {profile.reasoning_depth}/5")
        print(f"  Information Sufficiency: {profile.information_sufficiency:.2f}")
        print(f"  Expected Tool Usage: {profile.expected_tool_usage}")
        print(f"  Output Breadth: {profile.output_breadth}")
        print(f"  Inference: {profile.raw_inference}")
```

### Handling TTL Expiration

```python
result = orchestrator.execute(task)

if result.result_type == "ttl_expired":
    print("TTL expired before convergence")
    print(f"Expiration point: {result.expiration_point}")
    
    if result.expiration_point == "phase_boundary":
        print(f"Latest completed pass: {result.latest_pass_result}")
    elif result.expiration_point == "mid_phase":
        if result.partial_result:
            print(f"Partial result from incomplete pass: {result.partial_result}")
        else:
            print(f"Latest completed pass: {result.latest_pass_result}")
    
    # Check quality metrics
    metadata = result.ttl_expired_metadata
    print(f"Completeness: {metadata['completeness_score']:.2f}")
    print(f"Coherence: {metadata['coherence_score']:.2f}")
    print(f"Reason codes: {metadata['reason_codes']}")
```

## Configuration

### Adaptive Depth Settings

```python
adaptive_depth = AdaptiveDepth(
    llm=llm,
    global_ttl_limit=200,  # Maximum TTL allocation
    global_resource_caps={
        "max_passes": 10,
        "max_refinements": 20
    }
)
```

### Recursive Planner Settings

```python
recursive_planner = RecursivePlanner(
    llm=llm,
    tool_registry=tool_registry,  # Optional
    max_nesting_depth=5  # Maximum subplan nesting depth
)
```

### Convergence Engine Settings

```python
convergence_engine = ConvergenceEngine(
    llm=llm,
    default_thresholds={
        "completeness": 0.95,
        "coherence": 0.90,
        "consistency": 0.90
    }
)
```

## Common Patterns

### Pattern 1: Complex Task with Multiple Passes

```python
# Submit complex, ambiguous task
task = "Build a REST API for a task management system with user authentication, task assignment, and notification features"

result = orchestrator.execute(task)

# System will automatically:
# 1. Infer TaskProfile (high reasoning_depth, low information_sufficiency)
# 2. Generate initial plan
# 3. Validate and refine plan
# 4. Execute steps
# 5. Evaluate convergence
# 6. Refine if needed
# 7. Re-execute until converged or TTL expires

print(f"Total passes: {result.execution_history.overall_statistics['total_passes']}")
print(f"Total refinements: {result.execution_history.overall_statistics['total_refinements']}")
```

### Pattern 2: Inspecting Refinement History

```python
# Track which fragments required multiple refinements
refinement_counts = {}
for pass_obj in history.passes:
    if pass_obj.refinement_changes:
        for action in pass_obj.refinement_changes:
            step_id = action.target_step_id
            refinement_counts[step_id] = refinement_counts.get(step_id, 0) + 1

# Identify problematic fragments
problematic_fragments = {
    step_id: count
    for step_id, count in refinement_counts.items()
    if count >= 3
}

print(f"Fragments requiring 3+ refinements: {problematic_fragments}")
```

### Pattern 3: Analyzing Convergence Blockers

```python
# Identify why convergence failed
for pass_obj in history.passes:
    convergence = pass_obj.evaluation_results['convergence']
    if not convergence.converged:
        print(f"Pass {pass_obj.pass_number} convergence blockers:")
        print(f"  Reason codes: {convergence.reason_codes}")
        print(f"  Detected issues: {convergence.detected_issues}")
        
        # Check validation issues
        validation_report = pass_obj.evaluation_results['validation_report']
        if validation_report.issues:
            issue_types = {}
            for issue in validation_report.issues:
                issue_types[issue.type] = issue_types.get(issue.type, 0) + 1
            print(f"  Validation issue types: {issue_types}")
```

## Error Handling

### LLM Errors

```python
try:
    result = orchestrator.execute(task)
except LLMError as e:
    print(f"LLM error: {e}")
    # System will attempt supervisor repair for JSON/schema errors
    # For semantic errors, system falls back to previous state
```

### Validation Errors

```python
try:
    validation_report = semantic_validator.validate(
        artifact_type="plan",
        plan=plan
    )
except ValidationError as e:
    print(f"Validation error: {e}")
    # System uses supervisor repair_json() for schema violations
```

### Refinement Limits

```python
# System automatically handles refinement attempt limits
# Per-fragment limit: 3 attempts
# Global limit: 10 total attempts

# If limits reached, system:
# 1. Stops refining that fragment
# 2. Marks fragment as requiring manual intervention (advisory metadata)
# 3. Continues execution with best available version
# 4. Does NOT halt execution or throw error
```

## Best Practices

1. **Monitor Execution History**: Always inspect execution history to understand multi-pass behavior
2. **Check Convergence Scores**: Review completeness/coherence scores to understand solution quality
3. **Review Validation Issues**: Check validation reports to identify plan quality issues
4. **Track Refinement Patterns**: Identify fragments requiring multiple refinements for tuning
5. **Respect TTL Limits**: Set appropriate TTL based on task complexity expectations
6. **Use Custom Criteria Sparingly**: Default convergence criteria are sensible; only override if needed

## Next Steps

- See [data-model.md](./data-model.md) for detailed entity schemas
- See [contracts/interfaces.md](./contracts/interfaces.md) for interface definitions
- See [spec.md](./spec.md) for complete feature specification
- See [plan.md](./plan.md) for implementation plan

