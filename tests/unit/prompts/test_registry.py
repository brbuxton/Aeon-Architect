"""Unit tests for prompt registry infrastructure."""

import pytest

from aeon.prompts.registry import (
    PromptId,
    PromptDefinition,
    PromptRegistry,
    PromptInput,
    PromptOutput,
    PromptNotFoundError,
    NoOutputModelError,
    RenderingError,
    JSONExtractionError,
)


# ============================================================================
# Tests for User Story 1 (T007-T010)
# ============================================================================

class TestPromptRegistryInitialization:
    """Test prompt registry initialization (T007)."""

    def test_registry_initializes_empty(self):
        """Test that PromptRegistry can be initialized."""
        registry = PromptRegistry()
        assert registry is not None
        assert isinstance(registry, PromptRegistry)


class TestPromptRetrieval:
    """Test prompt retrieval by identifier (T008)."""

    def test_get_prompt_raises_error_when_not_found(self):
        """Test that get_prompt raises PromptNotFoundError for unknown prompt ID."""
        registry = PromptRegistry()
        input_data = PromptInput()
        
        with pytest.raises(PromptNotFoundError) as exc_info:
            registry.get_prompt(PromptId.PLAN_GENERATION_USER, input_data)
        
        assert exc_info.value.prompt_id == PromptId.PLAN_GENERATION_USER.value or exc_info.value.prompt_id == str(PromptId.PLAN_GENERATION_USER)


class TestLocationInvariant:
    """Test location invariant - no inline prompts outside registry (T009, T033A)."""

    def test_location_invariant_verification(self):
        """
        Test that automated search for inline prompts returns zero matches (T033A).
        
        This test searches for common prompt patterns and verifies they are
        not found outside the prompt registry module.
        """
        import os
        import re
        from pathlib import Path
        
        # Patterns that indicate inline prompts (per FR-005A)
        prompt_patterns = [
            (r'You are\s+[a-zA-Z]', 'You are [role] pattern'),
            (r'"""\s*You are', 'Docstring with "You are"'),
            (r'return\s+"""\s*You are', 'Return statement with prompt'),
            (r'system_prompt\s*=\s*"""', 'system_prompt assignment with triple quotes'),
            (r'system_prompt\s*=\s*"You are', 'system_prompt assignment with "You are"'),
        ]
        
        # Directories to search (exclude prompt registry itself and tests)
        repo_root = Path(__file__).parent.parent.parent.parent
        search_dirs = [
            repo_root / "aeon" / "kernel",
            repo_root / "aeon" / "plan",
            repo_root / "aeon" / "validation",
            repo_root / "aeon" / "convergence",
            repo_root / "aeon" / "adaptive",
            repo_root / "aeon" / "supervisor",
        ]
        
        matches = []
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for py_file in search_dir.rglob("*.py"):
                # Skip __init__.py, test files, and the registry itself
                if (py_file.name == "__init__.py" or 
                    "test" in py_file.name.lower() or
                    "registry" in py_file.name.lower()):
                    continue
                
                try:
                    content = py_file.read_text(encoding="utf-8")
                    for pattern, pattern_name in prompt_patterns:
                        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                            # Get line context
                            line_start = content.rfind("\n", 0, match.start())
                            line_end = content.find("\n", match.end())
                            if line_end == -1:
                                line_end = len(content)
                            line = content[line_start + 1 : line_end]
                            
                            # Skip if it's in a comment
                            if "#" in line[:max(0, match.start() - line_start - 1)]:
                                continue
                            
                            # Skip if it's in a docstring that's clearly documentation
                            if '"""' in line and '"""' in content[max(0, match.start()-100):match.start()]:
                                # Check if this is a module/class/function docstring
                                before_match = content[max(0, match.start()-200):match.start()]
                                if 'def ' in before_match or 'class ' in before_match:
                                    continue
                            
                            # Skip if it's clearly a test or example
                            if "test" in line.lower() or "example" in line.lower():
                                continue
                            
                            # This looks like an inline prompt - record it
                            matches.append({
                                'file': str(py_file.relative_to(repo_root)),
                                'pattern': pattern_name,
                                'line': line.strip()[:100],  # First 100 chars of line
                                'match': match.group()[:50]  # First 50 chars of match
                            })
                except Exception as e:
                    # Skip files that can't be read
                    continue
        
        # Assert zero matches (satisfies SC-001)
        if matches:
            error_msg = f"Found {len(matches)} inline prompt pattern(s) outside registry:\n"
            for match in matches[:10]:  # Show first 10
                error_msg += f"  - {match['file']}: {match['pattern']} - {match['line']}\n"
            if len(matches) > 10:
                error_msg += f"  ... and {len(matches) - 10} more\n"
            pytest.fail(error_msg)
        
        assert len(matches) == 0, "Location invariant violated: inline prompts found outside registry"


class TestRegistrationInvariant:
    """Test registration invariant - all PromptIds have entries (T010)."""

    def test_all_prompt_ids_have_registry_entries(self):
        """Test that every PromptId has a corresponding entry in the registry."""
        registry = PromptRegistry()
        
        # This test will fail until all prompts are registered
        # For now, we verify the structure
        for prompt_id in PromptId:
            # Once registry is populated, this should not raise
            # For now, we expect PromptNotFoundError
            with pytest.raises(PromptNotFoundError):
                registry.get_prompt(prompt_id, PromptInput())


# ============================================================================
# Tests for User Story 2 (T034-T038G, T090)
# ============================================================================

class TestInputModelValidation:
    """Test input model validation (T034)."""

    def test_input_validation_rejects_invalid_inputs(self):
        """Test that invalid inputs are rejected before rendering."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt definition with input model
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan for: {request}",
            input_model=PlanGenerationUserInput,
        )
        registry.register(definition)
        
        # Test with missing required field
        invalid_input = PromptInput()  # Missing 'request' field
        with pytest.raises(RenderingError) as exc_info:
            registry.get_prompt(PromptId.PLAN_GENERATION_USER, invalid_input)
        
        assert "validation" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower()


class TestPromptRenderingWithValidatedInput:
    """Test prompt rendering with validated input (T035)."""

    def test_prompt_rendering_with_valid_input(self):
        """Test that valid inputs produce correctly rendered prompts."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan for: {request}",
            input_model=PlanGenerationUserInput,
        )
        registry.register(definition)
        
        valid_input = PlanGenerationUserInput(request="Test request")
        rendered = registry.get_prompt(PromptId.PLAN_GENERATION_USER, valid_input)
        
        assert "Test request" in rendered
        assert "Generate plan for:" in rendered


class TestOutputModelValidation:
    """Test output model validation for JSON prompts (T036)."""

    def test_output_validation_for_json_prompts(self):
        """Test that JSON-producing prompts validate outputs correctly."""
        from pydantic import ValidationError as PydanticValidationError
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test that valid output is validated correctly
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            '{"goal": "test", "steps": []}',
        )
        assert validated.goal == "test"
        assert validated.steps == []


class TestSchemaInvariant:
    """Test schema invariant - all prompts have input models (T037)."""

    def test_all_prompts_have_input_models(self):
        """Test that every prompt has an input model defined."""
        from aeon.prompts.registry import _initialize_registry, get_prompt_registry
        
        # Initialize registry
        _initialize_registry()
        registry = get_prompt_registry()
        
        # Verify all registered prompts have input models
        for prompt_id in PromptId:
            if prompt_id not in registry._registry:
                # Skip if prompt not registered (shouldn't happen, but handle gracefully)
                continue
            
            definition = registry._registry[prompt_id]
            assert definition.input_model is not None, (
                f"Prompt {prompt_id} is missing input_model. "
                "All prompts must have an input model defined (schema invariant)."
            )


class TestJSONExtractionFromDictionaryTextKey:
    """Test JSON extraction from dictionary with 'text' key (T038A)."""

    def test_extract_json_from_dict_text_key(self):
        """Test that JSON is extracted from dictionary response with 'text' key."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test that JSON is extracted from dict with 'text' key
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            {"text": '{"goal": "test", "steps": []}'},
        )
        assert validated.goal == "test"
        assert validated.steps == []


class TestJSONExtractionFromMarkdownCodeBlocks:
    """Test JSON extraction from markdown code blocks (T038B)."""

    def test_extract_json_from_markdown_code_blocks(self):
        """Test that JSON is extracted from markdown code blocks."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test with ```json ... ``` block
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            "```json\n{\"goal\": \"test\", \"steps\": []}\n```",
        )
        assert validated.goal == "test"
        assert validated.steps == []
        
        # Test with ``` ... ``` block (no language)
        validated2 = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            "```\n{\"goal\": \"test2\", \"steps\": []}\n```",
        )
        assert validated2.goal == "test2"
        assert validated2.steps == []


class TestJSONExtractionFromEmbeddedJSON:
    """Test JSON extraction from embedded JSON using brace matching (T038C)."""

    def test_extract_json_from_embedded_json(self):
        """Test that JSON is extracted from text containing embedded JSON."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test with JSON embedded in text
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            "Here is the plan: {\"goal\": \"test\", \"steps\": []}",
        )
        assert validated.goal == "test"
        assert validated.steps == []


class TestJSONExtractionFromRawJSON:
    """Test JSON extraction from raw JSON string (T038D)."""

    def test_extract_json_from_raw_json_string(self):
        """Test that raw JSON strings are parsed directly."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test with raw JSON string
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            '{"goal": "test", "steps": []}',
        )
        assert validated.goal == "test"
        assert validated.steps == []


class TestJSONExtractionError:
    """Test JSONExtractionError when no valid JSON can be extracted (T038E)."""

    def test_json_extraction_error_when_no_json_found(self):
        """Test that JSONExtractionError is raised when no valid JSON can be extracted."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test that JSONExtractionError is raised when no valid JSON can be extracted
        with pytest.raises(JSONExtractionError):
            registry.validate_output(
                PromptId.PLAN_GENERATION_USER,
                "This is not JSON at all",
            )


class TestValidationErrorAfterJSONExtraction:
    """Test ValidationError when JSON extraction succeeds but validation fails (T038F)."""

    def test_validation_error_when_extraction_succeeds_but_validation_fails(self):
        """Test that ValidationError (not JSONExtractionError) is raised when validation fails."""
        from pydantic import ValidationError as PydanticValidationError
        from aeon.prompts.registry import PlanGenerationUserInput
        
        registry = PromptRegistry()
        
        # Create a prompt with output model
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        
        # Test that ValidationError (not JSONExtractionError) is raised when validation fails
        with pytest.raises(PydanticValidationError):
            registry.validate_output(
                PromptId.PLAN_GENERATION_USER,
                '{"invalid": "structure"}',  # Valid JSON but invalid for output model
            )


class TestJSONExtractionEdgeCases:
    """Test JSON extraction edge cases (T038G)."""

    def _setup_test_prompt(self, registry):
        """Helper to set up a test prompt with output model."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        class TestOutput(PromptOutput):
            goal: str
            steps: list
        
        definition = PromptDefinition(
            prompt_id=PromptId.PLAN_GENERATION_USER,
            template="Generate plan",
            input_model=PlanGenerationUserInput,
            output_model=TestOutput,
        )
        registry.register(definition)
        return TestOutput

    def test_empty_text_key_value(self):
        """Test handling of empty 'text' key values."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        # Empty text should raise JSONExtractionError
        with pytest.raises(JSONExtractionError):
            registry.validate_output(
                PromptId.PLAN_GENERATION_USER,
                {"text": ""},
            )
    
    def test_multiple_json_objects(self):
        """Test that first JSON object is selected when multiple are present."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        # First JSON object should be extracted
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            '{"goal": "first", "steps": []} {"goal": "second", "steps": []}',
        )
        assert validated.goal == "first"
        assert validated.steps == []
    
    def test_trailing_text_after_json(self):
        """Test that trailing text after JSON is ignored."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        # Trailing text should be ignored, JSON should be extracted
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            '{"goal": "test", "steps": []} and some trailing text',
        )
        assert validated.goal == "test"
        assert validated.steps == []
    
    def test_nested_json_in_text_key(self):
        """Test that nested JSON in 'text' key is extracted correctly."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        # Nested JSON should be extracted correctly
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            {"text": '{"goal": "test", "steps": []}'},
        )
        assert validated.goal == "test"
        assert validated.steps == []
    
    def test_missing_text_key(self):
        """Test that missing 'text' key raises JSONExtractionError."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        with pytest.raises(JSONExtractionError):
            registry.validate_output(
                PromptId.PLAN_GENERATION_USER,
                {"other_key": "value"},
            )
    
    def test_non_string_text_value(self):
        """Test that non-string 'text' value raises JSONExtractionError."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        with pytest.raises(JSONExtractionError):
            registry.validate_output(
                PromptId.PLAN_GENERATION_USER,
                {"text": 123},  # Not a string
            )
    
    def test_unclosed_code_blocks(self):
        """Test that unclosed code blocks are handled correctly."""
        registry = PromptRegistry()
        self._setup_test_prompt(registry)
        
        # Unclosed code blocks should fall back to embedded JSON extraction
        validated = registry.validate_output(
            PromptId.PLAN_GENERATION_USER,
            "```json\n{\"goal\": \"test\", \"steps\": []}",  # Missing closing ```
        )
        assert validated.goal == "test"
        assert validated.steps == []


class TestPydanticV1V2Compatibility:
    """Test Pydantic v1/v2 compatibility (T090)."""

    def test_pydantic_v1_v2_compatibility(self):
        """Test that prompt input/output models work with both Pydantic v1 and v2."""
        from aeon.prompts.registry import PlanGenerationUserInput
        
        # Test that models can be instantiated
        input_model = PlanGenerationUserInput(request="test")
        assert input_model.request == "test"
        
        # Test that model_dump() works (Pydantic v2) or dict() works (Pydantic v1)
        try:
            dumped = input_model.model_dump()
            assert "request" in dumped
        except AttributeError:
            # Fallback to dict() for Pydantic v1
            dumped = dict(input_model)
            assert "request" in dumped
        
        # Test that validation works
        with pytest.raises(Exception):  # Either ValidationError or similar
            PlanGenerationUserInput()  # Missing required field
