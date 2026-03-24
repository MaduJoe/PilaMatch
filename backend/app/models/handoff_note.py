from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, JSON
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

    # Template & quality (v5.0)
    template_id = Column(GUID(), ForeignKey("handoff_templates.id", ondelete="SET NULL"), nullable=True)
    completeness_score = Column(Numeric(3, 2), default=0, nullable=False)  # 0.00-1.00
    # Sensitive info as tags (법적 고려: 개인정보보호법 제23조)
    member_caution_tags = Column(JSON, default=[])  # ["허리_제한", "과신전_주의"]
    member_free_text = Column(Text, nullable=True)  # limited operational notes (no real names/specific conditions)
    # Post-lesson feedback from instructor
    instructor_feedback = Column(Text, nullable=True)
    instructor_feedback_at = Column(DateTime, nullable=True)

    # Relationships
    job_post = relationship("JobPost", back_populates="handoff_note")
    author = relationship("User")
