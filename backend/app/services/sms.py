"""SMS provider service with Strategy pattern."""

import hashlib
import hmac
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSProvider(ABC):
    """Base SMS provider."""

    @abstractmethod
    async def send_sms(self, to: str, text: str) -> bool:
        """Send SMS. Returns True on success."""
        ...


class MockSMSProvider(SMSProvider):
    """Mock SMS for development."""

    async def send_sms(self, to: str, text: str) -> bool:
        masked = to[:3] + "****" + to[-4:] if len(to) >= 7 else "****"
        logger.info(f"[MockSMS] SMS sent to {masked}")
        return True


class CoolSMSProvider(SMSProvider):
    """CoolSMS v4 API provider."""

    BASE_URL = "https://api.solapi.com"

    def __init__(self, api_key: str, api_secret: str, sender: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sender = sender

    def _make_auth_header(self) -> str:
        """Generate HMAC-SHA256 auth header for CoolSMS v4."""
        date = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())
        salt = uuid.uuid4().hex
        signature = hmac.new(
            self.api_secret.encode(),
            (date + salt).encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"HMAC-SHA256 apiKey={self.api_key}, date={date}, salt={salt}, signature={signature}"

    async def send_sms(self, to: str, text: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.BASE_URL}/messages/v4/send",
                    headers={
                        "Authorization": self._make_auth_header(),
                        "Content-Type": "application/json",
                    },
                    json={
                        "message": {
                            "to": to,
                            "from": self.sender,
                            "text": text,
                        }
                    },
                )
                if response.status_code in (200, 202):
                    logger.info(f"SMS sent to {to}")
                    return True
                logger.error(f"CoolSMS error: {response.status_code} {response.text}")
                return False
        except Exception as e:
            logger.error(f"CoolSMS exception: {e}")
            return False


def get_sms_provider() -> SMSProvider:
    """Factory: returns appropriate SMS provider based on config."""
    if (
        settings.SMS_PROVIDER in ("coolsms", "solapi", "solapi(coolsms)")
        and settings.SMS_API_KEY
        and settings.SMS_API_SECRET
        and settings.SMS_SENDER_NUMBER
    ):
        return CoolSMSProvider(
            api_key=settings.SMS_API_KEY,
            api_secret=settings.SMS_API_SECRET,
            sender=settings.SMS_SENDER_NUMBER,
        )
    return MockSMSProvider()


async def send_verification_sms(phone: str, otp: str) -> bool:
    """Send verification SMS with OTP code."""
    provider = get_sms_provider()
    text = f"[StudioBridge] 인증번호: {otp}"
    return await provider.send_sms(phone, text)
