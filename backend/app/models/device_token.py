from sqlalchemy import Column, String, Boolean, ForeignKey

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class DeviceToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "device_tokens"

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # "ios" / "android" / "web"
    is_active = Column(Boolean, default=True, nullable=False)
