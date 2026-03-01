from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class HandoffNote(Base, UUIDMixin, TimestampMixin):
    """Handoff note attached to a job post for substitute instructors.

    Contains class context (topic, sequence, atmosphere) visible to all,
    and sensitive fields (member_notes, equipment_notes) visible only
    after the instructor's application is accepted.
    """

    __tablename__ = "handoff_notes"

    job_post_id = Column(
        GUID(),
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    author_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_topic = Column(String(200))
    class_sequence_info = Column(Text)
    atmosphere_preference = Column(String(50))
    additional_notes = Column(Text)
    # Sensitive fields - only visible after acceptance
    member_notes = Column(Text)
    equipment_notes = Column(Text)

    # Relationships
    job_post = relationship("JobPost", back_populates="handoff_note")
    author = relationship("User")
