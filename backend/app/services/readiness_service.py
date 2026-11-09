from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dsa import DsaQuestion, DsaSubmission
from app.models.interview import InterviewSession
from app.models.job import JobMatch
from app.models.readiness import PlacementReadinessSnapshot
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.models.user import User

logger = logging.getLogger(__name__)


class PlacementReadinessEngine:
    """
    Central Explainable Placement Readiness Engine connecting all 5 modules.
    
    Dimensions & Standard Weights:
    - Resume Quality: 25% (Module 1)
    - Job Compatibility: 25% (Module 2)
    - DSA Proficiency: 25% (Module 3)
    - Interview Performance: 15% (Module 4)
    - Learning Progress: 10% (Module 5)
    
    Integrity Rules:
    - Never fabricates scores for incomplete modules.
    - Computes both Provisional Score (normalized over available dimensions) and
      Overall Benchmark Score (strictly evaluating all 5 dimensions).
    - Explains exactly how each dimension was scored and how to unlock missing dimensions.
    """

    DIMENSION_WEIGHTS = {
        "resume_quality": 0.25,
        "job_compatibility": 0.25,
        "dsa_performance": 0.25,
        "interview_performance": 0.15,
        "learning_progress": 0.10,
    }

    async def calculate_readiness(
        self,
        db: AsyncSession,
        user: User,
        save_snapshot: bool = True,
    ) -> Dict[str, Any]:
        dim_data: Dict[str, Any] = {}
        strengths: List[str] = []
        weaknesses: List[str] = []
        recommendations: List[str] = []

        # ── 1. Resume Quality Dimension (25%) ──
        res_stmt = (
            select(Resume)
            .where(Resume.user_id == user.id, Resume.status == "analyzed")
            .order_by(desc(Resume.version))
            .limit(1)
        )
        latest_resume = (await db.execute(res_stmt)).scalar_one_or_none()
        if latest_resume and latest_resume.overall_score > 0:
            r_score = float(latest_resume.overall_score)
            dim_data["resume_quality"] = {
                "score": r_score,
                "weight": self.DIMENSION_WEIGHTS["resume_quality"],
                "available": True,
                "status_message": f"Evaluated from Resume v{latest_resume.version}",
                "metric_summary": f"ATS Score: {r_score}%, {len(latest_resume.extracted_skills or [])} skills verified",
            }
            if r_score >= 75:
                strengths.append(f"Strong resume foundation ({r_score}%) with comprehensive section structure.")
            else:
                weaknesses.append(f"Resume ATS score ({r_score}%) is below competitive 75% placement benchmark.")
                recommendations.append("Enhance resume project bullet points with metrics and add missing technical skill categories.")
        else:
            dim_data["resume_quality"] = {
                "score": 0.0,
                "weight": self.DIMENSION_WEIGHTS["resume_quality"],
                "available": False,
                "status_message": "No analyzed resume uploaded yet.",
                "metric_summary": "Upload and analyze your resume in Module 1 to unlock this dimension.",
            }
            weaknesses.append("Resume quality dimension is inactive.")
            recommendations.append("Upload your PDF resume in the Resume Analyzer to establish baseline ATS scoring.")

        # ── 2. Job Compatibility Dimension (25%) ──
        match_stmt = (
            select(JobMatch)
            .where(JobMatch.user_id == user.id)
            .order_by(desc(JobMatch.match_score))
            .limit(1)
        )
        best_match = (await db.execute(match_stmt)).scalar_one_or_none()
        if best_match and best_match.match_score > 0:
            j_score = float(best_match.match_score)
            dim_data["job_compatibility"] = {
                "score": j_score,
                "weight": self.DIMENSION_WEIGHTS["job_compatibility"],
                "available": True,
                "status_message": f"Best match score from target role evaluations",
                "metric_summary": f"Role Match: {j_score}%, Skill Score: {best_match.skill_score}%",
            }
            if j_score >= 75:
                strengths.append(f"High semantic and skill alignment ({j_score}%) with target roles.")
            else:
                weaknesses.append(f"Job match compatibility ({j_score}%) has missing prerequisite skills.")
                recommendations.append("Target required skills identified in job matches to boost compatibility.")
        else:
            dim_data["job_compatibility"] = {
                "score": 0.0,
                "weight": self.DIMENSION_WEIGHTS["job_compatibility"],
                "available": False,
                "status_message": "No job match evaluation executed yet.",
                "metric_summary": "Run a match against an active job opening in Module 2 to activate.",
            }
            weaknesses.append("Job compatibility dimension is inactive.")
            recommendations.append("Run at least one job matching evaluation against a target role.")

        # ── 3. DSA Performance Dimension (25%) ──
        q_count = (await db.execute(select(func.count(DsaQuestion.id)).where(DsaQuestion.is_active == True))).scalar_one_or_none() or 1
        dsa_subs = (await db.execute(select(DsaSubmission).where(DsaSubmission.user_id == user.id))).scalars().all()
        solved_ids = {s.question_id for s in dsa_subs if s.status == "Accepted"}

        if dsa_subs:
            total_subs = len(dsa_subs)
            acc = (len([s for s in dsa_subs if s.status == "Accepted"]) / total_subs) * 100.0
            solved_ratio = (len(solved_ids) / q_count) * 100.0
            # DSA score: 65% based on solved coverage + 35% based on accuracy
            dsa_score = round(min(100.0, (0.65 * min(100.0, solved_ratio * 2.0)) + (0.35 * acc)), 1)
            dim_data["dsa_performance"] = {
                "score": dsa_score,
                "weight": self.DIMENSION_WEIGHTS["dsa_performance"],
                "available": True,
                "status_message": f"Evaluated from {len(solved_ids)} solved problems",
                "metric_summary": f"{len(solved_ids)}/{q_count} solved, {round(acc, 1)}% submission accuracy",
            }
            if dsa_score >= 70:
                strengths.append(f"Strong algorithmic problem-solving accuracy ({dsa_score}%).")
            else:
                weaknesses.append(f"DSA problem solving coverage ({len(solved_ids)} solved) needs expansion.")
                recommendations.append("Solve foundational Easy and Medium problems in Dynamic Programming and Trees.")
        else:
            dim_data["dsa_performance"] = {
                "score": 0.0,
                "weight": self.DIMENSION_WEIGHTS["dsa_performance"],
                "available": False,
                "status_message": "No DSA submissions found.",
                "metric_summary": "Solve coding problems in Module 3 to unlock this dimension.",
            }
            weaknesses.append("DSA performance dimension is inactive.")
            recommendations.append("Attempt coding assessments in the DSA Assessment Engine.")

        # ── 4. Interview Performance Dimension (15%) ──
        int_stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user.id, InterviewSession.status == "completed")
            .order_by(desc(InterviewSession.overall_score))
            .limit(1)
        )
        best_interview = (await db.execute(int_stmt)).scalar_one_or_none()
        if best_interview and best_interview.overall_score > 0:
            i_score = float(best_interview.overall_score)
            dim_data["interview_performance"] = {
                "score": i_score,
                "weight": self.DIMENSION_WEIGHTS["interview_performance"],
                "available": True,
                "status_message": f"Best score from {best_interview.role_title} ({best_interview.interview_type})",
                "metric_summary": f"Technical: {best_interview.technical_score}%, Communication: {best_interview.communication_score}%",
            }
            if i_score >= 75:
                strengths.append(f"Solid mock interview articulation and technical depth ({i_score}%).")
            else:
                weaknesses.append(f"Interview response rating ({i_score}%) indicates need for structured articulation.")
                recommendations.append("Practice STAR method responses in the AI Mock Interview simulator.")
        else:
            dim_data["interview_performance"] = {
                "score": 0.0,
                "weight": self.DIMENSION_WEIGHTS["interview_performance"],
                "available": False,
                "status_message": "No completed mock interviews found.",
                "metric_summary": "Complete a mock interview in Module 4 to unlock this dimension.",
            }
            weaknesses.append("Interview performance dimension is inactive.")
            recommendations.append("Attend an AI mock interview session to evaluate communication and depth.")

        # ── 5. Learning Progress Dimension (10%) ──
        road_stmt = (
            select(Roadmap)
            .where(Roadmap.user_id == user.id)
            .order_by(desc(Roadmap.created_at))
            .limit(1)
        )
        latest_roadmap = (await db.execute(road_stmt)).scalar_one_or_none()
        if latest_roadmap:
            l_score = float(latest_roadmap.completion_pct)
            dim_data["learning_progress"] = {
                "score": l_score,
                "weight": self.DIMENSION_WEIGHTS["learning_progress"],
                "available": True,
                "status_message": f"Milestone progress for {latest_roadmap.target_role}",
                "metric_summary": f"{l_score}% tasks completed, {latest_roadmap.current_streak_days}-day streak",
            }
            if l_score >= 50:
                strengths.append(f"Consistent learning progress ({l_score}% roadmap completion).")
            else:
                recommendations.append("Check off weekly milestone learning tasks to raise your learning score.")
        else:
            dim_data["learning_progress"] = {
                "score": 0.0,
                "weight": self.DIMENSION_WEIGHTS["learning_progress"],
                "available": False,
                "status_message": "No active roadmap initialized.",
                "metric_summary": "Generate a personalized roadmap in Module 5 to activate.",
            }

        # ── Calculate Composite Scores ──
        available_dims = [k for k, v in dim_data.items() if v["available"]]
        evaluated_count = len(available_dims)

        if evaluated_count > 0:
            sum_available_weights = sum(self.DIMENSION_WEIGHTS[k] for k in available_dims)
            provisional_score = round(
                sum(dim_data[k]["score"] * self.DIMENSION_WEIGHTS[k] for k in available_dims) / sum_available_weights,
                1,
            )
        else:
            provisional_score = 0.0

        overall_score = round(
            sum(dim_data[k]["score"] * self.DIMENSION_WEIGHTS[k] for k in dim_data.keys()),
            1,
        )

        # Determine Tier
        if evaluated_count >= 4 and overall_score >= 75:
            tier = "Placement Ready (Tier 1 Benchmark)"
        elif evaluated_count >= 3 and provisional_score >= 65:
            tier = "Approaching Benchmark (Competitive)"
        elif evaluated_count >= 2 and provisional_score >= 50:
            tier = "Developing Baseline"
        else:
            tier = "Needs Foundational Preparation"

        breakdown_list = [
            {
                "dimension": k.replace("_", " ").title(),
                "key": k,
                "score": v["score"],
                "normalized_score": v["score"],
                "weight": v["weight"],
                "available": v["available"],
                "status": v["status_message"],
                "metric_summary": v["metric_summary"],
            }
            for k, v in dim_data.items()
        ]

        result = {
            "overall_score": overall_score,
            "provisional_score": provisional_score,
            "evaluated_dimensions_count": evaluated_count,
            "total_dimensions_count": 5,
            "readiness_tier": tier,
            "dimension_scores": dim_data,
            "breakdown": breakdown_list,
            "strengths": strengths[:4],
            "weaknesses": weaknesses[:4],
            "recommendations": recommendations[:4],
            "actionable_recommendations": recommendations[:4],
            "formula_documentation": (
                "Placement Readiness Score = 25% Resume Quality + 25% Job Compatibility + "
                "25% DSA Performance + 15% Mock Interview + 10% Learning Roadmap Progress."
            ),
            "disclaimer": (
                "Placement Readiness Score is an analytical composite indicator developed for internal major project "
                "academic benchmarking. It does not predict or guarantee recruitment selection by external employers."
            ),
        }

        if save_snapshot:
            snapshot = PlacementReadinessSnapshot(
                user_id=user.id,
                overall_score=overall_score,
                provisional_score=provisional_score,
                evaluated_dimensions_count=evaluated_count,
                total_dimensions_count=5,
                dimension_scores=dim_data,
                strengths=result["strengths"],
                weaknesses=result["weaknesses"],
                recommendations=result["recommendations"],
                readiness_tier=tier,
            )
            db.add(snapshot)
            await db.commit()

        return result


readiness_engine = PlacementReadinessEngine()
