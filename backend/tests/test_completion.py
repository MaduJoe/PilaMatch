"""Tests for PilaMatch Mutual Completion Confirmation Service.

Covers:
1. Studio confirms first -- studio_confirmed=True, is_complete=False
2. Both confirm -- studio + instructor -> is_complete=True
3. Instructor stats updated on mutual completion
4. Non-participant rejection (PermissionError)
5. Get completion status
6. Get instructor stats
7. Auto-complete stale records (24h timeout)
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.completion_confirmation import CompletionConfirmation
from app.services.completion import CompletionService, auto_complete_stale_records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job_post(
    job_post_id: Optional[str] = None,
    studio_id: Optional[str] = None,
) -> MagicMock:
    """Create a fake JobPost."""
    job = MagicMock()
    job.id = job_post_id or str(uuid.uuid4())
    job.studio_id = studio_id or str(uuid.uuid4())
    return job


def _make_application(
    app_id: Optional[str] = None,
    instructor_id: Optional[str] = None,
    job_post_id: Optional[str] = None,
) -> MagicMock:
    """Create a fake accepted Application."""
    app = MagicMock()
    app.id = app_id or str(uuid.uuid4())
    app.instructor_id = instructor_id or str(uuid.uuid4())
    app.job_post_id = job_post_id or str(uuid.uuid4())
    app.status = "accepted"
    return app


def _make_studio_profile(
    profile_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> MagicMock:
    """Create a fake StudioProfile."""
    studio = MagicMock()
    studio.id = profile_id or str(uuid.uuid4())
    studio.user_id = user_id or str(uuid.uuid4())
    return studio


def _make_instructor_profile(
    profile_id: Optional[str] = None,
    user_id: Optional[str] = None,
    total_completions: int = 0,
    completed_substitute_count: int = 0,
    total_dispatches: int = 0,
    total_dispatch_accepts: int = 0,
    dispatch_success_rate: Decimal = Decimal("0.000"),
) -> MagicMock:
    """Create a fake InstructorProfile."""
    profile = MagicMock()
    profile.id = profile_id or str(uuid.uuid4())
    profile.user_id = user_id or str(uuid.uuid4())
    profile.total_completions = total_completions
    profile.completed_substitute_count = completed_substitute_count
    profile.total_dispatches = total_dispatches
    profile.total_dispatch_accepts = total_dispatch_accepts
    profile.dispatch_success_rate = dispatch_success_rate
    return profile


def _setup_completion_db(
    job_post: MagicMock,
    application: MagicMock,
    studio: MagicMock,
    instructor: MagicMock,
    existing_confirmation: MagicMock = None,
) -> AsyncMock:
    """Build mock db session for the completion flow.

    DB execute call sequence in confirm_completion:
    1. select JobPost
    2. select Application (accepted)
    3. select StudioProfile
    4. select InstructorProfile
    5. select CompletionConfirmation (existing)
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
            result.scalar_one_or_none.return_value = application
        elif call_count == 3:
            result.scalar_one_or_none.return_value = studio
        elif call_count == 4:
            result.scalar_one_or_none.return_value = instructor
        elif call_count == 5:
            result.scalar_one_or_none.return_value = existing_confirmation
        else:
            result.scalar_one_or_none.return_value = None
        return result

    db.execute = AsyncMock(side_effect=mock_execute)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


# ===========================================================================
# 1. Studio Confirms First
# ===========================================================================

class TestStudioConfirmsFirst:
    """Tests for studio confirming first -- single-side confirmation."""

    @pytest.mark.asyncio
    async def test_studio_confirms_sets_studio_confirmed_true(self) -> None:
        """Studio confirming should set studio_confirmed=True."""
        studio_user_id = str(uuid.uuid4())
        instructor_user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=studio_user_id)
        instructor = _make_instructor_profile(user_id=instructor_user_id)
        job_post = _make_job_post(studio_id=studio.id)
        application = _make_application(instructor_id=instructor.id)

        db = _setup_completion_db(job_post, application, studio, instructor)

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.confirm_completion(str(job_post.id), studio_user_id)

        assert isinstance(record, CompletionConfirmation)
        assert record.studio_confirmed is True
        assert record.instructor_confirmed is False
        assert record.is_complete is not True

    @pytest.mark.asyncio
    async def test_instructor_confirms_first_creates_record(self) -> None:
        """Instructor confirming first should set instructor_confirmed=True."""
        studio_user_id = str(uuid.uuid4())
        instructor_user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=studio_user_id)
        instructor = _make_instructor_profile(user_id=instructor_user_id)
        job_post = _make_job_post(studio_id=studio.id)
        application = _make_application(instructor_id=instructor.id)

        db = _setup_completion_db(job_post, application, studio, instructor)

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            record = await service.confirm_completion(str(job_post.id), instructor_user_id)

        assert isinstance(record, CompletionConfirmation)
        assert record.instructor_confirmed is True
        assert record.studio_confirmed is False


# ===========================================================================
# 2. Both Confirm -- is_complete=True
# ===========================================================================

class TestBothConfirm:
    """Tests for mutual completion (both parties confirm)."""

    @pytest.mark.asyncio
    async def test_both_confirm_marks_complete(self) -> None:
        """When studio already confirmed and instructor confirms, is_complete=True."""
        studio_user_id = str(uuid.uuid4())
        instructor_user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=studio_user_id)
        instructor = _make_instructor_profile(user_id=instructor_user_id)
        job_post = _make_job_post(studio_id=studio.id)
        application = _make_application(instructor_id=instructor.id)

        # Existing confirmation: studio already confirmed
        existing = MagicMock(spec=CompletionConfirmation)
        existing.job_post_id = str(job_post.id)
        existing.application_id = str(application.id)
        existing.studio_user_id = studio_user_id
        existing.instructor_user_id = instructor_user_id
        existing.studio_confirmed = True
        existing.instructor_confirmed = False
        existing.is_complete = False
        existing.studio_confirmed_at = datetime(2026, 3, 24, 9, 0)
        existing.instructor_confirmed_at = None

        db = _setup_completion_db(job_post, application, studio, instructor, existing)

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls, \
             patch.object(service, "_on_completion", new_callable=AsyncMock) as mock_on:
            mock_event_cls.return_value = AsyncMock()
            record = await service.confirm_completion(str(job_post.id), instructor_user_id)

        assert record.instructor_confirmed is True
        assert record.is_complete is True
        mock_on.assert_awaited_once()


# ===========================================================================
# 3. Instructor Stats Updated on Completion
# ===========================================================================

class TestInstructorStatsOnCompletion:
    """Tests for _on_completion stats update."""

    @pytest.mark.asyncio
    async def test_total_completions_incremented(self) -> None:
        """_on_completion should increment total_completions."""
        instructor = _make_instructor_profile(total_completions=3, completed_substitute_count=2)

        db = AsyncMock()
        db.flush = AsyncMock()

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            # evaluate_and_update_tier is imported locally inside _on_completion
            with patch("app.services.tier_evaluation.evaluate_and_update_tier", new_callable=AsyncMock):
                await service._on_completion(instructor, str(uuid.uuid4()), str(uuid.uuid4()))

        assert instructor.total_completions == 4
        assert instructor.completed_substitute_count == 3

    @pytest.mark.asyncio
    async def test_dispatch_success_rate_recalculated(self) -> None:
        """_on_completion should recalculate dispatch_success_rate."""
        instructor = _make_instructor_profile(
            total_dispatches=10,
            total_dispatch_accepts=8,
            dispatch_success_rate=Decimal("0.800"),
        )

        db = AsyncMock()
        db.flush = AsyncMock()

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            with patch("app.services.tier_evaluation.evaluate_and_update_tier", new_callable=AsyncMock):
                await service._on_completion(instructor, str(uuid.uuid4()), str(uuid.uuid4()))

        # dispatch_success_rate = 8 / 10 = 0.800
        assert instructor.dispatch_success_rate == Decimal("0.8")

    @pytest.mark.asyncio
    async def test_tier_reevaluation_called(self) -> None:
        """_on_completion should trigger tier re-evaluation."""
        instructor = _make_instructor_profile()

        db = AsyncMock()
        db.flush = AsyncMock()

        service = CompletionService(db)

        with patch("app.services.completion.EventLogService") as mock_event_cls:
            mock_event_cls.return_value = AsyncMock()
            with patch("app.services.tier_evaluation.evaluate_and_update_tier", new_callable=AsyncMock) as mock_tier:
                await service._on_completion(instructor, str(uuid.uuid4()), str(uuid.uuid4()))

        mock_tier.assert_awaited_once()


# ===========================================================================
# 4. Non-Participant Rejection
# ===========================================================================

class TestNonParticipantRejected:
    """Tests for PermissionError when non-participant tries to confirm."""

    @pytest.mark.asyncio
    async def test_random_user_gets_permission_error(self) -> None:
        """A user who is neither studio nor instructor should get PermissionError."""
        studio_user_id = str(uuid.uuid4())
        instructor_user_id = str(uuid.uuid4())
        random_user_id = str(uuid.uuid4())

        studio = _make_studio_profile(user_id=studio_user_id)
        instructor = _make_instructor_profile(user_id=instructor_user_id)
        job_post = _make_job_post(studio_id=studio.id)
        application = _make_application(instructor_id=instructor.id)

        db = _setup_completion_db(job_post, application, studio, instructor)

        service = CompletionService(db)

        with pytest.raises(PermissionError, match="NOT_PARTICIPANT"):
            await service.confirm_completion(str(job_post.id), random_user_id)

    @pytest.mark.asyncio
    async def test_job_post_not_found_raises(self) -> None:
        """Confirming with nonexistent job post should raise JOB_POST_NOT_FOUND."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)

        with pytest.raises(ValueError, match="JOB_POST_NOT_FOUND"):
            await service.confirm_completion("fake-id", str(uuid.uuid4()))

    @pytest.mark.asyncio
    async def test_no_accepted_application_raises(self) -> None:
        """Confirming without an accepted application should raise NO_ACCEPTED_APPLICATION."""
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
                result.scalar_one_or_none.return_value = None  # no application
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = CompletionService(db)

        with pytest.raises(ValueError, match="NO_ACCEPTED_APPLICATION"):
            await service.confirm_completion(str(job_post.id), str(uuid.uuid4()))


# ===========================================================================
# 5. Get Completion Status
# ===========================================================================

class TestGetCompletionStatus:
    """Tests for CompletionService.get_completion_status."""

    @pytest.mark.asyncio
    async def test_status_no_record(self) -> None:
        """Should return exists=False, is_complete=False when no record."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)
        status = await service.get_completion_status("job-123")

        assert status["exists"] is False
        assert status["is_complete"] is False

    @pytest.mark.asyncio
    async def test_status_partial_confirmation(self) -> None:
        """Should return partial confirmation details."""
        record = MagicMock()
        record.studio_confirmed = True
        record.instructor_confirmed = False
        record.is_complete = False
        record.auto_completed = False
        record.studio_confirmed_at = datetime(2026, 3, 24, 10, 0)
        record.instructor_confirmed_at = None

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)
        status = await service.get_completion_status("job-123")

        assert status["exists"] is True
        assert status["studio_confirmed"] is True
        assert status["instructor_confirmed"] is False
        assert status["is_complete"] is False

    @pytest.mark.asyncio
    async def test_status_complete(self) -> None:
        """Should return is_complete=True when both confirmed."""
        record = MagicMock()
        record.studio_confirmed = True
        record.instructor_confirmed = True
        record.is_complete = True
        record.auto_completed = False
        record.studio_confirmed_at = datetime(2026, 3, 24, 10, 0)
        record.instructor_confirmed_at = datetime(2026, 3, 24, 10, 30)

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = record
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)
        status = await service.get_completion_status("job-123")

        assert status["exists"] is True
        assert status["is_complete"] is True


# ===========================================================================
# 6. Get Instructor Stats
# ===========================================================================

class TestGetInstructorStats:
    """Tests for CompletionService.get_instructor_stats."""

    @pytest.mark.asyncio
    async def test_returns_correct_stats(self) -> None:
        """Should return formatted stats dict from instructor profile."""
        instructor = MagicMock()
        instructor.dispatch_success_rate = Decimal("0.850")
        instructor.total_dispatches = 20
        instructor.total_dispatch_accepts = 17
        instructor.total_completions = 15
        instructor.total_checkins = 12
        instructor.avg_checkin_distance_m = Decimal("95.5")

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = instructor
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)
        stats = await service.get_instructor_stats("user-123")

        assert stats["dispatch_success_rate"] == 0.85
        assert stats["total_dispatches"] == 20
        assert stats["total_dispatch_accepts"] == 17
        assert stats["total_completions"] == 15
        assert stats["total_checkins"] == 12
        assert stats["avg_checkin_distance_m"] == 95.5

    @pytest.mark.asyncio
    async def test_instructor_not_found_raises(self) -> None:
        """Should raise INSTRUCTOR_NOT_FOUND for nonexistent instructor."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)

        with pytest.raises(ValueError, match="INSTRUCTOR_NOT_FOUND"):
            await service.get_instructor_stats("fake-user")

    @pytest.mark.asyncio
    async def test_handles_none_values_gracefully(self) -> None:
        """Should handle None/0 values without error."""
        instructor = MagicMock()
        instructor.dispatch_success_rate = None
        instructor.total_dispatches = None
        instructor.total_dispatch_accepts = None
        instructor.total_completions = None
        instructor.total_checkins = None
        instructor.avg_checkin_distance_m = None

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = instructor
        db.execute = AsyncMock(return_value=result)

        service = CompletionService(db)
        stats = await service.get_instructor_stats("user-123")

        assert stats["dispatch_success_rate"] == 0
        assert stats["total_dispatches"] == 0
        assert stats["avg_checkin_distance_m"] is None


# ===========================================================================
# 7. Auto-Complete Stale Records
# ===========================================================================

class TestAutoCompleteStaleRecords:
    """Tests for auto_complete_stale_records background task."""

    @pytest.mark.asyncio
    async def test_auto_completes_after_24h_studio_confirmed(self) -> None:
        """Record where studio confirmed 25h ago should be auto-completed."""
        stale_record = MagicMock()
        stale_record.is_complete = False
        stale_record.studio_confirmed = True
        stale_record.instructor_confirmed = False
        stale_record.studio_confirmed_at = datetime.utcnow() - timedelta(hours=25)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Studio confirmed, instructor not
                scalars = MagicMock()
                scalars.all.return_value = [stale_record]
                result.scalars.return_value = scalars
            elif call_count == 2:
                # Instructor confirmed, studio not
                scalars = MagicMock()
                scalars.all.return_value = []
                result.scalars.return_value = scalars
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        count = await auto_complete_stale_records(db)

        assert count == 1
        assert stale_record.instructor_confirmed is True
        assert stale_record.is_complete is True
        assert stale_record.auto_completed is True

    @pytest.mark.asyncio
    async def test_no_stale_records_returns_zero(self) -> None:
        """When no stale records exist, should return 0."""
        db = AsyncMock()

        async def mock_execute(stmt):
            result = MagicMock()
            scalars = MagicMock()
            scalars.all.return_value = []
            result.scalars.return_value = scalars
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        count = await auto_complete_stale_records(db)

        assert count == 0


# ===========================================================================
# 8. Model Validation
# ===========================================================================

class TestCompletionConfirmationModel:
    """Tests for CompletionConfirmation model structure."""

    def test_table_name(self) -> None:
        """Table name should be 'completion_confirmations'."""
        assert CompletionConfirmation.__tablename__ == "completion_confirmations"

    def test_job_post_id_is_unique(self) -> None:
        """job_post_id should have unique constraint (one confirmation per job)."""
        col = CompletionConfirmation.__table__.columns["job_post_id"]
        assert col.unique is True

    def test_has_studio_confirmed_column(self) -> None:
        """Model should have studio_confirmed boolean column."""
        assert "studio_confirmed" in CompletionConfirmation.__table__.columns

    def test_has_instructor_confirmed_column(self) -> None:
        """Model should have instructor_confirmed boolean column."""
        assert "instructor_confirmed" in CompletionConfirmation.__table__.columns

    def test_has_is_complete_column(self) -> None:
        """Model should have is_complete boolean column."""
        assert "is_complete" in CompletionConfirmation.__table__.columns

    def test_has_auto_completed_column(self) -> None:
        """Model should have auto_completed boolean column."""
        assert "auto_completed" in CompletionConfirmation.__table__.columns
