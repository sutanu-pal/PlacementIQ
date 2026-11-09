from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.roadmap import Roadmap, RoadmapMilestone
from app.models.user import User
from app.schemas.roadmap import RoadmapGenerateRequest, RoadmapResponse
from app.services.roadmap_service import roadmap_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roadmap", tags=["Personalized Learning Roadmap"])


@router.get("/", response_model=RoadmapResponse)
async def get_current_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the current personalized learning roadmap for the student.
    If no roadmap has been generated yet, automatically synthesizes one.
    """
    query = (
        select(Roadmap)
        .options(
            selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.tasks)
        )
        .where(Roadmap.user_id == current_user.id)
        .order_by(desc(Roadmap.created_at))
        .limit(1)
    )
    res = await db.execute(query)
    roadmap = res.scalar_one_or_none()

    if not roadmap:
        roadmap = await roadmap_service.generate_roadmap_for_user(
            db=db,
            user=current_user,
            target_role="Full Stack Software Engineer",
        )

    return RoadmapResponse.model_validate(roadmap)


@router.post("/generate", response_model=RoadmapResponse)
async def generate_new_roadmap(
    payload: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate the personalized roadmap using the latest cross-module signals:
    resume skill gaps, job matching missing requirements, DSA weaknesses, and interview feedback.
    """
    roadmap = await roadmap_service.generate_roadmap_for_user(
        db=db,
        user=current_user,
        target_role=payload.target_role,
    )
    return RoadmapResponse.model_validate(roadmap)


@router.post("/tasks/{task_id}/toggle", response_model=RoadmapResponse)
async def toggle_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle task completion status and update student progress telemetry and streak.
    """
    try:
        updated_roadmap = await roadmap_service.toggle_task(
            db=db,
            task_id=task_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return RoadmapResponse.model_validate(updated_roadmap)
