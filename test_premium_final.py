#!/usr/bin/env python3
"""Final test for Premium membership implementation."""

import time
import requests
import uuid
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Generate unique test accounts
test_id = uuid.uuid4().hex[:8]
PREMIUM_INSTRUCTOR = {
    "email": f"prem_{test_id}@test.com",
    "password": "Test123!@#",
    "display_name": f"Premium {test_id}",
}

FREE_INSTRUCTOR = {
    "email": f"free_{test_id}@test.com",
    "password": "Test123!@#",
    "display_name": f"Free {test_id}",
}


def signup_and_login(email, password, role, display_name=None):
    """Sign up and login user."""
    # Signup
    payload = {
        "email": email,
        "password": password,
        "role": role,
    }
    if display_name:
        payload["display_name"] = display_name

    response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    if response.status_code not in [200, 201]:
        print(f"❌ Signup failed: {response.status_code}")
        return None

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None


def check_deposit_status(token):
    """Check deposit status."""
    response = requests.get(
        f"{BASE_URL}/deposit/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 200:
        return response.json()
    return None


def upgrade_to_premium(token):
    """Upgrade user to premium."""
    headers = {"Authorization": f"Bearer {token}"}

    # Initialize upgrade
    response = requests.post(f"{BASE_URL}/subscriptions/upgrade", json={}, headers=headers)
    if response.status_code != 200:
        return False

    upgrade_data = response.json()
    order_id = upgrade_data["order_id"]

    # Confirm payment
    response = requests.post(
        f"{BASE_URL}/subscriptions/confirm",
        json={
            "payment_key": f"test_pk_{order_id}",
            "order_id": order_id
        },
        headers=headers
    )
    return response.status_code == 200


def main():
    print("\n" + "=" * 60)
    print("PREMIUM MEMBERSHIP FINAL TEST")
    print("=" * 60)

    # Setup Premium Instructor
    print("\n📦 Setting up Premium Instructor...")
    premium_token = signup_and_login(
        PREMIUM_INSTRUCTOR["email"],
        PREMIUM_INSTRUCTOR["password"],
        "instructor",
        PREMIUM_INSTRUCTOR["display_name"]
    )
    if not premium_token:
        print("Failed to setup premium instructor")
        return

    # Setup Free Instructor
    print("\n📦 Setting up Free Instructor...")
    free_token = signup_and_login(
        FREE_INSTRUCTOR["email"],
        FREE_INSTRUCTOR["password"],
        "instructor",
        FREE_INSTRUCTOR["display_name"]
    )
    if not free_token:
        print("Failed to setup free instructor")
        return

    # Check initial status
    print("\n📊 Initial Status Comparison:")
    print("\nFREE User:")
    free_status_before = check_deposit_status(free_token)
    if free_status_before:
        print(f"  Tier: {free_status_before.get('membership_tier', 'unknown')}")
        print(f"  Required deposit: ₩{free_status_before['required']:,.0f}")
        print(f"  Can apply to jobs: {free_status_before['is_sufficient']}")

    print("\nPREMIUM User (before upgrade):")
    premium_status_before = check_deposit_status(premium_token)
    if premium_status_before:
        print(f"  Tier: {premium_status_before.get('membership_tier', 'unknown')}")
        print(f"  Required deposit: ₩{premium_status_before['required']:,.0f}")
        print(f"  Can apply to jobs: {premium_status_before['is_sufficient']}")

    # Upgrade to Premium
    print("\n⬆️ Upgrading to Premium...")
    if upgrade_to_premium(premium_token):
        print("✅ Successfully upgraded to Premium!")
    else:
        print("❌ Failed to upgrade to Premium")
        return

    # Check status after upgrade
    print("\n📊 After Premium Upgrade:")
    print("\nFREE User (unchanged):")
    free_status_after = check_deposit_status(free_token)
    if free_status_after:
        print(f"  Tier: {free_status_after.get('membership_tier', 'unknown')}")
        print(f"  Required deposit: ₩{free_status_after['required']:,.0f}")
        print(f"  Can apply to jobs: {free_status_after['is_sufficient']}")

    print("\nPREMIUM User (after upgrade):")
    premium_status_after = check_deposit_status(premium_token)
    if premium_status_after:
        print(f"  Tier: {premium_status_after.get('membership_tier', 'unknown')}")
        print(f"  Required deposit: ₩{premium_status_after['required']:,.0f}")
        print(f"  Can apply to jobs: {premium_status_after['is_sufficient']}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ TEST RESULTS")
    print("=" * 60)
    print("\n🎯 Key Findings:")
    print(f"  1. Free users need ₩{free_status_after['required']:,.0f} deposit")
    print(f"  2. Premium users need ₩{premium_status_after['required']:,.0f} deposit")
    print(f"  3. Free users can apply: {free_status_after['is_sufficient']}")
    print(f"  4. Premium users can apply: {premium_status_after['is_sufficient']}")

    if premium_status_after['required'] == 0 and premium_status_after['is_sufficient']:
        print("\n✅ SUCCESS: Premium users have NO deposit requirement!")
    else:
        print("\n❌ FAILURE: Premium users still need deposit")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()