import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import InstructorProfile, User
from app.models.contract import Contract
from app.models.enums import ContractStatus
from app.schemas.instructor import InstructorProfileUpdate

logger = logging.getLogger(__name__)


class InstructorService:
    """Service for instructor profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[InstructorProfile]:
        """Get instructor profile by user ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            InstructorProfile if found, None otherwise.
        """
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, profile_id: UUID) -> Optional[InstructorProfile]:
        """Get instructor profile by profile ID.

        Args:
            profile_id: The profile's unique identifier.

        Returns:
            InstructorProfile if found, None otherwise.
        """
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_completed_contracts_count(self, profile_id: UUID) -> int:
        """Count the number of completed contracts for an instructor.

        Args:
            profile_id: The instructor profile's unique identifier.

        Returns:
            Number of completed contracts.
        """
        result = await self.db.execute(
            select(func.count(Contract.id)).where(
                and_(
                    Contract.instructor_id == str(profile_id),
                    Contract.status == ContractStatus.COMPLETED.value,
                )
            )
        )
        count = result.scalar() or 0
        logger.debug(
            "Instructor %s has %d completed contracts", profile_id, count
        )
        return count

    async def update_profile(
        self, user_id: UUID, update_data: InstructorProfileUpdate
    ) -> Optional[InstructorProfile]:
        """Update instructor profile fields.

        Args:
            user_id: The user's unique identifier.
            update_data: Fields to update.

        Returns:
            Updated InstructorProfile if found, None otherwise.
        """
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
