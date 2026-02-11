from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.models.enums import PaymentStatus, PayoutStatus


class PaymentInitRequest(BaseModel):
    """Request to initialize a payment."""
    pass  # Contract ID comes from URL


class PaymentInitResponse(BaseModel):
    """Response with payment initialization data for frontend."""
    order_id: str
    amount: Decimal
    order_name: str
    customer_name: Optional[str] = None


class PaymentConfirmRequest(BaseModel):
    """Request from TossPayments after user completes payment."""
    payment_key: str
    order_id: str
    amount: Decimal


class PaymentWebhookRequest(BaseModel):
    """Webhook request from TossPayments."""
    event_type: str
    data: Dict[str, Any]


class PaymentResponse(BaseModel):
    id: UUID
    contract_id: UUID
    payer_user_id: UUID
    amount: Decimal
    platform_fee: Decimal
    status: PaymentStatus
    payment_key: Optional[str] = None
    order_id: str
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayoutResponse(BaseModel):
    id: UUID
    contract_id: UUID
    payee_user_id: UUID
    amount: Decimal
    status: PayoutStatus
    bank_code: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    transfer_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
