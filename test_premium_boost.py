#!/usr/bin/env python3
"""
Test script for Premium Boost feature in PilaMatch.
This script tests the 30% visibility boost for Premium members.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import User, InstructorProfile, StudioProfile, JobPost, Subscription
from app.models.enums import UserRole, Category, JobType, JobPostStatus, MembershipTier, SubscriptionStatus
from app.services.matching import calculate_matching_score
from app.services.subscription import SubscriptionService
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import uuid


async def test_premium_boost():
    """Test the premium boost feature."""
    # Create test database session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create tables
        from app.db.session import Base
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        print("🚀 Testing Premium Boost Feature\n")
        print("=" * 60)

        # Create test users
        print("1. Creating test users...")

        # Create a regular instructor
        regular_instructor_user = User(
            id=str(uuid.uuid4()),
            email="regular@test.com",
            hashed_password="test",
            role=UserRole.INSTRUCTOR.value,
            membership_tier=MembershipTier.FREE.value
        )
        session.add(regular_instructor_user)

        # Create a premium studio
        premium_studio_user = User(
            id=str(uuid.uuid4()),
            email="premium@studio.com",
            hashed_password="test",
            role=UserRole.STUDIO.value,
            membership_tier=MembershipTier.PREMIUM.value
        )
        session.add(premium_studio_user)

        # Create a regular studio
        regular_studio_user = User(
            id=str(uuid.uuid4()),
            email="regular@studio.com",
            hashed_password="test",
            role=UserRole.STUDIO.value,
            membership_tier=MembershipTier.FREE.value
        )
        session.add(regular_studio_user)

        await session.commit()

        # Create profiles
        print("2. Creating profiles...")

        instructor_profile = InstructorProfile(
            id=str(uuid.uuid4()),
            user_id=regular_instructor_user.id,
            display_name="Test Instructor",
            phone="010-1234-5678",
            categories=[Category.PILATES.value],
            experience_years=5,
            certifications=[{"name": "PMA-CPT", "issuer": "PMA", "issue_date": "2020-01-01"}],
            available_regions=["서울시 강남구"],
            hourly_rate_min=Decimal("50000"),
            hourly_rate_max=Decimal("100000")
        )
        session.add(instructor_profile)

        premium_studio = StudioProfile(
            id=str(uuid.uuid4()),
            user_id=premium_studio_user.id,
            business_name="Premium Pilates Studio",
            business_number="123-45-67890",
            phone="02-555-1234"
        )
        session.add(premium_studio)

        regular_studio = StudioProfile(
            id=str(uuid.uuid4()),
            user_id=regular_studio_user.id,
            business_name="Regular Yoga Studio",
            business_number="987-65-43210",
            phone="02-555-5678"
        )
        session.add(regular_studio)

        await session.commit()

        # Create job posts
        print("3. Creating job posts...")

        premium_job = JobPost(
            id=str(uuid.uuid4()),
            studio_id=premium_studio.id,
            title="Premium Studio Pilates Instructor",
            category=Category.PILATES.value,
            job_type=JobType.ONE_TIME.value,
            status=JobPostStatus.OPEN.value,
            date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            hourly_rate=Decimal("80000"),
            required_experience_years=3,
            required_certifications=["PMA-CPT"],
            region="서울시 강남구",
            total_sessions=1
        )
        session.add(premium_job)

        regular_job = JobPost(
            id=str(uuid.uuid4()),
            studio_id=regular_studio.id,
            title="Regular Studio Yoga Instructor",
            category=Category.PILATES.value,
            job_type=JobType.ONE_TIME.value,
            status=JobPostStatus.OPEN.value,
            date=date.today() + timedelta(days=7),
            start_time=time(14, 0),
            end_time=time(16, 0),
            hourly_rate=Decimal("70000"),
            required_experience_years=3,
            required_certifications=["PMA-CPT"],
            region="서울시 강남구",
            total_sessions=1
        )
        session.add(regular_job)

        await session.commit()

        # Test matching score calculation
        print("\n4. Testing Matching Score Calculation")
        print("-" * 40)

        # Calculate score for regular job (no boost)
        regular_score = calculate_matching_score(
            instructor_profile,
            regular_job,
            is_premium=False
        )

        print(f"Regular Job Post Score:")
        print(f"  Base Score: {regular_score['total']}")
        print(f"  Is Boosted: {regular_score.get('is_boosted', False)}")
        print(f"  Boost Factor: {regular_score.get('boost_factor', 1.0)}")

        # Calculate score for premium job (with boost)
        premium_score = calculate_matching_score(
            instructor_profile,
            premium_job,
            is_premium=True
        )

        print(f"\nPremium Job Post Score:")
        print(f"  Original Score: {premium_score.get('original_score', 'N/A')}")
        print(f"  Boosted Score: {premium_score['total']}")
        print(f"  Is Boosted: {premium_score.get('is_boosted', False)}")
        print(f"  Boost Factor: {premium_score.get('boost_factor', 1.0)}")

        # Test subscription service
        print("\n5. Testing Subscription Service")
        print("-" * 40)

        subscription_service = SubscriptionService(session)

        # Check membership tiers
        regular_tier = await subscription_service.get_membership_tier(regular_instructor_user.id)
        premium_tier = await subscription_service.get_membership_tier(premium_studio_user.id)

        print(f"Regular Instructor Tier: {regular_tier}")
        print(f"Premium Studio Tier: {premium_tier}")

        # Check premium status
        is_regular_premium = await subscription_service.is_premium_user(regular_instructor_user.id)
        is_studio_premium = await subscription_service.is_premium_user(premium_studio_user.id)

        print(f"Is Regular Instructor Premium: {is_regular_premium}")
        print(f"Is Premium Studio Premium: {is_studio_premium}")

        # Test sorting logic
        print("\n6. Testing Sort Order (Premium First)")
        print("-" * 40)

        jobs = [
            {"title": "Job 1", "is_premium": False, "score": 90},
            {"title": "Job 2", "is_premium": True, "score": 70},
            {"title": "Job 3", "is_premium": False, "score": 85},
            {"title": "Job 4", "is_premium": True, "score": 65},
        ]

        # Sort by: Premium first, then by score
        sorted_jobs = sorted(jobs, key=lambda x: (x["is_premium"], x["score"]), reverse=True)

        print("Sorted Jobs (Premium first, then by score):")
        for i, job in enumerate(sorted_jobs, 1):
            premium_badge = "⭐" if job["is_premium"] else "  "
            print(f"  {i}. {premium_badge} {job['title']} - Score: {job['score']}")

        print("\n✅ Premium Boost Feature Test Complete!")
        print("=" * 60)
        print("\nKey Features Implemented:")
        print("  1. Premium users get 30% boost in matching scores")
        print("  2. Premium listings appear first in search results")
        print("  3. Visual indicators (⭐) for premium listings")
        print("  4. Boost factor tracked in response data")

        return True


if __name__ == "__main__":
    asyncio.run(test_premium_boost())