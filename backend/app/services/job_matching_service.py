from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set
from app.ai.embedding_service import embedding_service
from app.ai.skill_extractor import skill_extractor
from app.models.job import Job
from app.models.resume import Resume

logger = logging.getLogger(__name__)


class JobMatchingService:
    """
    Explainable Semantic Job Matching Engine for PlacementIQ.

    Formula:
      Match Score = 50% Skill Coverage + 30% Semantic Similarity + 20% Project Relevance

    Weights and scoring criteria are transparent and deterministic.
    Evaluates required vs preferred skills separately, giving 70% weight to required skills.
    Semantic similarity is computed using dense SentenceTransformer embeddings (all-MiniLM-L6-v2).
    Project relevance evaluates candidate project descriptions against role responsibilities.
    """

    SKILL_WEIGHT = 0.50
    SEMANTIC_WEIGHT = 0.30
    PROJECT_WEIGHT = 0.20

    REQUIRED_SKILL_SUBWEIGHT = 0.70
    PREFERRED_SKILL_SUBWEIGHT = 0.30

    ALGORITHM_VERSION = "v1.0-explainable-nlp"

    def match_resume_to_job(
        self,
        resume: Resume,
        job: Job,
    ) -> Dict[str, Any]:
        """
        Execute explainable matching between a candidate resume and a job description.
        Returns complete score breakdown, matched/missing skills, project relevance,
        and human-readable explanations.
        """
        # 1. Normalize Candidate Skills
        candidate_skills_dict = resume.extracted_skills or []
        candidate_skill_names: Set[str] = {
            s["name"].lower().strip() for s in candidate_skills_dict if isinstance(s, dict) and "name" in s
        }

        # Also extract skills directly from raw_text to ensure complete taxonomy coverage
        if resume.raw_text:
            text_extracted = skill_extractor.extract_skills(resume.raw_text)
            for item in text_extracted:
                candidate_skill_names.add(item["name"].lower().strip())

        # 2. Skill Coverage Scoring
        job_req_skills = job.required_skills or []
        job_pref_skills = job.preferred_skills or []

        matched_req: List[str] = []
        missing_req: List[str] = []
        for req in job_req_skills:
            if self._is_skill_present(req, candidate_skill_names):
                matched_req.append(req)
            else:
                missing_req.append(req)

        matched_pref: List[str] = []
        missing_pref: List[str] = []
        for pref in job_pref_skills:
            if self._is_skill_present(pref, candidate_skill_names):
                matched_pref.append(pref)
            else:
                missing_pref.append(pref)

        matched_all = matched_req + matched_pref

        # Calculate coverage percentages
        req_coverage_pct = (len(matched_req) / len(job_req_skills) * 100.0) if job_req_skills else 100.0
        pref_coverage_pct = (len(matched_pref) / len(job_pref_skills) * 100.0) if job_pref_skills else 100.0

        if job_req_skills and job_pref_skills:
            skill_score = (
                self.REQUIRED_SKILL_SUBWEIGHT * req_coverage_pct
                + self.PREFERRED_SKILL_SUBWEIGHT * pref_coverage_pct
            )
        elif job_req_skills:
            skill_score = req_coverage_pct
        elif job_pref_skills:
            skill_score = pref_coverage_pct
        else:
            skill_score = 100.0

        skill_score = round(max(0.0, min(100.0, skill_score)), 1)

        # 3. Semantic Similarity via Sentence Transformers
        job_text = self._build_job_text(job)
        job_embedding = job.embedding
        if not job_embedding or len(job_embedding) != 384:
            job_embedding = embedding_service.encode_text(job_text)
            job.embedding = job_embedding  # Cache for future matches

        resume_text = self._build_resume_text(resume)
        resume_embedding = embedding_service.encode_text(resume_text)

        raw_similarity = embedding_service.cosine_similarity(resume_embedding, job_embedding)
        semantic_score = round(max(0.0, min(100.0, raw_similarity * 100.0)), 1)

        # 4. Project Relevance Scoring
        parsed_data = resume.parsed_data or {}
        projects = parsed_data.get("projects", [])
        project_result = self._evaluate_project_relevance(projects, job)
        project_score = project_result["score"]

        # 5. Total Explainable Match Score
        total_match_score = (
            self.SKILL_WEIGHT * skill_score
            + self.SEMANTIC_WEIGHT * semantic_score
            + self.PROJECT_WEIGHT * project_score
        )
        total_match_score = round(max(0.0, min(100.0, total_match_score)), 1)

        # 6. Explanations & Recommendations
        explanations = self._generate_explanations(
            job=job,
            skill_score=skill_score,
            semantic_score=semantic_score,
            project_score=project_score,
            matched_req=matched_req,
            missing_req=missing_req,
            matched_pref=matched_pref,
            missing_pref=missing_pref,
            project_count=len(projects),
            top_project_title=project_result.get("top_project_title"),
        )

        recommendations = self._generate_recommendations(
            missing_req=missing_req,
            missing_pref=missing_pref,
            project_score=project_score,
            projects=projects,
        )

        score_breakdown = {
            "formula": "50% Skill Coverage + 30% Semantic Similarity + 20% Project Relevance",
            "weights": {
                "skill_coverage": self.SKILL_WEIGHT,
                "semantic_similarity": self.SEMANTIC_WEIGHT,
                "project_relevance": self.PROJECT_WEIGHT,
            },
            "skill_subweights": {
                "required_skills": self.REQUIRED_SKILL_SUBWEIGHT if job_pref_skills else 1.0,
                "preferred_skills": self.PREFERRED_SKILL_SUBWEIGHT if job_req_skills else 1.0,
            },
            "required_skills_count": len(job_req_skills),
            "required_matched_count": len(matched_req),
            "required_coverage_pct": round(req_coverage_pct, 1),
            "preferred_skills_count": len(job_pref_skills),
            "preferred_matched_count": len(matched_pref),
            "preferred_coverage_pct": round(pref_coverage_pct, 1),
            "raw_cosine_similarity": round(raw_similarity, 4),
            "projects_analyzed": len(projects),
        }

        return {
            "match_score": total_match_score,
            "skill_score": skill_score,
            "semantic_score": semantic_score,
            "project_score": project_score,
            "matched_skills": matched_all,
            "missing_required_skills": missing_req,
            "missing_preferred_skills": missing_pref,
            "project_relevance": project_result,
            "score_breakdown": score_breakdown,
            "explanations": explanations,
            "recommendations": recommendations,
            "algorithm_version": self.ALGORITHM_VERSION,
            "disclaimer": (
                "PlacementIQ match score evaluates algorithmic alignment between resume contents "
                "and job requirements. It is an educational indicator and not a recruitment selection guarantee."
            ),
        }

    @staticmethod
    def _is_skill_present(skill: str, candidate_skills: Set[str]) -> bool:
        """Case-insensitive and alias-aware skill presence check."""
        s_clean = skill.lower().strip()
        if s_clean in candidate_skills:
            return True

        # Check substring boundary match (e.g. "React.js" matches "React")
        for c in candidate_skills:
            if s_clean in c or c in s_clean:
                # Disallow trivial false positives (e.g. "c" in "docker")
                if len(s_clean) >= 3 and len(c) >= 3:
                    return True
        return False

    @staticmethod
    def _build_job_text(job: Job) -> str:
        parts = [
            f"Job Title: {job.title}",
            f"Company: {job.company}",
            f"Experience Level: {job.experience_level}",
            f"Description: {job.description}",
        ]
        if job.responsibilities:
            parts.append("Responsibilities: " + " ".join(job.responsibilities))
        if job.required_skills:
            parts.append("Required Skills: " + ", ".join(job.required_skills))
        if job.preferred_skills:
            parts.append("Preferred Skills: " + ", ".join(job.preferred_skills))
        return " ".join(parts)

    @staticmethod
    def _build_resume_text(resume: Resume) -> str:
        if resume.raw_text and len(resume.raw_text.strip()) > 50:
            return resume.raw_text

        parts = []
        parsed = resume.parsed_data or {}
        if parsed.get("experience"):
            parts.append(str(parsed["experience"]))
        if parsed.get("projects"):
            parts.append(str(parsed["projects"]))
        if resume.extracted_skills:
            skills = [s.get("name", "") for s in resume.extracted_skills if isinstance(s, dict)]
            parts.append("Skills: " + ", ".join(skills))
        return " ".join(parts)

    def _evaluate_project_relevance(
        self,
        projects: List[Any],
        job: Job,
    ) -> Dict[str, Any]:
        """
        Evaluate candidate projects against job responsibilities and technical context.
        """
        if not projects:
            return {
                "score": 25.0,
                "project_count": 0,
                "top_project_title": None,
                "top_project_similarity": 0.0,
                "details": [],
                "summary": "No technical projects were detected on the resume to evaluate against job requirements.",
            }

        job_resp_text = (
            " ".join(job.responsibilities) if job.responsibilities else job.description
        )
        job_resp_emb = embedding_service.encode_text(job_resp_text)

        project_details = []
        top_sim = 0.0
        top_title = "Project"

        for proj in projects:
            if isinstance(proj, dict):
                title = proj.get("title", "Project")
                desc = proj.get("description", "")
                techs = proj.get("technologies", [])
                text = f"{title}. {desc}. Technologies: {', '.join(techs) if isinstance(techs, list) else str(techs)}"
            else:
                title = str(proj)[:40]
                text = str(proj)

            proj_emb = embedding_service.encode_text(text)
            sim = embedding_service.cosine_similarity(proj_emb, job_resp_emb)

            if sim > top_sim:
                top_sim = sim
                top_title = title

            project_details.append({
                "title": title,
                "relevance_similarity": round(sim, 3),
            })

        # Calculate project score:
        # Base from highest similarity project (scaled 0-80) + bonus for project breadth (up to 20)
        base_score = top_sim * 80.0
        breadth_bonus = min(20.0, len(projects) * 10.0)  # 1 project = +10, 2+ projects = +20
        project_score = round(max(30.0, min(100.0, base_score + breadth_bonus)), 1)

        return {
            "score": project_score,
            "project_count": len(projects),
            "top_project_title": top_title,
            "top_project_similarity": round(top_sim, 3),
            "details": project_details,
            "summary": (
                f"{len(projects)} projects evaluated. Top project '{top_title}' showed "
                f"{round(top_sim * 100, 1)}% contextual alignment with job responsibilities."
            ),
        }

    @staticmethod
    def _generate_explanations(
        job: Job,
        skill_score: float,
        semantic_score: float,
        project_score: float,
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str],
        missing_pref: List[str],
        project_count: int,
        top_project_title: Optional[str],
    ) -> List[str]:
        explanations = []

        # Skill explanation
        total_req = len(matched_req) + len(missing_req)
        if total_req > 0:
            explanations.append(
                f"Skill Coverage ({skill_score}%): Matched {len(matched_req)} of {total_req} mandatory skills. "
                + (f"Missing: {', '.join(missing_req[:3])}." if missing_req else "All required skills verified!")
            )
        else:
            explanations.append(f"Skill Coverage ({skill_score}%): Role does not list mandatory hard prerequisites.")

        total_pref = len(matched_pref) + len(missing_pref)
        if total_pref > 0:
            explanations.append(
                f"Preferred Skills: Matched {len(matched_pref)} of {total_pref} optional/preferred qualifications."
            )

        # Semantic explanation
        align_desc = (
            "strong" if semantic_score >= 75
            else "moderate" if semantic_score >= 50
            else "developing"
        )
        explanations.append(
            f"Semantic Relevance ({semantic_score}%): Textual profile shows {align_desc} semantic alignment "
            f"with '{job.title}' requirements."
        )

        # Project explanation
        if project_count > 0:
            explanations.append(
                f"Project Relevance ({project_score}%): {project_count} project(s) reviewed. "
                f"Primary project '{top_project_title or 'Main Project'}' demonstrates applicable hands-on engineering."
            )
        else:
            explanations.append(
                f"Project Relevance ({project_score}%): No distinct project records found. "
                "Adding practical projects will significantly improve this score."
            )

        return explanations

    @staticmethod
    def _generate_recommendations(
        missing_req: List[str],
        missing_pref: List[str],
        project_score: float,
        projects: List[Any],
    ) -> List[str]:
        recommendations = []

        if missing_req:
            top_missing = ", ".join(missing_req[:4])
            recommendations.append(
                f"Prioritize acquiring mandatory skills: {top_missing}. "
                "These are core prerequisites for candidate shortlisting."
            )

        if missing_pref:
            top_pref = ", ".join(missing_pref[:3])
            recommendations.append(
                f"Consider adding preferred proficiencies: {top_pref} to outrank competitive applicants."
            )

        if project_score < 60.0 or not projects:
            recommendations.append(
                "Develop and document at least one full-lifecycle project demonstrating the target tech stack "
                "with measurable metrics (e.g. latency reduction, test coverage, user volume)."
            )
        else:
            recommendations.append(
                "Refine project descriptions using the STAR format (Situation, Task, Action, Result) to highlight "
                "engineering decisions and production impact."
            )

        return recommendations


# Reusable global instance
job_matching_service = JobMatchingService()
