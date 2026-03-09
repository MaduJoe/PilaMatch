from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import (
    User, Application, InstructorProfile, StudioProfile, UserRole, Review
)
from app.schemas.review import (
    ReviewCreate, ReviewResponse, ReviewUpdate, ReviewEligibilityResponse
)
from app.services.review import ReviewService

router = APIRouter()


# ---------------------------------------------------------------------------
# Create review (application-anchored)
# ---------------------------------------------------------------------------

@router.post(
    "/applications/{application_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    application_id: UUID,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a review for a completed class session."""
    service = ReviewService(db)

    try:
        review = await service.create_review(
            application_id, current_user.id, current_user.role, data
        )
        return ReviewResponse.model_validate(review)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to review this application"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REVIEW_FAILED", "message": str(e)},
        )


# ---------------------------------------------------------------------------
# Get my review for an application
# ---------------------------------------------------------------------------

@router.get("/applications/{application_id}/reviews/my")
async def get_my_review_for_application(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's review for a specific application."""
    # Verify the application exists and user is a party
    app_result = await db.execute(
        select(Application)
        .options(joinedload(Application.job_post))
        .where(Application.id == application_id)
    )
    application = app_result.unique().scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Application not found"},
        )

    # IDOR check
    await _verify_party(db, current_user, application)

    service = ReviewService(db)
    review = await service.get_user_review_for_application(application_id, current_user.id)
    if review:
        return ReviewResponse.model_validate(review)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "REVIEW_NOT_FOUND", "message": "Review not found for this application"},
    )


# ---------------------------------------------------------------------------
# Get review eligibility + mutual reviews for an application
# ---------------------------------------------------------------------------

@router.get(
    "/applications/{application_id}/reviews",
    response_model=ReviewEligibilityResponse,
)
async def get_review_eligibility(
    application_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review eligibility and reviews for an application.

    Partner review is only visible when both parties have written.
    """
    app_result = await db.execute(
        select(Application)
        .options(joinedload(Application.job_post))
        .where(Application.id == application_id)
    )
    application = app_result.unique().scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "Application not found"},
        )

    # IDOR check
    await _verify_party(db, current_user, application)

    service = ReviewService(db)
    job_post = application.job_post

    is_eligible, is_expired = service.check_review_window(job_post)
    my_review = await service.get_user_review_for_application(application_id, current_user.id)
    both_reviewed = await service.get_both_reviewed(application_id)

    # Partner review: only visible when both have written
    partner_review = None
    if both_reviewed:
        all_reviews = await service.get_reviews_for_application(application_id)
        for r in all_reviews:
            if r.reviewer_user_id != current_user.id:
                partner_review = r
                break

    return ReviewEligibilityResponse(
        application_id=application_id,
        review_eligible=is_eligible,
        review_expired=is_expired,
        has_written=my_review is not None,
        both_reviewed=both_reviewed,
        my_review=ReviewResponse.model_validate(my_review) if my_review else None,
        partner_review=ReviewResponse.model_validate(partner_review) if partner_review else None,
    )


# ---------------------------------------------------------------------------
# Update / Delete (unchanged, by review ID)
# ---------------------------------------------------------------------------

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing review."""
    service = ReviewService(db)

    try:
        review = await service.update_review(review_id, current_user.id, data)
        return ReviewResponse.model_validate(review)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to update this review"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REVIEW_NOT_FOUND", "message": str(e)},
        )


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a review."""
    service = ReviewService(db)

    try:
        await service.delete_review(review_id, current_user.id)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to delete this review"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REVIEW_NOT_FOUND", "message": str(e)},
        )


# ---------------------------------------------------------------------------
# Received / Written reviews
# ---------------------------------------------------------------------------

@router.get("/reviews/received")
async def get_received_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reviews received by the current user."""
    service = ReviewService(db)

    if current_user.role == UserRole.INSTRUCTOR:
        result = await db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
            )
        reviews, avg_rating = await service.get_reviews_for_instructor(profile.id)

    elif current_user.role == UserRole.STUDIO:
        result = await db.execute(
            select(StudioProfile).where(StudioProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
            )
        reviews, avg_rating = await service.get_reviews_for_studio(profile.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ROLE", "message": "Invalid user role"},
        )

    review_list = []
    for review in reviews:
        review_dict = {
            "id": str(review.id),
            "application_id": str(review.application_id) if review.application_id else None,
            "contract_id": str(review.contract_id) if review.contract_id else None,
            "rating": review.rating,
            "comment": review.comment,
            "time_punctuality": review.time_punctuality,
            "professionalism": review.professionalism,
            "would_rehire": review.would_rehire,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "reviewer_name": None,
        }

        if review.reviewer_user_id:
            reviewer_result = await db.execute(
                select(User).where(User.id == review.reviewer_user_id)
            )
            reviewer_user = reviewer_result.scalar_one_or_none()

            if reviewer_user:
                if current_user.role == UserRole.INSTRUCTOR:
                    studio_result = await db.execute(
                        select(StudioProfile).where(StudioProfile.user_id == reviewer_user.id)
                    )
                    studio_profile = studio_result.scalar_one_or_none()
                    if studio_profile:
                        review_dict["reviewer_name"] = studio_profile.business_name
                else:
                    instructor_result = await db.execute(
                        select(InstructorProfile).where(InstructorProfile.user_id == reviewer_user.id)
                    )
                    instructor_profile = instructor_result.scalar_one_or_none()
                    if instructor_profile:
                        review_dict["reviewer_name"] = instructor_profile.display_name

        review_list.append(review_dict)

    return {
        "items": review_list,
        "total": len(reviews),
        "average_rating": float(avg_rating) if avg_rating else 0,
    }


@router.get("/reviews/written")
async def get_written_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews written by the current user."""
    query = (
        select(Review)
        .where(Review.reviewer_user_id == current_user.id)
        .order_by(Review.created_at.desc())
    )
    result = await db.execute(query)
    reviews = result.scalars().all()

    review_list = []
    for review in reviews:
        review_dict = {
            "id": str(review.id),
            "application_id": str(review.application_id) if review.application_id else None,
            "contract_id": str(review.contract_id) if review.contract_id else None,
            "rating": review.rating,
            "comment": review.comment,
            "time_punctuality": review.time_punctuality,
            "professionalism": review.professionalism,
            "would_rehire": review.would_rehire,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "reviewee_name": None,
            "job_date": None,
        }

        # Enrich with application/job data
        if review.application_id:
            app_result = await db.execute(
                select(Application)
                .options(joinedload(Application.job_post))
                .where(Application.id == review.application_id)
            )
            app = app_result.unique().scalar_one_or_none()
            if app and app.job_post:
                review_dict["job_date"] = app.job_post.date.isoformat()

        # Get reviewee name
        if current_user.role == UserRole.INSTRUCTOR:
            if review.reviewee_studio_id:
                studio_result = await db.execute(
                    select(StudioProfile).where(StudioProfile.id == review.reviewee_studio_id)
                )
                studio = studio_result.scalar_one_or_none()
                if studio:
                    review_dict["reviewee_name"] = studio.business_name
        else:
            if review.reviewee_instructor_id:
                instructor_result = await db.execute(
                    select(InstructorProfile).where(InstructorProfile.id == review.reviewee_instructor_id)
                )
                instructor = instructor_result.scalar_one_or_none()
                if instructor:
                    review_dict["reviewee_name"] = instructor.display_name

        review_list.append(review_dict)

    return {
        "items": review_list,
        "total": len(reviews),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _verify_party(
    db: AsyncSession, current_user: User, application: Application
) -> None:
    """Verify the current user is either the instructor or studio on this application."""
    job_post = application.job_post

    if current_user.role == UserRole.INSTRUCTOR:
        result = await db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == current_user.id)
        )
        instructor_id = result.scalar_one_or_none()
        if not instructor_id or str(application.instructor_id) != str(instructor_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Not a party to this application"},
            )
    else:
        result = await db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == current_user.id)
        )
        studio_id = result.scalar_one_or_none()
        if not studio_id or not job_post or str(job_post.studio_id) != str(studio_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Not a party to this application"},
            )
