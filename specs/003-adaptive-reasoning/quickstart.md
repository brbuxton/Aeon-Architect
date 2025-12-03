# Quickstart: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

**Date**: 2025-01-27  
**Feature**: Sprint 2 - Adaptive Multi-Pass Reasoning Engine

## Overview

Sprint 2 extends Aeon's single-pass orchestration system with a deterministic, adaptive, multi-pass reasoning engine. This guide demonstrates how to use the new multi-pass capabilities.

## Basic Usage

### Simple Multi-Pass Execution

```python
from aeon.kernel.orchestrator import Orchestrator
from aeon.llm.adapters.remote_api import RemoteAPIAdapter
from aeon.tools.registry import ToolRegistry

# Initialize components
llm_adapter = RemoteAPIAdapter(api_key="your-key")
tool_registry = ToolRegistry()
orchestrator = Orchestrator(llm_adapter, tool_registry)

# Submit a complex task
task = "Design a system architecture for a web application with user authentication"

# Execute multi-pass reasoning
result = orchestrator.execute(task)

# Check result
if result.converged:
    print(f"Task completed in {result.total_passes} passes")
    print(f"Final answer: {result.final_output}")
else:
    print(f"Task did not converge after {result.total_passes} passes")
    print(f"Reason: {result.convergence_reason_codes}")
```

### Inspecting Execution History

```python
# Access execution history
history = result.execution_history

# Inspect each pass
for pass_data in history.passes:
    print(f"Pass {pass_data.pass_number} - Phase {pass_data.phase}")
    print(f"  TTL remaining: {pass_data.ttl_remaining}")
    print(f"  Duration: {pass_data.timing_information['duration']}s")
    
    # Check convergence assessment
    if pass_data.evaluation_results.get('convergence'):
        conv = pass_data.evaluation_results['convergence']
        print(f"  Converged: {conv.converged}")
        print(f"  Completeness: {conv.completeness_score}")
        print(f"  Coherence: {conv.coherence_score}")
    
    # Check semantic validation
    if pass_data.evaluation_results.get('validation'):
        val = pass_data.evaluation_results['validation']
        print(f"  Validation issues: {len(val.issues)}")
        print(f"  Overall severity: {val.overall_severity}")
    
    # Check refinements
    if pass_data.refinement_changes:
        print(f"  Refinements: {len(pass_data.refinement_changes)}")
        for refinement in pass_data.refinement_changes:
            print(f"    - {refinement.action_type} on {refinement.target_step_id}")

# Overall statistics
stats = history.overall_statistics
print(f"\nTotal passes: {stats['total_passes']}")
print(f"Total refinements: {stats['total_refinements']}")
print(f"Convergence achieved: {stats['convergence_achieved']}")
print(f"Total time: {stats['total_time']}s")
```

## Advanced Usage

### Custom Convergence Criteria

```python
from aeon.convergence.engine import ConvergenceEngine
from aeon.convergence.models import ConvergenceAssessment

# Create convergence engine with custom criteria
convergence_engine = ConvergenceEngine(llm_adapter)

custom_criteria = {
    "completeness_threshold": 0.98,  # Higher threshold
    "coherence_threshold": 0.95,      # Higher threshold
    "consistency_threshold": 0.95    # Higher threshold
}

# Use custom criteria in orchestrator configuration
config = {
    "convergence_criteria": custom_criteria,
    "global_ttl_limit": 20,
    "refinement_limits": {
        "per_fragment": 3,
        "global": 10
    }
}

result = orchestrator.execute(task, config=config)
```

### TaskProfile Inspection

```python
# Access TaskProfile from execution history
for pass_data in history.passes:
    if pass_data.plan_state.get('task_profile'):
        profile = pass_data.plan_state['task_profile']
        print(f"Pass {pass_data.pass_number} TaskProfile:")
        print(f"  Reasoning depth: {profile.reasoning_depth}")
        print(f"  Information sufficiency: {profile.information_sufficiency}")
        print(f"  Expected tool usage: {profile.expected_tool_usage}")
        print(f"  Output breadth: {profile.output_breadth}")
        print(f"  Confidence requirement: {profile.confidence_requirement}")
        print(f"  Inference: {profile.raw_inference}")
```

### Semantic Validation Reports

```python
# Access semantic validation reports
for pass_data in history.passes:
    if pass_data.evaluation_results.get('validation'):
        val_report = pass_data.evaluation_results['validation']
        
        print(f"\nValidation Report (Pass {pass_data.pass_number}):")
        print(f"  Artifact type: {val_report.artifact_type}")
        print(f"  Overall severity: {val_report.overall_severity}")
        print(f"  Issues found: {len(val_report.issues)}")
        
        # Group issues by type
        for issue in val_report.issues:
            print(f"\n  Issue: {issue.type} ({issue.severity})")
            print(f"    Description: {issue.description}")
            if issue.location:
                print(f"    Location: {issue.location}")
            if issue.proposed_repair:
                print(f"    Proposed repair: {issue.proposed_repair}")
        
        # Issue summary
        print(f"\n  Issue summary: {val_report.issue_summary}")
```

### Refinement Actions

```python
# Inspect refinement actions
for pass_data in history.passes:
    if pass_data.refinement_changes:
        print(f"\nRefinements (Pass {pass_data.pass_number}):")
        for refinement in pass_data.refinement_changes:
            print(f"  Action: {refinement.action_type}")
            print(f"    Target: {refinement.target_step_id or refinement.target_plan_section}")
            print(f"    Reason: {refinement.reason}")
            print(f"    Inconsistency detected: {refinement.inconsistency_detected}")
            
            if refinement.semantic_validation_input:
                print(f"    Triggered by {len(refinement.semantic_validation_input)} validation issues")
```

### Handling TTL Expiration

```python
# Check for TTL expiration
if result.result_type == "ttl_expired":
    print("TTL expired before convergence")
    print(f"Expiration point: {result.expiration_point}")
    print(f"Latest pass: {result.ttl_expired_metadata['pass_number']}")
    
    if result.latest_pass_result:
        print(f"Latest completed pass result: {result.latest_pass_result}")
    elif result.partial_result:
        print(f"Partial result from incomplete pass: {result.partial_result}")
    
    # Quality metrics from convergence engine
    metadata = result.ttl_expired_metadata
    print(f"Completeness score: {metadata.get('completeness_score')}")
    print(f"Coherence score: {metadata.get('coherence_score')}")
    print(f"Reason codes: {metadata.get('reason_codes')}")
```

### Step Context Propagation

```python
# Inspect step context propagation
for pass_data in history.passes:
    plan = pass_data.plan_state.get('plan')
    if plan and plan.steps:
        print(f"\nStep Context (Pass {pass_data.pass_number}):")
        for step in plan.steps:
            print(f"  Step {step.step_index}/{step.total_steps}: {step.description}")
            if step.incoming_context:
                print(f"    Incoming context: {step.incoming_context[:100]}...")
            if step.handoff_to_next:
                print(f"    Handoff to next: {step.handoff_to_next[:100]}...")
            if step.clarity_state:
                print(f"    Clarity state: {step.clarity_state}")
```

## Configuration Options

### Global TTL Limit

```python
config = {
    "global_ttl_limit": 15,  # Maximum TTL across all passes
    "adaptive_depth": {
        "enabled": True,
        "update_threshold": "strict"  # or "lenient"
    }
}

result = orchestrator.execute(task, config=config)
```

### Refinement Limits

```python
config = {
    "refinement_limits": {
        "per_fragment": 3,   # Max refinements per plan fragment
        "global": 10         # Max total refinements across all fragments
    },
    "nesting_depth_limit": 5  # Max recursive planning depth
}

result = orchestrator.execute(task, config=config)
```

### Convergence Criteria

```python
config = {
    "convergence_criteria": {
        "completeness_threshold": 0.95,
        "coherence_threshold": 0.90,
        "consistency_threshold": 0.90
    }
}

result = orchestrator.execute(task, config=config)
```

## Error Handling

### LLM API Failures

```python
try:
    result = orchestrator.execute(task)
except LLMError as e:
    print(f"LLM API error: {e}")
    print(f"Retry attempts: {e.retry_count}")
    print(f"Final error: {e.original_error}")
```

### Refinement Limit Exceeded

```python
try:
    result = orchestrator.execute(task)
except RefinementLimitError as e:
    print(f"Refinement limit exceeded: {e}")
    print(f"Fragment: {e.fragment_id}")
    print(f"Attempts: {e.attempt_count}")
    # Execution continues with best available state
```

### Nesting Depth Exceeded

```python
try:
    result = orchestrator.execute(task)
except NestingDepthError as e:
    print(f"Nesting depth exceeded: {e}")
    print(f"Current depth: {e.current_depth}")
    print(f"Max depth: {e.max_depth}")
    # Fragment marked for manual intervention
```

## CLI Usage

### Basic Execution

```bash
aeon "Design a system architecture for a web application with user authentication"
```

### With Configuration

```bash
aeon --config config.json "Design a distributed system architecture"
```

### Inspect Execution History

```bash
aeon --inspect execution_history.json
```

## Best Practices

1. **Start with default configuration**: The system works well with default settings for most tasks.

2. **Monitor execution history**: Inspect execution history to understand how the system refined plans and detected convergence.

3. **Adjust TTL limits**: For very complex tasks, increase global_ttl_limit. For simple tasks, the system will allocate minimal TTL automatically.

4. **Custom convergence criteria**: Use custom convergence criteria for tasks requiring higher quality thresholds.

5. **Handle TTL expiration**: Always check for TTL expiration and inspect quality metrics to understand why convergence wasn't achieved.

6. **Review semantic validation**: Check semantic validation reports to understand plan quality issues and refinement triggers.

7. **Inspect TaskProfile**: Review TaskProfile to understand how the system assessed task complexity and allocated resources.

## Examples

See `tests/integration/` for comprehensive examples of:
- Multi-pass execution with convergence
- Recursive planning and refinement
- Semantic validation
- Adaptive depth heuristics
- TTL expiration handling

