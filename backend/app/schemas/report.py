from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.enums import ReportType, ReportStatus


class ReportCreate(BaseModel):
    reported_user_id: UUID
    report_type: ReportType
    description: str = Field(..., min_length=10)


class ReportResponse(BaseModel):
    id: UUID
    reporter_user_id: UUID
    reported_user_id: UUID
    report_type: ReportType
    status: ReportStatus
    description: str
    resolution_note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class BlockCreate(BaseModel):
    blocked_user_id: UUID


class BlockResponse(BaseModel):
    id: UUID
    blocker_user_id: UUID
    blocked_user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class BlockListResponse(BaseModel):
    items: List[BlockResponse]
    total: int
