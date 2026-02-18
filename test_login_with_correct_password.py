#!/usr/bin/env python3
"""
Test login with hardcoded test password
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

# Common password for test accounts
TEST_PASSWORD = "test123"

def test_login_display_name():
    """Test that login returns display name for instructors."""

    # Login with instructor account
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": "gangsa1@test.com",
            "password": TEST_PASSWORD
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False

    token = login_response.json()["access_token"]
    print(f"✅ Login successful")

    # Get user info with /me endpoint
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

    # Check for display_name
    if user.get("role") == "instructor":
        display_name = user.get("display_name")
        if display_name:
            print(f"\n✅ SUCCESS: display_name = '{display_name}'")
            return True
        else:
            print(f"\n❌ FAIL: display_name is missing or None")
            return False
    else:
        print(f"\n⚠️ User is not an instructor, role = {user.get('role')}")
        return False

if __name__ == "__main__":
    print("Testing login with gangsa1@test.com...")
    print("=" * 50)

    success = test_login_display_name()

    print("\n" + "=" * 50)
    if success:
        print("✅ Test PASSED: display_name is included in /me response")
        print("✅ The frontend will now show '강사1' instead of '프로필을 완성해주세요'")
    else:
        print("❌ Test FAILED: display_name is not included in /me response")