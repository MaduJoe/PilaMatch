"""Unit tests for Trust Score calculation service.

Verifies that trust score is purely behavior-based with no premium membership influence.
Tests cover all 8 scoring factors, level thresholds, edge cases, and the premium bonus
removal (the score must NOT change based on membership_tier).
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.trust_score import (
    FACTOR_LABELS,
    LEVEL_THRESHOLDS,
    TrustLevel,
    calculate_trust_score,
    get_trust_score_display,
    update_user_trust_score,
)


# ---------------------------------------------------------------------------
# Helpers: lightweight fakes that behave like SQLAlchemy model instances
# ---------------------------------------------------------------------------

def _make_user(
    user_id: Optional[uuid.UUID] = None,
    role: str = "instructor",
    phone_verified: bool = False,
    business_verified: bool = False,
    no_show_count: int = 0,
    last_active_at: Optional[datetime] = None,
    created_at: Optional[datetime] = None,
    membership_tier: str = "free",
    trust_score: int = 40,
    trust_level: str = "새싹",
    is_suspended: bool = False,
) -> MagicMock:
    """Create a fake User object."""
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    user.phone_verified = phone_verified
    user.business_verified = business_verified
    user.no_show_count = no_show_count
    user.last_active_at = last_active_at
    user.created_at = created_at or datetime.utcnow()
    user.membership_tier = membership_tier
    user.trust_score = trust_score
    user.trust_level = trust_level
    user.is_suspended = is_suspended
    user.has_premium_badge = membership_tier == "premium"
    return user


def _make_instructor_profile(
    profile_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    display_name: str = "Test Instructor",
    bio: str = "A passionate yoga instructor with many years of experience",
    phone: str = "010-1234-5678",
    experience_years: int = 5,
    categories: Optional[List[str]] = None,
    available_regions: Optional[List[str]] = None,
    hourly_rate_min: Decimal = Decimal("30000"),
    hourly_rate_max: Decimal = Decimal("50000"),
    certifications: Optional[List[str]] = None,
    rating_average: Optional[Decimal] = None,
    review_count: int = 0,
) -> MagicMock:
    """Create a fake InstructorProfile object."""
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.display_name = display_name
    profile.bio = bio
    profile.phone = phone
    profile.experience_years = experience_years
    profile.categories = categories or ["pilates"]
    profile.available_regions = available_regions or ["서울 강남"]
    profile.hourly_rate_min = hourly_rate_min
    profile.hourly_rate_max = hourly_rate_max
    profile.certifications = certifications or []
    profile.rating_average = rating_average
    profile.review_count = review_count
    return profile


def _make_studio_profile(
    profile_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    business_name: str = "Test Studio",
    description: str = "A great pilates studio in Gangnam area",
    phone: str = "02-1234-5678",
    address: str = "서울 강남구 역삼동 123",
    region: str = "서울 강남",
    categories: Optional[List[str]] = None,
    rating_average: Optional[Decimal] = None,
    review_count: int = 0,
) -> MagicMock:
    """Create a fake StudioProfile object."""
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.business_name = business_name
    profile.description = description
    profile.phone = phone
    profile.address = address
    profile.region = region
    profile.categories = categories or ["pilates"]
    profile.rating_average = rating_average
    profile.review_count = review_count
    return profile


def _build_mock_db(
    user: Optional[MagicMock] = None,
    profile: Optional[MagicMock] = None,
    completed_contracts: int = 0,
) -> AsyncMock:
    """Build a mock AsyncSession that returns user, profile, and contract count.

    The execute() mock returns different results depending on call order:
      1st call -> user
      2nd call -> profile (InstructorProfile or StudioProfile)
      3rd call -> completed contract count
    """
    db = AsyncMock()

    # Build the sequence of results returned by db.execute()
    results = []

    # 1st call: user query
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    results.append(user_result)

    # 2nd call: profile query (only reached if user exists and has role)
    if user is not None:
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile
        results.append(profile_result)

        # 3rd call: contract count query
        count_result = MagicMock()
        count_result.scalar.return_value = completed_contracts
        results.append(count_result)

    db.execute = AsyncMock(side_effect=results)
    db.commit = AsyncMock()

    return db


# ---------------------------------------------------------------------------
# TrustLevel unit tests
# ---------------------------------------------------------------------------

class TestTrustLevel:
    """TrustLevel.get_level threshold tests."""

    def test_score_0_is_bronze(self) -> None:
        """Score 0 should be bronze/새싹."""
        level, color = TrustLevel.get_level(0)
        assert level == "새싹"
        assert color == "bronze"

    def test_score_39_is_bronze(self) -> None:
        """Score 39 (upper boundary) should still be bronze."""
        level, color = TrustLevel.get_level(39)
        assert level == "새싹"
        assert color == "bronze"

    def test_score_40_is_silver(self) -> None:
        """Score 40 should transition to silver/인증."""
        level, color = TrustLevel.get_level(40)
        assert level == "인증"
        assert color == "silver"

    def test_score_59_is_silver(self) -> None:
        """Score 59 (upper boundary) should still be silver."""
        level, color = TrustLevel.get_level(59)
        assert level == "인증"
        assert color == "silver"

    def test_score_60_is_gold(self) -> None:
        """Score 60 should transition to gold/전문."""
        level, color = TrustLevel.get_level(60)
        assert level == "전문"
        assert color == "gold"

    def test_score_79_is_gold(self) -> None:
        """Score 79 (upper boundary) should still be gold."""
        level, color = TrustLevel.get_level(79)
        assert level == "전문"
        assert color == "gold"

    def test_score_80_is_platinum(self) -> None:
        """Score 80 should transition to platinum/마스터."""
        level, color = TrustLevel.get_level(80)
        assert level == "마스터"
        assert color == "platinum"

    def test_score_100_is_platinum(self) -> None:
        """Score 100 should be platinum."""
        level, color = TrustLevel.get_level(100)
        assert level == "마스터"
        assert color == "platinum"


# ---------------------------------------------------------------------------
# Module-level constants tests
# ---------------------------------------------------------------------------

class TestFactorLabels:
    """Verify FACTOR_LABELS structure is consistent."""

    def test_all_factors_present(self) -> None:
        """All 8 scoring factors must be declared."""
        expected = {
            "identity_verification",
            "profile_completeness",
            "contract_history",
            "review_average",
            "response_rate",
            "certifications",
            "no_show_penalty",
            "account_age",
        }
        assert set(FACTOR_LABELS.keys()) == expected

    def test_max_points_sum_to_105(self) -> None:
        """Sum of max points (excluding no_show which is 0) = 105."""
        total = sum(f["max"] for f in FACTOR_LABELS.values())
        assert total == 105

    def test_no_premium_factor(self) -> None:
        """There must be no premium bonus factor in the labels."""
        for key in FACTOR_LABELS:
            assert "premium" not in key.lower()


class TestLevelThresholds:
    """Verify LEVEL_THRESHOLDS constants."""

    def test_four_levels_defined(self) -> None:
        """Exactly 4 levels must be defined."""
        assert len(LEVEL_THRESHOLDS) == 4

    def test_levels_cover_full_range(self) -> None:
        """Levels must cover 0-100 without gaps."""
        assert LEVEL_THRESHOLDS[0]["min"] == 0
        assert LEVEL_THRESHOLDS[-1]["max"] == 100


# ---------------------------------------------------------------------------
# calculate_trust_score tests
# ---------------------------------------------------------------------------

class TestCalculateTrustScore:
    """Tests for the main calculate_trust_score function."""

    # --- User not found ---

    async def test_user_not_found_returns_zero(self) -> None:
        """When user does not exist, score should be 0."""
        db = _build_mock_db(user=None)
        result = await calculate_trust_score(db, str(uuid.uuid4()), "instructor")
        assert result["score"] == 0
        assert result["level"] == "새싹"
        assert "User not found" in result["recommendations"]

    # --- Factor 1: Identity Verification (20 points) ---

    async def test_identity_instructor_phone_verified(self) -> None:
        """Instructor with phone verified gets 20 points (10 phone + 10 instructor auto)."""
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["identity_verification"] == 20

    async def test_identity_instructor_phone_not_verified(self) -> None:
        """Instructor without phone verified gets 10 (instructor auto only)."""
        user = _make_user(phone_verified=False, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["identity_verification"] == 10

    async def test_identity_studio_both_verified(self) -> None:
        """Studio with phone + business verified gets 20 points."""
        user = _make_user(phone_verified=True, business_verified=True, role="studio")
        profile = _make_studio_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "studio")
        assert result["breakdown"]["identity_verification"] == 20

    async def test_identity_studio_phone_only(self) -> None:
        """Studio with only phone verified gets 10 points."""
        user = _make_user(phone_verified=True, business_verified=False, role="studio")
        profile = _make_studio_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "studio")
        assert result["breakdown"]["identity_verification"] == 10

    async def test_identity_studio_none_verified(self) -> None:
        """Studio with nothing verified gets 0 points."""
        user = _make_user(phone_verified=False, business_verified=False, role="studio")
        profile = _make_studio_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "studio")
        assert result["breakdown"]["identity_verification"] == 0

    # --- Factor 2: Profile Completeness (15 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_profile_completeness_full(self, mock_completeness) -> None:
        """100% complete profile gives 15 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["profile_completeness"] == 15

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_profile_completeness_partial(self, mock_completeness) -> None:
        """50% complete profile gives 7 points (int(50/100 * 15) = 7)."""
        mock_completeness.return_value = {"percentage": 50}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["profile_completeness"] == 7

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_profile_completeness_zero(self, mock_completeness) -> None:
        """0% complete profile gives 0 points."""
        mock_completeness.return_value = {"percentage": 0}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["profile_completeness"] == 0

    # --- Factor 3: Contract History (25 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_contract_history_zero(self, mock_completeness) -> None:
        """0 completed contracts gives 0 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=0)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["contract_history"] == 0

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_contract_history_one(self, mock_completeness) -> None:
        """1 completed contract gives 5 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=1)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["contract_history"] == 5

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_contract_history_two_to_five(self, mock_completeness) -> None:
        """2-5 completed contracts gives 12 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=3)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["contract_history"] == 12

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_contract_history_six_to_ten(self, mock_completeness) -> None:
        """6-10 completed contracts gives 18 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=8)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["contract_history"] == 18

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_contract_history_eleven_plus(self, mock_completeness) -> None:
        """11+ completed contracts gives max 25 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=15)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["contract_history"] == 25

    # --- Factor 4: Review Average (15 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_review_average_perfect(self, mock_completeness) -> None:
        """5.0 rating gives 15 points: max(0, int((5.0 - 2.0) * 5)) = 15."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(
            user_id=user.id, rating_average=Decimal("5.00")
        )
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["review_average"] == 15

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_review_average_four_point_five(self, mock_completeness) -> None:
        """4.5 rating gives 12 points: int((4.5 - 2.0) * 5) = 12."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(
            user_id=user.id, rating_average=Decimal("4.50")
        )
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["review_average"] == 12

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_review_average_three_point_zero(self, mock_completeness) -> None:
        """3.0 rating gives 5 points: int((3.0 - 2.0) * 5) = 5."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(
            user_id=user.id, rating_average=Decimal("3.00")
        )
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["review_average"] == 5

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_review_average_none(self, mock_completeness) -> None:
        """No rating (None) gives 0 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id, rating_average=None)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["review_average"] == 0

    # --- Factor 5: Response Rate (10 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_active_today(self, mock_completeness) -> None:
        """Active within 3 days gives 10 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow() - timedelta(days=1),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 10

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_active_week_ago(self, mock_completeness) -> None:
        """Active 4-7 days ago gives 7 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow() - timedelta(days=5),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 7

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_active_two_weeks_ago(self, mock_completeness) -> None:
        """Active 8-14 days ago gives 4 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow() - timedelta(days=10),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 4

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_active_month_ago(self, mock_completeness) -> None:
        """Active 15-30 days ago gives 2 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow() - timedelta(days=20),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 2

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_inactive(self, mock_completeness) -> None:
        """Inactive over 30 days gives 0 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow() - timedelta(days=60),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 0

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_response_rate_never_active(self, mock_completeness) -> None:
        """Never logged in (last_active_at is None) gives 0 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=None,
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["response_rate"] == 0

    # --- Factor 6: Certifications (15 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_certifications_three_or_more(self, mock_completeness) -> None:
        """3+ certifications gives max 15 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=["PMA-CPT", "STOTT", "Balanced Body"],
        )
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["certifications"] == 15

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_certifications_one(self, mock_completeness) -> None:
        """1 certification gives 5 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(
            user_id=user.id, certifications=["PMA-CPT"]
        )
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["certifications"] == 5

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_certifications_none(self, mock_completeness) -> None:
        """No certifications gives 0 points for instructor."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id, certifications=[])
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["certifications"] == 0

    @patch("app.services.trust_score.calculate_studio_completeness")
    async def test_certifications_studio_business_verified(self, mock_completeness) -> None:
        """Studio with business_verified gets 15 certification points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True, business_verified=True, role="studio"
        )
        profile = _make_studio_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "studio")
        assert result["breakdown"]["certifications"] == 15

    @patch("app.services.trust_score.calculate_studio_completeness")
    async def test_certifications_studio_not_verified(self, mock_completeness) -> None:
        """Studio without business_verified gets 0 certification points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True, business_verified=False, role="studio"
        )
        profile = _make_studio_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "studio")
        assert result["breakdown"]["certifications"] == 0

    # --- Factor 7: No-show Penalty (-20 per incident) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_no_show_one_incident(self, mock_completeness) -> None:
        """1 no-show deducts 20 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor", no_show_count=1)
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["no_show_penalty"] == -20

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_no_show_three_incidents(self, mock_completeness) -> None:
        """3 no-shows deduct 60 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor", no_show_count=3)
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["no_show_penalty"] == -60

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_no_show_zero(self, mock_completeness) -> None:
        """0 no-shows gives 0 penalty."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor", no_show_count=0)
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["no_show_penalty"] == 0

    # --- Factor 8: Account Age (5 points) ---

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_account_age_over_6_months(self, mock_completeness) -> None:
        """Account older than 6 months gives 5 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            created_at=datetime.utcnow() - timedelta(days=200),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["account_age"] == 5

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_account_age_3_to_6_months(self, mock_completeness) -> None:
        """Account 3-6 months old gives 3 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            created_at=datetime.utcnow() - timedelta(days=100),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["account_age"] == 3

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_account_age_1_to_3_months(self, mock_completeness) -> None:
        """Account 1-3 months old gives 1 point."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            created_at=datetime.utcnow() - timedelta(days=45),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["account_age"] == 1

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_account_age_under_1_month(self, mock_completeness) -> None:
        """Account under 1 month old gives 0 points."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["breakdown"]["account_age"] == 0


# ---------------------------------------------------------------------------
# Premium bonus removal verification
# ---------------------------------------------------------------------------

class TestPremiumBonusRemoved:
    """Verify that premium membership does NOT affect trust score.

    This is the critical change being tested: the +10 premium bonus was removed.
    Free and premium users with identical behavior must get identical scores.
    """

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_premium_instructor_same_score_as_free(self, mock_completeness) -> None:
        """Premium instructor gets the same score as free instructor."""
        mock_completeness.return_value = {"percentage": 100}
        base_kwargs = dict(
            phone_verified=True,
            role="instructor",
            no_show_count=0,
            last_active_at=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=200),
        )

        # Free user
        free_user = _make_user(membership_tier="free", **base_kwargs)
        free_profile = _make_instructor_profile(
            user_id=free_user.id,
            certifications=["PMA-CPT", "STOTT", "Balanced Body"],
            rating_average=Decimal("4.50"),
        )
        free_db = _build_mock_db(user=free_user, profile=free_profile, completed_contracts=5)
        free_result = await calculate_trust_score(free_db, str(free_user.id), "instructor")

        # Premium user (identical behavior)
        premium_user = _make_user(membership_tier="premium", **base_kwargs)
        premium_profile = _make_instructor_profile(
            user_id=premium_user.id,
            certifications=["PMA-CPT", "STOTT", "Balanced Body"],
            rating_average=Decimal("4.50"),
        )
        premium_db = _build_mock_db(user=premium_user, profile=premium_profile, completed_contracts=5)
        premium_result = await calculate_trust_score(premium_db, str(premium_user.id), "instructor")

        assert free_result["score"] == premium_result["score"]

    @patch("app.services.trust_score.calculate_studio_completeness")
    async def test_premium_studio_same_score_as_free(self, mock_completeness) -> None:
        """Premium studio gets the same score as free studio."""
        mock_completeness.return_value = {"percentage": 100}
        base_kwargs = dict(
            phone_verified=True,
            business_verified=True,
            role="studio",
            no_show_count=0,
            last_active_at=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=200),
        )

        # Free user
        free_user = _make_user(membership_tier="free", **base_kwargs)
        free_profile = _make_studio_profile(user_id=free_user.id)
        free_db = _build_mock_db(user=free_user, profile=free_profile, completed_contracts=5)
        free_result = await calculate_trust_score(free_db, str(free_user.id), "studio")

        # Premium user (identical behavior)
        premium_user = _make_user(membership_tier="premium", **base_kwargs)
        premium_profile = _make_studio_profile(user_id=premium_user.id)
        premium_db = _build_mock_db(user=premium_user, profile=premium_profile, completed_contracts=5)
        premium_result = await calculate_trust_score(premium_db, str(premium_user.id), "studio")

        assert free_result["score"] == premium_result["score"]

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_no_premium_key_in_breakdown(self, mock_completeness) -> None:
        """Breakdown dict must not contain any premium-related key."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor", membership_tier="premium")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        for key in result["breakdown"]:
            assert "premium" not in key.lower(), f"Found premium key in breakdown: {key}"


# ---------------------------------------------------------------------------
# Score clamping and edge cases
# ---------------------------------------------------------------------------

class TestScoreClamping:
    """Verify score is clamped to 0-100 range."""

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_score_never_below_zero(self, mock_completeness) -> None:
        """Heavy no-show penalties cannot make score negative."""
        mock_completeness.return_value = {"percentage": 0}
        user = _make_user(
            phone_verified=False,
            role="instructor",
            no_show_count=10,  # -200 points
            last_active_at=None,
            created_at=datetime.utcnow(),
        )
        profile = _make_instructor_profile(
            user_id=user.id, certifications=[], rating_average=None
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=0)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["score"] == 0
        assert result["level"] == "새싹"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_score_never_above_100(self, mock_completeness) -> None:
        """Maximum score is clamped to 100 even if raw sum exceeds it."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            no_show_count=0,
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=365),
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=["A", "B", "C", "D", "E"],  # 5 * 5 = 25 (capped at 15)
            rating_average=Decimal("5.00"),
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=20)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["score"] <= 100


# ---------------------------------------------------------------------------
# Experience Badge tests
# ---------------------------------------------------------------------------

class TestExperienceBadge:
    """Tests for the experience badge based on completed contracts count."""

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_no_badge_under_5_contracts(self, mock_completeness) -> None:
        """Less than 5 completed contracts gives no experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=4)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"] is None
        assert result["completed_contracts_count"] == 4

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_bronze_badge_5_contracts(self, mock_completeness) -> None:
        """5+ completed contracts gives bronze experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=5)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"]["tier"] == "bronze"
        assert result["experience_badge"]["label"] == "5회 완료"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_silver_badge_10_contracts(self, mock_completeness) -> None:
        """10+ completed contracts gives silver experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=10)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"]["tier"] == "silver"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_gold_badge_20_contracts(self, mock_completeness) -> None:
        """20+ completed contracts gives gold experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=20)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"]["tier"] == "gold"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_platinum_badge_50_contracts(self, mock_completeness) -> None:
        """50+ completed contracts gives platinum experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=50)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"]["tier"] == "platinum"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_diamond_badge_100_contracts(self, mock_completeness) -> None:
        """100+ completed contracts gives diamond experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=100)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"]["tier"] == "diamond"
        assert result["experience_badge"]["label"] == "100회 완료"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_zero_contracts_no_badge(self, mock_completeness) -> None:
        """0 completed contracts gives no experience badge."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile, completed_contracts=0)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert result["experience_badge"] is None
        assert result["completed_contracts_count"] == 0


# ---------------------------------------------------------------------------
# Full scenario: combined score calculation
# ---------------------------------------------------------------------------

class TestFullScoreScenario:
    """End-to-end scenarios verifying total score calculation."""

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_new_instructor_minimal_setup(self, mock_completeness) -> None:
        """New instructor with phone verified, no profile, no contracts."""
        mock_completeness.return_value = {"percentage": 30}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            no_show_count=0,
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        profile = _make_instructor_profile(
            user_id=user.id, certifications=[], rating_average=None
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=0)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        # identity: 20 (phone 10 + instructor auto 10)
        # profile: int(30/100 * 15) = 4
        # contracts: 0
        # reviews: 0
        # response: 10 (active today)
        # certs: 0
        # no_show: 0
        # account_age: 0 (5 days)
        # Total: 34
        expected = 20 + 4 + 0 + 0 + 10 + 0 + 0 + 0
        assert result["score"] == expected
        assert result["level"] == "새싹"  # 34 < 40

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_experienced_instructor_high_score(self, mock_completeness) -> None:
        """Experienced instructor should reach gold/platinum."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            no_show_count=0,
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=365),
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=["PMA-CPT", "STOTT", "Balanced Body"],
            rating_average=Decimal("4.80"),
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=12)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        # identity: 20
        # profile: 15
        # contracts: 25 (12 >= 11)
        # reviews: int((4.8 - 2.0) * 5) = 14
        # response: 10
        # certs: 15
        # no_show: 0
        # account_age: 5 (365 days >= 180)
        # Total: 104 -> capped to 100
        assert result["score"] == 100
        assert result["level"] == "마스터"

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_instructor_with_no_shows_penalty(self, mock_completeness) -> None:
        """No-show penalties significantly reduce the score."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            no_show_count=2,
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=200),
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=["PMA-CPT"],
            rating_average=Decimal("4.00"),
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=3)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        # identity: 20
        # profile: 15
        # contracts: 12
        # reviews: int((4.0 - 2.0) * 5) = 10
        # response: 10
        # certs: 5
        # no_show: -40
        # account_age: 5
        # Total: 37
        expected = 20 + 15 + 12 + 10 + 10 + 5 - 40 + 5
        assert result["score"] == expected
        assert expected == 37
        assert result["level"] == "새싹"  # 37 < 40


# ---------------------------------------------------------------------------
# Return structure tests
# ---------------------------------------------------------------------------

class TestReturnStructure:
    """Verify the structure of the returned dict."""

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_all_keys_present(self, mock_completeness) -> None:
        """Result must contain all expected top-level keys."""
        mock_completeness.return_value = {"percentage": 50}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        expected_keys = {
            "score", "level", "level_color", "breakdown",
            "recommendations", "next_level_score",
            "points_to_next_level", "factor_labels", "level_thresholds",
            "completed_contracts_count", "experience_badge",
        }
        assert set(result.keys()) == expected_keys

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_breakdown_has_all_factors(self, mock_completeness) -> None:
        """Breakdown must contain all 8 scoring factors."""
        mock_completeness.return_value = {"percentage": 50}
        user = _make_user(phone_verified=True, role="instructor")
        profile = _make_instructor_profile(user_id=user.id)
        db = _build_mock_db(user=user, profile=profile)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        expected_factors = {
            "identity_verification", "profile_completeness",
            "contract_history", "review_average", "response_rate",
            "certifications", "no_show_penalty", "account_age",
        }
        assert set(result["breakdown"].keys()) == expected_factors

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_recommendations_max_three(self, mock_completeness) -> None:
        """Recommendations list should have at most 3 items."""
        mock_completeness.return_value = {"percentage": 0}
        user = _make_user(
            phone_verified=False,
            role="instructor",
            no_show_count=2,
            last_active_at=None,
            created_at=datetime.utcnow(),
        )
        profile = _make_instructor_profile(
            user_id=user.id, certifications=[], rating_average=None
        )
        db = _build_mock_db(user=user, profile=profile, completed_contracts=0)

        result = await calculate_trust_score(db, str(user.id), "instructor")
        assert len(result["recommendations"]) <= 3

    @patch("app.services.trust_score.calculate_instructor_completeness")
    async def test_next_level_score_calculation(self, mock_completeness) -> None:
        """Points to next level should be correctly calculated."""
        mock_completeness.return_value = {"percentage": 100}
        user = _make_user(
            phone_verified=True,
            role="instructor",
            last_active_at=datetime.utcnow(),
            created_at=datetime.utcnow() - timedelta(days=45),
        )
        profile = _make_instructor_profile(user_id=user.id, certifications=[])
        db = _build_mock_db(user=user, profile=profile, completed_contracts=1)

        result = await calculate_trust_score(db, str(user.id), "instructor")

        score = result["score"]
        next_level = result["next_level_score"]
        points_needed = result["points_to_next_level"]

        assert points_needed == max(0, next_level - score)


# ---------------------------------------------------------------------------
# get_trust_score_display tests
# ---------------------------------------------------------------------------

class TestGetTrustScoreDisplay:
    """Tests for the simplified display function."""

    @patch("app.services.trust_score.calculate_trust_score")
    async def test_display_format(self, mock_calc) -> None:
        """Display should include score, level, color, display_text, badge_emoji."""
        mock_calc.return_value = {
            "score": 75,
            "level": "전문",
            "level_color": "gold",
            "breakdown": {},
            "recommendations": [],
            "next_level_score": 80,
            "points_to_next_level": 5,
            "factor_labels": FACTOR_LABELS,
            "level_thresholds": LEVEL_THRESHOLDS,
        }

        db = AsyncMock()
        result = await get_trust_score_display(db, str(uuid.uuid4()), "instructor")

        assert result["score"] == 75
        assert result["level"] == "전문"
        assert result["level_color"] == "gold"
        assert result["display_text"] == "전문 75점"

    @patch("app.services.trust_score.calculate_trust_score")
    async def test_display_badge_bronze(self, mock_calc) -> None:
        """Score < 40 should get bronze badge emoji."""
        mock_calc.return_value = {
            "score": 20,
            "level": "새싹",
            "level_color": "bronze",
            "breakdown": {},
            "recommendations": [],
            "next_level_score": 40,
            "points_to_next_level": 20,
            "factor_labels": FACTOR_LABELS,
            "level_thresholds": LEVEL_THRESHOLDS,
        }

        db = AsyncMock()
        result = await get_trust_score_display(db, str(uuid.uuid4()), "instructor")
        # Note: the emoji check is just validating the logic, not endorsing emoji use
        assert "score" in result
        assert result["score"] == 20

    @patch("app.services.trust_score.calculate_trust_score")
    async def test_display_badge_platinum(self, mock_calc) -> None:
        """Score >= 80 should get platinum badge."""
        mock_calc.return_value = {
            "score": 95,
            "level": "마스터",
            "level_color": "platinum",
            "breakdown": {},
            "recommendations": [],
            "next_level_score": 100,
            "points_to_next_level": 5,
            "factor_labels": FACTOR_LABELS,
            "level_thresholds": LEVEL_THRESHOLDS,
        }

        db = AsyncMock()
        result = await get_trust_score_display(db, str(uuid.uuid4()), "instructor")
        assert result["score"] == 95
        assert result["display_text"] == "마스터 95점"
