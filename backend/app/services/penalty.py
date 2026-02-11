"""No-show penalty service."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Contract, InstructorProfile, StudioProfile

NO_SHOW_LIMIT = 3  # Account suspended after this many no-shows


async def get_user_id_from_profile(db: AsyncSession, profile_id: str, profile_type: str = None) -> str:
    """Get user_id from a profile_id (instructor or studio)."""
    from uuid import UUID

    # Try instructor first
    result = await db.execute(
        select(InstructorProfile.user_id).where(InstructorProfile.id == UUID(profile_id))
    )
    user_id = result.scalar_one_or_none()

    if user_id:
        return str(user_id)

    # Try studio
    result = await db.execute(
        select(StudioProfile.user_id).where(StudioProfile.id == UUID(profile_id))
    )
    user_id = result.scalar_one_or_none()

    if user_id:
        return str(user_id)

    return None


async def report_no_show(
    db: AsyncSession,
    contract_id: str,
    reported_profile_id: str,
    reporter_user_id: str,
) -> dict:
    """
    Report a no-show for a contract.
    reported_profile_id can be either instructor_id or studio_id from the contract.

    Returns:
        dict with result status and penalty info
    """
    from uuid import UUID

    # Get user_id from profile_id
    reported_user_id = await get_user_id_from_profile(db, reported_profile_id)

    if not reported_user_id:
        raise ValueError("Profile not found")

    # Get the reported user
    result = await db.execute(
        select(User).where(User.id == UUID(reported_user_id))
    )
    reported_user = result.scalar_one_or_none()

    if not reported_user:
        raise ValueError("User not found")

    # Increment no-show count
    reported_user.no_show_count = (reported_user.no_show_count or 0) + 1

    # Check if should be suspended
    is_now_suspended = False
    if reported_user.no_show_count >= NO_SHOW_LIMIT:
        reported_user.is_suspended = True
        is_now_suspended = True

    # Deduct from deposit (보증금 차감)
    from app.services.deposit import apply_no_show_penalty
    deposit_result = await apply_no_show_penalty(db, reported_user_id)

    await db.commit()

    return {
        "no_show_count": reported_user.no_show_count,
        "is_suspended": is_now_suspended,
        "remaining_chances": max(0, NO_SHOW_LIMIT - reported_user.no_show_count),
        "deposit_deducted": deposit_result.get("deducted", 0),
        "deposit_remaining": deposit_result.get("new_balance", 0),
    }


async def check_user_suspended(db: AsyncSession, user_id: str) -> bool:
    """Check if a user is suspended."""
    from uuid import UUID

    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        return False

    return user.is_suspended


async def get_user_penalty_status(db: AsyncSession, user_id: str) -> dict:
    """Get user's penalty status."""
    from uuid import UUID

    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    return {
        "no_show_count": user.no_show_count or 0,
        "is_suspended": user.is_suspended,
        "remaining_chances": max(0, NO_SHOW_LIMIT - (user.no_show_count or 0)),
    }
