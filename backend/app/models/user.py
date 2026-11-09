from __future__ import annotations

from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.job import JobMatch
    from app.models.dsa import DsaSubmission
    from app.models.interview import InterviewSession
    from app.models.roadmap import Roadmap
    from app.models.readiness import PlacementReadinessSnapshot


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    branch: Mapped[str] = mapped_column(String(100), nullable=True, default="")
    semester: Mapped[int] = mapped_column(Integer, nullable=True, default=7)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Resume.version)",
    )
    job_matches: Mapped[List["JobMatch"]] = relationship(
        "JobMatch",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(JobMatch.created_at)",
    )
    dsa_submissions: Mapped[List["DsaSubmission"]] = relationship(
        "DsaSubmission",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(DsaSubmission.created_at)",
    )
    interview_sessions: Mapped[List["InterviewSession"]] = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(InterviewSession.created_at)",
    )
    roadmaps: Mapped[List["Roadmap"]] = relationship(
        "Roadmap",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Roadmap.created_at)",
    )
    readiness_snapshots: Mapped[List["PlacementReadinessSnapshot"]] = relationship(
        "PlacementReadinessSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(PlacementReadinessSnapshot.created_at)",
    )

    def __repr__(self) -> str:
        return f"<User email={self.email} name={self.full_name}>"
