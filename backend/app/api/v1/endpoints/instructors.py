from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.instructor import (
    InstructorProfileResponse,
    InstructorProfileUpdate,
    InstructorPublicResponse,
)
from app.services.instructor import InstructorService

router = APIRouter()


@router.get("/me", response_model=InstructorProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get current instructor's profile."""
    service = InstructorService(db)
    profile = await service.get_profile_by_user_id(current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    return InstructorProfileResponse.model_validate(profile)


@router.put("/me", response_model=InstructorProfileResponse)
async def update_my_profile(
    update_data: InstructorProfileUpdate,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Update current instructor's profile."""
    service = InstructorService(db)
    profile = await service.update_profile(current_user.id, update_data)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    return InstructorProfileResponse.model_validate(profile)


@router.get("/{instructor_id}", response_model=InstructorPublicResponse)
async def get_instructor(
    instructor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get instructor's public profile by ID."""
    service = InstructorService(db)
    profile = await service.get_profile_by_id(instructor_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    if not profile.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PROFILE_PRIVATE", "message": "This profile is private"},
        )

    return InstructorPublicResponse.model_validate(profile)
