from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class JobSkillSchema(BaseModel):
    skill_name: str
    is_required: bool = True
    category: str = "Technical"

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    company: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=10)
    responsibilities: List[str] = Field(default_factory=list)
    eligibility_criteria: Dict[str, Any] = Field(default_factory=dict)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_level: str = "Fresher / Entry Level"
    location: str = "Bengaluru"
    employment_type: str = "Full-time"
    salary_range: str = ""
    is_active: bool = True
    is_synthetic: bool = True


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None
    eligibility_criteria: Optional[Dict[str, Any]] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    is_active: Optional[bool] = None
    is_synthetic: Optional[bool] = None


class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    eligibility_criteria: Dict[str, Any] = Field(default_factory=dict)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_level: str
    location: str
    employment_type: str
    salary_range: str
    is_active: bool
    is_synthetic: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int


class JobMatchRequest(BaseModel):
    resume_id: Optional[str] = None


class JobMatchResponse(BaseModel):
    id: str
    user_id: str
    job_id: str
    resume_id: str
    resume_version: int
    match_score: float
    skill_score: float
    semantic_score: float
    project_score: float
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    project_relevance: Dict[str, Any] = Field(default_factory=dict)
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    explanations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    algorithm_version: str
    created_at: datetime
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    job_location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobMatchListResponse(BaseModel):
    items: List[JobMatchResponse]
    total: int
