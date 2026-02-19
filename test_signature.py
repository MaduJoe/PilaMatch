#!/usr/bin/env python3
"""
Test script for dual signature requirement
"""

import requests
import json
from datetime import datetime, date, time, timedelta
import uuid

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
INSTRUCTOR_PHONE = "01012345678"
STUDIO_PHONE = "01087654321"
PASSWORD = "password123!"

def login(phone, password, role="instructor"):
    """Login and get access token"""
    # Create email from phone for test
    email = f"test{phone}@example.com"

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return None, None

    data = response.json()
    token = data["access_token"]

    # Get profile to get profile_id
    headers = {"Authorization": f"Bearer {token}"}
    profile_response = requests.get(
        f"{BASE_URL}/{role}_profiles/me",
        headers=headers
    )

    profile_id = None
    if profile_response.status_code == 200:
        profile_id = profile_response.json()["id"]
    else:
        print(f"Failed to get profile: {profile_response.text}")

    return token, profile_id


def create_job_post(studio_token):
    """Create a job post as studio"""
    headers = {"Authorization": f"Bearer {studio_token}"}

    tomorrow = (datetime.now() + timedelta(days=1)).date()

    response = requests.post(
        f"{BASE_URL}/job_posts",
        headers=headers,
        json={
            "title": "Signature Test Job",
            "description": "Testing dual signature requirement",
            "date": tomorrow.isoformat(),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "hourly_rate": 50000,
            "location": "서울시 강남구",
            "requirements": ["테스트"],
            "preferred_style": "pilates"
        }
    )

    if response.status_code != 200:
        print(f"Failed to create job post: {response.text}")
        return None

    return response.json()["id"]


def apply_to_job(instructor_token, job_id):
    """Apply to job as instructor"""
    headers = {"Authorization": f"Bearer {instructor_token}"}

    response = requests.post(
        f"{BASE_URL}/applications",
        headers=headers,
        json={
            "job_post_id": job_id,
            "cover_letter": "Testing signature"
        }
    )

    if response.status_code != 200:
        print(f"Failed to apply: {response.text}")
        return None

    return response.json()["id"]


def send_offer(studio_token, application_id):
    """Send offer as studio"""
    headers = {"Authorization": f"Bearer {studio_token}"}

    response = requests.post(
        f"{BASE_URL}/offers",
        headers=headers,
        json={
            "application_id": application_id,
            "proposed_rate": 50000,
            "message": "Offer for signature test"
        }
    )

    if response.status_code != 200:
        print(f"Failed to send offer: {response.text}")
        return None

    return response.json()["id"]


def accept_offer(instructor_token, offer_id):
    """Accept offer as instructor"""
    headers = {"Authorization": f"Bearer {instructor_token}"}

    response = requests.post(
        f"{BASE_URL}/offers/{offer_id}/accept",
        headers=headers
    )

    if response.status_code != 200:
        print(f"Failed to accept offer: {response.text}")
        return None

    return response.json()["contract"]["id"]


def sign_contract(token, contract_id):
    """Sign a contract"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{BASE_URL}/contracts/{contract_id}/in-progress",
        headers=headers
    )

    return response


def get_contract(token, contract_id):
    """Get contract details"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/contracts/{contract_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"Failed to get contract: {response.text}")
        return None

    return response.json()


def main():
    print("=" * 50)
    print("Testing Dual Signature Requirement")
    print("=" * 50)

    # Step 1: Login as both users
    print("\n1. Logging in as instructor and studio...")
    instructor_token, instructor_profile_id = login(INSTRUCTOR_PHONE, PASSWORD, "instructor")
    studio_token, studio_profile_id = login(STUDIO_PHONE, PASSWORD, "studio")

    if not instructor_token or not studio_token:
        print("❌ Login failed. Please ensure test users exist.")
        return

    print("✅ Both users logged in successfully")

    # Step 2: Create job post, application, offer, and contract
    print("\n2. Setting up contract...")
    job_id = create_job_post(studio_token)
    if not job_id:
        return

    application_id = apply_to_job(instructor_token, job_id)
    if not application_id:
        return

    offer_id = send_offer(studio_token, application_id)
    if not offer_id:
        return

    contract_id = accept_offer(instructor_token, offer_id)
    if not contract_id:
        return

    print(f"✅ Contract created: {contract_id}")

    # Step 3: Test single signature
    print("\n3. Testing single signature...")

    # Instructor signs first
    print("   - Instructor signing...")
    response = sign_contract(instructor_token, contract_id)
    if response.status_code != 200:
        print(f"   ❌ Instructor signature failed: {response.text}")
        return

    # Check contract status
    contract = get_contract(instructor_token, contract_id)
    print(f"   - Contract status after instructor signature: {contract['status']}")
    print(f"   - Instructor signed at: {contract.get('instructor_signed_at', 'None')}")
    print(f"   - Studio signed at: {contract.get('studio_signed_at', 'None')}")

    if contract['status'] == 'in_progress':
        print("   ❌ ERROR: Contract moved to IN_PROGRESS with only one signature!")
        return
    elif contract['status'] == 'confirmed':
        print("   ✅ Contract remains in CONFIRMED status (correct)")

    # Step 4: Test duplicate signature
    print("\n4. Testing duplicate signature...")
    response = sign_contract(instructor_token, contract_id)
    if response.status_code == 200:
        print("   ❌ ERROR: Allowed duplicate signature!")
    else:
        print(f"   ✅ Duplicate signature prevented: {response.json().get('detail', 'Error')}")

    # Step 5: Complete with second signature
    print("\n5. Testing second signature...")

    # Studio signs second
    print("   - Studio signing...")
    response = sign_contract(studio_token, contract_id)
    if response.status_code != 200:
        print(f"   ❌ Studio signature failed: {response.text}")
        return

    # Check final status
    contract = get_contract(studio_token, contract_id)
    print(f"   - Contract status after both signatures: {contract['status']}")
    print(f"   - Instructor signed at: {contract.get('instructor_signed_at', 'None')}")
    print(f"   - Studio signed at: {contract.get('studio_signed_at', 'None')}")

    if contract['status'] == 'in_progress':
        print("   ✅ Contract moved to IN_PROGRESS after both signatures (correct)")
    else:
        print(f"   ❌ ERROR: Contract status is {contract['status']}, expected 'in_progress'")

    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()