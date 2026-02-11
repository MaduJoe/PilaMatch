from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import OfferStatus


class Offer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "offers"

    application_id = Column(GUID(), ForeignKey("applications.id", ondelete="CASCADE"), unique=True, index=True)
    studio_id = Column(GUID(), ForeignKey("studio_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default=OfferStatus.PENDING.value, nullable=False, index=True)
    message = Column(Text)
    proposed_rate = Column(Numeric(10, 2), nullable=False)
    expires_at = Column(DateTime)

    # Relationships
    application = relationship("Application", back_populates="offer")
    contract = relationship("Contract", back_populates="offer", uselist=False)
