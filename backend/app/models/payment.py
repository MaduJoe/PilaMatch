from sqlalchemy import Column, String, Text, ForeignKey, Numeric, JSON

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
# NOTE: These models are kept only for DB table preservation (no Alembic DROP).
# They are no longer imported or used in application code.


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    payer_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default="pending", nullable=False, index=True)
    payment_key = Column(String(200), unique=True, index=True)
    order_id = Column(String(200), unique=True, nullable=False, index=True)
    payment_method = Column(String(50))
    pg_response = Column(JSON)
    failure_reason = Column(Text)
    cancelled_amount = Column(Numeric(10, 2), default=0)
    balance_amount = Column(Numeric(10, 2))
    escrow_status = Column(String(20), default="HELD", nullable=False)


class Payout(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payouts"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    payee_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending", nullable=False, index=True)
    bank_code = Column(String(10))
    account_number = Column(String(50))
    account_holder = Column(String(100))
    transfer_reference = Column(String(200))
    failure_reason = Column(Text)
