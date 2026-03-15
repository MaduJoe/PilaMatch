"""Tier endpoints — replaces Trust Score API (v4.0)."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.tier import TierResponse, TierPublicResponse, TierRequirementsResponse
from app.services.tier_evaluation import (
    get_tier_display,
    evaluate_and_update_tier,
    TEACHER_TIER_LIMITS,
    CENTER_TIER_LIMITS,
)
from app.models.enums import TeacherTier, CenterTier

router = APIRouter()


@router.get("/tier/me", response_model=TierResponse)
async def get_my_tier(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's tier, badge, card data, and next tier requirements."""
    # Re-evaluate tier on every read to ensure it reflects current conditions
    await evaluate_and_update_tier(db, current_user.id)
    display = await get_tier_display(db, current_user.id)
    return TierResponse(**display)


@router.get("/tier/user/{user_id}", response_model=TierPublicResponse)
async def get_user_tier(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's public tier info."""
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    display = await get_tier_display(db, UUID(user_id))
    return TierPublicResponse(
        user_id=user_id,
        tier=display["tier"],
        tier_label=display["tier_label"],
        tier_color=display["tier_color"],
        role=display["role"],
        completed_jobs_recent=display["completed_jobs_recent"],
        no_show_recent=display["no_show_recent"],
    )


@router.get("/tier/requirements", response_model=TierRequirementsResponse)
async def get_tier_requirements(
    current_user: User = Depends(get_current_user),
):
    """Get full tier system description for onboarding/upgrade UI."""
    teacher_tiers = [
        {
            "tier": TeacherTier.T1_BASIC.value,
            "label": "Basic",
            "label_ko": "기본",
            "requirements": ["휴대폰 인증", "프로필 기본 정보 입력"],
            "limits": {"daily_applications": 3},
        },
        {
            "tier": TeacherTier.T2_VERIFIED.value,
            "label": "Verified",
            "label_ko": "인증",
            "requirements": [
                "T1 조건 충족",
                "본인인증 완료",
                "인증된 자격증 1개 이상",
                "최근 30일 완료 2건 이상",
                "최근 30일 노쇼 0회",
            ],
            "limits": {"daily_applications": 20},
        },
        {
            "tier": TeacherTier.T3_PRO.value,
            "label": "Premium",
            "label_ko": "프로",
            "requirements": [
                "T2 조건 충족",
                "최근 30일 완료 5건 이상",
                "최근 30일 노쇼 0회",
                "최근 30일 당일취소 0회",
                "최근 30일 지각 1회 이하",
            ],
            "limits": {"daily_applications": -1, "matching_boost": 1.3},
        },
    ]

    center_tiers = [
        {
            "tier": CenterTier.C1_BASIC.value,
            "label": "Basic",
            "label_ko": "기본",
            "requirements": ["휴대폰 인증", "센터 기본 정보 입력"],
            "limits": {"active_posts": 2},
        },
        {
            "tier": CenterTier.C2_VERIFIED.value,
            "label": "Verified",
            "label_ko": "인증",
            "requirements": [
                "C1 조건 충족",
                "사업자 인증 완료",
                "위치 증빙 인증",
                "최근 30일 완료 2건 이상",
                "최근 30일 확정후취소 1회 이하",
            ],
            "limits": {"active_posts": 10, "matching_boost": 1.15},
        },
    ]

    return TierRequirementsResponse(
        teacher_tiers=teacher_tiers,
        center_tiers=center_tiers,
    )
