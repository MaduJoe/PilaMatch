from typing import Optional, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
import base64
import hmac
import hashlib
import logging

import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import (
    Payment, Payout, Contract, StudioProfile, User,
    PaymentStatus, PayoutStatus, ContractStatus,
    PaymentCancellation, WebhookEvent,
)
from app.core.config import settings
from app.schemas.payment import PaymentConfirmRequest, PaymentCancelRequest

logger = logging.getLogger(__name__)

PLATFORM_FEE_RATE = Decimal("0.05")  # 5% platform fee
TOSS_API_BASE = "https://api.tosspayments.com/v1"
TOSS_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    def _toss_auth_header(self) -> str:
        secret_key = settings.TOSS_SECRET_KEY + ":"
        return base64.b64encode(secret_key.encode()).decode()

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_order_id(self, order_id: str) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_payment_key(self, payment_key: str) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.payment_key == payment_key)
        )
        return result.scalar_one_or_none()

    async def get_payment_by_id(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payment_with_cancellations(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.id == payment_id)
            .options(selectinload(Payment.cancellations))
        )
        return result.scalar_one_or_none()

    # ---------------------------------------------------------------
    # Initialize Payment
    # ---------------------------------------------------------------

    async def initialize_payment(
        self, contract_id: UUID, payer_user_id: UUID
    ) -> Tuple[str, Decimal, str]:
        """Initialize payment and return order_id, amount, order_name."""
        # Get contract
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()

        if not contract:
            raise ValueError("Contract not found")

        if contract.status not in (ContractStatus.CONFIRMED, ContractStatus.IN_PROGRESS):
            raise ValueError("Contract must be in CONFIRMED or IN_PROGRESS status")

        # Check for existing payment
        existing = await self.db.execute(
            select(Payment).where(Payment.contract_id == contract_id)
        )
        existing_payment = existing.scalar_one_or_none()

        if existing_payment:
            if existing_payment.status == PaymentStatus.COMPLETED:
                raise ValueError("Payment already completed")
            # Return existing pending payment
            return existing_payment.order_id, existing_payment.amount, f"Contract {contract_id}"

        # Calculate amount with platform fee
        total_amount = contract.total_amount
        platform_fee = total_amount * PLATFORM_FEE_RATE
        payment_amount = total_amount + platform_fee

        # Generate order ID
        order_id = f"ORDER-{uuid4().hex[:16].upper()}"

        # Create payment record
        payment = Payment(
            contract_id=contract_id,
            payer_user_id=payer_user_id,
            amount=payment_amount,
            platform_fee=platform_fee,
            status=PaymentStatus.PENDING,
            order_id=order_id,
            balance_amount=payment_amount,
        )
        self.db.add(payment)
        await self.db.commit()

        return order_id, payment_amount, f"Contract {contract_id}"

    # ---------------------------------------------------------------
    # Confirm Payment
    # ---------------------------------------------------------------

    async def confirm_payment(self, data: PaymentConfirmRequest) -> Payment:
        """Confirm payment with TossPayments."""
        # Idempotency check
        existing = await self.get_payment_by_payment_key(data.payment_key)
        if existing and existing.status == PaymentStatus.COMPLETED:
            return existing

        # Get payment record
        payment = await self.get_payment_by_order_id(data.order_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            return payment

        # Verify amount
        if payment.amount != data.amount:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = "Amount mismatch"
            await self.db.commit()
            raise ValueError("Amount mismatch")

        # Call TossPayments API to confirm
        try:
            response = await self._call_toss_confirm(data)
            payment.payment_key = data.payment_key
            payment.status = PaymentStatus.COMPLETED
            payment.payment_method = response.get("method", "unknown")
            payment.pg_response = response
            payment.balance_amount = payment.amount
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            await self.db.commit()
            raise

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def _call_toss_confirm(self, data: PaymentConfirmRequest) -> dict:
        """Call TossPayments confirm API with Idempotency-Key and timeout."""
        if not settings.TOSS_SECRET_KEY:
            # Mock response for development
            return {
                "paymentKey": data.payment_key,
                "orderId": data.order_id,
                "status": "DONE",
                "method": "카드",
            }

        encoded_key = self._toss_auth_header()
        idempotency_key = f"confirm-{data.order_id}"

        async with httpx.AsyncClient(timeout=TOSS_TIMEOUT) as client:
            response = await client.post(
                f"{TOSS_API_BASE}/payments/confirm",
                headers={
                    "Authorization": f"Basic {encoded_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json={
                    "paymentKey": data.payment_key,
                    "orderId": data.order_id,
                    "amount": int(data.amount),
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(error_data.get("message", "Payment confirmation failed"))

            return response.json()

    # ---------------------------------------------------------------
    # Cancel Payment
    # ---------------------------------------------------------------

    async def cancel_payment(
        self,
        payment_id: UUID,
        cancel_request: PaymentCancelRequest,
        requested_by_user_id: UUID,
    ) -> PaymentCancellation:
        """Cancel or partially cancel a payment."""
        # Idempotency: check if same key already processed
        if cancel_request.idempotency_key:
            existing_cancel = await self.db.execute(
                select(PaymentCancellation).where(
                    PaymentCancellation.idempotency_key == cancel_request.idempotency_key
                )
            )
            existing = existing_cancel.scalar_one_or_none()
            if existing:
                return existing

        # Get payment
        payment = await self.get_payment_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        # Validate payment status
        if payment.status == PaymentStatus.REFUNDED:
            raise ValueError("Payment is already fully refunded")

        if payment.status not in (
            PaymentStatus.COMPLETED,
            PaymentStatus.PARTIALLY_CANCELLED,
        ):
            raise ValueError("Payment must be COMPLETED or PARTIALLY_CANCELLED to cancel")

        # Calculate current balance
        balance = Decimal(str(payment.balance_amount or payment.amount)) - Decimal(str(payment.cancelled_amount or 0))
        if balance <= 0:
            raise ValueError("Payment is already fully refunded")

        cancel_amount = cancel_request.cancel_amount
        if cancel_amount > balance:
            raise ValueError(
                f"Cancel amount ({cancel_amount}) exceeds balance ({balance})"
            )

        # Create cancellation record
        cancellation = PaymentCancellation(
            payment_id=payment_id,
            cancel_amount=cancel_amount,
            cancel_reason=cancel_request.cancel_reason,
            cancel_status="PENDING",
            idempotency_key=cancel_request.idempotency_key,
            tax_free_amount=cancel_request.tax_free_amount,
            requested_by_user_id=requested_by_user_id,
        )
        self.db.add(cancellation)

        # Call Toss cancel API
        try:
            pg_response = await self._call_toss_cancel(
                payment_key=payment.payment_key,
                cancel_amount=int(cancel_amount),
                cancel_reason=cancel_request.cancel_reason,
                tax_free_amount=int(cancel_request.tax_free_amount),
                idempotency_key=cancel_request.idempotency_key,
            )

            cancellation.cancel_status = "DONE"
            cancellation.pg_cancel_response = pg_response

            # Extract transaction key from Toss response
            if pg_response and "cancels" in pg_response:
                cancels = pg_response["cancels"]
                if cancels:
                    cancellation.transaction_key = cancels[-1].get("transactionKey")

            # Update payment amounts
            new_cancelled = Decimal(str(payment.cancelled_amount or 0)) + cancel_amount
            payment.cancelled_amount = new_cancelled
            payment.balance_amount = Decimal(str(payment.amount)) - new_cancelled

            # Determine new payment status
            if payment.balance_amount <= 0:
                payment.status = PaymentStatus.REFUNDED
                payment.escrow_status = "REFUNDED"
            else:
                payment.status = PaymentStatus.PARTIALLY_CANCELLED

        except Exception as e:
            cancellation.cancel_status = "FAILED"
            cancellation.failure_reason = str(e)
            logger.error(f"Payment cancel failed for payment_id={payment_id}: {e}")
            await self.db.commit()
            await self.db.refresh(cancellation)
            return cancellation

        await self.db.commit()
        await self.db.refresh(cancellation)
        return cancellation

    async def _call_toss_cancel(
        self,
        payment_key: Optional[str],
        cancel_amount: int,
        cancel_reason: str,
        tax_free_amount: int = 0,
        idempotency_key: Optional[str] = None,
    ) -> Optional[dict]:
        """Call TossPayments cancel API."""
        if not payment_key:
            return None

        if not settings.TOSS_SECRET_KEY:
            # Mock response for development
            return {
                "paymentKey": payment_key,
                "status": "CANCELED",
                "cancels": [{
                    "cancelAmount": cancel_amount,
                    "cancelReason": cancel_reason,
                    "transactionKey": f"mock_txn_{uuid4().hex[:12]}",
                }],
            }

        encoded_key = self._toss_auth_header()
        headers = {
            "Authorization": f"Basic {encoded_key}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        body: dict = {
            "cancelReason": cancel_reason,
            "cancelAmount": cancel_amount,
        }
        if tax_free_amount > 0:
            body["taxFreeAmount"] = tax_free_amount

        async with httpx.AsyncClient(timeout=TOSS_TIMEOUT) as client:
            response = await client.post(
                f"{TOSS_API_BASE}/payments/{payment_key}/cancel",
                headers=headers,
                json=body,
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(
                    f"Toss cancel failed: {error_data.get('message', 'Unknown error')}"
                )

            return response.json()

    # ---------------------------------------------------------------
    # Webhook v2
    # ---------------------------------------------------------------

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        transmission_time: str = "",
        transmission_id: str = "",
    ) -> bool:
        """Verify TossPayments v2 webhook HMAC-SHA256 signature."""
        if not settings.TOSS_WEBHOOK_SECRET:
            return True  # Skip verification in development

        # Replay prevention: reject webhooks older than 5 minutes
        if transmission_time:
            try:
                webhook_time = datetime.fromisoformat(transmission_time.replace("Z", "+00:00"))
                now_utc = datetime.now(timezone.utc)
                if abs((now_utc - webhook_time).total_seconds()) > 300:
                    logger.warning(f"Webhook replay rejected: transmission_time={transmission_time}")
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid webhook transmission_time: {transmission_time}")
                return False

        # v2 signature: HMAC-SHA256(secret, transmission_id.time.payload)
        if transmission_id and transmission_time:
            message = f"{transmission_id}.{transmission_time}.{payload.decode()}"
            expected = hmac.new(
                settings.TOSS_WEBHOOK_SECRET.encode(),
                message.encode(),
                hashlib.sha256,
            ).hexdigest()
        else:
            # Fallback: legacy v1 verification (body-only HMAC)
            expected = hmac.new(
                settings.TOSS_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def handle_webhook(
        self,
        event_type: str,
        event_data: dict,
        transmission_id: Optional[str] = None,
    ) -> None:
        """Handle webhook events from TossPayments with deduplication."""
        # Deduplication check
        if transmission_id:
            existing_event = await self.db.execute(
                select(WebhookEvent).where(
                    WebhookEvent.transmission_id == transmission_id
                )
            )
            if existing_event.scalar_one_or_none():
                logger.info(f"Duplicate webhook skipped: transmission_id={transmission_id}")
                return

            # Record this webhook event
            webhook_event = WebhookEvent(
                transmission_id=transmission_id,
                event_type=event_type,
                payment_key=event_data.get("paymentKey"),
                processed=False,
                payload=event_data,
            )
            self.db.add(webhook_event)

        payment_key = event_data.get("paymentKey")
        if not payment_key:
            return

        payment = await self.get_payment_by_payment_key(payment_key)
        if not payment:
            return

        if event_type == "PAYMENT_STATUS_CHANGED":
            status = event_data.get("status")
            if status == "DONE":
                payment.status = PaymentStatus.COMPLETED
            elif status == "CANCELED":
                payment.status = PaymentStatus.REFUNDED
            elif status == "FAILED":
                payment.status = PaymentStatus.FAILED
                payment.failure_reason = event_data.get("failReason")

            payment.pg_response = event_data

        elif event_type == "CANCEL_STATUS_CHANGED":
            # Update cancellation records and recalculate amounts
            cancels = event_data.get("cancels", [])
            total_cancelled = Decimal("0")
            for cancel in cancels:
                total_cancelled += Decimal(str(cancel.get("cancelAmount", 0)))

            payment.cancelled_amount = total_cancelled
            payment.balance_amount = Decimal(str(payment.amount)) - total_cancelled

            if payment.balance_amount <= 0:
                payment.status = PaymentStatus.REFUNDED
                payment.escrow_status = "REFUNDED"
            elif total_cancelled > 0:
                payment.status = PaymentStatus.PARTIALLY_CANCELLED

            payment.pg_response = event_data

        # Mark webhook as processed
        if transmission_id:
            result = await self.db.execute(
                select(WebhookEvent).where(
                    WebhookEvent.transmission_id == transmission_id
                )
            )
            wh_event = result.scalar_one_or_none()
            if wh_event:
                wh_event.processed = True

        await self.db.commit()

    # ---------------------------------------------------------------
    # Create Payout
    # ---------------------------------------------------------------

    async def create_payout(self, contract_id: UUID) -> Payout:
        """Create payout record after contract completion."""
        # Get contract
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()

        if not contract:
            raise ValueError("Contract not found")

        if contract.status != ContractStatus.COMPLETED:
            raise ValueError("Contract must be completed")

        # Check for existing payout
        existing = await self.db.execute(
            select(Payout).where(Payout.contract_id == contract_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Payout already exists")

        # Get payment to calculate payout amount
        payment = await self.db.execute(
            select(Payment).where(
                Payment.contract_id == contract_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        payment = payment.scalar_one_or_none()

        if not payment:
            raise ValueError("No completed payment found")

        # Payout amount is total minus platform fee
        payout_amount = payment.amount - payment.platform_fee

        # Get instructor user ID
        from app.models import InstructorProfile
        instructor = await self.db.execute(
            select(InstructorProfile.user_id).where(InstructorProfile.id == contract.instructor_id)
        )
        instructor_user_id = instructor.scalar_one_or_none()

        if not instructor_user_id:
            raise ValueError("Instructor not found")

        payout = Payout(
            contract_id=contract_id,
            payee_user_id=instructor_user_id,
            amount=payout_amount,
            status=PayoutStatus.PENDING,
        )
        self.db.add(payout)
        await self.db.commit()
        await self.db.refresh(payout)
        return payout
