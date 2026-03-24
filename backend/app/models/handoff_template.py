"""Handoff template model -- reusable handoff note templates for studios."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class HandoffTemplate(Base, UUIDMixin, TimestampMixin):
    """Reusable handoff note templates for studios.

    Studios can save frequently-used class context as templates,
    reducing the time to create handoff notes for recurring class types.

    Attributes:
        studio_id: FK to studio_profiles.
        name: Template name for quick identification.
        class_topic: The class topic / theme.
        class_sequence_info: Sequence / flow description.
        atmosphere_preference: Desired class atmosphere.
        member_caution_tags: Pre-defined caution tags (JSON list).
        member_free_text: Limited operational notes (no PII).
        equipment_notes: Equipment setup notes.
        additional_notes: Any other context.
        usage_count: How many times this template has been used.
    """

    __tablename__ = "handoff_templates"

    studio_id = Column(
        GUID(),
        ForeignKey("studio_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)  # template name
    class_topic = Column(String(200), nullable=True)
    class_sequence_info = Column(Text, nullable=True)
    atmosphere_preference = Column(String(50), nullable=True)
    member_caution_tags = Column(JSON, default=[])  # ["허리_제한", "과신전_주의"]
    member_free_text = Column(Text, nullable=True)  # limited operational notes
    equipment_notes = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)

    # Relationships
    studio = relationship("StudioProfile")
