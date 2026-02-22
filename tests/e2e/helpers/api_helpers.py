"""
API helper utilities for E2E tests.

Provides functions to quickly set up test data via the backend API,
used by both MCP scenarios and pytest-playwright tests.
"""

import uuid
from datetime import date, timedelta
from typing import Optional

import httpx


def create_test_user(
    api_client: httpx.Client,
    role: str,
    *,
    email: Optional[str] = None,
    password: str = "testpass123",
    display_name: Optional[str] = None,
    business_name: Optional[str] = None,
) -> dict:
    """Create a user via API and return signup response with access_token.

    Returns dict with keys: access_token, token_type, email, password, role
    """
    uid = uuid.uuid4().hex[:8]
    if email is None:
        prefix = "inst" if role == "instructor" else "studio"
        email = f"e2e_{prefix}_{uid}@test.com"

    data = {"email": email, "password": password, "role": role}
    if role == "instructor":
        data["display_name"] = display_name or f"E2E강사{uid}"
    else:
        data["business_name"] = business_name or f"E2E스튜디오{uid}"

    resp = api_client.post("/auth/signup", json=data)
    resp.raise_for_status()
    result = resp.json()
    # Attach credentials for later use
    result["email"] = email
    result["password"] = password
    result["role"] = role
    if role == "instructor":
        result["display_name"] = data.get("display_name")
    else:
        result["business_name"] = data.get("business_name")
    return result


def login_user(
    api_client: httpx.Client, email: str, password: str
) -> dict:
    """Login and return response with access_token."""
    resp = api_client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    resp.raise_for_status()
    return resp.json()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_me(api_client: httpx.Client, token: str) -> dict:
    """Get current user info."""
    resp = api_client.get("/auth/me", headers=_auth_headers(token))
    resp.raise_for_status()
    return resp.json()


def complete_instructor_profile(
    api_client: httpx.Client,
    token: str,
    *,
    display_name: str = "E2E테스트강사",
    bio: str = "E2E 테스트용 강사 프로필입니다. 열심히 하겠습니다.",
    experience_years: int = 3,
    available_regions: Optional[list] = None,
    hourly_rate_min: int = 40000,
    hourly_rate_max: int = 60000,
) -> dict:
    """Complete instructor profile via API."""
    data = {
        "display_name": display_name,
        "bio": bio,
        "experience_years": experience_years,
        "available_regions": available_regions or ["강남", "서초"],
        "hourly_rate_min": hourly_rate_min,
        "hourly_rate_max": hourly_rate_max,
    }
    resp = api_client.put(
        "/instructors/me", json=data, headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def complete_studio_profile(
    api_client: httpx.Client,
    token: str,
    *,
    business_name: str = "E2E테스트스튜디오",
    description: str = "E2E 테스트용 스튜디오입니다.",
    region: str = "강남",
    address: str = "강남구 테헤란로 123",
) -> dict:
    """Complete studio profile via API."""
    data = {
        "business_name": business_name,
        "description": description,
        "region": region,
        "address": address,
    }
    resp = api_client.put(
        "/studios/me", json=data, headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def create_job_post(
    api_client: httpx.Client,
    token: str,
    *,
    title: Optional[str] = None,
    category: str = "pilates",
    job_type: str = "substitute",
    job_date: Optional[date] = None,
    start_time: str = "09:00:00",
    end_time: str = "10:00:00",
    hourly_rate: int = 50000,
    region: str = "강남",
    description: str = "E2E 테스트 공고",
) -> dict:
    """Create a job post via API."""
    if job_date is None:
        job_date = date.today() + timedelta(days=7)
    if title is None:
        title = f"[대타] {region} 필라테스 강사 모집"

    data = {
        "title": title,
        "category": category,
        "job_type": job_type,
        "date": job_date.isoformat(),
        "start_time": start_time,
        "end_time": end_time,
        "hourly_rate": hourly_rate,
        "region": region,
        "description": description,
        "total_sessions": 1,
    }
    resp = api_client.post(
        "/job-posts", json=data, headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def apply_to_job(
    api_client: httpx.Client,
    token: str,
    job_post_id: str,
    *,
    cover_letter: Optional[str] = None,
) -> dict:
    """Apply to a job post via API."""
    data = {}
    if cover_letter:
        data["cover_letter"] = cover_letter
    resp = api_client.post(
        f"/job-posts/{job_post_id}/applications",
        json=data,
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def send_offer(
    api_client: httpx.Client,
    token: str,
    application_id: str,
    *,
    proposed_rate: int = 50000,
    message: str = "오퍼를 전달합니다.",
) -> dict:
    """Send an offer to an applicant via API."""
    data = {
        "application_id": application_id,
        "proposed_rate": proposed_rate,
        "message": message,
    }
    resp = api_client.post(
        "/offers", json=data, headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def accept_offer(
    api_client: httpx.Client, token: str, offer_id: str
) -> dict:
    """Accept an offer via API."""
    resp = api_client.post(
        f"/offers/{offer_id}/accept", headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def create_contract(
    api_client: httpx.Client, token: str, offer_id: str
) -> dict:
    """Create a contract from an accepted offer via API."""
    resp = api_client.post(
        f"/contracts/from-offer/{offer_id}", headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def sign_contract(
    api_client: httpx.Client, token: str, contract_id: str
) -> dict:
    """Sign a contract (set-in-progress) via API."""
    resp = api_client.post(
        f"/contracts/{contract_id}/set-in-progress",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def initialize_payment(
    api_client: httpx.Client, token: str, contract_id: str
) -> dict:
    """Initialize payment for a contract via API."""
    resp = api_client.post(
        f"/contracts/{contract_id}/payments",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def confirm_payment(
    api_client: httpx.Client,
    token: str,
    payment_key: str,
    order_id: str,
    amount: int,
) -> dict:
    """Confirm payment via API."""
    data = {
        "payment_key": payment_key,
        "order_id": order_id,
        "amount": amount,
    }
    resp = api_client.post(
        "/payments/confirm", json=data, headers=_auth_headers(token)
    )
    resp.raise_for_status()
    return resp.json()


def confirm_completion(
    api_client: httpx.Client, token: str, contract_id: str
) -> dict:
    """Confirm contract completion via API."""
    resp = api_client.post(
        f"/contracts/{contract_id}/confirm-completion",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def create_review(
    api_client: httpx.Client,
    token: str,
    contract_id: str,
    *,
    rating: int = 5,
    comment: str = "훌륭했습니다!",
) -> dict:
    """Create a review for a completed contract via API."""
    data = {"rating": rating, "comment": comment}
    resp = api_client.post(
        f"/contracts/{contract_id}/reviews",
        json=data,
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def get_applications_for_job(
    api_client: httpx.Client, token: str, job_post_id: str
) -> list:
    """Get all applications for a job post (studio only)."""
    resp = api_client.get(
        f"/job-posts/{job_post_id}/applications",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return resp.json()


def get_my_offers(api_client: httpx.Client, token: str) -> list:
    """Get current user's offers."""
    resp = api_client.get("/offers/me", headers=_auth_headers(token))
    resp.raise_for_status()
    return resp.json()


def get_my_contracts(api_client: httpx.Client, token: str) -> list:
    """Get current user's contracts."""
    resp = api_client.get("/contracts/me", headers=_auth_headers(token))
    resp.raise_for_status()
    return resp.json()
