from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "student@college.edu",
        "password": "strongPassword123",
        "full_name": "Test Student",
        "college": "CSE Tech Institute",
        "branch": "AI & ML",
        "semester": 7,
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "student@college.edu"
    assert data["user"]["full_name"] == "Test Student"
    assert data["user"]["semester"] == 7
    assert data["user"]["is_admin"] is False


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "duplicate@college.edu",
        "password": "password123",
        "full_name": "Original User",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success_and_failure(client: AsyncClient):
    # Register
    reg_payload = {
        "email": "loginuser@college.edu",
        "password": "validPassword999",
        "full_name": "Login User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Valid Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@college.edu", "password": "validPassword999"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "loginuser@college.edu"

    # Invalid Password Login
    wrong_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@college.edu", "password": "wrongPassword"},
    )
    assert wrong_res.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_protected_endpoint(client: AsyncClient):
    # Unauthenticated access
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Register to get token
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@college.edu",
            "password": "password123",
            "full_name": "Profile User",
            "college": "NIT",
            "branch": "CSE",
            "semester": 7,
        },
    )
    token = reg_res.json()["access_token"]

    # Authenticated access
    auth_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 200
    user_data = auth_res.json()
    assert user_data["email"] == "profile@college.edu"
    assert user_data["full_name"] == "Profile User"

    # Update profile
    update_res = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name", "semester": 8},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Updated Name"
    assert updated_data["semester"] == 8


@pytest.mark.asyncio
async def test_refresh_token_flow(client: AsyncClient):
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@college.edu",
            "password": "password123",
            "full_name": "Refresh User",
        },
    )
    refresh_token = reg_res.json()["refresh_token"]

    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["user"]["email"] == "refresh@college.edu"
