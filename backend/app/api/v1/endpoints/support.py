from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketListResponse,
)
from app.services.support import SupportService

router = APIRouter()


@router.post("/support/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a support ticket."""
    service = SupportService(db)
    ticket = await service.create_ticket(current_user.id, data)
    return SupportTicketResponse.model_validate(ticket)


@router.get("/support/tickets/me", response_model=SupportTicketListResponse)
async def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's support tickets."""
    service = SupportService(db)
    tickets = await service.get_user_tickets(current_user.id)

    return SupportTicketListResponse(
        items=[SupportTicketResponse.model_validate(t) for t in tickets],
        total=len(tickets),
    )


@router.get("/support/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific support ticket."""
    service = SupportService(db)
    ticket = await service.get_ticket_by_id(ticket_id, current_user.id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TICKET_NOT_FOUND", "message": "Support ticket not found"},
        )

    return SupportTicketResponse.model_validate(ticket)
