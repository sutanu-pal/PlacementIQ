from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_interview_session(client: AsyncClient):
    """Test initializing a new mock interview session."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "interviewer_candidate@univ.edu", "password": "Password123!", "full_name": "Interviewee"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "role_title": "Backend Developer (Python/FastAPI)",
        "interview_type": "Technical",
        "total_questions": 3,
    }

    start_resp = await client.post("/api/v1/interviews/start", json=payload, headers=headers)
    assert start_resp.status_code == 201
    data = start_resp.json()
    assert data["role_title"] == "Backend Developer (Python/FastAPI)"
    assert data["interview_type"] == "Technical"
    assert data["status"] == "in_progress"
    assert len(data["messages"]) == 1
    assert len(data["messages"][0]["question_text"]) > 10


@pytest.mark.asyncio
async def test_interview_turn_and_completion(client: AsyncClient):
    """Test full interactive interview loop until completion and final report generation."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "full_interview@univ.edu", "password": "Password123!", "full_name": "Full Interviewee"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start 2-question session
    start_resp = await client.post(
        "/api/v1/interviews/start",
        json={"role_title": "Full Stack Engineer", "interview_type": "Technical", "total_questions": 2},
        headers=headers,
    )
    assert start_resp.status_code == 201
    session_id = start_resp.json()["id"]

    # Turn 1: Submit Answer 1
    answer_payload = {
        "answer_text": "I design our architecture with PostgreSQL connection pooling and Redis caching to lower database latency. We run async FastAPI handlers and handle transactions with explicit commit and rollback blocks."
    }
    turn1_resp = await client.post(
        f"/api/v1/interviews/{session_id}/answer",
        json=answer_payload,
        headers=headers,
    )
    assert turn1_resp.status_code == 200
    turn1 = turn1_resp.json()
    assert turn1["is_completed"] is False
    assert turn1["next_question"] is not None
    assert turn1["evaluation"]["overall_score"] > 50

    # Turn 2: Submit Answer 2 (Final Question)
    answer_payload_2 = {
        "answer_text": "We monitor performance using Prometheus and Grafana alerts. When traffic spikes, we implement backoff retries with jitter and circuit breakers to avoid cascading failures."
    }
    turn2_resp = await client.post(
        f"/api/v1/interviews/{session_id}/answer",
        json=answer_payload_2,
        headers=headers,
    )
    assert turn2_resp.status_code == 200
    turn2 = turn2_resp.json()
    assert turn2["is_completed"] is True
    session_summary = turn2["session"]
    assert session_summary["status"] == "completed"
    assert session_summary["overall_score"] > 50
    assert len(session_summary["messages"]) == 2
    assert len(session_summary["strengths"]) > 0 or len(session_summary["improvement_areas"]) > 0


@pytest.mark.asyncio
async def test_interview_cross_user_privacy(client: AsyncClient):
    """Ensure User B cannot inspect User A's interview transcript."""
    # User A starts interview
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_a@univ.edu", "password": "Password123!", "full_name": "Candidate A"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    sess_resp = await client.post(
        "/api/v1/interviews/start",
        json={"role_title": "AI Research Engineer", "interview_type": "Technical", "total_questions": 3},
        headers=headers_a,
    )
    session_id = sess_resp.json()["id"]

    # User B registers
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_b@univ.edu", "password": "Password123!", "full_name": "Candidate B"},
    )
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # User B attempts to access User A's session -> 403 Forbidden
    forbidden = await client.get(f"/api/v1/interviews/{session_id}", headers=headers_b)
    assert forbidden.status_code == 403
