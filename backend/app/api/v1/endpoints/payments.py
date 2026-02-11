from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import require_role
from app.models import User, UserRole
from app.schemas.payment import (
    PaymentInitResponse,
    PaymentConfirmRequest,
    PaymentWebhookRequest,
    PaymentResponse,
)
from app.services.payment import PaymentService

router = APIRouter()


@router.post("/contracts/{contract_id}/payments", response_model=PaymentInitResponse)
async def initialize_payment(
    contract_id: UUID,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a payment for a contract (studio only)."""
    service = PaymentService(db)

    try:
        order_id, amount, order_name = await service.initialize_payment(
            contract_id, current_user.id
        )
        return PaymentInitResponse(
            order_id=order_id,
            amount=amount,
            order_name=order_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_INIT_FAILED", "message": str(e)},
        )


@router.post("/payments/confirm", response_model=PaymentResponse)
async def confirm_payment(
    data: PaymentConfirmRequest,
    current_user: User = Depends(require_role(UserRole.STUDIO)),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a payment after TossPayments redirect."""
    service = PaymentService(db)

    try:
        payment = await service.confirm_payment(data)
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_CONFIRM_FAILED", "message": str(e)},
        )


@router.post("/payments/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle webhook from TossPayments."""
    # In production, verify webhook signature
    try:
        data = await request.json()
        event_type = data.get("eventType", "")
        event_data = data.get("data", {})

        service = PaymentService(db)
        await service.handle_webhook(event_type, event_data)

        return {"status": "ok"}
    except Exception as e:
        # Log error but return 200 to prevent retries
        return {"status": "error", "message": str(e)}
