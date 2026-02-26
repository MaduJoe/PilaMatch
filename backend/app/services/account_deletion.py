"""Account deletion service with 30-day grace period and cascade operations."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, Contract, Payment, Subscription,
    ContractStatus, PaymentStatus,
    SubscriptionStatus,
)
from app.core.security import verify_password

logger = logging.getLogger(__name__)


class AccountDeletionService:
    """Handles soft-delete account deletion with 30-day grace period."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_deletion(self, user_id: str, password: str) -> datetime:
        """Request account deletion with password confirmation.

        Returns:
            deletion_scheduled_at datetime
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if not verify_password(password, user.hashed_password):
            raise ValueError("INVALID_PASSWORD")

        if not user.is_active and getattr(user, "deleted_at", None):
            raise ValueError("ALREADY_DELETED")

        now = datetime.utcnow()
        deletion_scheduled_at = now + timedelta(days=30)

        # Soft-delete user
        user.is_active = False
        if hasattr(user, "deleted_at"):
            user.deleted_at = now
        if hasattr(user, "deletion_scheduled_at"):
            user.deletion_scheduled_at = deletion_scheduled_at

        # Cascade operations
        await self._cascade_cancel_contracts(user_id)
        await self._cascade_refund_escrows(user_id)
        await self._cascade_cancel_subscriptions(user_id)

        await self.db.commit()

        logger.info(f"Account deletion requested for user {user_id}, scheduled at {deletion_scheduled_at}")
        return deletion_scheduled_at

    async def cancel_deletion(self, user_id: str) -> None:
        """Cancel pending account deletion and restore account."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Check if deletion is pending
        deletion_scheduled = getattr(user, "deletion_scheduled_at", None)
        deleted_at = getattr(user, "deleted_at", None)

        if not deleted_at and user.is_active:
            raise ValueError("NO_PENDING_DELETION")

        if deletion_scheduled and deletion_scheduled < datetime.utcnow():
            raise ValueError("DELETION_ALREADY_PROCESSED")

        # Restore account
        user.is_active = True
        if hasattr(user, "deleted_at"):
            user.deleted_at = None
        if hasattr(user, "deletion_scheduled_at"):
            user.deletion_scheduled_at = None

        await self.db.commit()
        logger.info(f"Account deletion cancelled for user {user_id}")

    async def process_expired_deletions(self) -> int:
        """Process accounts whose 30-day grace period has expired. (cron job)

        Returns:
            Number of accounts permanently anonymized.
        """
        now = datetime.utcnow()
        count = 0

        # Find users with expired deletion schedule
        # Only works if deleted_at / deletion_scheduled_at columns exist
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.is_active == False,
                        User.deletion_scheduled_at <= now,
                        User.deletion_scheduled_at.isnot(None),
                    )
                )
            )
            users = result.scalars().all()

            for user in users:
                await self._anonymize_user(user)
                count += 1

            if count > 0:
                await self.db.commit()

        except Exception as e:
            logger.warning(f"process_expired_deletions skipped (columns may not exist yet): {e}")

        logger.info(f"Processed {count} expired account deletions")
        return count

    async def _anonymize_user(self, user: User) -> None:
        """Anonymize user data for GDPR compliance."""
        import hashlib

        hashed_email = hashlib.sha256(user.email.encode()).hexdigest()[:16]
        user.email = f"deleted_{hashed_email}@anonymized.local"
        user.hashed_password = "DELETED"
        user.phone = None
        user.phone_verified = False
        user.business_number = None
        user.business_verified = False
        user.identity_verified = False

        logger.info(f"User {user.id} anonymized")

    async def _cascade_cancel_contracts(self, user_id: str) -> None:
        """Cancel all active contracts for the user."""
        from app.models import InstructorProfile, StudioProfile

        # Find profile IDs
        instructor_result = await self.db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        instructor_profile_id = instructor_result.scalar_one_or_none()

        studio_result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        studio_profile_id = studio_result.scalar_one_or_none()

        # Find active contracts
        active_statuses = [
            ContractStatus.CONFIRMED.value,
            ContractStatus.IN_PROGRESS.value,
            ContractStatus.PENDING_COMPLETION.value,
        ]

        conditions = []
        if instructor_profile_id:
            conditions.append(
                and_(
                    Contract.instructor_id == instructor_profile_id,
                    Contract.status.in_(active_statuses),
                )
            )
        if studio_profile_id:
            conditions.append(
                and_(
                    Contract.studio_id == studio_profile_id,
                    Contract.status.in_(active_statuses),
                )
            )

        if not conditions:
            return

        from sqlalchemy import or_
        result = await self.db.execute(
            select(Contract).where(or_(*conditions))
        )
        contracts = result.scalars().all()

        for contract in contracts:
            contract.status = ContractStatus.CANCELLED.value
            contract.cancellation_reason = "Account deletion"

        logger.info(f"Cancelled {len(contracts)} contracts for user {user_id}")

    async def _cascade_refund_escrows(self, user_id: str) -> None:
        """Refund all held escrow payments for the user."""
        from app.models import InstructorProfile, StudioProfile

        studio_result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        studio_profile_id = studio_result.scalar_one_or_none()

        if not studio_profile_id:
            return

        # Find contracts with held escrow where this user is the studio
        result = await self.db.execute(
            select(Payment).join(Contract).where(
                and_(
                    Contract.studio_id == studio_profile_id,
                    Payment.escrow_status == "HELD",
                )
            )
        )
        payments = result.scalars().all()

        for payment in payments:
            payment.escrow_status = "REFUNDED"
            payment.status = PaymentStatus.REFUNDED.value

        logger.info(f"Refunded {len(payments)} escrow payments for user {user_id}")

    async def _cascade_cancel_subscriptions(self, user_id: str) -> None:
        """Cancel active subscriptions for the user."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE.value,
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.cancelled_at = datetime.utcnow()
            subscription.cancellation_reason = "Account deletion"
            subscription.auto_renew = False
            logger.info(f"Cancelled subscription for user {user_id}")
