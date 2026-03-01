from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class PenaltyRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "penalty_records"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    penalty_type = Column(String(30), nullable=False, index=True)
    status = Column(String(20), default="active", nullable=False)
    reported_by = Column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    suspend_until = Column(DateTime, nullable=True)
    restrict_until = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    evidence_snapshot = Column(JSON, nullable=True)
