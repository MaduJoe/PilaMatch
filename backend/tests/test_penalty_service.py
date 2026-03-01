"""Unit tests for Penalty Service (v4.0).

Tests cover recording no-show, same-day cancel, late, and cancel-after-confirm
penalties, including suspension/demotion effects and 3-strike permanent ban.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import (
    PenaltyType,
    PenaltyStatus,
    TeacherTier,
    CenterTier,
)
from app.services.penalty_service import (
    record_no_show,
    record_same_day_cancel,
    record_late,
    record_cancel_after_confirm,
    get_recent_penalty_counts,
    is_suspended,
    is_restricted_from_today_class,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    user_id: Optional[uuid.UUID] = None,
    role: str = "instructor",
    no_show_count: int = 0,
    is_suspended_flag: bool = False,
    tier: Optional[str] = None,
    suspension_until: Optional[datetime] = None,
    restriction_until: Optional[datetime] = None,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    user.no_show_count = no_show_count
    user.is_suspended = is_suspended_flag
    user.tier = tier or TeacherTier.T2_VERIFIED.value
    user.tier_computed_at = None
    user.suspension_until = suspension_until
    user.restriction_until = restriction_until
    return user


def _make_penalty_record(**kwargs) -> MagicMock:
    """Create a fake PenaltyRecord returned after commit/refresh."""
    record = MagicMock()
    record.id = uuid.uuid4()
    record.user_id = kwargs.get("user_id", uuid.uuid4())
    record.penalty_type = kwargs.get("penalty_type", PenaltyType.NO_SHOW.value)
    record.status = kwargs.get("status", PenaltyStatus.ACTIVE.value)
    record.reported_by = kwargs.get("reported_by")
    record.suspend_until = kwargs.get("suspend_until")
    record.restrict_until = kwargs.get("restrict_until")
    record.description = kwargs.get("description")
    record.evidence_snapshot = kwargs.get("evidence_snapshot")
    record.created_at = kwargs.get("created_at", datetime.utcnow())
    return record


def _mock_db_for_penalty(
    user: Optional[MagicMock] = None,
) -> AsyncMock:
    """Build mock db for penalty recording functions.

    The penalty functions do:
    1. db.add(record) -- we track via db.add
    2. select(User).where(...) -> user
    3. db.commit()
    4. db.refresh(record) -- noop
    Also, event_log.log() is attempted in a try/except.
    """
    db = AsyncMock()

    # Capture the record added via db.add
    added_records = []

    def capture_add(obj):
        added_records.append(obj)

    db.add = MagicMock(side_effect=capture_add)
    db._added_records = added_records

    # User query
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    db.execute = AsyncMock(return_value=user_result)

    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    return db


# ===========================================================================
# record_no_show
# ===========================================================================

class TestRecordNoShow:
    """Tests for record_no_show function."""

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_creates_penalty(self, mock_event_cls) -> None:
        """Creates a penalty record with type NO_SHOW."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(no_show_count=0, role="instructor")
        reporter_id = uuid.uuid4()
        db = _mock_db_for_penalty(user=user)

        record = await record_no_show(db, user.id, reporter_id)

        # A record was added
        assert db.add.called
        added = db._added_records[0]
        assert added.penalty_type == PenaltyType.NO_SHOW.value
        assert added.status == PenaltyStatus.ACTIVE.value

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_suspends_user(self, mock_event_cls) -> None:
        """User.suspension_until is set to 14 days from now."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(no_show_count=0, role="instructor")
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        assert user.suspension_until is not None
        # Should be approximately 14 days from now
        expected = datetime.utcnow() + timedelta(days=14)
        delta = abs((user.suspension_until - expected).total_seconds())
        assert delta < 5  # Within 5 seconds

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_demotes_to_t1(self, mock_event_cls) -> None:
        """User.tier becomes t1_basic after no-show."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(
            no_show_count=0,
            role="instructor",
            tier=TeacherTier.T2_VERIFIED.value,
        )
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        assert user.tier == TeacherTier.T1_BASIC.value

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_demotes_studio_to_c1(self, mock_event_cls) -> None:
        """Studio user's tier becomes c1_basic after no-show."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(
            no_show_count=0,
            role="studio",
            tier=CenterTier.C2_VERIFIED.value,
        )
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        assert user.tier == CenterTier.C1_BASIC.value

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_3_strikes_permanent_suspension(self, mock_event_cls) -> None:
        """is_suspended=True after 3 no-shows."""
        mock_event_cls.return_value.log = AsyncMock()
        # User already has 2 no-shows; this will be the 3rd
        user = _make_user(no_show_count=2, role="instructor")
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        # no_show_count should be 3
        assert user.no_show_count == 3
        assert user.is_suspended is True

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_increments_count(self, mock_event_cls) -> None:
        """no_show_count is incremented by 1."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(no_show_count=1, role="instructor")
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        assert user.no_show_count == 2

    @patch("app.services.event_log.EventLogService")
    async def test_record_no_show_2_strikes_not_permanently_suspended(self, mock_event_cls) -> None:
        """User with 2 no-shows is NOT permanently suspended (only at 3)."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(no_show_count=1, role="instructor")
        user.is_suspended = False
        db = _mock_db_for_penalty(user=user)

        await record_no_show(db, user.id, uuid.uuid4())

        assert user.no_show_count == 2
        # is_suspended should still be False (was set as attribute, not True)
        # record_no_show only sets is_suspended=True when count >= 3
        assert user.is_suspended is not True or user.no_show_count >= 3


# ===========================================================================
# record_same_day_cancel
# ===========================================================================

class TestRecordSameDayCancel:
    """Tests for record_same_day_cancel function."""

    async def test_record_same_day_cancel_restricts_user(self) -> None:
        """restriction_until is set to 7 days from now."""
        user = _make_user(role="instructor")
        db = _mock_db_for_penalty(user=user)

        await record_same_day_cancel(db, user.id, uuid.uuid4())

        assert user.restriction_until is not None
        expected = datetime.utcnow() + timedelta(days=7)
        delta = abs((user.restriction_until - expected).total_seconds())
        assert delta < 5

    async def test_record_same_day_cancel_creates_correct_type(self) -> None:
        """Creates a record with penalty_type = same_day_cancel."""
        user = _make_user(role="instructor")
        db = _mock_db_for_penalty(user=user)

        await record_same_day_cancel(db, user.id, uuid.uuid4())

        added = db._added_records[0]
        assert added.penalty_type == PenaltyType.SAME_DAY_CANCEL.value

    async def test_record_same_day_cancel_does_not_suspend(self) -> None:
        """Same-day cancel restricts but does not suspend."""
        user = _make_user(role="instructor")
        user.suspension_until = None
        db = _mock_db_for_penalty(user=user)

        await record_same_day_cancel(db, user.id, uuid.uuid4())

        # suspension_until should remain None (only restriction_until is set)
        assert user.suspension_until is None


# ===========================================================================
# record_late
# ===========================================================================

class TestRecordLate:
    """Tests for record_late function."""

    async def test_record_late_creates_record(self) -> None:
        """Creates a penalty record with type LATE but no suspension."""
        user = _make_user(role="instructor")
        db = _mock_db_for_penalty(user=user)

        # record_late does NOT query user, just creates and commits
        # Re-mock db for this simpler flow
        db2 = AsyncMock()
        added = []
        db2.add = MagicMock(side_effect=lambda obj: added.append(obj))
        db2.commit = AsyncMock()
        db2.refresh = AsyncMock()

        await record_late(db2, user.id, uuid.uuid4())

        assert len(added) == 1
        assert added[0].penalty_type == PenaltyType.LATE.value

    async def test_record_late_no_suspension(self) -> None:
        """Late penalty does not set suspension_until."""
        user = _make_user(role="instructor")
        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        await record_late(db, user.id, uuid.uuid4())

        record = added[0]
        assert record.suspend_until is None
        assert record.restrict_until is None


# ===========================================================================
# record_cancel_after_confirm
# ===========================================================================

class TestRecordCancelAfterConfirm:
    """Tests for record_cancel_after_confirm function."""

    async def test_record_cancel_after_confirm_creates_record(self) -> None:
        """Creates a penalty record for center cancellation after confirm."""
        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        center_id = uuid.uuid4()
        reporter_id = uuid.uuid4()
        await record_cancel_after_confirm(db, center_id, reporter_id)

        assert len(added) == 1
        assert added[0].penalty_type == PenaltyType.CANCEL_AFTER_CONFIRM.value
        assert added[0].user_id == center_id


# ===========================================================================
# get_recent_penalty_counts
# ===========================================================================

class TestGetRecentPenaltyCounts:
    """Tests for get_recent_penalty_counts function."""

    async def test_get_recent_penalty_counts_returns_correct_counts(self) -> None:
        """Returns correct counts by type."""
        user_id = uuid.uuid4()

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.all.return_value = [
            (PenaltyType.NO_SHOW.value, 2),
            (PenaltyType.LATE.value, 1),
        ]
        db.execute = AsyncMock(return_value=result_mock)

        counts = await get_recent_penalty_counts(db, user_id)

        assert counts["no_show"] == 2
        assert counts["late"] == 1
        assert counts["same_day_cancel"] == 0
        assert counts["cancel_after_confirm"] == 0

    async def test_get_recent_penalty_counts_all_zero(self) -> None:
        """Returns all zeros when no penalties found."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.all.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        counts = await get_recent_penalty_counts(db, uuid.uuid4())

        for pt in PenaltyType:
            assert counts[pt.value] == 0


# ===========================================================================
# is_suspended / is_restricted_from_today_class
# ===========================================================================

class TestIsSuspended:
    """Tests for is_suspended function."""

    async def test_permanently_suspended_user(self) -> None:
        """User with is_suspended=True returns True."""
        user = _make_user(is_suspended_flag=True)
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_suspended(db, user.id) is True

    async def test_temporarily_suspended_user(self) -> None:
        """User with future suspension_until returns True."""
        user = _make_user(
            is_suspended_flag=False,
            suspension_until=datetime.utcnow() + timedelta(days=7),
        )
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_suspended(db, user.id) is True

    async def test_not_suspended_user(self) -> None:
        """User with no suspension returns False."""
        user = _make_user(is_suspended_flag=False, suspension_until=None)
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_suspended(db, user.id) is False

    async def test_expired_suspension(self) -> None:
        """User with past suspension_until returns False."""
        user = _make_user(
            is_suspended_flag=False,
            suspension_until=datetime.utcnow() - timedelta(days=1),
        )
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_suspended(db, user.id) is False

    async def test_user_not_found(self) -> None:
        """Non-existent user returns False."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_suspended(db, uuid.uuid4()) is False


class TestIsRestrictedFromTodayClass:
    """Tests for is_restricted_from_today_class function."""

    async def test_restricted_user(self) -> None:
        """User with future restriction_until returns True."""
        user = _make_user(
            restriction_until=datetime.utcnow() + timedelta(days=3),
        )
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_restricted_from_today_class(db, user.id) is True

    async def test_not_restricted_user(self) -> None:
        """User with no restriction returns False."""
        user = _make_user(restriction_until=None)
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_restricted_from_today_class(db, user.id) is False

    async def test_expired_restriction(self) -> None:
        """User with past restriction_until returns False."""
        user = _make_user(
            restriction_until=datetime.utcnow() - timedelta(days=1),
        )
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        assert await is_restricted_from_today_class(db, user.id) is False
