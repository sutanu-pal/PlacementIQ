from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.dsa import DsaQuestion, DsaSubmission
from app.models.user import User
from app.schemas.dsa import (
    DsaQuestionCreate,
    DsaQuestionDetail,
    DsaQuestionListItem,
    DsaQuestionListResponse,
    DsaQuestionUpdate,
    DsaSubmissionListItem,
    DsaSubmissionListResponse,
    DsaSubmitRequest,
    DsaSubmitResponse,
    DsaTopicAnalytics,
    DsaUserAnalyticsResponse,
)
from app.services.code_executor import code_sandbox_executor
from app.services.dsa_seed_service import seed_dsa_questions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dsa", tags=["DSA Assessment Engine"])


async def ensure_dsa_seeded(db: AsyncSession) -> None:
    cnt = (await db.execute(select(func.count(DsaQuestion.id)))).scalar_one_or_none() or 0
    if cnt == 0:
        await seed_dsa_questions(db)


@router.get("/questions", response_model=DsaQuestionListResponse)
async def list_questions(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Easy, Medium, Hard)"),
    search: Optional[str] = Query(None, description="Search by title or description"),
    status_filter: Optional[str] = Query(None, description="'solved' or 'unsolved'"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List DSA coding questions with category/difficulty filters and solved state indicators.
    Automatically seeds curated benchmark question bank if table is empty.
    """
    await ensure_dsa_seeded(db)

    query = select(DsaQuestion).where(DsaQuestion.is_active == True)
    count_stmt = select(func.count(DsaQuestion.id)).where(DsaQuestion.is_active == True)

    if category:
        query = query.where(DsaQuestion.category.ilike(f"%{category}%"))
        count_stmt = count_stmt.where(DsaQuestion.category.ilike(f"%{category}%"))

    if difficulty:
        query = query.where(DsaQuestion.difficulty.ilike(f"%{difficulty}%"))
        count_stmt = count_stmt.where(DsaQuestion.difficulty.ilike(f"%{difficulty}%"))

    if search:
        search_filt = or_(
            DsaQuestion.title.ilike(f"%{search}%"),
            DsaQuestion.description.ilike(f"%{search}%"),
        )
        query = query.where(search_filt)
        count_stmt = count_stmt.where(search_filt)

    total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

    query = query.order_by(DsaQuestion.category, DsaQuestion.difficulty).offset(offset).limit(limit)
    res = await db.execute(query)
    questions = res.scalars().all()

    # Get set of question IDs solved by the user
    solved_stmt = select(DsaSubmission.question_id).where(
        DsaSubmission.user_id == current_user.id,
        DsaSubmission.status == "Accepted",
    ).distinct()
    solved_res = await db.execute(solved_stmt)
    solved_ids = set(solved_res.scalars().all())

    items = []
    for q in questions:
        is_solved = q.id in solved_ids
        if status_filter == "solved" and not is_solved:
            continue
        if status_filter == "unsolved" and is_solved:
            continue

        item = DsaQuestionListItem(
            id=q.id,
            title=q.title,
            slug=q.slug,
            category=q.category,
            difficulty=q.difficulty,
            is_active=q.is_active,
            created_at=q.created_at,
            is_solved=is_solved,
        )
        items.append(item)

    return DsaQuestionListResponse(items=items, questions=items, total=total)


@router.get("/questions/{id_or_slug}", response_model=DsaQuestionDetail)
async def get_question(
    id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve single question detail with starter code and visible test cases only.
    Hidden verification test cases are kept private.
    """
    await ensure_dsa_seeded(db)
    stmt = select(DsaQuestion).where(
        or_(DsaQuestion.id == id_or_slug, DsaQuestion.slug == id_or_slug),
        DsaQuestion.is_active == True,
    )
    res = await db.execute(stmt)
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question '{id_or_slug}' not found.",
        )

    # Check if solved by current user
    solved_stmt = select(DsaSubmission.id).where(
        DsaSubmission.user_id == current_user.id,
        DsaSubmission.question_id == q.id,
        DsaSubmission.status == "Accepted",
    ).limit(1)
    is_solved = (await db.execute(solved_stmt)).scalar_one_or_none() is not None

    visible_tcs = [tc for tc in (q.test_cases or []) if not tc.get("is_hidden", False)]

    return DsaQuestionDetail(
        id=q.id,
        title=q.title,
        slug=q.slug,
        category=q.category,
        difficulty=q.difficulty,
        description=q.description,
        constraints=q.constraints,
        examples=q.examples,
        starter_code=q.starter_code,
        visible_test_cases=visible_tcs,
        time_limit_ms=q.time_limit_ms,
        memory_limit_mb=q.memory_limit_mb,
        is_active=q.is_active,
        is_solved=is_solved,
    )


@router.post("/questions", response_model=DsaQuestionDetail, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: DsaQuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new DSA coding question. Admin-only."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges are required to create assessment questions.",
        )

    # Check duplicate slug
    exist = await db.execute(select(DsaQuestion).where(DsaQuestion.slug == payload.slug))
    if exist.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question with slug '{payload.slug}' already exists.",
        )

    q = DsaQuestion(
        title=payload.title,
        slug=payload.slug,
        category=payload.category,
        difficulty=payload.difficulty,
        description=payload.description,
        constraints=payload.constraints,
        examples=payload.examples,
        starter_code=payload.starter_code,
        test_cases=payload.test_cases,
        time_limit_ms=payload.time_limit_ms,
        memory_limit_mb=payload.memory_limit_mb,
        is_active=payload.is_active,
    )
    db.add(q)
    await db.commit()
    await db.refresh(q)

    visible_tcs = [tc for tc in q.test_cases if not tc.get("is_hidden", False)]
    return DsaQuestionDetail(
        id=q.id,
        title=q.title,
        slug=q.slug,
        category=q.category,
        difficulty=q.difficulty,
        description=q.description,
        constraints=q.constraints,
        examples=q.examples,
        starter_code=q.starter_code,
        visible_test_cases=visible_tcs,
        time_limit_ms=q.time_limit_ms,
        memory_limit_mb=q.memory_limit_mb,
        is_active=q.is_active,
        is_solved=False,
    )


@router.put("/questions/{id}", response_model=DsaQuestionDetail)
async def update_question(
    id: str,
    payload: DsaQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing DSA question. Admin-only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")

    res = await db.execute(select(DsaQuestion).where(DsaQuestion.id == id))
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(q, k, v)

    await db.commit()
    await db.refresh(q)
    visible_tcs = [tc for tc in q.test_cases if not tc.get("is_hidden", False)]
    return DsaQuestionDetail(
        id=q.id,
        title=q.title,
        slug=q.slug,
        category=q.category,
        difficulty=q.difficulty,
        description=q.description,
        constraints=q.constraints,
        examples=q.examples,
        starter_code=q.starter_code,
        visible_test_cases=visible_tcs,
        time_limit_ms=q.time_limit_ms,
        memory_limit_mb=q.memory_limit_mb,
        is_active=q.is_active,
    )


@router.delete("/questions/{id}", status_code=status.HTTP_200_OK)
async def delete_question(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a DSA question. Admin-only."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")

    res = await db.execute(select(DsaQuestion).where(DsaQuestion.id == id))
    q = res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    await db.delete(q)
    await db.commit()
    return {"detail": f"Question '{q.title}' deleted successfully."}


@router.post("/questions/{id}/submit", response_model=DsaSubmitResponse)
async def submit_solution(
    id: str,
    payload: DsaSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit solution code for automated evaluation in the secure Python sandbox.
    Executes against both visible and hidden test cases, returning granular results.
    """
    res = await db.execute(select(DsaQuestion).where(DsaQuestion.id == id))
    question = res.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    timeout_sec = max(1.0, min(10.0, question.time_limit_ms / 1000.0))

    # Run in sandbox
    eval_result = code_sandbox_executor.execute_submission(
        code=payload.code,
        test_cases=question.test_cases or [],
        timeout_sec=timeout_sec,
    )

    # Save submission
    sub = DsaSubmission(
        user_id=current_user.id,
        question_id=question.id,
        language=payload.language,
        code=payload.code,
        status=eval_result["status"],
        passed_count=eval_result["passed_count"],
        total_count=eval_result["total_count"],
        execution_time_ms=eval_result["execution_time_ms"],
        memory_used_mb=eval_result["memory_used_mb"],
        error_message=eval_result["error_message"],
        test_results=eval_result["test_results"],
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    return DsaSubmitResponse.model_validate(sub)


@router.get("/submissions", response_model=DsaSubmissionListResponse)
async def list_user_submissions(
    question_id: Optional[str] = Query(None, description="Filter by question ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical submissions for the current student."""
    query = (
        select(DsaSubmission, DsaQuestion.title.label("q_title"))
        .join(DsaQuestion, DsaSubmission.question_id == DsaQuestion.id)
        .where(DsaSubmission.user_id == current_user.id)
    )
    count_stmt = select(func.count(DsaSubmission.id)).where(DsaSubmission.user_id == current_user.id)

    if question_id:
        query = query.where(DsaSubmission.question_id == question_id)
        count_stmt = count_stmt.where(DsaSubmission.question_id == question_id)

    total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

    query = query.order_by(desc(DsaSubmission.created_at)).offset(offset).limit(limit)
    rows = (await db.execute(query)).all()

    items = []
    for sub, q_title in rows:
        item = DsaSubmissionListItem(
            id=sub.id,
            question_id=sub.question_id,
            question_title=q_title,
            language=sub.language,
            status=sub.status,
            passed_count=sub.passed_count,
            total_count=sub.total_count,
            execution_time_ms=sub.execution_time_ms,
            created_at=sub.created_at,
        )
        items.append(item)

    return DsaSubmissionListResponse(items=items, total=total)


@router.get("/submissions/{id}", response_model=DsaSubmitResponse)
async def get_submission(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single submission details enforcing ownership."""
    res = await db.execute(select(DsaSubmission).where(DsaSubmission.id == id))
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")

    if sub.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return DsaSubmitResponse.model_validate(sub)


@router.get("/analytics", response_model=DsaUserAnalyticsResponse)
async def get_user_dsa_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get topic-wise DSA performance metrics, solved count, accuracy,
    weakness identification, and actionable improvement recommendations.
    """
    await ensure_dsa_seeded(db)
    # 1. Fetch all questions
    q_res = await db.execute(select(DsaQuestion).where(DsaQuestion.is_active == True))
    all_questions = q_res.scalars().all()
    total_q_count = len(all_questions)

    # Category mapping: category -> list of question IDs
    category_map: dict[str, list[str]] = {}
    for q in all_questions:
        category_map.setdefault(q.category, []).append(q.id)

    # 2. Fetch all user submissions
    sub_res = await db.execute(select(DsaSubmission).where(DsaSubmission.user_id == current_user.id))
    user_subs = sub_res.scalars().all()
    total_subs = len(user_subs)

    # Identify solved questions
    solved_q_ids = {s.question_id for s in user_subs if s.status == "Accepted"}
    total_solved = len(solved_q_ids)

    # 3. Calculate category-wise breakdown
    topic_breakdown: List[DsaTopicAnalytics] = []
    weaknesses: List[str] = []

    for cat, q_ids in category_map.items():
        cat_total = len(q_ids)
        cat_solved = len([qid for qid in q_ids if qid in solved_q_ids])

        # Category submissions
        cat_subs = [s for s in user_subs if s.question_id in q_ids]
        accepted_cat_subs = [s for s in cat_subs if s.status == "Accepted"]
        accuracy = (len(accepted_cat_subs) / len(cat_subs) * 100.0) if cat_subs else 0.0

        topic_breakdown.append(DsaTopicAnalytics(
            category=cat,
            total_questions=cat_total,
            solved_questions=cat_solved,
            accuracy_pct=round(accuracy, 1),
        ))

        # Flag weakness if solved 0 or accuracy < 40% with at least one attempt
        if cat_solved == 0 or (cat_subs and accuracy < 40.0):
            weaknesses.append(cat)

    overall_acc = (
        (len([s for s in user_subs if s.status == "Accepted"]) / total_subs * 100.0)
        if total_subs > 0 else 0.0
    )
    solve_pct = (total_solved / total_q_count * 100.0) if total_q_count > 0 else 0.0

    # 4. Generate recommendations
    recs: List[str] = []
    if weaknesses:
        top_weak = ", ".join(weaknesses[:3])
        recs.append(f"Focus practice on {top_weak}. Master foundational patterns like two pointers and sliding window.")
    if total_solved < 5:
        recs.append("Aim to solve at least 5 foundational Easy and Medium problems to establish placement baseline.")
    if overall_acc > 0 and overall_acc < 60.0:
        recs.append("Review edge cases (e.g. empty inputs, single element, negative numbers) before submitting code.")
    if not recs:
        recs.append("Excellent consistency! Advance to Hard Dynamic Programming and Graph challenges.")

    return DsaUserAnalyticsResponse(
        total_solved=total_solved,
        total_questions=total_q_count,
        overall_solve_pct=round(solve_pct, 1),
        total_submissions=total_subs,
        overall_accuracy_pct=round(overall_acc, 1),
        topic_breakdown=topic_breakdown,
        weakness_areas=weaknesses,
        recommendations=recs,
    )
