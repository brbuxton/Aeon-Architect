"""Recursive planning and plan refinement."""

import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set

from aeon.exceptions import LLMError, ValidationError
from aeon.llm.interface import LLMAdapter
from aeon.plan.models import Plan, PlanStep, RefinementAction, Subplan
from aeon.plan.parser import PlanParser
from aeon.plan.prompts import construct_plan_generation_prompt, get_plan_generation_system_prompt
from aeon.prompts.registry import get_prompt, PromptId, RecursiveRefinementSystemInput
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry

if TYPE_CHECKING:
    # Forward references for types defined in other modules
    from aeon.adaptive.models import TaskProfile
    from aeon.validation.semantic import ValidationIssue


class NestingDepthError(Exception):
    """Raised when nesting depth limit is exceeded."""

    pass


class RefinementLimitError(Exception):
    """Raised when refinement attempt limits are exceeded."""

    pass


class RecursivePlanner:
    """Recursive planning and plan refinement using LLM-based reasoning."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry,
        max_nesting_depth: int = 5,
        max_refinement_attempts_per_fragment: int = 3,
        max_global_refinement_attempts: int = 10,
        semantic_validator: Optional[Any] = None,  # SemanticValidator from aeon.validation.semantic
    ) -> None:
        """
        Initialize RecursivePlanner.

        Args:
            llm_adapter: LLM adapter for plan generation and refinement
            tool_registry: Tool registry for tool awareness
            max_nesting_depth: Maximum allowed nesting depth for subplans (default 5)
            max_refinement_attempts_per_fragment: Maximum refinement attempts per fragment (default 3)
            max_global_refinement_attempts: Maximum total refinement attempts (default 10)
            semantic_validator: Optional semantic validator for validating refined fragments
        """
        self.llm_adapter = llm_adapter
        self.tool_registry = tool_registry
        self.max_nesting_depth = max_nesting_depth
        self.max_refinement_attempts_per_fragment = max_refinement_attempts_per_fragment
        self.max_global_refinement_attempts = max_global_refinement_attempts
        self.parser = PlanParser()
        self.supervisor = Supervisor(llm_adapter=llm_adapter)
        self.semantic_validator = semantic_validator  # Optional semantic validator
        
        # Track refinement attempts
        self._refinement_attempts: Dict[str, int] = {}  # fragment_id -> attempt count
        self._global_refinement_count = 0
        self._fragments_requiring_intervention: Set[str] = set()

    def generate_plan(
        self,
        task_description: str,
        task_profile: Any,  # TaskProfile from aeon.adaptive.models
        tool_registry: ToolRegistry,
    ) -> Plan:
        """
        Generate initial declarative plan for a task.

        Args:
            task_description: Natural language task description
            task_profile: TaskProfile for the task
            tool_registry: Tool registry for tool awareness

        Returns:
            Plan with steps including step_index, total_steps, incoming_context, handoff_to_next

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid
        """
        if not task_description or not task_description.strip():
            raise ValidationError("task_description must be non-empty string")

        # Construct prompt for plan generation
        prompt = construct_plan_generation_prompt(task_description, tool_registry)
        
        # Enhance prompt with TaskProfile context
        prompt += f"\n\nTaskProfile context:\n"
        prompt += f"- Reasoning depth: {task_profile.reasoning_depth}/5\n"
        prompt += f"- Information sufficiency: {task_profile.information_sufficiency:.2f}\n"
        prompt += f"- Expected tool usage: {task_profile.expected_tool_usage}\n"
        prompt += f"- Output breadth: {task_profile.output_breadth}\n"
        prompt += f"- Confidence requirement: {task_profile.confidence_requirement}\n"
        prompt += "\nGenerate a plan with steps that include step_index, total_steps, incoming_context, and handoff_to_next fields.\n"

        try:
            # Generate LLM response
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=get_plan_generation_system_prompt(),
                max_tokens=4096,
                temperature=0.7,
            )

            # Extract plan JSON from LLM response
            response_text = response.get("text", "").strip()
            plan_dict = self._extract_plan_from_response(response_text)

            # Parse and validate plan
            plan = self.parser.parse(plan_dict)

            # Populate step_index, total_steps, incoming_context, handoff_to_next
            total_steps = len(plan.steps)
            for idx, step in enumerate(plan.steps, start=1):
                step.step_index = idx
                step.total_steps = total_steps
                step.incoming_context = None  # Will be populated during execution
                step.handoff_to_next = None  # Will be populated during execution

            return plan

        except LLMError as e:
            raise LLMError(f"Failed to generate plan: {e}") from e
        except Exception as e:
            raise ValidationError(f"Failed to parse plan: {e}") from e

    def refine_plan(
        self,
        current_plan: Plan,
        validation_issues: List["ValidationIssue"],  # type: ignore
        convergence_reason_codes: List[str],
        blocked_steps: List[str],
        executed_step_ids: Set[str],
    ) -> List[RefinementAction]:
        """
        Generate refinement actions for plan fragments using delta-style operations.

        Args:
            current_plan: Current plan state
            validation_issues: Validation issues that triggered refinement
            convergence_reason_codes: Reason codes from convergence assessment
            blocked_steps: List of step IDs with clarity_state == BLOCKED
            executed_step_ids: Set of step IDs that have been executed (immutable)

        Returns:
            List of RefinementAction objects (ADD/MODIFY/REMOVE operations)

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid
            RefinementLimitError: If refinement attempt limits exceeded
        """
        # Check global refinement limit
        if self._global_refinement_count >= self.max_global_refinement_attempts:
            raise RefinementLimitError(
                f"Global refinement limit ({self.max_global_refinement_attempts}) exceeded"
            )

        # Collect refinement triggers
        refinement_triggers = self._collect_refinement_triggers(
            validation_issues, convergence_reason_codes, blocked_steps
        )

        if not refinement_triggers:
            return []  # No refinement needed

        # Identify target fragments (only pending/future steps)
        target_fragments = self._identify_target_fragments(
            current_plan, executed_step_ids, refinement_triggers
        )

        # Check per-fragment limits
        for fragment_id in target_fragments:
            if fragment_id in self._fragments_requiring_intervention:
                continue  # Skip fragments that require manual intervention
            if (
                self._refinement_attempts.get(fragment_id, 0)
                >= self.max_refinement_attempts_per_fragment
            ):
                self._fragments_requiring_intervention.add(fragment_id)
                continue  # Skip fragments at limit

        # Generate refinement actions using LLM
        refinement_actions = self._generate_refinement_actions_llm(
            current_plan, target_fragments, refinement_triggers, executed_step_ids
        )

        # Validate refined fragments if semantic validator is available (FR-033)
        if self.semantic_validator and refinement_actions:
            validated_actions = []
            for action in refinement_actions:
                # Create a test plan with the refinement action applied
                # For validation, we check if the action would create valid fragments
                try:
                    # Validate the new_step if it's an ADD or MODIFY action
                    if action.action_type in ("ADD", "MODIFY") and action.new_step:
                        # Validate the step fragment
                        validation_report = self.semantic_validator.validate(
                            artifact=action.new_step,
                            artifact_type="step",
                            tool_registry=self.tool_registry,
                        )
                        # If critical issues found, skip this action
                        if validation_report.overall_severity == "CRITICAL":
                            continue  # Skip actions with critical validation issues
                    validated_actions.append(action)
                except Exception:
                    # If validation fails, include the action anyway (best-effort)
                    validated_actions.append(action)
            refinement_actions = validated_actions

        # Update refinement attempt tracking
        for action in refinement_actions:
            fragment_id = action.target_step_id or action.target_plan_section or "plan"
            self._refinement_attempts[fragment_id] = (
                self._refinement_attempts.get(fragment_id, 0) + 1
            )
        self._global_refinement_count += len(refinement_actions)

        return refinement_actions

    def create_subplan(
        self,
        parent_step_id: str,
        parent_step_description: str,
        current_depth: int,
        max_depth: int = 5,
    ) -> Subplan:
        """
        Create subplan for complex step decomposition.

        Args:
            parent_step_id: ID of parent step being decomposed
            parent_step_description: Description of parent step
            current_depth: Current nesting depth
            max_depth: Maximum allowed nesting depth (default 5)

        Returns:
            Subplan (Plan instance) with nested steps

        Raises:
            LLMError: If LLM API calls fail after retries
            NestingDepthError: If current_depth >= max_depth
            ValidationError: If inputs are invalid
        """
        if current_depth >= max_depth:
            raise NestingDepthError(
                f"Nesting depth limit ({max_depth}) exceeded at depth {current_depth}"
            )

        if not parent_step_id or not parent_step_id.strip():
            raise ValidationError("parent_step_id must be non-empty string")
        if not parent_step_description or not parent_step_description.strip():
            raise ValidationError("parent_step_description must be non-empty string")

        # Construct prompt for subplan generation
        prompt = f"""Generate a subplan to decompose the following step:

Step ID: {parent_step_id}
Step Description: {parent_step_description}
Nesting Depth: {current_depth + 1} (max: {max_depth})

Break this step down into detailed substeps. Each substep should be concrete and actionable.
Return a JSON plan with goal and steps.
"""

        try:
            # Generate LLM response
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=get_plan_generation_system_prompt(),
                max_tokens=4096,
                temperature=0.7,
            )

            # Extract plan JSON from LLM response
            response_text = response.get("text", "").strip()
            plan_dict = self._extract_plan_from_response(response_text)

            # Parse and validate plan
            plan = self.parser.parse(plan_dict)

            # Populate step_index, total_steps
            total_steps = len(plan.steps)
            for idx, step in enumerate(plan.steps, start=1):
                step.step_index = idx
                step.total_steps = total_steps

            # Create Subplan
            subplan = Subplan(
                plan=plan,
                parent_step_id=parent_step_id,
                nesting_depth=current_depth + 1,
            )

            return subplan

        except LLMError as e:
            raise LLMError(f"Failed to create subplan: {e}") from e
        except Exception as e:
            raise ValidationError(f"Failed to parse subplan: {e}") from e

    def _extract_plan_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract plan JSON from LLM response text."""
        # Try to extract JSON from response (may be wrapped in markdown code blocks)
        import re

        # Look for JSON code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

        try:
            plan_dict = json.loads(json_str)
            return plan_dict
        except json.JSONDecodeError:
            # Try to repair JSON using supervisor
            try:
                repaired_json = self.supervisor.repair_json(
                    malformed_json=json_str,
                    expected_schema=self._get_plan_schema(),
                )
                return json.loads(repaired_json)
            except Exception as e:
                raise ValidationError(f"Failed to parse or repair plan JSON: {e}") from e

    def _get_plan_schema(self) -> Dict[str, Any]:
        """Get JSON schema for plan structure."""
        return {
            "type": "object",
            "required": ["goal", "steps"],
            "properties": {
                "goal": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["step_id", "description"],
                        "properties": {
                            "step_id": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {"type": "string", "enum": ["pending", "running", "complete", "failed", "invalid"]},
                            "tool": {"type": "string"},
                            "agent": {"type": "string"},
                        },
                    },
                },
            },
        }

    def _collect_refinement_triggers(
        self,
        validation_issues: List["ValidationIssue"],  # type: ignore
        convergence_reason_codes: List[str],
        blocked_steps: List[str],
    ) -> List[Dict[str, Any]]:
        """Collect refinement triggers from validation issues, convergence reasons, and blocked steps."""
        triggers = []

        # Add validation issues as triggers
        for issue in validation_issues:
            triggers.append(
                {
                    "type": "validation_issue",
                    "issue_type": getattr(issue, "type", "unknown"),
                    "severity": getattr(issue, "severity", "MEDIUM"),
                    "description": getattr(issue, "description", ""),
                    "location": getattr(issue, "location", {}),
                }
            )

        # Add convergence reason codes as triggers
        for reason_code in convergence_reason_codes:
            triggers.append(
                {
                    "type": "convergence_reason",
                    "reason_code": reason_code,
                }
            )

        # Add blocked steps as triggers
        for step_id in blocked_steps:
            triggers.append(
                {
                    "type": "blocked_step",
                    "step_id": step_id,
                }
            )

        return triggers

    def _identify_target_fragments(
        self,
        current_plan: Plan,
        executed_step_ids: Set[str],
        refinement_triggers: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify target fragments for refinement (only pending/future steps)."""
        target_fragments = set()

        for trigger in refinement_triggers:
            if trigger["type"] == "validation_issue":
                location = trigger.get("location", {})
                step_id = location.get("step_id")
                if step_id and step_id not in executed_step_ids:
                    target_fragments.add(step_id)
            elif trigger["type"] == "blocked_step":
                step_id = trigger.get("step_id")
                if step_id and step_id not in executed_step_ids:
                    target_fragments.add(step_id)

        return list(target_fragments)

    def _generate_refinement_actions_llm(
        self,
        current_plan: Plan,
        target_fragments: List[str],
        refinement_triggers: List[Dict[str, Any]],
        executed_step_ids: Set[str],
    ) -> List[RefinementAction]:
        """Generate refinement actions using LLM-based reasoning."""
        # Construct prompt for refinement
        prompt = f"""Generate refinement actions for the following plan:

Current Plan:
Goal: {current_plan.goal}
Steps:
"""
        for step in current_plan.steps:
            status_marker = " [EXECUTED - DO NOT MODIFY]" if step.step_id in executed_step_ids else ""
            prompt += f"- {step.step_id}: {step.description}{status_marker}\n"

        prompt += "\nRefinement Triggers:\n"
        for trigger in refinement_triggers:
            prompt += f"- {trigger['type']}: {trigger}\n"

        prompt += f"\nTarget Fragments (can be refined): {', '.join(target_fragments)}\n"
        prompt += "\nGenerate refinement actions (ADD/MODIFY/REMOVE/REPLACE) as JSON array.\n"
        prompt += "Each action should have: action_type, target_step_id (or target_plan_section), new_step (for ADD/MODIFY), changes, reason, semantic_validation_input, inconsistency_detected.\n"

        try:
            # Generate LLM response
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=get_prompt(PromptId.RECURSIVE_REFINEMENT_SYSTEM, RecursiveRefinementSystemInput()),
                max_tokens=4096,
                temperature=0.7,
            )

            # Extract refinement actions JSON from response
            response_text = response.get("text", "").strip()
            actions_dict = self._extract_refinement_actions_from_response(response_text)

            # Create RefinementAction objects
            refinement_actions = []
            for action_dict in actions_dict:
                try:
                    action = RefinementAction(**action_dict)
                    refinement_actions.append(action)
                except Exception as e:
                    # Try to repair JSON if schema validation fails
                    try:
                        repaired_dict = self.supervisor.repair_json(
                            malformed_json=json.dumps(action_dict),
                            expected_schema=self._get_refinement_action_schema(),
                        )
                        action = RefinementAction(**json.loads(repaired_dict))
                        refinement_actions.append(action)
                    except Exception:
                        # Skip invalid actions
                        continue

            return refinement_actions

        except LLMError as e:
            raise LLMError(f"Failed to generate refinement actions: {e}") from e
        except Exception as e:
            raise ValidationError(f"Failed to parse refinement actions: {e}") from e

    def _extract_refinement_actions_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Extract refinement actions JSON from LLM response text."""
        import re

        # Look for JSON array
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

        try:
            actions_list = json.loads(json_str)
            if not isinstance(actions_list, list):
                actions_list = [actions_list]
            return actions_list
        except json.JSONDecodeError:
            # Try to repair JSON using supervisor
            try:
                repaired_json = self.supervisor.repair_json(
                    malformed_json=json_str,
                    expected_schema=self._get_refinement_actions_schema(),
                )
                return json.loads(repaired_json)
            except Exception as e:
                raise ValidationError(f"Failed to parse or repair refinement actions JSON: {e}") from e

    def _get_refinement_action_schema(self) -> Dict[str, Any]:
        """Get JSON schema for RefinementAction."""
        return {
            "type": "object",
            "required": ["action_type", "changes", "reason"],
            "properties": {
                "action_type": {"type": "string", "enum": ["ADD", "MODIFY", "REMOVE", "REPLACE"]},
                "target_step_id": {"type": "string"},
                "target_plan_section": {"type": "string"},
                "new_step": {"type": "object"},
                "changes": {"type": "object"},
                "reason": {"type": "string"},
                "semantic_validation_input": {"type": "array"},
                "inconsistency_detected": {"type": "boolean"},
            },
        }

    def _get_refinement_actions_schema(self) -> Dict[str, Any]:
        """Get JSON schema for array of RefinementAction."""
        return {
            "type": "array",
            "items": self._get_refinement_action_schema(),
        }

