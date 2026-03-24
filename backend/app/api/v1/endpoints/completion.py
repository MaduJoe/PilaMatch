"""Completion confirmation endpoints -- mutual lesson completion verification."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.completion import CompletionService

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class CompletionConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    studio_confirmed: bool
    instructor_confirmed: bool
    is_complete: bool
    auto_completed: bool


class InstructorReliabilityResponse(BaseModel):
    dispatch_success_rate: float
    total_dispatches: int
    total_completions: int
    total_checkins: int
    avg_checkin_distance_m: Optional[float] = None


# --- Endpoints ---


@router.post("/jobs/{job_post_id}/complete", response_model=CompletionConfirmResponse)
async def confirm_completion(
    job_post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm lesson completion (either studio or instructor can call).

    Creates or updates a CompletionConfirmation record. When both parties
    confirm, the lesson is marked complete and instructor stats are updated.
    """
    service = CompletionService(db)

    try:
        record = await service.confirm_completion(
            job_post_id=str(job_post_id),
            user_id=str(current_user.id),
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "JOB_POST_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "JOB_POST_NOT_FOUND", "message": "Job post not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "COMPLETION_FAILED", "message": error_msg},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not a participant of this job"},
        )

    await db.commit()

    return CompletionConfirmResponse(
        studio_confirmed=record.studio_confirmed,
        instructor_confirmed=record.instructor_confirmed,
        is_complete=record.is_complete,
        auto_completed=record.auto_completed or False,
    )


@router.get("/jobs/{job_post_id}/completion")
async def get_completion_status(
    job_post_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get completion status for a job post."""
    service = CompletionService(db)
    return await service.get_completion_status(job_post_id=str(job_post_id))


@router.get("/instructors/{user_id}/reliability", response_model=InstructorReliabilityResponse)
async def get_instructor_reliability(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get instructor reliability stats (public-facing).

    Returns dispatch success rate, total dispatches, completions,
    check-ins, and average check-in distance.
    """
    service = CompletionService(db)

    try:
        stats = await service.get_instructor_stats(instructor_user_id=str(user_id))
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "INSTRUCTOR_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INSTRUCTOR_NOT_FOUND", "message": "Instructor not found"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "STATS_FAILED", "message": error_msg},
        )

    return InstructorReliabilityResponse(
        dispatch_success_rate=stats["dispatch_success_rate"],
        total_dispatches=stats["total_dispatches"],
        total_completions=stats["total_completions"],
        total_checkins=stats["total_checkins"],
        avg_checkin_distance_m=stats["avg_checkin_distance_m"],
    )
