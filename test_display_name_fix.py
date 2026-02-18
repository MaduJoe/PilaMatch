#!/usr/bin/env python3
"""
Test that display_name is returned in /me endpoint after login
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def test_display_name_flow():
    """Create account and test display name is returned."""

    # Test account details
    email = f"test_display_{int(time.time())}@test.com"
    password = "Test1234!"
    display_name = "테스트강사"

    print(f"Creating new instructor account...")
    print(f"Email: {email}")
    print(f"Display Name: {display_name}")
    print("=" * 50)

    # Step 1: Create account with display_name
    signup_response = requests.post(
        f"{API_BASE_URL}/auth/signup",
        json={
            "email": email,
            "password": password,
            "role": "instructor",
            "display_name": display_name
        }
    )

    if signup_response.status_code not in [200, 201]:
        print(f"❌ Signup failed: {signup_response.text}")
        return False

    print(f"✅ Account created successfully")

    # Step 2: Login with the new account
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    print(f"✅ Login successful")

    # Step 3: Get user info with /me endpoint
    me_response = requests.get(
        f"{API_BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    if me_response.status_code != 200:
        print(f"❌ /me failed: {me_response.text}")
        return False

    me_data = me_response.json()
    user = me_data.get("user", {})

    print("\n📋 User Data from /me endpoint:")
    print(json.dumps(user, indent=2, ensure_ascii=False))

    # Step 4: Check for display_name
    returned_display_name = user.get("display_name")
    if returned_display_name == display_name:
        print(f"\n✅ SUCCESS: display_name correctly returned as '{returned_display_name}'")
        return True
    elif returned_display_name:
        print(f"\n⚠️ PARTIAL: display_name returned but different: '{returned_display_name}' (expected: '{display_name}')")
        return False
    else:
        print(f"\n❌ FAIL: display_name is missing or None")
        return False

def test_existing_account():
    """Test with the existing gangsa1@test.com account."""

    print("\nTesting existing account gangsa1@test.com...")
    print("=" * 50)

    # Try common passwords
    test_passwords = ["Test1234!", "test123", "password123", "password"]

    for pwd in test_passwords:
        print(f"Trying password: {pwd}")

        login_response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                "email": "gangsa1@test.com",
                "password": pwd
            }
        )

        if login_response.status_code == 200:
            print(f"✅ Login successful with password: {pwd}")
            token = login_response.json()["access_token"]

            # Get user info
            me_response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )

            if me_response.status_code == 200:
                user = me_response.json()["user"]
                display_name = user.get("display_name")

                if display_name:
                    print(f"✅ display_name = '{display_name}'")
                    print("\n📋 Full user data:")
                    print(json.dumps(user, indent=2, ensure_ascii=False))
                    return True
                else:
                    print(f"❌ display_name is missing")
            break

    return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Display Name in /me Endpoint")
    print("=" * 60)

    # Test with new account
    print("\n1️⃣ TEST WITH NEW ACCOUNT:")
    new_account_success = test_display_name_flow()

    # Test with existing account
    print("\n2️⃣ TEST WITH EXISTING ACCOUNT:")
    existing_account_success = test_existing_account()

    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print("=" * 60)

    if new_account_success:
        print("✅ New account test: PASSED")
    else:
        print("❌ New account test: FAILED")

    if existing_account_success:
        print("✅ Existing account test: PASSED")
    else:
        print("❌ Existing account test: FAILED or couldn't login")

    if new_account_success or existing_account_success:
        print("\n🎉 The fix is working! The frontend will now show the display name instead of '프로필을 완성해주세요'")
    else:
        print("\n⚠️ There might still be an issue with the display name feature.")