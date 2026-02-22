"""Identity and business verification service."""
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.core.config import settings

# OTP storage - uses Redis when available, falls back to in-memory
_otp_store: Dict[str, dict] = {}
_redis_client = None


async def _get_redis():
    """Get Redis client for OTP storage. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


async def _store_otp(key: str, otp: str, expiry_seconds: int) -> None:
    """Store OTP in Redis (preferred) or in-memory fallback."""
    import json
    redis = await _get_redis()
    if redis:
        data = json.dumps({"otp": otp, "attempts": 0})
        await redis.setex(f"otp:{key}", expiry_seconds, data)
    else:
        _otp_store[key] = {
            "otp": otp,
            "expiry": datetime.utcnow() + timedelta(seconds=expiry_seconds),
            "attempts": 0,
        }


async def _get_otp(key: str) -> Optional[dict]:
    """Retrieve stored OTP data."""
    import json
    redis = await _get_redis()
    if redis:
        data = await redis.get(f"otp:{key}")
        if data:
            return json.loads(data)
        return None
    else:
        stored = _otp_store.get(key)
        if stored and datetime.utcnow() > stored["expiry"]:
            del _otp_store[key]
            return None
        return stored


async def _increment_otp_attempts(key: str) -> None:
    """Increment OTP attempt counter."""
    import json
    redis = await _get_redis()
    if redis:
        data = await redis.get(f"otp:{key}")
        if data:
            parsed = json.loads(data)
            parsed["attempts"] = parsed.get("attempts", 0) + 1
            ttl = await redis.ttl(f"otp:{key}")
            if ttl > 0:
                await redis.setex(f"otp:{key}", ttl, json.dumps(parsed))
    else:
        if key in _otp_store:
            _otp_store[key]["attempts"] += 1


async def _delete_otp(key: str) -> None:
    """Remove OTP from storage."""
    redis = await _get_redis()
    if redis:
        await redis.delete(f"otp:{key}")
    else:
        _otp_store.pop(key, None)

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

    # Store OTP in Redis (or in-memory fallback)
    await _store_otp(f"{user_id}:{phone}", otp, OTP_EXPIRY_MINUTES * 60)

    # Update user's phone number
    user.phone = phone
    await db.commit()

    # TODO: Send SMS via provider (NHN Cloud, AWS SNS, etc.)
    result = {
        "message": "Verification code sent",
        "expires_in": OTP_EXPIRY_MINUTES * 60,
    }
    # Only expose OTP in development mode
    if settings.APP_ENV == "development":
        result["_dev_otp"] = otp
    return result


async def verify_phone(
    db: AsyncSession,
    user_id: str,
    phone: str,
    otp: str,
) -> dict:
    """Verify phone number with OTP."""
    from uuid import UUID

    key = f"{user_id}:{phone}"
    stored = await _get_otp(key)

    if not stored:
        raise ValueError("No verification request found. Please request a new code.")

    if stored["attempts"] >= 3:
        await _delete_otp(key)
        raise ValueError("Too many attempts. Please request a new code.")

    if stored["otp"] != otp:
        await _increment_otp_attempts(key)
        remaining = 3 - (stored["attempts"] + 1)
        raise ValueError(f"Invalid code. {remaining} attempts remaining.")

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
    await _delete_otp(key)

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
