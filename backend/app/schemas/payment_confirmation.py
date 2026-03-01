from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class MarkPaidRequest(BaseModel):
    amount: Decimal


class DisputePaymentRequest(BaseModel):
    reason: str


class PaymentConfirmationResponse(BaseModel):
    id: UUID
    application_id: UUID
    center_user_id: UUID
    instructor_user_id: UUID
    amount: Decimal
    status: str
    center_marked_paid_at: Optional[datetime] = None
    instructor_confirmed_at: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentConfirmationListResponse(BaseModel):
    items: list[PaymentConfirmationResponse]
