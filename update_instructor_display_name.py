#!/usr/bin/env python3
"""
Update instructor display name in the database directly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.models import User, InstructorProfile

# Use the database URL from environment or default
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/pilamatch"

async def update_display_name():
    """Update display name for gangsa1@test.com"""

    # Create engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == "gangsa1@test.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ User gangsa1@test.com not found")
            return

        print(f"✅ Found user: {user.email}, role: {user.role}")

        # Find or create instructor profile
        profile_result = await db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()

        if profile:
            # Update existing profile
            profile.display_name = "강사1"
            print(f"✅ Updated display_name to '강사1'")
        else:
            # Create new profile
            profile = InstructorProfile(
                user_id=user.id,
                display_name="강사1"
            )
            db.add(profile)
            print(f"✅ Created profile with display_name='강사1'")

        await db.commit()
        print("✅ Changes committed to database")

    await engine.dispose()

if __name__ == "__main__":
    print("Updating display name for gangsa1@test.com...")
    print("=" * 50)
    asyncio.run(update_display_name())
    print("\nNow you can test login to verify display name is returned.")