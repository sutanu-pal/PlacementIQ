from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job, JobMatch
from app.models.user import User
from app.schemas.job import JobMatchListResponse, JobMatchResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/job-matches", tags=["Job Match History"])


@router.get("/", response_model=JobMatchListResponse)
async def list_user_matches(
    job_id: Optional[str] = Query(None, description="Filter matches by specific job ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve historical match evaluations for the authenticated student.
    Enforces user-level privacy and isolation.
    """
    query = (
        select(JobMatch)
        .options(joinedload(JobMatch.job))
        .where(JobMatch.user_id == current_user.id)
    )
    count_stmt = select(func.count(JobMatch.id)).where(JobMatch.user_id == current_user.id)

    if job_id:
        query = query.where(JobMatch.job_id == job_id)
        count_stmt = count_stmt.where(JobMatch.job_id == job_id)

    total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

    query = query.order_by(desc(JobMatch.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    matches = result.scalars().all()

    items = []
    for m in matches:
        resp = JobMatchResponse.model_validate(m)
        if m.job:
            resp.job_title = m.job.title
            resp.job_company = m.job.company
            resp.job_location = m.job.location
        items.append(resp)

    return JobMatchListResponse(items=items, matches=items, total=total)


@router.get("/{match_id}", response_model=JobMatchResponse)
async def get_match_detail(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a detailed breakdown of an individual match result.
    Enforces that students cannot view match reports belonging to other users.
    """
    query = (
        select(JobMatch)
        .options(joinedload(JobMatch.job))
        .where(JobMatch.id == match_id)
    )
    result = await db.execute(query)
    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match evaluation record not found.",
        )

    # Privacy check
    if match.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: This match report belongs to another candidate.",
        )

    resp = JobMatchResponse.model_validate(match)
    if match.job:
        resp.job_title = match.job.title
        resp.job_company = match.job.company
        resp.job_location = match.job.location

    return resp
