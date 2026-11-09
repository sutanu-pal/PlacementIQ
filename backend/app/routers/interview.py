from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.interview import InterviewMessage, InterviewSession
from app.models.resume import Resume
from app.models.user import User
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewSessionListItem,
    InterviewSessionListResponse,
    InterviewSessionResponse,
    InterviewStartRequest,
    InterviewTurnResponse,
)
from app.services.interview_service import interview_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interviews", tags=["AI Mock Interview"])


@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interview_session(
    payload: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new AI mock interview session.
    Automatically customizes opening question based on candidate's uploaded resume projects.
    """
    # 1. Fetch latest analyzed resume if available
    resume_stmt = (
        select(Resume)
        .where(Resume.user_id == current_user.id, Resume.status == "analyzed")
        .order_by(desc(Resume.version))
        .limit(1)
    )
    res = await db.execute(resume_stmt)
    resume = res.scalar_one_or_none()

    skills = [s.get("name", "") for s in (resume.extracted_skills or [])] if resume else []
    projects = (resume.parsed_data or {}).get("projects", []) if resume else []

    # 2. Generate opening question
    first_question = interview_service.generate_opening_question(
        role_title=payload.role_title,
        interview_type=payload.interview_type,
        candidate_skills=skills,
        candidate_projects=projects,
    )

    # 3. Create Session
    session = InterviewSession(
        user_id=current_user.id,
        job_id=payload.job_id,
        resume_id=resume.id if resume else None,
        role_title=payload.role_title,
        interview_type=payload.interview_type,
        status="in_progress",
        current_question_index=0,
        total_questions=payload.total_questions,
    )
    db.add(session)
    await db.flush()

    # 4. Create first InterviewMessage
    msg = InterviewMessage(
        session_id=session.id,
        sequence_num=0,
        question_text=first_question,
        answer_text=None,
        evaluation={},
    )
    db.add(msg)
    await db.commit()

    # Reload session with messages
    query = (
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == session.id)
    )
    loaded = (await db.execute(query)).scalar_one()
    return InterviewSessionResponse.model_validate(loaded)


@router.post("/{session_id}/answer", response_model=InterviewTurnResponse)
async def submit_interview_answer(
    session_id: str,
    payload: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit an answer to the current interview question.
    Returns structured rubric evaluation, score breakdown, and next adaptive question.
    """
    query = (
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == session_id)
    )
    res = await db.execute(query)
    session = res.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview session is already {session.status}.",
        )

    # Find the active message awaiting an answer
    current_msg = next((m for m in session.messages if m.answer_text is None), None)
    if not current_msg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending question to answer.")

    # Execute evaluation and next question generation
    result = await interview_service.evaluate_answer_and_next_question(
        session=session,
        current_question=current_msg.question_text,
        student_answer=payload.answer_text,
        current_index=session.current_question_index,
        total_questions=session.total_questions,
    )

    evaluation = result["evaluation"]
    current_msg.answer_text = payload.answer_text
    current_msg.evaluation = evaluation

    next_q = result["next_question"]
    is_completed = result["is_completed"]

    if next_q and not is_completed:
        session.current_question_index += 1
        new_msg = InterviewMessage(
            session_id=session.id,
            sequence_num=session.current_question_index,
            question_text=next_q,
            answer_text=None,
            evaluation={},
        )
        db.add(new_msg)
    else:
        # Wrap up session scores
        session.status = "completed"
        # Calculate aggregate scores across answered messages
        answered = [m for m in session.messages if m.answer_text is not None] + [current_msg]
        count = len(answered)
        if count > 0:
            session.overall_score = round(sum(m.evaluation.get("overall_score", 0.0) for m in answered) / count, 1)
            session.communication_score = round(sum(m.evaluation.get("communication_score", 0.0) for m in answered) / count, 1)
            session.technical_score = round(sum(m.evaluation.get("technical_score", 0.0) for m in answered) / count, 1)
            session.problem_solving_score = round(sum(m.evaluation.get("problem_solving_score", 0.0) for m in answered) / count, 1)
            session.relevance_score = round(sum(m.evaluation.get("relevance_score", 0.0) for m in answered) / count, 1)

            # Generate strengths & improvement areas
            strengths = []
            improvements = []
            if session.technical_score >= 75:
                strengths.append("Strong technical vocabulary and understanding of system components.")
            else:
                improvements.append("Deepen technical explanations with architectural mechanisms and trade-offs.")

            if session.communication_score >= 75:
                strengths.append("Clear and well-structured responses.")
            else:
                improvements.append("Adopt structured storytelling (STAR method) to explain project decisions.")

            if session.problem_solving_score >= 75:
                strengths.append("Demonstrated good consideration of scale and edge cases.")
            else:
                improvements.append("Proactively address failure modes, concurrency, and validation boundaries.")

            session.strengths = strengths
            session.improvement_areas = improvements
            session.feedback_summary = (
                f"Candidate achieved an overall interview rating of {session.overall_score}% across "
                f"{session.total_questions} questions for {session.role_title}."
            )

    await db.commit()
    await db.refresh(session)

    # Reload with all messages
    query = (
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == session.id)
    )
    loaded = (await db.execute(query)).scalar_one()

    return InterviewTurnResponse(
        evaluation=evaluation,
        next_question=next_q,
        is_completed=is_completed,
        session=InterviewSessionResponse.model_validate(loaded),
    )


@router.get("/", response_model=InterviewSessionListResponse)
async def list_user_interviews(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical interview sessions for the current student."""
    query = (
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(desc(InterviewSession.created_at))
        .offset(offset)
        .limit(limit)
    )
    count_stmt = select(func.count(InterviewSession.id)).where(InterviewSession.user_id == current_user.id)

    total = (await db.execute(count_stmt)).scalar_one_or_none() or 0
    sessions = (await db.execute(query)).scalars().all()

    items = [InterviewSessionListItem.model_validate(s) for s in sessions]
    return InterviewSessionListResponse(items=items, sessions=items, total=total)


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full transcript and evaluation report for an interview session."""
    query = (
        select(InterviewSession)
        .options(selectinload(InterviewSession.messages))
        .where(InterviewSession.id == session_id)
    )
    session = (await db.execute(query)).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found.")

    if session.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return InterviewSessionResponse.model_validate(session)
