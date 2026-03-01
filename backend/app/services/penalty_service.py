"""Penalty service — records penalties and applies tier consequences.

Replaces the inline penalty logic from dispute.py with structured penalty
records and tier-based consequences.
"""
import logging
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import User, PenaltyRecord
from app.models.enums import PenaltyType, PenaltyStatus, TeacherTier, CenterTier

logger = logging.getLogger(__name__)


async def _create_record(
    db: AsyncSession,
    user_id: UUID,
    penalty_type: PenaltyType,
    reported_by: Optional[UUID],
    suspend_until: Optional[datetime] = None,
    restrict_until: Optional[datetime] = None,
    description: Optional[str] = None,
    evidence: Optional[dict] = None,
) -> PenaltyRecord:
    record = PenaltyRecord(
        user_id=user_id,
        penalty_type=penalty_type.value,
        status=PenaltyStatus.ACTIVE.value,
        reported_by=reported_by,
        suspend_until=suspend_until,
        restrict_until=restrict_until,
        description=description,
        evidence_snapshot=evidence,
    )
    db.add(record)
    return record


async def record_no_show(
    db: AsyncSession, user_id: UUID, reported_by: UUID
) -> PenaltyRecord:
    """Record a no-show penalty: 14-day suspension + T1 demotion."""
    now = datetime.utcnow()
    suspend_end = now + timedelta(days=14)

    record = await _create_record(
        db, user_id, PenaltyType.NO_SHOW, reported_by,
        suspend_until=suspend_end,
        description="노쇼 신고 — 14일 정지 + T1 강등",
    )

    # Apply to user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.no_show_count = (user.no_show_count or 0) + 1
        user.suspension_until = suspend_end
        # Demote to T1/C1
        if user.role == "instructor":
            user.tier = TeacherTier.T1_BASIC.value
        elif user.role == "studio":
            user.tier = CenterTier.C1_BASIC.value
        user.tier_computed_at = now

        # 3-strike suspension
        if user.no_show_count >= 3:
            user.is_suspended = True

    # Event log (best-effort)
    try:
        from app.services.event_log import EventLogService
        event_service = EventLogService(db)
        await event_service.log(
            event_type="penalty.no_show",
            actor_user_id=str(reported_by),
            target_type="user",
            target_id=str(user_id),
            data={
                "suspend_until": suspend_end.isoformat(),
                "no_show_count": user.no_show_count if user else None,
            },
        )
    except Exception:
        logger.exception("Failed to log no-show penalty event")

    await db.commit()
    await db.refresh(record)
    return record


async def record_same_day_cancel(
    db: AsyncSession, user_id: UUID, reported_by: UUID
) -> PenaltyRecord:
    """Record a same-day cancellation: 7-day restriction from today-class postings."""
    now = datetime.utcnow()
    restrict_end = now + timedelta(days=7)

    record = await _create_record(
        db, user_id, PenaltyType.SAME_DAY_CANCEL, reported_by,
        restrict_until=restrict_end,
        description="당일 취소 — 7일 당일급구 제한",
    )

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.restriction_until = restrict_end

    await db.commit()
    await db.refresh(record)
    return record


async def record_late(
    db: AsyncSession, user_id: UUID, reported_by: UUID
) -> PenaltyRecord:
    """Record a lateness report. Affects T3 Pro maintenance condition."""
    record = await _create_record(
        db, user_id, PenaltyType.LATE, reported_by,
        description="지각 신고 — Pro 유지 조건 영향",
    )
    await db.commit()
    await db.refresh(record)
    return record


async def record_cancel_after_confirm(
    db: AsyncSession, center_user_id: UUID, reported_by: UUID
) -> PenaltyRecord:
    """Record a center cancelling after confirmation. Affects C2 status."""
    record = await _create_record(
        db, center_user_id, PenaltyType.CANCEL_AFTER_CONFIRM, reported_by,
        description="확정 후 취소 — C2 유지 조건 영향",
    )
    await db.commit()
    await db.refresh(record)
    return record


async def get_recent_penalty_counts(
    db: AsyncSession, user_id: UUID, days: int = 30
) -> Dict[str, int]:
    """Get penalty counts in the last N days by type."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(PenaltyRecord.penalty_type, func.count(PenaltyRecord.id))
        .where(
            PenaltyRecord.user_id == user_id,
            PenaltyRecord.status == PenaltyStatus.ACTIVE.value,
            PenaltyRecord.created_at >= cutoff,
        )
        .group_by(PenaltyRecord.penalty_type)
    )
    counts = {pt.value: 0 for pt in PenaltyType}
    for ptype, count in result.all():
        counts[ptype] = count
    return counts


async def is_suspended(db: AsyncSession, user_id: UUID) -> bool:
    """Check if user is currently suspended."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return False
    if user.is_suspended:
        return True
    now = datetime.utcnow()
    return bool(user.suspension_until and user.suspension_until > now)


async def is_restricted_from_today_class(db: AsyncSession, user_id: UUID) -> bool:
    """Check if user is restricted from urgent/today-class postings."""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return False
    now = datetime.utcnow()
    return bool(user.restriction_until and user.restriction_until > now)
