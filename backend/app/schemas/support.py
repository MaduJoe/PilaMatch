from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.enums import TicketStatus


class SupportTicketCreate(BaseModel):
    subject: str = Field(..., max_length=200)
    description: str = Field(..., min_length=10)


class SupportTicketResponse(BaseModel):
    id: UUID
    user_id: UUID
    subject: str
    description: str
    status: TicketStatus
    resolution_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportTicketListResponse(BaseModel):
    items: List[SupportTicketResponse]
    total: int
