from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import Job
    from app.models.resume import Resume


class InterviewSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interview_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )

    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Technical", index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress", index=True)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=4)

    # Multi-dimensional rubric scores (0-100)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    technical_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    problem_solving_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    strengths: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    feedback_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="interview_sessions")
    messages: Mapped[List["InterviewMessage"]] = relationship(
        "InterviewMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewMessage.sequence_num",
    )

    def __repr__(self) -> str:
        return f"<InterviewSession {self.id} user={self.user_id} role={self.role_title} status={self.status}>"


class InterviewMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interview_messages"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evaluation: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationship
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<InterviewMessage session={self.session_id} seq={self.sequence_num}>"


class InterviewTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "interview_templates"

    role_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    interview_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Technical", index=True)
    questions_pool: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    evaluation_rubric: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<InterviewTemplate role={self.role_title} type={self.interview_type}>"
