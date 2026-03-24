"""Dispatch record model -- tracks each dispatch attempt in cascading dispatch."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class DispatchRecord(Base, UUIDMixin, TimestampMixin):
    """Tracks each dispatch attempt in the cascading dispatch system.

    When auto-dispatch is triggered, the system sends notifications in waves.
    Each notification to an instructor creates one DispatchRecord. The record
    captures the matching snapshot at dispatch time for audit and analytics.

    Attributes:
        job_post_id: The urgent job being dispatched.
        instructor_id: The instructor receiving the dispatch.
        user_id: Denormalized user FK for fast queries.
        wave_number: Which wave of dispatch (1, 2, 3...).
        status: dispatched/accepted/declined/timeout/cancelled.
        dispatched_at: When the push notification was sent.
        responded_at: When the instructor responded (nullable).
        distance_km: Distance to studio at dispatch time.
        matching_score: 5-factor matching score snapshot.
        reliability_score: Dispatch priority score (tier + history).
    """

    __tablename__ = "dispatch_records"
    __table_args__ = (
        Index("ix_dispatch_job_status", "job_post_id", "status"),
    )

    job_post_id = Column(
        GUID(),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
    )
    wave_number = Column(Integer, nullable=False)
    status = Column(String(20), default="dispatched", nullable=False)  # dispatched/accepted/declined/timeout/cancelled
    dispatched_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    distance_km = Column(Numeric(6, 2), nullable=True)
    matching_score = Column(Integer, nullable=True)  # snapshot at dispatch time
    reliability_score = Column(Integer, nullable=True)  # dispatch priority score

    # Relationships
    job_post = relationship("JobPost")
    instructor = relationship("InstructorProfile")
