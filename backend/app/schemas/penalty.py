from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PenaltyReportRequest(BaseModel):
    reported_user_id: str
    penalty_type: str  # no_show, same_day_cancel, late, cancel_after_confirm
    description: Optional[str] = None


class PenaltyRecordResponse(BaseModel):
    id: UUID
    user_id: UUID
    penalty_type: str
    status: str
    reported_by: Optional[UUID] = None
    suspend_until: Optional[datetime] = None
    restrict_until: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PenaltyListResponse(BaseModel):
    items: list[PenaltyRecordResponse]
    total: int
