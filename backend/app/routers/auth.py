from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin_user, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Register a new student/user."""
    stmt = select(User).where(User.email == payload.email)
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        college=payload.college or "",
        branch=payload.branch or "",
        semester=payload.semester or 7,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id, {"email": user.email, "is_admin": user.is_admin})
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Authenticate with email and password."""
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(user.id, {"email": user.email, "is_admin": user.is_admin})
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Exchange a valid refresh token for a fresh access token."""
    decoded = decode_refresh_token(payload.refresh_token)
    if not decoded or "sub" not in decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    stmt = select(User).where(User.id == decoded["sub"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    new_access_token = create_access_token(user.id, {"email": user.email, "is_admin": user.is_admin})
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Retrieve profile of the currently logged-in user."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update profile of currently authenticated user."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.college is not None:
        current_user.college = payload.college
    if payload.branch is not None:
        current_user.branch = payload.branch
    if payload.semester is not None:
        current_user.semester = payload.semester

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/admin/users", response_model=List[UserResponse])
async def list_all_users_admin(
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    """Admin-only endpoint to list all platform users."""
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/admin/stats")
async def get_admin_platform_stats(
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Admin-only platform telemetry and module distribution analytics."""
    from app.models.resume import Resume
    from app.models.job import Job, JobMatch
    from app.models.dsa import DsaQuestion, DsaSubmission
    from app.models.interview import InterviewSession
    from app.models.roadmap import Roadmap
    from app.models.readiness import PlacementReadinessSnapshot

    # Users
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one_or_none() or 0
    total_students = (await db.execute(select(func.count(User.id)).where(User.is_admin == False))).scalar_one_or_none() or 0

    # Resumes
    total_resumes = (await db.execute(select(func.count(Resume.id)))).scalar_one_or_none() or 0
    avg_resume = (await db.execute(select(func.avg(Resume.overall_score)))).scalar_one_or_none() or 0.0

    # Jobs & Matching
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar_one_or_none() or 0
    total_matches = (await db.execute(select(func.count(JobMatch.id)))).scalar_one_or_none() or 0
    avg_match = (await db.execute(select(func.avg(JobMatch.match_score)))).scalar_one_or_none() or 0.0

    # DSA
    total_dsa_q = (await db.execute(select(func.count(DsaQuestion.id)))).scalar_one_or_none() or 0
    total_dsa_subs = (await db.execute(select(func.count(DsaSubmission.id)))).scalar_one_or_none() or 0
    accepted_subs = (await db.execute(select(func.count(DsaSubmission.id)).where(DsaSubmission.status == "Accepted"))).scalar_one_or_none() or 0

    # Interviews
    total_interviews = (await db.execute(select(func.count(InterviewSession.id)).where(InterviewSession.status == "completed"))).scalar_one_or_none() or 0
    avg_interview = (await db.execute(select(func.avg(InterviewSession.overall_score)).where(InterviewSession.status == "completed"))).scalar_one_or_none() or 0.0

    # Roadmaps
    total_roadmaps = (await db.execute(select(func.count(Roadmap.id)))).scalar_one_or_none() or 0

    # Readiness tiers
    tier1 = (await db.execute(select(func.count(PlacementReadinessSnapshot.id)).where(PlacementReadinessSnapshot.overall_score >= 75))).scalar_one_or_none() or 0
    tier2 = (await db.execute(select(func.count(PlacementReadinessSnapshot.id)).where(PlacementReadinessSnapshot.overall_score >= 50, PlacementReadinessSnapshot.overall_score < 75))).scalar_one_or_none() or 0
    tier3 = (await db.execute(select(func.count(PlacementReadinessSnapshot.id)).where(PlacementReadinessSnapshot.overall_score < 50))).scalar_one_or_none() or 0

    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_resumes": total_resumes,
        "avg_resume_score": round(float(avg_resume), 1),
        "total_jobs": total_jobs,
        "total_matches": total_matches,
        "avg_match_score": round(float(avg_match), 1),
        "total_dsa_questions": total_dsa_q,
        "total_dsa_submissions": total_dsa_subs,
        "dsa_accuracy_pct": round((accepted_subs / total_dsa_subs * 100.0) if total_dsa_subs > 0 else 0.0, 1),
        "total_interviews": total_interviews,
        "avg_interview_score": round(float(avg_interview), 1),
        "total_roadmaps": total_roadmaps,
        "readiness_distribution": {
            "tier1_ready": tier1,
            "tier2_approaching": tier2,
            "tier3_needs_prep": tier3,
        },
    }


@router.put("/admin/users/{user_id}/toggle-status", response_model=UserResponse)
async def toggle_user_active_status(
    user_id: str,
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Admin-only endpoint to toggle user activation status."""
    res = await db.execute(select(User).where(User.id == user_id))
    target_user = res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_active = not target_user.is_active
    await db.commit()
    await db.refresh(target_user)
    return UserResponse.model_validate(target_user)
