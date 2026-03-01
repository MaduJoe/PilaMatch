import pytest
from httpx import AsyncClient
from datetime import date


async def setup_contract(client: AsyncClient) -> dict:
    """Create a complete setup with confirmed contract."""
    # Create studio
    studio_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_pay_{id(client)}@test.com",
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
            "title": "Payment Test Job",
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
            "email": f"instructor_pay_{id(client)}@test.com",
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

    # Apply
    apply_response = await client.post(
        f"/api/v1/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={},
    )
    application_id = apply_response.json()["id"]

    # Create and accept offer
    offer_response = await client.post(
        "/api/v1/offers",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "application_id": application_id,
            "proposed_rate": 50000,
        },
    )
    offer_id = offer_response.json()["id"]

    await client.post(
        f"/api/v1/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )

    # Create contract
    contract_response = await client.post(
        f"/api/v1/contracts/from-offer/{offer_id}",
        headers={"Authorization": f"Bearer {studio_token}"},
    )
    contract_id = contract_response.json()["id"]

    return {
        "studio_token": studio_token,
        "instructor_token": instructor_token,
        "contract_id": contract_id,
    }


@pytest.mark.asyncio
async def test_initialize_payment(client: AsyncClient):
    setup = await setup_contract(client)

    response = await client.post(
        f"/api/v1/contracts/{setup['contract_id']}/payments",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert "amount" in data
    assert float(data["amount"]) > 0


@pytest.mark.asyncio
async def test_payment_webhook_success(client: AsyncClient):
    setup = await setup_contract(client)

    # Initialize payment
    init_response = await client.post(
        f"/api/v1/contracts/{setup['contract_id']}/payments",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    order_id = init_response.json()["order_id"]

    # Simulate webhook
    response = await client.post(
        "/api/v1/payments/webhook",
        json={
            "eventType": "PAYMENT_STATUS_CHANGED",
            "data": {
                "paymentKey": "test_payment_key_123",
                "orderId": order_id,
                "status": "DONE",
            },
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_payment_idempotency(client: AsyncClient):
    setup = await setup_contract(client)

    # Initialize payment twice
    response1 = await client.post(
        f"/api/v1/contracts/{setup['contract_id']}/payments",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )

    response2 = await client.post(
        f"/api/v1/contracts/{setup['contract_id']}/payments",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )

    # Should return same order_id
    assert response1.json()["order_id"] == response2.json()["order_id"]


@pytest.mark.asyncio
async def test_instructor_cannot_initialize_payment(client: AsyncClient):
    setup = await setup_contract(client)

    response = await client.post(
        f"/api/v1/contracts/{setup['contract_id']}/payments",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
    )
    assert response.status_code == 403
