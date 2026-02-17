"""Deposit (보증금) management service (v2.0)."""
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, MembershipTier

# Deposit amounts (v2.0 - Early bird program)
EARLY_BIRD_DEPOSIT = Decimal("30000")  # Early bird: 3만원
REGULAR_DEPOSIT = Decimal("50000")  # Regular: 5만원
NO_SHOW_PENALTY_AMOUNT = Decimal("30000")  # 노쇼 시 3만원 차감
EARLY_BIRD_END_DATE = datetime(2026, 5, 15)  # 3 months from launch


async def get_deposit_status(db: AsyncSession, user_id: str) -> dict:
    """Get user's deposit status (v2.1 with Premium membership)."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    balance = Decimal(str(user.deposit_balance or 0))

    # Premium users don't need deposit
    if user.membership_tier == MembershipTier.PREMIUM.value:
        return {
            "membership_tier": "premium",
            "balance": float(balance),
            "required": 0,
            "is_sufficient": True,
            "shortfall": 0,
            "is_early_bird_eligible": False,
            "has_ever_paid": user.deposit_first_paid_at is not None,
            "subscription_active": True,
        }

    # Free users need deposit - determine required amount based on early bird status
    now = datetime.utcnow()
    if user.is_early_bird or (not user.deposit_first_paid_at and now < EARLY_BIRD_END_DATE):
        required = EARLY_BIRD_DEPOSIT
        is_early_bird_eligible = True
    else:
        required = Decimal(str(user.deposit_required or REGULAR_DEPOSIT))
        is_early_bird_eligible = False

    return {
        "membership_tier": "free",
        "balance": float(balance),
        "required": float(required),
        "is_sufficient": balance >= required,
        "shortfall": float(max(Decimal("0"), required - balance)),
        "is_early_bird_eligible": is_early_bird_eligible,
        "has_ever_paid": user.deposit_first_paid_at is not None,
        "subscription_active": False,
    }


async def add_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    payment_key: str = None,
) -> dict:
    """Add deposit to user's account (v2.0 with early bird tracking)."""
    from uuid import UUID

    if amount <= 0:
        raise ValueError("Amount must be positive")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    old_balance = Decimal(str(user.deposit_balance or 0))
    new_balance = old_balance + amount
    user.deposit_balance = new_balance

    # Track first deposit and apply early bird if eligible
    now = datetime.utcnow()
    if not user.deposit_first_paid_at:
        user.deposit_first_paid_at = now
        if now < EARLY_BIRD_END_DATE:
            user.is_early_bird = True
            user.deposit_required = EARLY_BIRD_DEPOSIT
        else:
            user.deposit_required = REGULAR_DEPOSIT

    await db.commit()

    required = Decimal(str(user.deposit_required))

    return {
        "previous_balance": float(old_balance),
        "added": float(amount),
        "new_balance": float(new_balance),
        "is_sufficient": new_balance >= required,
        "is_early_bird": user.is_early_bird,
        "required_amount": float(required),
    }


async def deduct_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    reason: str,
) -> dict:
    """Deduct from user's deposit (for penalties)."""
    from uuid import UUID

    if amount <= 0:
        raise ValueError("Amount must be positive")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    old_balance = Decimal(str(user.deposit_balance or 0))
    new_balance = max(Decimal("0"), old_balance - amount)
    deducted = old_balance - new_balance
    user.deposit_balance = new_balance

    await db.commit()

    required = Decimal(str(user.deposit_required or REGULAR_DEPOSIT))

    return {
        "previous_balance": float(old_balance),
        "deducted": float(deducted),
        "new_balance": float(new_balance),
        "reason": reason,
        "is_sufficient": new_balance >= required,
    }


async def apply_no_show_penalty(db: AsyncSession, user_id: str) -> dict:
    """Apply no-show penalty to user's deposit."""
    return await deduct_deposit(
        db=db,
        user_id=user_id,
        amount=NO_SHOW_PENALTY_AMOUNT,
        reason="No-show penalty",
    )


async def check_deposit_sufficient(db: AsyncSession, user_id: str) -> bool:
    """Check if user has sufficient deposit to participate in contracts.

    v2.1: Premium users always have sufficient 'deposit' (no deposit required).
    """
    from uuid import UUID

    # Check membership tier first for performance
    result = await db.execute(
        select(User.membership_tier).where(User.id == UUID(user_id))
    )
    membership_tier = result.scalar_one_or_none()

    # Premium users don't need deposit
    if membership_tier == MembershipTier.PREMIUM.value:
        return True

    # Free users need deposit check
    status = await get_deposit_status(db, user_id)
    return status["is_sufficient"]


async def refund_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal = None,
) -> dict:
    """Refund deposit to user (when leaving platform, etc.)."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    balance = Decimal(str(user.deposit_balance or 0))
    refund_amount = min(balance, amount) if amount else balance

    user.deposit_balance = balance - refund_amount

    await db.commit()

    return {
        "refunded": float(refund_amount),
        "remaining_balance": float(user.deposit_balance),
    }
