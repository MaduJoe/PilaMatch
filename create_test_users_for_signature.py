#!/usr/bin/env python3
"""
Create test users for signature testing
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def create_user(email, phone, password, role):
    """Create a test user"""

    # Register user (v2 uses signup endpoint)
    signup_data = {
        "email": email,
        "password": password,
        "phone": phone,
        "role": role
    }

    # Add required fields for each role
    if role == "instructor":
        signup_data["display_name"] = f"Test Instructor {phone[-4:]}"
    else:  # studio
        signup_data["business_name"] = f"Test Studio {phone[-4:]}"

    response = requests.post(
        f"{BASE_URL}/auth/signup",
        json=signup_data
    )

    if response.status_code == 200:
        print(f"✅ Created {role}: {email}")
        user_data = response.json()
        access_token = user_data.get('access_token')

        # Create profile
        headers = {"Authorization": f"Bearer {access_token}"}

        profile_data = {
            "name": f"Test {role.title()}",
            "phone": phone,
            "region": "서울",
            "bio": f"Test {role} for signature testing"
        }

        if role == "instructor":
            profile_data.update({
                "experience_years": 3,
                "specialties": ["pilates"],
                "certifications": ["Test Cert"],
                "hourly_rate": 50000
            })
        else:  # studio
            profile_data.update({
                "business_name": "Test Studio",
                "business_number": "123-45-67890",
                "address": "서울시 강남구 테스트로 123",
                "facilities": ["매트", "기구"],
                "capacity": 10
            })

        profile_response = requests.post(
            f"{BASE_URL}/{role}_profiles",
            headers=headers,
            json=profile_data
        )

        if profile_response.status_code == 200:
            print(f"   Profile created for {role}")
        else:
            print(f"   Profile creation failed: {profile_response.text}")

        # Verify phone (dev mode)
        verify_response = requests.post(
            f"{BASE_URL}/auth/verify-phone",
            headers=headers,
            json={"verification_code": "000000"}  # Dev mode accepts any code
        )

        if verify_response.status_code == 200:
            print(f"   Phone verified for {role}")

        # Add deposit (50000 KRW)
        deposit_response = requests.post(
            f"{BASE_URL}/deposits",
            headers=headers,
            json={"amount": 50000}
        )

        if deposit_response.status_code == 200:
            print(f"   Deposit added for {role}")

        return True
    elif "already exists" in response.text:
        print(f"ℹ️  User {email} already exists")
        return True
    else:
        print(f"❌ Failed to create {role}: {response.text}")
        return False

def main():
    print("Creating test users for signature testing...")
    print("=" * 50)

    # Create instructor
    create_user(
        email="test01012345678@example.com",
        phone="01012345678",
        password="password123!",
        role="instructor"
    )

    print()

    # Create studio
    create_user(
        email="test01087654321@example.com",
        phone="01087654321",
        password="password123!",
        role="studio"
    )

    print("=" * 50)
    print("Test users created successfully!")
    print("\nYou can now run: python test_signature.py")

if __name__ == "__main__":
    main()