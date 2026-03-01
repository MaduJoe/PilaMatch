"""Unit tests for Payment Confirmation service (v4.0).

Tests cover mark_paid, confirm_payment, dispute_payment, and
on_time_payment_rate calculation for off-platform payment tracking.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import ApplicationStatus, PaymentConfirmationStatus
from app.services.payment_confirmation import (
    mark_paid,
    confirm_payment,
    dispute_payment,
    get_on_time_payment_rate,
    get_by_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_application(
    app_id: Optional[uuid.UUID] = None,
    instructor_id: Optional[uuid.UUID] = None,
    status: str = ApplicationStatus.ACCEPTED.value,
) -> MagicMock:
    app = MagicMock()
    app.id = app_id or uuid.uuid4()
    app.instructor_id = instructor_id or uuid.uuid4()
    app.status = status
    return app


def _make_confirmation(
    conf_id: Optional[uuid.UUID] = None,
    application_id: Optional[uuid.UUID] = None,
    center_user_id: Optional[uuid.UUID] = None,
    instructor_user_id: Optional[uuid.UUID] = None,
    amount: Decimal = Decimal("50000"),
    status: str = PaymentConfirmationStatus.PENDING.value,
    dispute_reason: Optional[str] = None,
) -> MagicMock:
    conf = MagicMock()
    conf.id = conf_id or uuid.uuid4()
    conf.application_id = application_id or uuid.uuid4()
    conf.center_user_id = center_user_id or uuid.uuid4()
    conf.instructor_user_id = instructor_user_id or uuid.uuid4()
    conf.amount = amount
    conf.status = status
    conf.center_marked_paid_at = datetime.utcnow()
    conf.instructor_confirmed_at = None
    conf.dispute_reason = dispute_reason
    conf.created_at = datetime.utcnow()
    return conf


# ===========================================================================
# mark_paid
# ===========================================================================

class TestMarkPaid:
    """Tests for mark_paid function."""

    async def test_mark_paid_creates_confirmation(self) -> None:
        """Creates a pending confirmation for an accepted application."""
        application = _make_application(status=ApplicationStatus.ACCEPTED.value)
        instructor_user_id = uuid.uuid4()
        center_user_id = uuid.uuid4()

        db = AsyncMock()
        added_objects = []

        # 1. Application query
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = application
        # 2. Existing confirmation check
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        # 3. Instructor user_id query
        inst_result = MagicMock()
        inst_result.scalar_one_or_none.return_value = instructor_user_id

        db.execute = AsyncMock(side_effect=[app_result, existing_result, inst_result])
        db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await mark_paid(
            db, application.id, center_user_id, Decimal("50000")
        )

        assert len(added_objects) == 1
        created = added_objects[0]
        assert created.status == PaymentConfirmationStatus.PENDING.value
        assert created.amount == Decimal("50000")
        assert created.center_user_id == center_user_id
        assert created.instructor_user_id == instructor_user_id

    async def test_mark_paid_duplicate_fails(self) -> None:
        """Second mark_paid for same application raises ValueError."""
        application = _make_application(status=ApplicationStatus.ACCEPTED.value)
        existing_conf = _make_confirmation(application_id=application.id)

        db = AsyncMock()
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = application
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = existing_conf

        db.execute = AsyncMock(side_effect=[app_result, existing_result])

        with pytest.raises(ValueError, match="already exists"):
            await mark_paid(db, application.id, uuid.uuid4(), Decimal("50000"))

    async def test_mark_paid_non_accepted_application_fails(self) -> None:
        """mark_paid on a non-accepted application raises ValueError."""
        application = _make_application(status=ApplicationStatus.PENDING.value)

        db = AsyncMock()
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = application

        db.execute = AsyncMock(return_value=app_result)

        with pytest.raises(ValueError, match="must be accepted"):
            await mark_paid(db, application.id, uuid.uuid4(), Decimal("50000"))

    async def test_mark_paid_application_not_found_fails(self) -> None:
        """mark_paid on non-existent application raises ValueError."""
        db = AsyncMock()
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = None

        db.execute = AsyncMock(return_value=app_result)

        with pytest.raises(ValueError, match="not found"):
            await mark_paid(db, uuid.uuid4(), uuid.uuid4(), Decimal("50000"))

    async def test_mark_paid_instructor_not_found_fails(self) -> None:
        """mark_paid when instructor profile not found raises ValueError."""
        application = _make_application(status=ApplicationStatus.ACCEPTED.value)

        db = AsyncMock()
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = application
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        inst_result = MagicMock()
        inst_result.scalar_one_or_none.return_value = None

        db.execute = AsyncMock(side_effect=[app_result, existing_result, inst_result])

        with pytest.raises(ValueError, match="Instructor not found"):
            await mark_paid(db, application.id, uuid.uuid4(), Decimal("50000"))


# ===========================================================================
# confirm_payment
# ===========================================================================

class TestConfirmPayment:
    """Tests for confirm_payment function."""

    async def test_confirm_payment_by_instructor(self) -> None:
        """Status changes to confirmed when instructor confirms."""
        instructor_user_id = uuid.uuid4()
        conf = _make_confirmation(
            instructor_user_id=instructor_user_id,
            status=PaymentConfirmationStatus.PENDING.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await confirm_payment(db, conf.id, instructor_user_id)

        assert conf.status == PaymentConfirmationStatus.CONFIRMED.value
        assert conf.instructor_confirmed_at is not None

    async def test_confirm_payment_wrong_user_fails(self) -> None:
        """PermissionError when wrong instructor tries to confirm."""
        conf = _make_confirmation(
            instructor_user_id=uuid.uuid4(),
            status=PaymentConfirmationStatus.PENDING.value,
        )
        wrong_user_id = uuid.uuid4()

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(PermissionError, match="Not authorized"):
            await confirm_payment(db, conf.id, wrong_user_id)

    async def test_confirm_already_confirmed_fails(self) -> None:
        """Cannot confirm an already-confirmed payment."""
        instructor_user_id = uuid.uuid4()
        conf = _make_confirmation(
            instructor_user_id=instructor_user_id,
            status=PaymentConfirmationStatus.CONFIRMED.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(ValueError, match="Cannot confirm"):
            await confirm_payment(db, conf.id, instructor_user_id)

    async def test_confirm_not_found_fails(self) -> None:
        """ValueError when confirmation not found."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(ValueError, match="not found"):
            await confirm_payment(db, uuid.uuid4(), uuid.uuid4())


# ===========================================================================
# dispute_payment
# ===========================================================================

class TestDisputePayment:
    """Tests for dispute_payment function."""

    async def test_dispute_payment(self) -> None:
        """Status changes to disputed with reason."""
        instructor_user_id = uuid.uuid4()
        conf = _make_confirmation(
            instructor_user_id=instructor_user_id,
            status=PaymentConfirmationStatus.PENDING.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        reason = "결제가 입금되지 않았습니다"
        result = await dispute_payment(db, conf.id, instructor_user_id, reason)

        assert conf.status == PaymentConfirmationStatus.DISPUTED.value
        assert conf.dispute_reason == reason

    async def test_dispute_wrong_user_fails(self) -> None:
        """PermissionError when wrong user disputes."""
        conf = _make_confirmation(
            instructor_user_id=uuid.uuid4(),
            status=PaymentConfirmationStatus.PENDING.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(PermissionError, match="Not authorized"):
            await dispute_payment(db, conf.id, uuid.uuid4(), "reason")

    async def test_dispute_already_confirmed_fails(self) -> None:
        """Cannot dispute an already-confirmed payment."""
        instructor_user_id = uuid.uuid4()
        conf = _make_confirmation(
            instructor_user_id=instructor_user_id,
            status=PaymentConfirmationStatus.CONFIRMED.value,
        )

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = conf
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(ValueError, match="Cannot dispute"):
            await dispute_payment(db, conf.id, instructor_user_id, "reason")

    async def test_dispute_not_found_fails(self) -> None:
        """ValueError when confirmation not found."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        with pytest.raises(ValueError, match="not found"):
            await dispute_payment(db, uuid.uuid4(), uuid.uuid4(), "reason")


# ===========================================================================
# get_on_time_payment_rate
# ===========================================================================

class TestGetOnTimePaymentRate:
    """Tests for get_on_time_payment_rate function."""

    async def test_correct_ratio_calculation(self) -> None:
        """Correct ratio: 3 confirmed out of 4 total = 0.75."""
        center_user_id = uuid.uuid4()

        db = AsyncMock()

        # 1. Total count
        total_result = MagicMock()
        total_result.scalar_one.return_value = 4
        # 2. Confirmed count
        confirmed_result = MagicMock()
        confirmed_result.scalar_one.return_value = 3

        db.execute = AsyncMock(side_effect=[total_result, confirmed_result])

        rate = await get_on_time_payment_rate(db, center_user_id)
        assert rate == 0.75

    async def test_no_payments_returns_1(self) -> None:
        """No data (0 total) returns 1.0 (assume good)."""
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 0
        db.execute = AsyncMock(return_value=total_result)

        rate = await get_on_time_payment_rate(db, uuid.uuid4())
        assert rate == 1.0

    async def test_all_confirmed_returns_1(self) -> None:
        """All confirmed returns 1.0."""
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 5
        confirmed_result = MagicMock()
        confirmed_result.scalar_one.return_value = 5
        db.execute = AsyncMock(side_effect=[total_result, confirmed_result])

        rate = await get_on_time_payment_rate(db, uuid.uuid4())
        assert rate == 1.0

    async def test_none_confirmed_returns_0(self) -> None:
        """None confirmed out of some total returns 0.0."""
        db = AsyncMock()
        total_result = MagicMock()
        total_result.scalar_one.return_value = 3
        confirmed_result = MagicMock()
        confirmed_result.scalar_one.return_value = 0
        db.execute = AsyncMock(side_effect=[total_result, confirmed_result])

        rate = await get_on_time_payment_rate(db, uuid.uuid4())
        assert rate == 0.0


# ===========================================================================
# get_by_user
# ===========================================================================

class TestGetByUser:
    """Tests for get_by_user function."""

    async def test_returns_list_of_confirmations(self) -> None:
        """Returns a list of PaymentConfirmation objects."""
        conf1 = _make_confirmation()
        conf2 = _make_confirmation()

        db = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [conf1, conf2]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        results = await get_by_user(db, uuid.uuid4())
        assert len(results) == 2

    async def test_returns_empty_list_when_no_records(self) -> None:
        """Returns empty list when no records."""
        db = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        results = await get_by_user(db, uuid.uuid4())
        assert results == []
