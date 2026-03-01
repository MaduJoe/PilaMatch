"""Tests for account deletion API (Task 1)."""
import pytest
from httpx import AsyncClient


async def _signup_and_get_token(client: AsyncClient, email: str = "delete@test.com") -> tuple[str, str]:
    """Helper: signup and return (token, email)."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Delete Test",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"], email


@pytest.mark.asyncio
async def test_delete_account_success(client: AsyncClient):
    """Account deletion with valid password should succeed."""
    token, _ = await _signup_and_get_token(client)

    response = await client.request(
        "DELETE",
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "TestPass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "deletion_scheduled_at" in data
    assert "계정 삭제가 예약" in data["message"]


@pytest.mark.asyncio
async def test_delete_account_wrong_password(client: AsyncClient):
    """Account deletion with wrong password should fail."""
    token, _ = await _signup_and_get_token(client, "wrongpw@test.com")

    response = await client.request(
        "DELETE",
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "wrongpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PASSWORD"


@pytest.mark.asyncio
async def test_delete_account_invalidates_token(client: AsyncClient):
    """After deletion, the token should be blacklisted."""
    token, _ = await _signup_and_get_token(client, "invalidate@test.com")

    # Delete account
    response = await client.request(
        "DELETE",
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "TestPass123"},
    )
    assert response.status_code == 200

    # Try to use the same token — should fail
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_cancel_deletion_no_pending(client: AsyncClient):
    """Cancel deletion when no deletion is pending should fail."""
    token, _ = await _signup_and_get_token(client, "nopending@test.com")

    response = await client.post(
        "/api/v1/auth/users/me/cancel-deletion",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "NO_PENDING_DELETION"


@pytest.mark.asyncio
async def test_account_deletion_schema():
    """Test that schemas validate correctly."""
    from app.schemas.auth import AccountDeletionRequest, AccountDeletionResponse
    from datetime import datetime

    req = AccountDeletionRequest(password="test123")
    assert req.password == "test123"

    resp = AccountDeletionResponse(
        message="test", deletion_scheduled_at=datetime.utcnow()
    )
    assert resp.message == "test"
