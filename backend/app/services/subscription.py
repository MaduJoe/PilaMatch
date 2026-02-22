"""Subscription service for Premium membership management."""

import base64
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple
import uuid

import httpx

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    User, Subscription, SubscriptionPayment, SubscriptionHistory,
    SubscriptionStatus, SubscriptionPaymentStatus, SubscriptionChangeReason,
    MembershipTier
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing premium subscriptions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.monthly_price = Decimal("9900")  # 9,900 KRW per month

    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Get active subscription for a user."""
        result = await self.db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE.value,
                        SubscriptionStatus.INACTIVE.value
                    ])
                )
            )
            .options(selectinload(Subscription.payments))
        )
        return result.scalar_one_or_none()

    async def create_subscription(self, user_id: str) -> Subscription:
        """Create a new premium subscription (inactive until payment)."""
        # Check if user already has a subscription
        existing = await self.get_user_subscription(user_id)
        if existing:
            if existing.status == SubscriptionStatus.ACTIVE.value:
                raise ValueError("User already has an active subscription")
            # Reuse inactive subscription
            return existing

        # Create new subscription
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tier="premium",
            status=SubscriptionStatus.INACTIVE.value,
            monthly_amount=self.monthly_price,
            auto_renew=True,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        logger.info(f"Created subscription {subscription.id} for user {user_id}")
        return subscription

    async def initialize_subscription_payment(
        self, subscription_id: str
    ) -> Tuple[str, Decimal]:
        """Initialize payment for subscription activation."""
        # Get subscription
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status == SubscriptionStatus.ACTIVE.value:
            raise ValueError("Subscription is already active")

        # Create payment record
        order_id = f"SUB-{uuid.uuid4().hex[:16].upper()}"
        payment = SubscriptionPayment(
            id=str(uuid.uuid4()),
            subscription_id=subscription_id,
            amount=self.monthly_price,
            status=SubscriptionPaymentStatus.PENDING.value,
            due_date=datetime.utcnow() + timedelta(hours=1),  # 1 hour to complete
            order_id=order_id,
            retry_count=0,
        )
        self.db.add(payment)
        await self.db.commit()

        logger.info(f"Initialized payment {order_id} for subscription {subscription_id}")
        return order_id, self.monthly_price

    async def confirm_subscription_payment(
        self, payment_key: str, order_id: str
    ) -> SubscriptionPayment:
        """Confirm payment and activate subscription."""
        # Get payment record
        result = await self.db.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.order_id == order_id)
            .options(selectinload(SubscriptionPayment.subscription))
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError("Payment not found")

        if payment.status == SubscriptionPaymentStatus.COMPLETED.value:
            logger.warning(f"Payment {order_id} already completed")
            return payment

        # Verify payment with TossPayments API
        await self._call_toss_confirm(payment_key, order_id, int(payment.amount))

        # Update payment
        payment.status = SubscriptionPaymentStatus.COMPLETED.value
        payment.toss_payment_key = payment_key
        payment.payment_date = datetime.utcnow()

        # Activate subscription
        subscription = payment.subscription
        now = datetime.utcnow()
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=30)
        subscription.next_billing_date = subscription.end_date
        subscription.billing_cycle_day = now.day

        # Update user's membership tier
        await self.db.execute(
            update(User)
            .where(User.id == subscription.user_id)
            .values(membership_tier=MembershipTier.PREMIUM.value)
        )

        # Record in history
        history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            user_id=subscription.user_id,
            old_tier=MembershipTier.FREE.value,
            new_tier=MembershipTier.PREMIUM.value,
            reason=SubscriptionChangeReason.UPGRADE.value,
            note="Premium subscription activated",
            payment_id=payment.id,
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Activated subscription {subscription.id} with payment {order_id}")
        return payment

    async def _call_toss_confirm(self, payment_key: str, order_id: str, amount: int) -> dict:
        """Call TossPayments confirm API for subscription payment."""
        if not settings.TOSS_SECRET_KEY:
            # Mock for development when no secret key configured
            return {"paymentKey": payment_key, "orderId": order_id, "status": "DONE", "method": "카드"}

        secret_key = settings.TOSS_SECRET_KEY + ":"
        encoded_key = base64.b64encode(secret_key.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tosspayments.com/v1/payments/confirm",
                headers={
                    "Authorization": f"Basic {encoded_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "paymentKey": payment_key,
                    "orderId": order_id,
                    "amount": amount,
                },
            )
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(error_data.get("message", "Subscription payment confirmation failed"))
            return response.json()

    async def cancel_subscription(
        self, user_id: str, reason: Optional[str] = None
    ) -> SubscriptionHistory:
        """Cancel active subscription and refund deposit if any."""
        # Get active subscription
        subscription = await self.get_user_subscription(user_id)
        if not subscription or subscription.status != SubscriptionStatus.ACTIVE.value:
            raise ValueError("No active subscription found")

        # Get user for deposit balance
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Mark subscription as cancelled
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.cancelled_at = datetime.utcnow()
        subscription.cancellation_reason = reason
        subscription.auto_renew = False

        # Downgrade user to free tier
        user.membership_tier = MembershipTier.FREE.value

        # TODO: Process deposit refund if user has deposit balance
        deposit_refunded = Decimal("0")
        if user.deposit_balance > 0:
            deposit_refunded = user.deposit_balance
            # In production, initiate bank transfer via TossPayments
            logger.info(f"Refunding deposit {deposit_refunded} for user {user_id}")
            user.deposit_balance = Decimal("0")

        # Record in history
        history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            old_tier=MembershipTier.PREMIUM.value,
            new_tier=MembershipTier.FREE.value,
            reason=SubscriptionChangeReason.CANCELLATION.value,
            note=f"Subscription cancelled. Reason: {reason}. Deposit refunded: {deposit_refunded}",
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(history)

        logger.info(f"Cancelled subscription {subscription.id} for user {user_id}")
        return history

    async def process_auto_renewal(self, subscription_id: str) -> Optional[SubscriptionPayment]:
        """Process automatic renewal for a subscription.

        Args:
            subscription_id: The ID of the subscription to renew.

        Returns:
            The renewal payment record, or None if renewal could not proceed.

        Raises:
            ValueError: If the subscription is not found.
        """
        # Get subscription
        result = await self.db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        if not subscription:
            raise ValueError("Subscription not found")

        if not subscription.auto_renew:
            logger.info(f"Auto-renewal disabled for subscription {subscription_id}")
            subscription.status = SubscriptionStatus.EXPIRED.value
            await self.db.commit()
            return None

        # Check if billing key exists for auto-charge
        if not subscription.toss_billing_key:
            # No billing key - cannot auto-renew, mark as expired
            logger.warning(
                f"Subscription {subscription_id} has no billing key, cannot auto-renew"
            )
            subscription.status = SubscriptionStatus.EXPIRED.value
            subscription.auto_renew = False

            # Downgrade user to free tier
            await self.db.execute(
                update(User)
                .where(User.id == subscription.user_id)
                .values(membership_tier=MembershipTier.FREE.value)
            )

            # Record in history
            history = SubscriptionHistory(
                id=str(uuid.uuid4()),
                user_id=subscription.user_id,
                old_tier=MembershipTier.PREMIUM.value,
                new_tier=MembershipTier.FREE.value,
                reason=SubscriptionChangeReason.AUTO_RENEW.value,
                note="Auto-renewal failed: no billing key registered",
            )
            self.db.add(history)

            await self.db.commit()
            return None

        # TODO: Implement Toss Billing API auto-charge using subscription.toss_billing_key
        # For now, mark as expired since billing API is not yet integrated
        logger.info(
            f"Subscription {subscription_id} billing API not yet integrated, "
            f"marking as expired"
        )
        subscription.status = SubscriptionStatus.EXPIRED.value
        subscription.auto_renew = False

        # Downgrade user to free tier
        await self.db.execute(
            update(User)
            .where(User.id == subscription.user_id)
            .values(membership_tier=MembershipTier.FREE.value)
        )

        # Record in history
        history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            user_id=subscription.user_id,
            old_tier=MembershipTier.PREMIUM.value,
            new_tier=MembershipTier.FREE.value,
            reason=SubscriptionChangeReason.AUTO_RENEW.value,
            note="Auto-renewal pending: Toss Billing API integration required",
        )
        self.db.add(history)

        await self.db.commit()
        return None

    async def check_renewals_due(self) -> List[Subscription]:
        """Find all subscriptions due for renewal today."""
        today = datetime.utcnow().date()
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE.value,
                    Subscription.auto_renew == True,
                    Subscription.next_billing_date <= today,
                )
            )
        )
        return result.scalars().all()

    async def handle_payment_failure(
        self, payment_id: str, failure_reason: str
    ) -> None:
        """Handle failed subscription payment."""
        result = await self.db.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.id == payment_id)
            .options(selectinload(SubscriptionPayment.subscription))
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return

        payment.status = SubscriptionPaymentStatus.FAILED.value
        payment.failure_reason = failure_reason
        payment.retry_count += 1
        payment.last_retry_at = datetime.utcnow()

        # After 3 retries, suspend subscription
        if payment.retry_count >= 3:
            subscription = payment.subscription
            subscription.status = SubscriptionStatus.SUSPENDED.value

            # Downgrade user
            await self.db.execute(
                update(User)
                .where(User.id == subscription.user_id)
                .values(membership_tier=MembershipTier.FREE.value)
            )

            # Record in history
            history = SubscriptionHistory(
                id=str(uuid.uuid4()),
                user_id=subscription.user_id,
                old_tier=MembershipTier.PREMIUM.value,
                new_tier=MembershipTier.FREE.value,
                reason=SubscriptionChangeReason.SUSPENSION.value,
                note=f"Subscription suspended due to payment failure",
                payment_id=payment_id,
            )
            self.db.add(history)

        await self.db.commit()

    async def get_subscription_history(
        self, user_id: str
    ) -> List[SubscriptionHistory]:
        """Get subscription change history for a user."""
        result = await self.db.execute(
            select(SubscriptionHistory)
            .where(SubscriptionHistory.user_id == user_id)
            .order_by(SubscriptionHistory.created_at.desc())
        )
        return result.scalars().all()

    async def can_user_skip_deposit(self, user_id: str) -> bool:
        """Check if user can skip deposit requirement (Premium users)."""
        result = await self.db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier = result.scalar_one_or_none()
        return tier == MembershipTier.PREMIUM.value

    async def get_membership_tier(self, user_id: str) -> str:
        """Get user's current membership tier."""
        result = await self.db.execute(
            select(User.membership_tier).where(User.id == user_id)
        )
        tier = result.scalar_one_or_none()
        return tier if tier else MembershipTier.FREE.value

    async def is_premium_user(self, user_id: str) -> bool:
        """Check if user has premium membership."""
        tier = await self.get_membership_tier(user_id)
        return tier == MembershipTier.PREMIUM.value