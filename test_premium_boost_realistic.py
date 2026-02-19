#!/usr/bin/env python3
"""
Realistic test for Premium Boost feature with various score ranges.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_realistic_matching():
    """Test premium boost with realistic matching scenarios."""
    from app.services.matching import calculate_matching_score, get_match_label

    print("🚀 Testing Premium Boost with Realistic Scenarios")
    print("=" * 60)

    # Test Case 1: Partial Match (70% base score)
    print("\n📊 Test Case 1: Partial Match Instructor")
    print("-" * 40)

    class InstructorPartial:
        available_regions = ["서울시 강남구"]
        experience_years = 2  # Less than required
        certifications = [{"name": "Yoga Alliance RYT-200"}]  # Different cert
        hourly_rate_min = Decimal("60000")
        hourly_rate_max = Decimal("90000")

    class JobRequiring:
        region = "서울시 강남구"
        required_experience_years = 5
        required_certifications = ["PMA-CPT"]
        hourly_rate = Decimal("70000")

    instructor = InstructorPartial()
    job = JobRequiring()

    # Regular score
    regular = calculate_matching_score(instructor, job, is_premium=False)
    print(f"  Regular Score: {regular['total']}")
    print(f"  Label: {get_match_label(regular['total'])}")

    # Premium boosted score
    premium = calculate_matching_score(instructor, job, is_premium=True)
    print(f"\n  Premium Score: {premium['total']} (was {premium.get('original_score', 'N/A')})")
    print(f"  Label: {get_match_label(premium['total'])}")
    print(f"  Boost: +{premium['total'] - premium.get('original_score', premium['total'])} points ({premium.get('boost_factor', 1.0)}x)")

    # Test Case 2: Good Match (80% base score)
    print("\n📊 Test Case 2: Good Match Instructor")
    print("-" * 40)

    class InstructorGood:
        available_regions = ["서울시 강남구", "서울시 서초구"]
        experience_years = 4  # Close to requirement
        certifications = [{"name": "PMA-CPT"}, {"name": "STOTT PILATES"}]
        hourly_rate_min = Decimal("50000")
        hourly_rate_max = Decimal("100000")

    instructor2 = InstructorGood()

    regular2 = calculate_matching_score(instructor2, job, is_premium=False)
    premium2 = calculate_matching_score(instructor2, job, is_premium=True)

    print(f"  Regular Score: {regular2['total']}")
    print(f"  Premium Score: {premium2['total']} (was {premium2.get('original_score', 'N/A')})")
    print(f"  Boost Effect: {get_match_label(regular2['total'])} → {get_match_label(premium2['total'])}")

    # Test Case 3: Low Match (40% base score)
    print("\n📊 Test Case 3: Low Match Instructor")
    print("-" * 40)

    class InstructorLow:
        available_regions = ["경기도 성남시"]  # Different region
        experience_years = 1  # Much less experience
        certifications = []  # No certifications
        hourly_rate_min = Decimal("100000")  # Too expensive
        hourly_rate_max = Decimal("150000")

    instructor3 = InstructorLow()

    regular3 = calculate_matching_score(instructor3, job, is_premium=False)
    premium3 = calculate_matching_score(instructor3, job, is_premium=True)

    print(f"  Regular Score: {regular3['total']}")
    print(f"  Premium Score: {premium3['total']} (was {premium3.get('original_score', 'N/A')})")
    print(f"  Even with boost: {get_match_label(premium3['total'])}")

    # Summary of Boost Effects
    print("\n📈 Premium Boost Impact Summary")
    print("=" * 60)

    test_cases = [
        ("Partial Match", regular['total'], premium['total']),
        ("Good Match", regular2['total'], premium2['total']),
        ("Low Match", regular3['total'], premium3['total'])
    ]

    for name, reg_score, prem_score in test_cases:
        boost_pct = ((prem_score - reg_score) / reg_score * 100) if reg_score > 0 else 0
        print(f"  {name:15} | Regular: {reg_score:3} | Premium: {prem_score:3} | Boost: +{boost_pct:.0f}%")

    # Demonstrate Sorting with Mixed Premium/Regular
    print("\n🔄 Mixed Listing Sort Example")
    print("-" * 40)

    listings = [
        {"name": "Regular High Score", "score": 85, "is_premium": False},
        {"name": "Premium Med Score", "score": 65, "is_premium": True},
        {"name": "Regular Med Score", "score": 70, "is_premium": False},
        {"name": "Premium Low Score", "score": 45, "is_premium": True},
        {"name": "Regular Low Score", "score": 50, "is_premium": False},
        {"name": "Premium High Score", "score": 80, "is_premium": True},
    ]

    # Apply boost to premium listings
    for listing in listings:
        if listing["is_premium"]:
            listing["boosted_score"] = min(100, round(listing["score"] * 1.3))
        else:
            listing["boosted_score"] = listing["score"]

    # Sort by premium first, then by boosted score
    sorted_listings = sorted(
        listings,
        key=lambda x: (x["is_premium"], x["boosted_score"]),
        reverse=True
    )

    print("  Original → After Premium Boost & Sort:")
    print("  " + "-" * 35)
    for i, item in enumerate(sorted_listings, 1):
        badge = "⭐" if item["is_premium"] else "  "
        boost_info = f"({item['score']}→{item['boosted_score']})" if item["is_premium"] else f"({item['score']})"
        print(f"  {i}. {badge} {item['name']:20} Score: {item['boosted_score']:3} {boost_info}")

    print("\n✅ Realistic Testing Complete!")
    print("=" * 60)
    print("Key Insights:")
    print("  • Premium boost helps moderate matches become strong matches")
    print("  • Low scores still remain low (but get priority placement)")
    print("  • Premium users always appear first in listings")
    print("  • 30% boost can change match labels (Fair→Good, Good→Great)")


if __name__ == "__main__":
    test_realistic_matching()