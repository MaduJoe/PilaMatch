from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class InstructorProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "instructor_profiles"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    bio = Column(Text)
    phone = Column(String(20))
    profile_image_url = Column(String(500))
    categories = Column(JSON, default=[])  # Array of Category values
    specialties = Column(JSON, default=[])
    certifications = Column(JSON, default=[])
    experience_years = Column(Integer, default=0)
    hourly_rate_min = Column(Numeric(10, 2))
    hourly_rate_max = Column(Numeric(10, 2))
    available_regions = Column(JSON, default=[])
    latitude = Column(Numeric(10, 7), nullable=True)  # GPS latitude
    longitude = Column(Numeric(10, 7), nullable=True)  # GPS longitude
    photo_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    rating_average = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    completed_substitute_count = Column(Integer, default=0)  # 완료된 대타 건수
    teaching_style = Column(JSON, default=dict)  # {correction_style, class_atmosphere, intensity_level, music_preference}

    # Dispatch & Trust verification stats (v5.0)
    dispatch_success_rate = Column(Numeric(4, 3), default=0, nullable=False)  # 0.000-1.000
    total_dispatches = Column(Integer, default=0, nullable=False)
    total_dispatch_accepts = Column(Integer, default=0, nullable=False)
    total_checkins = Column(Integer, default=0, nullable=False)
    avg_checkin_distance_m = Column(Numeric(8, 1), nullable=True)
    total_completions = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="instructor_profile")
    applications = relationship("Application", back_populates="instructor")
    reviews_received = relationship("Review", back_populates="reviewee_instructor", foreign_keys="Review.reviewee_instructor_id")
