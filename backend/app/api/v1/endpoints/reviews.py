from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.review import ReviewService

router = APIRouter()


@router.post("/contracts/{contract_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    contract_id: UUID,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a review for a completed contract."""
    service = ReviewService(db)

    try:
        review = await service.create_review(
            contract_id, current_user.id, current_user.role, data
        )
        return ReviewResponse.model_validate(review)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to review this contract"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REVIEW_FAILED", "message": str(e)},
        )


@router.get("/contracts/{contract_id}/reviews/my")
async def get_my_review(
    contract_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's review for a specific contract."""
    service = ReviewService(db)
    review = await service.get_user_review_for_contract(contract_id, current_user.id)
    if review:
        return ReviewResponse.model_validate(review)
    # Return 404 instead of None for clearer client handling
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "REVIEW_NOT_FOUND", "message": "Review not found for this contract"}
    )


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


@router.get("/reviews/received")
async def get_received_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reviews received by the current user."""
    from app.models import InstructorProfile, StudioProfile, UserRole
    from sqlalchemy import select

    service = ReviewService(db)

    # Determine user type and get appropriate profile
    if current_user.role == UserRole.INSTRUCTOR:
        # Get instructor profile
        from sqlalchemy import select
        result = await db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"}
            )

        reviews, avg_rating = await service.get_reviews_for_instructor(profile.id)

    elif current_user.role == UserRole.STUDIO:
        # Get studio profile
        from sqlalchemy import select
        result = await db.execute(
            select(StudioProfile).where(StudioProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"}
            )

        reviews, avg_rating = await service.get_reviews_for_studio(profile.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ROLE", "message": "Invalid user role"}
        )

    # Format response with reviewer information
    review_list = []
    for review in reviews:
        review_dict = {
            "id": str(review.id),
            "contract_id": str(review.contract_id),
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "reviewer_name": None  # Will be populated below
        }

        # Get reviewer name based on who wrote the review
        if review.reviewer_user_id:
            # Get reviewer user
            from app.models import User
            reviewer_result = await db.execute(
                select(User).where(User.id == review.reviewer_user_id)
            )
            reviewer_user = reviewer_result.scalar_one_or_none()

            if reviewer_user:
                if current_user.role == UserRole.INSTRUCTOR:
                    # Reviews are from studios
                    studio_result = await db.execute(
                        select(StudioProfile).where(StudioProfile.user_id == reviewer_user.id)
                    )
                    studio_profile = studio_result.scalar_one_or_none()
                    if studio_profile:
                        review_dict["reviewer_name"] = studio_profile.business_name
                else:
                    # Reviews are from instructors
                    instructor_result = await db.execute(
                        select(InstructorProfile).where(InstructorProfile.user_id == reviewer_user.id)
                    )
                    instructor_profile = instructor_result.scalar_one_or_none()
                    if instructor_profile:
                        review_dict["reviewer_name"] = instructor_profile.display_name

        review_list.append(review_dict)

    return {
        "reviews": review_list,
        "average_rating": float(avg_rating) if avg_rating else 0,
        "total_count": len(reviews)
    }


@router.get("/reviews/written")
async def get_written_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all reviews written by the current user."""
    from sqlalchemy import select
    from app.models import Review, Contract, InstructorProfile, StudioProfile, UserRole

    # Query all reviews written by the current user with contract details
    query = (
        select(Review)
        .where(Review.reviewer_user_id == current_user.id)
        .order_by(Review.created_at.desc())
    )
    result = await db.execute(query)
    reviews = result.scalars().all()

    # Format response with contract and reviewee information
    review_list = []
    for review in reviews:
        # Get contract details
        contract_result = await db.execute(
            select(Contract).where(Contract.id == review.contract_id)
        )
        contract = contract_result.scalar_one_or_none()

        review_dict = {
            "id": str(review.id),
            "contract_id": str(review.contract_id),
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat() if review.created_at else None,
            "contract_date": contract.date.isoformat() if contract and contract.date else None,
            "contract_amount": float(contract.total_amount) if contract else None,
            "reviewee_name": None  # Will be populated below
        }

        # Get reviewee name based on current user role
        if current_user.role == UserRole.INSTRUCTOR:
            # Instructor wrote review for studio
            if review.reviewee_studio_id:
                studio_result = await db.execute(
                    select(StudioProfile).where(StudioProfile.id == review.reviewee_studio_id)
                )
                studio = studio_result.scalar_one_or_none()
                if studio:
                    review_dict["reviewee_name"] = studio.business_name
        else:
            # Studio wrote review for instructor
            if review.reviewee_instructor_id:
                instructor_result = await db.execute(
                    select(InstructorProfile).where(InstructorProfile.id == review.reviewee_instructor_id)
                )
                instructor = instructor_result.scalar_one_or_none()
                if instructor:
                    review_dict["reviewee_name"] = instructor.display_name

        review_list.append(review_dict)

    return {
        "reviews": review_list,
        "total_count": len(reviews)
    }
