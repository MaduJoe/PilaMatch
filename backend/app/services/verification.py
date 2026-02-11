"""Identity and business verification service."""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User

# In-memory OTP storage (use Redis in production)
_otp_store: Dict[str, dict] = {}

OTP_EXPIRY_MINUTES = 5


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


async def request_phone_verification(
    db: AsyncSession,
    user_id: str,
    phone: str,
) -> dict:
    """
    Request phone verification by sending OTP.
    In production, integrate with SMS provider (NHN Cloud, AWS SNS, etc.)
    """
    from uuid import UUID

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    # Generate OTP
    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Store OTP (in production, use Redis with TTL)
    _otp_store[f"{user_id}:{phone}"] = {
        "otp": otp,
        "expiry": expiry,
        "attempts": 0,
    }

    # Update user's phone number
    user.phone = phone
    await db.commit()

    # TODO: Send SMS via provider
    # For MVP, we'll return the OTP in development mode
    return {
        "message": "Verification code sent",
        "expires_in": OTP_EXPIRY_MINUTES * 60,
        # Remove in production:
        "_dev_otp": otp,
    }


async def verify_phone(
    db: AsyncSession,
    user_id: str,
    phone: str,
    otp: str,
) -> dict:
    """Verify phone number with OTP."""
    from uuid import UUID

    key = f"{user_id}:{phone}"
    stored = _otp_store.get(key)

    if not stored:
        raise ValueError("No verification request found. Please request a new code.")

    if stored["attempts"] >= 3:
        del _otp_store[key]
        raise ValueError("Too many attempts. Please request a new code.")

    if datetime.utcnow() > stored["expiry"]:
        del _otp_store[key]
        raise ValueError("Code expired. Please request a new code.")

    if stored["otp"] != otp:
        stored["attempts"] += 1
        raise ValueError(f"Invalid code. {3 - stored['attempts']} attempts remaining.")

    # Success - update user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    user.phone = phone
    user.phone_verified = True
    user.identity_verified = True  # Phone verification = identity verified for MVP
    await db.commit()

    # Clean up
    del _otp_store[key]

    return {
        "verified": True,
        "message": "Phone number verified successfully",
    }


async def verify_business(
    db: AsyncSession,
    user_id: str,
    business_number: str,
) -> dict:
    """
    Verify business registration number.
    In production, integrate with 국세청 API or data provider.
    """
    from uuid import UUID

    # Validate format (XXX-XX-XXXXX)
    clean_number = business_number.replace("-", "")
    if len(clean_number) != 10 or not clean_number.isdigit():
        raise ValueError("Invalid business number format. Use XXX-XX-XXXXX.")

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    # TODO: In production, verify with 국세청 API
    # For MVP, we'll do basic format validation and mark as pending
    # Admin can manually verify

    user.business_number = clean_number
    # For MVP demo, auto-verify if format is correct
    user.business_verified = True
    await db.commit()

    return {
        "verified": True,
        "message": "Business number verified",
        "business_number": f"{clean_number[:3]}-{clean_number[3:5]}-{clean_number[5:]}",
    }


async def get_verification_status(db: AsyncSession, user_id: str) -> dict:
    """Get user's verification status."""
    from uuid import UUID

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError("User not found")

    return {
        "phone": user.phone,
        "phone_verified": user.phone_verified,
        "identity_verified": user.identity_verified,
        "business_number": user.business_number,
        "business_verified": user.business_verified,
        "fully_verified": (
            user.identity_verified and
            (user.role != "studio" or user.business_verified)
        ),
    }
