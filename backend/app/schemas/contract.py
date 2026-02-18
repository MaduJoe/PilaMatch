from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, time, datetime

from app.models.enums import ContractStatus


class ContractResponse(BaseModel):
    id: UUID
    offer_id: UUID
    studio_id: UUID
    instructor_id: UUID
    status: ContractStatus
    hourly_rate: Decimal
    total_amount: Decimal
    total_sessions: int
    date: date
    start_time: time
    end_time: time

    # Signature tracking
    instructor_signed_at: Optional[datetime] = None
    studio_signed_at: Optional[datetime] = None

    # v2.0 fields
    studio_confirmed_at: Optional[datetime] = None
    instructor_confirmed_at: Optional[datetime] = None
    platform_fee: Optional[float] = None
    settlement_amount: Optional[float] = None

    cancellation_reason: Optional[str] = None
    cancelled_by_user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    items: List[ContractResponse]
    total: int


class ContractCancelRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class ContractEventLogResponse(BaseModel):
    id: UUID
    contract_id: UUID
    actor_user_id: UUID
    from_status: Optional[ContractStatus] = None
    to_status: ContractStatus
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
