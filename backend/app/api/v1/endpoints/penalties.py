"""Penalty reporting endpoints (v4.0)."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole, PenaltyRecord
from app.models.enums import PenaltyType
from app.schemas.penalty import (
    PenaltyReportRequest,
    PenaltyRecordResponse,
    PenaltyListResponse,
)
from app.services import penalty_service

router = APIRouter()

_PENALTY_HANDLERS = {
    PenaltyType.NO_SHOW.value: penalty_service.record_no_show,
    PenaltyType.SAME_DAY_CANCEL.value: penalty_service.record_same_day_cancel,
    PenaltyType.LATE.value: penalty_service.record_late,
    PenaltyType.CANCEL_AFTER_CONFIRM.value: penalty_service.record_cancel_after_confirm,
}


@router.post("/penalties/report", response_model=PenaltyRecordResponse, status_code=status.HTTP_201_CREATED)
async def report_penalty(
    data: PenaltyReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a penalty (no-show, same-day cancel, late, cancel-after-confirm)."""
    handler = _PENALTY_HANDLERS.get(data.penalty_type)
    if not handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PENALTY_TYPE",
                "message": f"Invalid penalty type: {data.penalty_type}. "
                           f"Valid types: {', '.join(_PENALTY_HANDLERS.keys())}",
            },
        )

    try:
        record = await handler(
            db,
            user_id=UUID(data.reported_user_id),
            reported_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PENALTY_REPORT_FAILED", "message": str(e)},
        )

    # Re-evaluate reported user's tier
    try:
        from app.services.tier_evaluation import evaluate_and_update_tier
        await evaluate_and_update_tier(db, UUID(data.reported_user_id))
    except Exception:
        pass  # tier re-eval failure should not block the penalty

    return PenaltyRecordResponse.model_validate(record)


@router.get("/penalties/me", response_model=PenaltyListResponse)
async def get_my_penalties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's penalty history."""
    count_result = await db.execute(
        select(func.count(PenaltyRecord.id)).where(
            PenaltyRecord.user_id == current_user.id
        )
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(PenaltyRecord)
        .where(PenaltyRecord.user_id == current_user.id)
        .order_by(PenaltyRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    records = result.scalars().all()

    return PenaltyListResponse(
        items=[PenaltyRecordResponse.model_validate(r) for r in records],
        total=total,
    )
