from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.studio import (
    StudioProfileResponse,
    StudioProfileUpdate,
    StudioPublicResponse,
)
from app.services.studio import StudioService

router = APIRouter()


@router.get("/me", response_model=StudioProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Get current studio's profile with completed contracts count."""
    service = StudioService(db)
    profile = await service.get_profile_by_user_id(current_user.id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    completed_count = await service.get_completed_contracts_count(profile.id)
    response = StudioProfileResponse.model_validate(profile)
    response.completed_contracts_count = completed_count
    return response


@router.put("/me", response_model=StudioProfileResponse)
async def update_my_profile(
    update_data: StudioProfileUpdate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Update current studio's profile."""
    service = StudioService(db)
    profile = await service.update_profile(current_user.id, update_data)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    completed_count = await service.get_completed_contracts_count(profile.id)
    response = StudioProfileResponse.model_validate(profile)
    response.completed_contracts_count = completed_count
    return response


@router.get("/{studio_id}", response_model=StudioPublicResponse)
async def get_studio(
    studio_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get studio's public profile by ID."""
    service = StudioService(db)
    profile = await service.get_profile_by_id(studio_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    completed_count = await service.get_completed_contracts_count(profile.id)
    response = StudioPublicResponse.model_validate(profile)
    response.completed_contracts_count = completed_count
    return response
