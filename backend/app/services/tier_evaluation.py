"""Tier evaluation service — replaces Trust Score for user-facing trust signals.

Evaluates users into Teacher (T1/T2/T3) or Center (C1/C2) tiers based on
verification status, behavioral history, and activity metrics.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import (
    User, InstructorProfile, StudioProfile,
    Application, ApplicationStatus,
    PenaltyRecord,
)
from app.models.enums import TeacherTier, CenterTier, PenaltyType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier limits
# ---------------------------------------------------------------------------

TEACHER_TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    TeacherTier.T1_BASIC.value: {
        "daily_applications": 2,
        "extra_regions": 1,       # GPS + 1 region
        "urgent_limit": 1,        # 1 urgent per day
        "matching_boost": 1.0,
        "label": "Basic",
        "label_ko": "기본",
        "color": "gray",
    },
    TeacherTier.T2_VERIFIED.value: {
        "daily_applications": 3,
        "extra_regions": 2,       # GPS + 2 regions
        "urgent_limit": 2,        # 2 urgent per day
        "matching_boost": 1.0,
        "label": "Verified",
        "label_ko": "인증",
        "color": "blue",
    },
    TeacherTier.T3_PRO.value: {
        "daily_applications": -1,  # unlimited
        "extra_regions": -1,       # all regions
        "urgent_limit": -1,        # unlimited urgent
        "matching_boost": 1.3,
        "label": "Pro",
        "label_ko": "프로",
        "color": "gold",
    },
}

CENTER_TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    CenterTier.C1_BASIC.value: {
        "active_posts": 2,
        "extra_regions": 1,       # GPS + 1 region
        "urgent_limit": 1,        # 1 urgent per day
        "matching_boost": 1.0,
        "label": "Basic",
        "label_ko": "기본",
        "color": "gray",
    },
    CenterTier.C2_VERIFIED.value: {
        "active_posts": 10,
        "extra_regions": 2,       # GPS + 2 regions
        "urgent_limit": 2,        # 2 urgent per day
        "matching_boost": 1.15,
        "label": "Verified",
        "label_ko": "인증",
        "color": "blue",
    },
}


def get_tier_limits(tier: str) -> Dict[str, Any]:
    """Return limits and metadata for a tier string."""
    if tier in TEACHER_TIER_LIMITS:
        return TEACHER_TIER_LIMITS[tier]
    if tier in CENTER_TIER_LIMITS:
        return CENTER_TIER_LIMITS[tier]
    # Fallback
    return TEACHER_TIER_LIMITS[TeacherTier.T1_BASIC.value]


# ---------------------------------------------------------------------------
# Recent penalty counts helper
# ---------------------------------------------------------------------------

async def _get_recent_penalty_counts(
    db: AsyncSession, user_id: UUID, days: int = 30
) -> Dict[str, int]:
    """Count active penalties in the last N days by type."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(PenaltyRecord.penalty_type, func.count(PenaltyRecord.id))
        .where(
            PenaltyRecord.user_id == user_id,
            PenaltyRecord.status == "active",
            PenaltyRecord.created_at >= cutoff,
        )
        .group_by(PenaltyRecord.penalty_type)
    )
    counts: Dict[str, int] = {pt.value: 0 for pt in PenaltyType}
    for ptype, count in result.all():
        counts[ptype] = count
    return counts


async def _get_recent_completed_count(
    db: AsyncSession, user_id: UUID, role: str, days: int = 30
) -> int:
    """Count accepted applications in last N days (proxy for completed work)."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    if role == "instructor":
        # Get instructor profile
        profile_result = await db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        profile_id = profile_result.scalar_one_or_none()
        if not profile_id:
            return 0
        result = await db.execute(
            select(func.count(Application.id)).where(
                Application.instructor_id == profile_id,
                Application.status == ApplicationStatus.ACCEPTED,
                Application.created_at >= cutoff,
            )
        )
    else:
        # Center: count accepted applications on their job posts
        from app.models import JobPost
        result = await db.execute(
            select(func.count(Application.id))
            .join(JobPost, Application.job_post_id == JobPost.id)
            .join(StudioProfile, JobPost.studio_id == StudioProfile.id)
            .where(
                StudioProfile.user_id == user_id,
                Application.status == ApplicationStatus.ACCEPTED,
                Application.created_at >= cutoff,
            )
        )
    return result.scalar_one() or 0


# ---------------------------------------------------------------------------
# Tier evaluation
# ---------------------------------------------------------------------------

async def evaluate_teacher_tier(db: AsyncSession, user_id: UUID) -> TeacherTier:
    """Evaluate and return the teacher's tier based on current state."""
    # Fetch user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.role != "instructor":
        return TeacherTier.T1_BASIC

    # Fetch instructor profile
    profile_result = await db.execute(
        select(InstructorProfile).where(InstructorProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    # T1 check: phone_verified + profile basics
    if not user.phone_verified:
        return TeacherTier.T1_BASIC
    if not profile:
        return TeacherTier.T1_BASIC
    if not (profile.display_name and profile.available_regions and profile.categories):
        return TeacherTier.T1_BASIC

    # Recent stats
    penalty_counts = await _get_recent_penalty_counts(db, user_id)
    completed_30d = await _get_recent_completed_count(db, user_id, "instructor")

    # T3 check
    verified_cert_count = 0
    if profile.certifications:
        for cert in profile.certifications:
            if isinstance(cert, dict) and cert.get("is_verified"):
                verified_cert_count += 1

    t3_eligible = (
        user.identity_verified
        and verified_cert_count >= 1
        and completed_30d >= 5
        and penalty_counts.get("no_show", 0) == 0
        and penalty_counts.get("same_day_cancel", 0) == 0
        and penalty_counts.get("late", 0) <= 1
    )
    if t3_eligible:
        return TeacherTier.T3_PRO

    # T2 check
    t2_eligible = (
        user.identity_verified
        and verified_cert_count >= 1
        and completed_30d >= 2
        and penalty_counts.get("no_show", 0) == 0
    )
    if t2_eligible:
        return TeacherTier.T2_VERIFIED

    return TeacherTier.T1_BASIC


async def evaluate_center_tier(db: AsyncSession, user_id: UUID) -> CenterTier:
    """Evaluate and return the center's tier based on current state."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.role != "studio":
        return CenterTier.C1_BASIC

    profile_result = await db.execute(
        select(StudioProfile).where(StudioProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not user.phone_verified:
        return CenterTier.C1_BASIC
    if not profile:
        return CenterTier.C1_BASIC
    if not (profile.business_name and profile.address and profile.phone):
        return CenterTier.C1_BASIC

    # C2 check
    penalty_counts = await _get_recent_penalty_counts(db, user_id)
    completed_30d = await _get_recent_completed_count(db, user_id, "studio")

    c2_eligible = (
        user.business_verified
        and profile.location_proof_verified
        and completed_30d >= 2
        and penalty_counts.get("cancel_after_confirm", 0) <= 1
    )
    if c2_eligible:
        return CenterTier.C2_VERIFIED

    return CenterTier.C1_BASIC


async def evaluate_and_update_tier(db: AsyncSession, user_id: UUID) -> str:
    """Evaluate tier, update user.tier cache, and return the tier value."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return TeacherTier.T1_BASIC.value

    if user.role == "instructor":
        tier = await evaluate_teacher_tier(db, user_id)
    elif user.role == "studio":
        tier = await evaluate_center_tier(db, user_id)
    else:
        return user.tier or TeacherTier.T1_BASIC.value

    user.tier = tier.value
    user.tier_computed_at = datetime.utcnow()
    await db.commit()
    return tier.value


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

async def get_tier_display(db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
    """Get tier info formatted for the frontend card UI."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"tier": "t1_basic", "tier_label": "Basic", "tier_color": "gray"}

    tier = user.tier or (
        TeacherTier.T1_BASIC.value if user.role == "instructor" else CenterTier.C1_BASIC.value
    )
    limits = get_tier_limits(tier)

    # Recent stats
    penalty_counts = await _get_recent_penalty_counts(db, user.id)
    completed_30d = await _get_recent_completed_count(db, user.id, user.role)

    # Next tier requirements
    next_tier = None
    missing_requirements = []

    if user.role == "instructor":
        if tier == TeacherTier.T1_BASIC.value:
            next_tier = TeacherTier.T2_VERIFIED.value
            if not user.identity_verified:
                missing_requirements.append("본인인증 완료")
            # Check verified cert count
            profile_result = await db.execute(
                select(InstructorProfile).where(InstructorProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            verified_certs = 0
            if profile and profile.certifications:
                for c in profile.certifications:
                    if isinstance(c, dict) and c.get("is_verified"):
                        verified_certs += 1
            if verified_certs < 1:
                missing_requirements.append("인증된 자격증 1개 이상")
            if completed_30d < 2:
                missing_requirements.append(f"최근 30일 완료 2건 (현재 {completed_30d}건)")
            if penalty_counts.get("no_show", 0) > 0:
                missing_requirements.append("최근 30일 노쇼 0회")
        elif tier == TeacherTier.T2_VERIFIED.value:
            next_tier = TeacherTier.T3_PRO.value
            if completed_30d < 5:
                missing_requirements.append(f"최근 30일 완료 5건 (현재 {completed_30d}건)")
            if penalty_counts.get("same_day_cancel", 0) > 0:
                missing_requirements.append("최근 30일 당일취소 0회")
            if penalty_counts.get("late", 0) > 1:
                missing_requirements.append("최근 30일 지각 1회 이하")
    elif user.role == "studio":
        if tier == CenterTier.C1_BASIC.value:
            next_tier = CenterTier.C2_VERIFIED.value
            if not user.business_verified:
                missing_requirements.append("사업자 인증 완료")
            profile_result = await db.execute(
                select(StudioProfile).where(StudioProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            if profile and not profile.location_proof_verified:
                missing_requirements.append("위치 증빙 인증")
            if completed_30d < 2:
                missing_requirements.append(f"최근 30일 완료 2건 (현재 {completed_30d}건)")

    return {
        "tier": tier,
        "tier_label": limits.get("label", "Basic"),
        "tier_label_ko": limits.get("label_ko", "기본"),
        "tier_color": limits.get("color", "gray"),
        "role": user.role,
        "completed_jobs_recent": completed_30d,
        "no_show_recent": penalty_counts.get("no_show", 0),
        "same_day_cancel_recent": penalty_counts.get("same_day_cancel", 0),
        "late_recent": penalty_counts.get("late", 0),
        "cancel_after_confirm_recent": penalty_counts.get("cancel_after_confirm", 0),
        "next_tier": next_tier,
        "missing_requirements": missing_requirements,
    }


# ---------------------------------------------------------------------------
# Access checks
# ---------------------------------------------------------------------------

async def check_can_apply(db: AsyncSession, user_id: UUID) -> Tuple[bool, Optional[str]]:
    """Check if instructor can submit an application based on tier limits and suspension."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return False, "User not found"

    # Check suspension
    now = datetime.utcnow()
    if user.suspension_until and user.suspension_until > now:
        return False, f"계정이 정지 상태입니다. ({user.suspension_until.strftime('%Y-%m-%d')}까지)"

    tier = user.tier or TeacherTier.T1_BASIC.value
    limits = get_tier_limits(tier)
    daily_limit = limits.get("daily_applications", 3)

    if daily_limit == -1:
        return True, None  # Unlimited

    # Check today's usage
    from datetime import date as date_type
    today = date_type.today()
    if user.last_usage_reset_date != today:
        # Reset daily counter
        user.daily_applications_today = 0
        user.last_usage_reset_date = today
        await db.commit()

    if user.daily_applications_today >= daily_limit:
        return False, f"일일 지원 한도 초과 ({daily_limit}건). {limits['label_ko']} 등급 기준."

    return True, None


async def check_can_post(db: AsyncSession, user_id: UUID) -> Tuple[bool, Optional[str]]:
    """Check if center can create a new job post based on tier limits."""
    from app.models import JobPost, JobPostStatus

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return False, "User not found"

    now = datetime.utcnow()
    if user.suspension_until and user.suspension_until > now:
        return False, f"계정이 정지 상태입니다. ({user.suspension_until.strftime('%Y-%m-%d')}까지)"

    tier = user.tier or CenterTier.C1_BASIC.value
    limits = get_tier_limits(tier)
    max_active = limits.get("active_posts", 2)

    # Count currently active (open) posts
    profile_result = await db.execute(
        select(StudioProfile.id).where(StudioProfile.user_id == user_id)
    )
    studio_id = profile_result.scalar_one_or_none()
    if not studio_id:
        return False, "Studio profile not found"

    active_count_result = await db.execute(
        select(func.count(JobPost.id)).where(
            JobPost.studio_id == studio_id,
            JobPost.status == JobPostStatus.OPEN,
        )
    )
    active_count = active_count_result.scalar_one() or 0

    if active_count >= max_active:
        return False, f"활성 공고 한도 초과 ({max_active}건). {limits['label_ko']} 등급 기준."

    return True, None
