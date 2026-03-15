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
    BankTransferConfirmRequest,
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
    """Get current user's subscription status.

    Access is determined by end_date (current_period_end), not status alone.
    A cancelled subscription still grants access until end_date.
    """
    from datetime import datetime
    from sqlalchemy import select as sa_select
    from app.models.subscription import Subscription

    # Find any subscription (including cancelled with remaining access)
    service = SubscriptionService(db)
    subscription = await service.get_user_subscription(str(current_user.id))

    # Also check cancelled subscriptions still within their period
    if not subscription:
        result = await db.execute(
            sa_select(Subscription).where(Subscription.user_id == current_user.id)
        )
        any_sub = result.scalar_one_or_none()
        if any_sub and any_sub.end_date and any_sub.end_date > datetime.utcnow():
            subscription = any_sub

    sub_response = None
    has_access = False
    if subscription:
        sub_response = SubscriptionResponse.model_validate(subscription)
        sub_response.has_billing_key = bool(subscription.toss_billing_key)
        # Access check: end_date >= now (not status)
        has_access = (
            subscription.end_date is not None
            and subscription.end_date > datetime.utcnow()
        )

    # Also check membership_tier as fallback (admin-set premium)
    if current_user.membership_tier == "premium":
        has_access = True

    return SubscriptionStatusResponse(
        has_subscription=has_access,
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
    from datetime import datetime as dt
    from sqlalchemy import select as sa_select
    from app.models.subscription import Subscription

    service = SubscriptionService(db)

    # Find subscription (any status)
    result = await db.execute(
        sa_select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()

    # Already cancelled but still within period
    if sub and sub.status == "cancelled" and sub.end_date and sub.end_date > dt.utcnow():
        return CancelSubscriptionResponse(
            success=True,
            message=f"이미 해지되었습니다. {sub.end_date.strftime('%Y-%m-%d')}까지 프리미엄 혜택을 이용할 수 있습니다.",
            deposit_refunded=0,
            effective_date=sub.end_date,
        )

    # Inactive (re-subscribe pending, not yet confirmed)
    if sub and sub.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_ACTIVE", "message": "활성화 대기 중인 구독은 해지할 수 없습니다. 입금 확인 후 해지해주세요."},
        )

    # No subscription at all
    if not sub or (sub.status != "active" and current_user.membership_tier != "premium"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "NOT_PREMIUM", "message": "프리미엄 회원이 아닙니다"},
        )

    try:
        history = await service.cancel_subscription(
            str(current_user.id), request.reason
        )

        deposit_refunded = 0
        if history.note and "Deposit refunded:" in history.note:
            try:
                refund_str = history.note.split("Deposit refunded: ")[1].split()[0]
                deposit_refunded = float(refund_str)
            except:
                pass

        # Refresh sub to get updated end_date
        await db.refresh(sub)
        end_str = sub.end_date.strftime('%Y-%m-%d') if sub and sub.end_date else "즉시"
        return CancelSubscriptionResponse(
            success=True,
            message=f"구독이 해지되었습니다. {end_str}까지 프리미엄 혜택을 이용할 수 있습니다.",
            deposit_refunded=deposit_refunded,
            effective_date=sub.end_date if sub and sub.end_date else history.created_at,
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

    from app.utils.webhook_signature import verify_toss_webhook_signature
    if not verify_toss_webhook_signature(body, signature):
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
            billing_key = event_data.get("billingKey")
            if billing_key:
                subscription = await service.get_subscription_by_billing_key(billing_key)
                if subscription:
                    logger.info(f"Processing cancellation webhook for billing_key {billing_key}")
                    await service.cancel_subscription(
                        str(subscription.user_id),
                        reason="Cancelled via TossPayments webhook",
                    )
                else:
                    logger.warning(f"No subscription found for billing_key {billing_key}")

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
    # Block only if subscription is currently active (not cancelled)
    if current_user.membership_tier == "premium":
        from sqlalchemy import select as sa_select
        from app.models.subscription import Subscription
        result = await db.execute(
            sa_select(Subscription).where(Subscription.user_id == current_user.id)
        )
        existing = result.scalar_one_or_none()
        if existing and existing.status == "active":
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


# --- Admin: Bank Transfer Confirm ---


@router.post("/confirm-bank-transfer")
async def confirm_bank_transfer(
    request: BankTransferConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin confirms bank transfer and activates subscription."""
    service = SubscriptionService(db)
    try:
        payment = await service.confirm_bank_transfer(
            payment_id=request.payment_id,
            confirmed_amount=request.confirmed_amount,
            admin_user_id=str(current_user.id),
        )
        return {
            "message": "구독이 활성화되었습니다",
            "payment_id": str(payment.id),
            "status": payment.status,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CONFIRM_ERROR", "message": str(e)},
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