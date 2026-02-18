#!/usr/bin/env python3
"""
Check studio1's contracts and reviews status
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def check_studio_reviews():
    """Check contracts and reviews for studio1@test.com"""

    # Login as studio1
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": "studio1@test.com",
            "password": "Test1234!"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in as studio1@test.com")

    # Get contracts
    contracts_response = requests.get(
        f"{API_BASE_URL}/contracts/me",
        headers=headers
    )

    if contracts_response.status_code == 200:
        contracts_data = contracts_response.json()
        all_contracts = contracts_data.get("items", [])

        # Count by status
        completed = [c for c in all_contracts if c["status"] == "completed"]
        cancelled = [c for c in all_contracts if c["status"] == "cancelled"]
        in_progress = [c for c in all_contracts if c["status"] == "in_progress"]

        print("\n📋 CONTRACT STATUS:")
        print(f"  Total contracts: {len(all_contracts)}")
        print(f"  Completed: {len(completed)}")
        print(f"  Cancelled: {len(cancelled)}")
        print(f"  In Progress: {len(in_progress)}")

        print("\n📝 COMPLETED CONTRACTS:")
        for i, contract in enumerate(completed, 1):
            print(f"  {i}. Contract ID: {contract['id']}")
            print(f"     Date: {contract.get('date', 'N/A')}")
            print(f"     Instructor: {contract.get('instructor_name', 'N/A')}")
            print(f"     Amount: ₩{int(contract.get('total_amount', 0)):,}")

    # Get written reviews
    reviews_response = requests.get(
        f"{API_BASE_URL}/reviews/written",
        headers=headers
    )

    if reviews_response.status_code == 200:
        reviews_data = reviews_response.json()
        written_reviews = reviews_data.get("reviews", [])

        print(f"\n⭐ WRITTEN REVIEWS: {len(written_reviews)}")

        # Map reviews by contract ID
        review_map = {r["contract_id"]: r for r in written_reviews}

        # Check which completed contracts have reviews
        reviewed_contracts = []
        unreviewed_contracts = []

        for contract in completed:
            if contract["id"] in review_map:
                reviewed_contracts.append(contract)
            else:
                unreviewed_contracts.append(contract)

        print(f"\n✅ Reviewed contracts: {len(reviewed_contracts)}")
        for contract in reviewed_contracts:
            review = review_map[contract["id"]]
            print(f"  - Contract {contract['id'][:8]}...")
            print(f"    Rating: {'⭐' * review['rating']}")
            if review.get('comment'):
                print(f"    Comment: {review['comment'][:50]}...")

        print(f"\n⏳ Unreviewed contracts: {len(unreviewed_contracts)}")
        for contract in unreviewed_contracts:
            print(f"  - Contract {contract['id'][:8]}... (Date: {contract.get('date', 'N/A')})")

        print("\n📊 SUMMARY:")
        print(f"  Total completed contracts: {len(completed)}")
        print(f"  Reviews written: {len(reviewed_contracts)}")
        print(f"  Reviews pending: {len(unreviewed_contracts)}")
        print(f"  Review completion rate: {len(reviewed_contracts)/len(completed)*100:.1f}%" if completed else "N/A")

    else:
        print(f"❌ Failed to get reviews: {reviews_response.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("Checking studio1@test.com contracts and reviews...")
    print("=" * 60)

    check_studio_reviews()

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)