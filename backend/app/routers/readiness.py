from __future__ import annotations

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.readiness import PlacementReadinessSnapshot
from app.models.user import User
from app.schemas.readiness import PlacementReadinessResponse
from app.services.readiness_service import readiness_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/readiness", tags=["Placement Readiness Engine"])


@router.get("/", response_model=PlacementReadinessResponse)
async def get_placement_readiness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute explainable placement readiness score across all 5 dimensions.
    Returns composite score, provisional rating, available/missing dimensions,
    strengths, weaknesses, and targeted preparation recommendations.
    """
    result = await readiness_engine.calculate_readiness(
        db=db,
        user=current_user,
        save_snapshot=True,
    )
    return PlacementReadinessResponse.model_validate(result)


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_readiness_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve historical readiness snapshots to display preparation trends over time.
    """
    query = (
        select(PlacementReadinessSnapshot)
        .where(PlacementReadinessSnapshot.user_id == current_user.id)
        .order_by(desc(PlacementReadinessSnapshot.created_at))
        .limit(20)
    )
    snapshots = (await db.execute(query)).scalars().all()
    return [
        {
            "id": s.id,
            "overall_score": s.overall_score,
            "provisional_score": s.provisional_score,
            "evaluated_dimensions_count": s.evaluated_dimensions_count,
            "readiness_tier": s.readiness_tier,
            "created_at": s.created_at,
        }
        for s in snapshots
    ]
