"""Handoff template service -- reusable handoff note templates for studios."""

import logging
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.handoff_template import HandoffTemplate
from app.models.handoff_note import HandoffNote
from app.models.studio import StudioProfile

logger = logging.getLogger(__name__)

MAX_TEMPLATES_PER_STUDIO = 20

class HandoffTemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_template(
        self,
        user_id: str,
        name: str,
        class_topic: str = None,
        class_sequence_info: str = None,
        atmosphere_preference: str = None,
        member_caution_tags: list[str] = None,
        member_free_text: str = None,
        equipment_notes: str = None,
        additional_notes: str = None,
    ) -> HandoffTemplate:
        """Create a new handoff template. Max 20 per studio."""
        studio = await self._get_studio(user_id)

        # Check limit
        count_result = await self.db.execute(
            select(func.count()).select_from(HandoffTemplate).where(
                HandoffTemplate.studio_id == studio.id
            )
        )
        count = count_result.scalar_one()
        if count >= MAX_TEMPLATES_PER_STUDIO:
            raise ValueError("TEMPLATE_LIMIT_REACHED")

        template = HandoffTemplate(
            studio_id=studio.id,
            name=name,
            class_topic=class_topic,
            class_sequence_info=class_sequence_info,
            atmosphere_preference=atmosphere_preference,
            member_caution_tags=member_caution_tags or [],
            member_free_text=member_free_text,
            equipment_notes=equipment_notes,
            additional_notes=additional_notes,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def list_templates(self, user_id: str) -> list[HandoffTemplate]:
        """List all templates for the user's studio, sorted by usage count desc."""
        studio = await self._get_studio(user_id)
        result = await self.db.execute(
            select(HandoffTemplate)
            .where(HandoffTemplate.studio_id == studio.id)
            .order_by(HandoffTemplate.usage_count.desc())
        )
        return list(result.scalars().all())

    async def update_template(
        self,
        user_id: str,
        template_id: str,
        **kwargs,
    ) -> HandoffTemplate:
        """Update a template. Only the owning studio can update."""
        template = await self._get_owned_template(user_id, template_id)
        for key, value in kwargs.items():
            if hasattr(template, key) and value is not None:
                setattr(template, key, value)
        await self.db.flush()
        return template

    async def delete_template(self, user_id: str, template_id: str) -> None:
        """Delete a template."""
        template = await self._get_owned_template(user_id, template_id)
        await self.db.delete(template)
        await self.db.flush()

    async def apply_template(
        self,
        user_id: str,
        template_id: str,
        job_post_id: str,
    ) -> HandoffNote:
        """Apply a template to a job post's handoff note.
        Copies template fields to the handoff note and increments usage_count."""
        template = await self._get_owned_template(user_id, template_id)

        # Get or create handoff note
        note_result = await self.db.execute(
            select(HandoffNote).where(HandoffNote.job_post_id == job_post_id)
        )
        note = note_result.scalar_one_or_none()
        if not note:
            raise ValueError("HANDOFF_NOTE_NOT_FOUND")

        # Copy fields
        note.class_topic = template.class_topic
        note.class_sequence_info = template.class_sequence_info
        note.atmosphere_preference = template.atmosphere_preference
        note.member_caution_tags = template.member_caution_tags or []
        note.member_free_text = template.member_free_text
        note.equipment_notes = template.equipment_notes
        note.additional_notes = template.additional_notes
        note.template_id = str(template.id)

        # Calculate completeness score
        note.completeness_score = Decimal(str(calculate_completeness_score(note)))

        # Increment usage count
        template.usage_count = (template.usage_count or 0) + 1

        await self.db.flush()
        return note

    async def _get_studio(self, user_id: str) -> StudioProfile:
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.user_id == user_id)
        )
        studio = result.scalar_one_or_none()
        if not studio:
            raise ValueError("STUDIO_NOT_FOUND")
        return studio

    async def _get_owned_template(self, user_id: str, template_id: str) -> HandoffTemplate:
        studio = await self._get_studio(user_id)
        result = await self.db.execute(
            select(HandoffTemplate).where(
                HandoffTemplate.id == template_id,
                HandoffTemplate.studio_id == studio.id,
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError("TEMPLATE_NOT_FOUND")
        return template


def calculate_completeness_score(note: HandoffNote) -> float:
    """Calculate handoff note completeness score (0.0-1.0).

    Weights:
    - class_topic: 0.20
    - class_sequence_info (>20 chars): 0.25
    - atmosphere_preference: 0.15
    - member_caution_tags or member_free_text: 0.20
    - equipment_notes: 0.10
    - additional_notes: 0.10
    """
    score = 0.0
    if note.class_topic:
        score += 0.20
    if note.class_sequence_info and len(note.class_sequence_info) > 20:
        score += 0.25
    if note.atmosphere_preference:
        score += 0.15
    if (note.member_caution_tags and len(note.member_caution_tags) > 0) or \
       (note.member_free_text and len(note.member_free_text) > 10):
        score += 0.20
    if note.equipment_notes:
        score += 0.10
    if note.additional_notes:
        score += 0.10
    return round(score, 2)
