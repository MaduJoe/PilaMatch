"""Identity and business verification service."""
import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.core.config import settings


# ── Custom Exceptions ────────────────────────────────────────────────────────

class VerificationError(Exception):
    """Base verification error with error code."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class CooldownActiveError(VerificationError):
    def __init__(self, remaining_seconds: int):
        super().__init__(
            "COOLDOWN_ACTIVE",
            f"재발송 쿨타임 중입니다. {remaining_seconds}초 후 다시 시도해주세요.",
        )
        self.remaining_seconds = remaining_seconds


class PhoneLockedError(VerificationError):
    def __init__(self, remaining_seconds: int):
        super().__init__(
            "PHONE_LOCKED",
            f"인증 시도 횟수를 초과했습니다. {remaining_seconds}초 후 다시 시도해주세요.",
        )
        self.remaining_seconds = remaining_seconds


class OTPExpiredError(VerificationError):
    def __init__(self):
        super().__init__(
            "OTP_EXPIRED",
            "인증번호가 만료되었습니다. 새 인증번호를 요청해주세요.",
        )


class OTPInvalidError(VerificationError):
    def __init__(self, remaining_attempts: int):
        super().__init__(
            "OTP_INVALID",
            f"인증번호가 일치하지 않습니다. 남은 시도 횟수: {remaining_attempts}회",
        )
        self.remaining_attempts = remaining_attempts


# ── Constants from config ────────────────────────────────────────────────────

OTP_EXPIRY_SECONDS = settings.SMS_OTP_EXPIRY_SECONDS        # 180
MAX_VERIFY_ATTEMPTS = settings.SMS_OTP_MAX_ATTEMPTS          # 5
COOLDOWN_SECONDS = settings.SMS_OTP_COOLDOWN_SECONDS         # 60
LOCK_SECONDS = settings.SMS_OTP_LOCK_SECONDS                 # 600
VERIFIED_TTL_SECONDS = 600  # 인증완료 상태 유지 10분


# ── Redis Key Helpers ────────────────────────────────────────────────────────

def _key_code(phone: str) -> str:
    return f"auth:sms:code:{phone}"


def _key_attempt(phone: str) -> str:
    return f"auth:sms:attempt:{phone}"


def _key_cooldown(phone: str) -> str:
    return f"auth:sms:cooldown:{phone}"


def _key_verified(phone: str) -> str:
    return f"auth:sms:verified:{phone}"


# ── Phone Normalization ──────────────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """한국 전화번호를 E.164 포맷으로 정규화."""
    clean = phone.replace("-", "").replace(" ", "")
    if clean.startswith("+82"):
        return clean
    if clean.startswith("0"):
        return "+82" + clean[1:]
    return "+82" + clean


def to_domestic(phone_e164: str) -> str:
    """E.164 → 국내 포맷 (01012345678)."""
    if phone_e164.startswith("+82"):
        return "0" + phone_e164[3:]
    return phone_e164


# ── Redis / In-Memory Storage ────────────────────────────────────────────────

_redis_client = None
_memory_store: Dict[str, dict] = {}  # key → {"value": str, "expiry": datetime}


async def _get_redis():
    """Get Redis client. Returns None if unavailable."""
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


async def _set(key: str, value: str, ttl: int) -> None:
    """Set a key with TTL in Redis or in-memory fallback."""
    redis = await _get_redis()
    if redis:
        await redis.setex(key, ttl, value)
    else:
        _memory_store[key] = {
            "value": value,
            "expiry": datetime.utcnow() + timedelta(seconds=ttl),
        }


async def _get(key: str) -> Optional[str]:
    """Get a key value from Redis or in-memory fallback."""
    redis = await _get_redis()
    if redis:
        return await redis.get(key)
    else:
        stored = _memory_store.get(key)
        if stored is None:
            return None
        if datetime.utcnow() > stored["expiry"]:
            del _memory_store[key]
            return None
        return stored["value"]


async def _delete(key: str) -> None:
    """Delete a key from Redis or in-memory fallback."""
    redis = await _get_redis()
    if redis:
        await redis.delete(key)
    else:
        _memory_store.pop(key, None)


async def _incr(key: str, ttl: int) -> int:
    """Increment a counter key. Returns new value."""
    redis = await _get_redis()
    if redis:
        val = await redis.incr(key)
        if val == 1:
            await redis.expire(key, ttl)
        return val
    else:
        stored = _memory_store.get(key)
        if stored is None or datetime.utcnow() > stored["expiry"]:
            _memory_store[key] = {
                "value": "1",
                "expiry": datetime.utcnow() + timedelta(seconds=ttl),
            }
            return 1
        new_val = int(stored["value"]) + 1
        stored["value"] = str(new_val)
        return new_val


async def _ttl(key: str) -> int:
    """Get remaining TTL in seconds. Returns -1 if no TTL, -2 if key missing."""
    redis = await _get_redis()
    if redis:
        return await redis.ttl(key)
    else:
        stored = _memory_store.get(key)
        if stored is None:
            return -2
        remaining = (stored["expiry"] - datetime.utcnow()).total_seconds()
        if remaining <= 0:
            del _memory_store[key]
            return -2
        return int(remaining)


# ── OTP Generation ───────────────────────────────────────────────────────────

def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


# ── Phone Verification ───────────────────────────────────────────────────────

async def request_phone_verification(
    db: AsyncSession,
    user_id: str,
    phone: str,
) -> dict:
    """Request phone verification by sending OTP."""
    from uuid import UUID

    # Get user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    # Normalize phone for key lookups
    phone_e164 = normalize_phone(phone)
    domestic_phone = to_domestic(phone_e164)

    # Check lock (5회 실패 시 잠금)
    attempts_str = await _get(_key_attempt(phone_e164))
    if attempts_str and int(attempts_str) >= MAX_VERIFY_ATTEMPTS:
        remaining = await _ttl(_key_attempt(phone_e164))
        raise PhoneLockedError(remaining_seconds=max(remaining, 0))

    # Check cooldown (재발송 쿨타임)
    cooldown = await _get(_key_cooldown(phone_e164))
    if cooldown:
        remaining = await _ttl(_key_cooldown(phone_e164))
        raise CooldownActiveError(remaining_seconds=max(remaining, 0))

    # Generate and store OTP
    otp = generate_otp()
    await _set(_key_code(phone_e164), otp, OTP_EXPIRY_SECONDS)

    # Set cooldown
    await _set(_key_cooldown(phone_e164), "1", COOLDOWN_SECONDS)

    # Update user's phone number (domestic format for DB)
    user.phone = domestic_phone
    await db.commit()

    # Send SMS
    from app.services.sms import send_verification_sms
    sms_sent = await send_verification_sms(domestic_phone, otp)
    if not sms_sent:
        await _delete(_key_code(phone_e164))
        await _delete(_key_cooldown(phone_e164))
        raise ValueError("SMS 발송에 실패했습니다. 잠시 후 다시 시도해주세요.")

    result = {
        "message": "Verification code sent",
        "expires_in": OTP_EXPIRY_SECONDS,
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

    phone_e164 = normalize_phone(phone)

    # Check lock
    attempts_str = await _get(_key_attempt(phone_e164))
    current_attempts = int(attempts_str) if attempts_str else 0
    if current_attempts >= MAX_VERIFY_ATTEMPTS:
        remaining = await _ttl(_key_attempt(phone_e164))
        raise PhoneLockedError(remaining_seconds=max(remaining, 0))

    # Check OTP exists
    stored_otp = await _get(_key_code(phone_e164))
    if not stored_otp:
        raise OTPExpiredError()

    # Verify OTP
    if stored_otp != otp:
        new_attempts = await _incr(_key_attempt(phone_e164), LOCK_SECONDS)
        remaining_attempts = MAX_VERIFY_ATTEMPTS - new_attempts

        if remaining_attempts <= 0:
            await _delete(_key_code(phone_e164))
            remaining_lock = await _ttl(_key_attempt(phone_e164))
            raise PhoneLockedError(remaining_seconds=max(remaining_lock, 0))

        raise OTPInvalidError(remaining_attempts=remaining_attempts)

    # Success — update user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    domestic_phone = to_domestic(phone_e164)
    user.phone = domestic_phone
    user.phone_verified = True
    user.identity_verified = True
    await db.commit()

    # Clean up all keys and set verified status
    await _delete(_key_code(phone_e164))
    await _delete(_key_attempt(phone_e164))
    await _delete(_key_cooldown(phone_e164))
    await _set(_key_verified(phone_e164), "1", VERIFIED_TTL_SECONDS)

    return {
        "verified": True,
        "message": "Phone number verified successfully",
    }


# ── Business Verification ────────────────────────────────────────────────────

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

    # Verify with 국세청 API (or dev checksum mock)
    from app.services.nts_client import check_business_status
    nts_result = await check_business_status(clean_number)

    if not nts_result.is_operating:
        label = nts_result.status_label or "확인 불가"
        raise ValueError(
            f"사업자번호가 현재 '{label}' 상태입니다. "
            "영업 중인 사업자만 인증할 수 있습니다."
        )

    user.business_number = clean_number
    user.business_verified = True
    await db.commit()

    return {
        "verified": True,
        "message": "Business number verified",
        "business_number": f"{clean_number[:3]}-{clean_number[3:5]}-{clean_number[5:]}",
        "business_status": nts_result.status_label,
        "tax_type": nts_result.tax_type_label,
    }


# ── Verification Status ─────────────────────────────────────────────────────

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
