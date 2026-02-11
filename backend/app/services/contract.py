from typing import Optional, List, Dict, Set
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    Contract, ContractEventLog, Offer, JobPost, Application,
    Payment, InstructorProfile, StudioProfile,
    ContractStatus, OfferStatus, PaymentStatus
)


# Valid state transitions
VALID_TRANSITIONS: Dict[ContractStatus, Set[ContractStatus]] = {
    ContractStatus.CONFIRMED: {ContractStatus.IN_PROGRESS, ContractStatus.CANCELLED},
    ContractStatus.IN_PROGRESS: {ContractStatus.COMPLETED, ContractStatus.CANCELLED},
    ContractStatus.COMPLETED: set(),  # Terminal state
    ContractStatus.CANCELLED: set(),  # Terminal state
}


class ContractService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_instructor_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, contract_id: UUID) -> Optional[Contract]:
        result = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        return result.scalar_one_or_none()

    def _validate_transition(self, from_status: ContractStatus, to_status: ContractStatus) -> bool:
        valid_next = VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_next

    async def _log_event(
        self,
        contract_id: UUID,
        actor_user_id: UUID,
        from_status: Optional[ContractStatus],
        to_status: ContractStatus,
        note: Optional[str] = None,
    ) -> ContractEventLog:
        event = ContractEventLog(
            contract_id=contract_id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
        )
        self.db.add(event)
        return event

    async def create_from_offer(self, offer_id: UUID, actor_user_id: UUID) -> Contract:
        # Get offer
        offer = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        offer = offer.scalar_one_or_none()

        if not offer:
            raise ValueError("Offer not found")

        if offer.status != OfferStatus.ACCEPTED:
            raise ValueError("Offer must be accepted first")

        # Check if contract already exists for this offer
        existing = await self.db.execute(
            select(Contract).where(Contract.offer_id == offer_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Contract already exists for this offer")

        # Get job post details if application-based
        job_date = datetime.utcnow().date()
        start_time = datetime.utcnow().time()
        end_time = datetime.utcnow().time()
        total_sessions = 1

        if offer.application_id:
            application = await self.db.execute(
                select(Application).where(Application.id == offer.application_id)
            )
            application = application.scalar_one_or_none()

            if application:
                job_post = await self.db.execute(
                    select(JobPost).where(JobPost.id == application.job_post_id)
                )
                job_post = job_post.scalar_one_or_none()

                if job_post:
                    job_date = job_post.date
                    start_time = job_post.start_time
                    end_time = job_post.end_time
                    total_sessions = job_post.total_sessions

        # Calculate total amount (hours * rate * sessions)
        hours = 1  # Default
        if start_time and end_time:
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            hours = (end_dt - start_dt).seconds / 3600

        total_amount = float(offer.proposed_rate) * hours * total_sessions

        # Create contract
        contract = Contract(
            offer_id=offer_id,
            studio_id=offer.studio_id,
            instructor_id=offer.instructor_id,
            status=ContractStatus.CONFIRMED,
            hourly_rate=offer.proposed_rate,
            total_amount=total_amount,
            total_sessions=total_sessions,
            date=job_date,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add(contract)
        await self.db.flush()

        # Log event
        await self._log_event(
            contract_id=contract.id,
            actor_user_id=actor_user_id,
            from_status=None,
            to_status=ContractStatus.CONFIRMED,
            note="Contract created from accepted offer",
        )

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def get_by_user(self, user_id: UUID, role: str) -> List[Contract]:
        if role == "instructor":
            instructor_id = await self.get_instructor_profile_id(user_id)
            if not instructor_id:
                return []
            result = await self.db.execute(
                select(Contract)
                .where(Contract.instructor_id == instructor_id)
                .order_by(Contract.created_at.desc())
            )
        else:
            studio_id = await self.get_studio_profile_id(user_id)
            if not studio_id:
                return []
            result = await self.db.execute(
                select(Contract)
                .where(Contract.studio_id == studio_id)
                .order_by(Contract.created_at.desc())
            )

        return list(result.scalars().all())

    async def _check_payment(self, contract_id: UUID) -> bool:
        result = await self.db.execute(
            select(Payment).where(
                Payment.contract_id == contract_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        return result.scalar_one_or_none() is not None

    async def set_in_progress(
        self, contract_id: UUID, actor_user_id: UUID, profile_id: UUID, role: str
    ) -> Contract:
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization - either party can sign
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to update this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to update this contract")

        if not self._validate_transition(contract.status, ContractStatus.IN_PROGRESS):
            raise ValueError("INVALID_STATE_TRANSITION")

        # MVP: No payment required - signature-based agreement only

        from_status = contract.status
        contract.status = ContractStatus.IN_PROGRESS

        await self._log_event(
            contract_id=contract_id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=ContractStatus.IN_PROGRESS,
            note=f"Contract signed by {role}",
        )

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def complete(
        self, contract_id: UUID, actor_user_id: UUID, profile_id: UUID, role: str
    ) -> Contract:
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to complete this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to complete this contract")

        if contract.status != ContractStatus.IN_PROGRESS:
            raise ValueError("CONTRACT_NOT_IN_PROGRESS")

        if not self._validate_transition(contract.status, ContractStatus.COMPLETED):
            raise ValueError("INVALID_STATE_TRANSITION")

        from_status = contract.status
        contract.status = ContractStatus.COMPLETED

        await self._log_event(
            contract_id=contract_id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=ContractStatus.COMPLETED,
            note="Contract completed",
        )

        # Release escrow to instructor
        from app.services.escrow import release_escrow_to_instructor
        try:
            await release_escrow_to_instructor(self.db, str(contract_id))
        except ValueError:
            pass  # Payment may not exist yet

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def cancel(
        self,
        contract_id: UUID,
        actor_user_id: UUID,
        profile_id: UUID,
        role: str,
        reason: str,
    ) -> Contract:
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to cancel this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to cancel this contract")

        if not reason:
            raise ValueError("CANCEL_REASON_REQUIRED")

        if not self._validate_transition(contract.status, ContractStatus.CANCELLED):
            raise ValueError("INVALID_STATE_TRANSITION")

        from_status = contract.status
        contract.status = ContractStatus.CANCELLED
        contract.cancellation_reason = reason
        contract.cancelled_by_user_id = actor_user_id

        await self._log_event(
            contract_id=contract_id,
            actor_user_id=actor_user_id,
            from_status=from_status,
            to_status=ContractStatus.CANCELLED,
            note=f"Contract cancelled: {reason}",
        )

        # Refund escrow to studio (100% for normal cancellation)
        from app.services.escrow import refund_escrow_to_studio
        try:
            await refund_escrow_to_studio(self.db, str(contract_id), reason=reason)
        except ValueError:
            pass  # Payment may not exist

        await self.db.commit()
        await self.db.refresh(contract)
        return contract
