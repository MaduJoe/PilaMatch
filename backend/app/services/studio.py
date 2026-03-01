import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import StudioProfile, User
from app.models.contract import Contract
from app.models.enums import ContractStatus
from app.schemas.studio import StudioProfileUpdate

logger = logging.getLogger(__name__)


class StudioService:
    """Service for studio profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[StudioProfile]:
        """Get studio profile by user ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            StudioProfile if found, None otherwise.
        """
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, profile_id: UUID) -> Optional[StudioProfile]:
        """Get studio profile by profile ID.

        Args:
            profile_id: The profile's unique identifier.

        Returns:
            StudioProfile if found, None otherwise.
        """
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_completed_contracts_count(self, profile_id: UUID) -> int:
        """Count the number of completed contracts for a studio.

        Args:
            profile_id: The studio profile's unique identifier.

        Returns:
            Number of completed contracts.
        """
        result = await self.db.execute(
            select(func.count(Contract.id)).where(
                and_(
                    Contract.studio_id == str(profile_id),
                    Contract.status == ContractStatus.COMPLETED.value,
                )
            )
        )
        count = result.scalar() or 0
        logger.debug(
            "Studio %s has %d completed contracts", profile_id, count
        )
        return count

    async def update_profile(
        self, user_id: UUID, update_data: StudioProfileUpdate
    ) -> Optional[StudioProfile]:
        """Update studio profile fields.

        Args:
            user_id: The user's unique identifier.
            update_data: Fields to update.

        Returns:
            Updated StudioProfile if found, None otherwise.
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
