from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
from app.config import get_settings
from app.models.interview import InterviewMessage, InterviewSession

logger = logging.getLogger(__name__)
settings = get_settings()


class InterviewService:
    """
    AI Mock Interview Simulation Engine.
    
    Provides:
    1. Personalized interview question generation (Technical, Behavioral, System Design).
    2. Adaptive follow-up questioning based on previous candidate answers.
    3. Structured multi-dimensional rubric evaluation:
       - Communication clarity & structure (STAR method for behavioral)
       - Technical accuracy & depth
       - Problem solving & edge-case handling
       - Role & context relevance
    4. Deterministic fallback evaluator when Gemini is offline or unconfigured.
    """

    ROLE_QUESTION_BANKS = {
        "Technical": {
            "Backend": [
                "Can you walk me through how you design high-throughput REST APIs and handle relational database connection pooling and transaction rollbacks?",
                "How do you approach caching in distributed systems using Redis or Memcached? What cache invalidation strategies do you employ?",
                "Explain the trade-offs between asynchronous event-driven architecture (e.g. RabbitMQ/Kafka) versus synchronous HTTP microservices.",
                "How would you diagnose and resolve a slow SQL query in a production PostgreSQL database that handles millions of records?",
            ],
            "Frontend": [
                "Explain how React's reconciliation algorithm and virtual DOM work. When would you use useMemo, useCallback, or React.memo?",
                "How do you optimize Core Web Vitals (LCP, FID, CLS) in a modern single-page web application?",
                "How do you manage complex client-side state across deeply nested components? Compare Context API with Redux or Zustand.",
                "How do you handle accessible form validation, error states, and asynchronous race conditions in React?",
            ],
            "AI/ML": [
                "How do you evaluate and prevent overfitting in deep learning models? Compare dropout, regularization, and data augmentation.",
                "Explain how dense text embeddings like SentenceTransformers work compared to traditional TF-IDF or BM25 bag-of-words.",
                "Walk me through the lifecycle of deploying a machine learning model as a real-time low-latency REST inference service.",
                "How do you handle concept drift and data distribution shifts in production ML monitoring?",
            ],
            "Default": [
                "Can you describe the architectural design of your most complex technical project and the core engineering trade-offs you made?",
                "How do you ensure code maintainability, error handling, and unit test coverage in your development workflow?",
                "Explain how you approach debugging an intermittent or concurrency-related bug in production.",
                "What principles do you follow when designing scalable, modular software systems?",
            ],
        },
        "Behavioral": {
            "Default": [
                "Tell me about a time when you faced a critical technical challenge or roadblock during a project. How did you resolve it?",
                "Describe a situation where you had a disagreement with a team member regarding an engineering decision. How did you handle it?",
                "Tell me about a time when you had to learn a new framework or technology under tight deadline constraints.",
                "Give an example of a project where requirements changed midway. How did you adapt your plan and communicate with stakeholders?",
            ]
        },
        "System Design": {
            "Default": [
                "How would you design a scalable URL shortener service (like TinyURL) handling 100M daily active requests?",
                "Design a real-time collaborative document editing platform (like Google Docs). How would you handle conflict resolution?",
                "How would you architect a notification service supporting email, SMS, and in-app push alerts with guaranteed delivery?",
                "Design a rate-limiter microservice protecting downstream APIs against denial-of-service spikes.",
            ]
        },
    }

    def generate_opening_question(
        self,
        role_title: str,
        interview_type: str,
        candidate_skills: List[str],
        candidate_projects: List[Dict[str, Any]],
    ) -> str:
        """Generate tailored opening question based on role, type, and resume projects."""
        role_lower = role_title.lower()
        sub_bank = "Default"
        if "backend" in role_lower or "python" in role_lower or "api" in role_lower:
            sub_bank = "Backend"
        elif "frontend" in role_lower or "react" in role_lower or "web" in role_lower:
            sub_bank = "Frontend"
        elif "ai" in role_lower or "ml" in role_lower or "data" in role_lower:
            sub_bank = "AI/ML"

        questions = self.ROLE_QUESTION_BANKS.get(interview_type, {}).get(
            sub_bank, self.ROLE_QUESTION_BANKS.get(interview_type, {}).get("Default", [])
        )
        if not questions:
            questions = self.ROLE_QUESTION_BANKS["Technical"]["Default"]

        base_q = questions[0]

        # Personalize if candidate has projects
        if candidate_projects and len(candidate_projects) > 0:
            p_title = candidate_projects[0].get("title", "your featured project")
            if interview_type == "Behavioral":
                return f"I noticed you developed '{p_title}'. Tell me about the most difficult engineering challenge you encountered while building it and how you overcame it."
            elif interview_type == "System Design":
                return f"Looking at your project '{p_title}', how would you redesign its architecture to handle a 100x increase in concurrent users and data throughput?"

        return base_q

    async def evaluate_answer_and_next_question(
        self,
        session: InterviewSession,
        current_question: str,
        student_answer: str,
        current_index: int,
        total_questions: int,
    ) -> Dict[str, Any]:
        """
        Evaluate student answer using Gemini or deterministic rubric engine,
        and generate either the adaptive follow-up or the final wrap-up report.
        """
        # Try Gemini evaluation first if configured
        gemini_result = await self._try_gemini_evaluation(
            role_title=session.role_title,
            interview_type=session.interview_type,
            question=current_question,
            answer=student_answer,
            is_final=(current_index >= total_questions - 1),
        )

        if gemini_result:
            evaluation = gemini_result
        else:
            evaluation = self._deterministic_answer_evaluation(
                interview_type=session.interview_type,
                question=current_question,
                answer=student_answer,
            )

        # Determine next question if session is still in progress
        next_question: Optional[str] = None
        is_completed = (current_index >= total_questions - 1)

        if not is_completed:
            next_question = self._select_next_question(
                session=session,
                prev_question=current_question,
                prev_answer=student_answer,
                next_index=current_index + 1,
            )

        return {
            "evaluation": evaluation,
            "next_question": next_question,
            "is_completed": is_completed,
        }

    async def _try_gemini_evaluation(
        self,
        role_title: str,
        interview_type: str,
        question: str,
        answer: str,
        is_final: bool,
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini API for structured rubric evaluation if API key is present."""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your-"):
            return None

        prompt = f"""You are a Principal Software Engineering Interviewer evaluating a candidate for '{role_title}' ({interview_type} Interview).
Question asked: "{question}"
Candidate Answer: "{answer}"

Evaluate the candidate answer on a scale of 0 to 100 on these 4 dimensions:
1. communication_score (clarity, concise structure, STAR method if behavioral)
2. technical_score (correctness, depth, architectural terminology)
3. problem_solving_score (trade-off awareness, edge cases, scalability)
4. relevance_score (directness in answering what was specifically asked)

Return ONLY valid JSON matching this schema:
{{
  "overall_score": <float 0-100>,
  "communication_score": <float 0-100>,
  "technical_score": <float 0-100>,
  "problem_solving_score": <float 0-100>,
  "relevance_score": <float 0-100>,
  "feedback": "<2-3 constructive sentences highlighting what was good and what was missing>",
  "model_answer_hint": "<1-2 sentences on key points or engineering trade-offs expected>"
}}"""
        try:
            from google import genai
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            resp = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            text = resp.text.strip()
            # Clean markdown codeblocks
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            data = json.loads(text)
            return {
                "overall_score": float(data.get("overall_score", 70.0)),
                "communication_score": float(data.get("communication_score", 70.0)),
                "technical_score": float(data.get("technical_score", 70.0)),
                "problem_solving_score": float(data.get("problem_solving_score", 70.0)),
                "relevance_score": float(data.get("relevance_score", 70.0)),
                "feedback": data.get("feedback", "Good response showing clear foundational knowledge."),
                "model_answer_hint": data.get("model_answer_hint", "Include specific metrics, trade-offs, and failure handling."),
            }
        except Exception as e:
            logger.warning("Gemini interview evaluation failed: %s. Using deterministic rubric.", e)
            return None

    def _deterministic_answer_evaluation(
        self,
        interview_type: str,
        question: str,
        answer: str,
    ) -> Dict[str, Any]:
        """High-precision deterministic rubric evaluation based on technical terms, depth, and structure."""
        words = answer.strip().split()
        word_count = len(words)

        # Baseline length scoring
        if word_count < 10:
            comm = 40.0
            tech = 35.0
            prob = 35.0
            rel = 40.0
            feedback = "The answer was very brief. Elaborate on your approach, design decisions, and concrete examples."
        elif word_count < 35:
            comm = 65.0
            tech = 60.0
            prob = 60.0
            rel = 70.0
            feedback = "Adequate foundation, but lacks technical depth. Mention specific mechanisms, edge cases, and trade-offs."
        else:
            comm = 85.0
            tech = 80.0
            prob = 82.0
            rel = 88.0
            feedback = "Well-articulated response with solid technical depth and clear reasoning."

        # Technical keyword booster
        tech_keywords = [
            "trade-off", "latency", "throughput", "cache", "database", "scale",
            "concurrency", "acid", "index", "async", "lock", "failure", "retry",
            "distributed", "profiling", "benchmark", "star", "result", "action"
        ]
        hits = sum(1 for kw in tech_keywords if kw in answer.lower())
        tech_boost = min(15.0, hits * 3.0)
        tech = min(98.0, tech + tech_boost)
        prob = min(98.0, prob + (tech_boost * 0.8))

        # Overall weighted composite
        overall = round(
            0.35 * tech + 0.25 * prob + 0.25 * comm + 0.15 * rel, 1
        )

        return {
            "overall_score": overall,
            "communication_score": round(comm, 1),
            "technical_score": round(tech, 1),
            "problem_solving_score": round(prob, 1),
            "relevance_score": round(rel, 1),
            "feedback": feedback,
            "model_answer_hint": "Focus on real-world constraints, specific architecture patterns, and quantitative outcomes.",
        }

    def _select_next_question(
        self,
        session: InterviewSession,
        prev_question: str,
        prev_answer: str,
        next_index: int,
    ) -> str:
        """Select next question or generate adaptive follow-up based on candidate's answer."""
        role_lower = session.role_title.lower()
        sub_bank = "Default"
        if "backend" in role_lower or "python" in role_lower or "api" in role_lower:
            sub_bank = "Backend"
        elif "frontend" in role_lower or "react" in role_lower:
            sub_bank = "Frontend"
        elif "ai" in role_lower or "ml" in role_lower:
            sub_bank = "AI/ML"

        questions = self.ROLE_QUESTION_BANKS.get(session.interview_type, {}).get(
            sub_bank, self.ROLE_QUESTION_BANKS.get(session.interview_type, {}).get("Default", [])
        )
        if not questions:
            questions = self.ROLE_QUESTION_BANKS["Technical"]["Default"]

        if next_index < len(questions):
            return questions[next_index]

        return f"Regarding your point about '{prev_answer[:40]}...', how would you handle unexpected system failures or network partitions in that scenario?"


interview_service = InterviewService()
