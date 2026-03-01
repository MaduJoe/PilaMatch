"""TossPayments webhook signature verification utility."""

import hmac
import hashlib
import logging
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_toss_webhook_signature(
    payload: bytes,
    signature: str,
    transmission_time: str = "",
    transmission_id: str = "",
) -> bool:
    """Verify TossPayments v2 webhook HMAC-SHA256 signature."""
    if not settings.TOSS_WEBHOOK_SECRET:
        return True  # Skip verification in development

    # Replay prevention: reject webhooks older than 5 minutes
    if transmission_time:
        try:
            webhook_time = datetime.fromisoformat(transmission_time.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            if abs((now_utc - webhook_time).total_seconds()) > 300:
                logger.warning(f"Webhook replay rejected: transmission_time={transmission_time}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Invalid webhook transmission_time: {transmission_time}")
            return False

    # v2 signature: HMAC-SHA256(secret, transmission_id.time.payload)
    if transmission_id and transmission_time:
        message = f"{transmission_id}.{transmission_time}.{payload.decode()}"
        expected = hmac.new(
            settings.TOSS_WEBHOOK_SECRET.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
    else:
        # Fallback: legacy v1 verification (body-only HMAC)
        expected = hmac.new(
            settings.TOSS_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

    return hmac.compare_digest(expected, signature)
