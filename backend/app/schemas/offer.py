from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.models.enums import OfferStatus


class OfferCreate(BaseModel):
    application_id: Optional[UUID] = None  # For application-based offers
    instructor_id: Optional[UUID] = None  # For direct offers
    message: Optional[str] = None
    proposed_rate: Decimal = Field(..., gt=0)


class OfferResponse(BaseModel):
    id: UUID
    application_id: Optional[UUID] = None
    studio_id: UUID
    instructor_id: UUID
    status: OfferStatus
    message: Optional[str] = None
    proposed_rate: Decimal
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfferListResponse(BaseModel):
    items: List[OfferResponse]
    total: int
