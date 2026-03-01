"""Handoff Note service -- CRUD for substitute class handoff notes.

Allows studios to attach contextual notes to job posts so that
substitute instructors understand the class before arriving.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.handoff_note import HandoffNote
from app.schemas.handoff_note import HandoffNoteCreate

logger = logging.getLogger(__name__)


class HandoffNoteService:
    """Service for managing handoff notes attached to job posts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_or_update(
        self,
        job_post_id: UUID,
        author_user_id: UUID,
        data: HandoffNoteCreate,
    ) -> HandoffNote:
        """Create a new handoff note or update the existing one for a job post.

        Args:
            job_post_id: The job post to attach the note to.
            author_user_id: The user creating/updating the note.
            data: The handoff note fields.

        Returns:
            The created or updated HandoffNote instance.
        """
        result = await self.db.execute(
            select(HandoffNote).where(HandoffNote.job_post_id == job_post_id)
        )
        note = result.scalar_one_or_none()

        if note:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(note, field, value)
            logger.info(
                "handoff_note_updated job_post_id=%s author=%s",
                job_post_id,
                author_user_id,
            )
        else:
            note = HandoffNote(
                job_post_id=job_post_id,
                author_user_id=author_user_id,
                **data.model_dump(),
            )
            self.db.add(note)
            logger.info(
                "handoff_note_created job_post_id=%s author=%s",
                job_post_id,
                author_user_id,
            )

        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_by_job_post(self, job_post_id: UUID) -> Optional[HandoffNote]:
        """Retrieve the handoff note for a given job post.

        Args:
            job_post_id: The job post ID to look up.

        Returns:
            The HandoffNote if it exists, otherwise None.
        """
        result = await self.db.execute(
            select(HandoffNote).where(HandoffNote.job_post_id == job_post_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, job_post_id: UUID) -> bool:
        """Delete the handoff note for a given job post.

        Args:
            job_post_id: The job post ID whose note should be deleted.

        Returns:
            True if a note was deleted, False if none existed.
        """
        note = await self.get_by_job_post(job_post_id)
        if not note:
            return False
        await self.db.delete(note)
        await self.db.commit()
        logger.info("handoff_note_deleted job_post_id=%s", job_post_id)
        return True
