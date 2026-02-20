"""Escrow payment service.

Payment Flow:
1. Studio confirms contract → Makes payment → Funds held in ESCROW (status: HELD)
2. Contract IN_PROGRESS → Funds still held
3. Contract COMPLETED → Release funds to instructor (status: RELEASED)
4. Contract CANCELLED:
   - If no-show by instructor → Partial refund to studio, penalty from instructor deposit
   - If no-show by studio → Full refund from instructor, penalty from studio deposit
   - Normal cancel → Full refund to studio (status: REFUNDED)
"""
import base64
from decimal import Decimal

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Payment, Payout, Contract, User, PaymentStatus, PayoutStatus
from app.core.config import settings


PLATFORM_FEE_PERCENT = Decimal("0.05")  # 5% platform fee


async def release_escrow_to_instructor(
    db: AsyncSession,
    contract_id: str,
) -> dict:
    """
    Release escrowed funds to instructor when contract is completed.
    Creates a payout record for the instructor.
    """
    from uuid import UUID

    # Get payment
    result = await db.execute(
        select(Payment).where(Payment.contract_id == UUID(contract_id))
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise ValueError("Payment not found for this contract")

    if payment.escrow_status != "HELD":
        raise ValueError(f"Cannot release escrow. Current status: {payment.escrow_status}")

    # Get contract to find instructor
    result = await db.execute(
        select(Contract).where(Contract.id == UUID(contract_id))
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise ValueError("Contract not found")

    # Calculate payout (amount - platform fee)
    total_amount = Decimal(str(payment.amount))
    platform_fee = total_amount * PLATFORM_FEE_PERCENT
    instructor_amount = total_amount - platform_fee

    # Get instructor's user_id from profile
    from app.models import InstructorProfile
    result = await db.execute(
        select(InstructorProfile.user_id).where(InstructorProfile.id == contract.instructor_id)
    )
    instructor_user_id = result.scalar_one_or_none()

    if not instructor_user_id:
        raise ValueError("Instructor not found")

    # Check if payout already exists
    result = await db.execute(
        select(Payout).where(Payout.contract_id == UUID(contract_id))
    )
    existing_payout = result.scalar_one_or_none()

    if existing_payout:
        # Update existing payout
        existing_payout.status = PayoutStatus.COMPLETED.value
        existing_payout.amount = instructor_amount
        payout = existing_payout
    else:
        # Create new payout record
        payout = Payout(
            contract_id=contract.id,
            payee_user_id=instructor_user_id,
            amount=instructor_amount,
            status=PayoutStatus.COMPLETED.value,
        )
        db.add(payout)

    # Update payment escrow status
    payment.escrow_status = "RELEASED"
    payment.platform_fee = platform_fee

    await db.commit()

    return {
        "status": "released",
        "total_amount": float(total_amount),
        "platform_fee": float(platform_fee),
        "instructor_payout": float(instructor_amount),
    }


async def refund_escrow_to_studio(
    db: AsyncSession,
    contract_id: str,
    refund_percent: Decimal = Decimal("1.0"),  # 100% by default
    reason: str = None,
) -> dict:
    """
    Refund escrowed funds to studio when contract is cancelled.
    refund_percent: 1.0 = full refund, 0.7 = 70% refund (30% penalty), etc.
    """
    from uuid import UUID

    # Get payment
    result = await db.execute(
        select(Payment).where(Payment.contract_id == UUID(contract_id))
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise ValueError("Payment not found for this contract")

    if payment.escrow_status != "HELD":
        raise ValueError(f"Cannot refund escrow. Current status: {payment.escrow_status}")

    # Calculate refund
    total_amount = Decimal(str(payment.amount))
    refund_amount = total_amount * refund_percent
    penalty_amount = total_amount - refund_amount

    # Call TossPayments cancel API for actual refund
    pg_refund_result = await _call_toss_cancel(
        payment_key=payment.payment_key,
        cancel_amount=int(refund_amount),
        cancel_reason=reason or "Contract cancelled",
    )

    # Update payment
    payment.escrow_status = "REFUNDED"
    payment.status = PaymentStatus.REFUNDED.value
    if pg_refund_result:
        payment.pg_response = pg_refund_result

    await db.commit()

    return {
        "status": "refunded",
        "total_amount": float(total_amount),
        "refund_amount": float(refund_amount),
        "penalty_amount": float(penalty_amount),
        "reason": reason,
    }


async def get_escrow_status(db: AsyncSession, contract_id: str) -> dict:
    """Get escrow status for a contract."""
    from uuid import UUID

    result = await db.execute(
        select(Payment).where(Payment.contract_id == UUID(contract_id))
    )
    payment = result.scalar_one_or_none()

    if not payment:
        return {
            "has_payment": False,
            "escrow_status": None,
        }

    return {
        "has_payment": True,
        "payment_status": payment.status,
        "escrow_status": payment.escrow_status,
        "amount": float(payment.amount),
        "platform_fee": float(payment.platform_fee or 0),
    }


async def _call_toss_cancel(
    payment_key: str | None,
    cancel_amount: int,
    cancel_reason: str,
) -> dict | None:
    """Call TossPayments cancel API. Returns PG response or None in dev mode."""
    if not payment_key:
        return None

    if not settings.TOSS_SECRET_KEY:
        # Mock response for development
        return {
            "paymentKey": payment_key,
            "status": "CANCELED",
            "cancels": [{"cancelAmount": cancel_amount, "cancelReason": cancel_reason}],
        }

    secret_key = settings.TOSS_SECRET_KEY + ":"
    encoded_key = base64.b64encode(secret_key.encode()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.tosspayments.com/v1/payments/{payment_key}/cancel",
            headers={
                "Authorization": f"Basic {encoded_key}",
                "Content-Type": "application/json",
            },
            json={
                "cancelReason": cancel_reason,
                "cancelAmount": cancel_amount,
            },
        )

        if response.status_code != 200:
            error_data = response.json()
            raise ValueError(
                f"Toss refund failed: {error_data.get('message', 'Unknown error')}"
            )

        return response.json()
