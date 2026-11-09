from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dsa import DsaQuestion

logger = logging.getLogger(__name__)


async def seed_dsa_questions(db: AsyncSession) -> int:
    """
    Seed standard DSA curriculum questions if dsa_questions table is empty.
    Returns number of questions seeded.
    """
    result = await db.execute(select(func.count(DsaQuestion.id)))
    count = result.scalar_one_or_none() or 0
    if count > 0:
        return 0

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    json_path = os.path.join(base_dir, "data", "dsa_questions.json")

    if not os.path.exists(json_path):
        logger.warning("dsa_questions.json not found at %s", json_path)
        return 0

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            questions: List[Dict[str, Any]] = json.load(f)
    except Exception as exc:
        logger.error("Failed to parse dsa_questions.json: %s", exc)
        return 0

    created = 0
    for q in questions:
        question = DsaQuestion(
            title=q["title"],
            slug=q["slug"],
            category=q["category"],
            difficulty=q["difficulty"],
            description=q["description"],
            constraints=q.get("constraints", []),
            examples=q.get("examples", []),
            starter_code=q.get("starter_code", {}),
            test_cases=q.get("test_cases", []),
            time_limit_ms=q.get("time_limit_ms", 2000),
            memory_limit_mb=q.get("memory_limit_mb", 128),
            is_active=True,
        )
        db.add(question)
        created += 1

    await db.commit()
    logger.info("Successfully seeded %d DSA coding questions.", created)
    return created
