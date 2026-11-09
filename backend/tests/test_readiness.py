from __future__ import annotations

import fitz
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_readiness_new_user_handles_missing_dimensions(client: AsyncClient):
    """Test that a new user gets provisional 0 score and clear instructions for inactive dimensions."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "newbie@univ.edu", "password": "Password123!", "full_name": "New Student"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    resp = await client.get("/api/v1/readiness/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluated_dimensions_count"] == 0
    assert data["total_dimensions_count"] == 5
    assert data["overall_score"] == 0.0
    assert "Needs Foundational Preparation" in data["readiness_tier"]

    # Verify inactive dimension status messages
    dim_scores = data["dimension_scores"]
    assert dim_scores["resume_quality"]["available"] is False
    assert dim_scores["dsa_performance"]["available"] is False
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_readiness_with_resume_and_job_match(client: AsyncClient):
    """Test readiness computation when resume and job matching are completed."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "ready_cand@univ.edu", "password": "Password123!", "full_name": "Ready Candidate"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 1. Upload Resume
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Jane Doe\njane@example.com\n\nEDUCATION\nB.Tech CSE\n\n"
        "SKILLS\nPython, FastAPI, PostgreSQL, Docker, Git\n\n"
        "PROJECTS\nHigh Speed Microservice API\nBuilt in Python FastAPI.\n",
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    up_resp = await client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert up_resp.status_code == 201

    # 2. Match with job
    jobs = (await client.get("/api/v1/jobs/", headers=headers)).json()["items"]
    match_resp = await client.post(f"/api/v1/jobs/{jobs[0]['id']}/match", headers=headers)
    assert match_resp.status_code == 200

    # 3. Query Readiness
    readiness_resp = await client.get("/api/v1/readiness/", headers=headers)
    assert readiness_resp.status_code == 200
    r_data = readiness_resp.json()
    assert r_data["evaluated_dimensions_count"] >= 2
    assert r_data["provisional_score"] > 0.0
    assert r_data["dimension_scores"]["resume_quality"]["available"] is True
    assert r_data["dimension_scores"]["job_compatibility"]["available"] is True


@pytest.mark.asyncio
async def test_readiness_history(client: AsyncClient):
    """Test readiness history tracking."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "history_user@univ.edu", "password": "Password123!", "full_name": "History User"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Fetch readiness twice
    await client.get("/api/v1/readiness/", headers=headers)
    await client.get("/api/v1/readiness/", headers=headers)

    hist_resp = await client.get("/api/v1/readiness/history", headers=headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2
