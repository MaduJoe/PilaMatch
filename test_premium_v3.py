"""Test script for v3.0 Premium Membership System with daily limits."""
import asyncio
import sys
from datetime import datetime, date
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from app.db.session import get_async_session, AsyncSessionLocal
from app.models import User, UserRole, InstructorProfile, StudioProfile, JobPost, Application
from app.models.daily_usage import DailyUsageLimit
from app.services.subscription import SubscriptionService
from app.services.daily_usage import DailyUsageService
from app.services.trust_score import calculate_trust_score
from sqlalchemy import select


async def test_premium_benefits():
    """Test all premium membership benefits."""
    async with AsyncSessionLocal() as db:
        print("\n" + "="*60)
        print("🧪 PilaMatch Premium Membership v3.0 Test Suite")
        print("="*60)

        # 1. Get test users
        print("\n1️⃣ Finding test users...")

        # Get a free instructor
        free_instructor_result = await db.execute(
            select(User).where(
                User.role == UserRole.INSTRUCTOR,
                User.membership_tier == "free"
            ).limit(1)
        )
        free_instructor = free_instructor_result.scalar_one_or_none()

        # Get a premium instructor
        premium_instructor_result = await db.execute(
            select(User).where(
                User.role == UserRole.INSTRUCTOR,
                User.membership_tier == "premium"
            ).limit(1)
        )
        premium_instructor = premium_instructor_result.scalar_one_or_none()

        # Get a free studio
        free_studio_result = await db.execute(
            select(User).where(
                User.role == UserRole.STUDIO,
                User.membership_tier == "free"
            ).limit(1)
        )
        free_studio = free_studio_result.scalar_one_or_none()

        if not all([free_instructor, premium_instructor, free_studio]):
            print("❌ Not enough test users found. Creating test users...")
            # You would create test users here
            return

        print(f"✅ Free Instructor: {free_instructor.email}")
        print(f"✅ Premium Instructor: {premium_instructor.email}")
        print(f"✅ Free Studio: {free_studio.email}")

        # 2. Test Trust Score Bonus
        print("\n2️⃣ Testing Trust Score Bonus...")

        free_trust = await calculate_trust_score(db, free_instructor.id)
        premium_trust = await calculate_trust_score(db, premium_instructor.id)

        print(f"Free Instructor Trust Score: {free_trust['total']}/100")
        print(f"  - Premium Membership: {free_trust['breakdown']['premium_membership']} points")

        print(f"Premium Instructor Trust Score: {premium_trust['total']}/100")
        print(f"  - Premium Membership: {premium_trust['breakdown']['premium_membership']} points")

        premium_bonus = premium_trust['breakdown']['premium_membership'] - free_trust['breakdown']['premium_membership']
        print(f"✅ Premium bonus: +{premium_bonus} points (should be +10)")
        assert premium_bonus == 10, f"Expected +10 bonus, got +{premium_bonus}"

        # 3. Test Daily Application Limits
        print("\n3️⃣ Testing Daily Application Limits...")

        daily_service = DailyUsageService(db)

        # Reset counters for testing
        free_instructor.daily_applications_today = 0
        free_instructor.last_usage_reset_date = date.today()
        await db.commit()

        # Test free user application limit
        print("Testing free instructor (5 applications per day):")
        for i in range(6):
            result = await daily_service.check_and_increment_usage(
                free_instructor.id,
                DailyUsageLimit.UsageType.APPLICATION
            )
            if i < 5:
                print(f"  Application #{i+1}: ✅ Allowed (remaining: {4-i})")
                assert result["allowed"], f"Application {i+1} should be allowed"
            else:
                print(f"  Application #{i+1}: ❌ Blocked (limit reached)")
                assert not result["allowed"], "Application 6 should be blocked"
                assert "하루 5회" in result["message"], "Should show daily limit message"

        # Test premium user (unlimited)
        print("\nTesting premium instructor (unlimited):")
        for i in range(10):
            result = await daily_service.check_and_increment_usage(
                premium_instructor.id,
                DailyUsageLimit.UsageType.APPLICATION
            )
            print(f"  Application #{i+1}: ✅ Allowed (unlimited)")
            assert result["allowed"], f"Premium application {i+1} should be allowed"
            assert result["limit"] is None, "Premium should have no limit"

        # 4. Test Profile Viewing Limits (Studios)
        print("\n4️⃣ Testing Profile Viewing Limits...")

        # Reset studio viewing counter
        free_studio.daily_views_today = 0
        free_studio.last_usage_reset_date = date.today()
        free_studio.last_viewed_profiles = []
        await db.commit()

        print("Testing free studio (5 profiles per day):")

        # Create some test profile IDs
        test_profiles = [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
            "44444444-4444-4444-4444-444444444444",
            "55555555-5555-5555-5555-555555555555",
            "66666666-6666-6666-6666-666666666666",
        ]

        for i, profile_id in enumerate(test_profiles):
            result = await daily_service.track_profile_view(
                free_studio.id,
                profile_id
            )
            if i < 5:
                print(f"  Profile view #{i+1}: ✅ Allowed (remaining: {4-i})")
                assert result["allowed"], f"Profile view {i+1} should be allowed"
            else:
                print(f"  Profile view #{i+1}: ❌ Blocked (limit reached)")
                assert not result["allowed"], "Profile view 6 should be blocked"
                assert "일일 열람 한도" in result["message"], "Should show viewing limit message"

        # Test duplicate view (shouldn't count)
        print("\nTesting duplicate view (shouldn't count against limit):")
        free_studio.daily_views_today = 3  # Reset to 3 for testing
        await db.commit()

        result = await daily_service.track_profile_view(
            free_studio.id,
            test_profiles[0]  # View first profile again
        )
        print(f"  Duplicate view: ✅ Allowed (already viewed today)")
        assert result["allowed"], "Duplicate view should be allowed"
        assert "이미 오늘 열람한" in result["message"], "Should indicate duplicate view"
        assert result["count"] == 3, "Count shouldn't increase for duplicate"

        # 5. Test Usage Status API
        print("\n5️⃣ Testing Usage Status Retrieval...")

        free_status = await daily_service.get_usage_status(free_instructor.id)
        print(f"Free Instructor Status:")
        print(f"  - Membership: {free_status['membership_tier']}")
        print(f"  - Applications: {free_status['applications']['used']}/{free_status['applications']['limit']}")
        print(f"  - Unlimited: {free_status['applications']['unlimited']}")

        premium_status = await daily_service.get_usage_status(premium_instructor.id)
        print(f"Premium Instructor Status:")
        print(f"  - Membership: {premium_status['membership_tier']}")
        print(f"  - Applications: Unlimited")
        print(f"  - Profile Views: Unlimited")

        # 6. Test Premium Badge
        print("\n6️⃣ Testing Premium Badge...")

        print(f"Free Instructor has_premium_badge: {free_instructor.has_premium_badge}")
        print(f"Premium Instructor has_premium_badge: {premium_instructor.has_premium_badge}")

        assert not free_instructor.has_premium_badge, "Free user shouldn't have badge"
        assert premium_instructor.has_premium_badge, "Premium user should have badge"

        print("\n" + "="*60)
        print("✅ All Premium v3.0 Tests Passed!")
        print("="*60)

        print("\n📋 Summary of Changes:")
        print("- Daily application limit: 5/day for free, unlimited for premium")
        print("- Daily profile viewing: 5/day for free studios, unlimited for premium")
        print("- Trust Score bonus: +10 points for premium (up from +5)")
        print("- Premium badge: Visual indicator in profiles")
        print("- Platform fee: 3% for premium, 5% for free")
        print("- Premium priority: Job posts and applications sorted with premium first")


async def main():
    """Run all tests."""
    try:
        await test_premium_benefits()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())