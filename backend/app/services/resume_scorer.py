from __future__ import annotations

import re
from typing import Any, Dict, List


class ResumeScorer:
    """
    Explainable resume scoring engine.
    Calculates composite score (0-100) and itemized component scores.
    """

    DISCLAIMER = (
        "This score evaluates resume formatting, structural completeness, and technical keyword coverage. "
        "It is an algorithmic readiness signal and does not guarantee or predict recruitment success."
    )

    ACTION_VERBS = {
        "developed", "built", "implemented", "designed", "optimized",
        "created", "engineered", "accelerated", "reduced", "improved",
        "deployed", "integrated", "automated", "spearheaded", "led",
    }

    @classmethod
    def score_resume(
        cls,
        parsed_data: Dict[str, Any],
        extracted_skills: List[Dict[str, str]],
        raw_text: str,
    ) -> Dict[str, Any]:
        """Compute transparent, criteria-based evaluation."""
        strengths: List[str] = []
        improvements: List[str] = []

        # 1. Structure Score (Max 25)
        structure_score = 0
        contact = parsed_data.get("contact", {})
        if contact.get("email"):
            structure_score += 5
        else:
            improvements.append("Missing email address in contact section.")

        if contact.get("linkedin") or contact.get("github") or contact.get("phone"):
            structure_score += 5
            if contact.get("github"):
                strengths.append("GitHub profile link included for technical review.")
            if contact.get("linkedin"):
                strengths.append("Professional LinkedIn profile link provided.")
        else:
            improvements.append("Consider adding LinkedIn and GitHub profile links.")

        detected = set(parsed_data.get("detected_sections", []))
        if "education" in detected:
            structure_score += 4
        else:
            improvements.append("Education section not clearly identified with standard heading.")

        if "skills" in detected or len(extracted_skills) >= 3:
            structure_score += 4
        else:
            improvements.append("Dedicated Technical Skills section is recommended for ATS readability.")

        if "projects" in detected:
            structure_score += 4
        else:
            improvements.append("Projects section is missing or lacks clear heading.")

        if "experience" in detected or "certifications" in detected:
            structure_score += 3
        else:
            improvements.append("Include internships, work experience, or certifications.")

        structure_score = min(25, structure_score)
        if structure_score >= 21:
            strengths.append("Well-structured resume covering essential standard engineering sections.")

        # 2. Skills Score (Max 25)
        skills_score = 0
        skill_count = len(extracted_skills)
        categories = {s["category"] for s in extracted_skills}

        if skill_count >= 10:
            skills_score += 15
            strengths.append(f"Strong technical skill footprint with {skill_count} detected skills.")
        elif skill_count >= 6:
            skills_score += 11
            strengths.append(f"Good technical breadth with {skill_count} verified skills.")
        elif skill_count >= 3:
            skills_score += 7
            improvements.append("Expand your skills list with more frameworks and databases you know.")
        elif skill_count >= 1:
            skills_score += 3
            improvements.append("Very few technical skills identified; ensure skills match job descriptions.")
        else:
            skills_score += 0
            improvements.append("No technical skills identified. Add a dedicated Skills section.")

        # Diversity
        cat_count = len(categories)
        if cat_count >= 4:
            skills_score += 10
            strengths.append(f"Diverse skill distribution across {cat_count} technical categories.")
        elif cat_count >= 3:
            skills_score += 7
        elif cat_count >= 2:
            skills_score += 5
        elif cat_count >= 1:
            skills_score += 2
            improvements.append("Skills are concentrated in one domain; broaden into databases, cloud, or tools.")

        skills_score = min(25, skills_score)

        # 3. Projects Score (Max 20)
        projects_score = 0
        projects = parsed_data.get("projects", [])
        p_count = len(projects)

        if p_count >= 2:
            projects_score += 12
            strengths.append(f"Multiple engineering projects presented ({p_count} detected).")
        elif p_count == 1:
            projects_score += 7
            improvements.append("Include at least 2 substantial software projects to showcase versatility.")
        else:
            improvements.append("No distinct technical projects detected. Add project titles with descriptions.")

        # Quality of descriptions: tech mentions & action verbs
        tech_words_in_projects = sum(
            1 for p in projects if any(s["name"].lower() in p.get("description", "").lower() for s in extracted_skills[:10])
        )
        if tech_words_in_projects >= 1:
            projects_score += 4
            strengths.append("Projects explicitly reference technical stacks and toolsets.")
        else:
            improvements.append("Explicitly state technologies used for each project (e.g. 'Tech: React, FastAPI, Docker').")

        # Check for length/detail
        avg_p_len = sum(len(p.get("description", "")) for p in projects) / max(1, p_count)
        if avg_p_len > 80:
            projects_score += 4
        else:
            improvements.append("Elaborate on project architecture, key challenges solved, and results.")

        projects_score = min(20, projects_score)

        # 4. Education Score (Max 15)
        education_score = 0
        education = parsed_data.get("education", [])
        if education:
            education_score += 8
            edu_text = " ".join([e.get("degree", "") + " " + e.get("details", "") for e in education])
            # Check for college or degree clarification
            if re.search(r"\b(College|University|Institute|School|Campus|NIT|IIT|IIIT|BITS)\b", edu_text, re.I):
                education_score += 4
            # Check for GPA, CGPA or Year
            if re.search(r"\b(CGPA|GPA|Percentage|\d\.\d{1,2}|20\d\d)\b", edu_text, re.I):
                education_score += 3
                strengths.append("Clear educational credentials with academic metrics or graduation year.")
            else:
                improvements.append("Mention your CGPA/percentage and expected graduation year in Education.")
        else:
            improvements.append("Education details not detected. State degree, institution, and branch.")

        education_score = min(15, education_score)

        # 5. Experience / Practical Exposure (Max 15)
        experience_score = 0
        experience = parsed_data.get("experience", [])
        if experience and any(e.get("title") for e in experience):
            experience_score += 10
            strengths.append("Professional internship or practical work experience included.")
        elif p_count >= 3:
            # Grant student project compensation
            experience_score += 7
            strengths.append("Demonstrated solid hands-on development through multiple comprehensive projects.")
        else:
            improvements.append("Add an internship, research experience, or open-source contribution.")

        # Check for action-oriented impact verbs across experience/text
        text_lower = raw_text.lower()
        verb_matches = [v for v in cls.ACTION_VERBS if re.search(rf"\b{v}\b", text_lower)]
        if len(verb_matches) >= 4:
            experience_score += 5
            strengths.append("Strong use of impact-driven engineering action verbs in descriptions.")
        elif len(verb_matches) >= 2:
            experience_score += 3
        else:
            improvements.append("Use strong action verbs (e.g. 'Engineered', 'Optimized', 'Automated') to highlight impact.")

        experience_score = min(15, experience_score)

        # Total Composite
        total_score = round(structure_score + skills_score + projects_score + education_score + experience_score, 1)

        return {
            "overall_score": total_score,
            "score_breakdown": {
                "structure_score": structure_score,
                "skills_score": skills_score,
                "projects_score": projects_score,
                "education_score": education_score,
                "experience_score": experience_score,
            },
            "strengths": strengths[:6],
            "improvement_areas": improvements[:6],
            "disclaimer": cls.DISCLAIMER,
        }
