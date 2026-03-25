"""Auto-dispatch endpoints -- cascading dispatch accept/decline and status."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_role
from app.models import (
    User, UserRole, DispatchRecord, DispatchStatus, JobPost, StudioProfile,
)
from app.services.dispatch_engine import DispatchEngine

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Schemas ---


class DispatchRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_post_id: str
    instructor_id: str
    wave_number: int
    status: str
    dispatched_at: str
    responded_at: Optional[str] = None
    distance_km: Optional[float] = None
    reliability_score: Optional[int] = None


class ContactRevealResponse(BaseModel):
    application_id: str
    instructor_phone: Optional[str] = None
    instructor_name: Optional[str] = None
    studio_phone: Optional[str] = None
    studio_name: Optional[str] = None
    studio_address: Optional[str] = None


class DispatchStatusResponse(BaseModel):
    job_post_id: str
    dispatch_mode: str
    current_wave: int
    records: list[DispatchRecordResponse] = []
    matched: bool = False


# --- Helpers ---


def _record_to_response(record: DispatchRecord) -> DispatchRecordResponse:
    """Convert a DispatchRecord ORM model to a response schema."""
    return DispatchRecordResponse(
        id=str(record.id),
        job_post_id=str(record.job_post_id),
        instructor_id=str(record.instructor_id),
        wave_number=record.wave_number,
        status=record.status,
        dispatched_at=record.dispatched_at.isoformat() if record.dispatched_at else "",
        responded_at=record.responded_at.isoformat() if record.responded_at else None,
        distance_km=float(record.distance_km) if record.distance_km is not None else None,
        reliability_score=record.reliability_score,
    )


# --- Endpoints ---


class AcceptPendingResponse(BaseModel):
    status: str
    message: str
    dispatch_record_id: str
    job_post_id: str
    wave_number: int
    remaining_seconds: int


@router.post("/{dispatch_record_id}/accept", response_model=AcceptPendingResponse)
async def accept_dispatch(
    dispatch_record_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Accept a dispatch — time-window model.

    Records the instructor's acceptance intent. The actual confirmation
    happens when the wave window closes (via scheduler), which picks the
    best candidate by Reliability Score.
    """
    engine = DispatchEngine(db)

    try:
        result = await engine.accept_dispatch(
            dispatch_record_id=str(dispatch_record_id),
            user_id=str(current_user.id),
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "DISPATCH_RECORD_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "DISPATCH_RECORD_NOT_FOUND", "message": "Dispatch record not found"},
            )
        if error_msg == "ALREADY_RESPONDED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_RESPONDED", "message": "Already responded to this dispatch"},
            )
        if error_msg == "ALREADY_MATCHED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_MATCHED", "message": "이미 다른 강사가 배정되었습니다"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ACCEPT_FAILED", "message": error_msg},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to accept this dispatch"},
        )

    await db.commit()

    return AcceptPendingResponse(**result)


@router.post("/{dispatch_record_id}/decline")
async def decline_dispatch(
    dispatch_record_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Decline a dispatch. May trigger the next wave if all current wave records are terminal."""
    engine = DispatchEngine(db)

    try:
        await engine.decline_dispatch(
            dispatch_record_id=str(dispatch_record_id),
            user_id=str(current_user.id),
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "DISPATCH_RECORD_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "DISPATCH_RECORD_NOT_FOUND", "message": "Dispatch record not found"},
            )
        if error_msg == "ALREADY_RESPONDED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "ALREADY_RESPONDED", "message": "Already responded to this dispatch"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DECLINE_FAILED", "message": error_msg},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to decline this dispatch"},
        )

    await db.commit()

    return {"status": "declined"}


@router.get("/my-pending", response_model=list[DispatchRecordResponse])
async def get_my_pending_dispatches(
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Get current instructor's pending (dispatched) dispatch records."""
    result = await db.execute(
        select(DispatchRecord).where(
            and_(
                DispatchRecord.user_id == current_user.id,
                DispatchRecord.status == DispatchStatus.DISPATCHED.value,
            )
        ).order_by(DispatchRecord.dispatched_at.desc())
    )
    records = result.scalars().all()

    return [_record_to_response(record) for record in records]


@router.get("/job/{job_post_id}/status", response_model=DispatchStatusResponse)
async def get_dispatch_status(
    job_post_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Get dispatch status for a job post (studio owner only).

    Returns the current dispatch wave, all dispatch records, and whether
    the job has been matched.
    """
    # Verify the job post belongs to this studio
    studio_result = await db.execute(
        select(StudioProfile.id).where(StudioProfile.user_id == current_user.id)
    )
    studio_id = studio_result.scalar_one_or_none()
    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    job_result = await db.execute(
        select(JobPost).where(
            and_(
                JobPost.id == job_post_id,
                JobPost.studio_id == studio_id,
            )
        )
    )
    job_post = job_result.scalar_one_or_none()
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POST_NOT_FOUND", "message": "Job post not found or not owned by this studio"},
        )

    # Query all dispatch records for this job
    records_result = await db.execute(
        select(DispatchRecord)
        .where(DispatchRecord.job_post_id == job_post_id)
        .order_by(DispatchRecord.wave_number, DispatchRecord.dispatched_at)
    )
    records = records_result.scalars().all()

    # matched = job is FILLED (window finalized), not just "someone accepted"
    matched = job_post.status == "filled"

    return DispatchStatusResponse(
        job_post_id=str(job_post_id),
        dispatch_mode=job_post.dispatch_mode or "manual",
        current_wave=job_post.dispatch_wave or 0,
        records=[_record_to_response(r) for r in records],
        matched=matched,
    )
