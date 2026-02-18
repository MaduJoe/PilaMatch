#!/usr/bin/env python3
"""
Create instructor account with display name
"""

import requests
import json

API_BASE_URL = "http://localhost:8000/api/v1"

def create_instructor():
    """Create instructor with display name."""

    # Signup new instructor
    signup_response = requests.post(
        f"{API_BASE_URL}/auth/signup",
        json={
            "email": "gangsa1@test.com",
            "password": "password123",
            "role": "instructor",
            "display_name": "강사1"
        }
    )

    if signup_response.status_code == 201:
        print(f"✅ Instructor created successfully")
        token = signup_response.json()["access_token"]

        # Now check /me endpoint
        me_response = requests.get(
            f"{API_BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        if me_response.status_code == 200:
            user = me_response.json()["user"]
            print(f"\n📋 User data:")
            print(json.dumps(user, indent=2, ensure_ascii=False))

            if user.get("display_name"):
                print(f"\n✅ Display name: '{user['display_name']}'")
            else:
                print(f"\n❌ Display name not found in response")
        else:
            print(f"❌ Failed to get user info: {me_response.text}")
    else:
        print(f"❌ Failed to create instructor: {signup_response.text}")

if __name__ == "__main__":
    print("Creating instructor account with display_name='강사1'...")
    print("=" * 50)
    create_instructor()