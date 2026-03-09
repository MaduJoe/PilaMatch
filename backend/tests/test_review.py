"""Unit tests for ReviewService (application-anchored reviews).

Tests cover:
- Time window enforcement (before class end, within window, after deadline)
- Duplicate review rejection
- IDOR protection (studio/instructor authorization)
- Checklist fields persistence (time_punctuality, professionalism, would_rehire)
- Rating update dispatch (_update_instructor_rating / _update_studio_rating)
- get_both_reviewed (True when 2 reviews exist)
- Application not found / not accepted guards
- Update and delete with authorization checks
"""

import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import UserRole
from app.schemas.review import ReviewCreate, ReviewUpdate
from app.services.review import ReviewService, KST_OFFSET


# ---------------------------------------------------------------------------
# Helpers: lightweight fakes
# ---------------------------------------------------------------------------

def _make_job_post(
    studio_id: uuid.UUID | None = None,
    class_date: dt.date | None = None,
    end_time: dt.time | None = None,
) -> MagicMock:
    jp = MagicMock()
    jp.id = uuid.uuid4()
    jp.studio_id = studio_id or uuid.uuid4()
    jp.date = class_date or dt.date(2026, 3, 8)
    jp.end_time = end_time or dt.time(18, 0)  # 18:00 KST
    return jp


def _make_application(
    instructor_id: uuid.UUID | None = None,
    job_post: MagicMock | None = None,
    contact_revealed: bool = True,
) -> MagicMock:
    app = MagicMock()
    app.id = uuid.uuid4()
    app.instructor_id = instructor_id or uuid.uuid4()
    app.job_post = job_post or _make_job_post()
    app.contact_revealed = contact_revealed
    return app


def _make_review_data(
    rating: int = 4,
    comment: str = "Great class!",
    time_punctuality: bool | None = True,
    professionalism: bool | None = True,
    would_rehire: bool | None = True,
) -> ReviewCreate:
    return ReviewCreate(
        rating=rating,
        comment=comment,
        time_punctuality=time_punctuality,
        professionalism=professionalism,
        would_rehire=would_rehire,
    )


def _utc_from_kst(kst_dt: dt.datetime) -> dt.datetime:
    """Convert a naive KST datetime to naive UTC."""
    return kst_dt - KST_OFFSET


# ---------------------------------------------------------------------------
# Mock DB builder for ReviewService.create_review
# ---------------------------------------------------------------------------

def _mock_db_for_create(
    application: MagicMock | None = None,
    studio_profile_id: uuid.UUID | None = None,
    instructor_profile_id: uuid.UUID | None = None,
    existing_review: MagicMock | None = None,
    avg_rating: float = 4.5,
    review_count: int = 1,
    profile_obj: MagicMock | None = None,
) -> AsyncMock:
    """Build mock AsyncSession for create_review call sequence.

    Call sequence inside create_review:
    1. select(Application).options(joinedload(...)).where(...) -> application  [.unique().scalar_one_or_none()]
    2. get_studio_profile_id OR get_instructor_profile_id -> profile id  [.scalar_one_or_none()]
    3. select(Review).where(dup check) -> existing_review  [.scalar_one_or_none()]
    4. (after db.add) _update_instructor_rating OR _update_studio_rating:
       4a. select(func.avg, func.count).where(...) -> (avg_rating, count)  [.one()]
       4b. select(InstructorProfile/StudioProfile).where(...) -> profile_obj  [.scalar_one_or_none()]
    5. db.commit()
    6. db.refresh(review)
    """
    db = AsyncMock()
    results = []

    # 1. Application lookup (uses .unique().scalar_one_or_none())
    app_unique = MagicMock()
    app_unique.scalar_one_or_none.return_value = application
    app_result = MagicMock()
    app_result.unique.return_value = app_unique
    results.append(app_result)

    if application and application.contact_revealed and application.job_post:
        # 2. Profile ID lookup (studio or instructor)
        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = (
            studio_profile_id or instructor_profile_id
        )
        results.append(profile_id_result)

        # 3. Duplicate check
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = existing_review
        results.append(dup_result)

        if not existing_review:
            # 4a. avg/count query
            rating_result = MagicMock()
            rating_result.one.return_value = (avg_rating, review_count)
            results.append(rating_result)

            # 4b. profile object for rating update
            profile_result = MagicMock()
            _profile = profile_obj or MagicMock()
            _profile.rating_average = Decimal("0")
            _profile.review_count = 0
            profile_result.scalar_one_or_none.return_value = _profile
            results.append(profile_result)

    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ===========================================================================
# Time Window Tests (_review_window and check_review_window)
# ===========================================================================

class TestReviewWindow:
    """Tests for _review_window static method and check_review_window."""

    def test_review_window_returns_correct_utc_boundaries(self):
        """Window opens at class end_time (KST->UTC) and closes at 23:59:59 KST->UTC."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(18, 0),
        )
        open_utc, close_utc = ReviewService._review_window(jp)

        # 18:00 KST = 09:00 UTC
        expected_open = dt.datetime(2026, 3, 8, 9, 0, 0)
        # 23:59:59 KST = 14:59:59 UTC
        expected_close = dt.datetime(2026, 3, 8, 14, 59, 59)

        assert open_utc == expected_open
        assert close_utc == expected_close

    def test_review_window_early_morning_class(self):
        """Class ending at 06:00 KST still has same-day deadline."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(6, 0),
        )
        open_utc, close_utc = ReviewService._review_window(jp)

        # 06:00 KST = 2026-03-07 21:00 UTC (previous day in UTC)
        expected_open = dt.datetime(2026, 3, 7, 21, 0, 0)
        expected_close = dt.datetime(2026, 3, 8, 14, 59, 59)

        assert open_utc == expected_open
        assert close_utc == expected_close

    @patch("app.services.review.dt")
    def test_check_review_window_before_class_ends(self, mock_dt):
        """Before class end: is_eligible=False, is_expired=False."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(18, 0),
        )
        # Simulate 17:00 KST = 08:00 UTC (before 09:00 UTC open)
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 8, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        service = ReviewService(db=AsyncMock())
        is_eligible, is_expired = service.check_review_window(jp)

        assert is_eligible is False
        assert is_expired is False

    @patch("app.services.review.dt")
    def test_check_review_window_within_window(self, mock_dt):
        """During window: is_eligible=True, is_expired=False."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(18, 0),
        )
        # Simulate 20:00 KST = 11:00 UTC (between 09:00 and 14:59:59)
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        service = ReviewService(db=AsyncMock())
        is_eligible, is_expired = service.check_review_window(jp)

        assert is_eligible is True
        assert is_expired is False

    @patch("app.services.review.dt")
    def test_check_review_window_exactly_at_class_end(self, mock_dt):
        """Exactly at class end time: is_eligible=True, is_expired=False."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(18, 0),
        )
        # Exactly at 18:00 KST = 09:00 UTC
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 9, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        service = ReviewService(db=AsyncMock())
        is_eligible, is_expired = service.check_review_window(jp)

        assert is_eligible is True
        assert is_expired is False

    @patch("app.services.review.dt")
    def test_check_review_window_after_deadline(self, mock_dt):
        """After 23:59:59 KST: is_eligible=True, is_expired=True."""
        jp = _make_job_post(
            class_date=dt.date(2026, 3, 8),
            end_time=dt.time(18, 0),
        )
        # Simulate next day 00:00:01 KST = 15:00:01 UTC on 3/8
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 15, 0, 1)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        service = ReviewService(db=AsyncMock())
        is_eligible, is_expired = service.check_review_window(jp)

        assert is_eligible is True
        assert is_expired is True


# ===========================================================================
# create_review: Happy Path
# ===========================================================================

class TestCreateReviewHappyPath:
    """Tests for ReviewService.create_review happy path."""

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_studio_reviews_instructor_successfully(self, mock_dt):
        """Studio can review instructor within time window."""
        studio_id = uuid.uuid4()
        studio_user_id = uuid.uuid4()
        instructor_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(instructor_id=instructor_id, job_post=jp)

        # Set time inside review window (20:00 KST = 11:00 UTC)
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
        )

        service = ReviewService(db)
        data = _make_review_data(rating=5, comment="Excellent instructor")

        review = await service.create_review(
            application_id=application.id,
            reviewer_user_id=studio_user_id,
            reviewer_role=UserRole.STUDIO,
            data=data,
        )

        # Verify db.add was called with a Review-like object
        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert added_obj.application_id == application.id
        assert added_obj.contract_id is None
        assert added_obj.reviewer_user_id == studio_user_id
        assert added_obj.reviewee_instructor_id == instructor_id
        assert added_obj.reviewee_studio_id is None
        assert added_obj.rating == 5
        assert added_obj.comment == "Excellent instructor"

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_instructor_reviews_studio_successfully(self, mock_dt):
        """Instructor can review studio within time window."""
        studio_id = uuid.uuid4()
        instructor_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(instructor_id=instructor_id, job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            instructor_profile_id=instructor_id,
        )

        service = ReviewService(db)
        data = _make_review_data(rating=3, comment="Okay studio")

        review = await service.create_review(
            application_id=application.id,
            reviewer_user_id=instructor_user_id,
            reviewer_role=UserRole.INSTRUCTOR,
            data=data,
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.reviewee_instructor_id is None
        assert added_obj.reviewee_studio_id == studio_id
        assert added_obj.rating == 3

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_checklist_fields_persisted(self, mock_dt):
        """Checklist fields (time_punctuality, professionalism, would_rehire) are saved."""
        studio_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
        )

        data = _make_review_data(
            time_punctuality=True,
            professionalism=False,
            would_rehire=True,
        )

        service = ReviewService(db)
        await service.create_review(
            application_id=application.id,
            reviewer_user_id=uuid.uuid4(),
            reviewer_role=UserRole.STUDIO,
            data=data,
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.time_punctuality is True
        assert added_obj.professionalism is False
        assert added_obj.would_rehire is True

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_checklist_fields_none_when_omitted(self, mock_dt):
        """Checklist fields default to None when not provided."""
        studio_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
        )

        data = ReviewCreate(rating=4)

        service = ReviewService(db)
        await service.create_review(
            application_id=application.id,
            reviewer_user_id=uuid.uuid4(),
            reviewer_role=UserRole.STUDIO,
            data=data,
        )

        added_obj = db.add.call_args[0][0]
        assert added_obj.time_punctuality is None
        assert added_obj.professionalism is None
        assert added_obj.would_rehire is None


# ===========================================================================
# create_review: Time Window Enforcement
# ===========================================================================

class TestCreateReviewTimeWindow:
    """Tests for time window enforcement in create_review."""

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_cannot_review_before_class_ends(self, mock_dt):
        """Attempting to review before class end raises ValueError."""
        studio_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        # 17:00 KST = 08:00 UTC (before 09:00 open)
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 8, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="수업이 아직 종료되지 않았습니다"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_cannot_review_after_deadline(self, mock_dt):
        """Attempting to review after 23:59:59 KST raises ValueError."""
        studio_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        # Next day 01:00 KST = 16:00 UTC on 3/8 (after 14:59:59 close)
        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 16, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="리뷰 작성 가능 기간이 지났습니다"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )


# ===========================================================================
# create_review: Guard Conditions
# ===========================================================================

class TestCreateReviewGuards:
    """Tests for guard conditions: not found, not accepted, duplicate."""

    @pytest.mark.asyncio
    async def test_application_not_found(self):
        """Raises ValueError when application does not exist."""
        db = _mock_db_for_create(application=None)

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="Application not found"):
            await service.create_review(
                application_id=uuid.uuid4(),
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    async def test_application_not_accepted(self):
        """Raises ValueError when contact_revealed is False."""
        application = _make_application(contact_revealed=False)
        db = _mock_db_for_create(application=application)

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="Cannot review: application not accepted"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_duplicate_review_rejected(self, mock_dt):
        """Raises ValueError when same user tries to review same application twice."""
        studio_id = uuid.uuid4()
        studio_user_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        existing_review = MagicMock()  # Simulate existing review
        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
            existing_review=existing_review,
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="이미 리뷰를 작성했습니다"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=studio_user_id,
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_job_post_none_raises_error(self, mock_dt):
        """Raises ValueError when application.job_post is None."""
        application = _make_application()
        application.job_post = None

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(application=application)

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(ValueError, match="Job post not found"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )


# ===========================================================================
# create_review: IDOR Protection
# ===========================================================================

class TestCreateReviewIDOR:
    """Tests for IDOR protection in create_review."""

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_studio_cannot_review_other_studios_application(self, mock_dt):
        """Studio A cannot review application from Studio B's job post."""
        studio_a_id = uuid.uuid4()
        studio_b_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_b_id, end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        # Studio A's profile ID is different from jp.studio_id (Studio B)
        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_a_id,
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(PermissionError, match="Not authorized to review"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_instructor_cannot_review_other_instructors_application(self, mock_dt):
        """Instructor A cannot review application belonging to Instructor B."""
        instructor_a_id = uuid.uuid4()
        instructor_b_id = uuid.uuid4()
        jp = _make_job_post(end_time=dt.time(18, 0))
        application = _make_application(instructor_id=instructor_b_id, job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        # Instructor A's profile ID differs from application.instructor_id
        db = _mock_db_for_create(
            application=application,
            instructor_profile_id=instructor_a_id,
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(PermissionError, match="Not authorized to review"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.INSTRUCTOR,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_studio_no_profile_raises_permission_error(self, mock_dt):
        """Studio user with no profile gets PermissionError."""
        jp = _make_job_post(end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=None,  # No profile found
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(PermissionError, match="Not authorized to review"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.STUDIO,
                data=data,
            )

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_instructor_no_profile_raises_permission_error(self, mock_dt):
        """Instructor user with no profile gets PermissionError."""
        jp = _make_job_post(end_time=dt.time(18, 0))
        application = _make_application(job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        db = _mock_db_for_create(
            application=application,
            instructor_profile_id=None,  # No profile found
        )

        service = ReviewService(db)
        data = _make_review_data()

        with pytest.raises(PermissionError, match="Not authorized to review"):
            await service.create_review(
                application_id=application.id,
                reviewer_user_id=uuid.uuid4(),
                reviewer_role=UserRole.INSTRUCTOR,
                data=data,
            )


# ===========================================================================
# create_review: Rating Update Dispatch
# ===========================================================================

class TestCreateReviewRatingUpdate:
    """Tests for _update_instructor_rating and _update_studio_rating calls."""

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_studio_review_updates_instructor_rating(self, mock_dt):
        """When studio reviews, _update_instructor_rating is called (avg/count update)."""
        studio_id = uuid.uuid4()
        instructor_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(instructor_id=instructor_id, job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        instructor_profile = MagicMock()
        instructor_profile.rating_average = Decimal("0")
        instructor_profile.review_count = 0

        db = _mock_db_for_create(
            application=application,
            studio_profile_id=studio_id,
            avg_rating=4.5,
            review_count=3,
            profile_obj=instructor_profile,
        )

        service = ReviewService(db)
        data = _make_review_data(rating=5)

        await service.create_review(
            application_id=application.id,
            reviewer_user_id=uuid.uuid4(),
            reviewer_role=UserRole.STUDIO,
            data=data,
        )

        # Verify rating was updated on the instructor profile
        assert instructor_profile.rating_average == Decimal("4.5")
        assert instructor_profile.review_count == 3
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    @patch("app.services.review.dt")
    async def test_instructor_review_updates_studio_rating(self, mock_dt):
        """When instructor reviews, _update_studio_rating is called."""
        studio_id = uuid.uuid4()
        instructor_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()
        jp = _make_job_post(studio_id=studio_id, end_time=dt.time(18, 0))
        application = _make_application(instructor_id=instructor_id, job_post=jp)

        mock_dt.datetime.utcnow.return_value = dt.datetime(2026, 3, 8, 11, 0, 0)
        mock_dt.datetime.combine = dt.datetime.combine
        mock_dt.timedelta = dt.timedelta
        mock_dt.time = dt.time

        studio_profile = MagicMock()
        studio_profile.rating_average = Decimal("0")
        studio_profile.review_count = 0

        db = _mock_db_for_create(
            application=application,
            instructor_profile_id=instructor_id,
            avg_rating=3.8,
            review_count=5,
            profile_obj=studio_profile,
        )

        service = ReviewService(db)
        data = _make_review_data(rating=4)

        await service.create_review(
            application_id=application.id,
            reviewer_user_id=instructor_user_id,
            reviewer_role=UserRole.INSTRUCTOR,
            data=data,
        )

        assert studio_profile.rating_average == Decimal("3.8")
        assert studio_profile.review_count == 5


# ===========================================================================
# get_both_reviewed
# ===========================================================================

class TestGetBothReviewed:
    """Tests for get_both_reviewed method."""

    @pytest.mark.asyncio
    async def test_both_reviewed_true_when_two_reviews(self):
        """Returns True when 2 reviews exist for the application."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 2
        db.execute = AsyncMock(return_value=count_result)

        service = ReviewService(db)
        result = await service.get_both_reviewed(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_both_reviewed_false_when_one_review(self):
        """Returns False when only 1 review exists."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        db.execute = AsyncMock(return_value=count_result)

        service = ReviewService(db)
        result = await service.get_both_reviewed(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_both_reviewed_false_when_no_reviews(self):
        """Returns False when no reviews exist."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 0
        db.execute = AsyncMock(return_value=count_result)

        service = ReviewService(db)
        result = await service.get_both_reviewed(uuid.uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_both_reviewed_true_when_more_than_two(self):
        """Returns True when more than 2 reviews exist (edge case)."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = 3
        db.execute = AsyncMock(return_value=count_result)

        service = ReviewService(db)
        result = await service.get_both_reviewed(uuid.uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_both_reviewed_handles_null_count(self):
        """Returns False when scalar returns None."""
        db = AsyncMock()
        count_result = MagicMock()
        count_result.scalar.return_value = None
        db.execute = AsyncMock(return_value=count_result)

        service = ReviewService(db)
        result = await service.get_both_reviewed(uuid.uuid4())

        assert result is False


# ===========================================================================
# get_user_review_for_application
# ===========================================================================

class TestGetUserReviewForApplication:
    """Tests for get_user_review_for_application method."""

    @pytest.mark.asyncio
    async def test_returns_review_when_exists(self):
        """Returns review object when user has written a review."""
        mock_review = MagicMock()
        mock_review.id = uuid.uuid4()

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_review
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        review = await service.get_user_review_for_application(
            uuid.uuid4(), uuid.uuid4()
        )

        assert review is mock_review

    @pytest.mark.asyncio
    async def test_returns_none_when_no_review(self):
        """Returns None when user has not written a review."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        review = await service.get_user_review_for_application(
            uuid.uuid4(), uuid.uuid4()
        )

        assert review is None


# ===========================================================================
# update_review
# ===========================================================================

class TestUpdateReview:
    """Tests for ReviewService.update_review."""

    @pytest.mark.asyncio
    async def test_update_review_success(self):
        """Owner can update their review fields."""
        user_id = uuid.uuid4()
        review = MagicMock()
        review.id = uuid.uuid4()
        review.reviewer_user_id = user_id
        review.reviewee_instructor_id = uuid.uuid4()
        review.reviewee_studio_id = None
        review.rating = 3
        review.comment = "Old comment"

        db = AsyncMock()
        results = []

        # 1. Review lookup
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = review
        results.append(review_result)

        # 2. _update_instructor_rating: avg/count
        rating_result = MagicMock()
        rating_result.one.return_value = (4.0, 2)
        results.append(rating_result)

        # 3. _update_instructor_rating: profile
        profile = MagicMock()
        profile.rating_average = Decimal("0")
        profile.review_count = 0
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile
        results.append(profile_result)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        service = ReviewService(db)
        data = ReviewUpdate(rating=5, comment="Updated comment")

        result = await service.update_review(review.id, user_id, data)

        assert review.rating == 5
        assert review.comment == "Updated comment"

    @pytest.mark.asyncio
    async def test_update_review_not_found(self):
        """Raises ValueError when review does not exist."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        data = ReviewUpdate(rating=5)

        with pytest.raises(ValueError, match="Review not found"):
            await service.update_review(uuid.uuid4(), uuid.uuid4(), data)

    @pytest.mark.asyncio
    async def test_update_review_not_owner(self):
        """Raises PermissionError when user is not the reviewer."""
        review = MagicMock()
        review.reviewer_user_id = uuid.uuid4()

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = review
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        other_user = uuid.uuid4()
        data = ReviewUpdate(rating=5)

        with pytest.raises(PermissionError, match="Not authorized to update"):
            await service.update_review(review.id, other_user, data)


# ===========================================================================
# delete_review
# ===========================================================================

class TestDeleteReview:
    """Tests for ReviewService.delete_review."""

    @pytest.mark.asyncio
    async def test_delete_review_success(self):
        """Owner can delete their review."""
        user_id = uuid.uuid4()
        instructor_id = uuid.uuid4()
        review = MagicMock()
        review.id = uuid.uuid4()
        review.reviewer_user_id = user_id
        review.reviewee_instructor_id = instructor_id
        review.reviewee_studio_id = None

        db = AsyncMock()
        results = []

        # 1. Review lookup
        review_result = MagicMock()
        review_result.scalar_one_or_none.return_value = review
        results.append(review_result)

        # 2. _update_instructor_rating after delete: avg/count
        rating_result = MagicMock()
        rating_result.one.return_value = (None, 0)
        results.append(rating_result)

        # 3. _update_instructor_rating: profile lookup
        profile = MagicMock()
        profile.rating_average = Decimal("4.5")
        profile.review_count = 1
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile
        results.append(profile_result)

        db.execute = AsyncMock(side_effect=results)
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        service = ReviewService(db)
        await service.delete_review(review.id, user_id)

        db.delete.assert_awaited_once_with(review)
        # After deletion with no remaining reviews, rating should be 0
        assert profile.rating_average == Decimal("0")
        assert profile.review_count == 0

    @pytest.mark.asyncio
    async def test_delete_review_not_found(self):
        """Raises ValueError when review does not exist."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)

        with pytest.raises(ValueError, match="Review not found"):
            await service.delete_review(uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_delete_review_not_owner(self):
        """Raises PermissionError when user is not the reviewer."""
        review = MagicMock()
        review.reviewer_user_id = uuid.uuid4()

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = review
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        other_user = uuid.uuid4()

        with pytest.raises(PermissionError, match="Not authorized to delete"):
            await service.delete_review(review.id, other_user)


# ===========================================================================
# Profile Lookup Helpers
# ===========================================================================

class TestProfileLookups:
    """Tests for get_studio_profile_id and get_instructor_profile_id."""

    @pytest.mark.asyncio
    async def test_get_studio_profile_id_found(self):
        """Returns profile ID when studio profile exists."""
        expected_id = uuid.uuid4()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = expected_id
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        profile_id = await service.get_studio_profile_id(uuid.uuid4())

        assert profile_id == expected_id

    @pytest.mark.asyncio
    async def test_get_studio_profile_id_not_found(self):
        """Returns None when studio profile does not exist."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        profile_id = await service.get_studio_profile_id(uuid.uuid4())

        assert profile_id is None

    @pytest.mark.asyncio
    async def test_get_instructor_profile_id_found(self):
        """Returns profile ID when instructor profile exists."""
        expected_id = uuid.uuid4()
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = expected_id
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        profile_id = await service.get_instructor_profile_id(uuid.uuid4())

        assert profile_id == expected_id

    @pytest.mark.asyncio
    async def test_get_instructor_profile_id_not_found(self):
        """Returns None when instructor profile does not exist."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = ReviewService(db)
        profile_id = await service.get_instructor_profile_id(uuid.uuid4())

        assert profile_id is None
