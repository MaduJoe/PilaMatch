"""Tests for HSTS header and global exception handler.

Verifies:
1. HSTS (Strict-Transport-Security) header behavior based on DEBUG setting.
2. Global exception handler returns safe 500 responses without internal details.
3. All security headers are present across different response types.
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# 1. HSTS Header Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hsts_header_behavior(client: AsyncClient):
    """HSTS header presence depends on DEBUG setting."""
    from app.core.config import settings

    response = await client.get("/health")
    assert response.status_code == 200

    if not settings.DEBUG:
        hsts = response.headers.get("strict-transport-security")
        assert hsts is not None
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts
    else:
        # In DEBUG mode, HSTS may or may not be present (dev-safe behavior)
        pass


@pytest.mark.asyncio
async def test_hsts_max_age_value(client: AsyncClient):
    """HSTS max-age should be at least 1 year (31536000 seconds) in production."""
    from app.core.config import settings

    if settings.DEBUG:
        pytest.skip("HSTS not applied in DEBUG mode")

    response = await client.get("/health")
    hsts = response.headers.get("strict-transport-security", "")
    # Extract max-age value
    for part in hsts.split(";"):
        part = part.strip()
        if part.startswith("max-age="):
            max_age = int(part.split("=")[1])
            assert max_age >= 31536000


# ---------------------------------------------------------------------------
# 2. Security Headers on Various Response Codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_headers_on_200(client: AsyncClient):
    """All security headers present on successful (200) response."""
    response = await client.get("/health")
    assert response.status_code == 200

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert (
        response.headers.get("referrer-policy")
        == "strict-origin-when-cross-origin"
    )


@pytest.mark.asyncio
async def test_security_headers_on_401(client: AsyncClient):
    """Security headers present on 401 Unauthorized response."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_security_headers_on_422(client: AsyncClient):
    """Security headers present on 422 Validation Error response."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"invalid": "data"},
    )
    assert response.status_code == 422

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_security_headers_on_404(client: AsyncClient):
    """Security headers present on 404 Not Found response."""
    response = await client.get("/api/v1/nonexistent-endpoint-12345")
    assert response.status_code in (404, 405)

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


# ---------------------------------------------------------------------------
# 3. Global Exception Handler Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_exception_handler_exists():
    """The global exception handler is registered on the app."""
    from app.main import app

    # FastAPI stores exception handlers in the exception_handlers dict
    assert Exception in app.exception_handlers


@pytest.mark.asyncio
async def test_global_exception_handler_returns_safe_error():
    """Global exception handler returns safe 500 response format."""
    from app.main import global_exception_handler
    from unittest.mock import MagicMock, AsyncMock
    from starlette.requests import Request

    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.method = "GET"
    mock_request.url = MagicMock()
    mock_request.url.path = "/test"

    # Simulate an unhandled exception
    exc = RuntimeError("Database connection failed at 10.0.0.5:5432")

    response = await global_exception_handler(mock_request, exc)

    assert response.status_code == 500
    import json

    body = json.loads(response.body.decode())
    assert body["detail"]["code"] == "INTERNAL_ERROR"
    # The error message should NOT contain internal details
    assert "10.0.0.5" not in body["detail"]["message"]
    assert "Database" not in body["detail"]["message"]


@pytest.mark.asyncio
async def test_global_exception_handler_no_stack_trace():
    """Global exception handler does not leak stack trace."""
    from app.main import global_exception_handler
    from unittest.mock import MagicMock

    mock_request = MagicMock()
    mock_request.method = "POST"
    mock_request.url = MagicMock()
    mock_request.url.path = "/api/v1/payments"

    exc = ValueError("Invalid payment amount: user tried -50000")

    response = await global_exception_handler(mock_request, exc)

    assert response.status_code == 500
    import json

    body = json.loads(response.body.decode())
    # Should not leak the ValueError message
    assert "Invalid payment amount" not in body["detail"]["message"]
    assert "-50000" not in body["detail"]["message"]
    # Should return the generic Korean error message
    assert "서버 내부 오류" in body["detail"]["message"]
