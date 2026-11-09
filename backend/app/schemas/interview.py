from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InterviewStartRequest(BaseModel):
    role_title: str = Field(..., min_length=2, max_length=255)
    interview_type: str = Field(default="Technical", pattern="^(Technical|Behavioral|System Design)$")
    total_questions: int = Field(default=4, ge=2, le=8)
    job_id: Optional[str] = None


class InterviewAnswerRequest(BaseModel):
    answer_text: str = Field(..., min_length=2, max_length=5000)


class InterviewMessageResponse(BaseModel):
    id: str
    sequence_num: int
    question_text: str
    answer_text: Optional[str] = None
    evaluation: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionResponse(BaseModel):
    id: str
    user_id: str
    role_title: str
    interview_type: str
    status: str
    current_question_index: int
    total_questions: int
    overall_score: float
    communication_score: float
    technical_score: float
    problem_solving_score: float
    relevance_score: float
    strengths: List[str] = Field(default_factory=list)
    improvement_areas: List[str] = Field(default_factory=list)
    feedback_summary: str = ""
    created_at: datetime
    messages: List[InterviewMessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionListItem(BaseModel):
    id: str
    role_title: str
    interview_type: str
    status: str
    overall_score: float
    total_questions: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionListResponse(BaseModel):
    items: List[InterviewSessionListItem]
    sessions: List[InterviewSessionListItem] = Field(default_factory=list)
    total: int


class InterviewTurnResponse(BaseModel):
    evaluation: Dict[str, Any]
    next_question: Optional[str] = None
    is_completed: bool
    session: InterviewSessionResponse
