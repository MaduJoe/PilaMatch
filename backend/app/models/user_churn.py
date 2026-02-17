"""User churn tracking model (v2.0)."""
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class ChurnEventType(str):
    WITHDRAWAL = "withdrawal"  # User voluntarily withdraws
    DORMANT_30D = "dormant_30d"  # 30 days inactive
    DORMANT_60D = "dormant_60d"  # 60 days inactive
    DORMANT_90D = "dormant_90d"  # 90 days inactive (convert to dormant)


class ChurnReasonCode(str):
    NO_MATCHING = "no_matching"  # Couldn't find suitable matches
    PAYMENT_BURDEN = "payment_burden"  # Fee/deposit burden
    OTHER_SERVICE = "other_service"  # Using competing service
    APP_DIFFICULTY = "app_difficulty"  # App usage difficulty
    BAD_EXPERIENCE = "bad_experience"  # Dispute/unpleasant experience
    TEMPORARY_BREAK = "temporary_break"  # Temporarily inactive
    OTHER = "other"  # Other reasons


class UserChurnLog(Base, UUIDMixin, TimestampMixin):
    """Log user churn events for analysis."""
    __tablename__ = "user_churn_logs"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False, index=True)  # ChurnEventType
    reason_code = Column(String(50))  # ChurnReasonCode (for withdrawals)
    reason_detail = Column(Text)  # Free text for "other" reasons

    # Relationships
    user = relationship("User", foreign_keys=[user_id])