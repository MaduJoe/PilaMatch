from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import require_role, get_optional_user, get_current_user
from app.models import User, UserRole, InstructorProfile, StudioProfile
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
# PMF pivot: Premium sorting disabled
# from app.services.subscription import SubscriptionService


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
    is_premium: bool = False
    is_urgent: bool = False
    distance_km: Optional[float] = None
    distance_text: Optional[str] = None  # e.g. "2.3km"
    travel_time_min: Optional[int] = None  # e.g. 15


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

    # PMF pivot: Send urgent substitute notifications to nearby instructors
    if data.job_type == JobType.SUBSTITUTE or getattr(data, "is_urgent", False):
        try:
            from app.services.notification import NotificationService
            notif = NotificationService(db)

            # Find instructors with matching category in the same region
            instructor_query = select(InstructorProfile).where(
                InstructorProfile.is_public == True  # noqa: E712
            )
            result = await db.execute(instructor_query)
            instructors = result.scalars().all()

            studio_result = await db.execute(
                select(StudioProfile).where(StudioProfile.id == studio_id)
            )
            studio = studio_result.scalar_one_or_none()
            studio_name = studio.business_name if studio else "스튜디오"

            notified = 0
            for inst in instructors:
                # Filter by category match
                inst_categories = inst.categories or []
                if data.category and data.category not in inst_categories:
                    continue

                # Filter by region match if no GPS data
                if not (data.latitude and data.longitude):
                    inst_regions = inst.available_regions or []
                    if data.region and inst_regions and data.region not in inst_regions:
                        continue

                await notif.send(
                    user_id=str(inst.user_id),
                    type="URGENT_SUBSTITUTE",
                    title="긴급 대타 공고",
                    body=f"{studio_name}에서 {data.category} 대타를 찾고 있습니다. ({data.date} {data.start_time}~{data.end_time})",
                    data={
                        "type": "urgent_substitute",
                        "job_post_id": str(job_post.id),
                        "region": data.region,
                    },
                )
                notified += 1
                if notified >= 50:  # Cap at 50 notifications
                    break
        except Exception:
            pass  # Notification failure should not block job creation

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

    today = date.today()
    response_items = []
    for item in items:
        job_response = JobPostResponse.model_validate(item)
        job_response.is_past = item.date < today if item.date else False
        response_items.append(job_response)

    return JobPostListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size,
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
    max_distance_km: Optional[float] = Query(None, ge=0, description="Max distance filter in km"),
    user_latitude: Optional[float] = Query(None, description="Current latitude for distance calc"),
    user_longitude: Optional[float] = Query(None, description="Current longitude for distance calc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """List job posts with matching scores and distance for the current instructor.

    PMF pivot: Prioritizes urgent substitute jobs, adds distance-based sorting.
    """
    from app.utils.distance import haversine_distance, estimate_travel_time, format_distance

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

    # Use provided location or instructor's saved location
    inst_lat = user_latitude or (float(instructor.latitude) if getattr(instructor, "latitude", None) else None)
    inst_lng = user_longitude or (float(instructor.longitude) if getattr(instructor, "longitude", None) else None)

    service = JobPostService(db)

    filters = JobPostFilter(
        category=category,
        job_type=job_type,
        status=JobPostStatus.OPEN,
        region=region,
        date_from=date_from,
        date_to=date_to,
        min_rate=min_rate,
        max_rate=max_rate,
    )

    items, total = await service.list(filters, 1, 1000, "created_at", "desc", premium_first=False)

    jobs_with_scores = []
    for job in items:
        # Determine urgency: is_urgent flag OR posted <24h before class
        is_urgent = getattr(job, "is_urgent", False)
        if not is_urgent and job.date and job.start_time and job.created_at:
            class_datetime = datetime.combine(job.date, job.start_time)
            time_diff = class_datetime - job.created_at
            is_urgent = time_diff < timedelta(hours=24) and time_diff >= timedelta(0)

        # Calculate distance if location data is available
        distance_km = None
        job_lat = float(job.latitude) if getattr(job, "latitude", None) else None
        job_lng = float(job.longitude) if getattr(job, "longitude", None) else None

        if inst_lat and inst_lng and job_lat and job_lng:
            distance_km = haversine_distance(inst_lat, inst_lng, job_lat, job_lng)

            # Apply distance filter
            if max_distance_km is not None and distance_km > max_distance_km:
                continue

        # Calculate matching score with distance awareness
        score_data = calculate_matching_score(
            instructor, job,
            instructor_lat=inst_lat,
            instructor_lng=inst_lng,
        )

        if score_data["total"] >= min_match_score:
            jobs_with_scores.append({
                "job": job,
                "score": score_data["total"],
                "breakdown": score_data["breakdown"],
                "is_urgent": is_urgent,
                "is_premium": False,  # PMF pivot: premium hidden
                "distance_km": distance_km,
            })

    # Sort by: 1) Urgent first, 2) Closest distance (if available), 3) Match score, 4) Newest
    def sort_key(x):
        dist = x["distance_km"] if x["distance_km"] is not None else 9999
        return (
            -int(x["is_urgent"]),     # Urgent first
            dist,                      # Closest first
            -x["score"],               # Highest score
            -(x["job"].created_at or datetime.min).timestamp(),  # Newest
        )

    jobs_with_scores.sort(key=sort_key)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = jobs_with_scores[start:end]

    response_items = []
    for item in paginated:
        dist = item["distance_km"]
        resp = JobPostWithMatchingResponse(
            job=JobPostResponse.model_validate(item["job"]).model_copy(
                update={"is_past": item["job"].date < date.today() if item["job"].date else False}
            ),
            matching=MatchingScore(
                total=item["score"],
                label=get_match_label(item["score"]),
                breakdown=item["breakdown"],
            ),
            is_premium=False,
            is_urgent=item["is_urgent"],
            distance_km=round(dist, 1) if dist is not None else None,
            distance_text=format_distance(dist) if dist is not None else None,
            travel_time_min=estimate_travel_time(dist) if dist is not None else None,
        )
        response_items.append(resp)

    return JobPostWithMatchingListResponse(
        items=response_items,
        total=len(jobs_with_scores),
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
