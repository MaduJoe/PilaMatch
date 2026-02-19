"""Daily usage limit tracking model."""
from sqlalchemy import Column, String, Integer, Date, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, UUIDMixin, TimestampMixin


class DailyUsageLimit(Base, UUIDMixin, TimestampMixin):
    """Track daily usage limits for free tier users."""

    __tablename__ = "daily_usage_limits"
    __table_args__ = (
        UniqueConstraint('user_id', 'usage_date', 'usage_type', name='uq_user_date_type'),
    )

    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    usage_date = Column(Date, nullable=False)
    usage_type = Column(String(50), nullable=False)  # 'application' or 'profile_view'
    count = Column(Integer, default=0, nullable=False)
    max_limit = Column(Integer, nullable=True)  # NULL for unlimited (premium users)

    # Relationships
    user = relationship("User", back_populates="usage_limits")

    class UsageType:
        """Usage type constants."""
        APPLICATION = "application"
        PROFILE_VIEW = "profile_view"

    class Limits:
        """Free tier daily limits."""
        FREE_DAILY_APPLICATIONS = 5
        FREE_DAILY_PROFILE_VIEWS = 5

    def is_limit_reached(self) -> bool:
        """Check if daily limit is reached."""
        if self.max_limit is None:  # Premium users have no limit
            return False
        return self.count >= self.max_limit

    def increment(self) -> bool:
        """Increment usage count. Returns False if limit reached."""
        if self.is_limit_reached():
            return False
        self.count += 1
        self.updated_at = datetime.utcnow()
        return True

    def reset(self):
        """Reset daily count."""
        self.count = 0
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<DailyUsageLimit user={self.user_id} type={self.usage_type} date={self.usage_date} count={self.count}/{self.max_limit}>"