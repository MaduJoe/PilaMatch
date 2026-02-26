import logging
from decimal import Decimal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.core.deps import require_role, get_current_user
from app.core.config import settings
from app.models import User, UserRole
from app.schemas.payment import (
    PaymentInitResponse,
    PaymentConfirmRequest,
    PaymentWebhookRequest,
    PaymentResponse,
    PaymentCancelRequest,
    PaymentCancelResponse,
    PaymentDetailResponse,
)
from app.services.payment import PaymentService
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)
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


@router.get("/payments/{payment_id}", response_model=PaymentDetailResponse)
@limiter.limit("30/minute")
async def get_payment_detail(
    request: Request,
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get payment details including cancellation history."""
    service = PaymentService(db)
    payment = await service.get_payment_with_cancellations(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"},
        )

    # Only the payer or admin can view payment details
    if payment.payer_user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Not authorized to view this payment"},
        )

    return PaymentDetailResponse.model_validate(payment)


@router.post("/payments/{payment_id}/cancel", response_model=PaymentCancelResponse)
@limiter.limit("5/minute")
async def cancel_payment(
    request: Request,
    payment_id: UUID,
    cancel_data: PaymentCancelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel or partially cancel a payment."""
    service = PaymentService(db)
    payment = await service.get_payment_by_id(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"},
        )

    # Only the payer or admin can cancel payments
    if payment.payer_user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Not authorized to cancel this payment"},
        )

    try:
        cancellation = await service.cancel_payment(
            payment_id=payment_id,
            cancel_request=cancel_data,
            requested_by_user_id=current_user.id,
        )
        return PaymentCancelResponse.model_validate(cancellation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_CANCEL_FAILED", "message": str(e)},
        )


@router.post("/payments/webhook")
async def payment_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle webhook from TossPayments with v2 HMAC-SHA256 signature verification."""
    body = await request.body()

    # v2 webhook headers
    signature = request.headers.get("tosspayments-webhook-signature", "")
    transmission_time = request.headers.get("tosspayments-webhook-transmission-time", "")
    transmission_id = request.headers.get("tosspayments-webhook-transmission-id", "")

    # Fallback to v1 header if v2 headers not present
    if not signature:
        signature = request.headers.get("X-Toss-Signature", "")

    service = PaymentService(db)

    if not service.verify_webhook_signature(body, signature, transmission_time, transmission_id):
        logger.warning(
            f"Webhook signature verification failed: "
            f"ip={request.client.host if request.client else 'unknown'}, "
            f"transmission_id={transmission_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_SIGNATURE", "message": "Webhook signature verification failed"},
        )

    try:
        data = await request.json()
        event_type = data.get("eventType", "")
        event_data = data.get("data", {})

        await service.handle_webhook(event_type, event_data, transmission_id=transmission_id or None)

        return {"status": "ok"}
    except Exception as e:
        # Log error but return 200 to prevent retries
        logger.error(f"Webhook processing error: {e}")
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
    """Handle TossPayments success redirect -> confirm payment -> redirect to frontend."""
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
@limiter.limit("5/minute")
async def payment_fail_redirect(
    request: Request,
    code: str = "",
    message: str = "",
    orderId: str = "",
    type: str = "contract",
):
    """Handle TossPayments failure redirect -> redirect to frontend with error info."""
    frontend_url = settings.FRONTEND_URL
    error_msg = quote(message) if message else quote(code)
    payment_type = type if type in ("contract", "subscription") else "contract"
    return RedirectResponse(
        url=f"{frontend_url}?payment_result=fail&error_message={error_msg}&type={payment_type}",
        status_code=303,
    )
