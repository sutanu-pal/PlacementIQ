from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import JobMatch


class Resume(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="analyzed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_scanned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    parsed_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    extracted_skills: Mapped[List[Dict[str, str]]] = mapped_column(JSON, nullable=False, default=list)

    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_breakdown: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    strengths: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    ai_feedback: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    job_matches: Mapped[List["JobMatch"]] = relationship(
        "JobMatch",
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id} user={self.user_id} ver={self.version} score={self.overall_score}>"
