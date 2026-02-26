import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class NotificationType:
    NEW_APPLICATION = "NEW_APPLICATION"
    OFFER_RECEIVED = "OFFER_RECEIVED"
    CONTRACT_STATUS = "CONTRACT_STATUS"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    NO_SHOW_REPORTED = "NO_SHOW_REPORTED"
    CHAT_MESSAGE = "CHAT_MESSAGE"


class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # NEW_APPLICATION, OFFER_RECEIVED, etc.
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    data_json = Column(JSON, nullable=True)  # 추가 데이터 (관련 ID 등)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
