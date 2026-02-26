"""Trust Score endpoints (v3.0)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.trust_score import (
    calculate_trust_score,
    update_user_trust_score,
    get_trust_score_display
)

router = APIRouter()

# Rate limit tracking: user_id -> last refresh timestamp
_trust_refresh_timestamps: dict[str, datetime] = {}
_TRUST_REFRESH_INTERVAL = timedelta(hours=1)


@router.get("/trust-score")
async def get_my_trust_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's detailed Trust Score with breakdown."""
    trust_data = await calculate_trust_score(
        db, str(current_user.id), current_user.role
    )
    return trust_data


@router.get("/trust-score/display")
async def get_my_trust_display(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get simplified Trust Score for UI display."""
    display_data = await get_trust_score_display(
        db, str(current_user.id), current_user.role
    )
    return display_data


@router.post("/trust-score/refresh")
async def refresh_my_trust_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recalculate and update user's Trust Score.

    This is called automatically on certain actions but can be
    manually triggered once per hour. Returns cached value if called
    within the 1-hour cooldown.
    """
    user_id = str(current_user.id)
    now = datetime.utcnow()

    # Check rate limit: 1 refresh per hour
    last_refresh = _trust_refresh_timestamps.get(user_id)
    if last_refresh and (now - last_refresh) < _TRUST_REFRESH_INTERVAL:
        # Return cached display data without recalculating
        display_data = await get_trust_score_display(
            db, user_id, current_user.role
        )
        remaining = int((_TRUST_REFRESH_INTERVAL - (now - last_refresh)).total_seconds())
        return {
            "message": "Trust Score was recently updated. Showing cached value.",
            "new_score": current_user.trust_score,
            "rate_limited": True,
            "retry_after_seconds": remaining,
            **display_data
        }

    new_score = await update_user_trust_score(
        db, user_id, current_user.role
    )

    # Update rate limit timestamp
    _trust_refresh_timestamps[user_id] = now

    # Get updated display data
    display_data = await get_trust_score_display(
        db, user_id, current_user.role
    )

    return {
        "message": "Trust Score updated",
        "new_score": new_score,
        "rate_limited": False,
        **display_data
    }


@router.get("/trust-score/user/{user_id}")
async def get_user_trust_display(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get another user's public Trust Score display.

    This is used to show trust scores on profile cards.
    Only shows simplified public information.
    """
    from uuid import UUID
    from sqlalchemy import select

    # Get target user
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"}
        )

    # Return simplified public display
    display_data = await get_trust_score_display(
        db, user_id, target_user.role
    )

    # Remove sensitive information for other users
    public_data = {
        "user_id": user_id,
        "score": display_data["score"],
        "level": display_data["level"],
        "level_color": display_data["level_color"],
        "display_text": display_data["display_text"],
        "badge_emoji": display_data["badge_emoji"],
        "is_premium": display_data["is_premium"]
    }

    return public_data