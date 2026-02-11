from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import StudioProfile, User
from app.schemas.studio import StudioProfileUpdate


class StudioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[StudioProfile]:
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, profile_id: UUID) -> Optional[StudioProfile]:
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self, user_id: UUID, update_data: StudioProfileUpdate
    ) -> Optional[StudioProfile]:
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
