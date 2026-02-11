from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.enums import ThreadScope, MessageType


class ThreadCreate(BaseModel):
    scope: ThreadScope
    job_post_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    instructor_id: UUID


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    sender_user_id: Optional[UUID] = None
    message_type: MessageType
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ThreadResponse(BaseModel):
    id: UUID
    scope: ThreadScope
    job_post_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    studio_id: UUID
    instructor_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    items: List[ThreadResponse]
    total: int


class ThreadMessagesResponse(BaseModel):
    thread: ThreadResponse
    messages: List[MessageResponse]


class WebSocketMessage(BaseModel):
    type: str  # "message", "typing", "read"
    data: dict
