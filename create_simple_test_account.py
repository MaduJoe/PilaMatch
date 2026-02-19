#!/usr/bin/env python3
"""
Create simple test accounts with known passwords
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_account(email, password, role, display_name=None, business_name=None):
    """Create a simple test account"""

    # Prepare signup data
    signup_data = {
        "email": email,
        "password": password,
        "role": role
    }

    if role == "instructor" and display_name:
        signup_data["display_name"] = display_name
    elif role == "studio" and business_name:
        signup_data["business_name"] = business_name

    # Register user
    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json=signup_data
    )

    if response.status_code == 200:
        print(f"✅ Created {role}: {email}")
        print(f"   Password: {password}")
        return True
    elif "already exists" in response.text:
        print(f"ℹ️  User {email} already exists")
        print(f"   Password: {password}")
        return True
    else:
        print(f"❌ Failed to create {role}: {response.text}")
        return False

def main():
    print("=" * 60)
    print("Creating Simple Test Accounts")
    print("=" * 60)

    # Create test instructor account
    print("\n📚 Instructor Account:")
    create_account(
        email="test_instructor@example.com",
        password="Test1234!",
        role="instructor",
        display_name="Test Instructor"
    )

    print("\n🏢 Studio Account:")
    create_account(
        email="test_studio@example.com",
        password="Test1234!",
        role="studio",
        business_name="Test Studio"
    )

    print("\n" + "=" * 60)
    print("✅ Test accounts ready!")
    print("\n🔐 Login Credentials:")
    print("\nInstructor:")
    print("  Email: test_instructor@example.com")
    print("  Password: Test1234!")
    print("\nStudio:")
    print("  Email: test_studio@example.com")
    print("  Password: Test1234!")
    print("\n📌 Frontend URL: http://localhost:8501")
    print("=" * 60)

if __name__ == "__main__":
    main()