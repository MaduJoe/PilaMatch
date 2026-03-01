"""Contract State Machine Transition Tests

Service-level unit tests for the ContractService, covering:
- Valid and invalid state transitions
- Contract creation from accepted/non-accepted offers
- Cancellation flows (valid states and terminal state rejection)
- Event log creation and audit trail correctness
- Bidirectional signing (set_in_progress)
- Bidirectional completion confirmation (confirm_completion)
- Auto-completion of pending contracts (24h / 48h rules)

Test naming convention: test_{scenario}_{expected_result}
"""

import uuid
from datetime import date, time, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Contract,
    ContractEventLog,
    Offer,
    Application,
    JobPost,
    User,
    InstructorProfile,
    StudioProfile,
    ContractStatus,
    OfferStatus,
    ApplicationStatus,
    UserRole,
    JobPostStatus,
    MembershipTier,
)
from app.models.base import GUID
from app.services.contract import ContractService, VALID_TRANSITIONS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_users_and_profiles(
    db: AsyncSession,
) -> dict:
    """Insert a full chain of test records: User -> Profile -> JobPost -> Application -> Offer.

    Returns a dict with all created IDs and model instances.
    """
    # --- Studio user + profile ---
    studio_user_id = uuid.uuid4()
    studio_user = User(
        id=studio_user_id,
        email=f"studio_{studio_user_id}@test.com",
        hashed_password="hashed_test_password",
        role=UserRole.STUDIO.value,
        membership_tier=MembershipTier.FREE.value,
    )
    db.add(studio_user)
    await db.flush()

    studio_profile_id = uuid.uuid4()
    studio_profile = StudioProfile(
        id=studio_profile_id,
        user_id=studio_user_id,
        business_name="Test Studio",
        categories=["pilates"],
        region="Seoul",
    )
    db.add(studio_profile)
    await db.flush()

    # --- Instructor user + profile ---
    instructor_user_id = uuid.uuid4()
    instructor_user = User(
        id=instructor_user_id,
        email=f"instructor_{instructor_user_id}@test.com",
        hashed_password="hashed_test_password",
        role=UserRole.INSTRUCTOR.value,
        membership_tier=MembershipTier.FREE.value,
    )
    db.add(instructor_user)
    await db.flush()

    instructor_profile_id = uuid.uuid4()
    instructor_profile = InstructorProfile(
        id=instructor_profile_id,
        user_id=instructor_user_id,
        display_name="Test Instructor",
        categories=["pilates"],
        available_regions=["Seoul"],
        experience_years=3,
    )
    db.add(instructor_profile)
    await db.flush()

    # --- Job Post ---
    job_post_id = uuid.uuid4()
    job_post = JobPost(
        id=job_post_id,
        studio_id=studio_profile_id,
        title="Pilates Morning Class",
        category="pilates",
        job_type="substitute",
        status=JobPostStatus.OPEN.value,
        date=date.today() + timedelta(days=7),
        start_time=time(9, 0),
        end_time=time(11, 0),
        hourly_rate=50000,
        total_sessions=1,
    )
    db.add(job_post)
    await db.flush()

    # --- Application ---
    application_id = uuid.uuid4()
    application = Application(
        id=application_id,
        job_post_id=job_post_id,
        instructor_id=instructor_profile_id,
        status=ApplicationStatus.PENDING.value,
    )
    db.add(application)
    await db.flush()

    # --- Offer (ACCEPTED by default for contract creation) ---
    offer_id = uuid.uuid4()
    offer = Offer(
        id=offer_id,
        application_id=application_id,
        studio_id=studio_profile_id,
        instructor_id=instructor_profile_id,
        proposed_rate=50000,
        status=OfferStatus.ACCEPTED.value,
    )
    db.add(offer)
    await db.flush()

    return {
        "studio_user_id": studio_user_id,
        "studio_profile_id": studio_profile_id,
        "instructor_user_id": instructor_user_id,
        "instructor_profile_id": instructor_profile_id,
        "job_post_id": job_post_id,
        "application_id": application_id,
        "offer_id": offer_id,
        "offer": offer,
        "job_post": job_post,
    }


async def _create_contract_directly(
    db: AsyncSession,
    data: dict,
    *,
    status: ContractStatus = ContractStatus.CONFIRMED,
    studio_signed_at: datetime | None = None,
    instructor_signed_at: datetime | None = None,
    studio_confirmed_at: datetime | None = None,
    instructor_confirmed_at: datetime | None = None,
) -> Contract:
    """Insert a Contract record directly into the DB (bypassing the service).

    Useful for testing transitions from arbitrary starting states.
    """
    contract_id = uuid.uuid4()
    contract = Contract(
        id=contract_id,
        offer_id=data["offer_id"],
        studio_id=data["studio_profile_id"],
        instructor_id=data["instructor_profile_id"],
        status=status,
        hourly_rate=50000,
        total_amount=100000,
        total_sessions=1,
        date=date.today() + timedelta(days=7),
        start_time=time(9, 0),
        end_time=time(11, 0),
        studio_signed_at=studio_signed_at,
        instructor_signed_at=instructor_signed_at,
        studio_confirmed_at=studio_confirmed_at,
        instructor_confirmed_at=instructor_confirmed_at,
    )
    db.add(contract)
    await db.flush()
    return contract


# ---------------------------------------------------------------------------
# 1. _validate_transition -- valid cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_transition_valid_cases(db_session: AsyncSession):
    """All edges defined in VALID_TRANSITIONS must return True."""
    service = ContractService(db_session)

    for from_status, valid_targets in VALID_TRANSITIONS.items():
        for to_status in valid_targets:
            result = service._validate_transition(from_status, to_status)
            assert result is True, (
                f"Expected valid transition {from_status.value} -> {to_status.value} "
                f"but _validate_transition returned False"
            )


# ---------------------------------------------------------------------------
# 2. _validate_transition -- invalid cases
# ---------------------------------------------------------------------------


_INVALID_TRANSITIONS = [
    (ContractStatus.COMPLETED, ContractStatus.IN_PROGRESS),
    (ContractStatus.COMPLETED, ContractStatus.CANCELLED),
    (ContractStatus.COMPLETED, ContractStatus.CONFIRMED),
    (ContractStatus.CANCELLED, ContractStatus.CONFIRMED),
    (ContractStatus.CANCELLED, ContractStatus.IN_PROGRESS),
    (ContractStatus.CANCELLED, ContractStatus.COMPLETED),
    (ContractStatus.IN_PROGRESS, ContractStatus.CONFIRMED),
    (ContractStatus.CONFIRMED, ContractStatus.COMPLETED),
    (ContractStatus.CONFIRMED, ContractStatus.PENDING_COMPLETION),
    (ContractStatus.PENDING_COMPLETION, ContractStatus.IN_PROGRESS),
    (ContractStatus.PENDING_COMPLETION, ContractStatus.CANCELLED),
    (ContractStatus.DISPUTED, ContractStatus.IN_PROGRESS),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "from_status,to_status",
    _INVALID_TRANSITIONS,
    ids=[f"{f.value}_to_{t.value}" for f, t in _INVALID_TRANSITIONS],
)
async def test_validate_transition_invalid_cases(
    db_session: AsyncSession,
    from_status: ContractStatus,
    to_status: ContractStatus,
):
    """Transitions not in VALID_TRANSITIONS must return False."""
    service = ContractService(db_session)

    result = service._validate_transition(from_status, to_status)
    assert result is False, (
        f"Expected invalid transition {from_status.value} -> {to_status.value} "
        f"but _validate_transition returned True"
    )


# ---------------------------------------------------------------------------
# 3. create_from_offer -- accepted offer succeeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contract_from_accepted_offer(db_session: AsyncSession):
    """Creating a contract from an ACCEPTED offer produces a CONFIRMED contract with an event log."""
    data = await _create_users_and_profiles(db_session)
    service = ContractService(db_session)

    contract = await service.create_from_offer(
        offer_id=data["offer_id"],
        actor_user_id=data["studio_user_id"],
    )

    assert contract.status == ContractStatus.CONFIRMED


@pytest.mark.asyncio
async def test_create_contract_from_accepted_offer_event_log_created(
    db_session: AsyncSession,
):
    """The creation event log records from_status=None and to_status=CONFIRMED."""
    data = await _create_users_and_profiles(db_session)
    service = ContractService(db_session)

    contract = await service.create_from_offer(
        offer_id=data["offer_id"],
        actor_user_id=data["studio_user_id"],
    )

    logs = (
        await db_session.execute(
            select(ContractEventLog).where(
                ContractEventLog.contract_id == contract.id
            )
        )
    ).scalars().all()

    assert len(logs) == 1
    assert logs[0].from_status is None
    assert logs[0].to_status == ContractStatus.CONFIRMED.value


@pytest.mark.asyncio
async def test_create_contract_total_amount_calculated(db_session: AsyncSession):
    """Total amount should equal hourly_rate * hours * total_sessions from the job post."""
    data = await _create_users_and_profiles(db_session)
    service = ContractService(db_session)

    contract = await service.create_from_offer(
        offer_id=data["offer_id"],
        actor_user_id=data["studio_user_id"],
    )

    # Job post: 09:00-11:00 = 2 hours, rate 50000, sessions 1
    expected_amount = 50000 * 2 * 1
    assert float(contract.total_amount) == expected_amount


# ---------------------------------------------------------------------------
# 4. create_from_offer -- non-accepted offer fails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contract_from_pending_offer_fails(db_session: AsyncSession):
    """An offer that is still PENDING cannot be converted into a contract."""
    data = await _create_users_and_profiles(db_session)

    # Overwrite offer status to PENDING
    data["offer"].status = OfferStatus.PENDING.value
    await db_session.flush()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="Offer must be accepted first"):
        await service.create_from_offer(
            offer_id=data["offer_id"],
            actor_user_id=data["studio_user_id"],
        )


@pytest.mark.asyncio
async def test_create_contract_from_rejected_offer_fails(db_session: AsyncSession):
    """An offer that was REJECTED cannot be converted into a contract."""
    data = await _create_users_and_profiles(db_session)

    data["offer"].status = OfferStatus.REJECTED.value
    await db_session.flush()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="Offer must be accepted first"):
        await service.create_from_offer(
            offer_id=data["offer_id"],
            actor_user_id=data["studio_user_id"],
        )


@pytest.mark.asyncio
async def test_create_contract_duplicate_offer_fails(db_session: AsyncSession):
    """Creating two contracts from the same offer raises ValueError."""
    data = await _create_users_and_profiles(db_session)
    service = ContractService(db_session)

    await service.create_from_offer(
        offer_id=data["offer_id"],
        actor_user_id=data["studio_user_id"],
    )

    with pytest.raises(ValueError, match="Contract already exists"):
        await service.create_from_offer(
            offer_id=data["offer_id"],
            actor_user_id=data["studio_user_id"],
        )


# ---------------------------------------------------------------------------
# 5. cancel -- from CONFIRMED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_contract_from_confirmed(
    db_session: AsyncSession,
):
    """Cancelling a CONFIRMED contract transitions it to CANCELLED."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    cancelled = await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
        reason="Schedule conflict",
    )

    assert cancelled.status == ContractStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_contract_stores_reason(
    db_session: AsyncSession,
):
    """Cancellation reason is persisted on the contract record."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    cancelled = await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
        reason="Schedule conflict",
    )

    assert cancelled.cancellation_reason == "Schedule conflict"


@pytest.mark.asyncio
async def test_cancel_contract_stores_cancelled_by_user(
    db_session: AsyncSession,
):
    """The user who cancelled is recorded."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    cancelled = await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
        reason="Schedule conflict",
    )

    assert cancelled.cancelled_by_user_id == data["studio_user_id"]


@pytest.mark.asyncio
async def test_cancel_contract_from_in_progress(
    db_session: AsyncSession,
):
    """Cancelling an IN_PROGRESS contract also succeeds (valid transition)."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    cancelled = await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
        reason="Emergency",
    )

    assert cancelled.status == ContractStatus.CANCELLED


# ---------------------------------------------------------------------------
# 6. cancel -- from terminal COMPLETED state fails
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_contract_from_completed_fails(db_session: AsyncSession):
    """A COMPLETED contract is terminal and cannot be cancelled."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.COMPLETED)
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="INVALID_STATE_TRANSITION"):
        await service.cancel(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
            reason="Want to cancel",
        )


@pytest.mark.asyncio
async def test_cancel_contract_from_cancelled_fails(db_session: AsyncSession):
    """A CANCELLED contract is terminal and cannot be cancelled again."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CANCELLED)
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="INVALID_STATE_TRANSITION"):
        await service.cancel(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
            reason="Try again",
        )


# ---------------------------------------------------------------------------
# 7. cancel -- reason required
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_contract_without_reason_fails(db_session: AsyncSession):
    """Cancellation must include a reason."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="CANCEL_REASON_REQUIRED"):
        await service.cancel(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
            reason="",
        )


# ---------------------------------------------------------------------------
# 8. Event log audit trail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_log_created_on_cancellation(
    db_session: AsyncSession,
):
    """After cancelling a CONFIRMED contract, an event log with correct from/to is persisted."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
        reason="No longer needed",
    )

    logs = (
        await db_session.execute(
            select(ContractEventLog)
            .where(ContractEventLog.contract_id == contract.id)
            .order_by(ContractEventLog.created_at)
        )
    ).scalars().all()

    assert len(logs) == 1
    assert logs[0].from_status == ContractStatus.CONFIRMED.value
    assert logs[0].to_status == ContractStatus.CANCELLED.value
    assert logs[0].actor_user_id == data["studio_user_id"]


@pytest.mark.asyncio
async def test_event_log_note_contains_reason(
    db_session: AsyncSession,
):
    """The event log note includes the cancellation reason."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    await service.cancel(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
        reason="Instructor unavailable",
    )

    log = (
        await db_session.execute(
            select(ContractEventLog).where(
                ContractEventLog.contract_id == contract.id
            )
        )
    ).scalar_one()

    assert "Instructor unavailable" in log.note


# ---------------------------------------------------------------------------
# 9. set_in_progress -- bidirectional signing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sign_contract_studio_first_remains_confirmed(
    db_session: AsyncSession,
):
    """When only the studio signs, the contract stays CONFIRMED."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    result = await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    assert result.status == ContractStatus.CONFIRMED
    assert result.studio_signed_at is not None
    assert result.instructor_signed_at is None


@pytest.mark.asyncio
async def test_sign_contract_both_parties_transitions_to_in_progress(
    db_session: AsyncSession,
):
    """When both parties sign, the contract transitions to IN_PROGRESS."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    # Studio signs first
    await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    # Instructor signs second
    result = await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    assert result.status == ContractStatus.IN_PROGRESS
    assert result.studio_signed_at is not None
    assert result.instructor_signed_at is not None


@pytest.mark.asyncio
async def test_sign_contract_instructor_first_then_studio(
    db_session: AsyncSession,
):
    """Signing order does not matter -- instructor first, then studio, produces IN_PROGRESS."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    # Instructor signs first
    await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    # Studio signs second
    result = await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    assert result.status == ContractStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_sign_contract_duplicate_studio_signature_fails(
    db_session: AsyncSession,
):
    """A studio cannot sign the same contract twice."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    with pytest.raises(ValueError, match="Already signed by studio"):
        await service.set_in_progress(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
        )


@pytest.mark.asyncio
async def test_sign_contract_not_in_confirmed_status_fails(
    db_session: AsyncSession,
):
    """Only CONFIRMED contracts can be signed."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="Contract must be in CONFIRMED status"):
        await service.set_in_progress(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
        )


@pytest.mark.asyncio
async def test_sign_contract_unauthorized_studio_fails(
    db_session: AsyncSession,
):
    """A studio that is not party to the contract cannot sign it."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)
    other_profile_id = uuid.uuid4()

    with pytest.raises(PermissionError, match="Not authorized"):
        await service.set_in_progress(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=other_profile_id,
            role="studio",
        )


@pytest.mark.asyncio
async def test_sign_contract_event_log_on_both_signatures(
    db_session: AsyncSession,
):
    """Two event logs should be created: one for each signature, the second recording the IN_PROGRESS transition."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )
    await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    logs = (
        await db_session.execute(
            select(ContractEventLog)
            .where(ContractEventLog.contract_id == contract.id)
            .order_by(ContractEventLog.created_at)
        )
    ).scalars().all()

    assert len(logs) == 2

    # First log: studio signs, still CONFIRMED
    assert logs[0].from_status == ContractStatus.CONFIRMED.value
    assert logs[0].to_status == ContractStatus.CONFIRMED.value

    # Second log: instructor signs, transition to IN_PROGRESS
    assert logs[1].from_status == ContractStatus.CONFIRMED.value
    assert logs[1].to_status == ContractStatus.IN_PROGRESS.value


# ---------------------------------------------------------------------------
# 10. confirm_completion -- bidirectional completion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_completion_studio_first_moves_to_pending(
    db_session: AsyncSession,
):
    """When only the studio confirms, the contract moves to PENDING_COMPLETION."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    result = await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    assert result.status == ContractStatus.PENDING_COMPLETION
    assert result.studio_confirmed_at is not None
    assert result.instructor_confirmed_at is None


@pytest.mark.asyncio
async def test_confirm_completion_both_parties_completes(
    db_session: AsyncSession,
):
    """When both parties confirm, the contract transitions to COMPLETED."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    # Studio confirms first
    await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    # Instructor confirms second
    result = await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    assert result.status == ContractStatus.COMPLETED


@pytest.mark.asyncio
async def test_confirm_completion_instructor_first_then_studio(
    db_session: AsyncSession,
):
    """Confirmation order does not matter -- instructor first, then studio, produces COMPLETED."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    result = await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    assert result.status == ContractStatus.COMPLETED


@pytest.mark.asyncio
async def test_confirm_completion_duplicate_studio_fails(
    db_session: AsyncSession,
):
    """A studio cannot confirm completion twice."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )

    with pytest.raises(ValueError, match="Already confirmed by studio"):
        await service.confirm_completion(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
        )


@pytest.mark.asyncio
async def test_confirm_completion_from_confirmed_status_fails(
    db_session: AsyncSession,
):
    """A contract in CONFIRMED status cannot be confirmed for completion."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="CONTRACT_NOT_IN_PROGRESS"):
        await service.confirm_completion(
            contract_id=contract.id,
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
        )


@pytest.mark.asyncio
async def test_confirm_completion_event_logs(
    db_session: AsyncSession,
):
    """Full completion flow produces two event logs: IN_PROGRESS->PENDING_COMPLETION, then PENDING_COMPLETION->COMPLETED."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.IN_PROGRESS,
        studio_signed_at=datetime.utcnow(),
        instructor_signed_at=datetime.utcnow(),
    )
    await db_session.commit()

    service = ContractService(db_session)

    await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )
    await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )

    logs = (
        await db_session.execute(
            select(ContractEventLog)
            .where(ContractEventLog.contract_id == contract.id)
            .order_by(ContractEventLog.created_at)
        )
    ).scalars().all()

    assert len(logs) == 2

    assert logs[0].from_status == ContractStatus.IN_PROGRESS.value
    assert logs[0].to_status == ContractStatus.PENDING_COMPLETION.value

    assert logs[1].from_status == ContractStatus.PENDING_COMPLETION.value
    assert logs[1].to_status == ContractStatus.COMPLETED.value


# ---------------------------------------------------------------------------
# 11. auto_complete_pending_contracts -- 24h timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_complete_pending_after_24h_studio_confirmed(
    db_session: AsyncSession,
):
    """A PENDING_COMPLETION contract with studio confirmation >24h ago is auto-completed."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.PENDING_COMPLETION,
        studio_signed_at=datetime.utcnow() - timedelta(hours=48),
        instructor_signed_at=datetime.utcnow() - timedelta(hours=48),
        studio_confirmed_at=datetime.utcnow() - timedelta(hours=25),
    )
    await db_session.commit()

    service = ContractService(db_session)
    completed = await service.auto_complete_pending_contracts()

    assert len(completed) == 1
    assert completed[0].status == ContractStatus.COMPLETED


@pytest.mark.asyncio
async def test_auto_complete_pending_not_triggered_before_24h(
    db_session: AsyncSession,
):
    """A PENDING_COMPLETION contract confirmed <24h ago should NOT be auto-completed."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(
        db_session,
        data,
        status=ContractStatus.PENDING_COMPLETION,
        studio_signed_at=datetime.utcnow() - timedelta(hours=48),
        instructor_signed_at=datetime.utcnow() - timedelta(hours=48),
        studio_confirmed_at=datetime.utcnow() - timedelta(hours=12),
    )
    await db_session.commit()

    service = ContractService(db_session)
    completed = await service.auto_complete_pending_contracts()

    assert len(completed) == 0


# ---------------------------------------------------------------------------
# 12. auto_complete_pending_contracts -- 48h IN_PROGRESS timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_complete_in_progress_after_48h(
    db_session: AsyncSession,
):
    """An IN_PROGRESS contract where the class ended >48h ago is auto-completed."""
    data = await _create_users_and_profiles(db_session)

    past_date = date.today() - timedelta(days=3)
    contract_id = uuid.uuid4()
    contract = Contract(
        id=contract_id,
        offer_id=data["offer_id"],
        studio_id=data["studio_profile_id"],
        instructor_id=data["instructor_profile_id"],
        status=ContractStatus.IN_PROGRESS,
        hourly_rate=50000,
        total_amount=100000,
        total_sessions=1,
        date=past_date,
        start_time=time(9, 0),
        end_time=time(11, 0),
        studio_signed_at=datetime.utcnow() - timedelta(days=4),
        instructor_signed_at=datetime.utcnow() - timedelta(days=4),
    )
    db_session.add(contract)
    await db_session.commit()

    service = ContractService(db_session)
    completed = await service.auto_complete_pending_contracts()

    assert len(completed) == 1
    assert completed[0].status == ContractStatus.COMPLETED


@pytest.mark.asyncio
async def test_auto_complete_in_progress_not_triggered_before_48h(
    db_session: AsyncSession,
):
    """An IN_PROGRESS contract where the class ended <48h ago should NOT be auto-completed."""
    data = await _create_users_and_profiles(db_session)

    # Class ended just a few hours ago
    today = date.today()
    contract_id = uuid.uuid4()
    contract = Contract(
        id=contract_id,
        offer_id=data["offer_id"],
        studio_id=data["studio_profile_id"],
        instructor_id=data["instructor_profile_id"],
        status=ContractStatus.IN_PROGRESS,
        hourly_rate=50000,
        total_amount=100000,
        total_sessions=1,
        date=today,
        start_time=time(0, 0),
        end_time=time(1, 0),
        studio_signed_at=datetime.utcnow() - timedelta(days=1),
        instructor_signed_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(contract)
    await db_session.commit()

    service = ContractService(db_session)
    completed = await service.auto_complete_pending_contracts()

    assert len(completed) == 0


# ---------------------------------------------------------------------------
# 13. Authorization checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_by_unauthorized_instructor_fails(db_session: AsyncSession):
    """An instructor who is not party to the contract cannot cancel it."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)
    other_profile_id = uuid.uuid4()

    with pytest.raises(PermissionError, match="Not authorized"):
        await service.cancel(
            contract_id=contract.id,
            actor_user_id=data["instructor_user_id"],
            profile_id=other_profile_id,
            role="instructor",
            reason="Not my contract",
        )


@pytest.mark.asyncio
async def test_cancel_nonexistent_contract_fails(db_session: AsyncSession):
    """Attempting to cancel a non-existent contract raises ValueError."""
    data = await _create_users_and_profiles(db_session)
    await db_session.commit()

    service = ContractService(db_session)

    with pytest.raises(ValueError, match="Contract not found"):
        await service.cancel(
            contract_id=uuid.uuid4(),
            actor_user_id=data["studio_user_id"],
            profile_id=data["studio_profile_id"],
            role="studio",
            reason="Ghost contract",
        )


# ---------------------------------------------------------------------------
# 14. get_by_id / get_by_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_existing(db_session: AsyncSession):
    """get_by_id returns the correct contract."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)
    result = await service.get_by_id(contract.id)

    assert result is not None
    assert result.id == contract.id


@pytest.mark.asyncio
async def test_get_by_id_nonexistent(db_session: AsyncSession):
    """get_by_id returns None for a non-existent contract."""
    service = ContractService(db_session)
    result = await service.get_by_id(uuid.uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_as_instructor(db_session: AsyncSession):
    """get_by_user returns the instructor's contracts."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)
    contracts, total = await service.get_by_user(data["instructor_user_id"], "instructor")

    assert len(contracts) == 1
    assert contracts[0].id == contract.id


@pytest.mark.asyncio
async def test_get_by_user_as_studio(db_session: AsyncSession):
    """get_by_user returns the studio's contracts."""
    data = await _create_users_and_profiles(db_session)
    contract = await _create_contract_directly(db_session, data, status=ContractStatus.CONFIRMED)
    await db_session.commit()

    service = ContractService(db_session)
    contracts, total = await service.get_by_user(data["studio_user_id"], "studio")

    assert len(contracts) == 1
    assert contracts[0].id == contract.id


# ---------------------------------------------------------------------------
# 15. Full lifecycle: CONFIRMED -> IN_PROGRESS -> PENDING_COMPLETION -> COMPLETED
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_lifecycle_happy_path(
    db_session: AsyncSession,
):
    """Exercise the entire happy path: create -> sign (both) -> confirm (both) -> COMPLETED."""
    data = await _create_users_and_profiles(db_session)
    service = ContractService(db_session)

    # Step 1: Create contract from accepted offer
    contract = await service.create_from_offer(
        offer_id=data["offer_id"],
        actor_user_id=data["studio_user_id"],
    )
    assert contract.status == ContractStatus.CONFIRMED

    # Step 2: Studio signs
    contract = await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )
    assert contract.status == ContractStatus.CONFIRMED

    # Step 3: Instructor signs -> IN_PROGRESS
    contract = await service.set_in_progress(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )
    assert contract.status == ContractStatus.IN_PROGRESS

    # Step 4: Studio confirms completion -> PENDING_COMPLETION
    contract = await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["studio_user_id"],
        profile_id=data["studio_profile_id"],
        role="studio",
    )
    assert contract.status == ContractStatus.PENDING_COMPLETION

    # Step 5: Instructor confirms completion -> COMPLETED
    contract = await service.confirm_completion(
        contract_id=contract.id,
        actor_user_id=data["instructor_user_id"],
        profile_id=data["instructor_profile_id"],
        role="instructor",
    )
    assert contract.status == ContractStatus.COMPLETED

    # Verify event log trail
    logs = (
        await db_session.execute(
            select(ContractEventLog)
            .where(ContractEventLog.contract_id == contract.id)
            .order_by(ContractEventLog.created_at)
        )
    ).scalars().all()

    # 1: creation, 2: studio sign, 3: instructor sign (->IN_PROGRESS),
    # 4: studio confirm (->PENDING_COMPLETION), 5: instructor confirm (->COMPLETED)
    assert len(logs) == 5

    status_transitions = [(log.from_status, log.to_status) for log in logs]
    assert status_transitions == [
        (None, ContractStatus.CONFIRMED.value),
        (ContractStatus.CONFIRMED.value, ContractStatus.CONFIRMED.value),
        (ContractStatus.CONFIRMED.value, ContractStatus.IN_PROGRESS.value),
        (ContractStatus.IN_PROGRESS.value, ContractStatus.PENDING_COMPLETION.value),
        (ContractStatus.PENDING_COMPLETION.value, ContractStatus.COMPLETED.value),
    ]


# ---------------------------------------------------------------------------
# 16. Terminal state completeness check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_terminal_states_have_no_valid_transitions(db_session: AsyncSession):
    """COMPLETED and CANCELLED are terminal -- they have zero valid next states."""
    assert VALID_TRANSITIONS[ContractStatus.COMPLETED] == set()
    assert VALID_TRANSITIONS[ContractStatus.CANCELLED] == set()


@pytest.mark.asyncio
async def test_all_contract_statuses_are_in_transitions_dict(db_session: AsyncSession):
    """Every ContractStatus enum value must have an entry in VALID_TRANSITIONS."""
    for status in ContractStatus:
        assert status in VALID_TRANSITIONS, (
            f"ContractStatus.{status.name} is missing from VALID_TRANSITIONS"
        )
