"""Deposit (보증금) management service."""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User

# Default deposit amounts
DEFAULT_DEPOSIT_AMOUNT = Decimal("50000")  # 5만원
NO_SHOW_PENALTY_AMOUNT = Decimal("30000")  # 노쇼 시 3만원 차감


async def get_deposit_status(db: AsyncSession, user_id: str) -> dict:
    """Get user's deposit status."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    balance = Decimal(str(user.deposit_balance or 0))
    required = Decimal(str(user.deposit_required or DEFAULT_DEPOSIT_AMOUNT))

    return {
        "balance": float(balance),
        "required": float(required),
        "is_sufficient": balance >= required,
        "shortfall": float(max(Decimal("0"), required - balance)),
    }


async def add_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    payment_key: str = None,
) -> dict:
    """Add deposit to user's account."""
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

    await db.commit()

    required = Decimal(str(user.deposit_required or DEFAULT_DEPOSIT_AMOUNT))

    return {
        "previous_balance": float(old_balance),
        "added": float(amount),
        "new_balance": float(new_balance),
        "is_sufficient": new_balance >= required,
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

    required = Decimal(str(user.deposit_required or DEFAULT_DEPOSIT_AMOUNT))

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
    """Check if user has sufficient deposit to participate in contracts."""
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
