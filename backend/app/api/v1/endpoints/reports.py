from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.report import (
    ReportCreate,
    ReportResponse,
    BlockCreate,
    BlockResponse,
    BlockListResponse,
)
from app.services.report import ReportService

router = APIRouter()


@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a user for inappropriate behavior."""
    service = ReportService(db)

    try:
        report = await service.create_report(current_user.id, data)
        return ReportResponse.model_validate(report)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REPORT_FAILED", "message": str(e)},
        )


@router.post("/blocks", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(
    data: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Block a user."""
    service = ReportService(db)

    try:
        block = await service.create_block(current_user.id, data)
        return BlockResponse.model_validate(block)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "BLOCK_FAILED", "message": str(e)},
        )


@router.get("/blocks/me", response_model=BlockListResponse)
async def get_my_blocks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's blocked users."""
    service = ReportService(db)
    blocks = await service.get_blocks(current_user.id)

    return BlockListResponse(
        items=[BlockResponse.model_validate(b) for b in blocks],
        total=len(blocks),
    )


@router.delete("/blocks/{blocked_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_block(
    blocked_user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unblock a user."""
    service = ReportService(db)
    success = await service.remove_block(current_user.id, blocked_user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BLOCK_NOT_FOUND", "message": "Block not found"},
        )
