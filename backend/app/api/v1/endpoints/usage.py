"""Daily usage tracking endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.daily_usage import DailyUsageService

router = APIRouter()


@router.get("/limits")
async def get_usage_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's daily usage limits and status.

    Returns:
        - membership_tier: "free" or "premium"
        - applications: usage count and limit
        - profile_views: usage count and limit (studios only)
    """
    service = DailyUsageService(db)
    return await service.get_usage_status(current_user.id)