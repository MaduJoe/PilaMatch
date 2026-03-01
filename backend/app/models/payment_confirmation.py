from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class PaymentConfirmation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_confirmations"

    application_id = Column(GUID(), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    center_user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    center_marked_paid_at = Column(DateTime, nullable=True)
    instructor_confirmed_at = Column(DateTime, nullable=True)
    dispute_reason = Column(Text, nullable=True)
