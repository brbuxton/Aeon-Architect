"""Adaptive depth heuristics data models."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TaskProfile(BaseModel):
    """Represents inferred task characteristics used for adaptive depth heuristics and TTL allocation."""

    profile_version: int = Field(
        default=1, ge=1, description="Version number for TaskProfile updates"
    )
    reasoning_depth: int = Field(
        ...,
        ge=1,
        le=5,
        description="Ordinal scale 1-5 (1=very shallow, 2=shallow, 3=moderate, 4=deep, 5=very deep)",
    )
    information_sufficiency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Float 0.0-1.0 (0.0=insufficient, 1.0=sufficient)",
    )
    expected_tool_usage: Literal["none", "minimal", "moderate", "extensive"] = Field(
        ..., description="Expected tool usage level"
    )
    output_breadth: Literal["narrow", "moderate", "broad"] = Field(
        ..., description="Expected output breadth"
    )
    confidence_requirement: Literal["low", "medium", "high"] = Field(
        ..., description="Required confidence level"
    )
    raw_inference: str = Field(
        ...,
        min_length=1,
        description="Natural-language explanation summarizing how each dimension was determined",
    )

    @classmethod
    def default(cls) -> "TaskProfile":
        """
        Create default TaskProfile when inference fails.

        Returns:
            Default TaskProfile with moderate complexity assumptions
        """
        return cls(
            profile_version=1,
            reasoning_depth=3,
            information_sufficiency=0.5,
            expected_tool_usage="moderate",
            output_breadth="moderate",
            confidence_requirement="medium",
            raw_inference="Default profile: moderate complexity assumed",
        )

    @field_validator("reasoning_depth")
    @classmethod
    def validate_reasoning_depth(cls, v: int) -> int:
        """Validate reasoning_depth is in range [1, 5]."""
        if not (1 <= v <= 5):
            raise ValueError("reasoning_depth must be in range [1, 5]")
        return v

    @field_validator("information_sufficiency")
    @classmethod
    def validate_information_sufficiency(cls, v: float) -> float:
        """Validate information_sufficiency is in range [0.0, 1.0]."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("information_sufficiency must be in range [0.0, 1.0]")
        return v


class AdaptiveDepthConfiguration(BaseModel):
    """Configuration for adaptive depth heuristics."""

    global_ttl_limit: Optional[int] = Field(
        default=None, ge=1, description="Global TTL limit to cap allocation"
    )
    default_ttl: int = Field(
        default=10, ge=1, description="Default TTL when TaskProfile inference fails"
    )
    ttl_base_multiplier: float = Field(
        default=2.0,
        ge=0.1,
        description="Base multiplier for TTL allocation formula",
    )
    reasoning_depth_weight: float = Field(
        default=1.5,
        ge=0.1,
        description="Weight for reasoning_depth in TTL allocation",
    )
    information_sufficiency_weight: float = Field(
        default=1.0,
        ge=0.1,
        description="Weight for information_sufficiency in TTL allocation",
    )
    tool_usage_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "none": 0.5,
            "minimal": 0.75,
            "moderate": 1.0,
            "extensive": 1.5,
        },
        description="Weights for expected_tool_usage levels",
    )
    output_breadth_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "narrow": 0.75,
            "moderate": 1.0,
            "broad": 1.5,
        },
        description="Weights for output_breadth levels",
    )
    confidence_requirement_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "low": 0.75,
            "medium": 1.0,
            "high": 1.5,
        },
        description="Weights for confidence_requirement levels",
    )

