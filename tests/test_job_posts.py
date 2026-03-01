import pytest
from httpx import AsyncClient
from datetime import date, time


async def create_studio_user(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_{id(client)}@test.com",
            "password": "TestPass123",
            "role": "studio",
            "business_name": "Test Studio",
        },
    )
    return response.json()["access_token"]


async def create_instructor_user(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"instructor_{id(client)}@test.com",
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Test Instructor",
        },
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_job_post(client: AsyncClient):
    token = await create_studio_user(client)

    response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Pilates Instructor Needed",
            "description": "Looking for experienced instructor",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
            "region": "Seoul",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Pilates Instructor Needed"
    assert data["category"] == "pilates"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_create_job_post_instructor_forbidden(client: AsyncClient):
    token = await create_instructor_user(client)

    response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_job_posts(client: AsyncClient):
    token = await create_studio_user(client)

    # Create a job post
    await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Job",
            "category": "yoga",
            "job_type": "regular",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 40000,
        },
    )

    # List job posts
    response = await client.get("/api/v1/job-posts")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_job_posts_filter_category(client: AsyncClient):
    token = await create_studio_user(client)

    # Create pilates job
    await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Pilates Job",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )

    # Filter by yoga (should not include pilates)
    response = await client.get("/api/v1/job-posts?category=yoga")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["category"] == "yoga"


@pytest.mark.asyncio
async def test_get_job_post(client: AsyncClient):
    token = await create_studio_user(client)

    # Create job post
    create_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Get Test Job",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    job_id = create_response.json()["id"]

    # Get job post
    response = await client.get(f"/api/v1/job-posts/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["title"] == "Get Test Job"


@pytest.mark.asyncio
async def test_update_job_post(client: AsyncClient):
    token = await create_studio_user(client)

    # Create job post
    create_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Original Title",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    job_id = create_response.json()["id"]

    # Update job post
    response = await client.put(
        f"/api/v1/job-posts/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Updated Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_job_post(client: AsyncClient):
    token = await create_studio_user(client)

    # Create job post
    create_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "To Delete",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    job_id = create_response.json()["id"]

    # Delete job post
    response = await client.delete(
        f"/api/v1/job-posts/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/job-posts/{job_id}")
    assert get_response.status_code == 404
