"""Verification endpoints for identity and business."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.verification import (
    request_phone_verification,
    verify_phone,
    verify_business,
    get_verification_status,
    VerificationError,
)

router = APIRouter()


class PhoneVerificationRequest(BaseModel):
    phone: str = Field(..., pattern=r"^01[0-9]{8,9}$")


class PhoneVerifyRequest(BaseModel):
    phone: str
    otp: str = Field(..., min_length=6, max_length=6)


class BusinessVerificationRequest(BaseModel):
    business_number: str = Field(..., pattern=r"^[0-9]{3}-?[0-9]{2}-?[0-9]{5}$")


class VerificationStatusResponse(BaseModel):
    phone: str | None
    phone_verified: bool
    identity_verified: bool
    business_number: str | None
    business_verified: bool
    fully_verified: bool


@router.post("/phone/request")
async def request_phone_otp(
    data: PhoneVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request phone verification OTP."""
    try:
        result = await request_phone_verification(
            db=db,
            user_id=str(current_user.id),
            phone=data.phone,
        )
        return result
    except VerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": e.code, "message": e.message},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VERIFICATION_FAILED", "message": str(e)},
        )


@router.post("/phone/verify")
async def verify_phone_otp(
    data: PhoneVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify phone number with OTP code."""
    try:
        result = await verify_phone(
            db=db,
            user_id=str(current_user.id),
            phone=data.phone,
            otp=data.otp,
        )
        return result
    except VerificationError as e:
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        if e.code in ("OTP_EXPIRED", "OTP_INVALID"):
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={"code": e.code, "message": e.message},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VERIFICATION_FAILED", "message": str(e)},
        )


@router.post("/business/verify")
async def verify_business_number(
    data: BusinessVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify business registration number (studios only)."""
    if current_user.role != "studio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_STUDIO", "message": "Only studios can verify business numbers"},
        )

    try:
        result = await verify_business(
            db=db,
            user_id=str(current_user.id),
            business_number=data.business_number,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VERIFICATION_FAILED", "message": str(e)},
        )


@router.get("/status", response_model=VerificationStatusResponse)
async def get_my_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's verification status."""
    try:
        result = await get_verification_status(db, str(current_user.id))
        return VerificationStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ERROR", "message": str(e)},
        )
