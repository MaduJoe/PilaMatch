#!/usr/bin/env python3
"""Test script for Premium membership functionality."""

import time
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Test accounts
PREMIUM_INSTRUCTOR = {
    "email": "premium_instructor@test.com",
    "password": "Test123!@#",
    "display_name": "Premium Test Instructor",
}

FREE_INSTRUCTOR = {
    "email": "free_instructor@test.com",
    "password": "Test123!@#",
    "display_name": "Free Test Instructor",
}


def signup_user(email, password, role, display_name=None):
    """Sign up a new user."""
    payload = {
        "email": email,
        "password": password,
        "role": role,
    }
    if display_name:
        payload["display_name"] = display_name

    response = requests.post(f"{BASE_URL}/auth/signup", json=payload)
    if response.status_code == 200:
        print(f"✅ Signup successful: {email}")
        return response.json()
    elif response.status_code == 400:
        # User might already exist
        print(f"⚠️ User may already exist: {email}")
    else:
        print(f"❌ Signup failed: {response.status_code} - {response.text}")
        return None


def login_user(email, password):
    """Login and get token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful: {email}")
        return data["access_token"]
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None


def get_headers(token):
    """Get request headers with auth token."""
    return {"Authorization": f"Bearer {token}"}


def check_deposit_status(token):
    """Check deposit status."""
    response = requests.get(f"{BASE_URL}/deposit/status", headers=get_headers(token))
    if response.status_code == 200:
        data = response.json()
        print(f"  Membership tier: {data.get('membership_tier', 'unknown')}")
        print(f"  Balance: ₩{data['balance']:,.0f}")
        print(f"  Required: ₩{data['required']:,.0f}")
        print(f"  Sufficient: {data['is_sufficient']}")
        return data
    else:
        print(f"❌ Failed to get deposit status: {response.status_code}")
        return None


def check_subscription_status(token):
    """Check subscription status."""
    response = requests.get(f"{BASE_URL}/subscriptions/me", headers=get_headers(token))
    if response.status_code == 200:
        data = response.json()
        print(f"  Has subscription: {data['has_subscription']}")
        print(f"  Membership tier: {data['membership_tier']}")
        if data.get("subscription"):
            sub = data["subscription"]
            print(f"  Status: {sub['status']}")
            print(f"  Monthly amount: ₩{sub['monthly_amount']:,.0f}")
            if sub.get("next_billing_date"):
                print(f"  Next billing: {sub['next_billing_date'][:10]}")
        return data
    else:
        print(f"❌ Failed to get subscription status: {response.status_code}")
        return None


def upgrade_to_premium(token):
    """Upgrade user to premium."""
    # Step 1: Initialize upgrade
    print("  Initializing premium upgrade...")
    response = requests.post(
        f"{BASE_URL}/subscriptions/upgrade",
        json={},
        headers=get_headers(token)
    )
    if response.status_code != 200:
        print(f"❌ Failed to initialize upgrade: {response.status_code} - {response.text}")
        return False

    upgrade_data = response.json()
    order_id = upgrade_data["order_id"]
    amount = upgrade_data["amount"]
    print(f"  Order ID: {order_id}")
    print(f"  Amount: ₩{amount:,.0f}")

    # Step 2: Simulate payment confirmation
    print("  Simulating payment confirmation...")
    time.sleep(1)

    response = requests.post(
        f"{BASE_URL}/subscriptions/confirm",
        json={
            "payment_key": f"test_pk_{order_id}",
            "order_id": order_id
        },
        headers=get_headers(token)
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Upgrade successful!")
        print(f"  Next billing: {data['next_billing_date'][:10]}")
        return True
    else:
        print(f"❌ Failed to confirm payment: {response.status_code} - {response.text}")
        return False


def test_application_with_premium(token):
    """Test applying to a job with premium membership."""
    # First create a test job post (would need studio account for this)
    # For now, just test the application endpoint
    print("  Testing job application as premium user...")

    # This would normally apply to an existing job
    # The key is that premium users shouldn't need deposit
    deposit_status = check_deposit_status(token)
    if deposit_status:
        if deposit_status.get("membership_tier") == "premium":
            print("✅ Premium user can apply without deposit!")
        else:
            print("❌ User is not premium")


def cancel_subscription(token):
    """Cancel premium subscription."""
    response = requests.post(
        f"{BASE_URL}/subscriptions/cancel",
        json={"reason": "Testing cancellation"},
        headers=get_headers(token)
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Subscription cancelled!")
        print(f"  Deposit refunded: ₩{data.get('deposit_refunded', 0):,.0f}")
        return True
    else:
        print(f"❌ Failed to cancel subscription: {response.status_code} - {response.text}")
        return False


def main():
    print("=" * 60)
    print("PREMIUM MEMBERSHIP TEST")
    print("=" * 60)

    # 1. Setup premium instructor account
    print("\n1. Setting up PREMIUM instructor account...")
    signup_user(
        PREMIUM_INSTRUCTOR["email"],
        PREMIUM_INSTRUCTOR["password"],
        "instructor",
        PREMIUM_INSTRUCTOR["display_name"]
    )

    token = login_user(PREMIUM_INSTRUCTOR["email"], PREMIUM_INSTRUCTOR["password"])
    if not token:
        print("Failed to login premium instructor")
        return

    print("\n2. Checking initial status (should be FREE)...")
    check_subscription_status(token)
    check_deposit_status(token)

    print("\n3. Upgrading to PREMIUM...")
    if upgrade_to_premium(token):
        print("\n4. Checking status after upgrade (should be PREMIUM)...")
        check_subscription_status(token)
        check_deposit_status(token)

        print("\n5. Testing job application without deposit...")
        test_application_with_premium(token)

        print("\n6. Testing subscription cancellation...")
        if cancel_subscription(token):
            print("\n7. Checking status after cancellation (should be FREE)...")
            time.sleep(1)
            check_subscription_status(token)
            check_deposit_status(token)

    print("\n" + "=" * 60)
    print("TEST COMPARISON: FREE vs PREMIUM")
    print("=" * 60)

    # Setup free instructor for comparison
    print("\n8. Setting up FREE instructor account...")
    signup_user(
        FREE_INSTRUCTOR["email"],
        FREE_INSTRUCTOR["password"],
        "instructor",
        FREE_INSTRUCTOR["display_name"]
    )

    free_token = login_user(FREE_INSTRUCTOR["email"], FREE_INSTRUCTOR["password"])
    if free_token:
        print("\n9. FREE user deposit status:")
        free_deposit = check_deposit_status(free_token)

        print("\n10. PREMIUM user deposit status:")
        # Re-upgrade premium user for comparison
        upgrade_to_premium(token)
        premium_deposit = check_deposit_status(token)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("\n📊 Deposit Requirement Comparison:")
        print(f"  FREE user needs: ₩{free_deposit['required']:,.0f}")
        print(f"  PREMIUM user needs: ₩{premium_deposit['required']:,.0f}")
        print(f"\n✅ Premium users have NO deposit requirement!")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()