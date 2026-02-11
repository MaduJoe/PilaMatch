from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.review import ReviewCreate, ReviewResponse
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
