from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SkillItem(BaseModel):
    name: str
    category: str
    category_name: str


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class ScoreBreakdown(BaseModel):
    structure_score: float
    skills_score: float
    projects_score: float
    education_score: float
    experience_score: float


class AIFeedback(BaseModel):
    summary: str
    strengths: List[str] = Field(default_factory=list)
    actionable_tips: List[str] = Field(default_factory=list)
    ats_recommendations: List[str] = Field(default_factory=list)
    formatting_advice: List[str] = Field(default_factory=list)
    is_ai_generated: bool = False
    model: Optional[str] = None


class ResumeSummaryResponse(BaseModel):
    id: str
    filename: str
    version: int
    file_size_bytes: int
    status: str
    overall_score: float
    is_scanned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeDetailResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    version: int
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    page_count: int
    is_scanned: bool
    overall_score: float
    score_breakdown: Dict[str, Any]
    strengths: List[str]
    improvement_areas: List[str]
    extracted_skills: List[Dict[str, str]]
    parsed_data: Dict[str, Any]
    ai_feedback: Dict[str, Any]
    disclaimer: str = (
        "This score evaluates resume formatting, structural completeness, and technical keyword coverage. "
        "It is an algorithmic readiness signal and does not predict recruitment success."
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    resumes: List[ResumeSummaryResponse]
    items: List[ResumeSummaryResponse] = Field(default_factory=list)
    total: int
