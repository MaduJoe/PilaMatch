"""Deposit (보증금) management service (v3.0 - DEPRECATED).

This service is deprecated as of v3.0. Deposit system has been removed.
All functions return success/neutral values for backward compatibility.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, MembershipTier

# DEPRECATED - Kept for backward compatibility only
EARLY_BIRD_DEPOSIT = Decimal("0")
REGULAR_DEPOSIT = Decimal("0")
NO_SHOW_PENALTY_AMOUNT = Decimal("0")
EARLY_BIRD_END_DATE = datetime(2026, 5, 15)


async def get_deposit_status(db: AsyncSession, user_id: str) -> dict:
    """Get user's deposit status (v3.0 - DEPRECATED).

    Always returns sufficient deposit as deposit system is removed.
    """
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    # v3.0: All users have "sufficient" deposit (system removed)
    return {
        "membership_tier": user.membership_tier or "free",
        "balance": 0,
        "required": 0,
        "is_sufficient": True,  # Always sufficient
        "shortfall": 0,
        "is_early_bird_eligible": False,
        "has_ever_paid": False,
        "subscription_active": user.membership_tier == MembershipTier.PREMIUM.value,
    }


async def add_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    payment_key: str = None,
) -> dict:
    """Add deposit to user's account (v3.0 - DEPRECATED).

    This is a no-op as deposit system is removed.
    Returns success for backward compatibility.
    """
    # v3.0: No actual deposit processing
    return {
        "previous_balance": 0,
        "added": 0,
        "new_balance": 0,
        "is_sufficient": True,
        "is_early_bird": False,
        "required_amount": 0,
    }


async def deduct_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal,
    reason: str,
) -> dict:
    """Deduct from user's deposit (v3.0 - DEPRECATED).

    This is a no-op as deposit system is removed.
    Returns neutral values for backward compatibility.
    """
    # v3.0: No actual deposit deduction
    return {
        "previous_balance": 0,
        "deducted": 0,
        "new_balance": 0,
        "reason": reason,
        "is_sufficient": True,
    }


async def apply_no_show_penalty(db: AsyncSession, user_id: str) -> dict:
    """Apply no-show penalty (v3.0 - DEPRECATED).

    No-show penalties are now handled via Trust Score reduction,
    not financial penalties.
    """
    # v3.0: No financial penalty
    return {
        "previous_balance": 0,
        "deducted": 0,
        "new_balance": 0,
        "reason": "No-show penalty (deprecated)",
        "is_sufficient": True,
    }


async def check_deposit_sufficient(db: AsyncSession, user_id: str) -> bool:
    """Check if user has sufficient deposit to participate in contracts.

    v3.0: DEPRECATED - Always returns True as deposit system is removed.
    """
    # v3.0: No deposit required for any user
    return True


async def refund_deposit(
    db: AsyncSession,
    user_id: str,
    amount: Decimal = None,
) -> dict:
    """Refund deposit (v3.0 - DEPRECATED).

    This is a no-op as deposit system is removed.
    Returns neutral values for backward compatibility.
    """
    # v3.0: No deposit to refund
    return {
        "refunded": 0,
        "remaining_balance": 0,
    }
