#!/usr/bin/env python3
"""Direct test of review API endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_review_endpoint_behavior():
    """Test how the review endpoint behaves without authentication."""

    # Test a dummy contract ID
    test_contract_id = "1081eada-dee6-4791-b0f6-8c961b81991f"

    print(f"Testing GET /contracts/{test_contract_id}/reviews/my")
    print("=" * 60)

    # Test without auth (should fail with 401)
    response = requests.get(f"{BASE_URL}/contracts/{test_contract_id}/reviews/my")
    print(f"Without auth - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}\n")

    # Test with a fake token (should also fail)
    headers = {"Authorization": "Bearer fake_token"}
    response = requests.get(f"{BASE_URL}/contracts/{test_contract_id}/reviews/my", headers=headers)
    print(f"With fake token - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}\n")

def check_api_docs():
    """Check if API is running and accessible."""
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 200:
        print("✅ API is running and accessible")
        return True
    else:
        print(f"❌ API is not accessible: {response.status_code}")
        return False

def test_auth_endpoint():
    """Test auth endpoint to verify it's working."""
    # Test with wrong credentials
    test_data = {
        "email": "test@test.com",
        "password": "test123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=test_data)
    print(f"\nAuth endpoint test - Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    print("🔍 Testing Review API Behavior\n")

    if check_api_docs():
        print("\n📋 Testing review endpoint behavior:")
        test_review_endpoint_behavior()

        print("\n🔐 Testing auth endpoint:")
        test_auth_endpoint()
    else:
        print("API is not running. Please check the backend service.")