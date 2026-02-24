"""Subscription and Premium membership models."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import enum

from sqlalchemy import (
    Column, String, DateTime, Boolean, Numeric, Integer, Text, ForeignKey,
    Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin, GUID


class MembershipTier(str, enum.Enum):
    """Membership tier levels."""
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status types."""
    INACTIVE = "inactive"  # Created but not paid yet
    ACTIVE = "active"      # Paid and active
    CANCELLED = "cancelled"  # User cancelled, will expire at end of period
    EXPIRED = "expired"    # Past end date
    SUSPENDED = "suspended"  # Payment failed after retries


class PaymentStatus(str, enum.Enum):
    """Payment status for subscription payments."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionChangeReason(str, enum.Enum):
    """Reasons for subscription changes."""
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    AUTO_RENEW = "auto_renew"
    CANCELLATION = "cancellation"
    SUSPENSION = "suspension"
    REACTIVATION = "reactivation"


class Subscription(Base, UUIDMixin, TimestampMixin):
    """Premium subscription model."""

    __tablename__ = "subscriptions"

    # Relationships
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="subscription")

    # Subscription details
    tier = Column(String(20), nullable=False, default="premium")
    status = Column(String(20), nullable=False, default="inactive")

    # Billing
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    next_billing_date = Column(DateTime, nullable=True)
    billing_cycle_day = Column(Integer, nullable=True)  # Day of month (1-28)

    # Payment
    monthly_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("9900"))
    auto_renew = Column(Boolean, nullable=False, default=True)

    # Cancellation
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Payment method (for auto-renewal)
    toss_billing_key = Column(String(200), nullable=True)  # For recurring payments
    payment_method_type = Column(String(50), nullable=True)  # card, transfer, etc.
    toss_customer_key = Column(String(200), nullable=True)  # TossPayments customer key for billing
    card_last_four = Column(String(4), nullable=True)  # Last 4 digits of registered card
    card_company = Column(String(50), nullable=True)  # Card issuer name (e.g. 삼성카드, 현대카드)

    # Relationships
    payments = relationship("SubscriptionPayment", back_populates="subscription", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_subscription_user", "user_id"),
        Index("idx_subscription_status", "status"),
        Index("idx_subscription_next_billing", "next_billing_date"),
    )


class SubscriptionPayment(Base, UUIDMixin, TimestampMixin):
    """Individual payment records for subscriptions."""

    __tablename__ = "subscription_payments"

    # Relationships
    subscription_id = Column(GUID(), ForeignKey("subscriptions.id"), nullable=False)
    subscription = relationship("Subscription", back_populates="payments")

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False, default=Decimal("9900"))
    status = Column(String(20), nullable=False, default="pending")

    # Dates
    payment_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)

    # TossPayments integration
    order_id = Column(String(200), unique=True, nullable=False)
    toss_payment_key = Column(String(200), nullable=True, unique=True)

    # Error handling
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    last_retry_at = Column(DateTime, nullable=True)

    # Receipt
    receipt_url = Column(String(500), nullable=True)

    # Payment type and bank transfer
    payment_type = Column(String(20), default="initial")  # initial | renewal | bank_transfer
    bank_transfer_confirmed_by = Column(GUID(), ForeignKey("users.id"), nullable=True)
    bank_transfer_confirmed_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_payment_subscription", "subscription_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_order", "order_id"),
    )


class SubscriptionHistory(Base, UUIDMixin, TimestampMixin):
    """Audit log for all subscription changes."""

    __tablename__ = "subscription_history"

    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    user = relationship("User", foreign_keys=[user_id])

    # Change details
    old_tier = Column(String(20), nullable=True)
    new_tier = Column(String(20), nullable=False)
    reason = Column(String(50), nullable=False)

    # Additional context
    note = Column(Text, nullable=True)
    performed_by = Column(GUID(), ForeignKey("users.id"), nullable=True)  # Admin actions

    # Related payment (if applicable)
    payment_id = Column(GUID(), ForeignKey("subscription_payments.id"), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_history_user", "user_id"),
        Index("idx_history_created", "created_at"),
    )