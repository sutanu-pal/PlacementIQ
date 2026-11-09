from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiFeedbackSchema(BaseModel):
    summary: str = Field(..., description="High-level evaluation of resume effectiveness")
    strengths: List[str] = Field(default_factory=list, description="Key resume strengths")
    actionable_tips: List[str] = Field(default_factory=list, description="Specific actions to improve impact")
    ats_recommendations: List[str] = Field(default_factory=list, description="Suggestions for ATS alignment")
    formatting_advice: List[str] = Field(default_factory=list, description="Layout and visual clarity suggestions")


class GeminiResumeAdvisor:
    """Provides AI-powered resume review using Gemini with graceful fallback."""

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    @classmethod
    def sanitize_for_llm(cls, raw_text: str) -> str:
        """Strip sensitive contact details (PII) before sending to external LLM."""
        sanitized = re.sub(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "[CANDIDATE_EMAIL_REDACTED]",
            raw_text,
        )
        sanitized = re.sub(
            r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{4})",
            "[CANDIDATE_PHONE_REDACTED]",
            sanitized,
        )
        return sanitized[:4000]  # Cap length for prompt hygiene

    @classmethod
    async def generate_feedback(
        cls,
        parsed_data: Dict[str, Any],
        extracted_skills: List[Dict[str, str]],
        score_data: Dict[str, Any],
        raw_text: str,
    ) -> Dict[str, Any]:
        """
        Request AI feedback from Gemini or provide high-quality deterministic fallback.
        """
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

        if not api_key:
            logger.info("No GEMINI_API_KEY configured; employing deterministic placement advisor.")
            return cls._build_deterministic_fallback(parsed_data, extracted_skills, score_data)

        sanitized_resume = cls.sanitize_for_llm(raw_text)
        skill_names = [s["name"] for s in extracted_skills]

        prompt = f"""
You are an expert technical recruiter and resume reviewer for engineering campus placements.
Analyze the following candidate resume profile and output an honest, constructive critique in JSON format.

Candidate Skills Extracted: {', '.join(skill_names[:25])}
Computed Structural Score: {score_data.get('overall_score')}/100
Detected Sections: {', '.join(parsed_data.get('detected_sections', []))}

Sanitized Resume Excerpt:
{sanitized_resume}

Output MUST be a JSON object with this EXACT structure:
{{
  "summary": "1-2 sentence executive summary of candidate positioning",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "actionable_tips": ["specific tip 1", "specific tip 2", "specific tip 3"],
  "ats_recommendations": ["ats tip 1", "ats tip 2"],
  "formatting_advice": ["formatting tip 1"]
}}
"""

        endpoint = cls.GEMINI_API_URL.format(model=settings.GEMINI_MODEL)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "response_mime_type": "application/json",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    endpoint,
                    params={"key": api_key},
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_resp = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed_json = cls._extract_json(text_resp)
                        if parsed_json:
                            # Validate with Pydantic
                            validated = GeminiFeedbackSchema(**parsed_json)
                            feedback_dict = validated.model_dump()
                            feedback_dict["is_ai_generated"] = True
                            feedback_dict["model"] = settings.GEMINI_MODEL
                            return feedback_dict
                else:
                    logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:200]}")

        except Exception as exc:
            logger.warning(f"Gemini API error during resume analysis: {exc}")

        # Fallback when API call fails
        return cls._build_deterministic_fallback(parsed_data, extracted_skills, score_data)

    @classmethod
    def _extract_json(cls, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            # Try to match ```json ... ``` block
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

    @classmethod
    def _build_deterministic_fallback(
        cls,
        parsed_data: Dict[str, Any],
        extracted_skills: List[Dict[str, str]],
        score_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Provides rich, deterministic recommendations when LLM is unavailable."""
        overall = score_data.get("overall_score", 0)
        skill_count = len(extracted_skills)
        projects = parsed_data.get("projects", [])
        experience = parsed_data.get("experience", [])

        if overall >= 80:
            summary = "Well-balanced candidate resume with strong technical coverage and structured presentation."
        elif overall >= 60:
            summary = "Competent foundational engineering resume; key improvements needed in quantifiable project metrics and technical diversity."
        else:
            summary = "Resume needs structural refinement and explicit project deliverables to pass campus placement ATS filters."

        actionable_tips: List[str] = []
        if len(projects) < 2:
            actionable_tips.append("Add at least two end-to-end projects featuring frontend, backend, and database integration.")
        else:
            actionable_tips.append("Quantify project impact using metrics (e.g. 'reduced latency by 35%', 'processed 10k records').")

        if not experience or not experience[0].get("title"):
            actionable_tips.append("Highlight academic research, technical club leadership, or open-source PRs under practical experience.")
        else:
            actionable_tips.append("Structure experience bullet points with the XYZ formula: 'Accomplished [X] as measured by [Y] by doing [Z]'.")

        if skill_count < 8:
            actionable_tips.append("Categorize technical skills into Languages, Frameworks, Databases, and Developer Tools.")

        ats_recommendations = [
            "Use standard section headers (Education, Technical Skills, Projects, Experience) to ensure ATS parsers recognize them.",
            "Avoid multi-column tables and text boxes which frequently cause reading order inversion in recruitment parsers.",
            "Include technical keywords relevant to target job roles in both your Skills and Project descriptions.",
        ]

        formatting_advice = [
            "Keep layout to 1 page for undergraduate applicants unless you possess extensive industry internships.",
            "Ensure consistent date formatting (e.g., 'May 2025 - Jul 2025') across all experience and project entries.",
        ]

        return {
            "summary": summary,
            "strengths": score_data.get("strengths", ["Solid technical foundation."]),
            "actionable_tips": actionable_tips,
            "ats_recommendations": ats_recommendations,
            "formatting_advice": formatting_advice,
            "is_ai_generated": False,
            "model": "PlacementIQ Rule-Based Advisor (Deterministic Fallback)",
        }
