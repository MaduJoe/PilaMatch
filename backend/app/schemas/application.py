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
    contact_revealed: bool = False
    contact_revealed_at: Optional[datetime] = None
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
    contact_revealed: bool = False
    # These are only populated when contact_revealed is True:
    instructor_full_phone: Optional[str] = None
    studio_phone: Optional[str] = None
    studio_name: Optional[str] = None
    # Trust-tech profile data
    instructor_completed_substitutes: int = 0
    instructor_no_show_count: int = 0
    instructor_review_count: int = 0


class ContactRevealResponse(BaseModel):
    """Response when contact info is revealed after accepting an application."""
    application_id: UUID
    instructor_phone: str  # Full phone number
    instructor_name: str
    studio_phone: str  # Full phone number
    studio_name: str
    studio_address: Optional[str] = None
    message: str = "연락처가 공개되었습니다. 직접 연락하여 세부 사항을 조율해주세요."


class ApplicationListResponse(BaseModel):
    items: List[ApplicationWithJobResponse]
    total: int


class ApplicationWithInstructorListResponse(BaseModel):
    items: List[ApplicationWithInstructorResponse]
    total: int
