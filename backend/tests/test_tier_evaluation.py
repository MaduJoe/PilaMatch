"""Unit tests for Tier Evaluation service (v4.0).

Tests cover teacher tier evaluation (T1/T2/T3), center tier evaluation
(C1/C2), tier display helpers, and access checks (daily application
limits, active post limits).
"""

import uuid
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import (
    TeacherTier,
    CenterTier,
    PenaltyType,
    ApplicationStatus,
)
from app.services.tier_evaluation import (
    evaluate_teacher_tier,
    evaluate_center_tier,
    get_tier_display,
    get_tier_limits,
    check_can_apply,
    check_can_post,
    TEACHER_TIER_LIMITS,
    CENTER_TIER_LIMITS,
)


# ---------------------------------------------------------------------------
# Helpers: lightweight fakes
# ---------------------------------------------------------------------------

def _make_user(
    user_id: Optional[uuid.UUID] = None,
    role: str = "instructor",
    phone_verified: bool = False,
    identity_verified: bool = False,
    business_verified: bool = False,
    no_show_count: int = 0,
    is_suspended: bool = False,
    tier: Optional[str] = None,
    suspension_until: Optional[datetime] = None,
    restriction_until: Optional[datetime] = None,
    daily_applications_today: int = 0,
    last_usage_reset_date: Optional[date] = None,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    user.phone_verified = phone_verified
    user.identity_verified = identity_verified
    user.business_verified = business_verified
    user.no_show_count = no_show_count
    user.is_suspended = is_suspended
    user.tier = tier
    user.tier_computed_at = None
    user.suspension_until = suspension_until
    user.restriction_until = restriction_until
    user.daily_applications_today = daily_applications_today
    user.last_usage_reset_date = last_usage_reset_date
    return user


def _make_instructor_profile(
    user_id: Optional[uuid.UUID] = None,
    display_name: str = "Test Instructor",
    available_regions: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    certifications: Optional[list] = None,
) -> MagicMock:
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.display_name = display_name
    profile.available_regions = available_regions or ["서울 강남"]
    profile.categories = categories or ["pilates"]
    profile.certifications = certifications or []
    return profile


def _make_studio_profile(
    user_id: Optional[uuid.UUID] = None,
    business_name: str = "Test Studio",
    address: str = "서울 강남구 역삼동 123",
    phone: str = "02-1234-5678",
    location_proof_verified: bool = False,
) -> MagicMock:
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.business_name = business_name
    profile.address = address
    profile.phone = phone
    profile.location_proof_verified = location_proof_verified
    return profile


def _mock_db_for_teacher_eval(
    user: Optional[MagicMock] = None,
    profile: Optional[MagicMock] = None,
    penalty_counts: Optional[Dict[str, int]] = None,
    completed_count: int = 0,
) -> AsyncMock:
    """Build a mock AsyncSession for evaluate_teacher_tier.

    Call sequence (from reading the source):
    1. select(User).where(...) -> user
    2. select(InstructorProfile).where(...) -> profile  (always fetched if user is instructor)
    3. _get_recent_penalty_counts: select(...).group_by(...) -> penalty rows
    4. _get_recent_completed_count:
       4a. select(InstructorProfile.id).where(...) -> profile.id
       4b. select(func.count(...)).where(...) -> completed_count
    """
    db = AsyncMock()
    results = []

    # 1. User query
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    results.append(user_result)

    if user and user.role == "instructor":
        # 2. Profile query (always fetched before phone_verified check)
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile
        results.append(profile_result)

        # Steps 3-4 only happen if phone_verified AND profile has basics
        if (user.phone_verified and profile
                and profile.display_name and profile.available_regions and profile.categories):
            # 3. Penalty counts query (returns rows of (type, count))
            counts = penalty_counts or {pt.value: 0 for pt in PenaltyType}
            penalty_result = MagicMock()
            penalty_result.all.return_value = [
                (ptype, count) for ptype, count in counts.items() if count > 0
            ]
            results.append(penalty_result)

            # 4a. InstructorProfile.id for completed count
            profile_id_result = MagicMock()
            profile_id_result.scalar_one_or_none.return_value = profile.id if profile else None
            results.append(profile_id_result)

            # 4b. Completed count
            count_result = MagicMock()
            count_result.scalar_one.return_value = completed_count
            results.append(count_result)

    db.execute = AsyncMock(side_effect=results)
    db.commit = AsyncMock()
    return db


def _mock_db_for_center_eval(
    user: Optional[MagicMock] = None,
    profile: Optional[MagicMock] = None,
    penalty_counts: Optional[Dict[str, int]] = None,
    completed_count: int = 0,
) -> AsyncMock:
    """Build a mock AsyncSession for evaluate_center_tier.

    Call sequence (from reading the source):
    1. select(User).where(...) -> user
    2. select(StudioProfile).where(...) -> profile  (always fetched if user is studio)
    3. _get_recent_penalty_counts: select(...).group_by(...) -> penalty rows
    4. _get_recent_completed_count:
       4a-b. select(func.count(...)).join(...).where(...) -> completed_count
    """
    db = AsyncMock()
    results = []

    # 1. User query
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = user
    results.append(user_result)

    if user and user.role == "studio":
        # 2. Profile query (always fetched before phone_verified check)
        profile_result = MagicMock()
        profile_result.scalar_one_or_none.return_value = profile
        results.append(profile_result)

        # Steps 3-4 only happen if phone_verified AND profile has basics
        if (user.phone_verified and profile
                and profile.business_name and profile.address and profile.phone):
            # 3. Penalty counts
            counts = penalty_counts or {pt.value: 0 for pt in PenaltyType}
            penalty_result = MagicMock()
            penalty_result.all.return_value = [
                (ptype, count) for ptype, count in counts.items() if count > 0
            ]
            results.append(penalty_result)

            # 4. Completed count for center (single query with join)
            count_result = MagicMock()
            count_result.scalar_one.return_value = completed_count
            results.append(count_result)

    db.execute = AsyncMock(side_effect=results)
    db.commit = AsyncMock()
    return db


# ===========================================================================
# Teacher Tier Evaluation
# ===========================================================================

class TestEvaluateTeacherTier:
    """Tests for evaluate_teacher_tier function."""

    async def test_new_instructor_gets_t1(self) -> None:
        """New user with phone verified and basic profile gets T1."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=False,
        )
        profile = _make_instructor_profile(user_id=user.id)
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=0,
        )

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T1_BASIC

    async def test_instructor_without_phone_stays_t1(self) -> None:
        """Instructor without phone verification stays at T1."""
        user = _make_user(role="instructor", phone_verified=False)
        db = _mock_db_for_teacher_eval(user=user)

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T1_BASIC

    async def test_instructor_t2_requirements(self) -> None:
        """Instructor meeting T2 requirements: identity verified + 1 verified cert + 2 completed + 0 no-show."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=True,
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=[{"name": "PMA-CPT", "is_verified": True}],
        )
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=2,
            penalty_counts={"no_show": 0, "same_day_cancel": 0, "late": 0, "cancel_after_confirm": 0},
        )

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T2_VERIFIED

    async def test_instructor_t3_requirements(self) -> None:
        """Instructor meeting T3 requirements: T2 + 5 completed + 0 no-show + 0 same_day_cancel + <=1 late."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=True,
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=[{"name": "PMA-CPT", "is_verified": True}],
        )
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=5,
            penalty_counts={"no_show": 0, "same_day_cancel": 0, "late": 1, "cancel_after_confirm": 0},
        )

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T3_PRO

    async def test_instructor_no_show_prevents_t2(self) -> None:
        """Instructor with a no-show in 30 days stays at T1 even if other T2 conditions met."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=True,
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=[{"name": "PMA-CPT", "is_verified": True}],
        )
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=3,
            penalty_counts={"no_show": 1, "same_day_cancel": 0, "late": 0, "cancel_after_confirm": 0},
        )

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T1_BASIC

    async def test_instructor_no_profile_gets_t1(self) -> None:
        """Instructor with phone verified but no profile gets T1."""
        user = _make_user(role="instructor", phone_verified=True)
        db = _mock_db_for_teacher_eval(user=user, profile=None)

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T1_BASIC

    async def test_non_instructor_user_gets_t1(self) -> None:
        """Non-instructor (studio) user defaults to T1."""
        user = _make_user(role="studio", phone_verified=True)
        db = _mock_db_for_teacher_eval(user=user)

        tier = await evaluate_teacher_tier(db, user.id)
        assert tier == TeacherTier.T1_BASIC

    async def test_user_not_found_gets_t1(self) -> None:
        """If user does not exist, return T1."""
        db = _mock_db_for_teacher_eval(user=None)

        tier = await evaluate_teacher_tier(db, uuid.uuid4())
        assert tier == TeacherTier.T1_BASIC

    async def test_t3_blocked_by_same_day_cancel(self) -> None:
        """Same-day cancel prevents T3 even if other conditions met."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=True,
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=[{"name": "PMA-CPT", "is_verified": True}],
        )
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=5,
            penalty_counts={"no_show": 0, "same_day_cancel": 1, "late": 0, "cancel_after_confirm": 0},
        )

        tier = await evaluate_teacher_tier(db, user.id)
        # same_day_cancel > 0 blocks T3, but T2 conditions are met
        assert tier == TeacherTier.T2_VERIFIED

    async def test_t3_blocked_by_excessive_late(self) -> None:
        """More than 1 late penalty in 30d prevents T3."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            identity_verified=True,
        )
        profile = _make_instructor_profile(
            user_id=user.id,
            certifications=[{"name": "PMA-CPT", "is_verified": True}],
        )
        db = _mock_db_for_teacher_eval(
            user=user, profile=profile, completed_count=5,
            penalty_counts={"no_show": 0, "same_day_cancel": 0, "late": 2, "cancel_after_confirm": 0},
        )

        tier = await evaluate_teacher_tier(db, user.id)
        # late > 1 blocks T3, falls to T2
        assert tier == TeacherTier.T2_VERIFIED


# ===========================================================================
# Center Tier Evaluation
# ===========================================================================

class TestEvaluateCenterTier:
    """Tests for evaluate_center_tier function."""

    async def test_new_studio_gets_c1(self) -> None:
        """Phone-verified studio with basic profile gets C1."""
        user = _make_user(
            role="studio",
            phone_verified=True,
            business_verified=False,
        )
        profile = _make_studio_profile(user_id=user.id)
        db = _mock_db_for_center_eval(
            user=user, profile=profile, completed_count=0,
        )

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C1_BASIC

    async def test_studio_c2_requirements(self) -> None:
        """Studio meeting C2: business verified + location proof + 2 completed + <=1 cancel_after_confirm."""
        user = _make_user(
            role="studio",
            phone_verified=True,
            business_verified=True,
        )
        profile = _make_studio_profile(
            user_id=user.id,
            location_proof_verified=True,
        )
        db = _mock_db_for_center_eval(
            user=user, profile=profile, completed_count=2,
            penalty_counts={"no_show": 0, "same_day_cancel": 0, "late": 0, "cancel_after_confirm": 1},
        )

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C2_VERIFIED

    async def test_studio_no_business_verification_stays_c1(self) -> None:
        """Studio without business verification stays C1."""
        user = _make_user(
            role="studio",
            phone_verified=True,
            business_verified=False,
        )
        profile = _make_studio_profile(
            user_id=user.id,
            location_proof_verified=True,
        )
        db = _mock_db_for_center_eval(
            user=user, profile=profile, completed_count=5,
        )

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C1_BASIC

    async def test_studio_without_phone_stays_c1(self) -> None:
        """Studio without phone verification stays C1."""
        user = _make_user(role="studio", phone_verified=False)
        db = _mock_db_for_center_eval(user=user)

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C1_BASIC

    async def test_studio_no_location_proof_stays_c1(self) -> None:
        """Studio without location proof stays C1 even with business verification."""
        user = _make_user(
            role="studio",
            phone_verified=True,
            business_verified=True,
        )
        profile = _make_studio_profile(
            user_id=user.id,
            location_proof_verified=False,
        )
        db = _mock_db_for_center_eval(
            user=user, profile=profile, completed_count=5,
        )

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C1_BASIC

    async def test_studio_excessive_cancel_after_confirm_stays_c1(self) -> None:
        """Studio with >1 cancel_after_confirm stays C1."""
        user = _make_user(
            role="studio",
            phone_verified=True,
            business_verified=True,
        )
        profile = _make_studio_profile(
            user_id=user.id,
            location_proof_verified=True,
        )
        db = _mock_db_for_center_eval(
            user=user, profile=profile, completed_count=5,
            penalty_counts={"no_show": 0, "same_day_cancel": 0, "late": 0, "cancel_after_confirm": 2},
        )

        tier = await evaluate_center_tier(db, user.id)
        assert tier == CenterTier.C1_BASIC


# ===========================================================================
# Tier Display
# ===========================================================================

class TestGetTierDisplay:
    """Tests for get_tier_display function."""

    async def test_get_tier_display_returns_expected_fields(self) -> None:
        """Verify display dict has all expected keys for instructor."""
        user = _make_user(
            role="instructor",
            phone_verified=True,
            tier=TeacherTier.T1_BASIC.value,
        )

        # Build mock db for get_tier_display:
        # 1. User query
        # 2. _get_recent_penalty_counts
        # 3. _get_recent_completed_count (profile_id + count)
        # 4. Profile query for next tier requirements
        db = AsyncMock()
        results = []

        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        results.append(user_result)

        # Penalty counts
        penalty_result = MagicMock()
        penalty_result.all.return_value = []
        results.append(penalty_result)

        # Completed count: profile_id
        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = uuid.uuid4()
        results.append(profile_id_result)

        # Completed count: count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        results.append(count_result)

        # Profile query for next tier requirements
        profile = _make_instructor_profile(user_id=user.id)
        profile_for_display = MagicMock()
        profile_for_display.scalar_one_or_none.return_value = profile
        results.append(profile_for_display)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        display = await get_tier_display(db, user.id)

        expected_keys = {
            "tier", "tier_label", "tier_label_ko", "tier_color",
            "role", "completed_jobs_recent", "no_show_recent",
            "same_day_cancel_recent", "late_recent",
            "cancel_after_confirm_recent",
            "next_tier", "missing_requirements",
        }
        assert set(display.keys()) == expected_keys
        assert display["tier"] == TeacherTier.T1_BASIC.value
        assert display["tier_label"] == "Basic"
        assert display["tier_color"] == "gray"
        assert display["role"] == "instructor"


# ===========================================================================
# Tier Limits Lookup
# ===========================================================================

class TestGetTierLimits:
    """Tests for the get_tier_limits helper."""

    def test_teacher_t1_limits(self) -> None:
        """T1 Basic teacher has 2 daily application limit."""
        limits = get_tier_limits(TeacherTier.T1_BASIC.value)
        assert limits["daily_applications"] == 2
        assert limits["label"] == "Basic"

    def test_teacher_t2_limits(self) -> None:
        """T2 Verified teacher has 3 daily application limit."""
        limits = get_tier_limits(TeacherTier.T2_VERIFIED.value)
        assert limits["daily_applications"] == 3

    def test_teacher_t3_limits(self) -> None:
        """T3 Pro teacher has unlimited daily applications."""
        limits = get_tier_limits(TeacherTier.T3_PRO.value)
        assert limits["daily_applications"] == -1
        assert limits["matching_boost"] == 1.3

    def test_center_c1_limits(self) -> None:
        """C1 Basic center has 2 active posts limit."""
        limits = get_tier_limits(CenterTier.C1_BASIC.value)
        assert limits["active_posts"] == 2

    def test_center_c2_limits(self) -> None:
        """C2 Verified center has 10 active posts."""
        limits = get_tier_limits(CenterTier.C2_VERIFIED.value)
        assert limits["active_posts"] == 10
        assert limits["matching_boost"] == 1.15

    def test_unknown_tier_returns_t1_fallback(self) -> None:
        """Unknown tier string returns T1 Basic as fallback."""
        limits = get_tier_limits("unknown_tier")
        assert limits["daily_applications"] == 2


# ===========================================================================
# Access Checks: check_can_apply
# ===========================================================================

class TestCheckCanApply:
    """Tests for check_can_apply function."""

    async def test_check_can_apply_respects_daily_limit(self) -> None:
        """T1 user with 2 applications today is blocked."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T1_BASIC.value,
            daily_applications_today=2,
            last_usage_reset_date=date.today(),
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is False
        assert "한도 초과" in reason

    async def test_check_can_apply_t3_unlimited(self) -> None:
        """T3 Pro has no daily limit (returns True regardless of count)."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T3_PRO.value,
            daily_applications_today=100,
            last_usage_reset_date=date.today(),
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is True
        assert reason is None

    async def test_check_can_apply_suspended_user_blocked(self) -> None:
        """Suspended user cannot apply."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T1_BASIC.value,
            suspension_until=datetime.utcnow() + timedelta(days=7),
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is False
        assert "정지" in reason

    async def test_check_can_apply_user_not_found(self) -> None:
        """Non-existent user returns False."""
        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=user_result)

        can_apply, reason = await check_can_apply(db, uuid.uuid4())
        assert can_apply is False
        assert "User not found" in reason

    async def test_check_can_apply_under_limit(self) -> None:
        """T1 user with 1 application today can still apply."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T1_BASIC.value,
            daily_applications_today=1,
            last_usage_reset_date=date.today(),
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is True
        assert reason is None

    async def test_check_can_apply_resets_daily_counter_on_new_day(self) -> None:
        """Daily counter resets when last_usage_reset_date is yesterday."""
        yesterday = date.today() - timedelta(days=1)
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T1_BASIC.value,
            daily_applications_today=3,
            last_usage_reset_date=yesterday,
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is True
        assert reason is None
        # Counter should have been reset
        assert user.daily_applications_today == 0


# ===========================================================================
# Access Checks: check_can_post
# ===========================================================================

class TestCheckCanPost:
    """Tests for check_can_post function."""

    async def test_check_can_post_respects_limit(self) -> None:
        """C1 center with 2 active posts is blocked from posting more."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
        )

        db = AsyncMock()
        results = []

        # 1. User query
        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

        # 2. Studio profile id query
        studio_id = uuid.uuid4()
        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = studio_id
        results.append(profile_id_result)

        # 3. Active posts count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        results.append(count_result)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is False
        assert "한도 초과" in reason

    async def test_check_can_post_under_limit(self) -> None:
        """C1 center with 1 active post can still post."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
        )

        db = AsyncMock()
        results = []

        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

        studio_id = uuid.uuid4()
        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = studio_id
        results.append(profile_id_result)

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        results.append(count_result)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is True
        assert reason is None

    async def test_check_can_post_suspended_studio(self) -> None:
        """Suspended studio cannot post."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
            suspension_until=datetime.utcnow() + timedelta(days=7),
        )

        db = AsyncMock()
        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result_mock)

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is False
        assert "정지" in reason
