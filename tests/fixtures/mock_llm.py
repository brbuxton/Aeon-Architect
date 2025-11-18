"""Mock LLM adapter for testing."""

from typing import Any, Dict, Optional

from aeon.llm.interface import LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """Mock LLM adapter for testing."""

    def __init__(self, responses: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize mock LLM adapter.

        Args:
            responses: Dict mapping prompts to responses (optional)
        """
        self.responses = responses or {}
        self.calls = []  # Track all calls for testing

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate mock response."""
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        
        # Return predefined response if available
        if prompt in self.responses:
            response_text = self.responses[prompt]
        else:
            # Detect complex requests (multiple distinct actions) and return multi-step plan
            prompt_lower = prompt.lower()
            # Look for multiple distinct action verbs, not just "and" or commas
            action_verbs = ["analyze", "generate", "create", "process", "transform", "build", "write"]
            action_count = sum(1 for verb in action_verbs if verb in prompt_lower)
            # Also check for comma-separated actions (but not just "5 and 10" type phrases)
            has_comma_separated_actions = "," in prompt_lower and action_count >= 1
            is_complex = action_count >= 2 or has_comma_separated_actions
            
            if is_complex:
                # Multi-step plan for complex requests
                response_text = """{
                    "goal": "analyze a dataset, generate statistics, and create a report",
                    "steps": [
                        {"step_id": "step1", "description": "Analyze the dataset", "status": "pending"},
                        {"step_id": "step2", "description": "Generate statistics", "status": "pending"},
                        {"step_id": "step3", "description": "Create a report", "status": "pending"}
                    ]
                }"""
            else:
                # Default single-step plan for simple requests
                response_text = """{
                    "goal": "calculate the sum of 5 and 10",
                    "steps": [
                        {"step_id": "step1", "description": "Add 5 and 10", "status": "pending"}
                    ]
                }"""
        
        return {
            "text": response_text,
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            "model": "mock-model",
        }

    def supports_streaming(self) -> bool:
        """Return False for mock."""
        return False


