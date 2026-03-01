"""Pydantic schemas for the Backup Instructor (studio's trusted pool) feature."""
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class BackupInstructorCreate(BaseModel):
    """Request body when adding an instructor to the backup network."""

    model_config = ConfigDict(populate_by_name=True)

    instructor_id: UUID
    nickname: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, validation_alias=AliasChoices("note", "memo"))
    priority: int = Field(3, ge=1, le=3)


class BackupInstructorUpdate(BaseModel):
    """Request body when updating a backup instructor entry."""

    model_config = ConfigDict(populate_by_name=True)

    nickname: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, validation_alias=AliasChoices("note", "memo"))
    priority: Optional[int] = Field(None, ge=1, le=3)


class BackupInstructorResponse(BaseModel):
    """Single backup instructor entry with denormalised instructor info."""

    id: UUID
    studio_id: UUID
    instructor_id: UUID
    nickname: Optional[str] = None
    note: Optional[str] = None
    priority: int = 3
    last_worked_at: Optional[datetime] = None
    total_completed: int = 0
    # Instructor info (populated at endpoint level)
    instructor_name: Optional[str] = None
    instructor_phone: Optional[str] = None
    instructor_categories: Optional[list] = None
    instructor_rating: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BackupInstructorListResponse(BaseModel):
    """Paginated list of backup instructors."""

    items: list[BackupInstructorResponse]
    total: int
