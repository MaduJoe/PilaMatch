from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import InstructorProfile, User
from app.schemas.instructor import InstructorProfileUpdate


class InstructorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[InstructorProfile]:
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_profile_by_id(self, profile_id: UUID) -> Optional[InstructorProfile]:
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self, user_id: UUID, update_data: InstructorProfileUpdate
    ) -> Optional[InstructorProfile]:
        profile = await self.get_profile_by_user_id(user_id)
        if not profile:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)

        await self.db.commit()
        await self.db.refresh(profile)
        return profile
