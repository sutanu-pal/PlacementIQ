from __future__ import annotations

import io
import pytest
import pymupdf
from httpx import AsyncClient

from app.ai.skill_extractor import get_skill_extractor
from app.services.pdf_parser import ResumePDFParser
from app.services.resume_scorer import ResumeScorer


def create_synthetic_pdf(text: str) -> bytes:
    """Helper to generate an in-memory PDF from text using PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    # Insert text lines
    y = 50
    for line in text.split("\n"):
        page.insert_text((50, y), line, fontsize=11)
        y += 18
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ─── 1. Skill Extraction Tests ───

def test_skill_extractor_precision():
    extractor = get_skill_extractor()
    sample = """
    Software Engineer with expertise in Python, C++, and Java.
    Built fullstack web apps using React.js, FastAPI, and PostgreSQL.
    Automated CI/CD workflows using Docker and GitHub Actions.
    Studied algorithms and data structures in college.
    Not good at Go, but learning Rust.
    """
    skills = extractor.extract_skills(sample)
    skill_names = {s["name"] for s in skills}

    # Verified skills must be present
    assert "Python" in skill_names
    assert "C++" in skill_names
    assert "Java" in skill_names
    assert "React" in skill_names
    assert "FastAPI" in skill_names
    assert "PostgreSQL" in skill_names
    assert "Docker" in skill_names
    assert "GitHub Actions" in skill_names
    assert "Rust" in skill_names
    assert "Algorithms" in skill_names
    assert "Data Structures" in skill_names


def test_skill_extractor_avoids_false_positives():
    extractor = get_skill_extractor()
    # "Course", "Good", "Computer", "Certificate", "College" shouldn't trigger C, Go, or R
    sample = "Took a general computer course at college and earned a certificate of completion."
    skills = extractor.extract_skills(sample)
    skill_names = {s["name"] for s in skills}

    assert "C" not in skill_names
    assert "Go" not in skill_names
    assert "R" not in skill_names


# ─── 2. PDF Parser Tests ───

def test_pdf_parser_valid_extraction():
    content = """
    Jane Doe
    Email: jane.doe@college.edu
    Phone: +1 555-019-2834
    GitHub: https://github.com/janedoe
    LinkedIn: https://linkedin.com/in/janedoe

    Education
    B.Tech in Computer Science & Engineering
    National Institute of Technology | CGPA: 8.9 | 2022 - 2026

    Technical Skills
    Languages: Python, Java, C++, SQL
    Frameworks: React, FastAPI, Node.js
    Databases & Tools: PostgreSQL, Docker, Git

    Projects
    Campus Placement Intelligence Engine
    Developed an AI platform using React and FastAPI. Reduced manual evaluation time by 40%.
    Distributed Key-Value Store
    Engineered a high-throughput persistent storage engine in C++ with Raft consensus.

    Experience
    Software Engineering Intern
    TechCorp Solutions | May 2025 - Jul 2025
    Implemented RESTful microservices and optimized PostgreSQL database queries.
    """
    pdf_bytes = create_synthetic_pdf(content)
    raw_text, page_count, is_scanned = ResumePDFParser.extract_text(pdf_bytes)

    assert page_count == 1
    assert not is_scanned
    assert "Campus Placement Intelligence Engine" in raw_text

    sections = ResumePDFParser.parse_sections(raw_text)
    assert sections["contact"]["email"] == "jane.doe@college.edu"
    assert sections["contact"]["github"] == "https://github.com/janedoe"
    assert len(sections["education"]) >= 1
    assert len(sections["projects"]) >= 1


def test_pdf_parser_invalid_file():
    with pytest.raises(Exception):
        ResumePDFParser.extract_text(b"This is not a real PDF file!")


# ─── 3. Scoring Engine Tests ───

def test_resume_scorer_comprehensive():
    parsed_data = {
        "contact": {
            "email": "student@college.edu",
            "phone": "+1 555-123-4567",
            "github": "https://github.com/teststudent",
            "linkedin": "https://linkedin.com/in/teststudent",
        },
        "education": [{"degree": "B.Tech Computer Science", "details": "NIT | 8.8 CGPA | 2026"}],
        "projects": [
            {"title": "Project Alpha", "description": "Engineered fullstack app using React and FastAPI."},
            {"title": "Project Beta", "description": "Developed distributed system in C++ with high throughput."},
        ],
        "experience": [{"title": "Software Intern", "description": "Optimized database queries and built APIs."}],
        "detected_sections": ["contact", "education", "skills", "projects", "experience"],
    }
    extracted_skills = [
        {"name": "Python", "category": "programming_languages"},
        {"name": "C++", "category": "programming_languages"},
        {"name": "React", "category": "frameworks_and_libraries"},
        {"name": "FastAPI", "category": "frameworks_and_libraries"},
        {"name": "PostgreSQL", "category": "databases"},
        {"name": "Docker", "category": "cloud_and_devops"},
        {"name": "Git", "category": "tools_and_concepts"},
    ]
    raw_text = "Engineered, optimized, developed and built applications."

    score_res = ResumeScorer.score_resume(parsed_data, extracted_skills, raw_text)
    assert score_res["overall_score"] >= 65
    assert "score_breakdown" in score_res
    assert score_res["score_breakdown"]["structure_score"] > 0
    assert score_res["score_breakdown"]["skills_score"] > 0
    assert len(score_res["strengths"]) > 0
    assert "disclaimer" in score_res


# ─── 4. End-to-End API Integration & Authorization Tests ───

@pytest.mark.asyncio
async def test_resume_upload_and_lifecycle(client: AsyncClient):
    # 1. Register Student A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_a@college.edu",
            "password": "Password123!",
            "full_name": "Student A",
            "college": "State College",
            "branch": "CSE",
            "semester": 7,
        },
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Student B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "student_b@college.edu",
            "password": "Password123!",
            "full_name": "Student B",
            "college": "State College",
            "branch": "CSE",
            "semester": 7,
        },
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Non-PDF upload fails (400)
    res_bad = await client.post(
        "/api/v1/resumes/upload",
        headers=headers_a,
        files={"file": ("resume.txt", b"plain text is not pdf", "text/plain")},
    )
    assert res_bad.status_code == 400

    # 4. Valid PDF upload by Student A
    resume_text_v1 = """
    Alex Candidate
    Email: alex@example.com | Phone: 9876543210
    GitHub: https://github.com/alexcandidate
    
    Education
    B.Tech Computer Science - NIT - 2026 - 8.5 CGPA
    
    Technical Skills
    Python, C++, Java, React, FastAPI, PostgreSQL, Docker, Git
    
    Projects
    PlacementIQ AI Portal
    Built machine learning platform with FastAPI and React.
    
    Experience
    Software Intern at Tech Corp
    Developed automated REST APIs and optimized SQL database queries.
    """
    pdf_v1 = create_synthetic_pdf(resume_text_v1)
    res_upload_v1 = await client.post(
        "/api/v1/resumes/upload",
        headers=headers_a,
        files={"file": ("alex_resume.pdf", pdf_v1, "application/pdf")},
    )
    assert res_upload_v1.status_code == 201
    data_v1 = res_upload_v1.json()
    resume_id_v1 = data_v1["id"]
    assert data_v1["version"] == 1
    assert data_v1["filename"] == "alex_resume.pdf"
    assert data_v1["overall_score"] > 50
    assert len(data_v1["extracted_skills"]) >= 5
    assert "ai_feedback" in data_v1

    # 5. Upload second version by Student A -> version must be 2
    pdf_v2 = create_synthetic_pdf(resume_text_v1 + "\nAlso skilled in Kubernetes and Redis.")
    res_upload_v2 = await client.post(
        "/api/v1/resumes/upload",
        headers=headers_a,
        files={"file": ("alex_resume_v2.pdf", pdf_v2, "application/pdf")},
    )
    assert res_upload_v2.status_code == 201
    data_v2 = res_upload_v2.json()
    resume_id_v2 = data_v2["id"]
    assert data_v2["version"] == 2

    # 6. Student A lists their resumes
    res_list_a = await client.get("/api/v1/resumes/", headers=headers_a)
    assert res_list_a.status_code == 200
    list_a = res_list_a.json()
    assert list_a["total"] == 2
    assert list_a["resumes"][0]["version"] == 2
    assert list_a["resumes"][1]["version"] == 1

    # 7. Student B lists their resumes -> must be empty (tenant isolation)
    res_list_b = await client.get("/api/v1/resumes/", headers=headers_b)
    assert res_list_b.status_code == 200
    assert res_list_b.json()["total"] == 0

    # 8. Student B attempts to access Student A's resume -> 403 Forbidden
    res_cross_access = await client.get(f"/api/v1/resumes/{resume_id_v1}", headers=headers_b)
    assert res_cross_access.status_code == 403
    assert "Access denied" in res_cross_access.json()["detail"]

    # 9. Student B attempts to access Student A's analysis -> 403 Forbidden
    res_cross_analysis = await client.get(f"/api/v1/resumes/{resume_id_v1}/analysis", headers=headers_b)
    assert res_cross_analysis.status_code == 403

    # 10. Student B attempts to delete Student A's resume -> 403 Forbidden
    res_cross_del = await client.delete(f"/api/v1/resumes/{resume_id_v1}", headers=headers_b)
    assert res_cross_del.status_code == 403

    # 11. Student A fetches their resume detail and analysis
    res_detail = await client.get(f"/api/v1/resumes/{resume_id_v1}", headers=headers_a)
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == resume_id_v1

    res_analysis = await client.get(f"/api/v1/resumes/{resume_id_v1}/analysis", headers=headers_a)
    assert res_analysis.status_code == 200
    analysis_data = res_analysis.json()
    assert "score_breakdown" in analysis_data
    assert "extracted_skills" in analysis_data
    assert "ai_feedback" in analysis_data

    # 12. Student A deletes version 1
    res_del = await client.delete(f"/api/v1/resumes/{resume_id_v1}", headers=headers_a)
    assert res_del.status_code == 200

    # 13. Verify version 1 is gone
    res_deleted_check = await client.get(f"/api/v1/resumes/{resume_id_v1}", headers=headers_a)
    assert res_deleted_check.status_code == 404


@pytest.mark.asyncio
async def test_synthetic_sample_resumes(client: AsyncClient):
    import os

    base_dir = os.path.dirname(os.path.dirname(__file__))
    fullstack_pdf_path = os.path.join(base_dir, "data", "sample_resumes", "synthetic_fullstack_ai_student.pdf")
    entry_pdf_path = os.path.join(base_dir, "data", "sample_resumes", "synthetic_entry_student.pdf")

    assert os.path.exists(fullstack_pdf_path), "Fullstack sample PDF must exist"
    assert os.path.exists(entry_pdf_path), "Entry sample PDF must exist"

    # Register candidate
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "benchmarker@college.edu",
            "password": "BenchmarkPassword123!",
            "full_name": "Benchmark Student",
            "college": "MIT Tech",
            "branch": "CSE AI & ML",
            "semester": 7,
        },
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Upload Fullstack
    with open(fullstack_pdf_path, "rb") as f:
        bytes_fullstack = f.read()

    res_fs = await client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("alex_fullstack.pdf", bytes_fullstack, "application/pdf")},
    )
    assert res_fs.status_code == 201
    fs_data = res_fs.json()
    assert fs_data["overall_score"] >= 75
    assert len(fs_data["extracted_skills"]) >= 10

    # Upload Entry level
    with open(entry_pdf_path, "rb") as f:
        bytes_entry = f.read()

    res_entry = await client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("rohan_entry.pdf", bytes_entry, "application/pdf")},
    )
    assert res_entry.status_code == 201
    entry_data = res_entry.json()
    # Entry level score should be lower than fullstack candidate
    assert entry_data["overall_score"] < fs_data["overall_score"]
    assert len(entry_data["improvement_areas"]) > 0
