from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class HandoffNoteCreate(BaseModel):
    """Schema for creating or updating a handoff note."""

    class_topic: Optional[str] = Field(None, max_length=200)
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = Field(None, max_length=50)
    additional_notes: Optional[str] = None
    member_notes: Optional[str] = None
    equipment_notes: Optional[str] = None


class HandoffNoteUpdate(HandoffNoteCreate):
    """Schema for updating a handoff note (same fields as create)."""

    pass


class HandoffNotePublicResponse(BaseModel):
    """Public response — sensitive fields (member_notes, equipment_notes) hidden."""

    id: UUID
    job_post_id: UUID
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    additional_notes: Optional[str] = None
    has_sensitive_info: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HandoffNoteFullResponse(BaseModel):
    """Full response — includes sensitive fields for authorized users."""

    id: UUID
    job_post_id: UUID
    class_topic: Optional[str] = None
    class_sequence_info: Optional[str] = None
    atmosphere_preference: Optional[str] = None
    additional_notes: Optional[str] = None
    member_notes: Optional[str] = None
    equipment_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
