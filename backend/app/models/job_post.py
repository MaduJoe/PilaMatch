from sqlalchemy import Column, String, Text, Date, Time, DateTime, ForeignKey, Numeric, Integer, JSON, Boolean
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
    payment_method = Column(String(50), nullable=True)  # bank_transfer/cash/etc
    terms_agreed = Column(Boolean, default=False, nullable=False)  # Checklist agreement
    preferred_style = Column(JSON, default=dict)  # {correction_style, class_atmosphere, intensity_level}

    # Dispatch system (v5.0)
    dispatch_mode = Column(String(20), default="manual", nullable=False)  # manual | auto_dispatch
    urgency_score = Column(Numeric(5, 1), nullable=True)  # 0-100, computed from time-until-class
    dispatch_wave = Column(Integer, default=0, nullable=False)  # current wave number
    dispatch_started_at = Column(DateTime, nullable=True)
    auto_accepted_at = Column(DateTime, nullable=True)  # when auto-dispatch was accepted
    matched_instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    studio = relationship("StudioProfile", back_populates="job_posts")
    applications = relationship("Application", back_populates="job_post", cascade="all, delete-orphan", passive_deletes=True)
    handoff_note = relationship("HandoffNote", back_populates="job_post", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
