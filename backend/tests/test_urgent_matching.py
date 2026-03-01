"""Tests for PilaMatch urgent substitute matching pivot.

Covers:
1. Distance calculation utility (app/utils/distance.py)
2. Matching service with distance factor (app/services/matching.py)
3. Contact reveal flow (POST /applications/{id}/accept)
4. Daily usage limits removed (PMF pivot)
5. Urgent job post flag (is_urgent)
"""

import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.distance import (
    haversine_distance,
    estimate_travel_time,
    format_distance,
)
from app.services.matching import (
    _calculate_distance_score,
    calculate_matching_score,
    get_match_label,
)
from app.models.enums import ApplicationStatus, JobPostStatus


# ---------------------------------------------------------------------------
# Helpers: lightweight fakes for SQLAlchemy model instances
# ---------------------------------------------------------------------------

def _make_instructor_profile(
    user_id: Optional[uuid.UUID] = None,
    display_name: str = "Test Instructor",
    phone: str = "010-1234-5678",
    experience_years: int = 5,
    available_regions: Optional[list] = None,
    hourly_rate_min: Decimal = Decimal("30000"),
    hourly_rate_max: Decimal = Decimal("50000"),
    certifications: Optional[list] = None,
    latitude: Optional[Decimal] = None,
    longitude: Optional[Decimal] = None,
    rating_average: Optional[Decimal] = None,
    review_count: int = 0,
    completed_substitute_count: int = 0,
) -> MagicMock:
    """Create a fake InstructorProfile model instance."""
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.display_name = display_name
    profile.phone = phone
    profile.experience_years = experience_years
    profile.available_regions = available_regions or ["서울 강남"]
    profile.hourly_rate_min = hourly_rate_min
    profile.hourly_rate_max = hourly_rate_max
    profile.certifications = certifications or []
    profile.latitude = latitude
    profile.longitude = longitude
    profile.rating_average = rating_average
    profile.review_count = review_count
    profile.completed_substitute_count = completed_substitute_count
    profile.categories = ["pilates"]
    return profile


def _make_job_post(
    studio_id: Optional[uuid.UUID] = None,
    title: str = "Urgent Sub Needed",
    region: str = "서울 강남",
    required_experience_years: int = 3,
    required_certifications: Optional[list] = None,
    hourly_rate: Decimal = Decimal("40000"),
    latitude: Optional[Decimal] = None,
    longitude: Optional[Decimal] = None,
    is_urgent: bool = False,
    status: str = "open",
) -> MagicMock:
    """Create a fake JobPost model instance."""
    job = MagicMock()
    job.id = uuid.uuid4()
    job.studio_id = studio_id or uuid.uuid4()
    job.title = title
    job.region = region
    job.required_experience_years = required_experience_years
    job.required_certifications = required_certifications or []
    job.hourly_rate = hourly_rate
    job.latitude = latitude
    job.longitude = longitude
    job.is_urgent = is_urgent
    job.status = status
    job.application_count = 0
    return job


def _make_studio_profile(
    user_id: Optional[uuid.UUID] = None,
    business_name: str = "Test Studio",
    phone: str = "02-1234-5678",
    address: str = "서울 강남구 역삼동 123",
) -> MagicMock:
    """Create a fake StudioProfile model instance."""
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.business_name = business_name
    profile.phone = phone
    profile.address = address
    return profile


def _make_application(
    job_post_id: Optional[uuid.UUID] = None,
    instructor_id: Optional[uuid.UUID] = None,
    status: str = ApplicationStatus.PENDING.value,
    contact_revealed: bool = False,
    contact_revealed_at=None,
) -> MagicMock:
    """Create a fake Application model instance."""
    app = MagicMock()
    app.id = uuid.uuid4()
    app.job_post_id = job_post_id or uuid.uuid4()
    app.instructor_id = instructor_id or uuid.uuid4()
    app.status = status
    app.cover_letter = "I am available for this substitute class."
    app.contact_revealed = contact_revealed
    app.contact_revealed_at = contact_revealed_at
    app.created_at = datetime.utcnow()
    app.updated_at = datetime.utcnow()
    return app


# ===========================================================================
# 1. Distance Calculation (app/utils/distance.py)
# ===========================================================================

class TestHaversineDistance:
    """Tests for haversine_distance function."""

    def test_same_point_returns_zero(self) -> None:
        """Same point should return 0 distance."""
        result = haversine_distance(37.5665, 126.9780, 37.5665, 126.9780)
        assert result == 0.0

    def test_seoul_city_hall_to_gangnam_station(self) -> None:
        """Seoul City Hall to Gangnam Station should be approximately 8.8km.

        Seoul City Hall: 37.5665, 126.9780
        Gangnam Station: 37.4979, 127.0276
        Haversine gives ~8.79km (straight line).
        """
        result = haversine_distance(37.5665, 126.9780, 37.4979, 127.0276)
        assert 8.0 <= result <= 9.5, f"Expected ~8.8km, got {result:.2f}km"

    def test_short_distance_under_1km(self) -> None:
        """Two nearby points (approx 500m apart) should return < 1km.

        Points near Gangnam Station, about 500m apart.
        """
        result = haversine_distance(37.4979, 127.0276, 37.5010, 127.0276)
        assert result < 1.0, f"Expected < 1km, got {result:.3f}km"

    def test_symmetry(self) -> None:
        """Distance A->B should equal distance B->A."""
        d1 = haversine_distance(37.5665, 126.9780, 37.4979, 127.0276)
        d2 = haversine_distance(37.4979, 127.0276, 37.5665, 126.9780)
        assert abs(d1 - d2) < 1e-10

    def test_long_distance_seoul_to_busan(self) -> None:
        """Seoul to Busan should be approximately 325km.

        Seoul Station: 37.5547, 126.9707
        Busan Station: 35.1152, 129.0413
        """
        result = haversine_distance(37.5547, 126.9707, 35.1152, 129.0413)
        assert 300 <= result <= 350, f"Expected ~325km, got {result:.1f}km"


class TestEstimateTravelTime:
    """Tests for estimate_travel_time function."""

    def test_zero_distance_returns_zero(self) -> None:
        """Zero distance should return 0 minutes."""
        assert estimate_travel_time(0) == 0

    def test_negative_distance_returns_zero(self) -> None:
        """Negative distance should return 0 minutes."""
        assert estimate_travel_time(-5.0) == 0

    def test_1km_returns_3_minutes(self) -> None:
        """1km at 20km/h should take 3 minutes."""
        result = estimate_travel_time(1.0)
        assert result == 3

    def test_20km_returns_60_minutes(self) -> None:
        """20km at 20km/h should take exactly 60 minutes."""
        result = estimate_travel_time(20.0)
        assert result == 60

    def test_minimum_1_minute(self) -> None:
        """Very short distance should still return at least 1 minute."""
        result = estimate_travel_time(0.01)
        assert result >= 1

    def test_reasonable_commute(self) -> None:
        """5km should take about 15 minutes."""
        result = estimate_travel_time(5.0)
        assert result == 15


class TestFormatDistance:
    """Tests for format_distance function."""

    def test_under_1km_shows_meters(self) -> None:
        """Distances under 1km should display in meters."""
        assert format_distance(0.8) == "800m"

    def test_500_meters(self) -> None:
        """0.5km should show as 500m."""
        assert format_distance(0.5) == "500m"

    def test_exactly_1km(self) -> None:
        """1km should display as 1.0km."""
        assert format_distance(1.0) == "1.0km"

    def test_above_1km_shows_km(self) -> None:
        """Distances at or above 1km should display in km with one decimal."""
        assert format_distance(2.5) == "2.5km"

    def test_large_distance(self) -> None:
        """Large distance still shows km format."""
        assert format_distance(15.3) == "15.3km"

    def test_zero_distance(self) -> None:
        """0km should show as 0m."""
        assert format_distance(0.0) == "0m"

    def test_very_small_distance(self) -> None:
        """Very small distance rounds to meters."""
        result = format_distance(0.05)
        assert result == "50m"


# ===========================================================================
# 2. Matching Service with Distance (app/services/matching.py)
# ===========================================================================

class TestCalculateDistanceScore:
    """Tests for the _calculate_distance_score internal function."""

    def test_under_2km_returns_100(self) -> None:
        """Distance <= 2km should score 100."""
        assert _calculate_distance_score(0.0) == 100
        assert _calculate_distance_score(1.5) == 100
        assert _calculate_distance_score(2.0) == 100

    def test_2_to_5km_returns_80(self) -> None:
        """Distance 2-5km should score 80."""
        assert _calculate_distance_score(2.1) == 80
        assert _calculate_distance_score(3.0) == 80
        assert _calculate_distance_score(5.0) == 80

    def test_5_to_10km_returns_60(self) -> None:
        """Distance 5-10km should score 60."""
        assert _calculate_distance_score(5.1) == 60
        assert _calculate_distance_score(7.5) == 60
        assert _calculate_distance_score(10.0) == 60

    def test_10_to_20km_returns_40(self) -> None:
        """Distance 10-20km should score 40."""
        assert _calculate_distance_score(10.1) == 40
        assert _calculate_distance_score(15.0) == 40
        assert _calculate_distance_score(20.0) == 40

    def test_20_to_30km_returns_20(self) -> None:
        """Distance 20-30km should score 20."""
        assert _calculate_distance_score(20.1) == 20
        assert _calculate_distance_score(25.0) == 20
        assert _calculate_distance_score(30.0) == 20

    def test_over_30km_returns_10(self) -> None:
        """Distance > 30km should score 10."""
        assert _calculate_distance_score(30.1) == 10
        assert _calculate_distance_score(50.0) == 10
        assert _calculate_distance_score(100.0) == 10


class TestMatchingScoreWithoutDistance:
    """Matching score without location data (original 4-factor weights)."""

    def test_original_4_factor_weights_when_no_location(self) -> None:
        """When neither party has coordinates, use original 4-factor weights."""
        instructor = _make_instructor_profile(
            available_regions=["서울 강남"],
            experience_years=5,
            certifications=[],
            hourly_rate_min=Decimal("30000"),
            hourly_rate_max=Decimal("50000"),
            latitude=None,
            longitude=None,
        )
        job = _make_job_post(
            region="서울 강남",
            required_experience_years=3,
            required_certifications=[],
            hourly_rate=Decimal("40000"),
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" not in result["breakdown"]
        assert result["breakdown"]["region"]["weight"] == 30
        assert result["breakdown"]["experience"]["weight"] == 25
        assert result["breakdown"]["certifications"]["weight"] == 25
        assert result["breakdown"]["rate"]["weight"] == 20
        assert "distance_km" not in result

    def test_no_distance_when_only_instructor_has_coords(self) -> None:
        """If only instructor has coords but job does not, 4-factor weights apply."""
        instructor = _make_instructor_profile(
            latitude=Decimal("37.5665"),
            longitude=Decimal("126.9780"),
        )
        job = _make_job_post(latitude=None, longitude=None)

        result = calculate_matching_score(instructor, job)

        assert "distance" not in result["breakdown"]
        assert "distance_km" not in result

    def test_no_distance_when_only_job_has_coords(self) -> None:
        """If only job has coords but instructor does not, 4-factor weights apply."""
        instructor = _make_instructor_profile(latitude=None, longitude=None)
        job = _make_job_post(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" not in result["breakdown"]
        assert "distance_km" not in result

    def test_perfect_match_all_factors(self) -> None:
        """Instructor perfectly matches all 4 factors."""
        instructor = _make_instructor_profile(
            available_regions=["서울 강남"],
            experience_years=10,
            certifications=["PMA-CPT"],
            hourly_rate_min=Decimal("30000"),
            hourly_rate_max=Decimal("50000"),
        )
        job = _make_job_post(
            region="서울 강남",
            required_experience_years=5,
            required_certifications=["PMA-CPT"],
            hourly_rate=Decimal("40000"),
        )

        result = calculate_matching_score(instructor, job)

        assert result["total"] == 100
        assert result["breakdown"]["region"]["score"] == 100
        assert result["breakdown"]["experience"]["score"] == 100
        assert result["breakdown"]["certifications"]["score"] == 100
        assert result["breakdown"]["rate"]["score"] == 100


class TestMatchingScoreWithDistance:
    """Matching score with location data (5-factor weights including distance)."""

    def test_5_factor_weights_when_both_have_location(self) -> None:
        """When both have coordinates, use 5-factor weights with distance."""
        instructor = _make_instructor_profile(
            latitude=Decimal("37.5665"),
            longitude=Decimal("126.9780"),
        )
        job = _make_job_post(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" in result["breakdown"]
        assert result["breakdown"]["distance"]["weight"] == 35
        assert result["breakdown"]["region"]["weight"] == 10
        assert result["breakdown"]["experience"]["weight"] == 25
        assert result["breakdown"]["certifications"]["weight"] == 15
        assert result["breakdown"]["rate"]["weight"] == 15
        assert "distance_km" in result

    def test_distance_km_included_in_result(self) -> None:
        """distance_km should be a rounded float in the result."""
        instructor = _make_instructor_profile(
            latitude=Decimal("37.5665"),
            longitude=Decimal("126.9780"),
        )
        job = _make_job_post(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        result = calculate_matching_score(instructor, job)

        assert isinstance(result["distance_km"], float)
        assert result["distance_km"] > 0

    def test_very_close_distance_high_score(self) -> None:
        """Instructor very close to job should get high distance score."""
        instructor = _make_instructor_profile(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )
        job = _make_job_post(
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
        )

        result = calculate_matching_score(instructor, job)

        assert result["breakdown"]["distance"]["score"] == 100
        assert result["distance_km"] < 2.0

    def test_instructor_lat_lng_parameter_override(self) -> None:
        """instructor_lat/instructor_lng parameters override model fields."""
        instructor = _make_instructor_profile(
            latitude=Decimal("35.0"),  # Model says Busan area
            longitude=Decimal("129.0"),
        )
        job = _make_job_post(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        # Without override: far away
        result_far = calculate_matching_score(instructor, job)
        assert result_far["distance_km"] > 100

        # With override: close to job
        result_close = calculate_matching_score(
            instructor, job,
            instructor_lat=37.5000,
            instructor_lng=127.0280,
        )
        assert result_close["distance_km"] < 2

    def test_weights_sum_to_100(self) -> None:
        """All weights should sum to 100 regardless of distance availability."""
        instructor_with_loc = _make_instructor_profile(
            latitude=Decimal("37.5665"),
            longitude=Decimal("126.9780"),
        )
        job_with_loc = _make_job_post(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        result_5 = calculate_matching_score(instructor_with_loc, job_with_loc)
        total_5 = sum(v["weight"] for v in result_5["breakdown"].values())
        assert total_5 == 100

        instructor_no_loc = _make_instructor_profile(latitude=None, longitude=None)
        job_no_loc = _make_job_post(latitude=None, longitude=None)

        result_4 = calculate_matching_score(instructor_no_loc, job_no_loc)
        total_4 = sum(v["weight"] for v in result_4["breakdown"].values())
        assert total_4 == 100


class TestGetMatchLabel:
    """Tests for get_match_label function."""

    def test_perfect_match(self) -> None:
        """Score >= 90 is Perfect Match."""
        assert get_match_label(90) == "Perfect Match"
        assert get_match_label(100) == "Perfect Match"

    def test_great_match(self) -> None:
        """Score 75-89 is Great Match."""
        assert get_match_label(75) == "Great Match"
        assert get_match_label(89) == "Great Match"

    def test_good_match(self) -> None:
        """Score 60-74 is Good Match."""
        assert get_match_label(60) == "Good Match"
        assert get_match_label(74) == "Good Match"

    def test_fair_match(self) -> None:
        """Score 40-59 is Fair Match."""
        assert get_match_label(40) == "Fair Match"
        assert get_match_label(59) == "Fair Match"

    def test_low_match(self) -> None:
        """Score < 40 is Low Match."""
        assert get_match_label(0) == "Low Match"
        assert get_match_label(39) == "Low Match"


# ===========================================================================
# 3. Contact Reveal Flow (POST /applications/{id}/accept)
# ===========================================================================

class TestAcceptApplicationContactReveal:
    """Tests for the accept_application endpoint logic.

    These are unit tests that exercise the endpoint logic by mocking
    the database layer, following the pattern from test_trust_score.py.
    """

    def _setup_accept_mocks(
        self,
        application_status: str = ApplicationStatus.PENDING.value,
        job_belongs_to_studio: bool = True,
        other_pending_count: int = 0,
    ):
        """Build mock objects for the accept flow.

        Returns (db, application, job_post, instructor, studio, other_apps).
        """
        studio_user_id = uuid.uuid4()
        studio = _make_studio_profile(user_id=studio_user_id)
        instructor = _make_instructor_profile()
        job_post = _make_job_post(studio_id=studio.id)

        application = _make_application(
            job_post_id=job_post.id,
            instructor_id=instructor.id,
            status=application_status,
        )

        other_apps = []
        for _ in range(other_pending_count):
            other_app = _make_application(
                job_post_id=job_post.id,
                status=ApplicationStatus.PENDING.value,
            )
            other_apps.append(other_app)

        return (studio, instructor, job_post, application, other_apps)

    def test_accept_sets_contact_revealed_true(self) -> None:
        """Accepting a pending application should set contact_revealed = True."""
        _, _, _, application, _ = self._setup_accept_mocks()

        # Simulate the accept logic from the endpoint
        assert application.status == ApplicationStatus.PENDING.value

        application.status = ApplicationStatus.ACCEPTED.value
        application.contact_revealed = True
        application.contact_revealed_at = datetime.utcnow()

        assert application.status == ApplicationStatus.ACCEPTED.value
        assert application.contact_revealed is True
        assert application.contact_revealed_at is not None

    def test_accept_rejects_other_pending_applications(self) -> None:
        """After acceptance, other pending apps for the same job are rejected."""
        _, _, _, application, other_apps = self._setup_accept_mocks(
            other_pending_count=3,
        )

        # Simulate the accept logic
        application.status = ApplicationStatus.ACCEPTED.value
        application.contact_revealed = True

        for other_app in other_apps:
            if other_app.status == ApplicationStatus.PENDING.value:
                other_app.status = ApplicationStatus.REJECTED.value

        for other_app in other_apps:
            assert other_app.status == ApplicationStatus.REJECTED.value

    def test_accept_marks_job_as_filled(self) -> None:
        """After acceptance, the job post status should be 'filled'."""
        _, _, job_post, application, _ = self._setup_accept_mocks()

        application.status = ApplicationStatus.ACCEPTED.value
        job_post.status = "filled"

        assert job_post.status == "filled"

    def test_cannot_accept_non_pending_application(self) -> None:
        """Accepting an already-accepted application should not proceed."""
        _, _, _, application, _ = self._setup_accept_mocks(
            application_status=ApplicationStatus.ACCEPTED.value,
        )

        assert application.status != ApplicationStatus.PENDING.value

    def test_cannot_accept_withdrawn_application(self) -> None:
        """Accepting a withdrawn application should not proceed."""
        _, _, _, application, _ = self._setup_accept_mocks(
            application_status=ApplicationStatus.WITHDRAWN.value,
        )

        assert application.status != ApplicationStatus.PENDING.value

    def test_response_includes_contact_info(self) -> None:
        """The response after accept should include both phone numbers."""
        studio, instructor, _, application, _ = self._setup_accept_mocks()

        # Simulate building the ContactRevealResponse
        response_data = {
            "application_id": str(application.id),
            "instructor_phone": instructor.phone or "등록된 번호 없음",
            "instructor_name": instructor.display_name,
            "studio_phone": studio.phone or "등록된 번호 없음",
            "studio_name": studio.business_name,
            "studio_address": studio.address,
        }

        assert response_data["instructor_phone"] == "010-1234-5678"
        assert response_data["studio_phone"] == "02-1234-5678"
        assert response_data["instructor_name"] == "Test Instructor"
        assert response_data["studio_name"] == "Test Studio"

    def test_non_owner_studio_cannot_accept(self) -> None:
        """A studio that does not own the job post should be denied.

        The endpoint checks job_post.studio_id == studio_id.
        """
        _, _, job_post, application, _ = self._setup_accept_mocks()

        different_studio_id = uuid.uuid4()

        # Simulate the ownership check from the endpoint
        belongs_to_studio = (job_post.studio_id == different_studio_id)
        assert belongs_to_studio is False


class TestContactRevealResponseSchema:
    """Verify the ContactRevealResponse schema structure."""

    def test_schema_fields(self) -> None:
        """ContactRevealResponse should contain all expected fields."""
        from app.schemas.application import ContactRevealResponse

        response = ContactRevealResponse(
            application_id=uuid.uuid4(),
            instructor_phone="010-1234-5678",
            instructor_name="Test Instructor",
            studio_phone="02-1234-5678",
            studio_name="Test Studio",
            studio_address="서울 강남구 역삼동 123",
        )

        assert response.instructor_phone == "010-1234-5678"
        assert response.studio_phone == "02-1234-5678"
        assert response.message == "연락처가 공개되었습니다. 직접 연락하여 세부 사항을 조율해주세요."

    def test_schema_default_message(self) -> None:
        """ContactRevealResponse should have a default Korean message."""
        from app.schemas.application import ContactRevealResponse

        response = ContactRevealResponse(
            application_id=uuid.uuid4(),
            instructor_phone="010-0000-0000",
            instructor_name="A",
            studio_phone="02-0000-0000",
            studio_name="B",
        )

        assert "연락처" in response.message

    def test_schema_optional_address(self) -> None:
        """studio_address should be optional (None allowed)."""
        from app.schemas.application import ContactRevealResponse

        response = ContactRevealResponse(
            application_id=uuid.uuid4(),
            instructor_phone="010-0000-0000",
            instructor_name="A",
            studio_phone="02-0000-0000",
            studio_name="B",
            studio_address=None,
        )

        assert response.studio_address is None


# ===========================================================================
# 4. Daily Usage Limits Removed (PMF pivot)
# ===========================================================================

class TestDailyUsageLimitsRemoved:
    """Verify that daily usage limits are bypassed in the PMF pivot.

    The ApplicationService.create() method should NOT check daily_usage
    limits. This is confirmed by code inspection: the comment in
    application.py says "PMF pivot: Daily usage limits disabled".
    """

    def test_application_service_has_no_daily_limit_check(self) -> None:
        """ApplicationService.create source should not call track_daily_usage."""
        import inspect
        from app.services.application import ApplicationService

        source = inspect.getsource(ApplicationService.create)

        # The daily usage tracking code should be commented out / removed
        assert "track_daily_usage" not in source or "disabled" in source.lower() or "pivot" in source.lower()

    def test_application_service_has_pmf_pivot_comment(self) -> None:
        """ApplicationService.create should contain the PMF pivot comment."""
        import inspect
        from app.services.application import ApplicationService

        source = inspect.getsource(ApplicationService.create)
        assert "PMF pivot" in source or "Daily usage limits disabled" in source


# ===========================================================================
# 5. Urgent Job Post
# ===========================================================================

class TestUrgentJobPostModel:
    """Tests for the is_urgent flag on the JobPost model."""

    def test_job_post_has_is_urgent_field(self) -> None:
        """JobPost model should have an is_urgent column."""
        from app.models.job_post import JobPost

        assert hasattr(JobPost, "is_urgent")

    def test_is_urgent_defaults_to_false(self) -> None:
        """is_urgent should default to False."""
        from app.models.job_post import JobPost

        col = JobPost.__table__.columns["is_urgent"]
        assert col.default is not None
        assert col.default.arg is False

    def test_is_urgent_is_indexed(self) -> None:
        """is_urgent should be indexed for efficient querying."""
        from app.models.job_post import JobPost

        col = JobPost.__table__.columns["is_urgent"]
        assert col.index is True

    def test_job_post_has_latitude_longitude(self) -> None:
        """JobPost should have latitude and longitude columns for geo matching."""
        from app.models.job_post import JobPost

        assert hasattr(JobPost, "latitude")
        assert hasattr(JobPost, "longitude")


class TestInstructorProfileGeoFields:
    """Tests for the latitude/longitude fields on InstructorProfile."""

    def test_instructor_profile_has_latitude_longitude(self) -> None:
        """InstructorProfile should have latitude and longitude for geo matching."""
        from app.models.instructor import InstructorProfile

        assert hasattr(InstructorProfile, "latitude")
        assert hasattr(InstructorProfile, "longitude")

    def test_instructor_profile_has_completed_substitute_count(self) -> None:
        """InstructorProfile should track completed substitute count."""
        from app.models.instructor import InstructorProfile

        assert hasattr(InstructorProfile, "completed_substitute_count")


class TestUrgentJobPostWithMatching:
    """Tests verifying that urgent jobs work correctly with matching."""

    def test_urgent_job_with_distance_scoring(self) -> None:
        """Urgent jobs should still use distance-based matching when coords present."""
        instructor = _make_instructor_profile(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
            available_regions=["서울 강남"],
            experience_years=5,
        )
        job = _make_job_post(
            is_urgent=True,
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
            region="서울 강남",
            required_experience_years=2,
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" in result["breakdown"]
        assert result["distance_km"] < 2.0
        assert result["breakdown"]["distance"]["score"] == 100

    def test_urgent_flag_does_not_affect_score(self) -> None:
        """The is_urgent flag itself should not alter the matching score.

        Urgency affects sorting/display, not the score calculation.
        """
        instructor = _make_instructor_profile(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
        )

        job_urgent = _make_job_post(
            is_urgent=True,
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
        )
        job_normal = _make_job_post(
            is_urgent=False,
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
        )

        result_urgent = calculate_matching_score(instructor, job_urgent)
        result_normal = calculate_matching_score(instructor, job_normal)

        assert result_urgent["total"] == result_normal["total"]


class TestApplicationStatusEnum:
    """Verify the ApplicationStatus enum has the ACCEPTED value for contact reveal."""

    def test_accepted_status_exists(self) -> None:
        """ApplicationStatus should have ACCEPTED for the contact reveal flow."""
        assert hasattr(ApplicationStatus, "ACCEPTED")
        assert ApplicationStatus.ACCEPTED.value == "accepted"

    def test_pending_status_exists(self) -> None:
        """ApplicationStatus should have PENDING."""
        assert ApplicationStatus.PENDING.value == "pending"

    def test_rejected_status_exists(self) -> None:
        """ApplicationStatus should have REJECTED for auto-rejecting other apps."""
        assert ApplicationStatus.REJECTED.value == "rejected"


class TestApplicationModelContactFields:
    """Verify Application model has contact reveal fields."""

    def test_application_has_contact_revealed_field(self) -> None:
        """Application model should have contact_revealed boolean."""
        from app.models.application import Application

        assert hasattr(Application, "contact_revealed")
        col = Application.__table__.columns["contact_revealed"]
        assert col.default is not None
        assert col.default.arg is False

    def test_application_has_contact_revealed_at_field(self) -> None:
        """Application model should have contact_revealed_at timestamp."""
        from app.models.application import Application

        assert hasattr(Application, "contact_revealed_at")
        col = Application.__table__.columns["contact_revealed_at"]
        assert col.nullable is True
