"""Tests for password complexity validation.

The signup schema enforces password rules:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit

These tests verify that the Pydantic field_validator on SignupRequest.password
rejects non-compliant passwords with HTTP 422.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_password_no_uppercase_rejected(client: AsyncClient):
    """Password without uppercase letter is rejected."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_upper@test.com",
            "password": "testpass1",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_no_lowercase_rejected(client: AsyncClient):
    """Password without lowercase letter is rejected."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_lower@test.com",
            "password": "TESTPASS1",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_no_digit_rejected(client: AsyncClient):
    """Password without digit is rejected."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_digit@test.com",
            "password": "TestPasss",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_too_short_rejected(client: AsyncClient):
    """Password shorter than 8 chars is rejected."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_short@test.com",
            "password": "Ab1",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_valid_accepted(client: AsyncClient):
    """Valid password (uppercase + lowercase + digit + 8+ chars) is accepted."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "valid_pwd@test.com",
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_signup_password_only_digits_rejected(client: AsyncClient):
    """Password with only digits is rejected."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test_onlydigit@test.com",
            "password": "12345678",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_boundary_8_chars_accepted(client: AsyncClient):
    """Password at exactly 8 characters with full complexity is accepted."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "boundary@test.com",
            "password": "Abcdef1x",
            "role": "instructor",
            "display_name": "Test",
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_password_validator_unit():
    """Unit test: _validate_password_complexity raises for invalid passwords."""
    from app.schemas.auth import _validate_password_complexity

    # Valid
    assert _validate_password_complexity("TestPass1") == "TestPass1"

    # Missing uppercase
    with pytest.raises(ValueError, match="대문자"):
        _validate_password_complexity("testpass1")

    # Missing lowercase
    with pytest.raises(ValueError, match="소문자"):
        _validate_password_complexity("TESTPASS1")

    # Missing digit
    with pytest.raises(ValueError, match="숫자"):
        _validate_password_complexity("TestPasss")
