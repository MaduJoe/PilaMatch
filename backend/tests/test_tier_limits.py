"""Integration-style tests for tier-based limits via API endpoints.

These tests verify that tier limits are enforced at the service layer
through the check_can_apply and check_can_post functions, and that
the tier/penalty/payment-confirmation endpoints return expected shapes.

Uses mock pattern consistent with other tests in the project.
"""

import uuid
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import (
    TeacherTier,
    CenterTier,
    PenaltyType,
    PenaltyStatus,
    ApplicationStatus,
    PaymentConfirmationStatus,
)
from app.services.tier_evaluation import (
    check_can_apply,
    check_can_post,
    get_tier_display,
    TEACHER_TIER_LIMITS,
    CENTER_TIER_LIMITS,
)
from app.services.penalty_service import record_no_show
from app.services.payment_confirmation import mark_paid
from app.schemas.tier import TierResponse, TierPublicResponse, TierRequirementsResponse
from app.schemas.penalty import PenaltyReportRequest, PenaltyRecordResponse
from app.schemas.payment_confirmation import (
    MarkPaidRequest,
    PaymentConfirmationResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    user_id: Optional[uuid.UUID] = None,
    role: str = "instructor",
    phone_verified: bool = True,
    tier: Optional[str] = None,
    daily_applications_today: int = 0,
    last_usage_reset_date: Optional[date] = None,
    suspension_until: Optional[datetime] = None,
    is_suspended: bool = False,
    no_show_count: int = 0,
    identity_verified: bool = False,
    business_verified: bool = False,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.role = role
    user.phone_verified = phone_verified
    user.tier = tier
    user.tier_computed_at = None
    user.daily_applications_today = daily_applications_today
    user.last_usage_reset_date = last_usage_reset_date
    user.suspension_until = suspension_until
    user.is_suspended = is_suspended
    user.no_show_count = no_show_count
    user.identity_verified = identity_verified
    user.business_verified = business_verified
    return user


# ===========================================================================
# 1. Instructor Daily Limit (T1)
# ===========================================================================

class TestInstructorDailyLimitT1:
    """T1 instructor is blocked after 2 daily applications."""

    async def test_instructor_daily_limit_t1_blocked(self) -> None:
        """T1 instructor with 2 applications today is blocked."""
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
        assert "2" in reason

    async def test_instructor_daily_limit_t1_allowed(self) -> None:
        """T1 instructor with 1 application today can still apply."""
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

    async def test_instructor_daily_limit_t2_higher(self) -> None:
        """T2 instructor has higher limit (3), not blocked at 2."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T2_VERIFIED.value,
            daily_applications_today=2,
            last_usage_reset_date=date.today(),
        )

        db = AsyncMock()
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()

        can_apply, reason = await check_can_apply(db, user.id)
        assert can_apply is True

    async def test_instructor_no_tier_defaults_to_t1(self) -> None:
        """Instructor with no tier set defaults to T1 limits (2)."""
        user = _make_user(
            role="instructor",
            tier=None,  # No tier set
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


# ===========================================================================
# 2. Studio Active Post Limit (C1)
# ===========================================================================

class TestStudioActivePostLimitC1:
    """C1 studio is blocked after 2 active posts."""

    async def test_studio_active_post_limit_c1_blocked(self) -> None:
        """C1 studio with 2 active posts is blocked."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
        )
        studio_id = uuid.uuid4()

        db = AsyncMock()
        results = []

        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = studio_id
        results.append(profile_id_result)

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        results.append(count_result)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is False
        assert "2" in reason

    async def test_studio_active_post_limit_c1_allowed(self) -> None:
        """C1 studio with 1 active post can create another."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
        )
        studio_id = uuid.uuid4()

        db = AsyncMock()
        results = []

        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

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

    async def test_studio_c2_higher_limit(self) -> None:
        """C2 studio has 10 active post limit, not blocked at 2."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C2_VERIFIED.value,
        )
        studio_id = uuid.uuid4()

        db = AsyncMock()
        results = []

        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = studio_id
        results.append(profile_id_result)

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        results.append(count_result)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is True

    async def test_studio_no_profile_fails(self) -> None:
        """Studio without profile cannot post."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
        )

        db = AsyncMock()
        results = []

        user_result_mock = MagicMock()
        user_result_mock.scalar_one_or_none.return_value = user
        results.append(user_result_mock)

        profile_id_result = MagicMock()
        profile_id_result.scalar_one_or_none.return_value = None  # No profile
        results.append(profile_id_result)

        db.execute = AsyncMock(side_effect=results)

        can_post, reason = await check_can_post(db, user.id)
        assert can_post is False
        assert "profile not found" in reason.lower()


# ===========================================================================
# 3. Tier Endpoint Shape Validation
# ===========================================================================

class TestTierEndpointResponse:
    """Verify tier endpoint returns valid response structures."""

    async def test_tier_endpoint_returns_my_tier(self) -> None:
        """GET /tier/me returns valid TierResponse fields (via get_tier_display)."""
        user = _make_user(
            role="instructor",
            tier=TeacherTier.T1_BASIC.value,
        )

        db = AsyncMock()
        results = []

        # User query
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

        # Completed count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        results.append(count_result)

        # Profile for requirements
        profile_mock = MagicMock()
        profile_mock.display_name = "Test"
        profile_mock.certifications = []
        profile_for_req = MagicMock()
        profile_for_req.scalar_one_or_none.return_value = profile_mock
        results.append(profile_for_req)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        display = await get_tier_display(db, user.id)

        # Validate against TierResponse schema
        response = TierResponse(**display)
        assert response.tier == TeacherTier.T1_BASIC.value
        assert response.tier_label == "Basic"
        assert response.tier_label_ko == "기본"
        assert response.tier_color == "gray"
        assert response.role == "instructor"
        assert response.completed_jobs_recent == 0
        assert response.no_show_recent == 0
        assert response.next_tier == TeacherTier.T2_VERIFIED.value
        assert isinstance(response.missing_requirements, list)

    async def test_tier_response_for_studio(self) -> None:
        """TierResponse for studio role."""
        user = _make_user(
            role="studio",
            tier=CenterTier.C1_BASIC.value,
            business_verified=False,
        )

        db = AsyncMock()
        results = []

        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        results.append(user_result)

        penalty_result = MagicMock()
        penalty_result.all.return_value = []
        results.append(penalty_result)

        # Completed count for studio
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        results.append(count_result)

        # Profile for requirements
        profile_mock = MagicMock()
        profile_mock.location_proof_verified = False
        profile_for_req = MagicMock()
        profile_for_req.scalar_one_or_none.return_value = profile_mock
        results.append(profile_for_req)

        db.execute = AsyncMock(side_effect=results)
        db.commit = AsyncMock()

        display = await get_tier_display(db, user.id)
        response = TierResponse(**display)

        assert response.tier == CenterTier.C1_BASIC.value
        assert response.role == "studio"
        assert response.next_tier == CenterTier.C2_VERIFIED.value


# ===========================================================================
# 4. Penalty Report Shape
# ===========================================================================

class TestPenaltyReportEndpoint:
    """Verify penalty report creates a penalty record correctly."""

    @patch("app.services.event_log.EventLogService")
    async def test_penalty_report_endpoint_creates_penalty(self, mock_event_cls) -> None:
        """POST /penalties/report creates a penalty via record_no_show."""
        mock_event_cls.return_value.log = AsyncMock()
        user = _make_user(
            role="instructor",
            no_show_count=0,
            tier=TeacherTier.T2_VERIFIED.value,
        )
        reporter_id = uuid.uuid4()

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))

        # User query for record_no_show
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=user_result)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        record = await record_no_show(db, user.id, reporter_id)

        assert len(added) == 1
        created = added[0]
        assert created.penalty_type == PenaltyType.NO_SHOW.value
        assert created.status == PenaltyStatus.ACTIVE.value
        # User should be demoted
        assert user.tier == TeacherTier.T1_BASIC.value
        # User should be suspended for 14 days
        assert user.suspension_until is not None


# ===========================================================================
# 5. Payment mark_paid Shape
# ===========================================================================

class TestPaymentMarkPaidEndpoint:
    """Verify POST /applications/{id}/mark-paid works via mark_paid service."""

    async def test_payment_mark_paid_endpoint(self) -> None:
        """mark_paid creates a PaymentConfirmation with correct fields."""
        application = MagicMock()
        application.id = uuid.uuid4()
        application.instructor_id = uuid.uuid4()
        application.status = ApplicationStatus.ACCEPTED.value

        center_user_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()

        db = AsyncMock()
        added = []
        db.add = MagicMock(side_effect=lambda obj: added.append(obj))

        # 1. Application query
        app_result = MagicMock()
        app_result.scalar_one_or_none.return_value = application
        # 2. Existing confirmation (none)
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        # 3. Instructor user_id
        inst_result = MagicMock()
        inst_result.scalar_one_or_none.return_value = instructor_user_id

        db.execute = AsyncMock(side_effect=[app_result, existing_result, inst_result])
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await mark_paid(
            db, application.id, center_user_id, Decimal("40000")
        )

        assert len(added) == 1
        created = added[0]
        assert created.application_id == application.id
        assert created.center_user_id == center_user_id
        assert created.instructor_user_id == instructor_user_id
        assert created.amount == Decimal("40000")
        assert created.status == PaymentConfirmationStatus.PENDING.value
        assert created.center_marked_paid_at is not None


# ===========================================================================
# 6. Schema Validation
# ===========================================================================

class TestSchemaValidation:
    """Verify Pydantic schemas accept correct data."""

    def test_penalty_report_request_schema(self) -> None:
        """PenaltyReportRequest accepts valid data."""
        req = PenaltyReportRequest(
            reported_user_id=str(uuid.uuid4()),
            penalty_type=PenaltyType.NO_SHOW.value,
            description="Test no-show report",
        )
        assert req.penalty_type == "no_show"

    def test_mark_paid_request_schema(self) -> None:
        """MarkPaidRequest accepts valid amount."""
        req = MarkPaidRequest(amount=Decimal("50000"))
        assert req.amount == Decimal("50000")

    def test_tier_requirements_response_schema(self) -> None:
        """TierRequirementsResponse accepts teacher and center tier data."""
        response = TierRequirementsResponse(
            teacher_tiers=[
                {"tier": "t1_basic", "label": "Basic", "requirements": []},
            ],
            center_tiers=[
                {"tier": "c1_basic", "label": "Basic", "requirements": []},
            ],
        )
        assert len(response.teacher_tiers) == 1
        assert len(response.center_tiers) == 1

    def test_tier_public_response_schema(self) -> None:
        """TierPublicResponse accepts valid data."""
        response = TierPublicResponse(
            user_id=str(uuid.uuid4()),
            tier=TeacherTier.T1_BASIC.value,
            tier_label="Basic",
            tier_color="gray",
            role="instructor",
            completed_jobs_recent=3,
            no_show_recent=0,
        )
        assert response.tier == "t1_basic"
        assert response.role == "instructor"
