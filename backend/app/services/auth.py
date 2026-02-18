from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, InstructorProfile, StudioProfile, UserRole
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth import SignupRequest


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, request: SignupRequest) -> Tuple[User, str]:
        # Check if email exists
        existing_user = await self.get_user_by_email(request.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Validate role-specific fields
        if request.role == UserRole.INSTRUCTOR and not request.display_name:
            raise ValueError("Display name is required for instructors")
        if request.role == UserRole.STUDIO and not request.business_name:
            raise ValueError("Business name is required for studios")

        # Create user
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            role=request.role,
        )
        self.db.add(user)
        await self.db.flush()

        # Create profile based on role
        if request.role == UserRole.INSTRUCTOR:
            profile = InstructorProfile(
                user_id=user.id,
                display_name=request.display_name,
            )
            self.db.add(profile)
        elif request.role == UserRole.STUDIO:
            profile = StudioProfile(
                user_id=user.id,
                business_name=request.business_name,
            )
            self.db.add(profile)

        await self.db.commit()
        await self.db.refresh(user)

        # Generate token
        token = create_access_token(str(user.id))

        return user, token

    async def authenticate(self, email: str, password: str) -> Optional[Tuple[User, str]]:
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        if user.is_suspended:
            raise ValueError("ACCOUNT_SUSPENDED")

        token = create_access_token(str(user.id))
        return user, token

    async def get_user_profile_id(self, user: User) -> Optional[UUID]:
        if user.role == UserRole.INSTRUCTOR.value:
            result = await self.db.execute(
                select(InstructorProfile.id).where(InstructorProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()
            return profile
        elif user.role == UserRole.STUDIO.value:
            result = await self.db.execute(
                select(StudioProfile.id).where(StudioProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()
            return profile
        return None

    async def get_instructor_profile(self, user_id: UUID) -> Optional[InstructorProfile]:
        """Get instructor profile by user ID."""
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_studio_profile(self, user_id: UUID) -> Optional[StudioProfile]:
        """Get studio profile by user ID."""
        result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
