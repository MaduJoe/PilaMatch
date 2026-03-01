from sqlalchemy import Column, String, Text, ForeignKey, Numeric, JSON

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID

# NOTE: Kept only for DB table preservation (no Alembic DROP).


class PaymentCancellation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payment_cancellations"

    payment_id = Column(GUID(), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    cancel_amount = Column(Numeric(10, 2), nullable=False)
    cancel_reason = Column(String(200), nullable=False)
    cancel_status = Column(String(20), default="PENDING", nullable=False)
    idempotency_key = Column(String(100), unique=True, index=True)
    tax_free_amount = Column(Numeric(10, 2), default=0)
    pg_cancel_response = Column(JSON)
    failure_reason = Column(Text)
    requested_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    transaction_key = Column(String(200))
