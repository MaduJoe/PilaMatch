"""Profile completeness endpoints (v3.0)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.profile_completeness import (
    calculate_instructor_completeness,
    calculate_studio_completeness,
    check_profile_completeness_for_action,
)
from app.services.instructor import InstructorService
from app.services.studio import StudioService

router = APIRouter()


@router.get("/profile/completeness")
async def get_profile_completeness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile completeness percentage and missing fields."""
    if current_user.role == "instructor":
        service = InstructorService(db)
        profile = await service.get_profile_by_user_id(current_user.id)
        if not profile:
            return {
                "percentage": 0,
                "is_complete": False,
                "missing_fields": ["all"],
                "message": "프로필을 먼저 생성해주세요",
            }
        completeness = await calculate_instructor_completeness(profile, user=current_user)
    else:  # studio
        service = StudioService(db)
        profile = await service.get_profile_by_user_id(current_user.id)
        if not profile:
            return {
                "percentage": 0,
                "is_complete": False,
                "missing_fields": ["all"],
                "message": "프로필을 먼저 생성해주세요",
            }
        completeness = await calculate_studio_completeness(profile, user=current_user)

    # Add helpful message
    if completeness["percentage"] < 70:
        completeness["message"] = f"프로필을 70% 이상 완성해야 서비스를 이용할 수 있습니다. 현재: {completeness['percentage']}%"
    elif completeness["percentage"] < 90:
        completeness["message"] = f"프로필을 90% 이상 완성하면 우선 매칭 혜택을 받을 수 있습니다. 현재: {completeness['percentage']}%"
    else:
        completeness["message"] = "프로필이 완벽하게 완성되었습니다!"

    return completeness


@router.get("/profile/completeness/check/{action}")
async def check_completeness_for_action(
    action: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if user's profile is complete enough for a specific action.

    Actions: 'apply', 'post', 'offer'
    """
    if action not in ["apply", "post", "offer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ACTION", "message": "Invalid action type"},
        )

    result = await check_profile_completeness_for_action(
        db, str(current_user.id), action
    )
    return result