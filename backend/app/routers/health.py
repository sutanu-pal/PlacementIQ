from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.auth import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", response_model=HealthCheckResponse)
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthCheckResponse:
    """Verify application and database health."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
