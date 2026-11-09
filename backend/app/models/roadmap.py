from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Roadmap(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    completion_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    signals_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roadmaps")
    milestones: Mapped[List["RoadmapMilestone"]] = relationship(
        "RoadmapMilestone",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapMilestone.week_number",
    )

    def __repr__(self) -> str:
        return f"<Roadmap id={self.id} user={self.user_id} role={self.target_role}>"


class RoadmapMilestone(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roadmap_milestones"

    roadmap_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="milestones")
    tasks: Mapped[List["RoadmapTask"]] = relationship(
        "RoadmapTask",
        back_populates="milestone",
        cascade="all, delete-orphan",
        order_by="RoadmapTask.sequence_order",
    )

    def __repr__(self) -> str:
        return f"<RoadmapMilestone week={self.week_number} title={self.title}>"


class RoadmapTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roadmap_tasks"

    milestone_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roadmap_milestones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="High")
    estimated_hours: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    resource_title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    resource_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    triggered_by: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    milestone: Mapped["RoadmapMilestone"] = relationship("RoadmapMilestone", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<RoadmapTask title={self.title} done={self.is_completed}>"
