# Interface Contracts: Aeon Core

**Date**: 2025-01-27  
**Feature**: Aeon Core  
**Phase**: 1 - Design

## Overview

Aeon Core uses interface contracts to enforce separation of concerns between the kernel and external modules. All interfaces are defined as Python abstract base classes (ABC) with clear method signatures and contracts.

## LLM Adapter Interface

**Purpose**: Abstract LLM inference behind a unified interface supporting multiple backends.

**Interface**: `aeon.llm.interface.LLMAdapter`

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional

class LLMAdapter(ABC):
    """Abstract interface for LLM inference adapters."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate LLM response.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Dict with keys:
                - "text": Generated text (str)
                - "usage": Token usage dict (optional)
                - "model": Model identifier (str, optional)
                
        Raises:
            LLMError: On API failure, timeout, or other errors
        """
        pass
    
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return True if adapter supports streaming responses."""
        pass
```

**Contract Requirements**:
- Must handle retry logic internally (3 attempts with exponential backoff per FR-048)
- Must raise LLMError on failures after retries exhausted
- Must return consistent response format
- Must be thread-safe if used in concurrent contexts (not required for Sprint 1)

**Implementations**:
- `aeon.llm.adapters.vllm.VLLMAdapter`
- `aeon.llm.adapters.llama_cpp.LlamaCppAdapter`
- `aeon.llm.adapters.remote_api.RemoteAPIAdapter`

## Memory Interface

**Purpose**: Abstract key/value storage behind a replaceable interface.

**Interface**: `aeon.memory.interface.Memory`

```python
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

class Memory(ABC):
    """Abstract interface for memory storage."""
    
    @abstractmethod
    def write(self, key: str, value: Any) -> None:
        """
        Store a value with the given key.
        
        Args:
            key: Unique identifier (non-empty string)
            value: Value to store (must be serializable)
            
        Raises:
            MemoryError: On storage failure
        """
        pass
    
    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.
        
        Args:
            key: Identifier to look up
            
        Returns:
            Stored value or None if key not found
            
        Raises:
            MemoryError: On read failure
        """
        pass
    
    @abstractmethod
    def search(self, prefix: str) -> List[Tuple[str, Any]]:
        """
        Find all keys starting with the given prefix.
        
        Args:
            prefix: Prefix to match
            
        Returns:
            List of (key, value) tuples for matching keys
            
        Raises:
            MemoryError: On search failure
        """
        pass
```

**Contract Requirements**:
- Keys must be strings (non-empty)
- Values must be serializable (JSON-compatible)
- Prefix search must be case-sensitive (Sprint 1)
- Operations must be atomic (no partial writes)
- read() returns None (not raises exception) for missing keys

**Implementations**:
- `aeon.memory.kv_store.InMemoryKVStore` (Sprint 1)

## Tool Interface

**Purpose**: Define contract for tool registration and invocation.

**Interface**: `aeon.tools.interface.Tool`

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """Abstract interface for tools."""
    
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON schema
    output_schema: Dict[str, Any]  # JSON schema
    
    @abstractmethod
    def invoke(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with validated arguments.
        
        Args:
            **kwargs: Arguments validated against input_schema
            
        Returns:
            Result dict validated against output_schema
            
        Raises:
            ToolError: On execution failure
        """
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input against input_schema (default implementation uses pydantic)."""
        pass
    
    def validate_output(self, result: Dict[str, Any]) -> bool:
        """Validate output against output_schema (default implementation uses pydantic)."""
        pass
```

**Contract Requirements**:
- invoke() must be deterministic (same inputs → same outputs)
- invoke() must not access kernel internals
- invoke() must not contain orchestration logic
- Input/output validation must use provided schemas
- Tool errors must raise ToolError (not generic exceptions)

**Implementations**:
- `aeon.tools.stubs.echo.EchoTool`
- `aeon.tools.stubs.calculator.CalculatorTool`

## Tool Registry Interface

**Purpose**: Manage tool registration and lookup.

**Interface**: `aeon.tools.registry.ToolRegistry`

```python
from typing import Dict, List, Optional
from aeon.tools.interface import Tool

class ToolRegistry:
    """Tool registration and lookup."""
    
    def register(self, tool: Tool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If tool name already registered
        """
        pass
    
    def get(self, name: str) -> Optional[Tool]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None if not found
        """
        pass
    
    def list_all(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        pass
    
    def unregister(self, name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
        """
        pass
    
    def export_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Export tool registry for LLM prompts.
        
        Returns:
            List of tool dicts with:
                - "name": Tool name
                - "description": Tool description
                - "input_schema": Input JSON schema
                - "output_schema": Output JSON schema
                - "example": Example invocation (optional)
        """
        pass
```

**Contract Requirements**:
- Tool names must be unique
- Registration must validate tool schema
- get() returns None (not raises) for missing tools
- Thread-safe registration (not required for Sprint 1)
- export_tools_for_llm() must return complete tool information for LLM consumption

## Supervisor Interface

**Purpose**: Define contract for supervisor repair operations.

**Interface**: `aeon.supervisor.repair.Supervisor`

```python
from typing import Dict, Any, Optional
from aeon.llm.interface import LLMAdapter

class Supervisor:
    """Supervisor for repairing malformed LLM outputs."""
    
    def __init__(self, llm_adapter: LLMAdapter, system_prompt: str):
        """
        Initialize supervisor.
        
        Args:
            llm_adapter: LLM adapter to use for repair
            system_prompt: Reduced system prompt for repair focus
        """
        pass
    
    def repair_json(
        self,
        malformed_json: str,
        expected_schema: Optional[Dict[str, Any]] = None,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed JSON.
        
        Args:
            malformed_json: Malformed JSON string
            expected_schema: Expected JSON schema (optional)
            max_attempts: Maximum repair attempts (default 2)
            
        Returns:
            Repaired JSON as dict
            
        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        pass
    
    def repair_tool_call(
        self,
        malformed_call: Dict[str, Any],
        tool_schema: Dict[str, Any],
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed tool call.
        
        Args:
            malformed_call: Malformed tool call dict
            tool_schema: Tool input schema
            max_attempts: Maximum repair attempts (default 2)
            
        Returns:
            Repaired tool call dict
            
        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        pass
    
    def repair_plan(
        self,
        malformed_plan: Dict[str, Any],
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair malformed plan structure.
        
        Args:
            malformed_plan: Malformed plan dict
            max_attempts: Maximum repair attempts (default 2)
            
        Returns:
            Repaired plan dict
            
        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        pass
    
    def repair_missing_tool_step(
        self,
        step: Dict[str, Any],
        available_tools: List[Dict[str, Any]],
        plan_goal: str,
        max_attempts: int = 2,
    ) -> Dict[str, Any]:
        """
        Repair step with missing or invalid tool reference.
        
        Args:
            step: Step dict with missing/invalid tool
            available_tools: List of available tools (from ToolRegistry.export_tools_for_llm())
            plan_goal: Overall plan goal for context
            max_attempts: Maximum repair attempts (default 2)
            
        Returns:
            Repaired step dict with valid tool reference
            
        Raises:
            SupervisorError: If repair fails after max_attempts
        """
        pass
```

**Contract Requirements**:
- Must not add new tools or semantic meaning (FR-032)
- Must only correct syntax and structure
- Must retry up to max_attempts (default 2 per FR-050)
- Must raise SupervisorError if repair fails
- Must use same LLM adapter as main orchestration
- repair_missing_tool_step() must only reference tools from available_tools list (FR-066)

## Validation Interface

**Purpose**: Define contract for schema validation.

**Interface**: `aeon.validation.schema.Validator`

```python
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError

class Validator:
    """Schema validator for plans, LLM outputs, and tool calls."""
    
    def validate_plan(self, plan_dict: Dict[str, Any]) -> bool:
        """
        Validate plan structure.
        
        Args:
            plan_dict: Plan as dict
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    def validate_llm_output(
        self,
        output: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Validate LLM output structure.
        
        Args:
            output: LLM output as dict
            expected_schema: Expected schema (optional)
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    def validate_tool_call(
        self,
        tool_call: Dict[str, Any],
        tool_schema: Dict[str, Any],
    ) -> bool:
        """
        Validate tool call against tool schema.
        
        Args:
            tool_call: Tool call as dict
            tool_schema: Tool input schema
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    def validate_step_tool(
        self,
        step: PlanStep,
        tool_registry: ToolRegistry,
    ) -> ValidationResult:
        """
        Validate that step references a registered tool.
        
        Populates step.errors with error messages if validation fails.
        The step object is modified in-place (errors field is set).
        
        Args:
            step: PlanStep object to validate (modified in-place)
            tool_registry: Tool registry to check against
            
        Returns:
            ValidationResult with:
                - "valid": bool - True if step.tool is valid or step has no tool field
                - "error": Optional[str] - error message if invalid (also added to step.errors)
                
        Raises:
            ValidationError: If step structure is invalid (not tool-related)
            
        Note:
            This method modifies step.errors in-place. If step.tool is missing or invalid,
            step.errors is populated with error messages (e.g., "Tool 'X' not found in registry").
            Supervisor repair MUST read step.errors and clear it on successful repair.
        """
        pass
```

**Contract Requirements**:
- Must use pydantic for validation
- Must raise ValidationError (not return False) on failure
- Must provide detailed error messages
- Must validate before tool invocation, memory writes, plan updates (FR-024-026)
- validate_step_tool() must detect missing or invalid tool references (FR-063, FR-064)
- validate_step_tool() must populate step.errors field (not just return ValidationResult) when validation fails
- Supervisor repair methods must read step.errors and clear it on successful repair

## Step Executor Interface

**Purpose**: Execute plan steps in different modes (tool-based, LLM reasoning, fallback).

**Interface**: `aeon.kernel.executor.StepExecutor`

```python
from typing import Dict, Any
from aeon.plan.models import PlanStep
from aeon.memory.interface import Memory
from aeon.tools.registry import ToolRegistry
from aeon.llm.interface import LLMAdapter
from aeon.supervisor.models import Supervisor

class StepExecutionResult:
    """Result of step execution."""
    success: bool
    result: Dict[str, Any]
    error: Optional[str]
    execution_mode: str  # "tool", "llm", "fallback"

class StepExecutor:
    """Execute plan steps in different modes."""
    
    def execute_step(
        self,
        step: PlanStep,
        registry: ToolRegistry,
        memory: Memory,
        llm: LLMAdapter,
        supervisor: Supervisor,
    ) -> StepExecutionResult:
        """
        Execute a plan step.
        
        Determines execution mode:
        - If step.tool present and valid → tool-based execution
        - Else if step.agent == "llm" → LLM reasoning execution
        - Else → missing-tool path (repair → fallback)
        
        Args:
            step: PlanStep to execute
            registry: Tool registry
            memory: Memory interface for storing results
            llm: LLM adapter for reasoning steps
            supervisor: Supervisor for missing-tool repair
            
        Returns:
            StepExecutionResult with execution outcome
            
        Raises:
            ExecutionError: On unrecoverable execution failure
        """
        pass
    
    def execute_tool_step(
        self,
        step: PlanStep,
        registry: ToolRegistry,
        memory: Memory,
    ) -> StepExecutionResult:
        """Execute tool-based step."""
        pass
    
    def execute_llm_reasoning_step(
        self,
        step: PlanStep,
        memory: Memory,
        llm: LLMAdapter,
    ) -> StepExecutionResult:
        """Execute LLM reasoning step (explicit or fallback)."""
        pass
```

**Contract Requirements**:
- execute_step() must route to correct execution mode based on step fields
- Tool-based execution must validate arguments and store results in memory
- LLM reasoning execution must incorporate memory context
- Fallback execution must use step description as prompt
- All execution modes must update step status and log results

## Kernel Interface (Public API)

**Purpose**: Define public API for kernel orchestration.

**Interface**: `aeon.kernel.orchestrator.Orchestrator`

```python
from typing import Dict, Any, Optional
from aeon.plan.parser import Plan
from aeon.memory.interface import Memory
from aeon.tools.registry import ToolRegistry
from aeon.llm.interface import LLMAdapter

class Orchestrator:
    """Main orchestration kernel."""
    
    def __init__(
        self,
        llm_adapter: LLMAdapter,
        memory: Memory,
        tool_registry: ToolRegistry,
        supervisor: Supervisor,
        validator: Validator,
        ttl: int = 50,
    ):
        """Initialize orchestrator with dependencies."""
        pass
    
    def execute(
        self,
        user_request: str,
        initial_plan: Optional[Plan] = None,
    ) -> Dict[str, Any]:
        """
        Execute orchestration loop.
        
        Args:
            user_request: Natural language request
            initial_plan: Optional pre-created plan (if None, generates plan)
            
        Returns:
            Final state dict with:
                - "plan": Final plan state
                - "status": "completed" | "failed" | "ttl_expired"
                - "final_state": OrchestrationState snapshot
                
        Raises:
            OrchestrationError: On unrecoverable errors
        """
        pass
    
    def get_state(self) -> OrchestrationState:
        """Get current orchestration state."""
        pass
```

**Contract Requirements**:
- Kernel must remain under 800 LOC
- execute() must be deterministic (same inputs → same outputs, modulo LLM non-determinism)
- execute() must handle all error cases gracefully
- get_state() must return current state snapshot

## Interface Versioning

All interfaces follow semantic versioning:
- **MAJOR**: Breaking changes (method removal, signature changes)
- **MINOR**: New methods added (backward compatible)
- **PATCH**: Bug fixes, documentation updates

Interface contracts are versioned independently of the kernel.

