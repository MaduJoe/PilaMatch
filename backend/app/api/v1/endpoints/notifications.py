"""Notification API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models import User
from app.services.notification import NotificationService

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


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count."""
    service = NotificationService(db)
    count = await service.get_unread_count(str(current_user.id))
    return {"unread_count": count}
