"""Escrow payment service.

Payment Flow:
1. Studio confirms contract -> Makes payment -> Funds held in ESCROW (status: HELD)
2. Contract IN_PROGRESS -> Funds still held
3. Contract COMPLETED -> Release funds to instructor (status: RELEASED)
4. Contract CANCELLED:
   - If no-show by instructor -> Partial refund to studio, penalty from instructor deposit
   - If no-show by studio -> Full refund from instructor, penalty from studio deposit
   - Normal cancel -> Full refund to studio (status: REFUNDED)
"""
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Payment, Payout, Contract, PaymentStatus, PayoutStatus
from app.schemas.payment import PaymentCancelRequest
from app.services.payment import PaymentService


PLATFORM_FEE_PERCENT = Decimal("0.05")  # 5% platform fee


async def release_escrow_to_instructor(
    db: AsyncSession,
    contract_id: str,
) -> dict:
    """
    Release escrowed funds to instructor when contract is completed.
    Creates a payout record for the instructor.
    """
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
    requested_by_user_id: str = None,
) -> dict:
    """
    Refund escrowed funds to studio when contract is cancelled.
    Delegates to PaymentService.cancel_payment() for proper tracking.

    refund_percent: 1.0 = full refund, 0.7 = 70% refund (30% penalty), etc.
    """
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

    # Delegate to PaymentService.cancel_payment for proper tracking
    if refund_amount > 0:
        service = PaymentService(db)
        cancel_req = PaymentCancelRequest(
            cancel_amount=refund_amount,
            cancel_reason=reason or "Contract cancelled",
        )
        requester_id = UUID(requested_by_user_id) if requested_by_user_id else payment.payer_user_id
        await service.cancel_payment(
            payment_id=payment.id,
            cancel_request=cancel_req,
            requested_by_user_id=requester_id,
        )
    else:
        # Zero refund (100% penalty) - just update escrow status
        payment.escrow_status = "REFUNDED"
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
        "cancelled_amount": float(payment.cancelled_amount or 0),
        "balance_amount": float(payment.balance_amount or payment.amount),
    }
