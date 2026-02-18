#!/usr/bin/env python3
"""
Create a new studio account and check its status
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def create_and_check():
    """Create a new studio and check its status"""

    # Create unique email
    timestamp = int(time.time())
    email = f"studio_test_{timestamp}@test.com"
    password = "Test1234!"

    print(f"Creating studio account: {email}")

    # Create studio account
    signup_response = requests.post(
        f"{API_BASE_URL}/auth/signup",
        json={
            "email": email,
            "password": password,
            "role": "studio",
            "business_name": f"Test Studio {timestamp}"
        }
    )

    if signup_response.status_code not in [200, 201]:
        print(f"❌ Signup failed: {signup_response.text}")
        return

    token = signup_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Created studio account: {email}")

    # Get contracts
    contracts_response = requests.get(
        f"{API_BASE_URL}/contracts/me",
        headers=headers
    )

    if contracts_response.status_code == 200:
        contracts_data = contracts_response.json()
        all_contracts = contracts_data.get("items", [])

        print(f"\n📋 CONTRACTS: {len(all_contracts)} total")

        if len(all_contracts) == 0:
            print("   No contracts yet (expected for new account)")

    # Get written reviews
    reviews_response = requests.get(
        f"{API_BASE_URL}/reviews/written",
        headers=headers
    )

    if reviews_response.status_code == 200:
        reviews_data = reviews_response.json()
        written_reviews = reviews_data.get("reviews", [])

        print(f"\n⭐ WRITTEN REVIEWS: {len(written_reviews)}")

        if len(written_reviews) == 0:
            print("   No reviews yet (expected for new account)")

    print("\n✅ New studio account is working correctly!")
    print(f"   Email: {email}")
    print(f"   Password: {password}")

# Now let's find existing studio accounts in the database
def check_existing_studios():
    """Try to find existing studio accounts"""

    # Try common test patterns
    test_emails = [
        "studio1@test.com",
        "studio@test.com",
        "test_studio@example.com"
    ]

    test_passwords = [
        "Test1234!",
        "password123",
        "test123",
        "password"
    ]

    print("\n" + "=" * 60)
    print("Searching for existing studio accounts...")
    print("=" * 60)

    for email in test_emails:
        for password in test_passwords:
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )

            if login_response.status_code == 200:
                print(f"\n✅ FOUND WORKING ACCOUNT!")
                print(f"   Email: {email}")
                print(f"   Password: {password}")

                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Get contracts
                contracts_response = requests.get(
                    f"{API_BASE_URL}/contracts/me",
                    headers=headers
                )

                if contracts_response.status_code == 200:
                    contracts_data = contracts_response.json()
                    all_contracts = contracts_data.get("items", [])
                    completed = [c for c in all_contracts if c["status"] == "completed"]

                    print(f"   Total contracts: {len(all_contracts)}")
                    print(f"   Completed contracts: {len(completed)}")

                    # Get reviews
                    reviews_response = requests.get(
                        f"{API_BASE_URL}/reviews/written",
                        headers=headers
                    )

                    if reviews_response.status_code == 200:
                        reviews_data = reviews_response.json()
                        written_reviews = reviews_data.get("reviews", [])
                        print(f"   Written reviews: {len(written_reviews)}")

                return  # Found one, exit

if __name__ == "__main__":
    print("=" * 60)
    print("Studio Account Testing")
    print("=" * 60)

    # First check for existing accounts
    check_existing_studios()

    # Then create a new one for testing
    print("\n" + "=" * 60)
    print("Creating new test studio...")
    print("=" * 60)
    create_and_check()