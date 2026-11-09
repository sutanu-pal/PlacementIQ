from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobSkill
from app.ai.embedding_service import embedding_service
from app.ai.skill_extractor import skill_extractor

logger = logging.getLogger(__name__)


async def seed_sample_jobs(db: AsyncSession) -> int:
    """
    Seeds synthetic benchmark jobs into the database if the jobs table is empty.
    Returns the number of jobs created.
    """
    result = await db.execute(select(func.count(Job.id)))
    count = result.scalar_one_or_none() or 0
    if count > 0:
        return 0

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    json_path = os.path.join(base_dir, "data", "sample_jobs.json")

    if not os.path.exists(json_path):
        logger.warning("sample_jobs.json not found at %s", json_path)
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            sample_jobs: List[Dict[str, Any]] = json.load(f)
    except Exception as exc:
        logger.error("Failed to parse sample_jobs.json: %s", exc)
        return 0

    created = 0
    for item in sample_jobs:
        job = Job(
            title=item["title"],
            company=item["company"],
            description=item["description"],
            responsibilities=item.get("responsibilities", []),
            eligibility_criteria=item.get("eligibility_criteria", {}),
            required_skills=item.get("required_skills", []),
            preferred_skills=item.get("preferred_skills", []),
            experience_level=item.get("experience_level", "Fresher / Entry Level"),
            location=item.get("location", "Bengaluru"),
            employment_type=item.get("employment_type", "Full-time"),
            salary_range=item.get("salary_range", ""),
            is_active=item.get("is_active", True),
            is_synthetic=item.get("is_synthetic", True),
        )

        # Generate dense 384-d embedding
        text_for_embedding = (
            f"Job Title: {job.title}. Company: {job.company}. "
            f"Description: {job.description} "
            f"Responsibilities: {' '.join(job.responsibilities)} "
            f"Required Skills: {', '.join(job.required_skills)}"
        )
        try:
            job.embedding = embedding_service.encode_text(text_for_embedding)
        except Exception as e:
            logger.warning("Could not pre-embed job %s: %s", job.title, e)

        db.add(job)
        await db.flush()  # to obtain job.id

        # Also populate JobSkill relational rows for required and preferred skills
        for s in job.required_skills:
            cat = skill_extractor.get_category_for_skill(s)
            db.add(JobSkill(
                job_id=job.id,
                skill_name=s,
                is_required=True,
                category=cat,
            ))

        for s in job.preferred_skills:
            cat = skill_extractor.get_category_for_skill(s)
            db.add(JobSkill(
                job_id=job.id,
                skill_name=s,
                is_required=False,
                category=cat,
            ))

        created += 1

    await db.commit()
    logger.info("Successfully seeded %d synthetic benchmark jobs.", created)
    return created
