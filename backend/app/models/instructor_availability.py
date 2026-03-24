"""Instructor availability model -- standby pool for dispatch matching."""
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Numeric, JSON, Index
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class InstructorAvailability(Base, UUIDMixin, TimestampMixin):
    """Standby instructor pool -- instructors toggle 'available now'.

    When an instructor marks themselves available, they enter the dispatch
    pool. The system uses their GPS + categories to match against urgent
    job posts within max_distance_km.

    Attributes:
        instructor_id: FK to instructor_profiles.
        user_id: FK to users (denormalized for fast queries).
        is_available: Whether currently accepting dispatch.
        available_until: Auto-off timestamp (nullable = indefinite).
        latitude: Current GPS latitude.
        longitude: Current GPS longitude.
        categories: JSON list of categories they can sub for.
        max_distance_km: Maximum travel distance preference.
    """

    __tablename__ = "instructor_availabilities"
    __table_args__ = (
        Index("ix_availability_spatial", "is_available", "latitude", "longitude"),
    )

    instructor_id = Column(
        GUID(),
        ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_available = Column(Boolean, default=False, nullable=False)
    available_until = Column(DateTime, nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    categories = Column(JSON, default=[])  # ["pilates", "yoga"]
    max_distance_km = Column(Numeric(5, 1), default=10.0, nullable=False)

    # Relationships
    instructor = relationship("InstructorProfile")
    user = relationship("User")
