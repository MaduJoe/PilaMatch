from sqlalchemy import Column, String, Text, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import PaymentStatus, PayoutStatus


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    payer_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default=PaymentStatus.PENDING.value, nullable=False, index=True)
    payment_key = Column(String(200), unique=True, index=True)  # TossPayments key
    order_id = Column(String(200), unique=True, nullable=False, index=True)
    payment_method = Column(String(50))
    pg_response = Column(JSON)  # Full PG response
    failure_reason = Column(Text)

    # Cancellation tracking
    cancelled_amount = Column(Numeric(10, 2), default=0)
    balance_amount = Column(Numeric(10, 2))  # amount - cancelled_amount

    # Escrow status: HELD (결제완료, 보관중), RELEASED (강사 지급완료), REFUNDED (스튜디오 환불)
    escrow_status = Column(String(20), default="HELD", nullable=False)

    # Relationships
    contract = relationship("Contract", back_populates="payment")
    cancellations = relationship(
        "PaymentCancellation", back_populates="payment",
        order_by="PaymentCancellation.created_at",
    )


class Payout(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payouts"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    payee_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default=PayoutStatus.PENDING.value, nullable=False, index=True)
    bank_code = Column(String(10))
    account_number = Column(String(50))
    account_holder = Column(String(100))
    transfer_reference = Column(String(200))
    failure_reason = Column(Text)

    # Relationships
    contract = relationship("Contract", back_populates="payout")
