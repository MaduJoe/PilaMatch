"""Daily usage tracking service for premium features."""
from typing import Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import User, DailyUsageLimit
from app.models.daily_usage import DailyUsageLimit


class DailyUsageService:
    """Service for tracking and enforcing daily usage limits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_and_increment_usage(
        self,
        user_id: UUID,
        usage_type: str
    ) -> Dict[str, Any]:
        """
        Check if user can perform action and increment if allowed.

        Returns:
            Dict with 'allowed' (bool), 'count' (int), 'limit' (int/None), 'message' (str)
        """
        # Get user to check membership tier
        user = await self.db.get(User, user_id)
        if not user:
            return {
                "allowed": False,
                "count": 0,
                "limit": 0,
                "message": "사용자를 찾을 수 없습니다."
            }

        # Premium users have no limits
        if user.membership_tier == "premium":
            # Still track usage for analytics but don't enforce limits
            await self._track_usage(user_id, usage_type, limit=None)
            return {
                "allowed": True,
                "count": 0,  # Not relevant for premium
                "limit": None,
                "message": "프리미엄 회원 - 무제한"
            }

        # Get or create today's usage record for free users
        today = date.today()

        # Reset daily counters if it's a new day
        if user.last_usage_reset_date != today:
            user.daily_applications_today = 0
            user.daily_views_today = 0
            user.last_usage_reset_date = today
            user.last_viewed_profiles = []

        # Check current usage based on type
        if usage_type == DailyUsageLimit.UsageType.APPLICATION:
            current_count = user.daily_applications_today
            max_limit = DailyUsageLimit.Limits.FREE_DAILY_APPLICATIONS
            field_name = "daily_applications_today"
            limit_message = f"무료 회원은 하루 {max_limit}회까지 지원 가능합니다."
        elif usage_type == DailyUsageLimit.UsageType.PROFILE_VIEW:
            current_count = user.daily_views_today
            max_limit = DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS
            field_name = "daily_views_today"
            limit_message = f"무료 회원은 하루 {max_limit}명까지 프로필 열람 가능합니다."
        else:
            return {
                "allowed": False,
                "count": 0,
                "limit": 0,
                "message": "알 수 없는 사용 유형입니다."
            }

        # Check if limit reached
        if current_count >= max_limit:
            return {
                "allowed": False,
                "count": current_count,
                "limit": max_limit,
                "message": limit_message + " 프리미엄으로 업그레이드하면 무제한 이용이 가능합니다."
            }

        # Increment usage
        setattr(user, field_name, current_count + 1)

        # Track in daily_usage_limits table for analytics
        await self._track_usage(user_id, usage_type, max_limit)

        await self.db.commit()

        return {
            "allowed": True,
            "count": current_count + 1,
            "limit": max_limit,
            "message": f"남은 사용 횟수: {max_limit - current_count - 1}회"
        }

    async def _track_usage(
        self,
        user_id: UUID,
        usage_type: str,
        limit: Optional[int]
    ):
        """Track usage in daily_usage_limits table for analytics."""
        today = date.today()

        # Find or create usage record
        stmt = select(DailyUsageLimit).where(
            and_(
                DailyUsageLimit.user_id == str(user_id),
                DailyUsageLimit.usage_date == today,
                DailyUsageLimit.usage_type == usage_type
            )
        )
        result = await self.db.execute(stmt)
        usage_record = result.scalar_one_or_none()

        if usage_record:
            usage_record.count += 1
        else:
            usage_record = DailyUsageLimit(
                user_id=str(user_id),
                usage_date=today,
                usage_type=usage_type,
                count=1,
                max_limit=limit
            )
            self.db.add(usage_record)

    async def get_usage_status(self, user_id: UUID) -> Dict[str, Any]:
        """Get current usage status for a user."""
        user = await self.db.get(User, user_id)
        if not user:
            return {"error": "User not found"}

        today = date.today()

        # Reset if new day
        if user.last_usage_reset_date != today:
            user.daily_applications_today = 0
            user.daily_views_today = 0
            user.last_usage_reset_date = today
            user.last_viewed_profiles = []
            await self.db.commit()

        if user.membership_tier == "premium":
            return {
                "membership_tier": "premium",
                "applications": {
                    "used": 0,
                    "limit": None,
                    "unlimited": True
                },
                "profile_views": {
                    "used": 0,
                    "limit": None,
                    "unlimited": True
                }
            }
        else:
            return {
                "membership_tier": "free",
                "applications": {
                    "used": user.daily_applications_today,
                    "limit": DailyUsageLimit.Limits.FREE_DAILY_APPLICATIONS,
                    "unlimited": False,
                    "remaining": DailyUsageLimit.Limits.FREE_DAILY_APPLICATIONS - user.daily_applications_today
                },
                "profile_views": {
                    "used": user.daily_views_today,
                    "limit": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS,
                    "unlimited": False,
                    "remaining": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS - user.daily_views_today
                },
                "last_reset": user.last_usage_reset_date,
                "next_reset": "매일 자정"
            }

    async def track_profile_view(self, user_id: UUID, viewed_profile_id: UUID) -> Dict[str, Any]:
        """
        Track profile view and check if limit reached.
        Special handling to avoid counting duplicate views of same profile.
        """
        user = await self.db.get(User, user_id)
        if not user:
            return {"allowed": False, "message": "User not found"}

        # Premium users have no limits
        if user.membership_tier == "premium":
            return {"allowed": True, "message": "Premium - unlimited views"}

        today = date.today()

        # Reset if new day
        if user.last_usage_reset_date != today:
            user.daily_applications_today = 0
            user.daily_views_today = 0
            user.last_usage_reset_date = today
            user.last_viewed_profiles = []

        # Check if already viewed this profile today
        viewed_profiles = user.last_viewed_profiles or []
        viewed_profile_id_str = str(viewed_profile_id)

        if viewed_profile_id_str in viewed_profiles:
            # Already viewed today, don't count again
            return {
                "allowed": True,
                "message": "이미 오늘 열람한 프로필입니다.",
                "count": user.daily_views_today,
                "limit": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS
            }

        # Check limit
        if user.daily_views_today >= DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS:
            return {
                "allowed": False,
                "message": f"일일 열람 한도 {DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS}명 도달. 프리미엄 업그레이드 필요.",
                "count": user.daily_views_today,
                "limit": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS
            }

        # Update counts
        user.daily_views_today += 1
        viewed_profiles.append(viewed_profile_id_str)
        user.last_viewed_profiles = viewed_profiles

        # Track in analytics table
        await self._track_usage(
            user_id,
            DailyUsageLimit.UsageType.PROFILE_VIEW,
            DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS
        )

        await self.db.commit()

        return {
            "allowed": True,
            "message": f"프로필 열람 {user.daily_views_today}/{DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS}",
            "count": user.daily_views_today,
            "limit": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS,
            "remaining": DailyUsageLimit.Limits.FREE_DAILY_PROFILE_VIEWS - user.daily_views_today
        }

    async def reset_daily_limits(self, user_id: Optional[UUID] = None):
        """
        Reset daily limits for a user or all users.
        This would typically be called by a cron job at midnight.
        """
        if user_id:
            user = await self.db.get(User, user_id)
            if user:
                user.daily_applications_today = 0
                user.daily_views_today = 0
                user.last_usage_reset_date = date.today()
                user.last_viewed_profiles = []
        else:
            # Reset all users (for cron job)
            stmt = select(User)
            result = await self.db.execute(stmt)
            users = result.scalars().all()

            for user in users:
                user.daily_applications_today = 0
                user.daily_views_today = 0
                user.last_usage_reset_date = date.today()
                user.last_viewed_profiles = []

        await self.db.commit()