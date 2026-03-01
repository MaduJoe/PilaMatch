"""Trust Score calculation and management service (v3.0).

Trust Score is the primary trust signal replacing the deposit system.
Score ranges from 0-100 and affects user visibility and opportunities.
"""
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import and_

from app.models import (
    User, InstructorProfile, StudioProfile,
    Contract, ContractStatus, Review, Application,
    MembershipTier
)
from app.services.profile_completeness import (
    calculate_instructor_completeness,
    calculate_studio_completeness,
)

# Module-level constants for Trust Score factor metadata and level thresholds.
# Defined once here to avoid recreating on each call.

FACTOR_LABELS: Dict[str, Dict[str, Any]] = {
    "identity_verification": {"name": "본인인증", "max": 20},
    "profile_completeness": {"name": "프로필 완성도", "max": 15},
    "contract_history": {"name": "계약 이력", "max": 20},
    "review_average": {"name": "평균 평점", "max": 15},
    "response_rate": {"name": "활동 빈도", "max": 5},
    "certifications": {"name": "자격증/인증", "max": 15},
    "premium_membership": {"name": "프리미엄", "max": 10},
    "no_show_penalty": {"name": "노쇼 감점", "max": 0},
    "account_age": {"name": "가입 기간", "max": 5},
}

LEVEL_THRESHOLDS: list[Dict[str, Any]] = [
    {"level": "새싹", "min": 0, "max": 39, "color": "bronze"},
    {"level": "인증", "min": 40, "max": 59, "color": "silver"},
    {"level": "전문", "min": 60, "max": 79, "color": "gold"},
    {"level": "마스터", "min": 80, "max": 100, "color": "platinum"},
]


class TrustLevel:
    """Trust level thresholds and names."""
    BRONZE = (0, 39, "새싹")  # Beginner
    SILVER = (40, 59, "인증")  # Verified
    GOLD = (60, 79, "전문")  # Professional
    PLATINUM = (80, 100, "마스터")  # Master

    @classmethod
    def get_level(cls, score: int) -> Tuple[str, str]:
        """Get level name and badge color for a score."""
        if score < 40:
            return cls.BRONZE[2], "bronze"
        elif score < 60:
            return cls.SILVER[2], "silver"
        elif score < 80:
            return cls.GOLD[2], "gold"
        else:
            return cls.PLATINUM[2], "platinum"


async def calculate_trust_score(
    db: AsyncSession,
    user_id: str,
    user_role: str = None
) -> Dict[str, Any]:
    """Calculate comprehensive Trust Score for a user.

    Components:
    - Identity verification: 20 points
    - Profile completeness: 15 points
    - Contract history: 20 points
    - Review average: 15 points
    - Response rate: 5 points
    - Certifications: 15 points
    - Premium membership: 5 points
    - No-show penalties: -20 per incident
    - Account age bonus: 5 points

    Returns:
        Dict with score, level, breakdown, and recommendations
    """
    from uuid import UUID

    # Get user
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        return {
            "score": 0,
            "level": TrustLevel.BRONZE[2],
            "level_color": "bronze",
            "breakdown": {},
            "recommendations": ["User not found"]
        }

    breakdown = {}
    total_score = 0
    recommendations = []

    # 1. Identity Verification (20 points)
    identity_score = 0
    if user.phone_verified:
        identity_score += 10
    else:
        recommendations.append("본인인증을 완료하세요 (+10점)")

    if user.business_verified and user_role == "studio":
        identity_score += 10
    elif user_role == "studio":
        recommendations.append("사업자 인증을 완료하세요 (+10점)")
    elif user_role == "instructor":
        identity_score += 10  # Instructors get full points with phone verification

    breakdown["identity_verification"] = identity_score
    total_score += identity_score

    # 2. Profile Completeness (15 points)
    profile_score = 0
    if user_role or user.role:
        role = user_role or user.role
        if role == "instructor":
            result = await db.execute(
                select(InstructorProfile).where(
                    InstructorProfile.user_id == UUID(user_id)
                )
            )
            profile = result.scalar_one_or_none()
            if profile:
                completeness = await calculate_instructor_completeness(profile, user=user)
                profile_score = int((completeness["percentage"] / 100) * 15)
                if completeness["percentage"] < 100:
                    recommendations.append(f"프로필을 100% 완성하세요 (+{15 - profile_score}점)")
        else:  # studio
            result = await db.execute(
                select(StudioProfile).where(
                    StudioProfile.user_id == UUID(user_id)
                )
            )
            profile = result.scalar_one_or_none()
            if profile:
                completeness = await calculate_studio_completeness(profile, user=user)
                profile_score = int((completeness["percentage"] / 100) * 15)
                if completeness["percentage"] < 100:
                    recommendations.append(f"프로필을 100% 완성하세요 (+{15 - profile_score}점)")

    breakdown["profile_completeness"] = profile_score
    total_score += profile_score

    # 3. Contract History (20 points)
    contract_score = 0
    if user_role == "instructor" and profile:
        # Count completed contracts for instructor
        result = await db.execute(
            select(func.count(Contract.id)).where(
                and_(
                    Contract.instructor_id == profile.id,
                    Contract.status == ContractStatus.COMPLETED
                )
            )
        )
        completed_count = result.scalar() or 0
    elif user_role == "studio" and profile:
        # Count completed contracts for studio
        result = await db.execute(
            select(func.count(Contract.id)).where(
                and_(
                    Contract.studio_id == profile.id,
                    Contract.status == ContractStatus.COMPLETED
                )
            )
        )
        completed_count = result.scalar() or 0
    else:
        completed_count = 0

    # Progressive scoring: 0-1 contracts: 0pts, 2-5: 10pts, 6-10: 15pts, 11+: 20pts
    if completed_count >= 11:
        contract_score = 20
    elif completed_count >= 6:
        contract_score = 15
    elif completed_count >= 2:
        contract_score = 10
    elif completed_count >= 1:
        contract_score = 5

    if contract_score < 20:
        recommendations.append(f"더 많은 계약을 완료하세요 (현재 {completed_count}건)")

    breakdown["contract_history"] = contract_score
    total_score += contract_score

    # 4. Review Average (15 points)
    review_score = 0
    if profile:
        # Get average rating
        if hasattr(profile, 'rating_average') and profile.rating_average:
            avg_rating = float(profile.rating_average)
            # 5.0 = 15pts, 4.5 = 12pts, 4.0 = 9pts, 3.5 = 6pts, 3.0 = 3pts
            review_score = max(0, int((avg_rating - 2.0) * 5))
            if avg_rating < 4.5:
                recommendations.append(f"평점을 높이세요 (현재 {avg_rating:.1f}/5.0)")
        else:
            recommendations.append("첫 리뷰를 받으세요 (+15점)")

    breakdown["review_average"] = review_score
    total_score += review_score

    # 5. Response Rate (5 points)
    response_score = 0
    # TODO: Implement response rate tracking
    # For now, give full points if user has been active in last 7 days
    if user.last_active_at:
        days_since_login = (datetime.utcnow() - user.last_active_at).days
        if days_since_login <= 7:
            response_score = 5
        elif days_since_login <= 30:
            response_score = 3
        else:
            recommendations.append("더 자주 로그인하세요 (+5점)")

    breakdown["response_rate"] = response_score
    total_score += response_score

    # 6. Certifications (15 points for instructors)
    cert_score = 0
    if user_role == "instructor" and profile:
        if hasattr(profile, 'certifications') and profile.certifications:
            cert_count = len(profile.certifications)
            cert_score = min(15, cert_count * 5)  # 5 points per cert, max 15
            if cert_score < 15:
                recommendations.append(f"자격증을 더 추가하세요 (현재 {cert_count}개)")
    elif user_role == "studio":
        # Studios get points for business verification instead
        if user.business_verified:
            cert_score = 15

    breakdown["certifications"] = cert_score
    total_score += cert_score

    # 7. Premium Membership (10 points) - Enhanced benefit v3.0
    membership_score = 0
    if user.membership_tier == MembershipTier.PREMIUM.value:
        membership_score = 10  # Increased from 5 to 10 for premium
    else:
        recommendations.append("프리미엄 멤버십 가입 (+10점)")

    breakdown["premium_membership"] = membership_score
    total_score += membership_score

    # 8. No-show Penalties (-20 per incident)
    penalty_score = 0
    if user.no_show_count and user.no_show_count > 0:
        penalty_score = -20 * user.no_show_count
        recommendations.append(f"노쇼 기록이 있습니다 ({user.no_show_count}회, -{abs(penalty_score)}점)")

    breakdown["no_show_penalty"] = penalty_score
    total_score += penalty_score

    # 9. Account Age Bonus (5 points)
    age_score = 0
    if user.created_at:
        account_age_days = (datetime.utcnow() - user.created_at).days
        if account_age_days >= 180:  # 6 months
            age_score = 5
        elif account_age_days >= 90:  # 3 months
            age_score = 3
        elif account_age_days >= 30:  # 1 month
            age_score = 1

    breakdown["account_age"] = age_score
    total_score += age_score

    # Ensure score is within 0-100 range
    final_score = max(0, min(100, total_score))

    # Get level
    level_name, level_color = TrustLevel.get_level(final_score)

    # Sort recommendations by potential point gain
    recommendations = recommendations[:3]  # Top 3 recommendations

    return {
        "score": final_score,
        "level": level_name,
        "level_color": level_color,
        "breakdown": breakdown,
        "recommendations": recommendations,
        "next_level_score": 40 if final_score < 40 else (60 if final_score < 60 else (80 if final_score < 80 else 100)),
        "points_to_next_level": max(0, (40 if final_score < 40 else (60 if final_score < 60 else (80 if final_score < 80 else 100))) - final_score),
        "factor_labels": FACTOR_LABELS,
        "level_thresholds": LEVEL_THRESHOLDS,
    }


async def update_user_trust_score(
    db: AsyncSession,
    user_id: str,
    user_role: str = None
) -> int:
    """Update user's trust score in database.

    Returns:
        The new trust score
    """
    from uuid import UUID

    # Calculate current score
    trust_data = await calculate_trust_score(db, user_id, user_role)
    new_score = trust_data["score"]

    # Update user's trust_score field
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user:
        user.trust_score = new_score
        user.trust_level = trust_data["level"]
        await db.commit()

    return new_score


async def get_trust_score_display(
    db: AsyncSession,
    user_id: str,
    user_role: str = None
) -> Dict[str, Any]:
    """Get trust score formatted for display.

    Returns simplified version for UI display.
    """
    trust_data = await calculate_trust_score(db, user_id, user_role)

    return {
        "score": trust_data["score"],
        "level": trust_data["level"],
        "level_color": trust_data["level_color"],
        "display_text": f"{trust_data['level']} {trust_data['score']}점",
        "is_premium": trust_data["breakdown"].get("premium_membership", 0) > 0,
        "badge_emoji": "🥉" if trust_data["score"] < 40 else ("🥈" if trust_data["score"] < 60 else ("🥇" if trust_data["score"] < 80 else "🏆"))
    }