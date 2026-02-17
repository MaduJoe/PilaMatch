#!/usr/bin/env python3
"""Test script to check review status after submission."""

import requests
import json
import time

# API configuration
BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials (instructor)
test_credentials = {
    "email": "premium_instructor@test.com",
    "password": "Test1234!"
}

def login():
    """Login and get token."""
    response = requests.post(f"{BASE_URL}/auth/login", json=test_credentials)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_contracts(token):
    """Get user's contracts."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/contracts/me", headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("items", [])
    else:
        print(f"Failed to get contracts: {response.status_code} - {response.text}")
        return []

def check_review_exists(token, contract_id):
    """Check if review exists for a contract."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/contracts/{contract_id}/reviews/my", headers=headers)

    if response.status_code == 200:
        print(f"✅ Review exists for contract {contract_id[:8]}...")
        return response.json()
    elif response.status_code == 404:
        print(f"❌ No review for contract {contract_id[:8]}...")
        return None
    else:
        print(f"⚠️ Unexpected response: {response.status_code} - {response.text}")
        return None

def create_review(token, contract_id, rating=4, comment="Test review"):
    """Create a review for a contract."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "rating": rating,
        "comment": comment
    }
    response = requests.post(f"{BASE_URL}/contracts/{contract_id}/reviews", headers=headers, json=data)

    if response.status_code == 201:
        print(f"✅ Review created successfully for contract {contract_id[:8]}...")
        return response.json()
    else:
        print(f"❌ Failed to create review: {response.status_code} - {response.text}")
        return None

def main():
    print("🔑 Logging in...")
    token = login()
    if not token:
        print("Failed to login")
        return

    print("\n📋 Getting contracts...")
    contracts = get_contracts(token)

    # Filter completed contracts
    completed_contracts = [c for c in contracts if c.get('status') == 'completed']

    if not completed_contracts:
        print("No completed contracts found")
        return

    print(f"Found {len(completed_contracts)} completed contracts")

    # Test the first completed contract
    test_contract = completed_contracts[0]
    contract_id = test_contract['id']

    print(f"\n🧪 Testing contract: {contract_id}")

    # Step 1: Check if review exists
    print("\n1️⃣ Checking initial review status...")
    initial_review = check_review_exists(token, contract_id)

    if initial_review:
        print(f"   Review already exists with rating: {'⭐' * initial_review.get('rating', 0)}")
        print(f"   Comment: {initial_review.get('comment', 'No comment')}")
    else:
        # Step 2: Create a review
        print("\n2️⃣ Creating a new review...")
        new_review = create_review(token, contract_id, 5, "Excellent service!")

        if new_review:
            # Step 3: Check if review exists after creation
            print("\n3️⃣ Checking review status after creation...")
            time.sleep(1)  # Small delay to ensure DB is updated

            post_review = check_review_exists(token, contract_id)
            if post_review:
                print(f"   ✅ Review now exists with rating: {'⭐' * post_review.get('rating', 0)}")
                print(f"   Comment: {post_review.get('comment', 'No comment')}")
            else:
                print("   ❌ Review still not found after creation!")

    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()