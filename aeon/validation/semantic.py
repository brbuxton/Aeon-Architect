"""Semantic validation layer using LLM-based reasoning."""

import json
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from aeon.exceptions import LLMError, ValidationError

if TYPE_CHECKING:
    from aeon.observability.logger import JSONLLogger
from aeon.llm.interface import LLMAdapter
from aeon.supervisor.repair import Supervisor
from aeon.tools.registry import ToolRegistry
from aeon.validation.models import SemanticValidationReport, ValidationIssue


class SemanticValidator:
    """Semantic validator using LLM-based reasoning for quality checks."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        """
        Initialize semantic validator.

        Args:
            llm_adapter: LLM adapter for semantic reasoning
            tool_registry: Optional tool registry for hallucination detection
        """
        self.llm_adapter = llm_adapter
        self.tool_registry = tool_registry
        self.supervisor = Supervisor(llm_adapter)

    def validate(
        self,
        artifact: Dict[str, Any],
        artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"],
        tool_registry: Optional[ToolRegistry] = None,
        logger: Optional["JSONLLogger"] = None,
        correlation_id: Optional[str] = None,
    ) -> SemanticValidationReport:
        """
        Validate semantic quality of plan, step, or execution artifact.

        Args:
            artifact: Artifact to validate (plan, step, or execution artifact as JSON-serializable dict)
            artifact_type: Type of artifact being validated
            tool_registry: Optional tool registry for hallucination detection (overrides instance registry)

        Returns:
            SemanticValidationReport with detected issues, severity, and proposed repairs

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid
        """
        # Use provided tool_registry or fall back to instance registry
        registry = tool_registry or self.tool_registry

        # Perform structural checks before LLM delegation
        structural_issues = self._perform_structural_checks(artifact, artifact_type)
        
        # Perform LLM-based semantic checks
        semantic_issues = self._perform_semantic_checks(artifact, artifact_type, registry)
        
        # Combine all issues
        all_issues = structural_issues + semantic_issues

        # Create validation report
        report = SemanticValidationReport(
            validation_id=str(uuid.uuid4()),
            artifact_type=artifact_type,
            issues=all_issues,
        )

        return report

    def _perform_structural_checks(
        self,
        artifact: Dict[str, Any],
        artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"],
    ) -> List[ValidationIssue]:
        """
        Perform structural checks (duplicate IDs, missing attributes) before LLM delegation.

        Args:
            artifact: Artifact to check
            artifact_type: Type of artifact

        Returns:
            List of structural validation issues
        """
        issues: List[ValidationIssue] = []

        if artifact_type == "plan":
            # Check for duplicate step IDs
            if "steps" in artifact:
                step_ids = []
                for step in artifact.get("steps", []):
                    if isinstance(step, dict) and "step_id" in step:
                        step_id = step["step_id"]
                        if step_id in step_ids:
                            issues.append(
                                ValidationIssue(
                                    issue_id=str(uuid.uuid4()),
                                    type="consistency",
                                    severity="HIGH",
                                    description=f"Duplicate step_id found: {step_id}",
                                    location={"step_id": step_id},
                                )
                            )
                        step_ids.append(step_id)

                # Check for missing required fields
                for idx, step in enumerate(artifact.get("steps", [])):
                    if isinstance(step, dict):
                        if "step_id" not in step:
                            issues.append(
                                ValidationIssue(
                                    issue_id=str(uuid.uuid4()),
                                    type="consistency",
                                    severity="CRITICAL",
                                    description=f"Step at index {idx} missing required field: step_id",
                                    location={"step_index": idx},
                                )
                            )
                        if "description" not in step:
                            issues.append(
                                ValidationIssue(
                                    issue_id=str(uuid.uuid4()),
                                    type="consistency",
                                    severity="CRITICAL",
                                    description=f"Step at index {idx} missing required field: description",
                                    location={"step_index": idx},
                                )
                            )

            # Check for missing goal
            if "goal" not in artifact:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        type="consistency",
                        severity="CRITICAL",
                        description="Plan missing required field: goal",
                    )
                )

        elif artifact_type == "step":
            # Check for missing required fields
            if "step_id" not in artifact:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        type="consistency",
                        severity="CRITICAL",
                        description="Step missing required field: step_id",
                    )
                )
            if "description" not in artifact:
                issues.append(
                    ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        type="consistency",
                        severity="CRITICAL",
                        description="Step missing required field: description",
                    )
                )

        return issues

    def _perform_semantic_checks(
        self,
        artifact: Dict[str, Any],
        artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"],
        tool_registry: Optional[ToolRegistry],
    ) -> List[ValidationIssue]:
        """
        Perform LLM-based semantic checks.

        Args:
            artifact: Artifact to check
            artifact_type: Type of artifact
            tool_registry: Tool registry for hallucination detection

        Returns:
            List of semantic validation issues
        """
        issues: List[ValidationIssue] = []

        # Build prompt for LLM-based validation
        prompt = self._construct_validation_prompt(artifact, artifact_type, tool_registry)

        # Call LLM for semantic validation
        try:
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for validation
            )

            # Extract validation results from LLM response
            validation_text = response.get("text", "").strip()
            validation_result = self._parse_llm_validation_response(validation_text)

            # Convert LLM response to ValidationIssue objects
            for issue_data in validation_result.get("issues", []):
                try:
                    issue = ValidationIssue(
                        issue_id=str(uuid.uuid4()),
                        type=issue_data.get("type", "consistency"),
                        severity=issue_data.get("severity", "MEDIUM"),
                        description=issue_data.get("description", ""),
                        location=issue_data.get("location"),
                        proposed_repair=issue_data.get("proposed_repair"),
                    )
                    issues.append(issue)
                except Exception as e:
                    # Skip invalid issue data
                    continue

        except (LLMError, ValidationError) as e:
            # If LLM fails, return empty issues list (best-effort advisory)
            # Log error but don't fail validation
            if logger and correlation_id:
                if isinstance(e, ValidationError):
                    error_record = e.to_error_record(
                        context={"validation_type": "semantic", "artifact_type": artifact_type}
                    )
                    logger.log_error(
                        correlation_id=correlation_id,
                        error=error_record,
                        validation_type="semantic",
                        validation_details={"artifact_type": artifact_type},
                    )
            pass
        except Exception as e:
            # Unexpected error - return empty issues (best-effort)
            if logger and correlation_id:
                from aeon.exceptions import ValidationError as ValidationErrorClass
                validation_error = ValidationErrorClass(f"Unexpected validation error: {str(e)}")
                error_record = validation_error.to_error_record(
                    context={"validation_type": "semantic", "artifact_type": artifact_type, "error_type": type(e).__name__}
                )
                logger.log_error(
                    correlation_id=correlation_id,
                    error=error_record,
                    validation_type="semantic",
                    validation_details={"artifact_type": artifact_type, "error_type": type(e).__name__},
                )
            pass

        return issues

    def _construct_validation_prompt(
        self,
        artifact: Dict[str, Any],
        artifact_type: Literal["plan", "step", "execution_artifact", "cross_phase"],
        tool_registry: Optional[ToolRegistry],
    ) -> str:
        """Construct prompt for LLM-based validation."""
        prompt_parts = []

        if artifact_type == "plan":
            prompt_parts.append("Validate this plan for semantic quality issues:")
            prompt_parts.append(f"Goal: {artifact.get('goal', 'N/A')}")
            prompt_parts.append(f"Steps: {json.dumps(artifact.get('steps', []), indent=2)}")
            
            prompt_parts.append("""
Check for the following issues:
1. SPECIFICITY: Are steps concrete and actionable? Are descriptions vague or unclear?
2. RELEVANCE: Do steps contribute to the overall goal? Are there irrelevant steps?
3. DO/SAY MISMATCH: Do step descriptions match their actions or tool invocations?
4. CONSISTENCY: Do steps logically flow? Are there circular dependencies? Are dependencies satisfied?
""")

            # Add tool registry info for hallucination detection
            if tool_registry:
                available_tools = tool_registry.list_all()
                tool_names = [t["name"] for t in available_tools]
                prompt_parts.append(f"Available tools: {', '.join(tool_names)}")
                prompt_parts.append("5. HALLUCINATION: Are any tools referenced that don't exist in the available tools list?")

        elif artifact_type == "step":
            prompt_parts.append("Validate this step for semantic quality issues:")
            prompt_parts.append(json.dumps(artifact, indent=2))
            
            prompt_parts.append("""
Check for the following issues:
1. SPECIFICITY: Is the step description concrete and actionable?
2. RELEVANCE: Does this step contribute to the plan goal?
3. DO/SAY MISMATCH: Does the step description match its actions or tool invocations?
""")

            # Add tool registry info for hallucination detection
            if tool_registry and artifact.get("tool"):
                available_tools = tool_registry.list_all()
                tool_names = [t["name"] for t in available_tools]
                prompt_parts.append(f"Available tools: {', '.join(tool_names)}")
                prompt_parts.append(f"4. HALLUCINATION: Is the tool '{artifact.get('tool')}' in the available tools list?")

        elif artifact_type == "execution_artifact":
            prompt_parts.append("Validate this execution artifact for semantic quality issues:")
            prompt_parts.append(json.dumps(artifact, indent=2))
            
            prompt_parts.append("""
Check for the following issues:
1. CONSISTENCY: Does the artifact align with the plan and step descriptions?
2. RELEVANCE: Is the artifact relevant to the task goal?
""")

        elif artifact_type == "cross_phase":
            prompt_parts.append("Validate cross-phase consistency:")
            prompt_parts.append(json.dumps(artifact, indent=2))
            
            prompt_parts.append("""
Check for consistency between plan, execution steps, final answer, and memory artifacts.
Look for contradictions, misalignments, or inconsistencies across phases.
""")

        prompt_parts.append("""
Return a JSON object with this structure:
{
  "issues": [
    {
      "type": "specificity" | "relevance" | "consistency" | "hallucination" | "do_say_mismatch",
      "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
      "description": "Human-readable explanation of the issue",
      "location": {"step_id": "...", "field": "..."} (optional),
      "proposed_repair": {"field": "suggested fix"} (optional)
    }
  ]
}

Return only the JSON object, no explanation.
""")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for semantic validation."""
        return """You are a semantic validation assistant. Analyze plans, steps, and execution artifacts for quality issues.
Identify specificity problems, relevance issues, do/say mismatches, hallucinated tools, and consistency violations.
Classify issues by type and assign severity scores. Propose semantic repairs when possible.
Return structured JSON with detected issues."""

    def _parse_llm_validation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM validation response, handling schema violations with supervisor repair.

        Args:
            response_text: LLM response text

        Returns:
            Parsed validation result dict

        Raises:
            ValidationError: If parsing fails after supervisor repair attempts
        """
        # Try to extract JSON from response
        try:
            # Try parsing as-is
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from text
        import re
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Use supervisor repair for schema violations
        try:
            repaired = self.supervisor.repair_json(
                response_text,
                expected_schema={
                    "type": "object",
                    "properties": {
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "description": {"type": "string"},
                                    "location": {"type": "object"},
                                    "proposed_repair": {"type": "object"}
                                },
                                "required": ["type", "severity", "description"]
                            }
                        }
                    },
                    "required": ["issues"]
                },
                max_attempts=2,
            )
            return repaired
        except Exception as e:
            # If supervisor repair fails, return empty result (best-effort advisory)
            return {"issues": []}

