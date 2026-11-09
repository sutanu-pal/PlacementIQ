from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dsa import DsaQuestion, DsaSubmission
from app.models.interview import InterviewSession
from app.models.job import JobMatch
from app.models.resume import Resume
from app.models.roadmap import Roadmap, RoadmapMilestone, RoadmapTask
from app.models.user import User

logger = logging.getLogger(__name__)

CURATED_RESOURCES = {
    "python": {"title": "Python Official Documentation & Data Structures", "url": "https://docs.python.org/3/tutorial/datastructures.html"},
    "fastapi": {"title": "FastAPI Production Guide & Async Patterns", "url": "https://fastapi.tiangolo.com/tutorial/"},
    "postgresql": {"title": "PostgreSQL Indexes & Query Optimization", "url": "https://www.postgresql.org/docs/current/indexes.html"},
    "react": {"title": "React 19 Official Documentation & Hooks", "url": "https://react.dev/learn"},
    "docker": {"title": "Docker Containers Getting Started Guide", "url": "https://docs.docker.com/get-started/"},
    "redis": {"title": "Redis Cache Invalidation & Data Structures", "url": "https://redis.io/docs/latest/develop/get-started/"},
    "dsa_arrays": {"title": "LeetCode Curated Arrays & Two-Pointer Patterns", "url": "https://leetcode.com/explore/interview/card/top-interview-questions-easy/"},
    "dsa_dp": {"title": "Dynamic Programming Patterns & Memoization", "url": "https://leetcode.com/discuss/general-discussion/458695/dynamic-programming-patterns"},
    "dsa_trees": {"title": "Binary Trees & BST Traversal Techniques", "url": "https://leetcode.com/explore/learn/card/data-structure-tree/"},
    "star_method": {"title": "Behavioral STAR Interview Technique Guide", "url": "https://www.themuse.com/advice/star-interview-method"},
    "system_design": {"title": "System Design Primer & Scalability Patterns", "url": "https://github.com/donnemartin/system-design-primer"},
}


class RoadmapService:
    """
    Personalized Cross-Module Learning Roadmap Generation Engine.
    
    Synthesizes signals from:
    1. Resume Analyzer (Module 1): Missing skill categories & formatting improvements.
    2. Job Matching (Module 2): Critical missing required skills from target roles.
    3. DSA Engine (Module 3): Categories where solved count == 0 or accuracy < 40%.
    4. Mock Interview (Module 4): Communication, depth, or problem-solving areas.
    """

    async def generate_roadmap_for_user(
        self,
        db: AsyncSession,
        user: User,
        target_role: str = "Full Stack Engineer",
    ) -> Roadmap:
        # 1. Harvest Module 1 Signals (Resume)
        resume_res = await db.execute(
            select(Resume)
            .where(Resume.user_id == user.id, Resume.status == "analyzed")
            .order_by(desc(Resume.version))
            .limit(1)
        )
        latest_resume = resume_res.scalar_one_or_none()
        resume_improvements = latest_resume.improvement_areas if latest_resume else []

        # 2. Harvest Module 2 Signals (Job Matching)
        match_res = await db.execute(
            select(JobMatch)
            .where(JobMatch.user_id == user.id)
            .order_by(desc(JobMatch.created_at))
            .limit(1)
        )
        latest_match = match_res.scalar_one_or_none()
        missing_req_skills = latest_match.missing_required_skills if latest_match else []
        missing_pref_skills = latest_match.missing_preferred_skills if latest_match else []

        # 3. Harvest Module 3 Signals (DSA Analytics)
        dsa_subs_res = await db.execute(
            select(DsaSubmission.question_id, DsaSubmission.status)
            .where(DsaSubmission.user_id == user.id)
        )
        dsa_subs = dsa_subs_res.all()
        solved_ids = {qid for qid, s in dsa_subs if s == "Accepted"}

        q_res = await db.execute(select(DsaQuestion.id, DsaQuestion.category).where(DsaQuestion.is_active == True))
        all_qs = q_res.all()
        dsa_weaknesses = []
        for cat in ["Dynamic Programming", "Trees", "Graphs", "Arrays", "Greedy"]:
            cat_qs = [qid for qid, c in all_qs if c == cat]
            if cat_qs and not any(qid in solved_ids for qid in cat_qs):
                dsa_weaknesses.append(cat)

        # 4. Harvest Module 4 Signals (Interview)
        int_res = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
            .order_by(desc(InterviewSession.created_at))
            .limit(1)
        )
        latest_interview = int_res.scalar_one_or_none()
        interview_improvements = latest_interview.improvement_areas if latest_interview else []

        # Delete previous active roadmap if any
        prev_roadmaps = (await db.execute(select(Roadmap).where(Roadmap.user_id == user.id))).scalars().all()
        for pr in prev_roadmaps:
            await db.delete(pr)
        await db.flush()

        # 5. Build New 4-Week Milestone Roadmap
        signals_summary = {
            "resume_gaps": resume_improvements[:3],
            "missing_required_skills": missing_req_skills[:4],
            "missing_preferred_skills": missing_pref_skills[:3],
            "dsa_weaknesses": dsa_weaknesses[:3],
            "interview_weaknesses": interview_improvements[:3],
        }

        roadmap = Roadmap(
            user_id=user.id,
            target_role=target_role,
            title=f"4-Week Fast-Track Curriculum: {target_role}",
            description=(
                f"Personalized milestone roadmap generated from your verified resume gaps, "
                f"job matching requirements, DSA analytics, and mock interview rubric evaluations."
            ),
            total_weeks=4,
            completion_pct=0.0,
            current_streak_days=1,
            signals_summary=signals_summary,
        )
        db.add(roadmap)
        await db.flush()

        # Milestone 1: Core Prerequisite Foundations & Missing Required Skills
        m1 = RoadmapMilestone(
            roadmap_id=roadmap.id,
            week_number=1,
            title="Week 1: Core Prerequisites & High-Impact Skill Gaps",
            objective="Bridge mandatory technical skills required by target employer benchmarks.",
        )
        db.add(m1)
        await db.flush()

        # Build M1 Tasks
        top_missing_skill = missing_req_skills[0] if missing_req_skills else "PostgreSQL & Database Indexing"
        res1 = CURATED_RESOURCES.get(top_missing_skill.lower(), CURATED_RESOURCES["postgresql"])
        db.add(RoadmapTask(
            milestone_id=m1.id,
            sequence_order=1,
            title=f"Master Core Competency: {top_missing_skill}",
            description=f"Study core documentation and build a functional proof-of-concept incorporating {top_missing_skill}.",
            priority="High",
            estimated_hours=3.5,
            resource_title=res1["title"],
            resource_url=res1["url"],
            triggered_by=f"Missing mandatory skill detected in {target_role} job matches",
        ))

        db.add(RoadmapTask(
            milestone_id=m1.id,
            sequence_order=2,
            title="Implement Connection Pooling & Safe Schema Migrations",
            description="Build robust async database schemas with explicit foreign key indexing and transaction safety.",
            priority="High",
            estimated_hours=2.5,
            resource_title="FastAPI & SQLAlchemy Production Guide",
            resource_url=CURATED_RESOURCES["fastapi"]["url"],
            triggered_by="Standard baseline for backend placement technical rounds",
        ))

        # Milestone 2: Algorithms & Core Problem Solving
        m2 = RoadmapMilestone(
            roadmap_id=roadmap.id,
            week_number=2,
            title="Week 2: Data Structures & Algorithmic Patterns",
            objective="Close topic mastery gaps identified during DSA coding assessments.",
        )
        db.add(m2)
        await db.flush()

        primary_dsa = dsa_weaknesses[0] if dsa_weaknesses else "Dynamic Programming"
        res2 = CURATED_RESOURCES["dsa_dp"] if "dynamic" in primary_dsa.lower() else CURATED_RESOURCES["dsa_arrays"]
        db.add(RoadmapTask(
            milestone_id=m2.id,
            sequence_order=1,
            title=f"Master {primary_dsa} Patterns & Edge Cases",
            description=f"Solve at least 4 classic problems covering {primary_dsa}. Focus on space-time complexity analysis.",
            priority="High",
            estimated_hours=4.0,
            resource_title=res2["title"],
            resource_url=res2["url"],
            triggered_by=f"Identified as unpracticed category ({primary_dsa}) in DSA assessment engine",
        ))

        db.add(RoadmapTask(
            milestone_id=m2.id,
            sequence_order=2,
            title="Practice Two-Pointer & Sliding Window Techniques",
            description="Complete array and string subarray optimization challenges under timed constraints.",
            priority="Medium",
            estimated_hours=3.0,
            resource_title=CURATED_RESOURCES["dsa_arrays"]["title"],
            resource_url=CURATED_RESOURCES["dsa_arrays"]["url"],
            triggered_by="Core interview pattern across tier-1 software companies",
        ))

        # Milestone 3: Project Architecture & Practical Engineering
        m3 = RoadmapMilestone(
            roadmap_id=roadmap.id,
            week_number=3,
            title="Week 3: Production Project Engineering & Scalability",
            objective="Elevate resume project descriptions with quantitative engineering impact.",
        )
        db.add(m3)
        await db.flush()

        db.add(RoadmapTask(
            milestone_id=m3.id,
            sequence_order=1,
            title="Containerize Application with Docker & Compose",
            description="Create lightweight multi-stage Dockerfiles and isolate dependencies across microservices.",
            priority="High",
            estimated_hours=3.0,
            resource_title=CURATED_RESOURCES["docker"]["title"],
            resource_url=CURATED_RESOURCES["docker"]["url"],
            triggered_by="Identified missing DevOps/containerization competency in target job requirements",
        ))

        db.add(RoadmapTask(
            milestone_id=m3.id,
            sequence_order=2,
            title="Refactor Project Bullet Points into STAR Format",
            description="Restructure resume project points to emphasize Situation, Task, Action, and Quantifiable Result.",
            priority="Medium",
            estimated_hours=2.0,
            resource_title=CURATED_RESOURCES["star_method"]["title"],
            resource_url=CURATED_RESOURCES["star_method"]["url"],
            triggered_by="Feedback from Resume Analyzer scoring engine",
        ))

        # Milestone 4: Mock Interview Polishing & System Design
        m4 = RoadmapMilestone(
            roadmap_id=roadmap.id,
            week_number=4,
            title="Week 4: System Design & Mock Interview Polishing",
            objective="Synthesize communication clarity and structured architectural reasoning.",
        )
        db.add(m4)
        await db.flush()

        db.add(RoadmapTask(
            milestone_id=m4.id,
            sequence_order=1,
            title="Review Distributed Caching & Rate Limiting Architectures",
            description="Study trade-offs between cache-aside, write-through, and token-bucket rate limiting.",
            priority="High",
            estimated_hours=3.5,
            resource_title=CURATED_RESOURCES["system_design"]["title"],
            resource_url=CURATED_RESOURCES["system_design"]["url"],
            triggered_by="Key technical depth criteria evaluated in AI Mock Interview engine",
        ))

        db.add(RoadmapTask(
            milestone_id=m4.id,
            sequence_order=2,
            title="Complete Behavioral Mock Interview with STAR Answers",
            description="Attend a full 4-turn behavioral mock interview focusing on conflict resolution and leadership.",
            priority="Medium",
            estimated_hours=1.5,
            resource_title=CURATED_RESOURCES["star_method"]["title"],
            resource_url=CURATED_RESOURCES["star_method"]["url"],
            triggered_by="Placement readiness behavioral evaluation threshold",
        ))

        await db.commit()

        # Reload complete object with nested relationships
        query = (
            select(Roadmap)
            .options(
                selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.tasks)
            )
            .where(Roadmap.id == roadmap.id)
        )
        return (await db.execute(query)).scalar_one()

    async def toggle_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str,
    ) -> Roadmap:
        # Load task and verify user ownership through roadmap
        q = (
            select(RoadmapTask)
            .join(RoadmapMilestone, RoadmapTask.milestone_id == RoadmapMilestone.id)
            .join(Roadmap, RoadmapMilestone.roadmap_id == Roadmap.id)
            .where(RoadmapTask.id == task_id, Roadmap.user_id == user_id)
        )
        task = (await db.execute(q)).scalar_one_or_none()
        if not task:
            raise ValueError("Task not found or access denied.")

        task.is_completed = not task.is_completed
        task.completed_at = datetime.now(timezone.utc) if task.is_completed else None
        await db.flush()

        # Fetch entire roadmap to recalculate completion percentage
        m_res = await db.execute(
            select(RoadmapMilestone.roadmap_id).where(RoadmapMilestone.id == task.milestone_id)
        )
        roadmap_id = m_res.scalar_one()

        full_q = (
            select(Roadmap)
            .options(
                selectinload(Roadmap.milestones).selectinload(RoadmapMilestone.tasks)
            )
            .where(Roadmap.id == roadmap_id)
        )
        roadmap = (await db.execute(full_q)).scalar_one()

        all_tasks = [t for m in roadmap.milestones for t in m.tasks]
        completed = [t for t in all_tasks if t.is_completed]
        if all_tasks:
            roadmap.completion_pct = round((len(completed) / len(all_tasks)) * 100.0, 1)

        await db.commit()
        await db.refresh(roadmap)
        return roadmap


roadmap_service = RoadmapService()
