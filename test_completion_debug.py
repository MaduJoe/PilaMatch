#!/usr/bin/env python3
"""Debug script for bidirectional completion issue"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_completion():
    # Create test accounts
    test_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # 1. Signup
    instructor = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": f"inst_debug_{test_id}@test.com",
        "password": "Test1234!",
        "role": "instructor",
        "display_name": "Debug Instructor"
    }).json()

    studio = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": f"studio_debug_{test_id}@test.com",
        "password": "Test1234!",
        "role": "studio",
        "business_name": "Debug Studio"
    }).json()

    inst_token = instructor["access_token"]
    studio_token = studio["access_token"]

    # 2. Setup profiles
    inst_profile = requests.put(f"{BASE_URL}/instructors/me",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "name": "Debug Instructor",
            "categories": ["pilates"],
            "bio": "Test",
            "certifications": ["Test"],
            "experience_years": 5,
            "locations": ["강남구"],
            "hourly_rate_min": 50000,
            "hourly_rate_max": 80000
        }).json()

    studio_profile = requests.put(f"{BASE_URL}/studios/me",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "business_name": "Debug Studio",
            "address": "Test",
            "description": "Test",
            "categories": ["pilates"],
            "amenities": ["주차"]
        }).json()

    # 3. Create job post
    job = requests.post(f"{BASE_URL}/job-posts",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "title": "Debug Job",
            "description": "Test",
            "category": "pilates",
            "job_type": "substitute",
            "date": "2026-02-21",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "hourly_rate": 60000,
            "total_sessions": 1,
            "location": "강남구",
            "requirements": ["Test"]
        }).json()

    job_id = job["id"]

    # 4. Add deposit first
    deposit_add = requests.post(f"{BASE_URL}/deposit/add",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"amount": 30000}).json()
    print(f"Deposit added: {deposit_add}")

    # 5. Apply
    application = requests.post(f"{BASE_URL}/job-posts/{job_id}/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"cover_letter": "Test"}).json()

    app_id = application["id"]

    # 6. Create offer
    offer = requests.post(f"{BASE_URL}/offers",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "application_id": app_id,
            "proposed_rate": 60000
        }).json()

    offer_id = offer["id"]

    # 7. Accept offer
    accept = requests.post(f"{BASE_URL}/offers/{offer_id}/accept",
        headers={"Authorization": f"Bearer {inst_token}"}).json()

    # 8. Create contract
    contract = requests.post(f"{BASE_URL}/contracts/from-offer/{offer_id}",
        headers={"Authorization": f"Bearer {studio_token}"}).json()

    contract_id = contract["id"]
    print(f"Contract created: {contract_id}, Status: {contract['status']}")

    # 9. Set in progress
    in_progress = requests.post(f"{BASE_URL}/contracts/{contract_id}/set-in-progress",
        headers={"Authorization": f"Bearer {studio_token}"}).json()
    print(f"Contract in progress: {in_progress['status']}")

    # 10. Studio confirms completion
    print("\n--- STUDIO CONFIRMATION ---")
    studio_confirm = requests.post(f"{BASE_URL}/contracts/{contract_id}/confirm-completion",
        headers={"Authorization": f"Bearer {studio_token}"})

    print(f"Status Code: {studio_confirm.status_code}")
    if studio_confirm.status_code == 200:
        result = studio_confirm.json()
        print(f"Status: {result.get('status')}")
        print(f"Studio confirmed at: {result.get('studio_confirmed_at')}")
        print(f"Instructor confirmed at: {result.get('instructor_confirmed_at')}")
    else:
        print(f"Error: {studio_confirm.text}")

    # 11. Instructor confirms completion
    print("\n--- INSTRUCTOR CONFIRMATION ---")
    inst_confirm = requests.post(f"{BASE_URL}/contracts/{contract_id}/confirm-completion",
        headers={"Authorization": f"Bearer {inst_token}"})

    print(f"Status Code: {inst_confirm.status_code}")
    if inst_confirm.status_code == 200:
        result = inst_confirm.json()
        print(f"Status: {result.get('status')}")
        print(f"Studio confirmed at: {result.get('studio_confirmed_at')}")
        print(f"Instructor confirmed at: {result.get('instructor_confirmed_at')}")
        print(f"Platform fee: {result.get('platform_fee')}")
        print(f"Settlement amount: {result.get('settlement_amount')}")
    else:
        print(f"Error: {inst_confirm.text}")

if __name__ == "__main__":
    test_completion()