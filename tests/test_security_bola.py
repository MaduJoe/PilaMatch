"""Tests for BOLA (Broken Object Level Authorization) fixes.

Tests that users can only report no-show on contracts they are party to.
The report-no-show endpoint performs a BOLA check: it verifies the requesting
user's profile_id matches either the contract's studio_id or instructor_id.
"""

import uuid
from datetime import date, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    InstructorProfile,
    StudioProfile,
    JobPost,
    Application,
    Offer,
    Contract,
    UserRole,
    ContractStatus,
    OfferStatus,
    ApplicationStatus,
    JobPostStatus,
)
from app.core.security import create_access_token, get_password_hash


async def _setup_contract(db: AsyncSession) -> dict:
    """Create a full contract chain: studio -> job -> application -> offer -> contract.

    Returns a dict with all created model instances.
    """
    # --- Studio user + profile ---
    studio_user = User(
        id=uuid.uuid4(),
        email="studio_bola@test.com",
        hashed_password=get_password_hash("TestPass123"),
        role=UserRole.STUDIO.value,
        is_active=True,
        is_verified=True,
    )
    db.add(studio_user)

    studio_profile = StudioProfile(
        id=uuid.uuid4(),
        user_id=studio_user.id,
        business_name="Test Studio",
        region="Seoul",
    )
    db.add(studio_profile)

    # --- Instructor user + profile ---
    instructor_user = User(
        id=uuid.uuid4(),
        email="instructor_bola@test.com",
        hashed_password=get_password_hash("TestPass123"),
        role=UserRole.INSTRUCTOR.value,
        is_active=True,
        is_verified=True,
    )
    db.add(instructor_user)

    instructor_profile = InstructorProfile(
        id=uuid.uuid4(),
        user_id=instructor_user.id,
        display_name="Test Instructor",
    )
    db.add(instructor_profile)

    # --- Unrelated user (not party to the contract) ---
    other_user = User(
        id=uuid.uuid4(),
        email="other_bola@test.com",
        hashed_password=get_password_hash("TestPass123"),
        role=UserRole.STUDIO.value,
        is_active=True,
        is_verified=True,
    )
    db.add(other_user)

    other_profile = StudioProfile(
        id=uuid.uuid4(),
        user_id=other_user.id,
        business_name="Other Studio",
        region="Busan",
    )
    db.add(other_profile)

    await db.flush()

    # --- Job post ---
    job_post = JobPost(
        id=uuid.uuid4(),
        studio_id=studio_profile.id,
        title="Test Job",
        category="pilates",
        job_type="substitute",
        status=JobPostStatus.OPEN.value,
        region="Seoul",
        hourly_rate=30000,
        date=date.today() + timedelta(days=7),
        start_time=time(10, 0),
        end_time=time(12, 0),
    )
    db.add(job_post)
    await db.flush()

    # --- Application ---
    application = Application(
        id=uuid.uuid4(),
        job_post_id=job_post.id,
        instructor_id=instructor_profile.id,
        status=ApplicationStatus.ACCEPTED.value,
    )
    db.add(application)
    await db.flush()

    # --- Offer ---
    offer = Offer(
        id=uuid.uuid4(),
        application_id=application.id,
        studio_id=studio_profile.id,
        instructor_id=instructor_profile.id,
        status=OfferStatus.ACCEPTED.value,
        proposed_rate=30000,
    )
    db.add(offer)
    await db.flush()

    # --- Contract in CONFIRMED state (eligible for no-show report) ---
    contract = Contract(
        id=uuid.uuid4(),
        offer_id=offer.id,
        studio_id=studio_profile.id,
        instructor_id=instructor_profile.id,
        status=ContractStatus.CONFIRMED.value,
        hourly_rate=30000,
        total_amount=60000,
        total_sessions=1,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(12, 0),
    )
    db.add(contract)
    await db.commit()

    return {
        "contract": contract,
        "studio_user": studio_user,
        "instructor_user": instructor_user,
        "other_user": other_user,
        "instructor_profile": instructor_profile,
        "studio_profile": studio_profile,
    }


@pytest.mark.asyncio
async def test_report_no_show_by_contract_party_allowed(
    client: AsyncClient, db_session: AsyncSession
):
    """Studio that is party to the contract can report no-show."""
    data = await _setup_contract(db_session)
    token = create_access_token(str(data["studio_user"].id))

    response = await client.post(
        f"/api/v1/contracts/{data['contract'].id}/report-no-show",
        json={"reported_user_id": str(data["instructor_profile"].id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Should succeed (200) or fail for a reason other than permission denied
    assert response.status_code != 403


@pytest.mark.asyncio
async def test_report_no_show_by_instructor_party_allowed(
    client: AsyncClient, db_session: AsyncSession
):
    """Instructor that is party to the contract can report no-show."""
    data = await _setup_contract(db_session)
    token = create_access_token(str(data["instructor_user"].id))

    response = await client.post(
        f"/api/v1/contracts/{data['contract'].id}/report-no-show",
        json={"reported_user_id": str(data["studio_profile"].id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Should succeed (200) or fail for a reason other than permission denied
    assert response.status_code != 403


@pytest.mark.asyncio
async def test_report_no_show_by_non_party_denied(
    client: AsyncClient, db_session: AsyncSession
):
    """User NOT party to the contract gets 403 when reporting no-show."""
    data = await _setup_contract(db_session)
    token = create_access_token(str(data["other_user"].id))

    response = await client.post(
        f"/api/v1/contracts/{data['contract'].id}/report-no-show",
        json={"reported_user_id": str(data["instructor_profile"].id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_report_no_show_unauthenticated(client: AsyncClient):
    """Unauthenticated request returns 401 or 403."""
    fake_id = str(uuid.uuid4())
    response = await client.post(
        f"/api/v1/contracts/{fake_id}/report-no-show",
        json={"reported_user_id": fake_id},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_report_no_show_contract_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    """Report no-show on nonexistent contract returns 404."""
    data = await _setup_contract(db_session)
    token = create_access_token(str(data["studio_user"].id))

    fake_contract_id = str(uuid.uuid4())
    response = await client.post(
        f"/api/v1/contracts/{fake_contract_id}/report-no-show",
        json={"reported_user_id": str(data["instructor_profile"].id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CONTRACT_NOT_FOUND"
