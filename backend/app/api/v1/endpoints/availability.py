"""Instructor availability (standby pool) endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole
from app.services.instructor_availability import InstructorAvailabilityService

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class AvailabilityToggleRequest(BaseModel):
    is_available: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    categories: Optional[list[str]] = None
    max_distance_km: Optional[float] = None


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_available: bool
    available_until: Optional[str] = None  # ISO datetime string
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    categories: list[str] = []
    max_distance_km: float = 10.0


# --- Endpoints ---


@router.put("", response_model=AvailabilityResponse)
async def toggle_availability(
    data: AvailabilityToggleRequest,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Toggle instructor availability for dispatch matching.

    When toggling ON, GPS coordinates are required. The instructor enters
    the standby pool and becomes eligible for auto-dispatch matching.
    """
    service = InstructorAvailabilityService(db)

    try:
        record = await service.toggle_availability(
            user_id=str(current_user.id),
            is_available=data.is_available,
            latitude=data.latitude,
            longitude=data.longitude,
            categories=data.categories,
            max_distance_km=data.max_distance_km,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "INSTRUCTOR_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
            )
        if error_msg == "GPS_REQUIRED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "GPS_REQUIRED", "message": "GPS coordinates are required when toggling availability on"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "AVAILABILITY_FAILED", "message": error_msg},
        )
    except PermissionError as e:
        error_msg = str(e)
        if error_msg == "USER_SUSPENDED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "USER_SUSPENDED", "message": "Suspended users cannot toggle availability"},
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": error_msg},
        )

    await db.commit()

    return AvailabilityResponse(
        id=str(record.id),
        is_available=record.is_available,
        available_until=record.available_until.isoformat() if record.available_until else None,
        latitude=float(record.latitude) if record.latitude is not None else None,
        longitude=float(record.longitude) if record.longitude is not None else None,
        categories=record.categories or [],
        max_distance_km=float(record.max_distance_km) if record.max_distance_km is not None else 10.0,
    )


@router.get("/me", response_model=AvailabilityResponse)
async def get_my_availability(
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get the current instructor's active availability status."""
    service = InstructorAvailabilityService(db)
    record = await service.get_my_availability(user_id=str(current_user.id))

    if not record:
        return AvailabilityResponse(
            id="",
            is_available=False,
        )

    return AvailabilityResponse(
        id=str(record.id),
        is_available=record.is_available,
        available_until=record.available_until.isoformat() if record.available_until else None,
        latitude=float(record.latitude) if record.latitude is not None else None,
        longitude=float(record.longitude) if record.longitude is not None else None,
        categories=record.categories or [],
        max_distance_km=float(record.max_distance_km) if record.max_distance_km is not None else 10.0,
    )
