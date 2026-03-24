from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import ApplicationStatus


class Application(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_post_id", "instructor_id", name="uq_application_job_instructor"),
    )

    job_post_id = Column(GUID(), ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default=ApplicationStatus.PENDING.value, nullable=False, index=True)
    cover_letter = Column(Text)
    contact_revealed = Column(Boolean, default=False, nullable=False)  # Contact info revealed to both parties
    contact_revealed_at = Column(DateTime, nullable=True)  # When contact was revealed
    dispatch_record_id = Column(GUID(), ForeignKey("dispatch_records.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    job_post = relationship("JobPost", back_populates="applications")
    instructor = relationship("InstructorProfile", back_populates="applications")
    offer = relationship("Offer", back_populates="application", uselist=False)
    reviews = relationship("Review", back_populates="application")
