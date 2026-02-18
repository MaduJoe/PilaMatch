"""Application template model for Premium members (v3.0 Phase 2)."""
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class ApplicationTemplate(Base, UUIDMixin, TimestampMixin):
    """Templates for application cover letters (Premium feature)."""

    __tablename__ = "application_templates"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", backref="application_templates")