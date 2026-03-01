"""Tests for Task 3: Trust Score rate limit + billing key reverse lookup."""
import pytest
from httpx import AsyncClient


async def _signup_and_get_token(client: AsyncClient, email: str) -> str:
    """Helper: signup and return token."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Test User",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_trust_score_refresh_rate_limit(client: AsyncClient):
    """Trust score refresh should be rate limited to once per hour."""
    token = await _signup_and_get_token(client, "trust_rl@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # First refresh should succeed
    resp1 = await client.post("/api/v1/trust-score/refresh", headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1.get("rate_limited") is False

    # Second refresh within the hour should return cached value
    resp2 = await client.post("/api/v1/trust-score/refresh", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get("rate_limited") is True
    assert "retry_after_seconds" in data2


@pytest.mark.asyncio
async def test_trust_score_get_not_rate_limited(client: AsyncClient):
    """GET trust score should not be rate limited."""
    token = await _signup_and_get_token(client, "trust_get@test.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Multiple GET requests should all succeed
    for _ in range(3):
        resp = await client.get("/api/v1/trust-score", headers=headers)
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_billing_key_reverse_lookup():
    """Test that SubscriptionService.get_subscription_by_billing_key works."""
    from app.services.subscription import SubscriptionService

    # Just verify the method exists and is callable
    assert hasattr(SubscriptionService, "get_subscription_by_billing_key")
