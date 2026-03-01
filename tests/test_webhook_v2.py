import pytest
import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from datetime import date
from uuid import uuid4


async def setup_contract_with_payment(client: AsyncClient) -> dict:
    """Create a full setup with a completed payment for webhook testing."""
    unique = uuid4().hex[:8]

    # Create studio
    studio_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"studio_wh_{unique}@test.com",
            "password": "TestPass123",
            "role": "studio",
            "business_name": "Webhook Test Studio",
        },
    )
    studio_token = studio_response.json()["access_token"]

    # Create job
    job_response = await client.post(
        "/api/v1/job-posts",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "title": "Webhook Test Job",
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
            "email": f"instructor_wh_{unique}@test.com",
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Webhook Test Instructor",
        },
    )
    instructor_token = instructor_response.json()["access_token"]

    # Fill profile
    await client.put(
        "/api/v1/instructors/me",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={
            "display_name": "Webhook Test Instructor",
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
    order_id = init_response.json()["order_id"]
    amount = init_response.json()["amount"]

    # Confirm payment
    payment_key = f"test_pk_wh_{unique}"
    confirm_response = await client.post(
        "/api/v1/payments/confirm",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "payment_key": payment_key,
            "order_id": order_id,
            "amount": amount,
        },
    )
    payment_id = confirm_response.json()["id"]

    return {
        "studio_token": studio_token,
        "payment_id": payment_id,
        "payment_key": payment_key,
        "order_id": order_id,
        "amount": float(amount),
    }


# --- Webhook v2 signature verification tests ---


@pytest.mark.asyncio
async def test_webhook_v2_headers_accepted(client: AsyncClient):
    """Test that webhook with v2 headers is accepted (no secret = skip verification)."""
    setup = await setup_contract_with_payment(client)
    now = datetime.now(timezone.utc).isoformat()
    transmission_id = f"txid_{uuid4().hex[:12]}"

    payload = {
        "eventType": "PAYMENT_STATUS_CHANGED",
        "data": {
            "paymentKey": setup["payment_key"],
            "status": "DONE",
        },
    }

    response = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-signature": "dummy_signature",
            "tosspayments-webhook-transmission-time": now,
            "tosspayments-webhook-transmission-id": transmission_id,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_v1_fallback(client: AsyncClient):
    """Test that webhook with legacy v1 header still works."""
    setup = await setup_contract_with_payment(client)

    payload = {
        "eventType": "PAYMENT_STATUS_CHANGED",
        "data": {
            "paymentKey": setup["payment_key"],
            "status": "DONE",
        },
    }

    response = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={"X-Toss-Signature": "dummy_signature"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_deduplication(client: AsyncClient):
    """Test that duplicate webhooks with same transmission_id are skipped."""
    setup = await setup_contract_with_payment(client)
    now = datetime.now(timezone.utc).isoformat()
    transmission_id = f"dedup_{uuid4().hex[:12]}"

    payload = {
        "eventType": "PAYMENT_STATUS_CHANGED",
        "data": {
            "paymentKey": setup["payment_key"],
            "status": "DONE",
        },
    }

    # First webhook
    response1 = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-transmission-id": transmission_id,
            "tosspayments-webhook-transmission-time": now,
        },
    )
    assert response1.status_code == 200

    # Duplicate webhook with same transmission_id
    response2 = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-transmission-id": transmission_id,
            "tosspayments-webhook-transmission-time": now,
        },
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_webhook_cancel_status_changed(client: AsyncClient):
    """Test CANCEL_STATUS_CHANGED event updates payment amounts."""
    setup = await setup_contract_with_payment(client)
    now = datetime.now(timezone.utc).isoformat()
    cancel_amount = round(setup["amount"] / 2)

    payload = {
        "eventType": "CANCEL_STATUS_CHANGED",
        "data": {
            "paymentKey": setup["payment_key"],
            "status": "PARTIAL_CANCELED",
            "cancels": [
                {
                    "cancelAmount": cancel_amount,
                    "cancelReason": "Webhook cancel test",
                    "transactionKey": "txn_test_123",
                },
            ],
        },
    }

    response = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-transmission-id": f"cancel_{uuid4().hex[:12]}",
            "tosspayments-webhook-transmission-time": now,
        },
    )
    assert response.status_code == 200

    # Verify payment was updated
    detail = await client.get(
        f"/api/v1/payments/{setup['payment_id']}",
        headers={"Authorization": f"Bearer {setup['studio_token']}"},
    )
    assert detail.status_code == 200
    data = detail.json()
    assert data["status"] == "partially_cancelled"
    assert float(data["cancelled_amount"]) == cancel_amount


@pytest.mark.asyncio
async def test_webhook_unknown_payment_key(client: AsyncClient):
    """Test webhook with unknown payment_key is handled gracefully."""
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "eventType": "PAYMENT_STATUS_CHANGED",
        "data": {
            "paymentKey": "unknown_key_123",
            "status": "DONE",
        },
    }

    response = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-transmission-id": f"unknown_{uuid4().hex[:12]}",
            "tosspayments-webhook-transmission-time": now,
        },
    )
    # Should still return 200 (no error, just no-op)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_webhook_no_payment_key(client: AsyncClient):
    """Test webhook without paymentKey in data is handled gracefully."""
    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "eventType": "PAYMENT_STATUS_CHANGED",
        "data": {},
    }

    response = await client.post(
        "/api/v1/payments/webhook",
        json=payload,
        headers={
            "tosspayments-webhook-transmission-id": f"nopk_{uuid4().hex[:12]}",
            "tosspayments-webhook-transmission-time": now,
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_verify_webhook_signature_v2():
    """Unit test for v2 signature verification logic."""
    from app.services.payment import PaymentService
    from unittest.mock import MagicMock, patch

    db = MagicMock()
    service = PaymentService(db)

    secret = "test_webhook_secret_key"
    transmission_id = "txid_abc123"
    transmission_time = datetime.now(timezone.utc).isoformat()
    payload = b'{"eventType":"PAYMENT_STATUS_CHANGED","data":{}}'

    # Calculate expected signature
    message = f"{transmission_id}.{transmission_time}.{payload.decode()}"
    expected_sig = hmac.new(
        secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.TOSS_WEBHOOK_SECRET = secret

        # Valid signature
        assert service.verify_webhook_signature(
            payload, expected_sig, transmission_time, transmission_id
        ) is True

        # Invalid signature
        assert service.verify_webhook_signature(
            payload, "wrong_signature", transmission_time, transmission_id
        ) is False


@pytest.mark.asyncio
async def test_verify_webhook_signature_replay_prevention():
    """Unit test for replay attack prevention (>5 min old webhook)."""
    from app.services.payment import PaymentService
    from unittest.mock import MagicMock, patch

    db = MagicMock()
    service = PaymentService(db)

    secret = "test_webhook_secret_key"
    transmission_id = "txid_old123"
    # 10 minutes ago
    old_time = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    payload = b'{"test": true}'

    message = f"{transmission_id}.{old_time}.{payload.decode()}"
    sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.TOSS_WEBHOOK_SECRET = secret

        # Should be rejected due to replay prevention
        assert service.verify_webhook_signature(
            payload, sig, old_time, transmission_id
        ) is False


@pytest.mark.asyncio
async def test_verify_webhook_no_secret_skips():
    """Unit test: when no webhook secret is configured, verification is skipped."""
    from app.services.payment import PaymentService
    from unittest.mock import MagicMock, patch

    db = MagicMock()
    service = PaymentService(db)

    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.TOSS_WEBHOOK_SECRET = None

        assert service.verify_webhook_signature(
            b"anything", "any_sig", "any_time", "any_id"
        ) is True
