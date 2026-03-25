"""Check-in record model -- GPS check-in verification at studio location."""
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, GUID


class CheckinRecord(Base, UUIDMixin):
    """GPS check-in verification -- instructor checks in at studio location.

    When an instructor arrives at the studio, they submit their GPS coordinates.
    The system compares against the studio's known location and marks
    the check-in as valid if within 200m.

    No TimestampMixin needed -- checked_in_at serves as the creation timestamp.

    Attributes:
        job_post_id: The job being checked into.
        application_id: The accepted application (nullable for dispatch flow).
        instructor_user_id: The instructor's user id.
        studio_latitude/longitude: The studio's known GPS coordinates.
        checkin_latitude/longitude: The instructor's reported GPS coordinates.
        distance_meters: Calculated Haversine distance.
        is_valid: Whether distance_meters <= 200.
        checked_in_at: Timestamp of the check-in.
    """

    __tablename__ = "checkin_records"

    job_post_id = Column(
        GUID(),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = Column(
        GUID(),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=True,
    )
    instructor_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    studio_latitude = Column(Numeric(10, 7), nullable=False)
    studio_longitude = Column(Numeric(10, 7), nullable=False)
    checkin_latitude = Column(Numeric(10, 7), nullable=False)
    checkin_longitude = Column(Numeric(10, 7), nullable=False)
    distance_meters = Column(Numeric(8, 1), nullable=False)  # calculated distance
    is_valid = Column(Boolean, nullable=False)  # within 200m
    checked_in_at = Column(DateTime, nullable=False)
    retry_count = Column(Integer, nullable=False, default=0, server_default="0")

    # Relationships
    job_post = relationship("JobPost")
