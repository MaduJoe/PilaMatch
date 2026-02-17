#!/usr/bin/env python3
"""Debug script for dispute issue"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_dispute():
    # Create test accounts
    test_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # 1. Signup
    instructor = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": f"inst_disp_{test_id}@test.com",
        "password": "Test1234!",
        "role": "instructor",
        "display_name": "Dispute Instructor"
    }).json()

    studio = requests.post(f"{BASE_URL}/auth/signup", json={
        "email": f"studio_disp_{test_id}@test.com",
        "password": "Test1234!",
        "role": "studio",
        "business_name": "Dispute Studio"
    }).json()

    inst_token = instructor["access_token"]
    studio_token = studio["access_token"]

    print(f"Instructor token: {inst_token[:20]}...")
    print(f"Studio token: {studio_token[:20]}...")

    # 2. Setup profiles
    inst_profile = requests.put(f"{BASE_URL}/instructors/me",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={
            "name": "Dispute Instructor",
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
            "business_name": "Dispute Studio",
            "address": "Test",
            "description": "Test",
            "categories": ["pilates"],
            "amenities": ["주차"]
        }).json()

    print(f"Instructor profile: {inst_profile['id']}")
    print(f"Studio profile: {studio_profile['id']}")

    # 3. Get user IDs
    inst_me = requests.get(f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {inst_token}"}).json()

    studio_me = requests.get(f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {studio_token}"}).json()

    inst_user_id = inst_me["user"]["id"]
    studio_user_id = studio_me["user"]["id"]

    print(f"Instructor user ID: {inst_user_id}")
    print(f"Studio user ID: {studio_user_id}")

    # 4. Create job, apply, offer, contract (quick path)
    job = requests.post(f"{BASE_URL}/job-posts",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={
            "title": "Dispute Test Job",
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

    # Add deposit
    deposit_add = requests.post(f"{BASE_URL}/deposit/add",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"amount": 30000}).json()
    print(f"Deposit added: {deposit_add['new_balance']}")

    # Apply
    application = requests.post(f"{BASE_URL}/job-posts/{job['id']}/applications",
        headers={"Authorization": f"Bearer {inst_token}"},
        json={"cover_letter": "Test"}).json()

    # Offer
    offer = requests.post(f"{BASE_URL}/offers",
        headers={"Authorization": f"Bearer {studio_token}"},
        json={"application_id": application['id'], "proposed_rate": 60000}).json()

    # Accept
    requests.post(f"{BASE_URL}/offers/{offer['id']}/accept",
        headers={"Authorization": f"Bearer {inst_token}"})

    # Contract
    contract = requests.post(f"{BASE_URL}/contracts/from-offer/{offer['id']}",
        headers={"Authorization": f"Bearer {studio_token}"}).json()

    # Set in progress
    requests.post(f"{BASE_URL}/contracts/{contract['id']}/set-in-progress",
        headers={"Authorization": f"Bearer {studio_token}"})

    print(f"\nContract ready: {contract['id']}")

    # 5. Test no-show report
    print("\n--- TESTING NO-SHOW REPORT ---")
    print(f"Contract ID: {contract['id']}")
    print(f"Reported user ID: {inst_user_id}")

    response = requests.post(
        f"{BASE_URL}/contracts/{contract['id']}/report-no-show",
        headers={
            "Authorization": f"Bearer {studio_token}",
            "Content-Type": "application/json"
        },
        json={"reported_user_id": inst_user_id}
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        print("Success! Dispute created:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_dispute()