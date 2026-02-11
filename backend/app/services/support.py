from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import SupportTicket
from app.schemas.support import SupportTicketCreate


class SupportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(
        self, user_id: UUID, data: SupportTicketCreate
    ) -> SupportTicket:
        ticket = SupportTicket(
            user_id=user_id,
            subject=data.subject,
            description=data.description,
        )
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def get_user_tickets(self, user_id: UUID) -> List[SupportTicket]:
        result = await self.db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_ticket_by_id(
        self, ticket_id: UUID, user_id: UUID
    ) -> SupportTicket:
        result = await self.db.execute(
            select(SupportTicket).where(
                SupportTicket.id == ticket_id,
                SupportTicket.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
