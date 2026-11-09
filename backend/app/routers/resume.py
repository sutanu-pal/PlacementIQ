from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.resume import (
    ResumeDetailResponse,
    ResumeListResponse,
    ResumeSummaryResponse,
)
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["AI Resume Analyzer"])


@router.post(
    "/upload",
    response_model=ResumeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Analyze Resume PDF",
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF resume file"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    """
    Upload a resume in PDF format.
    Extracts text using PyMuPDF, detects sections, extracts technical skills,
    computes an explainable score, and generates actionable AI/ATS recommendations.
    """
    resume = await ResumeService.process_and_save_resume(
        db=db,
        user_id=current_user.id,
        upload_file=file,
    )
    return ResumeDetailResponse.model_validate(resume)


@router.get(
    "/",
    response_model=ResumeListResponse,
    summary="List All Resume Versions for Authenticated User",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeListResponse:
    """Retrieve history of all resumes uploaded by the current student."""
    resumes = await ResumeService.list_user_resumes(db, current_user.id)
    summaries = [ResumeSummaryResponse.model_validate(r) for r in resumes]
    return ResumeListResponse(resumes=summaries, total=len(summaries))


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    summary="Get Resume Record & Profile",
)
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    """Get full details of a specific resume version owned by the user."""
    resume = await ResumeService.get_user_resume(db, current_user.id, resume_id)
    return ResumeDetailResponse.model_validate(resume)


@router.get(
    "/{resume_id}/analysis",
    response_model=ResumeDetailResponse,
    summary="Get Detailed Resume Analysis & Recommendations",
)
async def get_resume_analysis(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    """Retrieve complete scoring breakdown, skill inventory, and AI feedback."""
    resume = await ResumeService.get_user_resume(db, current_user.id, resume_id)
    return ResumeDetailResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Resume Version",
)
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Delete a resume and remove its file from private storage."""
    await ResumeService.delete_user_resume(db, current_user.id, resume_id)
    return {"status": "deleted", "id": resume_id}
