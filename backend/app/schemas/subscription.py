"""Subscription schemas for Premium membership."""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, UUID4


class SubscriptionBase(BaseModel):
    """Base subscription model."""

    tier: str = "premium"
    monthly_amount: Decimal = Decimal("9900")
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Model for creating a subscription."""

    pass


class SubscriptionResponse(BaseModel):
    """Subscription response model."""

    id: UUID4
    user_id: UUID4
    tier: str
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    monthly_amount: float
    auto_renew: bool
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Billing info
    card_last_four: Optional[str] = None
    card_company: Optional[str] = None
    has_billing_key: bool = False

    class Config:
        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """Current subscription status for a user."""

    has_subscription: bool
    membership_tier: str
    subscription: Optional[SubscriptionResponse]


class UpgradeInitializeRequest(BaseModel):
    """Request to initialize premium upgrade."""

    payment_method: str = "card"  # "billing" | "card" | "bank_transfer"


class UpgradeInitializeResponse(BaseModel):
    """Response from upgrade initialization."""

    order_id: str
    amount: float
    subscription_id: UUID4
    client_key: str  # TossPayments client key
    customer_key: Optional[str] = None  # For billing key registration


class PaymentConfirmRequest(BaseModel):
    """Request to confirm subscription payment."""

    payment_key: str
    order_id: str


class PaymentConfirmResponse(BaseModel):
    """Response from payment confirmation."""

    success: bool
    subscription_id: UUID4
    message: str
    next_billing_date: datetime


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription."""

    reason: Optional[str] = None


class CancelSubscriptionResponse(BaseModel):
    """Response from subscription cancellation."""

    success: bool
    message: str
    deposit_refunded: float
    effective_date: datetime


class SubscriptionHistoryItem(BaseModel):
    """Individual subscription history entry."""

    id: UUID4
    old_tier: Optional[str]
    new_tier: str
    reason: str
    note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionHistoryResponse(BaseModel):
    """List of subscription history."""

    history: List[SubscriptionHistoryItem]
    total: int


class SubscriptionWebhookRequest(BaseModel):
    """Webhook request from TossPayments."""

    event_type: str
    data: dict


# --- Billing Key ---

class BillingKeyRegisterRequest(BaseModel):
    """Request to register a billing key from Toss auth."""

    auth_key: str
    customer_key: str


class BillingKeyRegisterResponse(BaseModel):
    """Response after billing key registration."""

    success: bool
    card_last_four: Optional[str] = None
    card_company: Optional[str] = None
    message: str


class BillingMethodResponse(BaseModel):
    """Registered billing method info."""

    has_billing_key: bool
    card_last_four: Optional[str] = None
    card_company: Optional[str] = None


# --- Bank Transfer ---

class BankTransferUpgradeRequest(BaseModel):
    """Request to initiate bank transfer upgrade."""

    depositor_name: str


class BankTransferUpgradeResponse(BaseModel):
    """Response with bank transfer info."""

    order_id: str
    amount: float
    bank_name: str
    account_number: str
    account_holder: str
    depositor_name: str
    expires_at: datetime
    message: str


# --- Renew All ---

class RenewAllRequest(BaseModel):
    """Request to trigger renewal (protected by CRON_SECRET)."""

    cron_secret: str