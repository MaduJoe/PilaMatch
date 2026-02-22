from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, time

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
    is_past: bool = False
    application_count: int = 0
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
