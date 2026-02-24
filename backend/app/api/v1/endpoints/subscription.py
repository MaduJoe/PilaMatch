"""Subscription API endpoints for Premium membership."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.models import User
from app.schemas.subscription import (
    SubscriptionStatusResponse,
    UpgradeInitializeRequest,
    UpgradeInitializeResponse,
    PaymentConfirmRequest,
    PaymentConfirmResponse,
    CancelSubscriptionRequest,
    CancelSubscriptionResponse,
    SubscriptionHistoryResponse,
    SubscriptionHistoryItem,
    SubscriptionWebhookRequest,
    SubscriptionResponse,
    BillingKeyRegisterRequest,
    BillingKeyRegisterResponse,
    BillingMethodResponse,
    BankTransferUpgradeRequest,
    BankTransferUpgradeResponse,
    RenewAllRequest,
)
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=SubscriptionStatusResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's subscription status."""
    service = SubscriptionService(db)
    subscription = await service.get_user_subscription(str(current_user.id))

    sub_response = None
    if subscription:
        sub_response = SubscriptionResponse.model_validate(subscription)
        sub_response.has_billing_key = bool(subscription.toss_billing_key)

    return SubscriptionStatusResponse(
        has_subscription=subscription is not None,
        membership_tier=current_user.membership_tier,
        subscription=sub_response,
    )


@router.post("/upgrade", response_model=UpgradeInitializeResponse)
async def initialize_premium_upgrade(
    req: UpgradeInitializeRequest = UpgradeInitializeRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initialize premium subscription upgrade."""
    import uuid as _uuid

    if current_user.membership_tier == "premium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_PREMIUM", "message": "이미 프리미엄 회원입니다"},
        )

    service = SubscriptionService(db)

    try:
        # Create or get subscription
        subscription = await service.create_subscription(str(current_user.id))

        # Initialize payment
        order_id, amount = await service.initialize_subscription_payment(
            subscription.id
        )

        # Generate customer_key for billing registration
        customer_key = None
        if req.payment_method == "billing":
            customer_key = f"cust_{_uuid.uuid4().hex[:16]}"

        return UpgradeInitializeResponse(
            order_id=order_id,
            amount=float(amount),
            subscription_id=subscription.id,
            client_key=settings.TOSS_CLIENT_KEY or "test_ck_mock",
            customer_key=customer_key,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPGRADE_ERROR", "message": str(e)},
        )


@router.post("/confirm", response_model=PaymentConfirmResponse)
async def confirm_subscription_payment(
    request: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm subscription payment after TossPayments."""
    service = SubscriptionService(db)

    try:
        payment = await service.confirm_subscription_payment(
            request.payment_key, request.order_id
        )

        return PaymentConfirmResponse(
            success=True,
            subscription_id=payment.subscription_id,
            message="프리미엄 회원이 되신 것을 축하합니다!",
            next_billing_date=payment.subscription.next_billing_date,
        )
    except ValueError as e:
        logger.error(f"Payment confirmation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PAYMENT_ERROR", "message": str(e)},
        )


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel active premium subscription."""
    if current_user.membership_tier != "premium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_PREMIUM", "message": "프리미엄 회원이 아닙니다"},
        )

    service = SubscriptionService(db)

    try:
        history = await service.cancel_subscription(
            str(current_user.id), request.reason
        )

        # Extract deposit refund amount from history note
        deposit_refunded = 0
        if "Deposit refunded:" in history.note:
            try:
                refund_str = history.note.split("Deposit refunded: ")[1].split()[0]
                deposit_refunded = float(refund_str)
            except:
                pass

        return CancelSubscriptionResponse(
            success=True,
            message="프리미엄 구독이 취소되었습니다. 보증금이 환불됩니다.",
            deposit_refunded=deposit_refunded,
            effective_date=history.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANCEL_ERROR", "message": str(e)},
        )


@router.get("/history", response_model=SubscriptionHistoryResponse)
async def get_subscription_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get subscription change history for current user."""
    service = SubscriptionService(db)
    history = await service.get_subscription_history(str(current_user.id))

    return SubscriptionHistoryResponse(
        history=[
            SubscriptionHistoryItem.model_validate(item) for item in history
        ],
        total=len(history),
    )


@router.post("/webhooks/payment")
async def handle_subscription_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle TossPayments subscription webhooks with signature verification."""
    # Verify webhook signature (same pattern as payment webhook)
    body = await request.body()
    signature = request.headers.get("X-Toss-Signature", "")

    from app.services.payment import PaymentService
    payment_service = PaymentService(db)
    if not payment_service.verify_webhook_signature(body, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_SIGNATURE", "message": "Webhook signature verification failed"},
        )

    service = SubscriptionService(db)

    try:
        data = await request.json()
        event_type = data.get("event_type", "")
        event_data = data.get("data", {})

        # Handle different webhook events
        if event_type == "PAYMENT.COMPLETED":
            # Auto-renewal successful
            payment_key = event_data.get("paymentKey")
            order_id = event_data.get("orderId")
            if order_id and order_id.startswith("RENEW-"):
                # This is an auto-renewal
                logger.info(f"Processing auto-renewal webhook for {order_id}")
                # Update payment status in database
                # (handled by service.confirm_subscription_payment)

        elif event_type == "PAYMENT.FAILED":
            # Payment failed
            payment_id = event_data.get("paymentId")
            failure_reason = event_data.get("failureReason", "Unknown")
            if payment_id:
                await service.handle_payment_failure(payment_id, failure_reason)

        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            # Subscription cancelled from TossPayments side
            subscription_id = event_data.get("subscriptionId")
            if subscription_id:
                # Find user and cancel subscription
                logger.info(f"Processing cancellation webhook for {subscription_id}")
                # TODO: Implement reverse lookup from toss_billing_key

        return {"success": True}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        # Return success to prevent retries for malformed webhooks
        return {"success": True, "error": str(e)}


# --- Billing Key Endpoints ---


@router.post("/billing/register", response_model=BillingKeyRegisterResponse)
async def register_billing_key(
    request: BillingKeyRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register billing key from Toss auth and optionally charge first month."""
    service = SubscriptionService(db)

    try:
        result = await service.register_billing_key(
            user_id=str(current_user.id),
            auth_key=request.auth_key,
            customer_key=request.customer_key,
        )
        return BillingKeyRegisterResponse(
            success=True,
            card_last_four=result["card_last_four"],
            card_company=result["card_company"],
            message="카드가 등록되고 첫 달 결제가 완료되었습니다.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BILLING_ERROR", "message": str(e)},
        )


@router.get("/billing", response_model=BillingMethodResponse)
async def get_billing_method(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get registered billing method info."""
    service = SubscriptionService(db)
    result = await service.get_billing_method(str(current_user.id))
    return BillingMethodResponse(**result)


@router.delete("/billing")
async def remove_billing_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove billing key (disables auto-renewal)."""
    service = SubscriptionService(db)
    try:
        await service.remove_billing_key(str(current_user.id))
        return {"success": True, "message": "결제수단이 삭제되었습니다. 자동갱신이 해제됩니다."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BILLING_ERROR", "message": str(e)},
        )


# --- Bank Transfer Endpoints ---


@router.post("/upgrade/bank-transfer", response_model=BankTransferUpgradeResponse)
async def initialize_bank_transfer_upgrade(
    request: BankTransferUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initialize bank transfer for premium upgrade."""
    if current_user.membership_tier == "premium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ALREADY_PREMIUM", "message": "이미 프리미엄 회원입니다"},
        )

    service = SubscriptionService(db)
    try:
        result = await service.initialize_bank_transfer(
            user_id=str(current_user.id),
            depositor_name=request.depositor_name,
        )
        return BankTransferUpgradeResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BANK_TRANSFER_ERROR", "message": str(e)},
        )


# --- Auto-Renewal Endpoint ---


@router.post("/renew-all")
async def trigger_renewal(
    request: RenewAllRequest,
    db: AsyncSession = Depends(get_db),
):
    """Trigger auto-renewal for all due subscriptions (CRON_SECRET protected)."""
    if not settings.CRON_SECRET or request.cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Invalid cron secret"},
        )

    service = SubscriptionService(db)
    due = await service.check_renewals_due()

    results = {"processed": 0, "success": 0, "failed": 0}
    for sub in due:
        results["processed"] += 1
        try:
            payment = await service.process_auto_renewal(sub.id)
            if payment:
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            logger.error(f"Renewal failed for {sub.id}: {e}")
            results["failed"] += 1

    return results