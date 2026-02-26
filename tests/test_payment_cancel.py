import pytest
from httpx import AsyncClient
from datetime import date
from uuid import uuid4


async def setup_contract_with_payment(client: AsyncClient) -> dict:
    """Create a full setup: studio, instructor, contract, and completed payment."""
    unique = uuid4().hex[:8]

    # Create studio
    studio_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_cancel_{unique}@test.com",
            "password": "testpass123",
            "role": "studio",
            "business_name": "Cancel Test Studio",
        },
    )
    studio_token = studio_response.json()["access_token"]

    # Create job
    job_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "title": "Cancel Test Job",
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
            "email": f"instructor_cancel_{unique}@test.com",
            "password": "testpass123",
            "role": "instructor",
            "display_name": "Cancel Test Instructor",
        },
    )
    instructor_token = instructor_response.json()["access_token"]

    # Fill profile
    await client.put(
        "/api/v1/instructors/me",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={
            "display_name": "Cancel Test Instructor",
            "bio": "Experienced instructor for testing.",
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
        json={"application_id": application_id, "proposed_rate": 50000},
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

    # Initialize payment
    init_response = await client.post(
        f"/api/v1/contracts/{contract_id}/payments",
        headers={"Authorization": f"Bearer {studio_token}"},
    )
    init_data = init_response.json()
    order_id = init_data["order_id"]
    amount = init_data["amount"]

    # Confirm payment (mock mode - no TOSS_SECRET_KEY)
    confirm_response = await client.post(
        "/api/v1/payments/confirm",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "payment_key": f"test_pk_{unique}",
            "order_id": order_id,
            "amount": amount,
        },
    )
    payment_data = confirm_response.json()
    payment_id = payment_data["id"]

    return {
        "studio_token": studio_token,
        "instructor_token": instructor_token,
        "contract_id": contract_id,
        "payment_id": payment_id,
        "amount": float(amount),
    }


@pytest.mark.asyncio
async def test_full_cancel(client: AsyncClient):
    """Test full payment cancellation."""
    setup = await setup_contract_with_payment(client)

    response = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": setup["amount"],
            "cancel_reason": "고객 요청 전액 환불",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cancel_status"] == "DONE"
    assert float(data["cancel_amount"]) == setup["amount"]

    # Verify payment detail shows REFUNDED status
    detail = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["status"] == "refunded"
    assert float(detail_data["cancelled_amount"]) == setup["amount"]
    assert len(detail_data["cancellations"]) == 1


@pytest.mark.asyncio
async def test_partial_cancel(client: AsyncClient):
    """Test partial payment cancellation."""
    setup = await setup_contract_with_payment(client)
    partial_amount = round(setup["amount"] / 2, 2)

    response = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": partial_amount,
            "cancel_reason": "부분 환불",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cancel_status"] == "DONE"
    assert float(data["cancel_amount"]) == partial_amount

    # Verify payment detail shows PARTIALLY_CANCELLED status
    detail = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["status"] == "partially_cancelled"
    assert float(detail_data["cancelled_amount"]) == partial_amount
    remaining = round(setup["amount"] - partial_amount, 2)
    assert float(detail_data["balance_amount"]) == remaining


@pytest.mark.asyncio
async def test_cancel_amount_exceeds_balance(client: AsyncClient):
    """Test cancellation fails when amount exceeds balance."""
    setup = await setup_contract_with_payment(client)

    response = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": setup["amount"] + 10000,
            "cancel_reason": "초과 금액 테스트",
        },
    )
    assert response.status_code == 400
    assert "exceeds balance" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_cancel_already_refunded(client: AsyncClient):
    """Test cancellation fails on already refunded payment."""
    setup = await setup_contract_with_payment(client)

    # Full cancel first
    await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": setup["amount"],
            "cancel_reason": "전액 환불",
        },
    )

    # Try to cancel again
    response = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": 1000,
            "cancel_reason": "추가 환불 시도",
        },
    )
    assert response.status_code == 400
    assert "already fully refunded" in response.json()["detail"]["message"]


@pytest.mark.asyncio
async def test_cancel_idempotency(client: AsyncClient):
    """Test idempotency key prevents duplicate cancellations."""
    setup = await setup_contract_with_payment(client)
    idempotency_key = f"idem_{uuid4().hex[:12]}"

    # First cancel
    response1 = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": 10000,
            "cancel_reason": "멱등성 테스트",
            "idempotency_key": idempotency_key,
        },
    )
    assert response1.status_code == 200

    # Second cancel with same idempotency key
    response2 = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": 10000,
            "cancel_reason": "멱등성 테스트",
            "idempotency_key": idempotency_key,
        },
    )
    assert response2.status_code == 200

    # Should return the same cancellation record
    assert response1.json()["id"] == response2.json()["id"]

    # Verify only one cancellation exists
    detail = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert len(detail.json()["cancellations"]) == 1


@pytest.mark.asyncio
async def test_instructor_cannot_cancel_payment(client: AsyncClient):
    """Test that instructor (non-payer) cannot cancel payment."""
    setup = await setup_contract_with_payment(client)

    response = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['instructor_token']}"},
        json={
            "cancel_amount": 10000,
            "cancel_reason": "권한 테스트",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_nonexistent_payment(client: AsyncClient):
    """Test cancellation of nonexistent payment returns 404."""
    setup = await setup_contract_with_payment(client)
    fake_id = str(uuid4())

    response = await client.post(
        f"/api/v1/payments/{fake_id}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={
            "cancel_amount": 10000,
            "cancel_reason": "존재하지 않는 결제",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_payment_detail(client: AsyncClient):
    """Test getting payment detail endpoint."""
    setup = await setup_contract_with_payment(client)

    response = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == setup["payment_id"]
    assert data["status"] == "completed"
    assert float(data["amount"]) == setup["amount"]
    assert data["cancellations"] == []


@pytest.mark.asyncio
async def test_multiple_partial_cancels(client: AsyncClient):
    """Test multiple partial cancellations adding up correctly."""
    setup = await setup_contract_with_payment(client)
    partial = round(setup["amount"] / 4, 2)

    # First partial cancel
    r1 = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={"cancel_amount": partial, "cancel_reason": "1차 부분 환불"},
    )
    assert r1.status_code == 200

    # Second partial cancel
    r2 = await client.post(
        f"/api/v1/payments/{setup['payment_id']}/cancel",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
        json={"cancel_amount": partial, "cancel_reason": "2차 부분 환불"},
    )
    assert r2.status_code == 200

    # Verify cumulative amounts
    detail = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    data = detail.json()
    assert data["status"] == "partially_cancelled"
    assert float(data["cancelled_amount"]) == round(partial * 2, 2)
    assert len(data["cancellations"]) == 2
