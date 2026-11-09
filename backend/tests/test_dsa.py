from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_dsa_questions_auto_seed(client: AsyncClient):
    """Test that listing DSA questions automatically seeds the question bank."""
    # Register and login user
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "dsa_student1@univ.edu", "password": "Password123!", "full_name": "DSA Student"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/dsa/questions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 8
    assert len(data["items"]) >= 8


@pytest.mark.asyncio
async def test_dsa_get_question_security(client: AsyncClient):
    """Test that retrieving question detail only exposes visible test cases, hiding private validation tests."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "dsa_student2@univ.edu", "password": "Password123!", "full_name": "DSA Student 2"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch Two Sum question
    resp = await client.get("/api/v1/dsa/questions/two-sum", headers=headers)
    assert resp.status_code == 200
    q = resp.json()
    assert q["slug"] == "two-sum"
    assert q["difficulty"] == "Easy"
    assert "visible_test_cases" in q
    # All visible test cases must have is_hidden == False
    for tc in q["visible_test_cases"]:
        assert tc.get("is_hidden", False) is False


@pytest.mark.asyncio
async def test_dsa_submission_correct_solution(client: AsyncClient):
    """Test submitting an optimal solution that passes all test cases."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "coder@univ.edu", "password": "Password123!", "full_name": "Coder User"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get question id for two-sum
    q_resp = await client.get("/api/v1/dsa/questions/two-sum", headers=headers)
    q_id = q_resp.json()["id"]

    correct_code = """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            diff = target - num
            if diff in seen:
                return [seen[diff], i]
            seen[num] = i
        return []
"""

    sub_resp = await client.post(
        f"/api/v1/dsa/questions/{q_id}/submit",
        json={"code": correct_code, "language": "python"},
        headers=headers,
    )
    assert sub_resp.status_code == 200
    result = sub_resp.json()
    assert result["status"] == "Accepted"
    assert result["passed_count"] == result["total_count"]
    assert result["passed_count"] >= 3
    assert len(result["test_results"]) > 0


@pytest.mark.asyncio
async def test_dsa_submission_wrong_solution(client: AsyncClient):
    """Test submitting incorrect code returns 'Wrong Answer'."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "wrong_coder@univ.edu", "password": "Password123!", "full_name": "Wrong Coder"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    q_resp = await client.get("/api/v1/dsa/questions/two-sum", headers=headers)
    q_id = q_resp.json()["id"]

    wrong_code = """class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        return [0, 0]
"""

    sub_resp = await client.post(
        f"/api/v1/dsa/questions/{q_id}/submit",
        json={"code": wrong_code, "language": "python"},
        headers=headers,
    )
    assert sub_resp.status_code == 200
    result = sub_resp.json()
    assert result["status"] == "Wrong Answer"
    assert result["error_message"] is not None


@pytest.mark.asyncio
async def test_dsa_submission_security_violation(client: AsyncClient):
    """Test that unauthorized imports or dangerous system access are blocked by AST analysis."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "malicious@univ.edu", "password": "Password123!", "full_name": "Malicious User"},
    )
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    q_resp = await client.get("/api/v1/dsa/questions/two-sum", headers=headers)
    q_id = q_resp.json()["id"]

    malicious_code = """import os
class Solution:
    def twoSum(self, nums, target):
        os.system("dir")
        return [0, 1]
"""

    sub_resp = await client.post(
        f"/api/v1/dsa/questions/{q_id}/submit",
        json={"code": malicious_code, "language": "python"},
        headers=headers,
    )
    assert sub_resp.status_code == 200
    result = sub_resp.json()
    assert result["status"] == "Security Violation"
    assert "Security Policy" in result["error_message"]


@pytest.mark.asyncio
async def test_dsa_admin_question_crud(client_with_db):
    """Test that regular students cannot create questions, but admins can."""
    client, db = client_with_db

    # 1. Student
    reg_student = await client.post(
        "/api/v1/auth/register",
        json={"email": "student_dsa@univ.edu", "password": "Password123!", "full_name": "Student DSA"},
    )
    student_headers = {"Authorization": f"Bearer {reg_student.json()['access_token']}"}

    # 2. Admin
    reg_admin = await client.post(
        "/api/v1/auth/register",
        json={"email": "admin_dsa@univ.edu", "password": "AdminPassword123!", "full_name": "Admin DSA"},
    )
    admin_headers = {"Authorization": f"Bearer {reg_admin.json()['access_token']}"}

    # Promote admin in shared test db
    res = await db.execute(select(User).where(User.email == "admin_dsa@univ.edu"))
    admin_u = res.scalar_one()
    admin_u.is_admin = True
    await db.commit()

    q_payload = {
        "title": "Merge Sorted Array",
        "slug": "merge-sorted-array-custom",
        "category": "Arrays",
        "difficulty": "Easy",
        "description": "Merge nums2 into nums1 as one sorted array.",
        "constraints": ["nums1.length == m + n"],
        "examples": [{"input": "nums1 = [1,2,3,0,0,0]", "output": "[1,2,2,3,5,6]"}],
        "starter_code": {"python": "class Solution:\n    def merge(self, nums1, m, nums2, n):\n        pass\n"},
        "test_cases": [{"input": {"nums1": [1, 2, 3], "nums2": [2, 5, 6]}, "expected_output": [1, 2, 2, 3, 5, 6]}],
        "time_limit_ms": 2000,
        "memory_limit_mb": 128,
        "is_active": True,
    }

    # Student cannot create -> 403
    forbidden_resp = await client.post("/api/v1/dsa/questions", json=q_payload, headers=student_headers)
    assert forbidden_resp.status_code == 403

    # Admin creates -> 201
    created_resp = await client.post("/api/v1/dsa/questions", json=q_payload, headers=admin_headers)
    assert created_resp.status_code == 201
    q_id = created_resp.json()["id"]

    # Admin deletes -> 200
    del_resp = await client.delete(f"/api/v1/dsa/questions/{q_id}", headers=admin_headers)
    assert del_resp.status_code == 200


@pytest.mark.asyncio
async def test_dsa_analytics(client: AsyncClient):
    """Test retrieving user topic-wise analytics and recommendations."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "analyt_student@univ.edu", "password": "Password123!", "full_name": "Analytics Student"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    analytics_resp = await client.get("/api/v1/dsa/analytics", headers=headers)
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    assert "total_solved" in data
    assert "topic_breakdown" in data
    assert "recommendations" in data
    assert len(data["topic_breakdown"]) >= 5
