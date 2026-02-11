import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.types import TypeDecorator, CHAR

from app.db.session import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Always uses CHAR(36) to store UUIDs as strings for compatibility.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
