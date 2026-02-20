from typing import Optional, Tuple
from uuid import UUID, uuid4
from decimal import Decimal
import base64
import hmac
import hashlib

import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    Payment, Payout, Contract, StudioProfile, User,
    PaymentStatus, PayoutStatus, ContractStatus
)
from app.core.config import settings
from app.schemas.payment import PaymentConfirmRequest


PLATFORM_FEE_RATE = Decimal("0.05")  # 5% platform fee


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

        if contract.status != ContractStatus.CONFIRMED:
            raise ValueError("Contract must be in CONFIRMED status")

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
        )
        self.db.add(payment)
        await self.db.commit()

        return order_id, payment_amount, f"Contract {contract_id}"

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
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            await self.db.commit()
            raise

        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def _call_toss_confirm(self, data: PaymentConfirmRequest) -> dict:
        """Call TossPayments confirm API."""
        if not settings.TOSS_SECRET_KEY:
            # Mock response for development
            return {
                "paymentKey": data.payment_key,
                "orderId": data.order_id,
                "status": "DONE",
                "method": "카드",
            }

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
                    "paymentKey": data.payment_key,
                    "orderId": data.order_id,
                    "amount": int(data.amount),
                },
            )

            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(error_data.get("message", "Payment confirmation failed"))

            return response.json()

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify TossPayments webhook HMAC-SHA256 signature."""
        if not settings.TOSS_WEBHOOK_SECRET:
            return True  # Skip verification in development
        expected = hmac.new(
            settings.TOSS_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def handle_webhook(self, event_type: str, event_data: dict) -> None:
        """Handle webhook events from TossPayments."""
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
            await self.db.commit()

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
