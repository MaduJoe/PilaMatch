"""Dispute model for handling conflicts (v2.0)."""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class DisputeType(str):
    NO_SHOW = "no_show"
    COMPLETION_REJECTED = "completion_rejected"
    OTHER = "other"


class DisputeStatus(str):
    OPEN = "open"
    OBJECTED = "objected"
    RESOLVED = "resolved"


class DisputeResolution(str):
    REPORTER_WINS = "reporter_wins"
    RESPONDENT_WINS = "respondent_wins"
    PARTIAL = "partial"


class Dispute(Base, UUIDMixin, TimestampMixin):
    """Dispute model for tracking and resolving conflicts between users."""
    __tablename__ = "disputes"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    reported_by = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_against = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    type = Column(String(20), nullable=False)  # DisputeType
    status = Column(String(20), default=DisputeStatus.OPEN, nullable=False, index=True)
    objection_deadline = Column(DateTime)  # 24h from creation for objection
    objection_reason = Column(Text)  # Reason for objection if provided
    resolution = Column(String(20))  # DisputeResolution
    resolution_reason = Column(Text)
    resolved_by = Column(String(50))  # 'system' or admin_user_id
    resolved_at = Column(DateTime)

    # Auto-collected evidence (chat logs, access logs, reminder confirmation, etc.)
    evidence_snapshot = Column(JSON)

    # Relationships
    contract = relationship("Contract", foreign_keys=[contract_id])
    reporter = relationship("User", foreign_keys=[reported_by])
    respondent = relationship("User", foreign_keys=[reported_against])