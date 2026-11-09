from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DsaQuestionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., min_length=2, max_length=50)
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    description: str = Field(..., min_length=10)
    constraints: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    starter_code: Dict[str, str] = Field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    time_limit_ms: int = 2000
    memory_limit_mb: int = 128
    is_active: bool = True


class DsaQuestionUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    starter_code: Optional[Dict[str, str]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    time_limit_ms: Optional[int] = None
    memory_limit_mb: Optional[int] = None
    is_active: Optional[bool] = None


class DsaQuestionListItem(BaseModel):
    id: str
    title: str
    slug: str
    category: str
    difficulty: str
    is_active: bool
    created_at: datetime
    is_solved: bool = False

    model_config = ConfigDict(from_attributes=True)


class DsaQuestionDetail(BaseModel):
    id: str
    title: str
    slug: str
    category: str
    difficulty: str
    description: str
    constraints: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    starter_code: Dict[str, str] = Field(default_factory=dict)
    visible_test_cases: List[Dict[str, Any]] = Field(default_factory=list)
    time_limit_ms: int
    memory_limit_mb: int
    is_active: bool
    is_solved: bool = False

    model_config = ConfigDict(from_attributes=True)


class DsaQuestionListResponse(BaseModel):
    items: List[DsaQuestionListItem]
    questions: List[DsaQuestionListItem] = Field(default_factory=list)
    total: int


class DsaSubmitRequest(BaseModel):
    code: str = Field(..., min_length=5, max_length=10000)
    language: str = Field(default="python")


class DsaSubmitResponse(BaseModel):
    id: str
    question_id: str
    language: str
    status: str
    passed_count: int
    total_count: int
    execution_time_ms: float
    memory_used_mb: float
    error_message: Optional[str] = None
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DsaSubmissionListItem(BaseModel):
    id: str
    question_id: str
    question_title: Optional[str] = None
    language: str
    status: str
    passed_count: int
    total_count: int
    execution_time_ms: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DsaSubmissionListResponse(BaseModel):
    items: List[DsaSubmissionListItem]
    total: int


class DsaTopicAnalytics(BaseModel):
    category: str
    total_questions: int
    solved_questions: int
    accuracy_pct: float


class DsaUserAnalyticsResponse(BaseModel):
    total_solved: int
    total_questions: int
    overall_solve_pct: float
    total_submissions: int
    overall_accuracy_pct: float
    topic_breakdown: List[DsaTopicAnalytics]
    weakness_areas: List[str]
    recommendations: List[str]
