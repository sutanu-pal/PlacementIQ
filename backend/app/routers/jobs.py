from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.job import Job, JobMatch, JobSkill
from app.models.resume import Resume
from app.models.user import User
from app.schemas.job import (
    JobCreate,
    JobListResponse,
    JobMatchRequest,
    JobMatchResponse,
    JobResponse,
    JobUpdate,
)
from app.services.job_matching_service import job_matching_service
from app.services.job_seed_service import seed_sample_jobs
from app.ai.embedding_service import embedding_service
from app.ai.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    search: Optional[str] = Query(None, description="Search by title, company, or keywords"),
    experience_level: Optional[str] = Query(None, description="Filter by experience level"),
    location: Optional[str] = Query(None, description="Filter by location"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    is_active: Optional[bool] = Query(True, description="Filter active jobs"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Browse active job opportunities with filtering.
    Automatically seeds benchmark synthetic opportunities if jobs table is empty.
    """
    # Auto-seed if empty
    count_query = select(func.count(Job.id))
    total_in_db = (await db.execute(count_query)).scalar_one_or_none() or 0
    if total_in_db == 0:
        await seed_sample_jobs(db)

    query = select(Job)
    count_stmt = select(func.count(Job.id))

    if is_active is not None:
        query = query.where(Job.is_active == is_active)
        count_stmt = count_stmt.where(Job.is_active == is_active)

    if search:
        search_filter = or_(
            Job.title.ilike(f"%{search}%"),
            Job.company.ilike(f"%{search}%"),
            Job.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    if experience_level:
        query = query.where(Job.experience_level.ilike(f"%{experience_level}%"))
        count_stmt = count_stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))

    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
        count_stmt = count_stmt.where(Job.location.ilike(f"%{location}%"))

    if employment_type:
        query = query.where(Job.employment_type.ilike(f"%{employment_type}%"))
        count_stmt = count_stmt.where(Job.employment_type.ilike(f"%{employment_type}%"))

    # Total matching count
    total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

    # Paginate and order
    query = query.order_by(desc(Job.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    # Filter in-memory for skill if requested
    items = []
    for j in jobs:
        if skill:
            reqs = [s.lower() for s in (j.required_skills or [])]
            prefs = [s.lower() for s in (j.preferred_skills or [])]
            if skill.lower() not in reqs and skill.lower() not in prefs:
                continue
        items.append(j)

    job_responses = [JobResponse.model_validate(j) for j in items]
    return JobListResponse(items=job_responses, jobs=job_responses, total=total)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full details of a single job opportunity."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job opportunity with ID '{job_id}' not found.",
        )
    return JobResponse.model_validate(job)


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new job opportunity.
    Admin-only endpoint. Automatically generates embedding and skill relational links.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required to create job postings.",
        )

    job = Job(
        title=payload.title,
        company=payload.company,
        description=payload.description,
        responsibilities=payload.responsibilities,
        eligibility_criteria=payload.eligibility_criteria,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        experience_level=payload.experience_level,
        location=payload.location,
        employment_type=payload.employment_type,
        salary_range=payload.salary_range,
        is_active=payload.is_active,
        is_synthetic=payload.is_synthetic,
    )

    # Compute embedding
    job_text = (
        f"{job.title} at {job.company}. {job.description} "
        f"Responsibilities: {' '.join(job.responsibilities)} "
        f"Skills: {', '.join(job.required_skills)}"
    )
    job.embedding = embedding_service.encode_text(job_text)

    db.add(job)
    await db.flush()

    for s in payload.required_skills:
        cat = skill_extractor.get_category_for_skill(s)
        db.add(JobSkill(job_id=job.id, skill_name=s, is_required=True, category=cat))

    for s in payload.preferred_skills:
        cat = skill_extractor.get_category_for_skill(s)
        db.add(JobSkill(job_id=job.id, skill_name=s, is_required=False, category=cat))

    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing job opportunity. Admin-only."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required to update job postings.",
        )

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    update_data = payload.model_dump(exclude_unset=True)
    recompute_embedding = False

    for key, value in update_data.items():
        setattr(job, key, value)
        if key in ("title", "company", "description", "responsibilities", "required_skills"):
            recompute_embedding = True

    if recompute_embedding:
        job_text = (
            f"{job.title} at {job.company}. {job.description} "
            f"Responsibilities: {' '.join(job.responsibilities)} "
            f"Skills: {', '.join(job.required_skills)}"
        )
        job.embedding = embedding_service.encode_text(job_text)

    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a job opportunity and associated matches. Admin-only."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required to delete job postings.",
        )

    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    await db.delete(job)
    await db.commit()
    return {"detail": f"Job '{job.title}' deleted successfully."}


@router.post("/{job_id}/match", response_model=JobMatchResponse)
async def match_resume_to_job(
    job_id: str,
    payload: JobMatchRequest = JobMatchRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run explainable semantic matching between a student's resume and this job opportunity.
    If no resume_id is provided, automatically uses the student's latest analyzed resume.
    """
    # 1. Fetch Job
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    # 2. Fetch Target Resume
    if payload.resume_id:
        resume_stmt = select(Resume).where(
            Resume.id == payload.resume_id,
            Resume.user_id == current_user.id,
        )
        res = await db.execute(resume_stmt)
        resume = res.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified resume not found or does not belong to you.",
            )
    else:
        # Default to latest analyzed resume
        resume_stmt = (
            select(Resume)
            .where(Resume.user_id == current_user.id, Resume.status == "analyzed")
            .order_by(desc(Resume.version))
            .limit(1)
        )
        res = await db.execute(resume_stmt)
        resume = res.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No analyzed resume found. Please upload a resume in the Resume Analyzer first.",
            )

    # 3. Execute NLP Matching
    match_data = job_matching_service.match_resume_to_job(resume=resume, job=job)

    # 4. Persist Match Result in JobMatch table
    match_record = JobMatch(
        user_id=current_user.id,
        job_id=job.id,
        resume_id=resume.id,
        resume_version=resume.version,
        match_score=match_data["match_score"],
        skill_score=match_data["skill_score"],
        semantic_score=match_data["semantic_score"],
        project_score=match_data["project_score"],
        matched_skills=match_data["matched_skills"],
        missing_required_skills=match_data["missing_required_skills"],
        missing_preferred_skills=match_data["missing_preferred_skills"],
        project_relevance=match_data["project_relevance"],
        score_breakdown=match_data["score_breakdown"],
        explanations=match_data["explanations"],
        recommendations=match_data["recommendations"],
        algorithm_version=match_data["algorithm_version"],
    )

    db.add(match_record)
    await db.commit()
    await db.refresh(match_record)

    # Format response
    resp = JobMatchResponse.model_validate(match_record)
    resp.job_title = job.title
    resp.job_company = job.company
    resp.job_location = job.location
    return resp
