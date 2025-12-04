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
            # Detect convergence assessment prompts
            prompt_lower = prompt.lower()
            is_convergence_assessment = (
                "assess whether task execution has converged" in prompt_lower
                or "convergence assessment" in prompt_lower
                or "completeness_score" in prompt_lower
            )
            
            if is_convergence_assessment:
                # Return convergence assessment response
                # Check if all steps are complete by looking at execution results in prompt
                all_complete = "status" in prompt_lower and "complete" in prompt_lower
                # Default to converged if all steps appear complete, otherwise not converged
                if all_complete and "failed" not in prompt_lower:
                    response_text = """{
                        "completeness_score": 0.95,
                        "coherence_score": 0.90,
                        "consistency_status": {
                            "plan_aligned": true,
                            "step_aligned": true,
                            "answer_aligned": true,
                            "memory_aligned": true
                        },
                        "detected_issues": [],
                        "reason_codes": ["completeness_threshold_met", "coherence_threshold_met", "consistency_aligned"],
                        "metadata": {
                            "completeness_explanation": "All steps completed successfully",
                            "coherence_explanation": "Execution results form a coherent solution",
                            "consistency_explanation": "All alignment checks passed"
                        }
                    }"""
                else:
                    # Not converged - return lower scores
                    response_text = """{
                        "completeness_score": 0.70,
                        "coherence_score": 0.75,
                        "consistency_status": {
                            "plan_aligned": false,
                            "step_aligned": true,
                            "answer_aligned": false,
                            "memory_aligned": true
                        },
                        "detected_issues": ["Some steps may need refinement"],
                        "reason_codes": ["completeness_below_threshold", "consistency_not_aligned"],
                        "metadata": {
                            "completeness_explanation": "Some steps may be incomplete",
                            "coherence_explanation": "Execution results need review",
                            "consistency_explanation": "Some alignment checks failed"
                        }
                    }"""
            else:
                # Detect complex requests (multiple distinct actions) and return multi-step plan
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


