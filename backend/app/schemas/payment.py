from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
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


class PaymentDetailResponse(BaseModel):
    id: UUID
    contract_id: UUID
    payer_user_id: UUID
    amount: Decimal
    platform_fee: Decimal
    status: PaymentStatus
    payment_key: Optional[str] = None
    order_id: str
    payment_method: Optional[str] = None
    cancelled_amount: Decimal = Decimal("0")
    balance_amount: Optional[Decimal] = None
    escrow_status: str = "HELD"
    cancellations: List["PaymentCancellationResponse"] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCancelRequest(BaseModel):
    cancel_amount: Decimal = Field(..., gt=0, description="취소 금액")
    cancel_reason: str = Field(..., min_length=1, max_length=200, description="취소 사유")
    idempotency_key: Optional[str] = Field(None, max_length=100, description="멱등성 키")
    tax_free_amount: Decimal = Field(default=Decimal("0"), ge=0, description="면세 금액")


class PaymentCancelResponse(BaseModel):
    id: UUID
    payment_id: UUID
    cancel_amount: Decimal
    cancel_reason: str
    cancel_status: str
    idempotency_key: Optional[str] = None
    tax_free_amount: Decimal = Decimal("0")
    failure_reason: Optional[str] = None
    transaction_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCancellationResponse(BaseModel):
    id: UUID
    cancel_amount: Decimal
    cancel_reason: str
    cancel_status: str
    tax_free_amount: Decimal = Decimal("0")
    created_at: datetime

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


# Resolve forward references
PaymentDetailResponse.model_rebuild()
