from sqlalchemy import Column, String, Text, Date, Time, ForeignKey, Numeric, Integer, JSON, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID
from app.models.enums import JobPostStatus


class JobPost(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "job_posts"

    studio_id = Column(GUID(), ForeignKey("studio_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(20), nullable=False, index=True)
    job_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default=JobPostStatus.OPEN.value, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    total_sessions = Column(Integer, default=1)
    required_experience_years = Column(Integer, default=0)
    required_certifications = Column(JSON, default=[])
    region = Column(String(100), index=True)
    address = Column(String(500))
    latitude = Column(Numeric(10, 7), nullable=True)  # GPS latitude
    longitude = Column(Numeric(10, 7), nullable=True)  # GPS longitude
    is_urgent = Column(Boolean, default=False, nullable=False, index=True)  # Urgent substitute flag
    application_count = Column(Integer, default=0)

    # Relationships
    studio = relationship("StudioProfile", back_populates="job_posts")
    applications = relationship("Application", back_populates="job_post")
