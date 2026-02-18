"""Dispute management service (v2.0)."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import (
    Dispute, DisputeType, DisputeStatus, DisputeResolution,
    Contract, ContractStatus, User,
    ChatMessage, ChatThread
)
from app.services.escrow import refund_escrow_to_studio

# v3.0: No deposit system - penalties handled via Trust Score
NO_SHOW_PENALTY_AMOUNT = Decimal("0")


class DisputeService:
    """Handle dispute creation, objection, and resolution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_no_show_dispute(
        self,
        contract_id: UUID,
        reporter_id: UUID,
        reported_user_id: UUID,
    ) -> Dispute:
        """Create a no-show dispute with 24h objection period."""
        # Verify contract exists and is in progress
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()

        if not contract:
            raise ValueError("Contract not found")

        # Allow no-show reports for both CONFIRMED and IN_PROGRESS contracts
        if contract.status not in [ContractStatus.CONFIRMED, ContractStatus.IN_PROGRESS]:
            raise ValueError(f"Contract must be confirmed or in progress to report no-show, current status: {contract.status}")

        # Collect evidence automatically
        evidence = await self._collect_evidence(contract_id, reported_user_id)

        # Create dispute with 24h objection deadline
        dispute = Dispute(
            contract_id=contract_id,
            reported_by=reporter_id,
            reported_against=reported_user_id,
            type=DisputeType.NO_SHOW,
            status=DisputeStatus.OPEN,
            objection_deadline=datetime.utcnow() + timedelta(hours=24),
            evidence_snapshot=evidence,
        )

        self.db.add(dispute)
        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def create_completion_dispute(
        self,
        contract_id: UUID,
        reporter_id: UUID,
        reported_user_id: UUID,
        reason: str,
    ) -> Dispute:
        """Create a dispute when completion is rejected."""
        # Verify contract exists and is pending completion
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()

        if not contract:
            raise ValueError("Contract not found")

        if contract.status != ContractStatus.PENDING_COMPLETION:
            raise ValueError("Contract must be pending completion to dispute")

        # Collect evidence automatically
        evidence = await self._collect_evidence(contract_id, reported_user_id)
        evidence["rejection_reason"] = reason

        # Create dispute
        dispute = Dispute(
            contract_id=contract_id,
            reported_by=reporter_id,
            reported_against=reported_user_id,
            type=DisputeType.COMPLETION_REJECTED,
            status=DisputeStatus.OPEN,
            objection_deadline=datetime.utcnow() + timedelta(hours=24),
            evidence_snapshot=evidence,
        )

        # Update contract status to DISPUTED
        contract.status = ContractStatus.DISPUTED

        self.db.add(dispute)
        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def object_to_dispute(
        self,
        dispute_id: UUID,
        user_id: UUID,
        objection_reason: str,
    ) -> Dispute:
        """Object to a dispute within the deadline."""
        dispute = await self.db.execute(
            select(Dispute).where(Dispute.id == dispute_id)
        )
        dispute = dispute.scalar_one_or_none()

        if not dispute:
            raise ValueError("Dispute not found")

        if str(dispute.reported_against) != str(user_id):
            raise PermissionError("Only the reported party can object")

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError("Dispute is not open for objection")

        now = datetime.utcnow()
        if dispute.objection_deadline and now > dispute.objection_deadline:
            raise ValueError("Objection deadline has passed")

        dispute.status = DisputeStatus.OBJECTED
        dispute.objection_reason = objection_reason

        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def auto_resolve_expired_disputes(self) -> List[Dispute]:
        """Automatically resolve disputes where objection deadline has passed."""
        now = datetime.utcnow()

        # Find open disputes past their deadline
        result = await self.db.execute(
            select(Dispute).where(
                and_(
                    Dispute.status == DisputeStatus.OPEN,
                    Dispute.objection_deadline < now
                )
            )
        )
        disputes = result.scalars().all()

        resolved = []
        for dispute in disputes:
            # Auto-resolve in favor of reporter (no objection received)
            dispute.status = DisputeStatus.RESOLVED
            dispute.resolution = DisputeResolution.REPORTER_WINS
            dispute.resolution_reason = "No objection received within 24 hours"
            dispute.resolved_by = "system"
            dispute.resolved_at = now

            # Apply penalties if it's a no-show dispute
            if dispute.type == DisputeType.NO_SHOW:
                await self._apply_no_show_penalty(dispute)

            resolved.append(dispute)

        if resolved:
            await self.db.commit()

        return resolved

    async def resolve_manually(
        self,
        dispute_id: UUID,
        admin_user_id: UUID,
        resolution: DisputeResolution,
        reason: str,
    ) -> Dispute:
        """Manually resolve a dispute (admin only)."""
        dispute = await self.db.execute(
            select(Dispute).where(Dispute.id == dispute_id)
        )
        dispute = dispute.scalar_one_or_none()

        if not dispute:
            raise ValueError("Dispute not found")

        if dispute.status == DisputeStatus.RESOLVED:
            raise ValueError("Dispute is already resolved")

        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = resolution
        dispute.resolution_reason = reason
        dispute.resolved_by = str(admin_user_id)
        dispute.resolved_at = datetime.utcnow()

        # Apply appropriate actions based on resolution
        if dispute.type == DisputeType.NO_SHOW:
            if resolution == DisputeResolution.REPORTER_WINS:
                await self._apply_no_show_penalty(dispute)
            elif resolution == DisputeResolution.PARTIAL:
                # Partial penalty (e.g., 50% of normal penalty)
                await self._apply_no_show_penalty(dispute, amount=NO_SHOW_PENALTY_AMOUNT / 2)

        # Update contract status if needed
        contract = await self.db.execute(
            select(Contract).where(Contract.id == dispute.contract_id)
        )
        contract = contract.scalar_one_or_none()

        if contract and contract.status == ContractStatus.DISPUTED:
            if resolution == DisputeResolution.REPORTER_WINS:
                if dispute.type == DisputeType.NO_SHOW:
                    contract.status = ContractStatus.CANCELLED
                else:
                    contract.status = ContractStatus.COMPLETED
            elif resolution == DisputeResolution.RESPONDENT_WINS:
                contract.status = ContractStatus.COMPLETED
            else:  # PARTIAL
                contract.status = ContractStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(dispute)

        return dispute

    async def get_pending_disputes(self) -> List[Dict[str, Any]]:
        """Get all disputes needing manual review (for admin dashboard)."""
        result = await self.db.execute(
            select(Dispute, Contract).join(
                Contract, Dispute.contract_id == Contract.id
            ).where(
                Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.OBJECTED])
            ).order_by(Dispute.created_at.asc())
        )

        disputes_with_contracts = result.all()

        disputes_data = []
        for dispute, contract in disputes_with_contracts:
            # Get reporter and respondent info
            reporter = await self.db.execute(
                select(User).where(User.id == dispute.reported_by)
            )
            reporter = reporter.scalar_one_or_none()

            respondent = await self.db.execute(
                select(User).where(User.id == dispute.reported_against)
            )
            respondent = respondent.scalar_one_or_none()

            disputes_data.append({
                "dispute": dispute,
                "contract": contract,
                "reporter_email": reporter.email if reporter else None,
                "respondent_email": respondent.email if respondent else None,
                "time_remaining": self._get_time_remaining(dispute.objection_deadline) if dispute.objection_deadline else None,
            })

        return disputes_data

    async def _collect_evidence(self, contract_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Automatically collect evidence for dispute."""
        evidence = {}

        # Get user's last activity
        user = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        if user:
            evidence["last_active_at"] = user.last_active_at.isoformat() if user.last_active_at else None

        # Get contract details
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()
        if contract:
            evidence["contract_date"] = contract.date.isoformat() if contract.date else None
            evidence["contract_time"] = f"{contract.start_time}-{contract.end_time}"

        # Get chat messages related to the contract (last 10 messages)
        chat_thread = await self.db.execute(
            select(ChatThread).where(ChatThread.contract_id == contract_id)
        )
        chat_thread = chat_thread.scalar_one_or_none()

        if chat_thread:
            messages = await self.db.execute(
                select(ChatMessage).where(
                    ChatMessage.thread_id == chat_thread.id
                ).order_by(ChatMessage.created_at.desc()).limit(10)
            )
            messages = messages.scalars().all()

            evidence["recent_messages"] = [
                {
                    "sender_id": str(msg.sender_id),
                    "content": msg.content,
                    "sent_at": msg.created_at.isoformat(),
                }
                for msg in reversed(messages)
            ]

        # TODO: Add reminder confirmation check when reminder system is implemented
        evidence["reminder_confirmed"] = None  # Placeholder

        return evidence

    async def _apply_no_show_penalty(self, dispute: Dispute, amount: Decimal = None) -> None:
        """Apply no-show penalty to the reported user.

        v3.0: No financial penalty - only increment count and suspend if needed.
        Trust Score reduction handled separately.
        """
        # Increment no-show count
        user = await self.db.execute(
            select(User).where(User.id == dispute.reported_against)
        )
        user = user.scalar_one_or_none()
        if user:
            user.no_show_count += 1
            if user.no_show_count >= 3:
                user.is_suspended = True

        # Refund studio if it's a no-show case
        contract = await self.db.execute(
            select(Contract).where(Contract.id == dispute.contract_id)
        )
        contract = contract.scalar_one_or_none()
        if contract:
            await refund_escrow_to_studio(self.db, str(contract.id), reason="No-show by instructor")

    def _get_time_remaining(self, deadline: datetime) -> Optional[str]:
        """Get human-readable time remaining until deadline."""
        if not deadline:
            return None

        now = datetime.utcnow()
        if now >= deadline:
            return "Expired"

        delta = deadline - now
        hours = int(delta.total_seconds() / 3600)
        minutes = int((delta.total_seconds() % 3600) / 60)

        if hours > 0:
            return f"{hours}h {minutes}m remaining"
        else:
            return f"{minutes}m remaining"