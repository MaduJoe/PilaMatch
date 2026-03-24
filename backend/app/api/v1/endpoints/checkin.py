"""GPS check-in endpoints -- instructor arrival verification at studio."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.services.checkin import CheckinService

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class CheckinRequest(BaseModel):
    latitude: float
    longitude: float


class CheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_post_id: str
    distance_meters: float
    is_valid: bool
    checked_in_at: str


# --- Endpoints ---


@router.post("/jobs/{job_post_id}/checkin", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    job_post_id: UUID,
    body: CheckinRequest,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Instructor GPS check-in at studio location.

    Calculates Haversine distance between instructor GPS and studio GPS.
    Marks valid if within 200m.
    """
    service = CheckinService(db)

    try:
        record = await service.check_in(
            job_post_id=str(job_post_id),
            user_id=str(current_user.id),
            latitude=body.latitude,
            longitude=body.longitude,
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "JOB_POST_NOT_FOUND" or error_msg == "INSTRUCTOR_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": error_msg, "message": "Resource not found"},
            )
        if error_msg == "ALREADY_CHECKED_IN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_CHECKED_IN", "message": "Already checked in for this job"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHECKIN_FAILED", "message": error_msg},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to check in for this job"},
        )

    await db.commit()

    return CheckinResponse(
        id=str(record.id),
        job_post_id=str(record.job_post_id),
        distance_meters=float(record.distance_meters),
        is_valid=record.is_valid,
        checked_in_at=str(record.checked_in_at),
    )


@router.get("/jobs/{job_post_id}/checkin")
async def get_checkin_status(
    job_post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get check-in status for the current user on a specific job post."""
    service = CheckinService(db)
    return await service.get_checkin_status(
        job_post_id=str(job_post_id),
        user_id=str(current_user.id),
    )
