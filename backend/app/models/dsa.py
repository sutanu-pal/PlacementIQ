from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class DsaQuestion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dsa_questions"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # Easy, Medium, Hard
    description: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    examples: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    starter_code: Mapped[Dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    test_cases: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    time_limit_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=128)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Relationship
    submissions: Mapped[List["DsaSubmission"]] = relationship(
        "DsaSubmission",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="desc(DsaSubmission.created_at)",
    )

    def __repr__(self) -> str:
        return f"<DsaQuestion {self.slug} ({self.difficulty})>"


class DsaSubmission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dsa_submissions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dsa_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    language: Mapped[str] = mapped_column(String(20), nullable=False, default="python")
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Accepted, Wrong Answer, etc.
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_used_mb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    test_results: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dsa_submissions")
    question: Mapped["DsaQuestion"] = relationship("DsaQuestion", back_populates="submissions")

    def __repr__(self) -> str:
        return f"<DsaSubmission user={self.user_id} q={self.question_id} status={self.status}>"
