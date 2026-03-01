"""Backup Instructor service -- manage studio's trusted substitute pool."""
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backup_instructor import BackupInstructor
from app.models.instructor import InstructorProfile
from app.schemas.backup_instructor import BackupInstructorCreate, BackupInstructorUpdate

logger = logging.getLogger(__name__)


class BackupInstructorService:
    """Service layer for backup instructor CRUD operations.

    Args:
        db: Async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add(self, studio_id: UUID, data: BackupInstructorCreate) -> BackupInstructor:
        """Add an instructor to the studio's backup network.

        Args:
            studio_id: The studio's profile ID.
            data: Creation payload with instructor_id and optional metadata.

        Returns:
            The newly created BackupInstructor record.

        Raises:
            ValueError: If instructor does not exist or is already in the network.
        """
        # Check if instructor exists
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == data.instructor_id)
        )
        if not result.scalar_one_or_none():
            raise ValueError("INSTRUCTOR_NOT_FOUND")

        # Check duplicate
        existing = await self.db.execute(
            select(BackupInstructor).where(
                BackupInstructor.studio_id == studio_id,
                BackupInstructor.instructor_id == data.instructor_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("ALREADY_IN_BACKUP")

        backup = BackupInstructor(
            studio_id=studio_id,
            instructor_id=data.instructor_id,
            nickname=data.nickname,
            note=data.note,
            priority=data.priority,
        )
        self.db.add(backup)
        await self.db.commit()
        await self.db.refresh(backup)

        logger.info(
            "Backup instructor added: studio=%s instructor=%s priority=%d",
            studio_id, data.instructor_id, data.priority,
        )
        return backup

    async def list_by_studio(self, studio_id: UUID) -> list[tuple]:
        """List all backup instructors for a studio with instructor details.

        Args:
            studio_id: The studio's profile ID.

        Returns:
            List of (BackupInstructor, InstructorProfile) tuples ordered by
            priority ascending, then created_at descending.
        """
        result = await self.db.execute(
            select(BackupInstructor, InstructorProfile)
            .join(InstructorProfile, InstructorProfile.id == BackupInstructor.instructor_id)
            .where(BackupInstructor.studio_id == studio_id)
            .order_by(BackupInstructor.priority.asc(), BackupInstructor.created_at.desc())
        )
        return result.all()

    async def update(
        self, studio_id: UUID, instructor_id: UUID, data: BackupInstructorUpdate
    ) -> Optional[BackupInstructor]:
        """Update a backup instructor entry.

        Args:
            studio_id: The studio's profile ID.
            instructor_id: The instructor's profile ID.
            data: Update payload with optional fields.

        Returns:
            Updated BackupInstructor or None if not found.
        """
        result = await self.db.execute(
            select(BackupInstructor).where(
                BackupInstructor.studio_id == studio_id,
                BackupInstructor.instructor_id == instructor_id,
            )
        )
        backup = result.scalar_one_or_none()
        if not backup:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(backup, field, value)

        await self.db.commit()
        await self.db.refresh(backup)

        logger.info(
            "Backup instructor updated: studio=%s instructor=%s",
            studio_id, instructor_id,
        )
        return backup

    async def delete(self, studio_id: UUID, instructor_id: UUID) -> bool:
        """Remove an instructor from the studio's backup network.

        Args:
            studio_id: The studio's profile ID.
            instructor_id: The instructor's profile ID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self.db.execute(
            select(BackupInstructor).where(
                BackupInstructor.studio_id == studio_id,
                BackupInstructor.instructor_id == instructor_id,
            )
        )
        backup = result.scalar_one_or_none()
        if not backup:
            return False
        await self.db.delete(backup)
        await self.db.commit()

        logger.info(
            "Backup instructor removed: studio=%s instructor=%s",
            studio_id, instructor_id,
        )
        return True

    async def get_backup_instructor_ids(self, studio_id: UUID) -> list[UUID]:
        """Get instructor IDs in the studio's backup network, ordered by priority.

        Args:
            studio_id: The studio's profile ID.

        Returns:
            List of instructor profile IDs sorted by priority ascending.
        """
        result = await self.db.execute(
            select(BackupInstructor.instructor_id)
            .where(BackupInstructor.studio_id == studio_id)
            .order_by(BackupInstructor.priority.asc())
        )
        return [row[0] for row in result.all()]
