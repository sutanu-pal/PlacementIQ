from __future__ import annotations

import hashlib
import os
import uuid
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.skill_extractor import get_skill_extractor
from app.config import get_settings
from app.models.resume import Resume
from app.services.gemini_service import GeminiResumeAdvisor
from app.services.pdf_parser import PDFParserError, ResumePDFParser
from app.services.resume_scorer import ResumeScorer

settings = get_settings()


class ResumeService:
    """Manages secure PDF storage, parsing, scoring, and lifecycle."""

    @classmethod
    async def process_and_save_resume(
        cls,
        db: AsyncSession,
        user_id: str,
        upload_file: UploadFile,
    ) -> Resume:
        """
        Validate, parse, extract skills, score, and persist a new resume version.
        """
        # 1. Basic validation
        orig_filename = upload_file.filename or "resume.pdf"
        if not orig_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF documents (.pdf) are supported.",
            )

        # 2. Read bytes with size restriction
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        content = await upload_file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            )

        # 3. Magic bytes inspection
        if not ResumePDFParser.validate_pdf_bytes(content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file format. Header signature missing.",
            )

        # 4. Compute file hash
        file_hash = hashlib.sha256(content).hexdigest()

        # 5. Extract text via PyMuPDF
        try:
            raw_text, page_count, is_scanned = ResumePDFParser.extract_text(content)
        except PDFParserError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            ) from err

        # 6. Parse sections & extract skills
        parsed_data = ResumePDFParser.parse_sections(raw_text)
        skill_extractor = get_skill_extractor()
        extracted_skills = skill_extractor.extract_skills(raw_text)

        # 7. Deterministic Scoring
        score_data = ResumeScorer.score_resume(parsed_data, extracted_skills, raw_text)

        # 8. AI Recommendations (with graceful fallback)
        ai_feedback = await GeminiResumeAdvisor.generate_feedback(
            parsed_data=parsed_data,
            extracted_skills=extracted_skills,
            score_data=score_data,
            raw_text=raw_text,
        )

        # 9. Determine version number for this student
        stmt_ver = select(func.coalesce(func.max(Resume.version), 0)).where(Resume.user_id == user_id)
        current_max_ver = (await db.execute(stmt_ver)).scalar_one()
        next_version = current_max_ver + 1

        # 10. Store file privately outside static web directories
        user_upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes", user_id)
        os.makedirs(user_upload_dir, exist_ok=True)

        stored_filename = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(user_upload_dir, stored_filename)

        with open(file_path, "wb") as f:
            f.write(content)

        # 11. Create DB Record
        resume_record = Resume(
            user_id=user_id,
            filename=orig_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=file_size,
            file_hash=file_hash,
            version=next_version,
            status="analyzed",
            raw_text=raw_text,
            page_count=page_count,
            is_scanned=is_scanned,
            parsed_data=parsed_data,
            extracted_skills=extracted_skills,
            overall_score=score_data["overall_score"],
            score_breakdown=score_data["score_breakdown"],
            strengths=score_data["strengths"],
            improvement_areas=score_data["improvement_areas"],
            ai_feedback=ai_feedback,
        )

        db.add(resume_record)
        await db.commit()
        await db.refresh(resume_record)

        return resume_record

    @classmethod
    async def list_user_resumes(cls, db: AsyncSession, user_id: str) -> List[Resume]:
        """Fetch all resume versions belonging to the user."""
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(desc(Resume.version))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_user_resume(cls, db: AsyncSession, user_id: str, resume_id: str) -> Resume:
        """Fetch specific resume ensuring strict user ownership."""
        stmt = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        if resume.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not own this resume.",
            )

        return resume

    @classmethod
    async def delete_user_resume(cls, db: AsyncSession, user_id: str, resume_id: str) -> None:
        """Delete resume record and remove physical file from disk."""
        resume = await cls.get_user_resume(db, user_id, resume_id)

        # Remove physical file if it exists
        if resume.file_path and os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
            except OSError:
                pass

        await db.delete(resume)
        await db.commit()
