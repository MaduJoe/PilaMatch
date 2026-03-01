"""Profile completeness calculation service (v3.0).

This service calculates profile completeness percentage and
enforces completeness requirements for certain actions.
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, InstructorProfile, StudioProfile


async def calculate_instructor_completeness(
    profile: InstructorProfile, user: Optional[User] = None
) -> Dict[str, Any]:
    """Calculate instructor profile completeness.

    Returns:
        dict with completeness percentage and missing fields
    """
    required_fields = {
        "display_name": 25,  # 25% weight
        "phone": 15,
        "bio": 15,
        "experience_years": 10,
        "categories": 15,
        "available_regions": 20,
    }

    total_weight = sum(required_fields.values())
    completed_weight = 0
    missing_fields = []

    # Check each field
    if profile.display_name and len(profile.display_name) > 0:
        completed_weight += required_fields["display_name"]
    else:
        missing_fields.append("display_name")

    phone_ok = (profile.phone and len(profile.phone) > 0) or (user and user.phone_verified)
    if phone_ok:
        completed_weight += required_fields["phone"]
    else:
        missing_fields.append("phone")

    if profile.bio and len(profile.bio) >= 20:  # Minimum 20 chars for bio
        completed_weight += required_fields["bio"]
    else:
        missing_fields.append("bio")

    if profile.experience_years is not None and profile.experience_years >= 0:
        completed_weight += required_fields["experience_years"]
    else:
        missing_fields.append("experience_years")

    if profile.categories and len(profile.categories) > 0:
        completed_weight += required_fields["categories"]
    else:
        missing_fields.append("categories")

    if profile.available_regions and len(profile.available_regions) > 0:
        completed_weight += required_fields["available_regions"]
    else:
        missing_fields.append("available_regions")

    completeness_percentage = int((completed_weight / total_weight) * 100)

    return {
        "percentage": completeness_percentage,
        "is_complete": completeness_percentage >= 70,  # 70% threshold
        "missing_fields": missing_fields,
        "missing_fields_display": {
            "display_name": "이름",
            "phone": "전화번호",
            "bio": "자기소개",
            "experience_years": "경력",
            "categories": "수업 종목",
            "available_regions": "활동 지역",
        },
    }


async def calculate_studio_completeness(
    profile: StudioProfile, user: Optional[User] = None
) -> Dict[str, Any]:
    """Calculate studio profile completeness.

    Returns:
        dict with completeness percentage and missing fields
    """
    required_fields = {
        "business_name": 25,  # 25% weight
        "phone": 10,
        "description": 20,
        "address": 15,
        "region": 15,
        "categories": 15,
    }

    total_weight = sum(required_fields.values())
    completed_weight = 0
    missing_fields = []

    # Check each field
    if profile.business_name and len(profile.business_name) > 0:
        completed_weight += required_fields["business_name"]
    else:
        missing_fields.append("business_name")

    phone_ok = (profile.phone and len(profile.phone) > 0) or (user and user.phone_verified)
    if phone_ok:
        completed_weight += required_fields["phone"]
    else:
        missing_fields.append("phone")

    if profile.description and len(profile.description) >= 20:
        completed_weight += required_fields["description"]
    else:
        missing_fields.append("description")

    if profile.address and len(profile.address) > 0:
        completed_weight += required_fields["address"]
    else:
        missing_fields.append("address")

    if profile.region and len(profile.region) > 0:
        completed_weight += required_fields["region"]
    else:
        missing_fields.append("region")

    if profile.categories and len(profile.categories) > 0:
        completed_weight += required_fields["categories"]
    else:
        missing_fields.append("categories")

    completeness_percentage = int((completed_weight / total_weight) * 100)

    return {
        "percentage": completeness_percentage,
        "is_complete": completeness_percentage >= 70,  # 70% threshold
        "missing_fields": missing_fields,
        "missing_fields_display": {
            "business_name": "스튜디오명",
            "phone": "전화번호",
            "description": "소개",
            "address": "주소",
            "region": "지역",
            "categories": "운영 종목",
        },
    }


async def check_profile_completeness_for_action(
    db: AsyncSession, user_id: str, action: str = "apply"
) -> Dict[str, Any]:
    """Check if user's profile is complete enough for an action.

    Args:
        db: Database session
        user_id: User ID
        action: Action type ('apply', 'post', 'offer')

    Returns:
        dict with allowed status and completeness info
    """
    from uuid import UUID

    # Get user to determine role
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        return {
            "allowed": False,
            "reason": "User not found",
            "percentage": 0,
        }

    # Check based on role
    if user.role == "instructor":
        # Get instructor profile
        result = await db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == UUID(user_id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return {
                "allowed": False,
                "reason": "프로필을 먼저 생성해주세요",
                "percentage": 0,
            }

        completeness = await calculate_instructor_completeness(profile, user=user)
    else:  # studio
        # Get studio profile
        result = await db.execute(
            select(StudioProfile).where(StudioProfile.user_id == UUID(user_id))
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return {
                "allowed": False,
                "reason": "프로필을 먼저 생성해주세요",
                "percentage": 0,
            }

        completeness = await calculate_studio_completeness(profile, user=user)

    # Check threshold based on action
    thresholds = {
        "apply": 70,  # 70% to apply for jobs
        "post": 70,  # 70% to post jobs
        "offer": 90,  # 90% to receive priority offers
    }

    required_percentage = thresholds.get(action, 70)
    is_allowed = completeness["percentage"] >= required_percentage

    if not is_allowed:
        missing_display = completeness["missing_fields_display"]
        missing_names = [
            missing_display.get(field, field) for field in completeness["missing_fields"]
        ]
        reason = f"프로필을 {required_percentage}% 이상 완성해주세요. 미완성 항목: {', '.join(missing_names[:3])}"
    else:
        reason = None

    return {
        "allowed": is_allowed,
        "reason": reason,
        "percentage": completeness["percentage"],
        "missing_fields": completeness.get("missing_fields", []),
        "required_percentage": required_percentage,
    }