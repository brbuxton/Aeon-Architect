# Research: Aeon Core

**Date**: 2025-01-27  
**Feature**: Aeon Core  
**Phase**: 0 - Research & Technology Decisions

## Technology Decisions

### Decision 1: LLM Adapter Interface Design

**Decision**: Create a unified LLM adapter interface that abstracts vLLM, llama-cpp-python, and remote API implementations.

**Rationale**: 
- Kernel must remain domain-agnostic and not depend on specific LLM implementations
- Multiple LLM backends may be needed (local inference vs remote API)
- Interface enables swapping LLM providers without kernel changes
- Aligns with constitutional Principle II (Separation of Concerns)

**Alternatives Considered**:
- Direct integration with single LLM provider: Rejected - violates separation of concerns, locks kernel to one provider
- LLM abstraction library (e.g., litellm): Considered but adds external dependency; custom interface keeps kernel minimal

**Implementation Approach**:
- Define `LLMAdapter` abstract base class with `generate(prompt, system_prompt, max_tokens)` method
- Implement adapters for vLLM, llama-cpp-python, and remote API (OpenAI/Anthropic style)
- Kernel only knows the interface, not implementation details
- Adapter handles retry logic with exponential backoff (3 attempts per FR-048)

### Decision 2: Validation Library Choice

**Decision**: Use pydantic for validation of plans, LLM outputs, and tool calls.

**Rationale**:
- pydantic provides Python-native validation with excellent error messages
- Type safety and schema validation in one library
- JSON schema export available for documentation
- Better integration with Python type hints than jsonschema
- Performance is sufficient for Sprint 1 scale

**Alternatives Considered**:
- jsonschema: Rejected - more verbose, less Pythonic, requires separate JSON schema definitions
- Custom validation: Rejected - reinventing the wheel, maintenance burden

**Implementation Approach**:
- Define pydantic models for Plan, PlanStep, LLMOutput, ToolCall
- Use pydantic validators for complex validation rules
- Export JSON schemas for documentation and external tooling

### Decision 3: Plan Schema Design

**Decision**: JSON schema for plans with required fields: goal (string), steps (array of step objects with step_id, description, status).

**Rationale**:
- JSON is declarative, human-readable, and language-agnostic
- Simple structure aligns with Sprint 1 minimalism
- Easy to validate with pydantic
- Supports future extensions without breaking changes

**Alternatives Considered**:
- YAML: Considered but JSON is simpler, more universal, and sufficient for Sprint 1
- Complex plan structures: Rejected - violates minimalism principle, adds unnecessary complexity

**Implementation Approach**:
```python
class PlanStep(BaseModel):
    step_id: str
    description: str
    status: Literal["pending", "running", "complete", "failed"]

class Plan(BaseModel):
    goal: str
    steps: List[PlanStep]
```

### Decision 4: Tool Interface Design

**Decision**: Tools are Python classes implementing a `Tool` interface with `name`, `description`, `input_schema`, `output_schema`, and `invoke()` method.

**Rationale**:
- Python classes provide natural encapsulation and type safety
- Schema-based validation ensures tool calls are validated before invocation
- Interface contract enables tool registry and discovery
- Deterministic invoke() function aligns with constitutional requirements

**Alternatives Considered**:
- Function-based tools: Rejected - harder to attach metadata (schemas, descriptions)
- Plugin system: Considered but overkill for Sprint 1; simple registry is sufficient

**Implementation Approach**:
```python
class Tool(ABC):
    name: str
    description: str
    input_schema: dict  # JSON schema
    output_schema: dict  # JSON schema
    
    @abstractmethod
    def invoke(self, **kwargs) -> dict:
        pass
```

### Decision 5: Memory Interface Design

**Decision**: Abstract `Memory` interface with `write(key, value)`, `read(key)`, and `search(prefix)` methods. Sprint 1 implementation uses in-memory dict.

**Rationale**:
- Interface enables future replacement with embeddings/vector search
- Simple K/V store sufficient for Sprint 1
- Prefix search (not regex) keeps implementation simple
- In-memory dict is fast and requires no external dependencies

**Alternatives Considered**:
- Direct dict usage: Rejected - violates interface abstraction, prevents future replacement
- SQLite for Sprint 1: Rejected - adds complexity, in-memory is sufficient
- Full-text search: Rejected - overkill for Sprint 1, prefix match is sufficient

**Implementation Approach**:
```python
class Memory(ABC):
    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        pass
    
    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def search(self, prefix: str) -> List[Tuple[str, Any]]:
        pass
```

### Decision 6: Supervisor Prompt Design

**Decision**: Supervisor uses same LLM with reduced system prompt focused on JSON repair. Prompt instructs: "Fix malformed JSON/tool calls/plan fragments. Do not add new meaning or tools. Return corrected JSON only."

**Rationale**:
- Same LLM ensures consistency and reduces dependencies
- Reduced prompt keeps supervisor focused on repair, not reasoning
- Explicit instructions prevent supervisor from adding semantic changes
- Aligns with FR-032 (supervisor only corrects, doesn't add meaning)

**Alternatives Considered**:
- Separate LLM for supervisor: Rejected - adds complexity, same LLM is sufficient
- Rule-based repair: Considered but LLM-based repair handles edge cases better
- Multiple repair strategies: Rejected - adds complexity, single strategy sufficient for Sprint 1

**Implementation Approach**:
- Supervisor system prompt: "You are a JSON repair assistant. Fix malformed JSON, tool calls, or plan structures. Return only the corrected JSON. Do not add new fields, tools, or semantic meaning."
- Supervisor retries up to 2 times (FR-050) before declaring unrecoverable

### Decision 7: Logging Approach

**Decision**: Use Python's `logging` module with custom JSONL formatter for cycle-by-cycle logs.

**Rationale**:
- Standard library logging is sufficient, no external dependencies
- JSONL format enables easy parsing and analysis
- Custom formatter can structure log entries per FR-037-039
- Non-blocking logging preserves kernel determinism

**Alternatives Considered**:
- External logging library (structlog): Considered but standard library is sufficient for Sprint 1
- File-based JSONL writer: Considered but logging module provides better integration
- External observability stack: Rejected - out of scope for Sprint 1

**Implementation Approach**:
- Custom JSONL formatter that outputs one JSON object per line
- Log entries include: step_number, plan_state, llm_output, supervisor_actions, tool_calls, ttl_remaining, errors, timestamp
- Logging is non-blocking and doesn't affect kernel execution

### Decision 8: Error Handling Strategy

**Decision**: Kernel uses exception handling with structured error responses. Tool errors mark step as failed and continue. LLM API errors retry with exponential backoff. Supervisor errors declare unrecoverable after 2 attempts.

**Rationale**:
- Exception handling is Pythonic and clear
- Structured error responses enable proper logging and state management
- Retry strategies align with FR-048 and FR-050
- Graceful degradation (continue on tool failure) enables partial plan success

**Alternatives Considered**:
- Result types (Rust-style): Considered but Python exceptions are more idiomatic
- Error codes: Rejected - exceptions provide better context and stack traces
- Fail-fast on all errors: Rejected - too strict, prevents partial success scenarios

**Implementation Approach**:
- Custom exception hierarchy: `AeonError`, `LLMError`, `ToolError`, `ValidationError`, `SupervisorError`
- Error objects include context (step_id, tool_name, error_type, message)
- Errors are logged and included in orchestration state

### Decision 9: State Management Approach

**Decision**: In-memory state object (`OrchestrationState`) containing plan, current_step, tool_history, llm_outputs, supervisor_actions, ttl_remaining. State is passed between kernel cycles.

**Rationale**:
- In-memory state is fast and sufficient for Sprint 1
- Explicit state object enables clear state transitions
- State immutability not required for Sprint 1 (can be added later)
- State persistence to disk is optional (Sprint 2)

**Alternatives Considered**:
- Immutable state: Considered but adds complexity, not required for Sprint 1
- State machine library: Rejected - overkill, simple state object is sufficient
- Database-backed state: Rejected - adds complexity, in-memory is sufficient

**Implementation Approach**:
```python
@dataclass
class OrchestrationState:
    plan: Plan
    current_step_id: Optional[str]
    tool_history: List[ToolCall]
    llm_outputs: List[dict]
    supervisor_actions: List[dict]
    ttl_remaining: int
```

### Decision 10: TTL Implementation

**Decision**: TTL counter decrements after each complete LLM cycle. When TTL reaches zero, loop terminates gracefully with structured "TTL expired" response.

**Rationale**:
- Simple counter is sufficient for Sprint 1
- Decrement after LLM cycle (not tool call) aligns with FR-035
- Graceful termination preserves state and enables debugging
- TTL prevents infinite loops and resource exhaustion

**Alternatives Considered**:
- Time-based TTL: Considered but cycle-based is simpler and more deterministic
- TTL per step: Rejected - adds complexity, global TTL is sufficient
- No TTL: Rejected - risk of infinite loops

**Implementation Approach**:
- TTL initialized at orchestration start (default: configurable, e.g., 50 cycles)
- Decremented in kernel after processing LLM response
- Checked before each LLM call; if zero, return structured expiration response

## Research Summary

All technology decisions align with constitutional principles:
- Kernel remains minimal and domain-agnostic
- All components communicate through interfaces
- No external dependencies beyond standard library and pydantic
- Simple, testable implementations
- Extensible architecture for future enhancements

No blocking research questions remain. Ready to proceed to Phase 1 design.

