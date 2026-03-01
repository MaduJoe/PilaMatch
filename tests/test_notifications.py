"""Tests for notification service and API (Task 5)."""
import pytest
from httpx import AsyncClient


async def _signup_and_get_token(client: AsyncClient, email: str) -> str:
    """Helper: signup and return token."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "Notif Test",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_notification_service_send():
    """Test NotificationService.send() stores notification."""
    from app.services.notification import NotificationService, _notifications

    service = NotificationService()
    user_id = "test-user-001"

    # Clear any existing notifications
    _notifications[user_id] = []

    nid = await service.send(
        user_id=user_id,
        type="NEW_APPLICATION",
        title="Test Title",
        body="Test Body",
        data={"key": "value"},
    )

    assert nid
    notifs = await service.get_notifications(user_id)
    assert len(notifs) == 1
    assert notifs[0]["title"] == "Test Title"
    assert notifs[0]["is_read"] is False


@pytest.mark.asyncio
async def test_notification_service_mark_read():
    """Test marking notification as read."""
    from app.services.notification import NotificationService, _notifications

    service = NotificationService()
    user_id = "test-user-002"
    _notifications[user_id] = []

    nid = await service.send(user_id, "TEST", "Title", "Body")

    # Verify unread count
    count = await service.get_unread_count(user_id)
    assert count == 1

    # Mark as read
    success = await service.mark_read(nid, user_id)
    assert success is True

    # Verify unread count is 0
    count = await service.get_unread_count(user_id)
    assert count == 0


@pytest.mark.asyncio
async def test_notification_service_bulk_send():
    """Test sending to multiple users."""
    from app.services.notification import NotificationService, _notifications

    service = NotificationService()
    user_ids = ["bulk-1", "bulk-2", "bulk-3"]
    for uid in user_ids:
        _notifications[uid] = []

    ids = await service.send_bulk(user_ids, "TEST", "Bulk Title", "Bulk Body")
    assert len(ids) == 3

    for uid in user_ids:
        notifs = await service.get_notifications(uid)
        assert len(notifs) == 1


@pytest.mark.asyncio
async def test_register_device_token(client: AsyncClient):
    """Test device token registration endpoint."""
    token = await _signup_and_get_token(client, "notif_device@test.com")

    response = await client.post(
        "/api/v1/notifications/device-token",
        headers={"Authorization": f"Bearer {token}"},
        json={"token": "fcm-token-12345", "platform": "fcm"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_notifications_empty(client: AsyncClient):
    """Get notifications when empty should return empty list."""
    token = await _signup_and_get_token(client, "notif_empty@test.com")

    response = await client.get(
        "/api/v1/notifications/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notifications"] == []
    assert data["unread_count"] == 0


@pytest.mark.asyncio
async def test_get_unread_count(client: AsyncClient):
    """Test unread count endpoint."""
    token = await _signup_and_get_token(client, "notif_unread@test.com")

    response = await client.get(
        "/api/v1/notifications/unread-count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_convenience_functions():
    """Test convenience notification functions."""
    from app.services.notification import (
        notify_new_application,
        notify_offer_received,
        notify_contract_status,
        _notifications,
    )

    uid = "convenience-test"
    _notifications[uid] = []

    await notify_new_application(None, uid, "TestInstructor", "TestJob")
    await notify_offer_received(None, uid, "TestStudio")
    await notify_contract_status(None, uid, "completed", "contract-123")

    from app.services.notification import NotificationService
    service = NotificationService()
    notifs = await service.get_notifications(uid)
    assert len(notifs) == 3
