from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.models.enums import ApplicationStatus


class ApplicationCreate(BaseModel):
    cover_letter: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: UUID
    job_post_id: UUID
    instructor_id: UUID
    status: ApplicationStatus
    cover_letter: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationWithJobResponse(ApplicationResponse):
    job_title: Optional[str] = None
    studio_name: Optional[str] = None


class ApplicationWithInstructorResponse(ApplicationResponse):
    """Application with instructor info (for studio viewing applicants)."""
    instructor_name: Optional[str] = None
    instructor_phone: Optional[str] = None
    instructor_experience_years: Optional[int] = None
    instructor_categories: Optional[list] = None
    instructor_rating: Optional[float] = None
    has_offer: bool = False  # True if an offer has been sent for this application
    is_premium: bool = False  # True if instructor has premium membership


class ApplicationListResponse(BaseModel):
    items: List[ApplicationWithJobResponse]
    total: int


class ApplicationWithInstructorListResponse(BaseModel):
    items: List[ApplicationWithInstructorResponse]
    total: int
