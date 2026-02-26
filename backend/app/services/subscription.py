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

        # Charge using billing key
        order_id = f"RENEW-{uuid.uuid4().hex[:16].upper()}"
        order_name = f"StudioBridge 프리미엄 자동갱신"

        try:
            charge_result = await self._call_toss_billing_charge(
                billing_key=subscription.toss_billing_key,
                customer_key=subscription.toss_customer_key or str(subscription.user_id),
                amount=int(self.monthly_price),
                order_id=order_id,
                order_name=order_name,
            )
        except ValueError as e:
            # Payment failed
            logger.error(f"Auto-renewal charge failed for {subscription_id}: {e}")
            payment = SubscriptionPayment(
                id=str(uuid.uuid4()),
                subscription_id=subscription_id,
                amount=self.monthly_price,
                status=SubscriptionPaymentStatus.FAILED.value,
                due_date=datetime.utcnow(),
                order_id=order_id,
                payment_type="renewal",
                failure_reason=str(e),
                retry_count=0,
            )
            self.db.add(payment)
            await self.db.commit()
            await self.handle_payment_failure(payment.id, str(e))
            return None

        # Success: create payment record
        payment = SubscriptionPayment(
            id=str(uuid.uuid4()),
            subscription_id=subscription_id,
            amount=self.monthly_price,
            status=SubscriptionPaymentStatus.COMPLETED.value,
            due_date=datetime.utcnow(),
            order_id=order_id,
            toss_payment_key=charge_result.get("paymentKey"),
            payment_date=datetime.utcnow(),
            payment_type="renewal",
            retry_count=0,
        )
        self.db.add(payment)

        # Extend subscription
        now = datetime.utcnow()
        subscription.end_date = now + timedelta(days=30)
        subscription.next_billing_date = subscription.end_date

        # Record in history
        history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            user_id=subscription.user_id,
            old_tier=MembershipTier.PREMIUM.value,
            new_tier=MembershipTier.PREMIUM.value,
            reason=SubscriptionChangeReason.AUTO_RENEW.value,
            note=f"Auto-renewal successful. Order: {order_id}",
            payment_id=payment.id,
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Auto-renewal successful for subscription {subscription_id}")
        return payment

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

    # --- Billing Key Methods ---

    def _toss_auth_header(self) -> str:
        """Generate Basic auth header for TossPayments."""
        secret_key = (settings.TOSS_SECRET_KEY or "") + ":"
        return "Basic " + base64.b64encode(secret_key.encode()).decode()

    async def _call_toss_issue_billing_key(
        self, auth_key: str, customer_key: str
    ) -> dict:
        """Issue a billing key via Toss Billing Authorization API."""
        if not settings.TOSS_SECRET_KEY:
            # Mock for development
            return {
                "billingKey": f"mock_billing_{uuid.uuid4().hex[:12]}",
                "customerKey": customer_key,
                "card": {
                    "number": "****1234",
                    "company": "테스트카드",
                },
            }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.tosspayments.com/v1/billing/authorizations/issue",
                headers={
                    "Authorization": self._toss_auth_header(),
                    "Content-Type": "application/json",
                },
                json={
                    "authKey": auth_key,
                    "customerKey": customer_key,
                },
            )
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    error_data.get("message", "빌링키 발급에 실패했습니다")
                )
            return response.json()

    async def _call_toss_billing_charge(
        self,
        billing_key: str,
        customer_key: str,
        amount: int,
        order_id: str,
        order_name: str,
    ) -> dict:
        """Charge using billing key via Toss Billing API."""
        if not settings.TOSS_SECRET_KEY:
            # Mock for development
            return {
                "paymentKey": f"mock_pay_{uuid.uuid4().hex[:12]}",
                "orderId": order_id,
                "status": "DONE",
                "method": "카드",
            }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.tosspayments.com/v1/billing/{billing_key}",
                headers={
                    "Authorization": self._toss_auth_header(),
                    "Content-Type": "application/json",
                },
                json={
                    "customerKey": customer_key,
                    "amount": amount,
                    "orderId": order_id,
                    "orderName": order_name,
                },
            )
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    error_data.get("message", "자동결제 승인에 실패했습니다")
                )
            return response.json()

    async def register_billing_key(
        self, user_id: str, auth_key: str, customer_key: str
    ) -> dict:
        """Register billing key and optionally charge first month."""
        # Get or create subscription
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            subscription = await self.create_subscription(user_id)

        # Issue billing key
        result = await self._call_toss_issue_billing_key(auth_key, customer_key)

        billing_key = result.get("billingKey")
        card_info = result.get("card", {})
        card_number = card_info.get("number", "")
        card_last_four = card_number[-4:] if len(card_number) >= 4 else card_number
        card_company = card_info.get("company", "")

        # Save billing key to subscription
        subscription.toss_billing_key = billing_key
        subscription.toss_customer_key = customer_key
        subscription.card_last_four = card_last_four
        subscription.card_company = card_company
        subscription.payment_method_type = "card"

        await self.db.commit()

        logger.info(f"Registered billing key for user {user_id}")

        # If subscription is not active, charge first month
        if subscription.status != SubscriptionStatus.ACTIVE.value:
            order_id = f"SUB-{uuid.uuid4().hex[:16].upper()}"
            charge_result = await self._call_toss_billing_charge(
                billing_key=billing_key,
                customer_key=customer_key,
                amount=int(self.monthly_price),
                order_id=order_id,
                order_name="StudioBridge 프리미엄 첫 결제",
            )

            # Create payment record and activate
            payment = SubscriptionPayment(
                id=str(uuid.uuid4()),
                subscription_id=subscription.id,
                amount=self.monthly_price,
                status=SubscriptionPaymentStatus.COMPLETED.value,
                due_date=datetime.utcnow(),
                order_id=order_id,
                toss_payment_key=charge_result.get("paymentKey"),
                payment_date=datetime.utcnow(),
                payment_type="initial",
                retry_count=0,
            )
            self.db.add(payment)

            # Activate subscription
            now = datetime.utcnow()
            subscription.status = SubscriptionStatus.ACTIVE.value
            subscription.start_date = now
            subscription.end_date = now + timedelta(days=30)
            subscription.next_billing_date = subscription.end_date
            subscription.billing_cycle_day = now.day

            # Update user's membership tier
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(membership_tier=MembershipTier.PREMIUM.value)
            )

            # Record in history
            history = SubscriptionHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                old_tier=MembershipTier.FREE.value,
                new_tier=MembershipTier.PREMIUM.value,
                reason=SubscriptionChangeReason.UPGRADE.value,
                note="Premium activated via billing key registration",
                payment_id=payment.id,
            )
            self.db.add(history)

            await self.db.commit()

        return {
            "card_last_four": card_last_four,
            "card_company": card_company,
        }

    async def get_billing_method(self, user_id: str) -> dict:
        """Get registered billing method info."""
        subscription = await self.get_user_subscription(user_id)
        if not subscription or not subscription.toss_billing_key:
            return {"has_billing_key": False}

        return {
            "has_billing_key": True,
            "card_last_four": subscription.card_last_four,
            "card_company": subscription.card_company,
        }

    async def remove_billing_key(self, user_id: str) -> None:
        """Remove billing key (disables auto-renewal)."""
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            raise ValueError("구독 정보를 찾을 수 없습니다")

        subscription.toss_billing_key = None
        subscription.toss_customer_key = None
        subscription.card_last_four = None
        subscription.card_company = None
        subscription.auto_renew = False

        await self.db.commit()
        logger.info(f"Removed billing key for user {user_id}")

    async def get_subscription_by_billing_key(self, billing_key: str) -> Optional[Subscription]:
        """Reverse lookup: find subscription by Toss billing key."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.toss_billing_key == billing_key)
        )
        return result.scalar_one_or_none()

    # --- Bank Transfer Methods ---

    async def initialize_bank_transfer(
        self, user_id: str, depositor_name: str
    ) -> dict:
        """Initialize bank transfer for premium subscription."""
        if not settings.BANK_ACCOUNT_NUMBER:
            raise ValueError("무통장입금 설정이 되어있지 않습니다. 관리자에게 문의하세요.")

        # Get or create subscription
        subscription = await self.get_user_subscription(user_id)
        if not subscription:
            subscription = await self.create_subscription(user_id)

        if subscription.status == SubscriptionStatus.ACTIVE.value:
            raise ValueError("이미 활성화된 구독이 있습니다")

        # Create payment record with 24-hour expiry
        order_id = f"BANK-{uuid.uuid4().hex[:16].upper()}"
        expires_at = datetime.utcnow() + timedelta(hours=24)

        payment = SubscriptionPayment(
            id=str(uuid.uuid4()),
            subscription_id=subscription.id,
            amount=self.monthly_price,
            status=SubscriptionPaymentStatus.PENDING.value,
            due_date=expires_at,
            order_id=order_id,
            payment_type="bank_transfer",
            retry_count=0,
        )
        self.db.add(payment)
        await self.db.commit()

        logger.info(f"Initialized bank transfer {order_id} for user {user_id}")

        return {
            "order_id": order_id,
            "amount": float(self.monthly_price),
            "bank_name": settings.BANK_NAME,
            "account_number": settings.BANK_ACCOUNT_NUMBER,
            "account_holder": settings.BANK_ACCOUNT_HOLDER,
            "depositor_name": depositor_name,
            "expires_at": expires_at,
            "message": f"입금자명을 '{depositor_name}'으로 {expires_at.strftime('%Y-%m-%d %H:%M')}까지 입금해주세요.",
        }

    async def confirm_bank_transfer(
        self,
        payment_id: str,
        confirmed_amount: int,
        admin_user_id: str,
    ) -> SubscriptionPayment:
        """Admin confirms bank transfer and activates subscription."""
        result = await self.db.execute(
            select(SubscriptionPayment)
            .where(SubscriptionPayment.id == payment_id)
            .options(selectinload(SubscriptionPayment.subscription))
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise ValueError("결제 정보를 찾을 수 없습니다")

        if payment.payment_type != "bank_transfer":
            raise ValueError("무통장입금 결제만 확인할 수 있습니다")

        if payment.status == SubscriptionPaymentStatus.COMPLETED.value:
            raise ValueError("이미 확인된 결제입니다")

        if confirmed_amount != int(payment.amount):
            raise ValueError(
                f"입금액({confirmed_amount:,}원)이 결제금액({int(payment.amount):,}원)과 다릅니다"
            )

        # Update payment
        payment.status = SubscriptionPaymentStatus.COMPLETED.value
        payment.payment_date = datetime.utcnow()
        payment.bank_transfer_confirmed_by = admin_user_id
        payment.bank_transfer_confirmed_at = datetime.utcnow()

        # Activate subscription
        subscription = payment.subscription
        now = datetime.utcnow()
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.start_date = now
        subscription.end_date = now + timedelta(days=30)
        subscription.next_billing_date = subscription.end_date
        subscription.billing_cycle_day = now.day
        subscription.payment_method_type = "bank_transfer"

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
            note=f"Premium activated via bank transfer. Confirmed by admin.",
            payment_id=payment.id,
            performed_by=admin_user_id,
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(payment)

        logger.info(f"Bank transfer confirmed for payment {payment_id}")
        return payment