"""Adaptive depth heuristics for TaskProfile inference and TTL allocation."""

import json
from typing import Any, Dict, Literal, Optional

from aeon.adaptive.models import AdaptiveDepthConfiguration, TaskProfile
from aeon.exceptions import LLMError, ValidationError
from aeon.llm.interface import LLMAdapter
from aeon.supervisor.repair import Supervisor


class AdaptiveDepth:
    """Adaptive depth heuristics for TaskProfile inference and TTL allocation."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        global_ttl_limit: Optional[int] = None,
        config: Optional[AdaptiveDepthConfiguration] = None,
    ) -> None:
        """
        Initialize AdaptiveDepth.

        Args:
            llm_adapter: LLM adapter for TaskProfile inference
            global_ttl_limit: Optional global TTL limit to cap allocation
            config: Optional configuration for adaptive depth heuristics
        """
        self.llm_adapter = llm_adapter
        self.global_ttl_limit = global_ttl_limit
        self.config = config or AdaptiveDepthConfiguration(
            global_ttl_limit=global_ttl_limit
        )
        self.supervisor = Supervisor(llm_adapter=llm_adapter)

    def infer_task_profile(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskProfile:
        """
        Infer TaskProfile for a task using LLM-based reasoning.

        Args:
            task_description: Natural language task description
            context: Optional context (previous attempts, user preferences, etc.)

        Returns:
            TaskProfile with all dimensions inferred

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid
        """
        if not task_description or not task_description.strip():
            raise ValidationError("task_description must be non-empty string")

        # Construct prompt for TaskProfile inference
        prompt = self._construct_task_profile_prompt(task_description, context)

        try:
            # Generate LLM response
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_task_profile_system_prompt(),
                max_tokens=2048,
                temperature=0.7,
            )

            # Extract TaskProfile JSON from LLM response
            response_text = response.get("text", "").strip()
            task_profile_dict = self._extract_task_profile_from_response(response_text)

            # Validate and create TaskProfile
            try:
                task_profile = TaskProfile(**task_profile_dict)
                return task_profile
            except Exception as e:
                # Try to repair JSON if schema validation fails
                try:
                    repaired_dict = self.supervisor.repair_json(
                        malformed_json=json.dumps(task_profile_dict),
                        expected_schema=self._get_task_profile_schema(),
                    )
                    task_profile = TaskProfile(**repaired_dict)
                    return task_profile
                except Exception as repair_error:
                    # Fall back to default TaskProfile on repair failure
                    return TaskProfile.default()

        except LLMError:
            # Fall back to default TaskProfile on LLM failure
            return TaskProfile.default()
        except Exception as e:
            # Fall back to default TaskProfile on any other error
            return TaskProfile.default()

    def allocate_ttl(
        self,
        task_profile: TaskProfile,
        global_ttl_limit: Optional[int] = None,
    ) -> int:
        """
        Allocate TTL based on TaskProfile dimensions using deterministic function.

        Args:
            task_profile: TaskProfile instance
            global_ttl_limit: Optional global TTL limit to cap allocation (overrides config)

        Returns:
            Allocated TTL (integer, >= 1)

        Raises:
            ValueError: If task_profile is invalid
        """
        if not isinstance(task_profile, TaskProfile):
            raise ValueError("task_profile must be a TaskProfile instance")

        # Use provided global_ttl_limit or fall back to config
        ttl_limit = global_ttl_limit or self.global_ttl_limit or self.config.global_ttl_limit

        # Deterministic TTL allocation formula
        # Base TTL from reasoning_depth (1-5 scale)
        base_ttl = (
            task_profile.reasoning_depth * self.config.reasoning_depth_weight
        )

        # Adjust for information_sufficiency (0.0-1.0)
        info_factor = (
            task_profile.information_sufficiency
            * self.config.information_sufficiency_weight
        )

        # Adjust for expected_tool_usage
        tool_weight = self.config.tool_usage_weights.get(
            task_profile.expected_tool_usage, 1.0
        )

        # Adjust for output_breadth
        breadth_weight = self.config.output_breadth_weights.get(
            task_profile.output_breadth, 1.0
        )

        # Adjust for confidence_requirement
        confidence_weight = self.config.confidence_requirement_weights.get(
            task_profile.confidence_requirement, 1.0
        )

        # Calculate TTL: base * multipliers
        allocated_ttl = int(
            base_ttl
            * info_factor
            * tool_weight
            * breadth_weight
            * confidence_weight
            * self.config.ttl_base_multiplier
        )

        # Ensure minimum TTL of 1
        allocated_ttl = max(1, allocated_ttl)

        # Cap at global limit if provided
        if ttl_limit is not None:
            allocated_ttl = min(allocated_ttl, ttl_limit)

        return allocated_ttl

    def update_task_profile(
        self,
        current_profile: TaskProfile,
        convergence_assessment: Any,  # ConvergenceAssessment (avoid circular import)
        semantic_validation_report: Any,  # SemanticValidationReport (avoid circular import)
        clarity_states: list[Literal["CLEAR", "PARTIALLY_CLEAR", "BLOCKED"]],
    ) -> Optional[TaskProfile]:
        """
        Update TaskProfile at pass boundary when complexity mismatch detected.

        Args:
            current_profile: Current TaskProfile instance
            convergence_assessment: Convergence assessment from current pass
            semantic_validation_report: Semantic validation report from current pass
            clarity_states: List of clarity states from step executions

        Returns:
            Updated TaskProfile if update triggered, None otherwise. Includes adjustment_reason in metadata.

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid

        Trigger Conditions:
            - convergence_assessment.converged == False (convergence failure)
            - semantic_validation_report has issues (validation issues)
            - At least one clarity_state == "BLOCKED" (blocked steps)
        """
        if not isinstance(current_profile, TaskProfile):
            raise ValidationError("current_profile must be a TaskProfile instance")

        # Check trigger conditions
        convergence_failed = (
            convergence_assessment is not None
            and hasattr(convergence_assessment, "converged")
            and not convergence_assessment.converged
        )

        validation_issues_present = (
            semantic_validation_report is not None
            and hasattr(semantic_validation_report, "issues")
            and len(semantic_validation_report.issues) > 0
        )

        blocked_steps_present = (
            clarity_states is not None
            and len(clarity_states) > 0
            and "BLOCKED" in clarity_states
        )

        # All three conditions must be met to trigger update
        if not (convergence_failed and validation_issues_present and blocked_steps_present):
            return None

        # Construct prompt for TaskProfile update
        prompt = self._construct_update_task_profile_prompt(
            current_profile,
            convergence_assessment,
            semantic_validation_report,
            clarity_states,
        )

        try:
            # Generate LLM response
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_update_task_profile_system_prompt(),
                max_tokens=2048,
                temperature=0.7,
            )

            # Extract updated TaskProfile JSON from LLM response
            response_text = response.get("text", "").strip()
            updated_profile_dict = self._extract_task_profile_from_response(response_text)

            # Increment profile_version (T102: version tracking)
            updated_profile_dict["profile_version"] = current_profile.profile_version + 1

            # Validate and create updated TaskProfile
            try:
                updated_profile = TaskProfile(**updated_profile_dict)
                return updated_profile
            except Exception as e:
                # Try to repair JSON if schema validation fails
                try:
                    repaired_dict = self.supervisor.repair_json(
                        malformed_json=json.dumps(updated_profile_dict),
                        expected_schema=self._get_task_profile_schema(),
                    )
                    repaired_dict["profile_version"] = current_profile.profile_version + 1
                    updated_profile = TaskProfile(**repaired_dict)
                    return updated_profile
                except Exception as repair_error:
                    # Fall back to current profile on repair failure (no update)
                    return None

        except LLMError:
            # Fall back to current profile on LLM failure (no update)
            return None
        except Exception as e:
            # Fall back to current profile on any other error (no update)
            return None

    def _construct_task_profile_prompt(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct prompt for TaskProfile inference."""
        prompt = f"""Analyze this task and infer its complexity characteristics:

Task: {task_description}
"""
        if context:
            prompt += f"\nContext: {json.dumps(context, indent=2)}\n"

        prompt += """
Infer the following dimensions:
1. reasoning_depth: Integer 1-5 (1=very shallow, 2=shallow, 3=moderate, 4=deep, 5=very deep)
2. information_sufficiency: Float 0.0-1.0 (0.0=insufficient, 1.0=sufficient)
3. expected_tool_usage: One of "none", "minimal", "moderate", "extensive"
4. output_breadth: One of "narrow", "moderate", "broad"
5. confidence_requirement: One of "low", "medium", "high"
6. raw_inference: Natural-language explanation of how each dimension was determined

Return a JSON object with these fields.
"""
        return prompt

    def _get_task_profile_system_prompt(self) -> str:
        """Get system prompt for TaskProfile inference."""
        return """You are a task complexity analyzer. Analyze tasks and infer their complexity characteristics.
Return only valid JSON with the required fields: reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference."""

    def _get_task_profile_schema(self) -> Dict[str, Any]:
        """Get JSON schema for TaskProfile."""
        return {
            "type": "object",
            "required": [
                "reasoning_depth",
                "information_sufficiency",
                "expected_tool_usage",
                "output_breadth",
                "confidence_requirement",
                "raw_inference",
            ],
            "properties": {
                "reasoning_depth": {"type": "integer", "minimum": 1, "maximum": 5},
                "information_sufficiency": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "expected_tool_usage": {
                    "type": "string",
                    "enum": ["none", "minimal", "moderate", "extensive"],
                },
                "output_breadth": {
                    "type": "string",
                    "enum": ["narrow", "moderate", "broad"],
                },
                "confidence_requirement": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "raw_inference": {"type": "string", "minLength": 1},
            },
        }

    def _extract_task_profile_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract TaskProfile JSON from LLM response.

        Args:
            response_text: LLM response text

        Returns:
            TaskProfile dict

        Raises:
            ValueError: If no valid JSON found
        """
        import re

        # Try to find JSON block
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try parsing entire text
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"No valid JSON found in response: {response_text[:100]}") from e

    def _construct_update_task_profile_prompt(
        self,
        current_profile: TaskProfile,
        convergence_assessment: Any,
        semantic_validation_report: Any,
        clarity_states: list[Literal["CLEAR", "PARTIALLY_CLEAR", "BLOCKED"]],
    ) -> str:
        """Construct prompt for TaskProfile update."""
        prompt = f"""Update the TaskProfile based on execution feedback:

Current TaskProfile:
{json.dumps(current_profile.model_dump(), indent=2)}

Convergence Assessment:
{json.dumps(convergence_assessment.model_dump() if hasattr(convergence_assessment, 'model_dump') else str(convergence_assessment), indent=2)}

Semantic Validation Issues:
{json.dumps([issue.model_dump() if hasattr(issue, 'model_dump') else str(issue) for issue in (semantic_validation_report.issues if hasattr(semantic_validation_report, 'issues') else [])], indent=2)}

Clarity States: {clarity_states}

Based on this feedback, determine if the task complexity was underestimated or overestimated:
- If complexity was underestimated (task harder than expected): Increase reasoning_depth, decrease information_sufficiency, increase expected_tool_usage, increase output_breadth, increase confidence_requirement
- If complexity was overestimated (task easier than expected): Decrease reasoning_depth, increase information_sufficiency, decrease expected_tool_usage, decrease output_breadth, decrease confidence_requirement

Return an updated TaskProfile JSON with adjusted dimensions.
"""
        return prompt

    def _get_update_task_profile_system_prompt(self) -> str:
        """Get system prompt for TaskProfile update."""
        return """You are a task complexity analyzer. Based on execution feedback (convergence failure, validation issues, blocked steps), update the TaskProfile to better reflect the actual task complexity.
Return only valid JSON with the required fields: reasoning_depth, information_sufficiency, expected_tool_usage, output_breadth, confidence_requirement, raw_inference.
Adjust dimensions based on whether complexity was underestimated (increase) or overestimated (decrease)."""

    def adjust_ttl_for_updated_profile(
        self,
        old_profile: TaskProfile,
        new_profile: TaskProfile,
        current_ttl: int,
        global_ttl_limit: Optional[int] = None,
    ) -> tuple[int, str]:
        """
        Adjust TTL bidirectionally based on TaskProfile update (T103).

        Args:
            old_profile: Previous TaskProfile
            new_profile: Updated TaskProfile
            current_ttl: Current TTL remaining
            global_ttl_limit: Optional global TTL limit

        Returns:
            Tuple of (adjusted_ttl, adjustment_reason)
        """
        # Calculate TTL for new profile
        new_ttl_allocation = self.allocate_ttl(new_profile, global_ttl_limit)

        # Calculate difference in reasoning_depth (primary complexity indicator)
        depth_delta = new_profile.reasoning_depth - old_profile.reasoning_depth

        # Bidirectional adjustment: increase or decrease TTL based on complexity change
        if depth_delta > 0:
            # Complexity increased - increase TTL
            # Use proportional increase based on depth delta
            adjustment_factor = 1.0 + (depth_delta * 0.2)  # 20% per depth level
            adjusted_ttl = int(current_ttl * adjustment_factor)
            adjustment_reason = f"Complexity increased (reasoning_depth {old_profile.reasoning_depth} → {new_profile.reasoning_depth}), TTL increased by {int((adjustment_factor - 1.0) * 100)}%"
        elif depth_delta < 0:
            # Complexity decreased - decrease TTL
            # Use proportional decrease based on depth delta
            adjustment_factor = 1.0 + (depth_delta * 0.15)  # 15% per depth level
            adjusted_ttl = int(current_ttl * adjustment_factor)
            adjustment_reason = f"Complexity decreased (reasoning_depth {old_profile.reasoning_depth} → {new_profile.reasoning_depth}), TTL decreased by {int(abs(depth_delta * 0.15) * 100)}%"
        else:
            # No depth change - use new allocation but keep current TTL if it's reasonable
            if abs(new_ttl_allocation - current_ttl) > current_ttl * 0.3:  # More than 30% difference
                adjusted_ttl = new_ttl_allocation
                adjustment_reason = f"TaskProfile updated (no depth change), TTL adjusted to new allocation ({new_ttl_allocation})"
            else:
                adjusted_ttl = current_ttl
                adjustment_reason = f"TaskProfile updated (no depth change), TTL unchanged ({current_ttl})"

        # Ensure minimum TTL of 1
        adjusted_ttl = max(1, adjusted_ttl)

        # Cap at global limit if provided
        ttl_limit = global_ttl_limit or self.global_ttl_limit or self.config.global_ttl_limit
        if ttl_limit is not None:
            adjusted_ttl = min(adjusted_ttl, ttl_limit)

        return (adjusted_ttl, adjustment_reason)

