from sqlalchemy import Column, String, Text, ForeignKey

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import TicketStatus


class SupportTicket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "support_tickets"

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default=TicketStatus.OPEN.value, nullable=False, index=True)
    resolution_note = Column(Text)
