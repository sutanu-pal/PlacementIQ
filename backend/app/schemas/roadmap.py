from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class RoadmapTaskResponse(BaseModel):
    id: str
    sequence_order: int
    title: str
    description: str
    priority: str
    estimated_hours: float
    resource_title: str
    resource_url: str
    triggered_by: str
    is_completed: bool
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RoadmapMilestoneResponse(BaseModel):
    id: str
    week_number: int
    title: str
    objective: str
    tasks: List[RoadmapTaskResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RoadmapResponse(BaseModel):
    id: str
    user_id: str
    target_role: str
    title: str
    description: str
    total_weeks: int
    completion_pct: float
    current_streak_days: int
    signals_summary: Dict[str, Any] = Field(default_factory=dict)
    milestones: List[RoadmapMilestoneResponse] = Field(default_factory=list)
    created_at: datetime

    @computed_field
    @property
    def progress_percentage(self) -> float:
        return self.completion_pct

    @computed_field
    @property
    def total_tasks_count(self) -> int:
        return sum(len(m.tasks) for m in self.milestones)

    @computed_field
    @property
    def completed_tasks_count(self) -> int:
        return sum(sum(1 for t in m.tasks if t.is_completed) for m in self.milestones)

    model_config = ConfigDict(from_attributes=True)


class RoadmapGenerateRequest(BaseModel):
    target_role: str = Field(default="Full Stack Engineer", min_length=2, max_length=255)
