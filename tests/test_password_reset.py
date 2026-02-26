"""Tests for password reset API (Task 2)."""
import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str = "reset@test.com") -> str:
    """Helper: signup and return token."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "oldpass123",
            "role": "instructor",
            "display_name": "Reset Test",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_forgot_password_existing_email(client: AsyncClient):
    """Forgot password for existing user should return 200."""
    await _signup(client, "forgot@test.com")
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "forgot@test.com"},
    )
    assert response.status_code == 200
    assert "이메일" in response.json()["message"]


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_email(client: AsyncClient):
    """Forgot password for nonexistent email should still return 200 (no info leak)."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "noone@test.com"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_success(client: AsyncClient):
    """Full flow: signup -> forgot password -> reset with new password -> login."""
    await _signup(client, "fullreset@test.com")

    # Generate reset token directly
    from app.core.security import create_password_reset_token
    from app.services.auth import AuthService
    from sqlalchemy.ext.asyncio import AsyncSession

    # Get the user_id via login check
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "fullreset@test.com", "password": "oldpass123"},
    )
    assert login_resp.status_code == 200

    # We need the user ID - get it from /me
    token = login_resp.json()["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = str(me_resp.json()["user"]["id"])

    # Create reset token
    reset_token = create_password_reset_token(user_id)

    # Reset password
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "newpass456"},
    )
    assert response.status_code == 200
    assert "성공" in response.json()["message"]

    # Login with new password should work
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "fullreset@test.com", "password": "newpass456"},
    )
    assert new_login.status_code == 200

    # Login with old password should fail
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "fullreset@test.com", "password": "oldpass123"},
    )
    assert old_login.status_code == 401


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient):
    """Reset with invalid token should fail."""
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid.token.here", "new_password": "newpass456"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_reset_password_token_reuse(client: AsyncClient):
    """Reset token should only work once."""
    await _signup(client, "reuse@test.com")

    # Get user ID
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "reuse@test.com", "password": "oldpass123"},
    )
    token = login_resp.json()["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = str(me_resp.json()["user"]["id"])

    # Create reset token
    from app.core.security import create_password_reset_token
    reset_token = create_password_reset_token(user_id)

    # First use - should succeed
    resp1 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "newpass111"},
    )
    assert resp1.status_code == 200

    # Second use - should fail
    resp2 = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "newpass222"},
    )
    assert resp2.status_code == 400
    assert resp2.json()["detail"]["code"] == "TOKEN_USED"


@pytest.mark.asyncio
async def test_email_service_mock():
    """Test EmailService in mock mode."""
    from app.services.email import EmailService

    service = EmailService()
    # Should not raise
    await service.send_password_reset("test@test.com", "fake-token")
    await service.send_account_deletion_notice("test@test.com")
