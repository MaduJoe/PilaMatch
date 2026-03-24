"""Push notification service with FCM/APNs support (mock mode by default).

Uses Redis for persistence when available, falling back to in-memory storage.
When a Notification model is added (DATA worktree), this will persist to DB.
"""

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _get_redis():
    """Get Redis connection for notification storage. Returns None if unavailable."""
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None


# Notification types
class NotificationType:
    NEW_APPLICATION = "NEW_APPLICATION"
    OFFER_RECEIVED = "OFFER_RECEIVED"
    CONTRACT_STATUS = "CONTRACT_STATUS"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    NO_SHOW_REPORTED = "NO_SHOW_REPORTED"
    CHAT_MESSAGE = "CHAT_MESSAGE"
    LESSON_REMINDER = "LESSON_REMINDER"
    URGENT_SUBSTITUTE = "URGENT_SUBSTITUTE"


# In-memory notification store (mock mode)
_notifications: dict[str, list[dict]] = defaultdict(list)
# Device token store: user_id -> [tokens]
_device_tokens: dict[str, list[str]] = defaultdict(list)


class NotificationService:
    """FCM + APNs integrated notification service. Mock mode stores in memory."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def send(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> str:
        """Send a notification to a user. Returns notification ID."""
        notification_id = str(uuid.uuid4())
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "type": type,
            "title": title,
            "body": body,
            "data": data or {},
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
        }

        r = _get_redis()
        if r:
            r.lpush(f"notifications:{user_id}", json.dumps(notification))
            r.expire(f"notifications:{user_id}", 86400 * 30)  # 30 days TTL
        else:
            _notifications[user_id].append(notification)

        # In production, send to FCM/APNs
        if r:
            tokens = list(r.smembers(f"device_tokens:{user_id}"))
        else:
            tokens = _device_tokens.get(user_id, [])
        if tokens:
            await self._send_push(tokens, title, body, data)

        logger.info(
            f"[NOTIFICATION] user={user_id} type={type} title={title}"
        )
        return notification_id

    async def send_bulk(
        self,
        user_ids: list[str],
        type: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> list[str]:
        """Send notification to multiple users."""
        ids = []
        for user_id in user_ids:
            nid = await self.send(user_id, type, title, body, data)
            ids.append(nid)
        return ids

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        r = _get_redis()
        if r:
            key = f"notifications:{user_id}"
            items = r.lrange(key, 0, -1)
            for i, raw in enumerate(items):
                n = json.loads(raw)
                if n["id"] == notification_id:
                    n["is_read"] = True
                    r.lset(key, i, json.dumps(n))
                    return True
            return False
        else:
            for n in _notifications.get(user_id, []):
                if n["id"] == notification_id:
                    n["is_read"] = True
                    return True
            return False

    async def mark_all_read(self, user_id: str) -> int:
        """Mark all unread notifications as read for a user. Returns count updated."""
        count = 0
        r = _get_redis()
        if r:
            key = f"notifications:{user_id}"
            items = r.lrange(key, 0, -1)
            for i, raw in enumerate(items):
                n = json.loads(raw)
                if not n.get("is_read"):
                    n["is_read"] = True
                    r.lset(key, i, json.dumps(n))
                    count += 1
        else:
            for n in _notifications.get(user_id, []):
                if not n.get("is_read"):
                    n["is_read"] = True
                    count += 1
        logger.info(f"[NOTIFICATION] mark_all_read user={user_id} count={count}")
        return count

    async def get_notifications(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> list[dict]:
        """Get paginated notifications for a user."""
        r = _get_redis()
        if r:
            key = f"notifications:{user_id}"
            # Redis list is already in reverse chronological order (lpush)
            items = r.lrange(key, skip, skip + limit - 1)
            return [json.loads(raw) for raw in items]
        else:
            all_notifs = _notifications.get(user_id, [])
            # Sort by created_at desc
            sorted_notifs = sorted(
                all_notifs, key=lambda x: x["created_at"], reverse=True
            )
            return sorted_notifs[skip : skip + limit]

    async def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for a user."""
        r = _get_redis()
        if r:
            items = r.lrange(f"notifications:{user_id}", 0, -1)
            return sum(1 for raw in items if not json.loads(raw).get("is_read"))
        else:
            return sum(
                1 for n in _notifications.get(user_id, []) if not n["is_read"]
            )

    async def register_device_token(
        self, user_id: str, token: str, platform: str = "fcm"
    ) -> None:
        """Register a device token for push notifications."""
        r = _get_redis()
        if r:
            r.sadd(f"device_tokens:{user_id}", token)
        else:
            tokens = _device_tokens[user_id]
            if token not in tokens:
                tokens.append(token)
        logger.info(f"Registered device token for user {user_id}: {platform}")

    async def _send_push(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> None:
        """Send push via FCM. Falls back to mock if firebase-admin not configured."""
        try:
            import firebase_admin
            from firebase_admin import messaging

            if not firebase_admin._apps:
                logger.warning("[FCM] Firebase not initialized, skipping push")
                return

            # Convert data values to strings (FCM requirement)
            str_data = {k: str(v) for k, v in (data or {}).items()}

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=str_data,
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default",
                        channel_id="urgent_substitute",
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1,
                        ),
                    ),
                ),
            )

            response = messaging.send_each_for_multicast(message)
            logger.info(
                f"[FCM] sent={response.success_count} failed={response.failure_count}"
            )

            # Clean up invalid tokens
            for idx, send_response in enumerate(response.responses):
                if send_response.exception:
                    error_code = send_response.exception.code
                    if error_code in ("NOT_FOUND", "UNREGISTERED"):
                        await self._remove_token(tokens[idx])

        except ImportError:
            logger.info(f"[MOCK PUSH] tokens={len(tokens)} title={title}")
        except Exception as e:
            logger.error(f"[FCM ERROR] {e}")

    async def _remove_token(self, token: str) -> None:
        """Remove an invalid device token."""
        r = _get_redis()
        if r:
            # Scan all device_tokens sets and remove
            for key in r.scan_iter("device_tokens:*"):
                r.srem(key, token)
        else:
            for user_tokens in _device_tokens.values():
                if token in user_tokens:
                    user_tokens.remove(token)


# --- Convenience functions for notification triggers ---

async def notify_new_application(
    db: AsyncSession, studio_user_id: str, instructor_name: str, job_title: str
) -> None:
    """Notify studio about a new application."""
    service = NotificationService(db)
    await service.send(
        user_id=studio_user_id,
        type=NotificationType.NEW_APPLICATION,
        title="새로운 지원",
        body=f"{instructor_name}님이 '{job_title}' 공고에 지원했습니다.",
        data={"type": "application"},
    )


async def notify_offer_received(
    db: AsyncSession, instructor_user_id: str, studio_name: str
) -> None:
    """Notify instructor about a received offer."""
    service = NotificationService(db)
    await service.send(
        user_id=instructor_user_id,
        type=NotificationType.OFFER_RECEIVED,
        title="새로운 오퍼",
        body=f"{studio_name}에서 오퍼를 보냈습니다.",
        data={"type": "offer"},
    )


async def notify_contract_status(
    db: AsyncSession, user_id: str, status: str, contract_id: str
) -> None:
    """Notify user about contract status change."""
    status_messages = {
        "in_progress": "계약이 시작되었습니다.",
        "completed": "계약이 완료되었습니다.",
        "cancelled": "계약이 취소되었습니다.",
        "pending_completion": "상대방이 완료를 확인했습니다. 확인해주세요.",
    }
    service = NotificationService(db)
    await service.send(
        user_id=user_id,
        type=NotificationType.CONTRACT_STATUS,
        title="계약 상태 변경",
        body=status_messages.get(status, f"계약 상태가 '{status}'로 변경되었습니다."),
        data={"type": "contract", "contract_id": contract_id},
    )


async def send_lesson_reminders(db: AsyncSession) -> int:
    """Send reminders for upcoming lessons. Call via cron every hour.

    Sends reminders for contracts in IN_PROGRESS status:
    - 24 hours before: "내일 수업이 있습니다"
    - 1 hour before: "1시간 후 수업이 시작됩니다"

    Returns:
        Number of reminders sent
    """
    from sqlalchemy import select, and_
    from app.models import Contract, ContractStatus, InstructorProfile, StudioProfile, User

    now = datetime.utcnow()
    today = now.date()
    tomorrow = today + __import__("datetime").timedelta(days=1)

    service = NotificationService(db)
    sent = 0

    # Find active contracts for today or tomorrow
    result = await db.execute(
        select(Contract).where(
            and_(
                Contract.status.in_([
                    ContractStatus.CONFIRMED.value,
                    ContractStatus.IN_PROGRESS.value,
                ]),
                Contract.date.in_([today, tomorrow]),
            )
        )
    )
    contracts = result.scalars().all()

    for contract in contracts:
        # Determine reminder type
        is_tomorrow = contract.date == tomorrow
        is_today = contract.date == today

        if is_today and contract.start_time:
            # Check if within 1-2 hours
            from datetime import timedelta
            lesson_start = datetime.combine(today, contract.start_time)
            time_until = (lesson_start - now).total_seconds() / 3600
            if not (0.5 <= time_until <= 1.5):
                continue
            reminder_body = f"오늘 {contract.start_time.strftime('%H:%M')} 수업이 1시간 후 시작됩니다."
            reminder_title = "수업 시작 임박"
        elif is_tomorrow:
            reminder_body = f"내일 {contract.start_time.strftime('%H:%M')} 수업이 예정되어 있습니다."
            reminder_title = "내일 수업 알림"
        else:
            continue

        # Get user IDs for both parties
        instructor_result = await db.execute(
            select(InstructorProfile.user_id).where(
                InstructorProfile.id == contract.instructor_id
            )
        )
        instructor_user_id = instructor_result.scalar_one_or_none()

        studio_result = await db.execute(
            select(StudioProfile.user_id).where(
                StudioProfile.id == contract.studio_id
            )
        )
        studio_user_id = studio_result.scalar_one_or_none()

        for uid in [instructor_user_id, studio_user_id]:
            if uid:
                await service.send(
                    user_id=str(uid),
                    type=NotificationType.LESSON_REMINDER,
                    title=reminder_title,
                    body=reminder_body,
                    data={"type": "lesson_reminder", "contract_id": str(contract.id)},
                )
                sent += 1

    return sent


async def notify_urgent_substitute(
    db: AsyncSession,
    instructor_user_ids: list[str],
    studio_name: str,
    job_title: str,
    job_id: str,
    distance_km: Optional[float] = None,
) -> list[str]:
    """Notify nearby instructors about an urgent substitute job."""
    service = NotificationService(db)
    distance_text = f" ({distance_km:.1f}km)" if distance_km else ""
    return await service.send_bulk(
        user_ids=instructor_user_ids,
        type=NotificationType.URGENT_SUBSTITUTE,
        title=f"긴급 대타{distance_text}",
        body=f"{studio_name} — {job_title}",
        data={"type": "urgent_substitute", "job_id": job_id},
    )
