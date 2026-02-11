from sqlalchemy import Column, String, Text, ForeignKey

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import ReportStatus


class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    reporter_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    reported_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String(20), nullable=False)
    status = Column(String(20), default=ReportStatus.OPEN.value, nullable=False, index=True)
    description = Column(Text, nullable=False)
    resolution_note = Column(Text)


class Block(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "blocks"

    blocker_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    blocked_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
