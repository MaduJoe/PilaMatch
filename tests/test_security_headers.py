"""Security Headers and CORS Tests

Integration tests verifying that security middleware is correctly applied:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- CORS does not allow PATCH or TRACE methods

Uses the same async test client pattern as other integration tests.

Test naming convention: test_{scenario}_{expected_result}
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# 1. X-Content-Type-Options: nosniff
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_has_x_content_type_options(
    client: AsyncClient,
):
    """The /health endpoint response includes X-Content-Type-Options: nosniff."""
    response = await client.get("/health")

    assert response.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_api_endpoint_has_x_content_type_options(
    client: AsyncClient,
):
    """An API endpoint response includes X-Content-Type-Options: nosniff."""
    response = await client.get("/api/v1/job-posts")

    assert response.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_auth_endpoint_has_x_content_type_options(
    client: AsyncClient,
):
    """The auth login endpoint response includes X-Content-Type-Options: nosniff."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "wrong"},
    )

    assert response.headers.get("x-content-type-options") == "nosniff"


# ---------------------------------------------------------------------------
# 2. X-Frame-Options: DENY
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_has_x_frame_options_deny(
    client: AsyncClient,
):
    """The /health endpoint response includes X-Frame-Options: DENY."""
    response = await client.get("/health")

    assert response.headers.get("x-frame-options") == "DENY"


@pytest.mark.asyncio
async def test_api_endpoint_has_x_frame_options_deny(
    client: AsyncClient,
):
    """An API endpoint response includes X-Frame-Options: DENY."""
    response = await client.get("/api/v1/job-posts")

    assert response.headers.get("x-frame-options") == "DENY"


@pytest.mark.asyncio
async def test_auth_endpoint_has_x_frame_options_deny(
    client: AsyncClient,
):
    """The auth endpoint response includes X-Frame-Options: DENY."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "wrong"},
    )

    assert response.headers.get("x-frame-options") == "DENY"


# ---------------------------------------------------------------------------
# 3. X-XSS-Protection: 1; mode=block
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_has_x_xss_protection(
    client: AsyncClient,
):
    """The /health endpoint response includes X-XSS-Protection: 1; mode=block."""
    response = await client.get("/health")

    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_api_endpoint_has_x_xss_protection(
    client: AsyncClient,
):
    """An API endpoint response includes X-XSS-Protection: 1; mode=block."""
    response = await client.get("/api/v1/job-posts")

    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_auth_endpoint_has_x_xss_protection(
    client: AsyncClient,
):
    """The auth endpoint response includes X-XSS-Protection: 1; mode=block."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "wrong"},
    )

    assert response.headers.get("x-xss-protection") == "1; mode=block"


# ---------------------------------------------------------------------------
# 4. Referrer-Policy: strict-origin-when-cross-origin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_has_referrer_policy(
    client: AsyncClient,
):
    """The /health endpoint response includes Referrer-Policy: strict-origin-when-cross-origin."""
    response = await client.get("/health")

    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_api_endpoint_has_referrer_policy(
    client: AsyncClient,
):
    """An API endpoint response includes Referrer-Policy."""
    response = await client.get("/api/v1/job-posts")

    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# 5. All security headers present on a single response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_security_headers_present_on_single_response(
    client: AsyncClient,
):
    """A single API response includes all 4 required security headers."""
    response = await client.get("/health")

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# 6. Security headers on error responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_security_headers_on_404_response(
    client: AsyncClient,
):
    """Security headers are present even on 404 Not Found responses."""
    response = await client.get("/api/v1/nonexistent-endpoint")

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_security_headers_on_403_response(
    client: AsyncClient,
):
    """Security headers are present even on 403 Forbidden responses."""
    response = await client.get("/api/v1/auth/me")

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


@pytest.mark.asyncio
async def test_security_headers_on_post_error_response(
    client: AsyncClient,
):
    """Security headers are present on POST error responses."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={"invalid": "data"},
    )

    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"


# ---------------------------------------------------------------------------
# 7. CORS -- allowed methods do not include PATCH or TRACE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_does_not_allow_patch_method(
    client: AsyncClient,
):
    """CORS preflight for PATCH method should not be in the allowed methods."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "PATCH" not in allow_methods


@pytest.mark.asyncio
async def test_cors_does_not_allow_trace_method(
    client: AsyncClient,
):
    """CORS preflight for TRACE method should not be in the allowed methods."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "TRACE",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "TRACE" not in allow_methods


@pytest.mark.asyncio
async def test_cors_allows_get_method(
    client: AsyncClient,
):
    """CORS preflight for GET method is allowed."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "GET" in allow_methods


@pytest.mark.asyncio
async def test_cors_allows_post_method(
    client: AsyncClient,
):
    """CORS preflight for POST method is allowed."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


@pytest.mark.asyncio
async def test_cors_allows_delete_method(
    client: AsyncClient,
):
    """CORS preflight for DELETE method is allowed."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_methods = response.headers.get("access-control-allow-methods", "")
    assert "DELETE" in allow_methods


# ---------------------------------------------------------------------------
# 8. CORS -- origin restrictions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_allows_configured_origin(
    client: AsyncClient,
):
    """CORS allows requests from a configured origin (localhost:8501)."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.headers.get("access-control-allow-origin") == "http://localhost:8501"


@pytest.mark.asyncio
async def test_cors_rejects_unknown_origin(
    client: AsyncClient,
):
    """CORS does not allow requests from an unconfigured origin."""
    response = await client.options(
        "/api/v1/job-posts",
        headers={
            "Origin": "http://evil-site.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    # Either the origin is not in the response, or access-control-allow-origin is not set
    allow_origin = response.headers.get("access-control-allow-origin", "")
    assert "evil-site.com" not in allow_origin


# ---------------------------------------------------------------------------
# 9. CORS -- allowed headers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cors_allows_authorization_header(
    client: AsyncClient,
):
    """CORS allows the Authorization header for Bearer token auth."""
    response = await client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    allow_headers = response.headers.get("access-control-allow-headers", "")
    assert "authorization" in allow_headers.lower()


@pytest.mark.asyncio
async def test_cors_allows_content_type_header(
    client: AsyncClient,
):
    """CORS allows the Content-Type header for JSON requests."""
    response = await client.options(
        "/api/v1/auth/signup",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    allow_headers = response.headers.get("access-control-allow-headers", "")
    assert "content-type" in allow_headers.lower()
