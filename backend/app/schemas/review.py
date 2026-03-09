from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    # Checklist review fields (lightweight review for substitute)
    time_punctuality: Optional[bool] = None  # 시간 준수
    professionalism: Optional[bool] = None   # 전문성
    would_rehire: Optional[bool] = None      # 재고용 의향


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    time_punctuality: Optional[bool] = None
    professionalism: Optional[bool] = None
    would_rehire: Optional[bool] = None


class ReviewResponse(BaseModel):
    id: UUID
    application_id: Optional[UUID] = None
    contract_id: Optional[UUID] = None
    reviewer_user_id: UUID
    reviewee_instructor_id: Optional[UUID] = None
    reviewee_studio_id: Optional[UUID] = None
    rating: int
    comment: Optional[str] = None
    time_punctuality: Optional[bool] = None
    professionalism: Optional[bool] = None
    would_rehire: Optional[bool] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    average_rating: Optional[float] = None


class ReviewEligibilityResponse(BaseModel):
    application_id: UUID
    review_eligible: bool       # class has ended
    review_expired: bool        # past end-of-day KST
    has_written: bool           # current user already wrote
    both_reviewed: bool         # mutual reviews present
    my_review: Optional[ReviewResponse] = None
    partner_review: Optional[ReviewResponse] = None  # only when both_reviewed=True
