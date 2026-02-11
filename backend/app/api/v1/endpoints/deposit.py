"""Deposit (보증금) management endpoints."""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.deposit import (
    get_deposit_status,
    add_deposit,
    refund_deposit,
)

router = APIRouter()


class DepositStatusResponse(BaseModel):
    balance: float
    required: float
    is_sufficient: bool
    shortfall: float


class DepositAddRequest(BaseModel):
    amount: float = Field(..., gt=0)


class DepositAddResponse(BaseModel):
    previous_balance: float
    added: float
    new_balance: float
    is_sufficient: bool


@router.get("/status", response_model=DepositStatusResponse)
async def get_my_deposit_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's deposit status."""
    try:
        result = await get_deposit_status(db, str(current_user.id))
        return DepositStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERROR", "message": str(e)},
        )


@router.post("/add", response_model=DepositAddResponse)
async def add_my_deposit(
    data: DepositAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add deposit to account.
    In production, this would integrate with payment gateway.
    """
    try:
        result = await add_deposit(
            db=db,
            user_id=str(current_user.id),
            amount=Decimal(str(data.amount)),
        )
        return DepositAddResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DEPOSIT_FAILED", "message": str(e)},
        )


@router.post("/refund")
async def request_deposit_refund(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request full deposit refund.
    Only available if user has no active contracts.
    """
    # TODO: Check for active contracts
    try:
        result = await refund_deposit(db, str(current_user.id))
        return {
            "message": "Deposit refund processed",
            "refunded": result["refunded"],
            "remaining_balance": result["remaining_balance"],
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REFUND_FAILED", "message": str(e)},
        )
