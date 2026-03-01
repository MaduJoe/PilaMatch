"""Payment confirmation endpoints (v4.0)."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.models import User, UserRole
from app.schemas.payment_confirmation import (
    MarkPaidRequest,
    DisputePaymentRequest,
    PaymentConfirmationResponse,
    PaymentConfirmationListResponse,
)
from app.services import payment_confirmation as pc_service

router = APIRouter()


@router.post(
    "/applications/{application_id}/mark-paid",
    response_model=PaymentConfirmationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def mark_paid(
    application_id: UUID,
    data: MarkPaidRequest,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Center marks payment as sent for an accepted application."""
    try:
        confirmation = await pc_service.mark_paid(
            db, application_id, current_user.id, data.amount
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MARK_PAID_FAILED", "message": str(e)},
        )
    return PaymentConfirmationResponse.model_validate(confirmation)


@router.post(
    "/payment-confirmations/{confirmation_id}/confirm",
    response_model=PaymentConfirmationResponse,
)
async def confirm_payment(
    confirmation_id: UUID,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Instructor confirms they received payment."""
    try:
        confirmation = await pc_service.confirm_payment(
            db, confirmation_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONFIRM_FAILED", "message": str(e)},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized"},
        )
    return PaymentConfirmationResponse.model_validate(confirmation)


@router.post(
    "/payment-confirmations/{confirmation_id}/dispute",
    response_model=PaymentConfirmationResponse,
)
async def dispute_payment(
    confirmation_id: UUID,
    data: DisputePaymentRequest,
    current_user: User = Depends(require_role(UserRole.INSTRUCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """Instructor disputes non-payment."""
    try:
        confirmation = await pc_service.dispute_payment(
            db, confirmation_id, current_user.id, data.reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DISPUTE_FAILED", "message": str(e)},
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "Not authorized"},
        )
    return PaymentConfirmationResponse.model_validate(confirmation)


@router.get("/payment-confirmations/me", response_model=PaymentConfirmationListResponse)
async def get_my_payment_confirmations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment confirmations involving the current user."""
    records = await pc_service.get_by_user(db, current_user.id)
    return PaymentConfirmationListResponse(
        items=[PaymentConfirmationResponse.model_validate(r) for r in records],
    )
