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
