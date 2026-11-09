from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.job import Job
from app.models.resume import Resume
from app.services.job_matching_service import job_matching_service


@pytest.mark.asyncio
async def test_job_matching_service_unit():
    """Unit test for JobMatchingService scoring and explanation logic."""
    resume = Resume(
        id="res-1",
        user_id="user-1",
        version=1,
        raw_text="Experienced Python backend developer skilled in FastAPI, PostgreSQL, Docker, Git. Built REST API platform.",
        extracted_skills=[
            {"name": "Python", "category": "Languages"},
            {"name": "FastAPI", "category": "Frameworks"},
            {"name": "PostgreSQL", "category": "Databases"},
        ],
        parsed_data={
            "projects": [
                {
                    "title": "Placement Platform",
                    "description": "High performance backend built with FastAPI and PostgreSQL",
                    "technologies": ["Python", "FastAPI", "PostgreSQL"],
                }
            ]
        },
    )

    job = Job(
        id="job-1",
        title="Backend Developer",
        company="ApexTech",
        description="Looking for Python FastAPI engineer with PostgreSQL and Redis knowledge.",
        responsibilities=["Build REST APIs in FastAPI", "Maintain PostgreSQL database"],
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_skills=["Redis", "Docker"],
        experience_level="Fresher / Entry Level",
    )

    result = job_matching_service.match_resume_to_job(resume=resume, job=job)

    assert result["match_score"] > 0.0
    assert result["match_score"] <= 100.0
    # Required skills all matched (100%), preferred: Docker matched via text (50%)
    assert "Python" in result["matched_skills"]
    assert "FastAPI" in result["matched_skills"]
    assert "PostgreSQL" in result["matched_skills"]
    assert len(result["missing_required_skills"]) == 0
    assert "Redis" in result["missing_preferred_skills"]
    assert result["skill_score"] >= 70.0
    assert len(result["explanations"]) >= 3
    assert len(result["recommendations"]) >= 1
    assert "disclaimer" in result


@pytest.mark.asyncio
async def test_job_matching_service_zero_match():
    """Test matching when candidate has completely disjoint skills."""
    resume = Resume(
        id="res-2",
        user_id="user-1",
        version=1,
        raw_text="Frontend enthusiast working with React, CSS, HTML, Figma.",
        extracted_skills=[
            {"name": "React", "category": "Frameworks"},
            {"name": "CSS", "category": "Languages"},
        ],
        parsed_data={"projects": []},
    )

    job = Job(
        id="job-2",
        title="DevOps Engineer",
        company="InfraCloud",
        description="Kubernetes, Terraform, AWS, and Linux specialist needed.",
        responsibilities=["Manage cloud clusters"],
        required_skills=["Kubernetes", "Terraform", "AWS"],
        preferred_skills=["Linux"],
    )

    result = job_matching_service.match_resume_to_job(resume=resume, job=job)

    assert result["skill_score"] == 0.0
    assert set(result["missing_required_skills"]) == {"Kubernetes", "Terraform", "AWS"}
    assert result["match_score"] < 50.0


@pytest.mark.asyncio
async def test_jobs_list_auto_seed(client: AsyncClient):
    """Test that listing jobs returns benchmark jobs and auto-seeds them."""
    # Register and login user
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "student1@univ.edu", "password": "Password123!", "full_name": "Student One"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/jobs/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 6
    assert len(data["items"]) >= 6
    assert all(item["is_synthetic"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_jobs_filtering(client: AsyncClient):
    """Test searching and filtering jobs."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "student2@univ.edu", "password": "Password123!", "full_name": "Student Two"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search by keyword
    resp = await client.get("/api/v1/jobs/?search=Backend", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Backend" in item["title"] for item in items)


@pytest.mark.asyncio
async def test_admin_job_crud_permissions(client_with_db):
    """
    Test that regular students cannot create/update/delete jobs (403 Forbidden),
    but a user promoted to admin CAN perform those operations (201/200).

    Security contract:
    - Public registration NEVER grants admin privileges (is_admin defaults to False).
    - Admin promotion happens only via direct database access (e.g. a seeded admin seed
      script or a secure internal tool).  Here we simulate that by writing directly to
      the shared test-session, which is the same StaticPool connection the test client
      uses — no separate engine or connection is created.
    - The existing JWT token stays valid; the backend reloads is_admin from DB on
      every request (see app/dependencies.py get_current_user), so the promotion is
      reflected immediately without re-login.
    """
    client, db = client_with_db

    # --- Register a plain student via public API (is_admin stays False) ---
    reg_student = await client.post(
        "/api/v1/auth/register",
        json={"email": "regular@univ.edu", "password": "Password123!", "full_name": "Regular Student"},
    )
    assert reg_student.status_code == 201
    student_token = reg_student.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # --- Register the future admin via public API (also starts as a plain student) ---
    reg_admin = await client.post(
        "/api/v1/auth/register",
        json={"email": "admin@univ.edu", "password": "AdminPassword123!", "full_name": "Admin User"},
    )
    assert reg_admin.status_code == 201
    # Keep the token from registration — the backend re-reads is_admin from DB each
    # request, so we do NOT need to re-login after the DB promotion below.
    admin_token = reg_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # --- Promote user to admin directly in the shared test-database session ---
    # This is the ONLY safe way to test admin flows: write to DB, not public API.
    from sqlalchemy import select as _select
    from app.models.user import User

    result = await db.execute(_select(User).where(User.email == "admin@univ.edu"))
    admin_user = result.scalar_one()
    assert admin_user.is_admin is False, "Sanity check: registration must not grant admin"
    admin_user.is_admin = True
    await db.commit()
    await db.refresh(admin_user)
    assert admin_user.is_admin is True

    # --- Job payload used for all CRUD tests ---
    job_payload = {
        "title": "Distributed Systems Engineer",
        "company": "ScaleTech [Synthetic]",
        "description": "Design high throughput distributed message queues.",
        "responsibilities": ["Build Kafka pipelines", "Optimize raft consensus"],
        "required_skills": ["Go", "Kafka", "Docker"],
        "preferred_skills": ["Kubernetes"],
        "experience_level": "Fresher / Entry Level",
        "location": "Bengaluru",
        "employment_type": "Full-time",
        "salary_range": "₹15-20 LPA",
        "is_active": True,
        "is_synthetic": True,
    }

    # 1. Student attempts creation → must be 403 Forbidden
    student_create = await client.post("/api/v1/jobs/", json=job_payload, headers=student_headers)
    assert student_create.status_code == 403, f"Student create should be 403, got {student_create.status_code}"

    # 2. Admin creates → must be 201 Created
    admin_create = await client.post("/api/v1/jobs/", json=job_payload, headers=admin_headers)
    assert admin_create.status_code == 201, f"Admin create failed: {admin_create.text}"
    job_id = admin_create.json()["id"]

    # 3. Admin updates → must be 200 OK with new salary_range
    admin_update = await client.put(
        f"/api/v1/jobs/{job_id}",
        json={"salary_range": "₹18-24 LPA"},
        headers=admin_headers,
    )
    assert admin_update.status_code == 200
    assert admin_update.json()["salary_range"] == "₹18-24 LPA"

    # 4. Student attempts deletion → must be 403 Forbidden
    student_del = await client.delete(f"/api/v1/jobs/{job_id}", headers=student_headers)
    assert student_del.status_code == 403

    # 5. Admin deletes → must be 200 OK
    admin_del = await client.delete(f"/api/v1/jobs/{job_id}", headers=admin_headers)
    assert admin_del.status_code == 200


@pytest.mark.asyncio
async def test_end_to_end_job_match(client: AsyncClient):
    """End-to-end test: upload resume, match with job, retrieve match history."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate@univ.edu", "password": "Password123!", "full_name": "Job Candidate"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Trigger job seeding by listing jobs
    jobs_resp = await client.get("/api/v1/jobs/", headers=headers)
    jobs = jobs_resp.json()["items"]
    target_job = jobs[0]

    # 2. Attempt match without resume -> 400 Bad Request
    match_fail = await client.post(f"/api/v1/jobs/{target_job['id']}/match", headers=headers)
    assert match_fail.status_code == 400

    # 3. Create synthetic PDF content and upload resume
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "John Doe\njohn@example.com\n\nEDUCATION\nB.Tech Computer Science\n\n"
        "SKILLS\nPython, FastAPI, PostgreSQL, Git, Docker, Redis\n\n"
        "PROJECTS\nREST API Microservices Platform\nBuilt with Python, FastAPI and PostgreSQL database.\n",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    upload_resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert upload_resp.status_code == 201

    # 4. Perform match with job
    match_resp = await client.post(f"/api/v1/jobs/{target_job['id']}/match", headers=headers)
    assert match_resp.status_code == 200
    match_data = match_resp.json()
    assert match_data["match_score"] > 0
    assert match_data["job_id"] == target_job["id"]
    match_id = match_data["id"]

    # 5. Fetch match history
    history_resp = await client.get("/api/v1/job-matches/", headers=headers)
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert history["total"] >= 1
    assert any(m["id"] == match_id for m in history["items"])

    # 6. Fetch individual match detail
    detail_resp = await client.get(f"/api/v1/job-matches/{match_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == match_id


@pytest.mark.asyncio
async def test_job_match_user_privacy(client: AsyncClient):
    """Ensure User B cannot view User A's match evaluation report."""
    # User A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@univ.edu", "password": "Password123!", "full_name": "User A"},
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@univ.edu", "password": "Password123!", "full_name": "User B"},
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Seed jobs
    jobs_resp = await client.get("/api/v1/jobs/", headers=headers_a)
    job_id = jobs_resp.json()["items"][0]["id"]

    # User A uploads resume
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "User A\nPython, FastAPI Developer")
    pdf_bytes = doc.tobytes()
    doc.close()

    await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume_a.pdf", pdf_bytes, "application/pdf")},
        headers=headers_a,
    )

    # User A matches
    match_res = await client.post(f"/api/v1/jobs/{job_id}/match", headers=headers_a)
    assert match_res.status_code == 200
    match_id = match_res.json()["id"]

    # User B attempts to access User A's match -> 403 Forbidden
    unauthorized = await client.get(f"/api/v1/job-matches/{match_id}", headers=headers_b)
    assert unauthorized.status_code == 403
