from decimal import Decimal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.core.deps import require_role
from app.core.config import settings
from app.models import User, UserRole
from app.schemas.payment import (
    PaymentInitResponse,
    PaymentConfirmRequest,
    PaymentWebhookRequest,
    PaymentResponse,
)
from app.services.payment import PaymentService
from app.services.subscription import SubscriptionService

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/contracts/{contract_id}/payments", response_model=PaymentInitResponse)
@limiter.limit("10/minute")
async def initialize_payment(
    request: Request,
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
@limiter.limit("10/minute")
async def confirm_payment(
    request: Request,
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
    """Handle webhook from TossPayments with HMAC-SHA256 signature verification."""
    body = await request.body()
    signature = request.headers.get("X-Toss-Signature", "")

    service = PaymentService(db)

    if not service.verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_SIGNATURE", "message": "Webhook signature verification failed"},
        )

    try:
        data = await request.json()
        event_type = data.get("eventType", "")
        event_data = data.get("data", {})

        await service.handle_webhook(event_type, event_data)

        return {"status": "ok"}
    except Exception as e:
        # Log error but return 200 to prevent retries
        return {"status": "error", "message": str(e)}


@router.get("/payments/success")
@limiter.limit("5/minute")
async def payment_success_redirect(
    request: Request,
    paymentKey: str,
    orderId: str,
    amount: str,
    type: str = "contract",
    db: AsyncSession = Depends(get_db),
):
    """Handle TossPayments success redirect -> confirm payment -> redirect to Streamlit."""
    frontend_url = settings.FRONTEND_URL

    try:
        if type == "subscription":
            service = SubscriptionService(db)
            await service.confirm_subscription_payment(paymentKey, orderId)
            return RedirectResponse(
                url=f"{frontend_url}?payment_result=success&type=subscription",
                status_code=303,
            )
        else:
            # Contract payment
            service = PaymentService(db)
            confirm_data = PaymentConfirmRequest(
                payment_key=paymentKey,
                order_id=orderId,
                amount=Decimal(amount),
            )
            await service.confirm_payment(confirm_data)
            return RedirectResponse(
                url=f"{frontend_url}?payment_result=success&type=contract",
                status_code=303,
            )
    except Exception as e:
        error_msg = quote(str(e))
        payment_type = type if type in ("contract", "subscription") else "contract"
        return RedirectResponse(
            url=f"{frontend_url}?payment_result=fail&error_message={error_msg}&type={payment_type}",
            status_code=303,
        )


@router.get("/payments/fail")
async def payment_fail_redirect(
    code: str = "",
    message: str = "",
    orderId: str = "",
    type: str = "contract",
):
    """Handle TossPayments failure redirect -> redirect to Streamlit with error info."""
    frontend_url = settings.FRONTEND_URL
    error_msg = quote(message) if message else quote(code)
    payment_type = type if type in ("contract", "subscription") else "contract"
    return RedirectResponse(
        url=f"{frontend_url}?payment_result=fail&error_message={error_msg}&type={payment_type}",
        status_code=303,
    )
