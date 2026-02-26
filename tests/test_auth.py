import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_instructor(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "instructor@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Test Instructor",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_studio(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "studio@test.com",
            "password": "testpass123",
            "role": "studio",
            "business_name": "Test Studio",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Test",
        },
    )

    # Duplicate signup
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # First signup
    await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Test",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@test.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "wrongpass",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    # Signup
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "me@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Me Test",
        },
    )
    token = signup_response.json()["access_token"]

    # Get me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "me@test.com"
    assert data["user"]["role"] == "instructor"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401  # No auth header
