from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, time, datetime

from app.models.enums import Category, JobType, JobPostStatus


class JobPostCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: Category
    job_type: JobType
    date: date
    start_time: time
    end_time: time
    hourly_rate: Decimal = Field(..., gt=0)
    total_sessions: int = Field(1, ge=1)
    required_experience_years: int = Field(0, ge=0)
    required_certifications: List[str] = []
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_urgent: bool = False
    payment_method: Optional[str] = None  # bank_transfer/cash/etc
    terms_agreed: bool = False  # Checklist 6+7 agreement
    preferred_style: Optional[dict] = None  # {correction_style, class_atmosphere, intensity_level}
    # Handoff note (required for trust — embedded at creation)
    handoff_class_topic: str = Field(..., max_length=200)
    handoff_class_sequence_info: str = Field(...)
    handoff_atmosphere_preference: str = Field(..., max_length=50)
    handoff_member_notes: str = Field(...)
    handoff_equipment_notes: str = Field(...)


class JobPostUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[Category] = None
    job_type: Optional[JobType] = None
    status: Optional[JobPostStatus] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    hourly_rate: Optional[Decimal] = Field(None, gt=0)
    total_sessions: Optional[int] = Field(None, ge=1)
    required_experience_years: Optional[int] = Field(None, ge=0)
    required_certifications: Optional[List[str]] = None
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_urgent: Optional[bool] = None
    payment_method: Optional[str] = None
    terms_agreed: Optional[bool] = None
    preferred_style: Optional[dict] = None


class JobPostResponse(BaseModel):
    id: UUID
    studio_id: UUID
    title: str
    description: Optional[str] = None
    category: Category
    job_type: JobType
    status: JobPostStatus
    date: date
    start_time: time
    end_time: time
    hourly_rate: Decimal
    total_sessions: int
    required_experience_years: int
    required_certifications: List[str]
    region: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_urgent: bool = False
    payment_method: Optional[str] = None
    terms_agreed: bool = False
    preferred_style: Optional[dict] = None
    distance_km: Optional[float] = None  # Calculated field, not from DB
    distance_text: Optional[str] = None  # e.g. "2.3km"
    travel_time_min: Optional[int] = None  # e.g. 15
    is_past: bool = False
    application_count: int = 0
    has_handoff_note: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Note: is_premium is added at the endpoint level for security reasons

    class Config:
        from_attributes = True


class JobPostListResponse(BaseModel):
    items: List[JobPostResponse]
    total: int
    page: int
    page_size: int


class JobPostFilter(BaseModel):
    category: Optional[Category] = None
    job_type: Optional[JobType] = None
    status: Optional[JobPostStatus] = None
    region: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_rate: Optional[Decimal] = None
    max_rate: Optional[Decimal] = None
    is_urgent: Optional[bool] = None
    sort_by_distance: bool = False  # If true, sorts by distance when lat/lng provided
    user_latitude: Optional[float] = None
    user_longitude: Optional[float] = None
    max_distance_km: Optional[float] = None  # Filter by max distance
