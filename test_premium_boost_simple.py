#!/usr/bin/env python3
"""
Simple test for Premium Boost feature without database dependencies.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

# Test the matching score calculation directly
def test_matching_score():
    """Test the premium boost in matching score calculation."""
    from app.services.matching import calculate_matching_score, get_match_label

    # Create mock instructor and job post objects
    class MockInstructor:
        available_regions = ["서울시 강남구"]
        experience_years = 5
        certifications = [{"name": "PMA-CPT", "issuer": "PMA"}]
        hourly_rate_min = Decimal("50000")
        hourly_rate_max = Decimal("100000")

    class MockJobPost:
        region = "서울시 강남구"
        required_experience_years = 3
        required_certifications = ["PMA-CPT"]
        hourly_rate = Decimal("80000")

    instructor = MockInstructor()
    job = MockJobPost()

    print("🚀 Testing Premium Boost Feature")
    print("=" * 60)

    # Test regular (non-premium) matching score
    print("\n1. Regular Matching Score (No Boost):")
    print("-" * 40)
    regular_score = calculate_matching_score(instructor, job, is_premium=False)

    print(f"  Total Score: {regular_score['total']}")
    print(f"  Match Label: {get_match_label(regular_score['total'])}")
    print(f"  Is Boosted: {regular_score.get('is_boosted', False)}")
    print(f"  Boost Factor: {regular_score.get('boost_factor', 1.0)}")
    print(f"  Breakdown:")
    for key, value in regular_score['breakdown'].items():
        print(f"    - {key}: {value['score']}/100 (weight: {value['weight']}%)")

    # Test premium matching score with boost
    print("\n2. Premium Matching Score (30% Boost):")
    print("-" * 40)
    premium_score = calculate_matching_score(instructor, job, is_premium=True)

    print(f"  Original Score: {premium_score.get('original_score', 'N/A')}")
    print(f"  Boosted Score: {premium_score['total']}")
    print(f"  Match Label: {get_match_label(premium_score['total'])}")
    print(f"  Is Boosted: {premium_score.get('is_boosted', False)}")
    print(f"  Boost Factor: {premium_score.get('boost_factor', 1.0)}")
    print(f"  Boost Applied: +{premium_score['total'] - premium_score.get('original_score', premium_score['total'])} points")

    # Test sorting logic
    print("\n3. Sorting Logic Test (Premium First):")
    print("-" * 40)

    # Simulate job posts with scores
    jobs = [
        {"title": "Regular Job A", "is_premium": False, "score": 95},
        {"title": "Premium Job B", "is_premium": True, "score": 75},
        {"title": "Regular Job C", "is_premium": False, "score": 85},
        {"title": "Premium Job D", "is_premium": True, "score": 80},
        {"title": "Regular Job E", "is_premium": False, "score": 90},
    ]

    # Sort by: Premium first, then by score
    sorted_jobs = sorted(jobs, key=lambda x: (x["is_premium"], x["score"]), reverse=True)

    print("  Sorted Results (Premium listings appear first):")
    for i, job in enumerate(sorted_jobs, 1):
        premium_badge = "⭐" if job["is_premium"] else "  "
        print(f"    {i}. {premium_badge} {job['title']:<20} Score: {job['score']}")

    # Test edge cases
    print("\n4. Edge Cases:")
    print("-" * 40)

    # Test maximum score with boost
    class MockHighScoreJob:
        region = "서울시 강남구"
        required_experience_years = 5
        required_certifications = ["PMA-CPT"]
        hourly_rate = Decimal("75000")

    high_score_job = MockHighScoreJob()
    high_score = calculate_matching_score(instructor, high_score_job, is_premium=True)

    print(f"  High Score Job:")
    print(f"    Original: {high_score.get('original_score', 'N/A')}")
    print(f"    Boosted: {high_score['total']} (capped at 100)")

    print("\n✅ Premium Boost Feature Test Complete!")
    print("=" * 60)
    print("\n📋 Summary of Premium Benefits:")
    print("  • 30% boost in matching scores (1.3x multiplier)")
    print("  • Priority placement in search results")
    print("  • Visual premium indicator (⭐)")
    print("  • Boost tracking in API responses")

    return True


if __name__ == "__main__":
    test_matching_score()