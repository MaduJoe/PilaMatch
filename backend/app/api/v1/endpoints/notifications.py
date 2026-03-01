"""Notification API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.notification import NotificationService, send_lesson_reminders

logger = logging.getLogger(__name__)

router = APIRouter()


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str = "fcm"  # fcm / apns


@router.post("/device-token", status_code=status.HTTP_200_OK)
async def register_device_token(
    data: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a device token for push notifications."""
    service = NotificationService(db)
    await service.register_device_token(
        str(current_user.id), data.token, data.platform
    )
    return {"message": "디바이스 토큰이 등록되었습니다"}


@router.get("/")
async def get_notifications(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notification list with pagination."""
    service = NotificationService(db)
    notifications = await service.get_notifications(
        str(current_user.id), skip=skip, limit=limit
    )
    unread = await service.get_unread_count(str(current_user.id))

    return {
        "notifications": notifications,
        "unread_count": unread,
        "skip": skip,
        "limit": limit,
    }


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    service = NotificationService(db)
    success = await service.mark_read(notification_id, str(current_user.id))

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": "알림을 찾을 수 없습니다"},
        )

    return {"message": "알림이 읽음 처리되었습니다"}


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the current user."""
    service = NotificationService(db)
    count = await service.mark_all_read(str(current_user.id))
    return {"message": f"{count}개 알림이 읽음 처리되었습니다", "count": count}


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count."""
    service = NotificationService(db)
    count = await service.get_unread_count(str(current_user.id))
    return {"unread_count": count}


class CronSecretRequest(BaseModel):
    cron_secret: str


@router.post("/send-reminders")
async def trigger_lesson_reminders(
    request: CronSecretRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send lesson reminders for upcoming classes (CRON_SECRET protected).

    Call via cron every hour. Sends reminders:
    - 24 hours before: "내일 수업이 있습니다"
    - 1 hour before: "1시간 후 수업이 시작됩니다"
    """
    if not settings.CRON_SECRET or request.cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Invalid cron secret"},
        )

    sent = await send_lesson_reminders(db)
    logger.info(f"Lesson reminders sent: {sent}")
    return {"sent": sent}
