"""Tests for PilaMatch Auto Dispatch Engine.

Covers:
1. Urgency score calculation (time-to-class -> 0-100 score)
2. Reliability score calculation (Tier + dispatch history + no-shows + completions + check-in)
3. Dispatch wave creation (candidate selection -> DispatchRecord creation)
4. Accept dispatch (FCFS, race condition guard, contact reveal)
5. Decline dispatch (status transition, wave advancement)
6. Start auto dispatch (entry point, fallback to manual)
7. Timeout handling (stale dispatches -> TIMEOUT status)
"""

import uuid
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import (
    DispatchStatus,
    ApplicationStatus,
    JobPostStatus,
    TeacherTier,
)
from app.services.dispatch_engine import (
    calculate_urgency_score,
    calculate_reliability_score,
    DispatchEngine,
    WAVE_CONFIG,
    _TIER_WEIGHT_MAP,
    _TIER_WEIGHT_DEFAULT,
)
from app.models.dispatch_record import DispatchRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_instructor_profile(
    user_id: Optional[uuid.UUID] = None,
    dispatch_success_rate: Decimal = Decimal("0.800"),
    total_dispatches: int = 10,
    total_dispatch_accepts: int = 8,
    total_completions: int = 5,
    total_checkins: int = 5,
    avg_checkin_distance_m: Optional[Decimal] = Decimal("120.0"),
    display_name: str = "Test Instructor",
    phone: str = "010-1234-5678",
) -> MagicMock:
    """Create a fake InstructorProfile for dispatch tests."""
    profile = MagicMock()
    profile.id = str(uuid.uuid4())
    profile.user_id = user_id or str(uuid.uuid4())
    profile.dispatch_success_rate = dispatch_success_rate
    profile.total_dispatches = total_dispatches
    profile.total_dispatch_accepts = total_dispatch_accepts
    profile.total_completions = total_completions
    profile.total_checkins = total_checkins
    profile.avg_checkin_distance_m = avg_checkin_distance_m
    profile.display_name = display_name
    profile.phone = phone
    profile.address = None
    return profile


def _make_user(
    user_id: Optional[str] = None,
    tier: Optional[str] = None,
    no_show_count: int = 0,
    is_active: bool = True,
    suspension_until: Optional[datetime] = None,
) -> MagicMock:
    """Create a fake User for dispatch tests."""
    user = MagicMock()
    user.id = user_id or str(uuid.uuid4())
    user.tier = tier
    user.no_show_count = no_show_count
    user.is_active = is_active
    user.suspension_until = suspension_until
    return user


def _make_dispatch_record(
    record_id: Optional[str] = None,
    job_post_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
    user_id: Optional[str] = None,
    wave_number: int = 1,
    status: str = DispatchStatus.DISPATCHED.value,
    dispatched_at: Optional[datetime] = None,
    distance_km: Decimal = Decimal("2.5"),
    reliability_score: int = 75,
) -> MagicMock:
    """Create a fake DispatchRecord."""
    record = MagicMock(spec=DispatchRecord)
    record.id = record_id or str(uuid.uuid4())
    record.job_post_id = job_post_id or str(uuid.uuid4())
    record.instructor_id = instructor_id or str(uuid.uuid4())
    record.user_id = user_id or str(uuid.uuid4())
    record.wave_number = wave_number
    record.status = status
    record.dispatched_at = dispatched_at or datetime.utcnow()
    record.responded_at = None
    record.distance_km = distance_km
    record.matching_score = reliability_score
    record.reliability_score = reliability_score
    return record


def _make_job_post(
    job_post_id: Optional[str] = None,
    status: str = JobPostStatus.OPEN.value,
    latitude: Optional[Decimal] = Decimal("37.4979"),
    longitude: Optional[Decimal] = Decimal("127.0276"),
    title: str = "Urgent Sub",
    studio_id: Optional[str] = None,
    dispatch_wave: int = 0,
    dispatch_mode: str = "auto_dispatch",
    date_val: Optional[date] = None,
    start_time_val: Optional[time] = None,
    category: str = "pilates",
) -> MagicMock:
    """Create a fake JobPost for dispatch tests."""
    job = MagicMock()
    job.id = job_post_id or str(uuid.uuid4())
    job.status = status
    job.latitude = latitude
    job.longitude = longitude
    job.title = title
    job.studio_id = studio_id or str(uuid.uuid4())
    job.dispatch_wave = dispatch_wave
    job.dispatch_mode = dispatch_mode
    job.dispatch_started_at = None
    job.auto_accepted_at = None
    job.matched_instructor_id = None
    job.urgency_score = None
    job.category = category
    # Date/time for urgency calculation
    job.date = date_val or (datetime.utcnow() + timedelta(hours=1)).date()
    job.start_time = start_time_val or (datetime.utcnow() + timedelta(hours=1)).time()
    return job


# ===========================================================================
# 1. Urgency Score Calculation
# ===========================================================================

class TestCalculateUrgencyScore:
    """Tests for calculate_urgency_score -- time-to-class -> 0-100 urgency."""

    def test_class_in_1h_returns_100(self) -> None:
        """Class starting in < 2 hours should have urgency 100."""
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 100.0

    def test_class_in_3h_returns_80(self) -> None:
        """Class starting in 2-4 hours should have urgency 80."""
        now = datetime.utcnow()
        future = now + timedelta(hours=3)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 80.0

    def test_class_in_6h_returns_60(self) -> None:
        """Class starting in 4-8 hours should have urgency 60."""
        now = datetime.utcnow()
        future = now + timedelta(hours=6)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 60.0

    def test_class_in_12h_returns_40(self) -> None:
        """Class starting in 8-24 hours should have urgency 40."""
        now = datetime.utcnow()
        future = now + timedelta(hours=12)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 40.0

    def test_class_in_48h_returns_20(self) -> None:
        """Class starting in > 24 hours should have urgency 20."""
        now = datetime.utcnow()
        future = now + timedelta(hours=48)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 20.0

    def test_class_in_30_minutes_returns_100(self) -> None:
        """Class starting very soon (30 min) should return max urgency."""
        now = datetime.utcnow()
        future = now + timedelta(minutes=30)
        result = calculate_urgency_score(future.date(), future.time())
        assert result == 100.0

    def test_score_is_float(self) -> None:
        """Urgency score should always be a float."""
        now = datetime.utcnow()
        future = now + timedelta(hours=5)
        result = calculate_urgency_score(future.date(), future.time())
        assert isinstance(result, float)


# ===========================================================================
# 2. Reliability Score Calculation
# ===========================================================================

class TestCalculateReliabilityScore:
    """Tests for calculate_reliability_score -- weighted instructor ranking."""

    @pytest.mark.asyncio
    async def test_t3_with_high_stats_gives_high_score(self) -> None:
        """T3 Pro user with excellent stats should score high (>= 70)."""
        db = AsyncMock()
        profile = _make_instructor_profile(
            dispatch_success_rate=Decimal("0.900"),
            total_completions=10,
            avg_checkin_distance_m=Decimal("50.0"),
        )
        user = _make_user(tier=TeacherTier.T3_PRO.value, no_show_count=0)

        score = await calculate_reliability_score(db, profile, user)

        assert score >= 70

    @pytest.mark.asyncio
    async def test_t1_with_no_history_gives_low_score(self) -> None:
        """T1 Basic user with no dispatch history should score lower than T3 Pro.

        Expected breakdown:
        - Tier: T1=40 * 0.30 = 12
        - Dispatch success: 0 * 0.25 = 0
        - No-show: 100 * 0.20 = 20 (clean record)
        - Completions: 0 * 0.15 = 0
        - Check-in: avg_dist=None -> 0 -> <=200 -> 100 * 0.10 = 10
        Total = 42
        """
        db = AsyncMock()
        profile = _make_instructor_profile(
            dispatch_success_rate=Decimal("0.000"),
            total_dispatches=0,
            total_dispatch_accepts=0,
            total_completions=0,
            total_checkins=0,
            avg_checkin_distance_m=None,
        )
        user = _make_user(tier=TeacherTier.T1_BASIC.value, no_show_count=0)

        score = await calculate_reliability_score(db, profile, user)

        # T1 with no history scores 42 (tier 12 + clean no-show 20 + default checkin 10)
        assert score == 42

    @pytest.mark.asyncio
    async def test_no_shows_reduce_score(self) -> None:
        """Multiple no-shows should significantly reduce the score."""
        db = AsyncMock()
        profile = _make_instructor_profile(
            dispatch_success_rate=Decimal("0.800"),
            total_completions=5,
        )
        user_clean = _make_user(tier=TeacherTier.T2_VERIFIED.value, no_show_count=0)
        user_noshows = _make_user(tier=TeacherTier.T2_VERIFIED.value, no_show_count=3)

        score_clean = await calculate_reliability_score(db, profile, user_clean)
        score_noshows = await calculate_reliability_score(db, profile, user_noshows)

        assert score_clean > score_noshows

    @pytest.mark.asyncio
    async def test_no_tier_uses_default_weight(self) -> None:
        """User with no tier should use the default tier weight (20)."""
        db = AsyncMock()
        profile = _make_instructor_profile(
            dispatch_success_rate=Decimal("0.500"),
            total_completions=3,
        )
        user = _make_user(tier=None, no_show_count=0)

        score = await calculate_reliability_score(db, profile, user)

        # Tier component = 20 * 0.30 = 6
        # With other components, total should be moderate
        assert score >= 0
        assert score <= 100

    @pytest.mark.asyncio
    async def test_score_range_is_0_to_100(self) -> None:
        """Reliability score should always be 0-100 inclusive."""
        db = AsyncMock()
        profile = _make_instructor_profile(
            dispatch_success_rate=Decimal("1.000"),
            total_completions=50,
            avg_checkin_distance_m=Decimal("10.0"),
        )
        user = _make_user(tier=TeacherTier.T3_PRO.value, no_show_count=0)

        score = await calculate_reliability_score(db, profile, user)

        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_high_checkin_distance_reduces_score(self) -> None:
        """Instructor with high average check-in distance gets lower score."""
        db = AsyncMock()
        profile_close = _make_instructor_profile(
            avg_checkin_distance_m=Decimal("50.0"),
        )
        profile_far = _make_instructor_profile(
            avg_checkin_distance_m=Decimal("500.0"),
        )
        user = _make_user(tier=TeacherTier.T2_VERIFIED.value, no_show_count=0)

        score_close = await calculate_reliability_score(db, profile_close, user)
        score_far = await calculate_reliability_score(db, profile_far, user)

        assert score_close > score_far


# ===========================================================================
# 3. Dispatch Wave Creation
# ===========================================================================

class TestDispatchWave:
    """Tests for DispatchEngine.dispatch_wave -- creating DispatchRecord entries."""

    @pytest.mark.asyncio
    async def test_dispatch_wave_creates_records(self) -> None:
        """dispatch_wave should create DispatchRecord for each candidate."""
        job_post_id = str(uuid.uuid4())
        job_post = _make_job_post(job_post_id=job_post_id)

        db = AsyncMock()
        # First call: select JobPost
        job_result = MagicMock()
        job_result.scalar_one_or_none.return_value = job_post
        # Second call: select existing dispatch records (excluded IDs)
        excluded_result = MagicMock()
        excluded_result.all.return_value = []

        db.execute = AsyncMock(side_effect=[job_result, excluded_result])
        db.add = MagicMock()
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        # Mock get_dispatch_candidates to return 3 candidates
        candidates = [
            {"instructor_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "distance_km": 1.5, "reliability_score": 90, "matching_score": 90},
            {"instructor_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "distance_km": 3.0, "reliability_score": 75, "matching_score": 75},
            {"instructor_id": str(uuid.uuid4()), "user_id": str(uuid.uuid4()), "distance_km": 4.5, "reliability_score": 60, "matching_score": 60},
        ]

        with patch.object(engine, "get_dispatch_candidates", return_value=candidates):
            # Need to also mock the notification service and update queries
            with patch("app.services.dispatch_engine.NotificationService") as mock_notif_cls:
                mock_notif = AsyncMock()
                mock_notif_cls.return_value = mock_notif
                # Additional db.execute calls for update stats -- just return a mock
                db.execute = AsyncMock(side_effect=[job_result, excluded_result] + [MagicMock()] * 3)

                records = await engine.dispatch_wave(job_post_id, wave_number=1)

        assert len(records) == 3
        # All records should be DispatchRecord instances
        for record in records:
            assert isinstance(record, DispatchRecord)
            assert record.job_post_id == job_post_id
            assert record.status == DispatchStatus.DISPATCHED.value

    @pytest.mark.asyncio
    async def test_dispatch_wave_job_not_found_raises(self) -> None:
        """dispatch_wave should raise ValueError if job post not found."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="JOB_POST_NOT_FOUND"):
            await engine.dispatch_wave("nonexistent-id", wave_number=1)

    @pytest.mark.asyncio
    async def test_dispatch_wave_job_not_open_raises(self) -> None:
        """dispatch_wave should raise ValueError if job post is not OPEN."""
        job = _make_job_post(status=JobPostStatus.FILLED.value)
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = job
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="JOB_POST_NOT_OPEN"):
            await engine.dispatch_wave(str(job.id), wave_number=1)

    @pytest.mark.asyncio
    async def test_dispatch_wave_invalid_wave_number_raises(self) -> None:
        """dispatch_wave should raise ValueError for invalid wave number."""
        job = _make_job_post()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = job
        # Second call for excluded IDs (won't reach due to validation)
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="INVALID_WAVE_NUMBER"):
            await engine.dispatch_wave(str(job.id), wave_number=99)


# ===========================================================================
# 4. Accept Dispatch (Time-Window Model)
# ===========================================================================

class TestAcceptDispatch:
    """Tests for DispatchEngine.accept_dispatch -- time-window acceptance."""

    @pytest.mark.asyncio
    async def test_accept_dispatch_records_intent(self) -> None:
        """Accept marks record as accepted (intent) and returns pending status."""
        user_id = str(uuid.uuid4())
        record = _make_dispatch_record(user_id=user_id, status=DispatchStatus.DISPATCHED.value)
        job_post = _make_job_post(job_post_id=record.job_post_id)
        instructor_profile = _make_instructor_profile(user_id=user_id)
        studio_profile = MagicMock()
        studio_profile.user_id = str(uuid.uuid4())
        studio_profile.phone = "02-111-2222"
        studio_profile.business_name = "Test Studio"
        studio_profile.address = "Seoul"

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = record
            elif call_count == 2:
                result.scalar_one_or_none.return_value = job_post
            elif call_count == 3:
                result.scalar_one_or_none.return_value = instructor_profile
            elif call_count == 4:
                result.scalar_one_or_none.return_value = studio_profile
            elif call_count == 5:
                # accepted count query
                result.scalars.return_value.all.return_value = [record]
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.add = MagicMock()
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        with patch("app.services.dispatch_engine.NotificationService") as mock_notif_cls, \
             patch("app.services.dispatch_engine.EventLogService") as mock_event_cls:
            mock_notif_cls.return_value = AsyncMock()
            mock_event_cls.return_value = AsyncMock()

            response = await engine.accept_dispatch(str(record.id), user_id)

        assert record.status == DispatchStatus.ACCEPTED.value
        assert record.responded_at is not None
        assert response["status"] == "accepted_pending"
        assert "remaining_seconds" in response

    @pytest.mark.asyncio
    async def test_accept_dispatch_already_filled_raises(self) -> None:
        """If job is already FILLED, accept raises ALREADY_MATCHED."""
        user_id = str(uuid.uuid4())
        record = _make_dispatch_record(user_id=user_id, status=DispatchStatus.DISPATCHED.value)
        job_post = _make_job_post(job_post_id=record.job_post_id)
        job_post.status = "filled"

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = record
            elif call_count == 2:
                result.scalar_one_or_none.return_value = job_post
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="ALREADY_MATCHED"):
            await engine.accept_dispatch(str(record.id), user_id)

        assert record.status == DispatchStatus.CANCELLED.value

    @pytest.mark.asyncio
    async def test_accept_dispatch_not_owner_raises_permission_error(self) -> None:
        """Accepting dispatch owned by another user should raise PermissionError."""
        record = _make_dispatch_record(user_id=str(uuid.uuid4()))

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)
        different_user = str(uuid.uuid4())

        with pytest.raises(PermissionError, match="NOT_YOUR_DISPATCH"):
            await engine.accept_dispatch(str(record.id), different_user)

    @pytest.mark.asyncio
    async def test_accept_dispatch_already_responded_raises(self) -> None:
        """Accepting a record that is no longer DISPATCHED should raise ValueError."""
        user_id = str(uuid.uuid4())
        record = _make_dispatch_record(
            user_id=user_id,
            status=DispatchStatus.DECLINED.value,
        )

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="ALREADY_RESPONDED"):
            await engine.accept_dispatch(str(record.id), user_id)

    @pytest.mark.asyncio
    async def test_accept_dispatch_not_found_raises(self) -> None:
        """Accepting nonexistent dispatch record should raise ValueError."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="DISPATCH_RECORD_NOT_FOUND"):
            await engine.accept_dispatch("fake-id", str(uuid.uuid4()))


# ===========================================================================
# 5. Decline Dispatch
# ===========================================================================

class TestDeclineDispatch:
    """Tests for DispatchEngine.decline_dispatch."""

    @pytest.mark.asyncio
    async def test_decline_sets_status_declined(self) -> None:
        """Declining a dispatch should set status to DECLINED."""
        user_id = str(uuid.uuid4())
        record = _make_dispatch_record(user_id=user_id, status=DispatchStatus.DISPATCHED.value)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        with patch.object(engine, "_maybe_advance_wave", new_callable=AsyncMock):
            await engine.decline_dispatch(str(record.id), user_id)

        assert record.status == DispatchStatus.DECLINED.value
        assert record.responded_at is not None

    @pytest.mark.asyncio
    async def test_decline_not_owner_raises_permission_error(self) -> None:
        """Declining dispatch owned by another user should raise PermissionError."""
        record = _make_dispatch_record(user_id=str(uuid.uuid4()))

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(PermissionError, match="NOT_YOUR_DISPATCH"):
            await engine.decline_dispatch(str(record.id), str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_decline_already_responded_raises(self) -> None:
        """Declining a record that is already responded should raise ValueError."""
        user_id = str(uuid.uuid4())
        record = _make_dispatch_record(
            user_id=user_id,
            status=DispatchStatus.ACCEPTED.value,
        )

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="ALREADY_RESPONDED"):
            await engine.decline_dispatch(str(record.id), user_id)


# ===========================================================================
# 6. Start Auto Dispatch (Entry Point)
# ===========================================================================

class TestStartAutoDispatch:
    """Tests for DispatchEngine.start_auto_dispatch -- full entry point."""

    @pytest.mark.asyncio
    async def test_start_dispatches_wave_1(self) -> None:
        """start_auto_dispatch should calculate urgency and dispatch wave 1."""
        job_post_id = str(uuid.uuid4())
        job_post = _make_job_post(job_post_id=job_post_id)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = job_post
        db.execute = AsyncMock(return_value=result)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        mock_records = [_make_dispatch_record(job_post_id=job_post_id)]

        with patch.object(engine, "dispatch_wave", new_callable=AsyncMock, return_value=mock_records) as mock_wave, \
             patch("app.services.dispatch_engine.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()

            records = await engine.start_auto_dispatch(job_post_id)

        assert len(records) == 1
        mock_wave.assert_awaited_once_with(job_post_id, wave_number=1)
        assert job_post.dispatch_mode == "auto_dispatch"
        assert job_post.urgency_score is not None

    @pytest.mark.asyncio
    async def test_start_dispatch_job_not_found_raises(self) -> None:
        """start_auto_dispatch should raise ValueError if job not found."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        engine = DispatchEngine(db)

        with pytest.raises(ValueError, match="JOB_POST_NOT_FOUND"):
            await engine.start_auto_dispatch("fake-id")

    @pytest.mark.asyncio
    async def test_no_candidates_fallback_to_manual(self) -> None:
        """If all 3 waves return no candidates, should fall back to manual mode."""
        job_post_id = str(uuid.uuid4())
        job_post = _make_job_post(job_post_id=job_post_id)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = job_post
        db.execute = AsyncMock(return_value=result)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        with patch.object(engine, "dispatch_wave", new_callable=AsyncMock, return_value=[]) as mock_wave, \
             patch.object(engine, "_fallback_to_manual", new_callable=AsyncMock) as mock_fallback, \
             patch("app.services.dispatch_engine.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()

            records = await engine.start_auto_dispatch(job_post_id)

        assert len(records) == 0
        # All 3 waves tried
        assert mock_wave.await_count == 3
        # Fallback triggered
        mock_fallback.assert_awaited_once_with(job_post_id, job_post)


# ===========================================================================
# 7. Dispatch Timeouts
# ===========================================================================

class TestCheckDispatchTimeouts:
    """Tests for DispatchEngine.check_dispatch_timeouts."""

    @pytest.mark.asyncio
    async def test_timeout_old_dispatches(self) -> None:
        """Dispatches past their timeout window should become TIMEOUT."""
        old_record = _make_dispatch_record(
            dispatched_at=datetime.utcnow() - timedelta(minutes=10),
            status=DispatchStatus.DISPATCHED.value,
            wave_number=1,
        )

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count <= 3:
                # Iterate over WAVE_CONFIG (3 waves)
                scalars = MagicMock()
                if call_count == 1:
                    # Wave 1 returns our timed-out record
                    scalars.all.return_value = [old_record]
                else:
                    scalars.all.return_value = []
                result.scalars.return_value = scalars
            elif call_count == 4:
                # select JobPost (check if filled)
                jp = MagicMock()
                jp.status = "open"
                result.scalar_one_or_none.return_value = jp
            else:
                result.scalars.return_value = MagicMock(first=MagicMock(return_value=None))
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)

        with patch.object(engine, "_maybe_advance_wave", new_callable=AsyncMock), \
             patch.object(engine, "finalize_dispatch_window", new_callable=AsyncMock, return_value=None):
            count = await engine.check_dispatch_timeouts()

        assert count == 1
        assert old_record.status == DispatchStatus.TIMEOUT.value
        assert old_record.responded_at is not None

    @pytest.mark.asyncio
    async def test_no_timeouts_returns_zero(self) -> None:
        """When no dispatches are past timeout, should return 0."""
        db = AsyncMock()

        async def mock_execute(stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.all.return_value = []
            result.scalars.return_value = scalars
            result.all.return_value = []
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        engine = DispatchEngine(db)
        count = await engine.check_dispatch_timeouts()

        assert count == 0


# ===========================================================================
# 8. Wave Configuration Validation
# ===========================================================================

class TestWaveConfig:
    """Tests for the WAVE_CONFIG constants."""

    def test_wave_config_has_3_waves(self) -> None:
        """WAVE_CONFIG should define exactly 3 waves."""
        assert len(WAVE_CONFIG) == 3

    def test_wave_1_config(self) -> None:
        """Wave 1 should have 5km radius, 5 max candidates, 120s window."""
        wave1 = WAVE_CONFIG[0]
        assert wave1["wave"] == 1
        assert wave1["radius_km"] == 5
        assert wave1["max_candidates"] == 5
        assert wave1["timeout_seconds"] == 120

    def test_wave_radii_expand(self) -> None:
        """Each wave should have a larger radius than the previous."""
        radii = [cfg["radius_km"] for cfg in WAVE_CONFIG]
        assert radii == sorted(radii)
        assert len(set(radii)) == len(radii)  # all different

    def test_wave_candidate_counts_increase(self) -> None:
        """Each wave should allow more candidates than the previous."""
        counts = [cfg["max_candidates"] for cfg in WAVE_CONFIG]
        assert counts == sorted(counts)

    def test_tier_weight_map_completeness(self) -> None:
        """Tier weight map should cover all TeacherTier values."""
        for tier in TeacherTier:
            assert tier.value in _TIER_WEIGHT_MAP
