from sqlalchemy import Column, String, Text, Date, Time, ForeignKey, Numeric, Integer, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import ContractStatus


class Contract(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contracts"

    offer_id = Column(GUID(), ForeignKey("offers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    studio_id = Column(GUID(), ForeignKey("studio_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default=ContractStatus.CONFIRMED.value, nullable=False, index=True)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), default=0, nullable=False)  # 5% platform fee (v2.0)
    settlement_amount = Column(Numeric(10, 2), default=0, nullable=False)  # Amount after fee (v2.0)
    total_sessions = Column(Integer, default=1)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Bidirectional completion confirmation (v2.0)
    studio_confirmed_at = Column(DateTime)
    instructor_confirmed_at = Column(DateTime)

    # Cancellation/Refund policy agreement (v2.0)
    policy_agreed_at = Column(DateTime)
    policy_version = Column(String(10))

    cancellation_reason = Column(Text)
    cancelled_by_user_id = Column(GUID(), ForeignKey("users.id"))

    # Relationships
    offer = relationship("Offer", back_populates="contract")
    event_logs = relationship("ContractEventLog", back_populates="contract", order_by="ContractEventLog.created_at")
    payment = relationship("Payment", back_populates="contract", uselist=False)
    payout = relationship("Payout", back_populates="contract", uselist=False)
    reviews = relationship("Review", back_populates="contract")
    chat_thread = relationship("ChatThread", back_populates="contract", uselist=False)


class ContractEventLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "contract_event_logs"

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    from_status = Column(String(20))
    to_status = Column(String(20), nullable=False)
    note = Column(Text)

    # Relationships
    contract = relationship("Contract", back_populates="event_logs")
