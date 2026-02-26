from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: Optional[str]
    data_json: Optional[dict]
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int


class DeviceTokenCreate(BaseModel):
    token: str
    platform: str  # ios / android / web


class UnreadCountResponse(BaseModel):
    count: int
