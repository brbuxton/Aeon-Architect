# Quickstart Guide: Aeon Core

**Date**: 2025-11-18  
**Feature**: Aeon Core  
**Phase**: 1 - Design

## Overview

This guide provides a quick introduction to using Aeon Core for LLM orchestration. It demonstrates the core workflow: plan generation, tool invocation, and state management.

## Prerequisites

- Python 3.11+
- LLM access (vLLM, llama-cpp-python, or remote API)
- pydantic library

## Installation

```bash
# Clone repository
git clone <repository-url>
cd aeon-architect

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Basic Usage

### 1. Initialize Components

```python
from aeon.llm.adapters.remote_api import RemoteAPIAdapter
from aeon.memory.kv_store import InMemoryKVStore
from aeon.tools.registry import ToolRegistry
from aeon.tools.stubs.echo import EchoTool
from aeon.supervisor.repair import Supervisor
from aeon.validation.schema import Validator
from aeon.kernel.orchestrator import Orchestrator

# Initialize LLM adapter
llm = RemoteAPIAdapter(api_key="your-key", model="gpt-4")

# Initialize memory
memory = InMemoryKVStore()

# Initialize tool registry and register tools
tool_registry = ToolRegistry()
tool_registry.register(EchoTool())

# Initialize supervisor
supervisor = Supervisor(
    llm_adapter=llm,
    system_prompt="You are a JSON repair assistant..."
)

# Initialize validator
validator = Validator()

# Create orchestrator
orchestrator = Orchestrator(
    llm_adapter=llm,
    memory=memory,
    tool_registry=tool_registry,
    supervisor=supervisor,
    validator=validator,
    ttl=50,  # 50 cycles max
)
```

### 2. Execute a Simple Request

```python
# Execute orchestration
result = orchestrator.execute(
    user_request="Calculate the sum of 5 and 10"
)

# Check result
print(f"Status: {result['status']}")
print(f"Plan: {result['plan']}")
print(f"Final State: {result['final_state']}")
```

### 3. Access Orchestration State

```python
# Get current state during execution
state = orchestrator.get_state()

print(f"Current Step: {state.current_step_id}")
print(f"TTL Remaining: {state.ttl_remaining}")
print(f"Tool History: {len(state.tool_history)} calls")
```

## Example Scenarios

### Scenario 1: Plan Generation

```python
# Request generates a multi-step plan
result = orchestrator.execute(
    user_request="Research the weather in San Francisco and summarize it"
)

# Plan structure:
# {
#   "goal": "Research weather in San Francisco and summarize",
#   "steps": [
#     {"step_id": "1", "description": "Search for weather data", "status": "complete"},
#     {"step_id": "2", "description": "Summarize findings", "status": "complete"}
#   ]
# }
```

### Scenario 2: Tool Invocation

```python
# Register a calculator tool
from aeon.tools.stubs.calculator import CalculatorTool
tool_registry.register(CalculatorTool())

# Execute request that uses the tool
result = orchestrator.execute(
    user_request="Calculate 15 * 23"
)

# Tool call is logged in state.tool_history:
# {
#   "tool_name": "calculator",
#   "arguments": {"operation": "multiply", "a": 15, "b": 23},
#   "result": {"value": 345},
#   "step_id": "1"
# }
```

### Scenario 3: Memory Operations

```python
# Store data in memory
memory.write("user_name", "Alice")
memory.write("user_age", 30)

# Read from memory
name = memory.read("user_name")  # Returns "Alice"

# Search by prefix
results = memory.search("user_")  # Returns [("user_name", "Alice"), ("user_age", 30)]
```

### Scenario 4: Multi-Mode Step Execution

```python
# Plan with tool-based step
plan_with_tool = {
    "goal": "Calculate and store result",
    "steps": [
        {
            "step_id": "1",
            "description": "Calculate 5 + 10",
            "status": "pending",
            "tool": "calculator"  # Tool-based execution
        },
        {
            "step_id": "2",
            "description": "Reason about the result",
            "status": "pending",
            "agent": "llm"  # Explicit LLM reasoning
        }
    ]
}

# Execute plan with mixed execution modes
result = orchestrator.execute(
    user_request="Calculate and reason",
    initial_plan=Plan(**plan_with_tool)
)

# Missing-tool step automatically handled:
# - Validator detects missing tool
# - Supervisor attempts repair with tool registry
# - If repair fails, falls back to LLM reasoning
```

### Scenario 5: Error Handling

```python
# Supervisor automatically repairs malformed JSON
# If LLM produces invalid JSON, supervisor attempts repair (up to 2 times)

# Tool errors mark step as failed and continue
# If tool throws exception, step status = "failed", execution continues

# TTL expiration
# If TTL reaches zero, orchestration stops gracefully:
result = orchestrator.execute(
    user_request="Complex multi-step task",
    # ... with low TTL
)
# result['status'] == "ttl_expired"
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run kernel tests with coverage
pytest tests/unit/kernel/ --cov=aeon.kernel --cov-report=html

# Run specific test
pytest tests/unit/kernel/test_orchestrator.py
```

### Integration Tests

```bash
# Test complete orchestration loop
pytest tests/integration/test_orchestration_loop.py

# Test supervisor repair
pytest tests/integration/test_supervisor_repair.py
```

### Contract Tests

```bash
# Test interface contracts
pytest tests/contract/test_memory_interface.py
pytest tests/contract/test_tool_interface.py
```

## Logging

### View JSONL Logs

```python
# Logs are written to aeon.log (JSONL format)
# Each line is a complete orchestration cycle

import json

with open("aeon.log", "r") as f:
    for line in f:
        cycle = json.loads(line)
        print(f"Step {cycle['step_number']}: {cycle['plan_state']}")
        print(f"TTL: {cycle['ttl_remaining']}")
        if cycle['errors']:
            print(f"Errors: {cycle['errors']}")
```

## Creating Custom Tools

```python
from aeon.tools.interface import Tool
from typing import Dict, Any

class MyCustomTool(Tool):
    name = "my_tool"
    description = "Does something useful"
    input_schema = {
        "type": "object",
        "properties": {
            "input_param": {"type": "string"}
        },
        "required": ["input_param"]
    }
    output_schema = {
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    }
    
    def invoke(self, **kwargs) -> Dict[str, Any]:
        input_param = kwargs["input_param"]
        # Do something
        return {"result": f"Processed: {input_param}"}

# Register custom tool
tool_registry.register(MyCustomTool())
```

## Common Patterns

### Pattern 1: Pre-created Plan

```python
from aeon.plan.parser import PlanParser

# Create plan manually
plan_dict = {
    "goal": "Execute specific steps",
    "steps": [
        {"step_id": "1", "description": "Step 1", "status": "pending"},
        {"step_id": "2", "description": "Step 2", "status": "pending"}
    ]
}
plan = PlanParser.parse(plan_dict)

# Execute with pre-created plan
result = orchestrator.execute(
    user_request="Execute this plan",
    initial_plan=plan
)
```

### Pattern 2: State Inspection

```python
# Monitor execution progress
state = orchestrator.get_state()

for step in state.plan.steps:
    print(f"Step {step.step_id}: {step.status}")

if state.current_step_id:
    print(f"Currently executing: {state.current_step_id}")
```

### Pattern 3: Error Recovery

```python
try:
    result = orchestrator.execute(user_request="...")
except OrchestrationError as e:
    # Check if supervisor can help
    if e.recoverable:
        # Retry with supervisor repair
        pass
    else:
        # Unrecoverable error
        print(f"Error: {e}")
```

## Next Steps

1. **Read the specification**: See [spec.md](./spec.md) for complete requirements
2. **Review the data model**: See [data-model.md](./data-model.md) for entity definitions
3. **Check interface contracts**: See [contracts/interfaces.md](./contracts/interfaces.md) for API details
4. **Explore examples**: Check `examples/` directory for more use cases

## Troubleshooting

### Issue: LLM API errors

**Solution**: Check LLM adapter configuration. Ensure API keys are set correctly. Retry logic (3 attempts) should handle transient failures.

### Issue: Tool validation failures

**Solution**: Verify tool input/output schemas match the tool call. Check supervisor repair logs for details.

### Issue: TTL expiration

**Solution**: Increase TTL value when creating orchestrator, or break request into smaller plans.

### Issue: Memory search not finding keys

**Solution**: Remember search uses prefix matching. Use exact prefix, case-sensitive.

## Performance Tips

- Use in-memory storage for Sprint 1 (fast, sufficient)
- Keep plans under 10 steps for best results
- Monitor TTL to avoid premature expiration
- Check logs for performance bottlenecks

## Architecture Notes

- Kernel remains under 800 LOC (constitutional requirement)
- All domain logic is in external modules (tools, memory, supervisor)
- Interfaces enable component replacement without kernel changes
- State is in-memory for Sprint 1 (persistence optional in Sprint 2)

