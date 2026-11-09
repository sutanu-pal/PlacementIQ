from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_or_create_roadmap(client: AsyncClient):
    """Test getting current roadmap automatically generates 4-week personalized curriculum."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "roadmap_student@univ.edu", "password": "Password123!", "full_name": "Roadmap Student"},
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    resp = await client.get("/api/v1/roadmap/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_weeks"] == 4
    assert len(data["milestones"]) == 4
    # Verify tasks and verified resource links exist
    first_task = data["milestones"][0]["tasks"][0]
    assert len(first_task["title"]) > 5
    assert len(first_task["resource_url"]) > 10
    assert len(first_task["triggered_by"]) > 5


@pytest.mark.asyncio
async def test_toggle_task_and_completion_percentage(client: AsyncClient):
    """Test checking off a task updates completion percentage."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "completer@univ.edu", "password": "Password123!", "full_name": "Completer Student"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Fetch roadmap
    r_resp = await client.get("/api/v1/roadmap/", headers=headers)
    assert r_resp.status_code == 200
    roadmap = r_resp.json()
    task_id = roadmap["milestones"][0]["tasks"][0]["id"]
    assert roadmap["completion_pct"] == 0.0

    # Toggle task
    toggle_resp = await client.post(f"/api/v1/roadmap/tasks/{task_id}/toggle", headers=headers)
    assert toggle_resp.status_code == 200
    updated = toggle_resp.json()
    assert updated["completion_pct"] > 0.0

    # Toggle back to unchecked
    untoggle_resp = await client.post(f"/api/v1/roadmap/tasks/{task_id}/toggle", headers=headers)
    assert untoggle_resp.status_code == 200
    assert untoggle_resp.json()["completion_pct"] == 0.0


@pytest.mark.asyncio
async def test_regenerate_roadmap_with_role(client: AsyncClient):
    """Test generating a roadmap tailored to a specific target role."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "ai_seeker@univ.edu", "password": "Password123!", "full_name": "AI Seeker"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    payload = {"target_role": "Machine Learning Engineer"}
    gen_resp = await client.post("/api/v1/roadmap/generate", json=payload, headers=headers)
    assert gen_resp.status_code == 200
    data = gen_resp.json()
    assert "Machine Learning Engineer" in data["target_role"]
    assert len(data["milestones"]) == 4


@pytest.mark.asyncio
async def test_roadmap_task_privacy(client: AsyncClient):
    """Ensure User B cannot toggle tasks belonging to User A."""
    # User A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera_road@univ.edu", "password": "Password123!", "full_name": "User A"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}
    r_a = await client.get("/api/v1/roadmap/", headers=headers_a)
    task_id_a = r_a.json()["milestones"][0]["tasks"][0]["id"]

    # User B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb_road@univ.edu", "password": "Password123!", "full_name": "User B"},
    )
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # User B attempts to toggle User A's task -> 404 Not Found
    unauthorized = await client.post(f"/api/v1/roadmap/tasks/{task_id_a}/toggle", headers=headers_b)
    assert unauthorized.status_code == 404
