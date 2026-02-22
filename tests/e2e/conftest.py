"""
E2E test fixtures for StudioBridge.

Requires running services: docker-compose up -d
"""

import os
import uuid
from typing import Optional

import httpx
import pytest

from tests.e2e.helpers.api_helpers import (
    create_test_user,
    complete_instructor_profile,
    complete_studio_profile,
    create_job_post,
)

FRONTEND_URL = os.getenv("E2E_FRONTEND_URL", "http://localhost:8501")
BACKEND_URL = os.getenv("E2E_BACKEND_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api/v1"


@pytest.fixture(scope="session")
def services_up():
    """Skip all E2E tests if backend/frontend are not running."""
    try:
        httpx.get(f"{BACKEND_URL}/health", timeout=5)
    except httpx.ConnectError:
        pytest.skip("Backend not running. Start with: docker-compose up -d")
    try:
        httpx.get(f"{FRONTEND_URL}/_stcore/health", timeout=5)
    except httpx.ConnectError:
        pytest.skip("Frontend not running. Start with: docker-compose up -d")


@pytest.fixture(scope="session")
def base_url() -> str:
    return FRONTEND_URL


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul",
    }


@pytest.fixture(scope="session")
def api_client():
    """HTTP client pointed at the backend API."""
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client


@pytest.fixture
def instructor_credentials():
    """Generate unique instructor credentials for each test."""
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"e2e_inst_{uid}@test.com",
        "password": "testpass123",
        "role": "instructor",
        "display_name": f"E2E강사{uid}",
    }


@pytest.fixture
def studio_credentials():
    """Generate unique studio credentials for each test."""
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"e2e_studio_{uid}@test.com",
        "password": "testpass123",
        "role": "studio",
        "business_name": f"E2E스튜디오{uid}",
    }


@pytest.fixture
def user_factory(api_client):
    """Factory fixture to create users via API.

    Usage:
        user = user_factory("instructor")
        user = user_factory("studio", email="custom@test.com")

    Returns dict with: access_token, email, password, role, display_name/business_name
    """

    def _create(
        role: str,
        *,
        email: Optional[str] = None,
        password: str = "testpass123",
    ) -> dict:
        return create_test_user(
            api_client, role, email=email, password=password
        )

    return _create


@pytest.fixture
def authenticated_api(api_client):
    """Helper to make authenticated API calls.

    Usage:
        resp = authenticated_api("POST", "/endpoint", token, json={"key": "val"})
    """

    def _call(
        method: str, endpoint: str, token: str, **kwargs
    ) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return api_client.request(method, endpoint, headers=headers, **kwargs)

    return _call


@pytest.fixture
def setup_full_flow(user_factory, api_client):
    """Set up the full happy path prerequisites via API.

    Creates instructor + studio, completes profiles, creates a job post.
    Returns dict with all created data for use in browser tests.
    """
    # Create users
    instructor = user_factory("instructor")
    studio = user_factory("studio")

    # Complete profiles
    inst_profile = complete_instructor_profile(
        api_client, instructor["access_token"]
    )
    studio_profile = complete_studio_profile(
        api_client, studio["access_token"]
    )

    # Create job post
    job = create_job_post(api_client, studio["access_token"])

    return {
        "instructor": instructor,
        "studio": studio,
        "instructor_profile": inst_profile,
        "studio_profile": studio_profile,
        "job_post": job,
    }
