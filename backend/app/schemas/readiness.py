from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class DimensionDetail(BaseModel):
    score: float
    weight: float
    available: bool
    status_message: str
    metric_summary: str


class PlacementReadinessResponse(BaseModel):
    overall_score: float
    provisional_score: float
    evaluated_dimensions_count: int
    total_dimensions_count: int
    readiness_tier: str
    dimension_scores: Dict[str, DimensionDetail]
    breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    actionable_recommendations: List[str] = Field(default_factory=list)
    formula_documentation: str
    disclaimer: str

    model_config = ConfigDict(from_attributes=True)
