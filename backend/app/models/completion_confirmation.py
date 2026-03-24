"""Completion confirmation model -- mutual confirmation that lesson happened."""
from sqlalchemy import Column, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class CompletionConfirmation(Base, UUIDMixin, TimestampMixin):
    """Mutual completion confirmation -- both sides confirm lesson happened.

    After a lesson, both the studio and instructor confirm completion.
    Once both confirm, is_complete flips to True. If neither party confirms
    within 24 hours, auto_completed is set via a background task.

    Attributes:
        job_post_id: The job being confirmed (unique -- one confirmation per job).
        application_id: The accepted application.
        studio_user_id: The studio's user id.
        instructor_user_id: The instructor's user id.
        studio_confirmed: Whether the studio has confirmed.
        instructor_confirmed: Whether the instructor has confirmed.
        studio_confirmed_at: Timestamp of studio confirmation.
        instructor_confirmed_at: Timestamp of instructor confirmation.
        is_complete: True when both have confirmed.
        auto_completed: True if auto-confirmed after 24h.
    """

    __tablename__ = "completion_confirmations"

    job_post_id = Column(
        GUID(),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    application_id = Column(
        GUID(),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    studio_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    instructor_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    studio_confirmed = Column(Boolean, default=False, nullable=False)
    instructor_confirmed = Column(Boolean, default=False, nullable=False)
    studio_confirmed_at = Column(DateTime, nullable=True)
    instructor_confirmed_at = Column(DateTime, nullable=True)
    is_complete = Column(Boolean, default=False, nullable=False)  # both confirmed
    auto_completed = Column(Boolean, default=False, nullable=False)  # auto-confirmed after 24h

    # Relationships
    job_post = relationship("JobPost")
    application = relationship("Application")
