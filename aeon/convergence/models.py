"""Convergence detection data models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ConvergenceAssessment(BaseModel):
    """Result from convergence engine determining whether task execution has converged."""

    converged: bool = Field(..., description="Whether convergence was achieved")
    reason_codes: List[str] = Field(
        default_factory=list,
        description="Array of strings indicating why convergence was/wasn't achieved",
    )
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numeric score 0.0-1.0",
    )
    coherence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numeric score 0.0-1.0",
    )
    consistency_status: Dict[str, Any] = Field(
        default_factory=dict,
        description="Object with plan/step/answer/memory alignment status (JSON-serializable)",
    )
    detected_issues: List[str] = Field(
        default_factory=list,
        description="Array of issue descriptions",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional evaluation data (JSON-serializable)",
    )

    @field_validator("completeness_score", "coherence_score")
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Validate that scores are in range [0.0, 1.0]."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Score must be in range [0.0, 1.0]")
        return v

    @model_validator(mode="after")
    def validate_reason_codes_when_not_converged(self) -> "ConvergenceAssessment":
        """Validate that reason_codes is non-empty when converged is False."""
        if not self.converged and not self.reason_codes:
            raise ValueError("reason_codes must be non-empty when converged is False")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "converged": True,
                "reason_codes": ["completeness_threshold_met", "coherence_threshold_met", "consistency_aligned"],
                "completeness_score": 0.98,
                "coherence_score": 0.95,
                "consistency_status": {
                    "plan_aligned": True,
                    "step_aligned": True,
                    "answer_aligned": True,
                    "memory_aligned": True,
                },
                "detected_issues": [],
                "metadata": {
                    "evaluation_timestamp": "2025-01-27T12:00:00Z",
                    "thresholds_used": {
                        "completeness": 0.95,
                        "coherence": 0.90,
                        "consistency": 0.90,
                    },
                },
            }
        }
    }

