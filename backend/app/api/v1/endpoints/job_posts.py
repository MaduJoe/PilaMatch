from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import require_role, get_optional_user, get_current_user
from app.models import User, UserRole, InstructorProfile
from app.models.enums import Category, JobType, JobPostStatus
from app.schemas.job_post import (
    JobPostCreate,
    JobPostUpdate,
    JobPostResponse,
    JobPostListResponse,
    JobPostFilter,
)
from app.services.job_post import JobPostService
from app.services.matching import calculate_matching_score, get_match_label


class MatchingBreakdown(BaseModel):
    score: int
    weight: int


class MatchingScore(BaseModel):
    total: int
    label: str
    breakdown: dict


class JobPostWithMatchingResponse(BaseModel):
    job: JobPostResponse
    matching: MatchingScore


class JobPostWithMatchingListResponse(BaseModel):
    items: List[JobPostWithMatchingResponse]
    total: int
    page: int
    page_size: int

router = APIRouter()


@router.post("", response_model=JobPostResponse, status_code=status.HTTP_201_CREATED)
async def create_job_post(
    data: JobPostCreate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job post (studio only)."""
    service = JobPostService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    job_post = await service.create(studio_id, data)
    return JobPostResponse.model_validate(job_post)


@router.get("", response_model=JobPostListResponse)
async def list_job_posts(
    category: Optional[Category] = None,
    job_type: Optional[JobType] = None,
    status: Optional[JobPostStatus] = None,
    region: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_rate: Optional[Decimal] = None,
    max_rate: Optional[Decimal] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
):
    """List job posts with filtering and pagination."""
    service = JobPostService(db)

    filters = JobPostFilter(
        category=category,
        job_type=job_type,
        status=status,
        region=region,
        date_from=date_from,
        date_to=date_to,
        min_rate=min_rate,
        max_rate=max_rate,
    )

    items, total = await service.list(filters, page, page_size, sort_by, sort_order)

    return JobPostListResponse(
        items=[JobPostResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_post_id}", response_model=JobPostResponse)
async def get_job_post(
    job_post_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a job post by ID."""
    service = JobPostService(db)
    job_post = await service.get_by_id(job_post_id)

    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POST_NOT_FOUND", "message": "Job post not found"},
        )

    return JobPostResponse.model_validate(job_post)


@router.put("/{job_post_id}", response_model=JobPostResponse)
async def update_job_post(
    job_post_id: UUID,
    data: JobPostUpdate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Update a job post (owner studio only)."""
    service = JobPostService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    try:
        job_post = await service.update(job_post_id, studio_id, data)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to update this job post"},
        )

    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POST_NOT_FOUND", "message": "Job post not found"},
        )

    return JobPostResponse.model_validate(job_post)


@router.delete("/{job_post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_post(
    job_post_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a job post (owner studio only)."""
    service = JobPostService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    try:
        success = await service.delete(job_post_id, studio_id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to delete this job post"},
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POST_NOT_FOUND", "message": "Job post not found"},
        )


@router.get("/for-me/with-matching", response_model=JobPostWithMatchingListResponse)
async def list_job_posts_with_matching(
    category: Optional[Category] = None,
    job_type: Optional[JobType] = None,
    region: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_rate: Optional[Decimal] = None,
    max_rate: Optional[Decimal] = None,
    min_match_score: int = Query(0, ge=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """List job posts with matching scores for the current instructor."""
    # Get instructor profile
    result = await db.execute(
        select(InstructorProfile).where(InstructorProfile.user_id == current_user.id)
    )
    instructor = result.scalar_one_or_none()

    if not instructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    service = JobPostService(db)

    filters = JobPostFilter(
        category=category,
        job_type=job_type,
        status=JobPostStatus.OPEN,  # Only show open jobs
        region=region,
        date_from=date_from,
        date_to=date_to,
        min_rate=min_rate,
        max_rate=max_rate,
    )

    items, total = await service.list(filters, 1, 1000, "created_at", "desc")  # Get all for scoring

    # Calculate matching scores
    jobs_with_scores = []
    for job in items:
        score_data = calculate_matching_score(instructor, job)
        if score_data["total"] >= min_match_score:
            jobs_with_scores.append({
                "job": job,
                "score": score_data["total"],
                "breakdown": score_data["breakdown"],
            })

    # Sort by matching score (descending)
    jobs_with_scores.sort(key=lambda x: x["score"], reverse=True)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = jobs_with_scores[start:end]

    return JobPostWithMatchingListResponse(
        items=[
            JobPostWithMatchingResponse(
                job=JobPostResponse.model_validate(item["job"]),
                matching=MatchingScore(
                    total=item["score"],
                    label=get_match_label(item["score"]),
                    breakdown=item["breakdown"],
                ),
            )
            for item in paginated
        ],
        total=len(jobs_with_scores),
        page=page,
        page_size=page_size,
    )
