"""Tests for PilaMatch GPS Check-in Service.

Covers:
1. Valid check-in (within 200m) -- distance calculation, record creation, stats update
2. Invalid check-in (too far) -- is_valid=False
3. Duplicate check-in prevention
4. No accepted application rejection
5. Instructor stats update (running average)
6. Check-in status retrieval
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.checkin_record import CheckinRecord
from app.services.checkin import CheckinService, VALID_CHECKIN_DISTANCE_M


# ---------------------------------------------------------------------------
# GPS Coordinate Constants
# ---------------------------------------------------------------------------

# Studio location: Gangnam (37.4979, 127.0276)
STUDIO_LAT = 37.4979
STUDIO_LNG = 127.0276

# Instructor close: ~130m away
INSTRUCTOR_CLOSE_LAT = 37.4989
INSTRUCTOR_CLOSE_LNG = 127.0286

# Instructor far: ~3.2km away
INSTRUCTOR_FAR_LAT = 37.5200
INSTRUCTOR_FAR_LNG = 127.0500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job_post(
    job_post_id: Optional[str] = None,
    latitude: Optional[Decimal] = Decimal(str(STUDIO_LAT)),
    longitude: Optional[Decimal] = Decimal(str(STUDIO_LNG)),
    studio_id: Optional[str] = None,
) -> MagicMock:
    """Create a fake JobPost with GPS coordinates."""
    job = MagicMock()
    job.id = job_post_id or str(uuid.uuid4())
    job.latitude = latitude
    job.longitude = longitude
    job.studio_id = studio_id or str(uuid.uuid4())
    return job


def _make_instructor_profile(
    profile_id: Optional[str] = None,
    user_id: Optional[str] = None,
    total_checkins: int = 0,
    avg_checkin_distance_m: Optional[Decimal] = None,
) -> MagicMock:
    """Create a fake InstructorProfile for check-in tests."""
    profile = MagicMock()
    profile.id = profile_id or str(uuid.uuid4())
    profile.user_id = user_id or str(uuid.uuid4())
    profile.total_checkins = total_checkins
    profile.avg_checkin_distance_m = avg_checkin_distance_m
    return profile


def _make_application(
    app_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
    job_post_id: Optional[str] = None,
    status: str = "accepted",
) -> MagicMock:
    """Create a fake Application."""
    app = MagicMock()
    app.id = app_id or str(uuid.uuid4())
    app.instructor_id = instructor_id or str(uuid.uuid4())
    app.job_post_id = job_post_id or str(uuid.uuid4())
    app.status = status
    return app


def _setup_checkin_db(
    job_post: MagicMock,
    instructor: MagicMock,
    application: MagicMock,
    existing_checkin: MagicMock = None,
) -> AsyncMock:
    """Build a mock db session for the check-in flow.

    Sequence of db.execute calls in CheckinService.check_in:
    1. select JobPost
    2. select InstructorProfile (by user_id)
    3. select Application (accepted for this job+instructor)
    4. select CheckinRecord (duplicate check)
    ...then after creation:
    5. select StudioProfile (for notification)
    """
    db = AsyncMock()
    call_count = 0

    async def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalar_one_or_none.return_value = job_post
        elif call_count == 2:
            result.scalar_one_or_none.return_value = instructor
        elif call_count == 3:
            result.scalar_one_or_none.return_value = application
        elif call_count == 4:
            result.scalar_one_or_none.return_value = existing_checkin
        else:
            # Studio profile lookup for notification -- return None to skip
            result.scalar_one_or_none.return_value = None
        return result

    db.execute = AsyncMock(side_effect=mock_execute)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


# ===========================================================================
# 1. Valid Check-in (close distance)
# ===========================================================================

class TestCheckinValid:
    """Tests for valid GPS check-in within VALID_CHECKIN_DISTANCE_M (200m)."""

    @pytest.mark.asyncio
    async def test_checkin_valid_within_200m(self) -> None:
        """Instructor at ~130m should produce is_valid=True."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_CLOSE_LAT,
                longitude=INSTRUCTOR_CLOSE_LNG,
            )

        assert isinstance(record, CheckinRecord)
        assert record.is_valid is True
        # Distance should be roughly 100-200m
        assert float(record.distance_meters) < VALID_CHECKIN_DISTANCE_M

    @pytest.mark.asyncio
    async def test_checkin_valid_exact_location(self) -> None:
        """Instructor at exact studio location should have is_valid=True and 0m distance."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=STUDIO_LAT,
                longitude=STUDIO_LNG,
            )

        assert record.is_valid is True
        assert float(record.distance_meters) == 0.0


# ===========================================================================
# 2. Invalid Check-in (too far)
# ===========================================================================

class TestCheckinInvalidTooFar:
    """Tests for invalid check-in exceeding VALID_CHECKIN_DISTANCE_M."""

    @pytest.mark.asyncio
    async def test_checkin_invalid_3km_away(self) -> None:
        """Instructor at ~3.2km should produce is_valid=False."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_FAR_LAT,
                longitude=INSTRUCTOR_FAR_LNG,
            )

        assert record.is_valid is False
        assert float(record.distance_meters) > VALID_CHECKIN_DISTANCE_M

    @pytest.mark.asyncio
    async def test_checkin_invalid_500m_away(self) -> None:
        """Instructor at ~500m should produce is_valid=False."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        # ~500m north of studio
        lat_500m = STUDIO_LAT + 0.0045  # roughly 500m
        lng_500m = STUDIO_LNG

        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=lat_500m,
                longitude=lng_500m,
            )

        assert record.is_valid is False
        assert float(record.distance_meters) > 200


# ===========================================================================
# 3. Duplicate Check-in Prevention
# ===========================================================================

class TestCheckinDuplicate:
    """Tests for duplicate check-in blocking."""

    @pytest.mark.asyncio
    async def test_duplicate_checkin_raises_error(self) -> None:
        """Second check-in for same job+user should raise ALREADY_CHECKED_IN."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        existing_checkin = MagicMock()  # A previous check-in exists

        db = _setup_checkin_db(job_post, instructor, application, existing_checkin=existing_checkin)

        service = CheckinService(db)

        with pytest.raises(ValueError, match="ALREADY_CHECKED_IN"):
            await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_CLOSE_LAT,
                longitude=INSTRUCTOR_CLOSE_LNG,
            )


# ===========================================================================
# 4. No Accepted Application
# ===========================================================================

class TestCheckinNoAcceptedApplication:
    """Tests for check-in without accepted application."""

    @pytest.mark.asyncio
    async def test_no_accepted_application_raises_error(self) -> None:
        """Check-in without an accepted application should raise NO_ACCEPTED_APPLICATION."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(user_id=user_id)
        job_post = _make_job_post()

        db = _setup_checkin_db(job_post, instructor, application=None)

        service = CheckinService(db)

        with pytest.raises(ValueError, match="NO_ACCEPTED_APPLICATION"):
            await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_CLOSE_LAT,
                longitude=INSTRUCTOR_CLOSE_LNG,
            )

    @pytest.mark.asyncio
    async def test_job_post_not_found_raises(self) -> None:
        """Check-in with nonexistent job post should raise JOB_POST_NOT_FOUND."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = CheckinService(db)

        with pytest.raises(ValueError, match="JOB_POST_NOT_FOUND"):
            await service.check_in("fake-id", str(uuid.uuid4()), 37.5, 127.0)

    @pytest.mark.asyncio
    async def test_job_post_no_gps_raises(self) -> None:
        """Check-in for job post without GPS coordinates should raise JOB_POST_NO_GPS."""
        job_post = _make_job_post(latitude=None, longitude=None)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = job_post
        db.execute = AsyncMock(return_value=result)

        service = CheckinService(db)

        with pytest.raises(ValueError, match="JOB_POST_NO_GPS"):
            await service.check_in(str(job_post.id), str(uuid.uuid4()), 37.5, 127.0)

    @pytest.mark.asyncio
    async def test_instructor_not_found_raises(self) -> None:
        """Check-in with nonexistent instructor profile should raise INSTRUCTOR_NOT_FOUND."""
        job_post = _make_job_post()

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = job_post
            elif call_count == 2:
                result.scalar_one_or_none.return_value = None  # no instructor
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = CheckinService(db)

        with pytest.raises(ValueError, match="INSTRUCTOR_NOT_FOUND"):
            await service.check_in(str(job_post.id), str(uuid.uuid4()), 37.5, 127.0)


# ===========================================================================
# 5. Instructor Stats Update
# ===========================================================================

class TestCheckinUpdatesInstructorStats:
    """Tests for instructor stats update on check-in."""

    @pytest.mark.asyncio
    async def test_first_checkin_increments_total(self) -> None:
        """First check-in should set total_checkins to 1."""
        user_id = str(uuid.uuid4())
        instructor = _make_instructor_profile(
            user_id=user_id,
            total_checkins=0,
            avg_checkin_distance_m=None,
        )
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_CLOSE_LAT,
                longitude=INSTRUCTOR_CLOSE_LNG,
            )

        assert instructor.total_checkins == 1
        assert instructor.avg_checkin_distance_m is not None

    @pytest.mark.asyncio
    async def test_running_average_updates_correctly(self) -> None:
        """Running average should update based on previous count and distance."""
        user_id = str(uuid.uuid4())
        # Instructor has 4 previous check-ins with avg 100m
        instructor = _make_instructor_profile(
            user_id=user_id,
            total_checkins=4,
            avg_checkin_distance_m=Decimal("100.0"),
        )
        job_post = _make_job_post()
        application = _make_application(instructor_id=instructor.id)

        db = _setup_checkin_db(job_post, instructor, application)

        service = CheckinService(db)

        # Check in at roughly 130m
        with patch("app.services.checkin.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.check_in(
                job_post_id=str(job_post.id),
                user_id=user_id,
                latitude=INSTRUCTOR_CLOSE_LAT,
                longitude=INSTRUCTOR_CLOSE_LNG,
            )

        assert instructor.total_checkins == 5
        # New avg should be between old avg (100) and new distance (~130)
        new_avg = float(instructor.avg_checkin_distance_m)
        assert new_avg > 100.0
        assert new_avg < 200.0


# ===========================================================================
# 6. Check-in Status Retrieval
# ===========================================================================

class TestGetCheckinStatus:
    """Tests for CheckinService.get_checkin_status."""

    @pytest.mark.asyncio
    async def test_status_when_not_checked_in(self) -> None:
        """Should return checked_in=False when no check-in record exists."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = CheckinService(db)
        status = await service.get_checkin_status("job-123", "user-456")

        assert status["checked_in"] is False

    @pytest.mark.asyncio
    async def test_status_when_checked_in(self) -> None:
        """Should return full status dict when check-in record exists."""
        checkin_record = MagicMock()
        checkin_record.is_valid = True
        checkin_record.distance_meters = Decimal("120.5")
        checkin_record.checked_in_at = datetime(2026, 3, 24, 10, 0)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = checkin_record
        db.execute = AsyncMock(return_value=result)

        service = CheckinService(db)
        status = await service.get_checkin_status("job-123", "user-456")

        assert status["checked_in"] is True
        assert status["is_valid"] is True
        assert status["distance_meters"] == 120.5


# ===========================================================================
# 7. Constants validation
# ===========================================================================

class TestCheckinConstants:
    """Tests for check-in system constants."""

    def test_valid_distance_is_200m(self) -> None:
        """VALID_CHECKIN_DISTANCE_M should be 200 meters."""
        assert VALID_CHECKIN_DISTANCE_M == 200

    def test_checkin_record_model_has_expected_columns(self) -> None:
        """CheckinRecord model should have all required columns."""
        columns = CheckinRecord.__table__.columns
        assert "job_post_id" in columns
        assert "instructor_user_id" in columns
        assert "distance_meters" in columns
        assert "is_valid" in columns
        assert "checked_in_at" in columns
        assert "studio_latitude" in columns
        assert "studio_longitude" in columns
        assert "checkin_latitude" in columns
        assert "checkin_longitude" in columns
