from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class PlacementReadinessSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "readiness_snapshots"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    provisional_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evaluated_dimensions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_dimensions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    dimension_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    strengths: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    readiness_tier: Mapped[str] = mapped_column(String(50), nullable=False, default="Getting Started")

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="readiness_snapshots")

    def __repr__(self) -> str:
        return f"<PlacementReadinessSnapshot user={self.user_id} score={self.overall_score}>"
