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


# Valid state transitions (v2.0 updated)
VALID_TRANSITIONS: Dict[ContractStatus, Set[ContractStatus]] = {
    ContractStatus.CONFIRMED: {ContractStatus.IN_PROGRESS, ContractStatus.CANCELLED},
    ContractStatus.IN_PROGRESS: {ContractStatus.PENDING_COMPLETION, ContractStatus.CANCELLED},
    ContractStatus.PENDING_COMPLETION: {ContractStatus.COMPLETED, ContractStatus.DISPUTED},
    ContractStatus.COMPLETED: set(),  # Terminal state
    ContractStatus.DISPUTED: {ContractStatus.COMPLETED, ContractStatus.CANCELLED},  # Can be resolved
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

    async def confirm_completion(
        self, contract_id: UUID, actor_user_id: UUID, profile_id: UUID, role: str
    ) -> Contract:
        """Confirm completion from one party (v2.0 bidirectional confirmation)."""
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to confirm this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to confirm this contract")

        # Contract must be IN_PROGRESS or PENDING_COMPLETION
        if contract.status not in [ContractStatus.IN_PROGRESS, ContractStatus.PENDING_COMPLETION]:
            raise ValueError("CONTRACT_NOT_IN_PROGRESS")

        # Mark confirmation from the appropriate party
        if role == "studio":
            if contract.studio_confirmed_at:
                raise ValueError("Already confirmed by studio")
            contract.studio_confirmed_at = datetime.utcnow()
        else:  # instructor
            if contract.instructor_confirmed_at:
                raise ValueError("Already confirmed by instructor")
            contract.instructor_confirmed_at = datetime.utcnow()

        # Check if both parties have confirmed
        if contract.studio_confirmed_at and contract.instructor_confirmed_at:
            # Both confirmed - complete the contract
            from_status = contract.status
            contract.status = ContractStatus.COMPLETED

            await self._log_event(
                contract_id=contract_id,
                actor_user_id=actor_user_id,
                from_status=from_status,
                to_status=ContractStatus.COMPLETED,
                note="Contract completed - both parties confirmed",
            )

            # Calculate platform fee (5%) and settlement amount
            from decimal import Decimal
            contract.platform_fee = float(contract.total_amount) * 0.05
            contract.settlement_amount = float(contract.total_amount) - contract.platform_fee

            # Release escrow to instructor
            from app.services.escrow import release_escrow_to_instructor
            try:
                await release_escrow_to_instructor(self.db, str(contract_id))
            except ValueError:
                pass  # Payment may not exist yet
        else:
            # First confirmation - move to PENDING_COMPLETION
            if contract.status == ContractStatus.IN_PROGRESS:
                from_status = contract.status
                contract.status = ContractStatus.PENDING_COMPLETION

                await self._log_event(
                    contract_id=contract_id,
                    actor_user_id=actor_user_id,
                    from_status=from_status,
                    to_status=ContractStatus.PENDING_COMPLETION,
                    note=f"Completion confirmed by {role}, waiting for other party",
                )

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def reject_completion(
        self, contract_id: UUID, actor_user_id: UUID, profile_id: UUID, role: str, reason: str
    ) -> Contract:
        """Reject completion and create a dispute (v2.0)."""
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to reject this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to reject this contract")

        # Contract must be PENDING_COMPLETION
        if contract.status != ContractStatus.PENDING_COMPLETION:
            raise ValueError("CONTRACT_NOT_PENDING_COMPLETION")

        # Create a dispute
        from app.services.dispute import DisputeService
        dispute_service = DisputeService(self.db)

        # Determine who to report
        if role == "studio":
            reported_against = contract.instructor_id
        else:
            reported_against = contract.studio_id

        dispute = await dispute_service.create_completion_dispute(
            contract_id=contract_id,
            reporter_id=actor_user_id,
            reported_user_id=reported_against,
            reason=reason,
        )

        # Contract status is updated to DISPUTED by the dispute service

        await self._log_event(
            contract_id=contract_id,
            actor_user_id=actor_user_id,
            from_status=ContractStatus.PENDING_COMPLETION,
            to_status=ContractStatus.DISPUTED,
            note=f"Completion rejected by {role}: {reason}",
        )

        await self.db.commit()
        await self.db.refresh(contract)
        return contract

    async def auto_complete_pending_contracts(self) -> List[Contract]:
        """Auto-complete contracts where confirmation timeout has passed (v2.0).

        Rules:
        - One party confirmed, 24h passed: auto-complete
        - No party confirmed, 48h passed: auto-complete
        """
        from datetime import timedelta

        now = datetime.utcnow()
        auto_completed = []

        # Find PENDING_COMPLETION contracts
        result = await self.db.execute(
            select(Contract).where(
                Contract.status == ContractStatus.PENDING_COMPLETION
            )
        )
        pending_contracts = result.scalars().all()

        for contract in pending_contracts:
            should_complete = False
            note = ""

            # Check if one party confirmed and 24h passed
            if contract.studio_confirmed_at:
                if now - contract.studio_confirmed_at > timedelta(hours=24):
                    should_complete = True
                    note = "Auto-completed: Studio confirmed, 24h passed without instructor confirmation"
            elif contract.instructor_confirmed_at:
                if now - contract.instructor_confirmed_at > timedelta(hours=24):
                    should_complete = True
                    note = "Auto-completed: Instructor confirmed, 24h passed without studio confirmation"

            if should_complete:
                contract.status = ContractStatus.COMPLETED
                contract.platform_fee = float(contract.total_amount) * 0.05
                contract.settlement_amount = float(contract.total_amount) - contract.platform_fee

                await self._log_event(
                    contract_id=contract.id,
                    actor_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
                    from_status=ContractStatus.PENDING_COMPLETION,
                    to_status=ContractStatus.COMPLETED,
                    note=note,
                )

                # Release escrow to instructor
                from app.services.escrow import release_escrow_to_instructor
                try:
                    await release_escrow_to_instructor(self.db, str(contract.id))
                except ValueError:
                    pass

                auto_completed.append(contract)

        # Find IN_PROGRESS contracts where class ended 48h ago
        result = await self.db.execute(
            select(Contract).where(
                Contract.status == ContractStatus.IN_PROGRESS
            )
        )
        in_progress_contracts = result.scalars().all()

        for contract in in_progress_contracts:
            # Calculate when the class ended
            class_end = datetime.combine(contract.date, contract.end_time)
            if now - class_end > timedelta(hours=48):
                contract.status = ContractStatus.COMPLETED
                contract.platform_fee = float(contract.total_amount) * 0.05
                contract.settlement_amount = float(contract.total_amount) - contract.platform_fee

                await self._log_event(
                    contract_id=contract.id,
                    actor_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
                    from_status=ContractStatus.IN_PROGRESS,
                    to_status=ContractStatus.COMPLETED,
                    note="Auto-completed: 48h passed since class end without confirmation",
                )

                # Release escrow to instructor
                from app.services.escrow import release_escrow_to_instructor
                try:
                    await release_escrow_to_instructor(self.db, str(contract.id))
                except ValueError:
                    pass

                auto_completed.append(contract)

        if auto_completed:
            await self.db.commit()

        return auto_completed

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
