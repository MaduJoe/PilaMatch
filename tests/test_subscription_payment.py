"""Subscription Payment Flow Tests

Service-level unit tests for the SubscriptionService, covering:
- confirm_subscription_payment() calls Toss API (mock httpx)
- When TOSS_SECRET_KEY is not set, returns mock response
- When Toss API returns error, payment is marked as FAILED
- Idempotency: calling twice with same payment_key doesn't double-activate
- Payment failure handling: retry count, 3-retry suspension
- Subscription creation, cancellation, and tier downgrade

Test naming convention: test_{scenario}_{expected_result}
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User,
    Subscription,
    SubscriptionPayment,
    SubscriptionHistory,
    SubscriptionStatus,
    SubscriptionPaymentStatus,
    SubscriptionChangeReason,
    MembershipTier,
    UserRole,
)
from app.services.subscription import SubscriptionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_user(
    db: AsyncSession,
    *,
    membership: str = MembershipTier.FREE.value,
    deposit_balance: Decimal = Decimal("0"),
) -> User:
    """Create a test user and return the model instance."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"sub_test_{user_id}@test.com",
        hashed_password="hashed_test_password",
        role=UserRole.INSTRUCTOR.value,
        membership_tier=membership,
        deposit_balance=deposit_balance,
    )
    db.add(user)
    await db.flush()
    return user


async def _create_subscription(
    db: AsyncSession,
    user_id,
    *,
    status: str = SubscriptionStatus.INACTIVE.value,
    billing_key: str = None,
    auto_renew: bool = True,
) -> Subscription:
    """Create a subscription record for the given user."""
    sub_id = str(uuid.uuid4())
    subscription = Subscription(
        id=sub_id,
        user_id=user_id,
        tier="premium",
        status=status,
        monthly_amount=Decimal("9900"),
        auto_renew=auto_renew,
        toss_billing_key=billing_key,
    )
    db.add(subscription)
    await db.flush()
    return subscription


async def _create_payment(
    db: AsyncSession,
    subscription_id: str,
    *,
    status: str = SubscriptionPaymentStatus.PENDING.value,
    order_id: str = None,
    retry_count: int = 0,
) -> SubscriptionPayment:
    """Create a subscription payment record."""
    payment_id = str(uuid.uuid4())
    if order_id is None:
        order_id = f"SUB-{uuid.uuid4().hex[:16].upper()}"
    payment = SubscriptionPayment(
        id=payment_id,
        subscription_id=subscription_id,
        amount=Decimal("9900"),
        status=status,
        due_date=datetime.utcnow() + timedelta(hours=1),
        order_id=order_id,
        retry_count=retry_count,
    )
    db.add(payment)
    await db.flush()
    return payment


# ---------------------------------------------------------------------------
# 1. confirm_subscription_payment -- Toss API mock (no secret key)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_payment_without_toss_key_returns_mock_response(
    db_session: AsyncSession,
):
    """When TOSS_SECRET_KEY is not set, _call_toss_confirm returns a mock success response."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch("app.services.subscription.settings") as mock_settings:
        mock_settings.TOSS_SECRET_KEY = None
        result = await service._call_toss_confirm("test_pk", payment.order_id, 9900)

    assert result["paymentKey"] == "test_pk"
    assert result["status"] == "DONE"


# ---------------------------------------------------------------------------
# 2. confirm_subscription_payment -- successful activation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_payment_activates_subscription(
    db_session: AsyncSession,
):
    """After successful payment confirmation, subscription status becomes ACTIVE."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.return_value = {"paymentKey": "pk_test", "status": "DONE"}
        result = await service.confirm_subscription_payment("pk_test", payment.order_id)

    assert result.status == SubscriptionPaymentStatus.COMPLETED.value
    assert result.toss_payment_key == "pk_test"

    # Verify subscription is active
    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_confirm_payment_upgrades_user_to_premium(
    db_session: AsyncSession,
):
    """After successful payment, user's membership_tier is set to PREMIUM."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.return_value = {"paymentKey": "pk_test", "status": "DONE"}
        await service.confirm_subscription_payment("pk_test", payment.order_id)

    # Verify user tier upgraded
    user_result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    refreshed_user = user_result.scalar_one()
    assert refreshed_user.membership_tier == MembershipTier.PREMIUM.value


@pytest.mark.asyncio
async def test_confirm_payment_creates_history_record(
    db_session: AsyncSession,
):
    """A SubscriptionHistory record is created with upgrade reason."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.return_value = {"paymentKey": "pk_test", "status": "DONE"}
        await service.confirm_subscription_payment("pk_test", payment.order_id)

    # Verify history was created
    history_result = await db_session.execute(
        select(SubscriptionHistory).where(
            SubscriptionHistory.user_id == user.id
        )
    )
    histories = history_result.scalars().all()
    assert len(histories) == 1
    assert histories[0].old_tier == MembershipTier.FREE.value
    assert histories[0].new_tier == MembershipTier.PREMIUM.value
    assert histories[0].reason == SubscriptionChangeReason.UPGRADE.value


@pytest.mark.asyncio
async def test_confirm_payment_sets_subscription_dates(
    db_session: AsyncSession,
):
    """After activation, start_date, end_date, and next_billing_date are set."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.return_value = {"paymentKey": "pk_test", "status": "DONE"}
        await service.confirm_subscription_payment("pk_test", payment.order_id)

    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.start_date is not None
    assert refreshed_sub.end_date is not None
    assert refreshed_sub.next_billing_date is not None
    # end_date should be ~30 days after start_date
    delta = refreshed_sub.end_date - refreshed_sub.start_date
    assert delta.days == 30


# ---------------------------------------------------------------------------
# 3. confirm_subscription_payment -- Toss API error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_payment_toss_api_error_raises_value_error(
    db_session: AsyncSession,
):
    """When Toss API returns an error, confirm_subscription_payment raises ValueError."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.side_effect = ValueError("Payment confirmation failed")

        with pytest.raises(ValueError, match="Payment confirmation failed"):
            await service.confirm_subscription_payment("bad_pk", payment.order_id)


@pytest.mark.asyncio
async def test_call_toss_confirm_with_secret_key_calls_httpx(
    db_session: AsyncSession,
):
    """When TOSS_SECRET_KEY is set, _call_toss_confirm calls httpx.AsyncClient."""
    service = SubscriptionService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "paymentKey": "pk_test",
        "orderId": "ORD-123",
        "status": "DONE",
    }

    with patch("app.services.subscription.settings") as mock_settings:
        mock_settings.TOSS_SECRET_KEY = "test_secret_key_12345"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            result = await service._call_toss_confirm("pk_test", "ORD-123", 9900)

    assert result["paymentKey"] == "pk_test"
    mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_call_toss_confirm_with_secret_key_error_response_raises(
    db_session: AsyncSession,
):
    """When Toss API returns non-200 status, ValueError is raised."""
    service = SubscriptionService(db_session)

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"message": "INVALID_PAYMENT_KEY"}

    with patch("app.services.subscription.settings") as mock_settings:
        mock_settings.TOSS_SECRET_KEY = "test_secret_key_12345"

        with patch("httpx.AsyncClient") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client_instance

            with pytest.raises(ValueError, match="INVALID_PAYMENT_KEY"):
                await service._call_toss_confirm("bad_pk", "ORD-123", 9900)


# ---------------------------------------------------------------------------
# 4. Idempotency -- duplicate confirmation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_payment_idempotent_returns_completed_payment(
    db_session: AsyncSession,
):
    """Calling confirm twice with same order_id does not double-activate."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    payment = await _create_payment(db_session, subscription.id)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with patch.object(service, "_call_toss_confirm", new_callable=AsyncMock) as mock_toss:
        mock_toss.return_value = {"paymentKey": "pk_test", "status": "DONE"}

        # First confirmation
        result1 = await service.confirm_subscription_payment("pk_test", payment.order_id)
        assert result1.status == SubscriptionPaymentStatus.COMPLETED.value

        # Second confirmation -- should return existing completed payment
        result2 = await service.confirm_subscription_payment("pk_test", payment.order_id)
        assert result2.status == SubscriptionPaymentStatus.COMPLETED.value

    # Toss API should only be called once (second call short-circuits)
    assert mock_toss.call_count == 1


@pytest.mark.asyncio
async def test_confirm_payment_nonexistent_order_raises_error(
    db_session: AsyncSession,
):
    """Confirming a payment with an unknown order_id raises ValueError."""
    service = SubscriptionService(db_session)

    with pytest.raises(ValueError, match="Payment not found"):
        await service.confirm_subscription_payment("pk_test", "NONEXISTENT-ORDER")


# ---------------------------------------------------------------------------
# 5. Subscription creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_subscription_for_new_user(
    db_session: AsyncSession,
):
    """Creating a subscription for a user without one produces an INACTIVE subscription."""
    user = await _create_user(db_session)
    await db_session.commit()

    service = SubscriptionService(db_session)
    subscription = await service.create_subscription(str(user.id))

    assert subscription.status == SubscriptionStatus.INACTIVE.value
    assert subscription.tier == "premium"
    assert subscription.user_id == user.id


@pytest.mark.asyncio
async def test_create_subscription_duplicate_active_raises_error(
    db_session: AsyncSession,
):
    """Creating a subscription when user already has an ACTIVE one raises ValueError."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)

    with pytest.raises(ValueError, match="User already has an active subscription"):
        await service.create_subscription(str(user.id))


@pytest.mark.asyncio
async def test_create_subscription_reuses_inactive_subscription(
    db_session: AsyncSession,
):
    """If user has an INACTIVE subscription, it is reused instead of creating a new one."""
    user = await _create_user(db_session)
    existing_sub = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.INACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    result = await service.create_subscription(str(user.id))

    assert result.id == existing_sub.id


# ---------------------------------------------------------------------------
# 6. Initialize subscription payment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_initialize_payment_for_inactive_subscription(
    db_session: AsyncSession,
):
    """Initializing payment for an INACTIVE subscription returns order_id and amount."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(db_session, user.id)
    await db_session.commit()

    service = SubscriptionService(db_session)
    order_id, amount = await service.initialize_subscription_payment(subscription.id)

    assert order_id.startswith("SUB-")
    assert amount == Decimal("9900")


@pytest.mark.asyncio
async def test_initialize_payment_for_active_subscription_raises_error(
    db_session: AsyncSession,
):
    """Cannot initialize payment for an already ACTIVE subscription."""
    user = await _create_user(db_session)
    subscription = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)

    with pytest.raises(ValueError, match="Subscription is already active"):
        await service.initialize_subscription_payment(subscription.id)


@pytest.mark.asyncio
async def test_initialize_payment_nonexistent_subscription_raises_error(
    db_session: AsyncSession,
):
    """Initializing payment for a non-existent subscription raises ValueError."""
    service = SubscriptionService(db_session)

    with pytest.raises(ValueError, match="Subscription not found"):
        await service.initialize_subscription_payment(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# 7. Cancel subscription
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_subscription_downgrades_to_free(
    db_session: AsyncSession,
):
    """Cancelling an active subscription downgrades user to FREE tier."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    history = await service.cancel_subscription(str(user.id), reason="Too expensive")

    assert history.new_tier == MembershipTier.FREE.value
    assert history.reason == SubscriptionChangeReason.CANCELLATION.value

    # Verify user is now free tier
    user_result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    refreshed_user = user_result.scalar_one()
    assert refreshed_user.membership_tier == MembershipTier.FREE.value


@pytest.mark.asyncio
async def test_cancel_subscription_sets_cancelled_status(
    db_session: AsyncSession,
):
    """After cancellation, subscription status is CANCELLED."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    await service.cancel_subscription(str(user.id), reason="Moving away")

    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.CANCELLED.value
    assert refreshed_sub.cancelled_at is not None
    assert refreshed_sub.auto_renew is False


@pytest.mark.asyncio
async def test_cancel_subscription_without_active_raises_error(
    db_session: AsyncSession,
):
    """Attempting to cancel when no active subscription exists raises ValueError."""
    user = await _create_user(db_session)
    await db_session.commit()

    service = SubscriptionService(db_session)

    with pytest.raises(ValueError, match="No active subscription found"):
        await service.cancel_subscription(str(user.id))


@pytest.mark.asyncio
async def test_cancel_subscription_refunds_deposit_balance(
    db_session: AsyncSession,
):
    """Cancellation refunds any remaining deposit balance."""
    user = await _create_user(
        db_session,
        membership=MembershipTier.PREMIUM.value,
        deposit_balance=Decimal("50000"),
    )
    await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    history = await service.cancel_subscription(str(user.id), reason="Done")

    # Deposit balance should be zeroed out
    user_result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    refreshed_user = user_result.scalar_one()
    assert refreshed_user.deposit_balance == Decimal("0")

    assert "50000" in history.note


# ---------------------------------------------------------------------------
# 8. Payment failure handling -- retry and suspension
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_payment_failure_increments_retry_count(
    db_session: AsyncSession,
):
    """Each payment failure increments the retry_count."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    payment = await _create_payment(db_session, subscription.id, retry_count=0)
    await db_session.commit()

    service = SubscriptionService(db_session)
    await service.handle_payment_failure(payment.id, "Card declined")

    pay_result = await db_session.execute(
        select(SubscriptionPayment).where(SubscriptionPayment.id == payment.id)
    )
    refreshed_pay = pay_result.scalar_one()
    assert refreshed_pay.retry_count == 1
    assert refreshed_pay.status == SubscriptionPaymentStatus.FAILED.value
    assert refreshed_pay.failure_reason == "Card declined"


@pytest.mark.asyncio
async def test_handle_payment_failure_3_retries_suspends_subscription(
    db_session: AsyncSession,
):
    """After 3 payment failures, subscription is SUSPENDED and user downgraded to FREE."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    # Payment already at retry_count=2 (this will be the 3rd failure)
    payment = await _create_payment(db_session, subscription.id, retry_count=2)
    await db_session.commit()

    service = SubscriptionService(db_session)
    await service.handle_payment_failure(payment.id, "Card expired")

    # Verify subscription is suspended
    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.SUSPENDED.value

    # Verify user downgraded
    user_result = await db_session.execute(
        select(User).where(User.id == user.id)
    )
    refreshed_user = user_result.scalar_one()
    assert refreshed_user.membership_tier == MembershipTier.FREE.value

    # Verify history record
    history_result = await db_session.execute(
        select(SubscriptionHistory).where(
            SubscriptionHistory.user_id == user.id
        )
    )
    histories = history_result.scalars().all()
    assert len(histories) == 1
    assert histories[0].reason == SubscriptionChangeReason.SUSPENSION.value


@pytest.mark.asyncio
async def test_handle_payment_failure_2_retries_does_not_suspend(
    db_session: AsyncSession,
):
    """After 2 payment failures (retry_count goes from 1 to 2), subscription is NOT suspended."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id, status=SubscriptionStatus.ACTIVE.value
    )
    payment = await _create_payment(db_session, subscription.id, retry_count=1)
    await db_session.commit()

    service = SubscriptionService(db_session)
    await service.handle_payment_failure(payment.id, "Temporary error")

    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_handle_payment_failure_nonexistent_payment_does_nothing(
    db_session: AsyncSession,
):
    """Calling handle_payment_failure with non-existent payment_id does not raise."""
    service = SubscriptionService(db_session)
    # Should return silently without error
    await service.handle_payment_failure(str(uuid.uuid4()), "No such payment")


# ---------------------------------------------------------------------------
# 9. Auto-renewal -- no billing key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_renewal_without_billing_key_expires_subscription(
    db_session: AsyncSession,
):
    """Auto-renewal without a billing key marks the subscription as EXPIRED."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id,
        status=SubscriptionStatus.ACTIVE.value,
        billing_key=None,
        auto_renew=True,
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    result = await service.process_auto_renewal(subscription.id)

    assert result is None

    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.EXPIRED.value


@pytest.mark.asyncio
async def test_auto_renewal_disabled_expires_subscription(
    db_session: AsyncSession,
):
    """When auto_renew is disabled, subscription is marked as EXPIRED."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    subscription = await _create_subscription(
        db_session, user.id,
        status=SubscriptionStatus.ACTIVE.value,
        auto_renew=False,
    )
    await db_session.commit()

    service = SubscriptionService(db_session)
    result = await service.process_auto_renewal(subscription.id)

    assert result is None

    sub_result = await db_session.execute(
        select(Subscription).where(Subscription.id == subscription.id)
    )
    refreshed_sub = sub_result.scalar_one()
    assert refreshed_sub.status == SubscriptionStatus.EXPIRED.value


# ---------------------------------------------------------------------------
# 10. Membership tier checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_premium_user_returns_true_for_premium(
    db_session: AsyncSession,
):
    """is_premium_user returns True for a PREMIUM user."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    await db_session.commit()

    service = SubscriptionService(db_session)
    assert await service.is_premium_user(str(user.id)) is True


@pytest.mark.asyncio
async def test_is_premium_user_returns_false_for_free(
    db_session: AsyncSession,
):
    """is_premium_user returns False for a FREE user."""
    user = await _create_user(db_session, membership=MembershipTier.FREE.value)
    await db_session.commit()

    service = SubscriptionService(db_session)
    assert await service.is_premium_user(str(user.id)) is False


@pytest.mark.asyncio
async def test_can_user_skip_deposit_premium_returns_true(
    db_session: AsyncSession,
):
    """Premium users can skip the deposit requirement."""
    user = await _create_user(db_session, membership=MembershipTier.PREMIUM.value)
    await db_session.commit()

    service = SubscriptionService(db_session)
    assert await service.can_user_skip_deposit(str(user.id)) is True


@pytest.mark.asyncio
async def test_can_user_skip_deposit_free_returns_false(
    db_session: AsyncSession,
):
    """Free users cannot skip the deposit requirement."""
    user = await _create_user(db_session, membership=MembershipTier.FREE.value)
    await db_session.commit()

    service = SubscriptionService(db_session)
    assert await service.can_user_skip_deposit(str(user.id)) is False
