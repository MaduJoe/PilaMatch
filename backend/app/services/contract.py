from typing import Optional, List, Dict, Set, Tuple
from uuid import UUID
from datetime import datetime
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import (
    Contract, ContractEventLog, Offer, JobPost, Application,
    InstructorProfile, StudioProfile, User,
    ContractStatus, OfferStatus,
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

    async def _get_user_id_from_profile(self, profile_id: UUID) -> Optional[UUID]:
        """Get user_id from instructor or studio profile ID."""
        result = await self.db.execute(
            select(InstructorProfile.user_id).where(InstructorProfile.id == profile_id)
        )
        uid = result.scalar_one_or_none()
        if uid:
            return uid
        result = await self.db.execute(
            select(StudioProfile.user_id).where(StudioProfile.id == profile_id)
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
            hours = (end_dt - start_dt).total_seconds() / 3600

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

    async def get_by_user(
        self, user_id: UUID, role: str, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Contract], int]:
        if role == "instructor":
            profile_id = await self.get_instructor_profile_id(user_id)
            if not profile_id:
                return [], 0
            filter_clause = Contract.instructor_id == profile_id
        else:
            profile_id = await self.get_studio_profile_id(user_id)
            if not profile_id:
                return [], 0
            filter_clause = Contract.studio_id == profile_id

        # Count total
        count_result = await self.db.execute(
            select(func.count(Contract.id)).where(filter_clause)
        )
        total = count_result.scalar_one()

        # Fetch with eager loading + pagination
        result = await self.db.execute(
            select(Contract)
            .options(
                selectinload(Contract.offer),
            )
            .where(filter_clause)
            .order_by(Contract.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all()), total

    async def set_in_progress(
        self, contract_id: UUID, actor_user_id: UUID, profile_id: UUID, role: str
    ) -> Contract:
        """Sign contract - requires both parties to sign before progressing"""
        contract = await self.get_by_id(contract_id)

        if not contract:
            raise ValueError("Contract not found")

        # Check authorization - either party can sign
        if role == "studio" and contract.studio_id != profile_id:
            raise PermissionError("Not authorized to update this contract")
        if role == "instructor" and contract.instructor_id != profile_id:
            raise PermissionError("Not authorized to update this contract")

        # Contract must be in CONFIRMED status to be signed
        if contract.status != ContractStatus.CONFIRMED:
            raise ValueError("Contract must be in CONFIRMED status to sign")

        # Mark signature from the appropriate party
        from datetime import datetime

        if role == "studio":
            if contract.studio_signed_at:
                raise ValueError("Already signed by studio")
            contract.studio_signed_at = datetime.utcnow()
            signature_note = "Contract signed by studio"
        else:  # instructor
            if contract.instructor_signed_at:
                raise ValueError("Already signed by instructor")
            contract.instructor_signed_at = datetime.utcnow()
            signature_note = "Contract signed by instructor"

        # Check if both parties have signed
        if contract.studio_signed_at and contract.instructor_signed_at:
            # Both signed - compute SHA-256 hash for non-repudiation
            contract_content = {
                "id": str(contract.id),
                "hourly_rate": str(contract.hourly_rate),
                "total_amount": str(contract.total_amount),
                "total_sessions": contract.total_sessions,
                "date": contract.date.isoformat(),
                "start_time": contract.start_time.isoformat(),
                "end_time": contract.end_time.isoformat(),
                "studio_id": str(contract.studio_id),
                "instructor_id": str(contract.instructor_id),
            }
            contract.content_hash = hashlib.sha256(
                json.dumps(contract_content, sort_keys=True).encode()
            ).hexdigest()

            # Both signed - move to IN_PROGRESS
            from_status = contract.status
            contract.status = ContractStatus.IN_PROGRESS

            await self._log_event(
                contract_id=contract_id,
                actor_user_id=actor_user_id,
                from_status=from_status,
                to_status=ContractStatus.IN_PROGRESS,
                note="Contract signed by both parties - now in progress",
            )

            # Notify both parties
            try:
                from app.services.notification import notify_contract_status
                for pid in [contract.instructor_id, contract.studio_id]:
                    profile_uid = await self._get_user_id_from_profile(pid)
                    if profile_uid:
                        await notify_contract_status(
                            self.db, str(profile_uid), "in_progress", str(contract_id)
                        )
            except Exception:
                pass
        else:
            # First signature - remain in CONFIRMED status
            await self._log_event(
                contract_id=contract_id,
                actor_user_id=actor_user_id,
                from_status=ContractStatus.CONFIRMED,
                to_status=ContractStatus.CONFIRMED,
                note=f"{signature_note} - waiting for other party",
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

            # Notify both parties of completion
            try:
                from app.services.notification import notify_contract_status
                for pid in [contract.instructor_id, contract.studio_id]:
                    profile_uid = await self._get_user_id_from_profile(pid)
                    if profile_uid:
                        await notify_contract_status(
                            self.db, str(profile_uid), "completed", str(contract_id)
                        )
            except Exception:
                pass
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

                await self._log_event(
                    contract_id=contract.id,
                    actor_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
                    from_status=ContractStatus.PENDING_COMPLETION,
                    to_status=ContractStatus.COMPLETED,
                    note=note,
                )

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

                await self._log_event(
                    contract_id=contract.id,
                    actor_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # System user
                    from_status=ContractStatus.IN_PROGRESS,
                    to_status=ContractStatus.COMPLETED,
                    note="Auto-completed: 48h passed since class end without confirmation",
                )

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

        await self.db.commit()
        await self.db.refresh(contract)
        return contract
