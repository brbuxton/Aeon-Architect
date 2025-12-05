"""Convergence engine for assessing task execution convergence."""

import json
import re
from typing import Any, Dict, List, Optional

from typing import TYPE_CHECKING, Optional

from aeon.convergence.models import ConvergenceAssessment
from aeon.exceptions import LLMError, ValidationError
from aeon.llm.interface import LLMAdapter
from aeon.supervisor.repair import Supervisor
from aeon.validation.models import SemanticValidationReport

if TYPE_CHECKING:
    from aeon.kernel.state import ExecutionContext
    from aeon.observability.logger import JSONLLogger


class ConvergenceEngine:
    """Convergence engine using LLM-based reasoning for completion assessment."""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        completeness_threshold: float = 0.95,
        coherence_threshold: float = 0.90,
        consistency_threshold: float = 0.90,
    ) -> None:
        """
        Initialize convergence engine.

        Args:
            llm_adapter: LLM adapter for convergence reasoning
            completeness_threshold: Default completeness threshold (default 0.95)
            coherence_threshold: Default coherence threshold (default 0.90)
            consistency_threshold: Default consistency threshold (default 0.90)
        """
        self.llm_adapter = llm_adapter
        self.completeness_threshold = completeness_threshold
        self.coherence_threshold = coherence_threshold
        self.consistency_threshold = consistency_threshold
        self.supervisor = Supervisor(llm_adapter)

    def assess(
        self,
        plan_state: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        semantic_validation_report: SemanticValidationReport,
        custom_criteria: Optional[Dict[str, Any]] = None,
        execution_context: Optional["ExecutionContext"] = None,
        logger: Optional["JSONLLogger"] = None,
    ) -> ConvergenceAssessment:
        """
        Assess whether task execution has converged on a complete, coherent, consistent solution.

        Args:
            plan_state: Current plan state (JSON-serializable dict)
            execution_results: Step outputs and tool results (list of JSON-serializable dicts)
            semantic_validation_report: Semantic validation report from validation layer
            custom_criteria: Optional custom convergence criteria (dict with thresholds)

        Returns:
            ConvergenceAssessment with converged flag, reason codes, scores, and metadata

        Raises:
            LLMError: If LLM API calls fail after retries
            ValidationError: If inputs are invalid
        """
        # Use custom criteria if provided, otherwise use defaults
        completeness_threshold = (
            custom_criteria.get("completeness_threshold", self.completeness_threshold)
            if custom_criteria
            else self.completeness_threshold
        )
        coherence_threshold = (
            custom_criteria.get("coherence_threshold", self.coherence_threshold)
            if custom_criteria
            else self.coherence_threshold
        )
        consistency_threshold = (
            custom_criteria.get("consistency_threshold", self.consistency_threshold)
            if custom_criteria
            else self.consistency_threshold
        )

        # Perform LLM-based convergence assessment
        try:
            assessment_result = self._perform_convergence_assessment(
                plan_state=plan_state,
                execution_results=execution_results,
                semantic_validation_report=semantic_validation_report,
                completeness_threshold=completeness_threshold,
                coherence_threshold=coherence_threshold,
                consistency_threshold=consistency_threshold,
            )
        except (LLMError, ValidationError) as e:
            # If LLM fails, return conservative assessment (not converged)
            return ConvergenceAssessment(
                converged=False,
                reason_codes=["llm_assessment_failed", str(e)],
                completeness_score=0.0,
                coherence_score=0.0,
                consistency_status={},
                detected_issues=[f"LLM assessment failed: {str(e)}"],
                metadata={"error": str(e), "assessment_failed": True},
            )
        except Exception as e:
            # Unexpected error - return conservative assessment
            return ConvergenceAssessment(
                converged=False,
                reason_codes=["unexpected_error", str(e)],
                completeness_score=0.0,
                coherence_score=0.0,
                consistency_status={},
                detected_issues=[f"Unexpected error: {str(e)}"],
                metadata={"error": str(e), "assessment_failed": True},
            )

        # Extract scores and determine convergence
        completeness_score = assessment_result.get("completeness_score", 0.0)
        coherence_score = assessment_result.get("coherence_score", 0.0)
        consistency_status = assessment_result.get("consistency_status", {})
        detected_issues = assessment_result.get("detected_issues", [])
        reason_codes = assessment_result.get("reason_codes", [])

        # Determine consistency alignment (all alignment flags must be True)
        consistency_aligned = all(
            consistency_status.get(key, False)
            for key in ["plan_aligned", "step_aligned", "answer_aligned", "memory_aligned"]
        )

        # Check convergence criteria
        completeness_met = completeness_score >= completeness_threshold
        coherence_met = coherence_score >= coherence_threshold
        consistency_met = consistency_aligned

        # Determine convergence (all criteria must be met)
        converged = completeness_met and coherence_met and consistency_met

        # Generate reason codes if not converged
        if not converged:
            if not reason_codes:
                reason_codes = []
            if not completeness_met:
                reason_codes.append(f"completeness_below_threshold_{completeness_score:.2f}_<_{completeness_threshold:.2f}")
            if not coherence_met:
                reason_codes.append(f"coherence_below_threshold_{coherence_score:.2f}_<_{coherence_threshold:.2f}")
            if not consistency_met:
                reason_codes.append("consistency_not_aligned")
        else:
            if not reason_codes:
                reason_codes = [
                    "completeness_threshold_met",
                    "coherence_threshold_met",
                    "consistency_aligned",
                ]

        # Handle conflicts (if criteria conflict, mark as not converged)
        if completeness_met and coherence_met and not consistency_met:
            # Conflict: high scores but consistency issues
            converged = False
            if "consistency_conflict" not in reason_codes:
                reason_codes.append("consistency_conflict")

        # Build metadata
        metadata = {
            "thresholds_used": {
                "completeness": completeness_threshold,
                "coherence": coherence_threshold,
                "consistency": consistency_threshold,
            },
            "criteria_met": {
                "completeness": completeness_met,
                "coherence": coherence_met,
                "consistency": consistency_met,
            },
            "semantic_validation_issues_count": len(semantic_validation_report.issues),
            "semantic_validation_severity": semantic_validation_report.overall_severity,
        }
        metadata.update(assessment_result.get("metadata", {}))

        assessment = ConvergenceAssessment(
            converged=converged,
            reason_codes=reason_codes,
            completeness_score=completeness_score,
            coherence_score=coherence_score,
            consistency_status=consistency_status,
            detected_issues=detected_issues,
            metadata=metadata,
        )
        
        # Log evaluation outcome (T025, T074, T075, T076)
        if logger and execution_context:
            from aeon.observability.models import ConvergenceAssessmentSummary, ValidationIssuesSummary
            from datetime import datetime
            
            # Create convergence assessment summary with reason codes explaining convergence decision (T074, T076)
            convergence_summary = ConvergenceAssessmentSummary(
                converged=converged,
                reason_codes=reason_codes,  # Reason codes explain why convergence was/wasn't achieved (T076)
                scores={
                    "completeness": completeness_score,
                    "coherence": coherence_score,
                },
                pass_number=0,  # Pass number should come from caller if available
            )
            
            # Create validation issues summary
            validation_summary = ValidationIssuesSummary(
                total_issues=len(semantic_validation_report.issues),
                critical_count=sum(1 for i in semantic_validation_report.issues if i.severity == "CRITICAL"),
                error_count=sum(1 for i in semantic_validation_report.issues if i.severity == "ERROR"),
                warning_count=sum(1 for i in semantic_validation_report.issues if i.severity == "WARNING"),
                info_count=sum(1 for i in semantic_validation_report.issues if i.severity == "INFO"),
                issues_by_type={},
            )
            
            # Build evaluation_signals
            evaluation_signals = {
                "convergence_assessment": convergence_summary.model_dump(),
                "validation_issues": validation_summary.model_dump(),
            }
            
            # Log with enhanced summary models (T074, T075)
            logger.log_evaluation_outcome(
                correlation_id=execution_context.correlation_id,
                convergence_assessment=convergence_summary.model_dump(),
                validation_report=validation_summary.model_dump(),
                evaluation_signals=evaluation_signals,
                convergence_assessment_summary=convergence_summary,  # T074: Pass summary model
                validation_issues_summary=validation_summary,  # T074: Pass summary model
                pass_number=None,  # Pass number should come from caller if available
            )
        
        return assessment

    def _perform_convergence_assessment(
        self,
        plan_state: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        semantic_validation_report: SemanticValidationReport,
        completeness_threshold: float,
        coherence_threshold: float,
        consistency_threshold: float,
    ) -> Dict[str, Any]:
        """
        Perform LLM-based convergence assessment.

        Args:
            plan_state: Current plan state
            execution_results: Execution results
            semantic_validation_report: Semantic validation report
            completeness_threshold: Completeness threshold
            coherence_threshold: Coherence threshold
            consistency_threshold: Consistency threshold

        Returns:
            Assessment result dict with scores, status, and metadata
        """
        # Construct prompt for convergence assessment
        prompt = self._construct_convergence_prompt(
            plan_state=plan_state,
            execution_results=execution_results,
            semantic_validation_report=semantic_validation_report,
            completeness_threshold=completeness_threshold,
            coherence_threshold=coherence_threshold,
            consistency_threshold=consistency_threshold,
        )

        # Call LLM
        try:
            response = self.llm_adapter.generate(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more deterministic assessment
            )
        except Exception as e:
            raise LLMError(f"LLM call failed: {str(e)}") from e

        # Parse LLM response
        response_text = response.get("text", "").strip()
        assessment_result = self._parse_llm_assessment_response(response_text)

        return assessment_result

    def _construct_convergence_prompt(
        self,
        plan_state: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        semantic_validation_report: SemanticValidationReport,
        completeness_threshold: float,
        coherence_threshold: float,
        consistency_threshold: float,
    ) -> str:
        """Construct prompt for LLM-based convergence assessment."""
        prompt_parts = []

        prompt_parts.append("Assess whether task execution has converged on a complete, coherent, consistent solution.")
        prompt_parts.append("")

        # Plan state
        prompt_parts.append("PLAN STATE:")
        prompt_parts.append(json.dumps(plan_state, indent=2))
        prompt_parts.append("")

        # Execution results
        prompt_parts.append("EXECUTION RESULTS:")
        prompt_parts.append(json.dumps(execution_results, indent=2))
        prompt_parts.append("")

        # Semantic validation report
        prompt_parts.append("SEMANTIC VALIDATION REPORT:")
        prompt_parts.append(f"Issues found: {len(semantic_validation_report.issues)}")
        prompt_parts.append(f"Overall severity: {semantic_validation_report.overall_severity}")
        if semantic_validation_report.issues:
            prompt_parts.append("Issues:")
            for issue in semantic_validation_report.issues[:10]:  # Limit to first 10 issues
                prompt_parts.append(f"  - [{issue.severity}] {issue.type}: {issue.description}")
        prompt_parts.append("")

        # Assessment criteria
        prompt_parts.append("ASSESSMENT CRITERIA:")
        prompt_parts.append("")
        prompt_parts.append("1. COMPLETENESS (0.0-1.0):")
        prompt_parts.append("   - Are all required steps completed?")
        prompt_parts.append("   - Is the task goal fully addressed?")
        prompt_parts.append("   - Are there any missing components or gaps?")
        prompt_parts.append(f"   - Threshold: {completeness_threshold:.2f}")
        prompt_parts.append("")
        prompt_parts.append("2. COHERENCE (0.0-1.0):")
        prompt_parts.append("   - Do the execution results form a coherent solution?")
        prompt_parts.append("   - Are the steps logically connected?")
        prompt_parts.append("   - Does the solution make sense as a whole?")
        prompt_parts.append(f"   - Threshold: {coherence_threshold:.2f}")
        prompt_parts.append("")
        prompt_parts.append("3. CONSISTENCY (alignment status):")
        prompt_parts.append("   - plan_aligned: Does execution align with the plan?")
        prompt_parts.append("   - step_aligned: Do step outputs align with step descriptions?")
        prompt_parts.append("   - answer_aligned: Does the final answer align with the task goal?")
        prompt_parts.append("   - memory_aligned: Are memory artifacts consistent with execution?")
        prompt_parts.append(f"   - Threshold: All alignment flags must be True")
        prompt_parts.append("")

        prompt_parts.append("""
Return a JSON object with this structure:
{
  "completeness_score": 0.0-1.0,
  "coherence_score": 0.0-1.0,
  "consistency_status": {
    "plan_aligned": true/false,
    "step_aligned": true/false,
    "answer_aligned": true/false,
    "memory_aligned": true/false
  },
  "detected_issues": ["issue description 1", "issue description 2", ...],
  "reason_codes": ["reason_code_1", "reason_code_2", ...],
  "metadata": {
    "completeness_explanation": "explanation of completeness score",
    "coherence_explanation": "explanation of coherence score",
    "consistency_explanation": "explanation of consistency status"
  }
}

Return only the JSON object, no explanation.
""")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for convergence assessment."""
        return """You are a convergence assessment assistant. Evaluate task execution for completeness, coherence, and consistency.
Assess whether the execution has converged on a complete, coherent, consistent solution.
Provide numeric scores (0.0-1.0) for completeness and coherence, and alignment status for consistency.
Return structured JSON with scores, status, and explanations."""

    def _parse_llm_assessment_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM assessment response, handling schema violations with supervisor repair.

        Args:
            response_text: LLM response text

        Returns:
            Parsed assessment result dict

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
                        "completeness_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "coherence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "consistency_status": {
                            "type": "object",
                            "properties": {
                                "plan_aligned": {"type": "boolean"},
                                "step_aligned": {"type": "boolean"},
                                "answer_aligned": {"type": "boolean"},
                                "memory_aligned": {"type": "boolean"},
                            },
                            "required": ["plan_aligned", "step_aligned", "answer_aligned", "memory_aligned"],
                        },
                        "detected_issues": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "reason_codes": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "metadata": {"type": "object"},
                    },
                    "required": ["completeness_score", "coherence_score", "consistency_status"],
                },
                max_attempts=2,
            )
            return repaired
        except Exception as e:
            # If supervisor repair fails, return conservative default
            return {
                "completeness_score": 0.0,
                "coherence_score": 0.0,
                "consistency_status": {
                    "plan_aligned": False,
                    "step_aligned": False,
                    "answer_aligned": False,
                    "memory_aligned": False,
                },
                "detected_issues": [f"Failed to parse LLM response: {str(e)}"],
                "reason_codes": ["llm_parse_failed"],
                "metadata": {"parse_error": str(e)},
            }

