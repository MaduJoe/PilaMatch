import pytest
from httpx import AsyncClient
from datetime import date


async def setup_application(client: AsyncClient) -> dict:
    """Create studio, job, instructor, and application. Return all tokens and IDs."""
    # Create studio
    studio_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_oc_{id(client)}@test.com",
            "password": "TestPass123",
            "role": "studio",
            "business_name": "Test Studio",
        },
    )
    studio_token = studio_response.json()["access_token"]

    # Create job
    job_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "title": "Test Job",
            "category": "pilates",
            "job_type": "substitute",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "hourly_rate": 50000,
        },
    )
    job_id = job_response.json()["id"]

    # Create instructor
    instructor_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"instructor_oc_{id(client)}@test.com",
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Test Instructor",
        },
    )
    instructor_token = instructor_response.json()["access_token"]

    # Fill profile to pass 70% completeness check
    await client.put(
        "/api/v1/instructors/me",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={
            "display_name": "Test Instructor",
            "bio": "Experienced pilates instructor with 5 years of teaching.",
            "categories": ["pilates"],
            "available_regions": ["seoul"],
            "experience_years": 5,
            "hourly_rate_min": 30000,
            "hourly_rate_max": 60000,
        },
    )

    # Get instructor profile ID
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    instructor_id = me_response.json()["profile_id"]

    # Apply
    apply_response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )
    application_id = apply_response.json()["id"]

    return {
        "studio_token": studio_token,
        "instructor_token": instructor_token,
        "job_id": job_id,
        "application_id": application_id,
        "instructor_id": instructor_id,
    }


@pytest.mark.asyncio
async def test_create_offer(client: AsyncClient):
    setup = await setup_application(client)

    response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
            "message": "We would like to offer you this position!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert float(data["proposed_rate"]) == 55000


@pytest.mark.asyncio
async def test_accept_offer(client: AsyncClient):
    setup = await setup_application(client)

    # Create offer
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
        },
    )
    offer_id = offer_response.json()["id"]

    # Accept offer
    response = await client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_reject_offer(client: AsyncClient):
    setup = await setup_application(client)

    # Create offer
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
        },
    )
    offer_id = offer_response.json()["id"]

    # Reject offer
    response = await client.post(
        f"/api/v1/offers/{offer_id}/reject",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


@pytest.mark.asyncio
async def test_create_contract_from_offer(client: AsyncClient):
    setup = await setup_application(client)

    # Create and accept offer
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
        },
    )
    offer_id = offer_response.json()["id"]

    await client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )

    # Create contract
    response = await client.post(
        f"/api/v1/contracts/from-offer/{offer_id}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["offer_id"] == offer_id


@pytest.mark.asyncio
async def test_single_signature_keeps_confirmed_status(client: AsyncClient):
    """Dual-signature flow: a single party signing keeps contract in confirmed status."""
    setup = await setup_application(client)

    # Create and accept offer, then contract
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
        },
    )
    offer_id = offer_response.json()["id"]

    await client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )

    contract_response = await client.post(
        f"/api/v1/contracts/from-offer/{offer_id}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    contract_id = contract_response.json()["id"]

    # Studio signs - contract should remain in confirmed (needs both signatures)
    response = await client.post(
        f"/api/v1/contracts/{contract_id}/set-in-progress",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"  # Still confirmed - waiting for instructor signature


@pytest.mark.asyncio
async def test_cancel_contract_requires_reason(client: AsyncClient):
    setup = await setup_application(client)

    # Create and accept offer, then contract
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "application_id": setup["application_id"],
            "proposed_rate": 55000,
        },
    )
    offer_id = offer_response.json()["id"]

    await client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )

    contract_response = await client.post(
        f"/api/v1/contracts/from-offer/{offer_id}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    contract_id = contract_response.json()["id"]

    # Cancel with reason
    response = await client.post(
        f"/api/v1/contracts/{contract_id}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={"reason": "Schedule conflict"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancellation_reason"] == "Schedule conflict"
