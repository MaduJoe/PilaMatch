"""Payment confirmation service — tracks off-platform payment between center and instructor.

Centers mark payments as sent, instructors confirm receipt.
Dispute tracking for non-payment.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal

from app.models import Application, ApplicationStatus
from app.models.payment_confirmation import PaymentConfirmation
from app.models.enums import PaymentConfirmationStatus

logger = logging.getLogger(__name__)


async def mark_paid(
    db: AsyncSession,
    application_id: UUID,
    center_user_id: UUID,
    amount: Decimal,
) -> PaymentConfirmation:
    """Center marks payment as sent for an accepted application."""
    # Verify application exists and is accepted
    app_result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = app_result.scalar_one_or_none()
    if not application:
        raise ValueError("Application not found")
    if application.status != ApplicationStatus.ACCEPTED:
        raise ValueError("Application must be accepted to mark payment")

    # Check for existing confirmation
    existing = await db.execute(
        select(PaymentConfirmation).where(
            PaymentConfirmation.application_id == application_id
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Payment confirmation already exists for this application")

    # Get instructor user_id from instructor profile
    from app.models import InstructorProfile
    inst_result = await db.execute(
        select(InstructorProfile.user_id).where(
            InstructorProfile.id == application.instructor_id
        )
    )
    instructor_user_id = inst_result.scalar_one_or_none()
    if not instructor_user_id:
        raise ValueError("Instructor not found")

    now = datetime.utcnow()
    confirmation = PaymentConfirmation(
        application_id=application_id,
        center_user_id=center_user_id,
        instructor_user_id=instructor_user_id,
        amount=amount,
        status=PaymentConfirmationStatus.PENDING.value,
        center_marked_paid_at=now,
    )
    db.add(confirmation)
    await db.commit()
    await db.refresh(confirmation)
    return confirmation


async def confirm_payment(
    db: AsyncSession,
    confirmation_id: UUID,
    instructor_user_id: UUID,
) -> PaymentConfirmation:
    """Instructor confirms they received payment."""
    result = await db.execute(
        select(PaymentConfirmation).where(PaymentConfirmation.id == confirmation_id)
    )
    confirmation = result.scalar_one_or_none()
    if not confirmation:
        raise ValueError("Payment confirmation not found")
    if confirmation.instructor_user_id != instructor_user_id:
        raise PermissionError("Not authorized to confirm this payment")
    if confirmation.status != PaymentConfirmationStatus.PENDING.value:
        raise ValueError(f"Cannot confirm payment with status '{confirmation.status}'")

    confirmation.status = PaymentConfirmationStatus.CONFIRMED.value
    confirmation.instructor_confirmed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(confirmation)
    return confirmation


async def dispute_payment(
    db: AsyncSession,
    confirmation_id: UUID,
    instructor_user_id: UUID,
    reason: str,
) -> PaymentConfirmation:
    """Instructor disputes non-payment."""
    result = await db.execute(
        select(PaymentConfirmation).where(PaymentConfirmation.id == confirmation_id)
    )
    confirmation = result.scalar_one_or_none()
    if not confirmation:
        raise ValueError("Payment confirmation not found")
    if confirmation.instructor_user_id != instructor_user_id:
        raise PermissionError("Not authorized to dispute this payment")
    if confirmation.status != PaymentConfirmationStatus.PENDING.value:
        raise ValueError(f"Cannot dispute payment with status '{confirmation.status}'")

    confirmation.status = PaymentConfirmationStatus.DISPUTED.value
    confirmation.dispute_reason = reason
    await db.commit()
    await db.refresh(confirmation)
    return confirmation


async def get_on_time_payment_rate(
    db: AsyncSession, center_user_id: UUID, days: int = 30
) -> float:
    """Calculate on-time payment rate for a center in the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(PaymentConfirmation.id)).where(
            PaymentConfirmation.center_user_id == center_user_id,
            PaymentConfirmation.created_at >= cutoff,
        )
    )
    total = total_result.scalar_one() or 0
    if total == 0:
        return 1.0  # No data = assume good

    confirmed_result = await db.execute(
        select(func.count(PaymentConfirmation.id)).where(
            PaymentConfirmation.center_user_id == center_user_id,
            PaymentConfirmation.status == PaymentConfirmationStatus.CONFIRMED.value,
            PaymentConfirmation.created_at >= cutoff,
        )
    )
    confirmed = confirmed_result.scalar_one() or 0

    return confirmed / total


async def get_by_user(
    db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20,
) -> List[PaymentConfirmation]:
    """Get payment confirmations involving a user (as center or instructor)."""
    result = await db.execute(
        select(PaymentConfirmation)
        .where(
            (PaymentConfirmation.center_user_id == user_id)
            | (PaymentConfirmation.instructor_user_id == user_id)
        )
        .order_by(PaymentConfirmation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
