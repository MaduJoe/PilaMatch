from sqlalchemy import Column, String, Boolean, JSON

from app.db.session import Base
from app.models.base import TimestampMixin


class WebhookEvent(Base, TimestampMixin):
    __tablename__ = "webhook_events"

    transmission_id = Column(String(100), primary_key=True)
    event_type = Column(String(50), nullable=False)
    payment_key = Column(String(200), index=True)
    processed = Column(Boolean, default=False, nullable=False)
    payload = Column(JSON)
