"""Pydantic models for structured LLM responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """LLM output: event classification."""

    event_type: Literal["log", "metric_alert", "app_error", "deploy", "unknown"] = "unknown"
    severity: Literal["low", "medium", "high", "critical"] = "low"
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    reasoning: str = ""


class ExtractionResult(BaseModel):
    """LLM output: structured extraction from raw event."""

    summary: str = ""
    affected_component: str = ""
    error_code: str = ""
    user_impact: str = ""
    key_metrics: dict[str, str] = Field(default_factory=dict)


class RootCauseResult(BaseModel):
    """LLM output: root cause analysis."""

    root_cause: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    contributing_factors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    similar_incidents: list[str] = Field(default_factory=list)
