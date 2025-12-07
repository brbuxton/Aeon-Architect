# Prompt Registry Interface Contract

**Feature**: Prompt Infrastructure  
**Date**: 2025-12-07  
**Type**: Python Module Interface

## Overview

This contract defines the interface for the centralized prompt registry system, including prompt retrieval, rendering, and validation.

## Interface: PromptRegistry

### Class Definition

```python
class PromptRegistry:
    """Central registry for all system prompts."""
    
    def __init__(self) -> None:
        """Initialize registry with all prompt definitions."""
        pass
    
    def get_prompt(
        self,
        prompt_id: PromptId,
        input_data: PromptInput
    ) -> str:
        """
        Retrieve and render a prompt by identifier.
        
        Args:
            prompt_id: Unique prompt identifier
            input_data: Input data conforming to prompt's input model
            
        Returns:
            Rendered prompt string ready for LLM consumption
            
        Raises:
            PromptNotFoundError: If prompt_id not found in registry
            ValidationError: If input_data does not conform to prompt's input model
            RenderingError: If prompt rendering fails (e.g., missing fields)
        """
        pass
    
    def validate_output(
        self,
        prompt_id: PromptId,
        llm_response: str
    ) -> PromptOutput:
        """
        Validate LLM response against prompt's output model (if defined).
        
        Args:
            prompt_id: Unique prompt identifier
            llm_response: Raw LLM response string
            
        Returns:
            Validated output model instance
            
        Raises:
            PromptNotFoundError: If prompt_id not found in registry
            ValidationError: If response does not conform to prompt's output model
            NoOutputModelError: If prompt has no output model defined
        """
        pass
    
    def list_prompts(self) -> List[PromptId]:
        """
        List all registered prompt identifiers.
        
        Returns:
            List of all PromptId values in registry
        """
        pass
```

## Interface: PromptDefinition

### Class Definition

```python
class PromptDefinition:
    """Definition of a prompt with its contract."""
    
    prompt_id: PromptId
    template: str
    input_model: Type[PromptInput]
    output_model: Optional[Type[PromptOutput]]
    render_fn: Callable[[PromptInput], str]
    
    def render(self, input_data: PromptInput) -> str:
        """
        Render prompt template with input data.
        
        Args:
            input_data: Input data conforming to input_model
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValidationError: If input_data does not conform to input_model
            RenderingError: If template rendering fails
        """
        pass
```

## Interface: get_prompt (Module-Level Function)

### Function Definition

```python
def get_prompt(
    prompt_id: PromptId,
    input_data: PromptInput
) -> str:
    """
    Convenience function to retrieve and render a prompt.
    
    This function provides a module-level interface to the global
    PromptRegistry instance, simplifying prompt usage throughout
    the codebase.
    
    Args:
        prompt_id: Unique prompt identifier
        input_data: Input data conforming to prompt's input model
        
    Returns:
        Rendered prompt string ready for LLM consumption
        
    Raises:
        PromptNotFoundError: If prompt_id not found in registry
        ValidationError: If input_data does not conform to prompt's input model
        RenderingError: If prompt rendering fails
    """
    pass
```

## Error Types

### PromptNotFoundError

```python
class PromptNotFoundError(Exception):
    """Raised when a prompt identifier is not found in registry."""
    pass
```

### NoOutputModelError

```python
class NoOutputModelError(Exception):
    """Raised when attempting to validate output for a prompt with no output model."""
    pass
```

### RenderingError

```python
class RenderingError(Exception):
    """Raised when prompt template rendering fails."""
    pass
```

## Usage Examples

### Example 1: Retrieve and Render a Prompt

```python
from aeon.prompts.registry import get_prompt, PromptId
from aeon.prompts.registry import PlanGenerationInput

# Create input data
input_data = PlanGenerationInput(
    request="Create a plan to deploy a web application",
    tool_registry={"calculator": {...}, "echo": {...}}
)

# Retrieve and render prompt
prompt = get_prompt(PromptId.PLAN_GENERATION_USER, input_data)

# Use prompt with LLM
response = llm_adapter.generate(prompt=prompt, system_prompt=...)
```

### Example 2: Validate LLM Output

```python
from aeon.prompts.registry import PromptRegistry, PromptId

registry = PromptRegistry()

# Get LLM response
llm_response = llm_adapter.generate(...)

# Validate against output model
output = registry.validate_output(
    PromptId.CONVERGENCE_ASSESSMENT_USER,
    llm_response
)

# Use validated output
print(f"Converged: {output.converged}")
print(f"Completeness: {output.completeness_score}")
```

## Contract Guarantees

### Input Validation
- All input data is validated against the prompt's input model before rendering
- Validation errors provide clear messages indicating which fields are invalid
- Required fields must be present; optional fields may be omitted

### Output Validation
- Output validation only occurs for prompts with output_model defined
- LLM responses must be valid JSON for prompts with output models
- Validation errors provide clear messages indicating which fields are invalid

### Rendering Guarantees
- Rendered prompts are ready for direct use with LLM adapters
- Template rendering uses f-string syntax with Pydantic model field access
- Missing required fields in input data cause RenderingError before template evaluation

### Registry Guarantees
- All PromptId enum values have corresponding PromptDefinitions
- Registry is initialized at module load time (no lazy loading)
- Registry is thread-safe for read operations (immutable after initialization)

## Implementation Notes

- Registry uses a singleton pattern (global instance)
- Prompt definitions are registered at module import time
- Input/output models use Pydantic v2 BaseModel
- Validation uses Pydantic's `model_validate()` and `model_dump_json()`
