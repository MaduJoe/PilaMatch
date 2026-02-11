from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.offer import OfferCreate, OfferResponse, OfferListResponse
from app.services.offer import OfferService

router = APIRouter()


@router.post("", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    data: OfferCreate,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Create an offer (studio only)."""
    service = OfferService(db)
    studio_id = await service.get_studio_profile_id(current_user.id)

    if not studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Studio profile not found"},
        )

    try:
        offer = await service.create(studio_id, data)
        return OfferResponse.model_validate(offer)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "OFFER_FAILED", "message": str(e)},
        )


@router.get("/me", response_model=OfferListResponse)
async def get_my_offers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's offers."""
    service = OfferService(db)
    offers = await service.get_by_user(current_user.id, current_user.role)

    return OfferListResponse(
        items=[OfferResponse.model_validate(o) for o in offers],
        total=len(offers),
    )


@router.post("/{offer_id}/accept", response_model=OfferResponse)
async def accept_offer(
    offer_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Accept an offer (instructor only)."""
    service = OfferService(db)
    instructor_id = await service.get_instructor_profile_id(current_user.id)

    if not instructor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    try:
        offer = await service.accept(offer_id, instructor_id)
        return OfferResponse.model_validate(offer)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to accept this offer"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "OFFER_NOT_PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "OFFER_NOT_PENDING", "message": "Offer is not pending"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ACCEPT_FAILED", "message": error_msg},
        )


@router.post("/{offer_id}/reject", response_model=OfferResponse)
async def reject_offer(
    offer_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Reject an offer (instructor only)."""
    service = OfferService(db)
    instructor_id = await service.get_instructor_profile_id(current_user.id)

    if not instructor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROFILE_NOT_FOUND", "message": "Instructor profile not found"},
        )

    try:
        offer = await service.reject(offer_id, instructor_id)
        return OfferResponse.model_validate(offer)
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized to reject this offer"},
        )
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "OFFER_NOT_PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "OFFER_NOT_PENDING", "message": "Offer is not pending"},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REJECT_FAILED", "message": error_msg},
        )
