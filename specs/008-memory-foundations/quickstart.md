# Quickstart Guide: Memory Foundations

**Date**: 2025-12-17  
**Feature**: Memory Foundations  
**Phase**: 1 - Design

## Overview

This guide provides a quick introduction to using Short-Term Memory (STM) and Session subsystems in Aeon. It demonstrates session-scoped memory that persists across multiple executions (turns) within a single session, with capacity and TTL-based eviction.

## Prerequisites

- Python 3.11+
- LLM access (vLLM, llama-cpp-python, or remote API)
- pydantic>=2.0.0 library
- Existing Aeon Core installation (Sprint 1)

## Installation

```bash
# Ensure you have Aeon Core installed
pip install -e .

# No additional dependencies required (uses existing pydantic)
```

## Basic Usage

### 1. Initialize Components with Memory and Session

```python
from aeon.llm.adapters.remote_api import RemoteAPIAdapter
from aeon.memory.stm import STM
from aeon.memory.null_memory import NullMemory
from aeon.session.manager import SessionManager
from aeon.tools.registry import ToolRegistry
from aeon.supervisor.repair import Supervisor
from aeon.validation.schema import Validator
from aeon.kernel.orchestrator import Orchestrator

# Initialize LLM adapter
llm = RemoteAPIAdapter(api_key="your-key", model="gpt-4")

# Initialize Session subsystem
session_manager = SessionManager()

# Initialize memory (STM or NullMemory)
memory = STM(capacity=100, initial_ttl=10)  # STM with capacity 100, TTL 10
# OR use NullMemory for no-op behavior:
# memory = NullMemory()

# Initialize tool registry and register tools
tool_registry = ToolRegistry()
# ... register tools ...

# Initialize supervisor
supervisor = Supervisor(
    llm_adapter=llm,
    system_prompt="You are a JSON repair assistant..."
)

# Initialize validator
validator = Validator()

# Create orchestrator with memory and session
orchestrator = Orchestrator(
    llm_adapter=llm,
    memory=memory,  # Memory Access Interface
    session_manager=session_manager,  # Session subsystem
    tool_registry=tool_registry,
    supervisor=supervisor,
    validator=validator,
    ttl=50,  # Execution TTL (TaskProfile TTL)
)
```

### 2. Execute Multiple Turns in a Session

```python
# Create a session
session_id = session_manager.create_session()
print(f"Created session: {session_id}")

# Execute first turn
result1 = orchestrator.execute(
    user_request="What is the capital of France?",
    session_id=session_id
)

# Execute second turn (memory from first turn is available)
result2 = orchestrator.execute(
    user_request="What is the population of that city?",
    session_id=session_id  # Same session_id
)

# Memory entries from first turn are accessible in second turn
# STM automatically selects relevant entries for prompt injection
```

### 3. Access Memory Usage Statistics

```python
# Get memory usage stats for a session
stats = memory.get_usage_stats(session_id)
print(f"Memory used: {stats.memory_used}")
print(f"Entries considered: {stats.memory_entries_considered}")
print(f"Entries injected: {stats.memory_entries_injected}")
print(f"Total entries: {stats.total_entries}")
print(f"Expired entries: {stats.expired_entries}")
```

### 4. List Memory Entries (Metadata Only)

```python
# List all memory entries for a session (metadata only, no content)
entries = memory.list_entries(session_id)
for entry in entries:
    print(f"Entry: {entry.execution_id}/{entry.phase}, TTL: {entry.ttl}, Created: {entry.created_at}")
```

## Example Scenarios

### Scenario 1: Session-Scoped Memory Across Turns

```python
# Create session
session_id = session_manager.create_session()

# Turn 1: Store information about user preferences
result1 = orchestrator.execute(
    user_request="I prefer Python over Java for backend development",
    session_id=session_id
)
# Memory entry created after Phase B (Reasoning Steps)

# Turn 2: Use stored information
result2 = orchestrator.execute(
    user_request="Recommend a backend framework for me",
    session_id=session_id
)
# STM selects relevant entries from Turn 1 and injects into Phase B prompt
# LLM can leverage previous context about Python preference
```

### Scenario 2: Memory with Capacity Eviction

```python
# Create STM with small capacity for testing
memory = STM(capacity=5, initial_ttl=10)

session_id = session_manager.create_session()

# Write multiple entries until capacity is exceeded
for i in range(10):
    result = memory.write_entry(
        session_id=session_id,
        execution_id=f"exec_{i}",
        phase="B",
        content={"user_request": f"Request {i}", "response": f"Response {i}"}
    )
    print(f"Write {i}: success={result.success}, evicted={result.evicted_count}")

# Capacity eviction occurs deterministically
# Oldest entries are evicted when capacity is exceeded
```

### Scenario 3: TTL-Based Entry Expiration

```python
# Create STM with short TTL for testing
memory = STM(capacity=100, initial_ttl=2)  # TTL = 2

session_id = session_manager.create_session()

# Write entry
result = memory.write_entry(
    session_id=session_id,
    execution_id="exec_1",
    phase="B",
    content={"user_request": "Hello", "response": "Hi there"}
)

# Access memory multiple times (each access decrements TTL)
for i in range(3):
    entries = memory.read_entries(session_id)
    stats = memory.get_usage_stats(session_id)
    print(f"Access {i}: entries={len(entries)}, expired={stats.expired_entries}")

# After 3 accesses, TTL reaches 0 and entry is expired
# Expired entries are excluded from read_entries() results
```

### Scenario 4: Memory Injection into Prompts

```python
# Configure prompt registry for memory injection
from aeon.prompts.registry import PromptRegistry

prompt_registry = PromptRegistry()

# Register prompt with memory injection enabled
prompt_registry.register(
    prompt_id="phase_b_reasoning",
    template="... {memory_context} ...",
    memory_injection_enabled=True,  # Enable memory injection
    injection_point="memory_context"
)

# When orchestrator renders this prompt:
# 1. Calls memory.select_for_injection() with context
# 2. STM selects relevant entries and extracts fields
# 3. Prompt registry formats and inserts context blocks
# 4. Non-authoritative marker is applied
```

### Scenario 5: Session Lifecycle Management

```python
# Create session
session_id = session_manager.create_session()

# Check session state
state = session_manager.get_session_state(session_id)
print(f"Session state: {state.state}, TTL: {state.ttl}")

# Execute multiple turns
for i in range(5):
    result = orchestrator.execute(
        user_request=f"Request {i}",
        session_id=session_id
    )
    # After each execution, orchestrator calls notify_execution_complete()
    # Session subsystem decrements Session TTL
    
    state = session_manager.get_session_state(session_id)
    print(f"After turn {i}: state={state.state}, ttl={state.ttl}")

# When Session TTL reaches 0, session is marked as expired
# Orchestrator receives expired status and triggers memory cleanup
```

### Scenario 6: Graceful Session Closure

```python
# Create session
session_id = session_manager.create_session()

# Execute some turns
for i in range(3):
    orchestrator.execute(
        user_request=f"Request {i}",
        session_id=session_id
    )

# Gracefully close session (before TTL expiration)
close_result = session_manager.close_session(session_id)
print(f"Close success: {close_result.success}")

# Clean up memory entries
delete_result = memory.delete_session_entries(session_id)
print(f"Deleted {delete_result.entries_removed} entries")
```

### Scenario 7: NullMemory (Memory Disabled)

```python
# Use NullMemory to disable memory functionality
memory = NullMemory()

# All memory operations succeed but store nothing
result = memory.write_entry(
    session_id="session_1",
    execution_id="exec_1",
    phase="B",
    content={"test": "data"}
)
print(f"Write success: {result.success}")  # True, but nothing stored

entries = memory.read_entries("session_1")
print(f"Entries: {len(entries)}")  # 0

# Execution continues normally with memory disabled
# Useful for testing or when memory is not needed
```

### Scenario 8: Memory Selection for Injection

```python
# Write entries from different phases and executions
session_id = session_manager.create_session()

# Execution 1, Phase B
memory.write_entry(
    session_id=session_id,
    execution_id="exec_1",
    phase="B",
    content={
        "user_request": "What is Python?",
        "response": "Python is a programming language..."
    }
)

# Execution 1, Phase D
memory.write_entry(
    session_id=session_id,
    execution_id="exec_1",
    phase="D",
    content={
        "refinement_reason": "Need more detail",
        "updated_goal": "Explain Python in detail"
    }
)

# Execution 2, Phase B (current execution)
# Select memory for injection
injection_result = memory.select_for_injection(
    session_id=session_id,
    context={
        "current_phase": "B",
        "current_execution_id": "exec_2",
        "injection_point": "phase_b_memory"
    },
    budget=1000  # Token budget
)

print(f"Context blocks: {len(injection_result['context_blocks'])}")
print(f"Marker: {injection_result['non_authoritative_marker']}")

# STM selects Phase B entries from earlier executions
# Extracts user_request and response fields
# Orders by recency (most recent first)
# Applies injection budget as hard upper bound
```

## Testing

### Unit Tests

```bash
# Run STM unit tests
pytest tests/unit/test_stm.py

# Run NullMemory unit tests
pytest tests/unit/test_null_memory.py

# Run Session subsystem unit tests
pytest tests/unit/test_session_manager.py
```

### Integration Tests

```bash
# Test memory integration with orchestrator
pytest tests/integration/test_memory_integration.py

# Test session integration with orchestrator
pytest tests/integration/test_session_integration.py

# Test memory across multiple executions
pytest tests/integration/test_memory_multi_turn.py
```

### Contract Tests

```bash
# Test Memory Access Interface contract
pytest tests/contract/test_memory_interface.py

# Test Session Subsystem Interface contract
pytest tests/contract/test_session_interface.py
```

## Observability

### Memory Operation Logging

```python
# Memory operations are logged with structural metadata (no content)
# Log format:
# {
#   "operation": "write_entry",
#   "session_id": "session_123",
#   "execution_id": "exec_1",
#   "phase": "B",
#   "entry_count": 1,
#   "success": true
# }

# Check logs for memory usage patterns
import json

with open("aeon.log", "r") as f:
    for line in f:
        cycle = json.loads(line)
        if "memory" in cycle:
            print(f"Memory: {cycle['memory']}")
```

### Phase E Metadata

```python
# Phase E metadata includes memory usage statistics
result = orchestrator.execute(
    user_request="...",
    session_id=session_id
)

# Access Phase E metadata
metadata = result.get("phase_e_metadata", {})
memory_stats = metadata.get("memory", {})

print(f"Memory used: {memory_stats.get('memory_used')}")
print(f"Entries considered: {memory_stats.get('memory_entries_considered')}")
print(f"Entries injected: {memory_stats.get('memory_entries_injected')}")
print(f"Failures: {memory_stats.get('memory_failures')}")
```

## Common Patterns

### Pattern 1: Session Per User Request

```python
# Create new session for each user request
def handle_user_request(user_request: str):
    session_id = session_manager.create_session()
    try:
        result = orchestrator.execute(
            user_request=user_request,
            session_id=session_id
        )
        return result
    finally:
        # Clean up session and memory
        memory.delete_session_entries(session_id)
```

### Pattern 2: Long-Running Session

```python
# Create session for long-running conversation
session_id = session_manager.create_session()

# Multiple turns in same session
for user_request in user_requests:
    result = orchestrator.execute(
        user_request=user_request,
        session_id=session_id
    )
    
    # Check if session expired
    state = session_manager.get_session_state(session_id)
    if state.state == "expired":
        # Session TTL exhausted, create new session
        session_id = session_manager.create_session()

# Clean up when done
memory.delete_session_entries(session_id)
```

### Pattern 3: Memory-Aware Prompt Configuration

```python
# Configure prompts with memory injection
prompt_registry.register(
    prompt_id="phase_b_reasoning",
    template="""
    User request: {user_request}
    
    {memory_context}
    
    Please respond to the user request.
    """,
    memory_injection_enabled=True,
    injection_point="memory_context",
    injection_budget=500  # Token budget
)

# Memory injection is automatic when prompt is rendered
# STM selects relevant entries and extracts fields
# Prompt registry formats and inserts context
```

## Troubleshooting

### Issue: Memory entries not persisting across turns

**Solution**: Ensure you're using the same `session_id` for both turns. Each session has its own memory scope.

### Issue: Memory entries expired too quickly

**Solution**: Increase `initial_ttl` value when creating STM. TTL decrements on each STM access, so entries accessed frequently expire faster.

### Issue: Memory capacity exceeded

**Solution**: Increase `capacity` value when creating STM, or implement custom eviction logic. Eviction is deterministic (LRU or creation-order based).

### Issue: Memory injection not working

**Solution**: 
1. Verify `memory_injection_enabled=True` in prompt registry
2. Check that memory entries exist for the session
3. Verify injection budget is sufficient
4. Ensure phase allows memory injection (Phase C and E never inject)

### Issue: Session expired unexpectedly

**Solution**: Session TTL decrements on execution completion. Increase Session TTL initial value (default: 3) or create new session when expired.

## Performance Tips

- Use STM for session-scoped memory (fast, in-memory)
- Use NullMemory when memory is not needed (zero overhead)
- Keep memory capacity reasonable (100-1000 entries per session)
- Monitor TTL values to balance recency vs. retention
- Check memory usage stats in Phase E metadata

## Architecture Notes

- Memory subsystem is external to kernel (clean interface)
- Session subsystem is autonomous (manages own TTL)
- All memory operations degrade gracefully (never block execution)
- Memory content is never logged (content-free observability)
- TTL management is autonomous (orchestrator has no knowledge)

## Next Steps

1. **Read the specification**: See [spec.md](./spec.md) for complete requirements
2. **Review the data model**: See [data-model.md](./data-model.md) for entity definitions
3. **Check interface contracts**: See [contracts/interfaces.md](./contracts/interfaces.md) for API details
4. **Explore research decisions**: See [research.md](./research.md) for design rationale

## Key Constraints

- **No Disk I/O**: STM and SessionManager never write to disk
- **Graceful Degradation**: All operations never raise exceptions
- **Autonomous TTL**: Session and Memory Entry TTLs managed independently
- **Session Scoping**: All memory entries associated with exactly one session_id
- **Content-Free Observability**: Logs and metadata never contain raw memory content

