import pytest
from httpx import AsyncClient
from datetime import date


async def create_studio_and_job(client: AsyncClient) -> tuple[str, str]:
    """Create a studio user and a job post, return (token, job_id)."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_app_{id(client)}@test.com",
            "password": "testpass123",
            "role": "studio",
            "business_name": "Test Studio",
        },
    )
    token = response.json()["access_token"]

    job_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Job for Applications",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    job_id = job_response.json()["id"]

    return token, job_id


async def create_instructor_user(client: AsyncClient, suffix: str = "") -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"instructor_app_{suffix}_{id(client)}@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Test Instructor",
        },
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_apply_to_job(client: AsyncClient):
    _, job_id = await create_studio_and_job(client)
    instructor_token = await create_instructor_user(client, "apply")

    response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={"cover_letter": "I am a great instructor!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_post_id"] == job_id
    assert data["status"] == "pending"
    assert data["cover_letter"] == "I am a great instructor!"


@pytest.mark.asyncio
async def test_duplicate_application(client: AsyncClient):
    _, job_id = await create_studio_and_job(client)
    instructor_token = await create_instructor_user(client, "dup")

    # First application
    await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )

    # Duplicate application
    response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["code"] == "DUPLICATE_APPLICATION"


@pytest.mark.asyncio
async def test_get_my_applications(client: AsyncClient):
    _, job_id = await create_studio_and_job(client)
    instructor_token = await create_instructor_user(client, "mine")

    # Apply
    await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )

    # Get my applications
    response = await client.get(
        "/api/v1/applications/me",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_withdraw_application(client: AsyncClient):
    _, job_id = await create_studio_and_job(client)
    instructor_token = await create_instructor_user(client, "withdraw")

    # Apply
    apply_response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )
    application_id = apply_response.json()["id"]

    # Withdraw
    response = await client.post(
        f"/api/v1/applications/{application_id}/withdraw",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "withdrawn"


@pytest.mark.asyncio
async def test_studio_cannot_apply(client: AsyncClient):
    studio_token, job_id = await create_studio_and_job(client)

    response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={},
    )
    assert response.status_code == 403
