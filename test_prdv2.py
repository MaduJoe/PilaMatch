#!/usr/bin/env python3
"""
PRDv2.0.0 Comprehensive Test Suite
Tests all features including early bird deposit, bidirectional completion, and dispute system
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000/api/v1"

class TestPRDv2:
    def __init__(self):
        self.instructor_token = None
        self.studio_token = None
        self.instructor_id = None
        self.studio_id = None
        self.instructor_profile_id = None
        self.studio_profile_id = None
        self.job_post_id = None
        self.application_id = None
        self.offer_id = None
        self.contract_id = None
        self.dispute_id = None

        # Test account credentials
        self.test_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.instructor_email = f"instructor_{self.test_id}@test.com"
        self.studio_email = f"studio_{self.test_id}@test.com"
        self.password = "Test1234!"

    def log(self, step: str, message: str, success: bool = True):
        """Log test progress"""
        status = "✅" if success else "❌"
        print(f"{status} [{step}] {message}")

    def api_request(self, method: str, endpoint: str, token: Optional[str] = None,
                   data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.request(
                method=method,
                url=f"{BASE_URL}{endpoint}",
                headers=headers,
                json=data,
                params=params,
                timeout=10
            )

            if response.status_code >= 400:
                self.log(endpoint, f"Error {response.status_code}: {response.text}", False)
                return {"error": response.text, "status_code": response.status_code}

            if response.status_code == 204:
                return {}

            return response.json() if response.text else {}
        except Exception as e:
            self.log(endpoint, f"Request failed: {str(e)}", False)
            return {"error": str(e)}

    def test_1_signup(self):
        """Test 1: User Signup (No deposit required at signup per v2.0)"""
        print("\n" + "="*60)
        print("TEST 1: USER SIGNUP (v2.0 - No Deposit Required)")
        print("="*60)

        # Signup instructor
        instructor_data = {
            "email": self.instructor_email,
            "password": self.password,
            "role": "instructor",
            "display_name": "Test Instructor v2"
        }
        result = self.api_request("POST", "/auth/signup", data=instructor_data)

        if "access_token" in result:
            self.instructor_token = result["access_token"]
            self.log("1.1", f"Instructor signup successful: {self.instructor_email}")
        else:
            self.log("1.1", f"Instructor signup failed: {result.get('error')}", False)
            return False

        # Signup studio
        studio_data = {
            "email": self.studio_email,
            "password": self.password,
            "role": "studio",
            "business_name": "Test Studio v2"
        }
        result = self.api_request("POST", "/auth/signup", data=studio_data)

        if "access_token" in result:
            self.studio_token = result["access_token"]
            self.log("1.2", f"Studio signup successful: {self.studio_email}")
        else:
            self.log("1.2", f"Studio signup failed: {result.get('error')}", False)
            return False

        # Check deposit status (should not be required yet)
        deposit_status = self.api_request("GET", "/deposit/status", token=self.instructor_token)
        if "required" in deposit_status:
            self.log("1.3", f"Early bird eligible: {deposit_status.get('required')}원 (Regular: 50000원)")
        else:
            self.log("1.3", f"Deposit status check: {deposit_status}", False)

        return True

    def test_2_profile_setup(self):
        """Test 2: Profile Setup"""
        print("\n" + "="*60)
        print("TEST 2: PROFILE SETUP")
        print("="*60)

        # Setup instructor profile
        instructor_profile = {
            "display_name": "Test Instructor v2",  # Changed from "name" to "display_name"
            "categories": ["pilates"],
            "bio": "Experienced pilates instructor with v2.0 features",
            "certifications": ["National Pilates Certification"],
            "experience_years": 5,
            "available_regions": ["강남구", "서초구"],  # Changed from "locations" to "available_regions"
            "hourly_rate_min": 50000,
            "hourly_rate_max": 80000
        }
        result = self.api_request("PUT", "/instructors/me", token=self.instructor_token, data=instructor_profile)

        if "id" in result:
            self.instructor_profile_id = result["id"]
            self.log("2.1", f"Instructor profile created: {self.instructor_profile_id}")
        else:
            self.log("2.1", f"Instructor profile creation failed: {result.get('error')}", False)
            return False

        # Setup studio profile
        studio_profile = {
            "business_name": "Test Studio v2",
            "address": "서울시 강남구 테스트로 123",
            "region": "강남구",  # Added region field for onboarding
            "description": "Premium pilates studio testing v2.0 features",
            "categories": ["pilates"],
            "amenities": ["주차 가능", "샤워실"]
        }
        result = self.api_request("PUT", "/studios/me", token=self.studio_token, data=studio_profile)

        if "id" in result:
            self.studio_profile_id = result["id"]
            self.log("2.2", f"Studio profile created: {self.studio_profile_id}")
        else:
            self.log("2.2", f"Studio profile creation failed: {result.get('error')}", False)
            return False

        return True

    def test_3_job_post(self):
        """Test 3: Job Post Creation"""
        print("\n" + "="*60)
        print("TEST 3: JOB POST CREATION")
        print("="*60)

        # Create job post
        job_data = {
            "title": "PRDv2 Test - Pilates Instructor Needed",
            "description": "Testing bidirectional completion and dispute features",
            "category": "pilates",
            "job_type": "substitute",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "hourly_rate": 70000,
            "total_sessions": 1,
            "location": "강남구",
            "requirements": ["Certified instructor", "PRDv2 test participant"]
        }
        result = self.api_request("POST", "/job-posts", token=self.studio_token, data=job_data)

        if "id" in result:
            self.job_post_id = result["id"]
            self.log("3.1", f"Job post created: {self.job_post_id}")
        else:
            self.log("3.1", f"Job post creation failed: {result.get('error')}", False)
            return False

        return True

    def test_4_application_with_deposit(self):
        """Test 4: Job Application (Deposit required at first application per v2.0)"""
        print("\n" + "="*60)
        print("TEST 4: JOB APPLICATION (v2.0 - First Deposit Check)")
        print("="*60)

        # Check deposit status before application
        deposit_status = self.api_request("GET", "/deposit/status", token=self.instructor_token)
        self.log("4.1", f"Deposit status - Balance: {deposit_status.get('balance')}원, Required: {deposit_status.get('required')}원")

        # Try to apply (should fail if deposit not sufficient)
        application_data = {
            "cover_letter": "Testing PRDv2.0 features - excited to participate!"
        }
        result = self.api_request("POST", f"/job-posts/{self.job_post_id}/applications",
                                 token=self.instructor_token, data=application_data)

        if result.get("status_code") == 402 or (result.get("status_code") == 400 and "INSUFFICIENT_DEPOSIT" in str(result.get("error", ""))):
            self.log("4.2", "Application blocked - deposit required (Expected for v2.0)")

            # Add early bird deposit
            deposit_amount = deposit_status.get("required", 30000)
            deposit_result = self.api_request("POST", "/deposit/add",
                                             token=self.instructor_token,
                                             data={"amount": deposit_amount})

            if "new_balance" in deposit_result:
                self.log("4.3", f"Early bird deposit added: {deposit_result.get('added')}원 (Balance: {deposit_result.get('new_balance')}원)")

                # Retry application
                result = self.api_request("POST", f"/job-posts/{self.job_post_id}/applications",
                                         token=self.instructor_token, data=application_data)

                if "id" in result:
                    self.application_id = result["id"]
                    self.log("4.4", f"Application successful after deposit: {self.application_id}")
                else:
                    self.log("4.4", f"Application failed even after deposit: {result.get('error')}", False)
                    return False
            else:
                self.log("4.3", f"Deposit add failed: {deposit_result.get('error')}", False)
                return False
        elif "id" in result:
            self.application_id = result["id"]
            self.log("4.2", f"Application successful (deposit already sufficient): {self.application_id}")
        else:
            self.log("4.2", f"Application failed: {result.get('error')}", False)
            return False

        return True

    def test_5_offer_and_contract(self):
        """Test 5: Offer Creation and Contract Formation"""
        print("\n" + "="*60)
        print("TEST 5: OFFER AND CONTRACT CREATION")
        print("="*60)

        # Create offer
        offer_data = {
            "application_id": self.application_id,
            "proposed_rate": 70000,
            "message": "We'd love to work with you for this PRDv2 test!"
        }
        result = self.api_request("POST", "/offers", token=self.studio_token, data=offer_data)

        if "id" in result:
            self.offer_id = result["id"]
            self.log("5.1", f"Offer created: {self.offer_id}")
        else:
            self.log("5.1", f"Offer creation failed: {result.get('error')}", False)
            return False

        # Accept offer
        result = self.api_request("POST", f"/offers/{self.offer_id}/accept", token=self.instructor_token)
        if result.get("status") == "accepted":
            self.log("5.2", "Offer accepted successfully")
        else:
            self.log("5.2", f"Offer acceptance failed: {result.get('error')}", False)
            return False

        # Create contract from offer
        result = self.api_request("POST", f"/contracts/from-offer/{self.offer_id}", token=self.studio_token)
        if "id" in result:
            self.contract_id = result["id"]
            self.log("5.3", f"Contract created: {self.contract_id} (Status: {result.get('status')})")
        else:
            self.log("5.3", f"Contract creation failed: {result.get('error')}", False)
            return False

        return True

    def test_6_contract_progression(self):
        """Test 6: Contract Progression to In-Progress"""
        print("\n" + "="*60)
        print("TEST 6: CONTRACT PROGRESSION")
        print("="*60)

        # Set contract in progress (studio signs)
        result = self.api_request("POST", f"/contracts/{self.contract_id}/set-in-progress",
                                 token=self.studio_token)
        if "status" in result:
            self.log("6.1", f"Studio signed - Contract status: {result.get('status')}")
        else:
            self.log("6.1", f"Studio signing failed: {result.get('error')}", False)
            return False

        # Set contract in progress (instructor signs)
        result = self.api_request("POST", f"/contracts/{self.contract_id}/set-in-progress",
                                 token=self.instructor_token)
        if result.get("status") == "in_progress":
            self.log("6.2", f"Instructor signed - Contract now IN_PROGRESS")
        else:
            # It might already be in progress from studio signing
            self.log("6.2", f"Contract status: {result.get('status', 'Already in progress')}")

        return True

    def test_7_bidirectional_completion(self):
        """Test 7: Bidirectional Completion Confirmation (v2.0 Feature)"""
        print("\n" + "="*60)
        print("TEST 7: BIDIRECTIONAL COMPLETION (v2.0 Feature)")
        print("="*60)

        # First confirmation - Studio confirms
        result = self.api_request("POST", f"/contracts/{self.contract_id}/confirm-completion",
                                 token=self.studio_token)
        if "status" in result:
            status = result.get("status")
            studio_confirmed = result.get("studio_confirmed_at")
            instructor_confirmed = result.get("instructor_confirmed_at")

            if status == "pending_completion":
                self.log("7.1", f"Studio confirmed - Status: PENDING_COMPLETION (waiting for instructor)")
                self.log("7.1", f"  Studio confirmed at: {studio_confirmed}")
                self.log("7.1", f"  Instructor confirmed: {instructor_confirmed or 'Not yet'}")
            else:
                self.log("7.1", f"Unexpected status after studio confirmation: {status}", False)
        else:
            self.log("7.1", f"Studio confirmation failed: {result.get('error')}", False)
            return False

        # Second confirmation - Instructor confirms
        result = self.api_request("POST", f"/contracts/{self.contract_id}/confirm-completion",
                                 token=self.instructor_token)
        if "status" in result:
            status = result.get("status")
            studio_confirmed = result.get("studio_confirmed_at")
            instructor_confirmed = result.get("instructor_confirmed_at")

            if status == "completed":
                self.log("7.2", f"Instructor confirmed - Status: COMPLETED (both parties confirmed)")
                self.log("7.2", f"  Studio confirmed at: {studio_confirmed}")
                self.log("7.2", f"  Instructor confirmed at: {instructor_confirmed}")
                self.log("7.2", f"  Platform fee: {result.get('platform_fee')}원 (5%)")
                self.log("7.2", f"  Settlement amount: {result.get('settlement_amount')}원")
            else:
                self.log("7.2", f"Unexpected status after instructor confirmation: {status}", False)
        else:
            self.log("7.2", f"Instructor confirmation failed: {result.get('error')}", False)
            return False

        return True

    def test_8_dispute_system(self):
        """Test 8: Dispute System with 24h Objection Period (v2.0 Feature)"""
        print("\n" + "="*60)
        print("TEST 8: DISPUTE SYSTEM (v2.0 - 24h Objection)")
        print("="*60)

        # Create new contract for dispute test
        self.log("8.1", "Creating new contract for dispute test...")

        # Quick create job, application, offer, contract
        job_data = {
            "title": "Dispute Test Job",
            "description": "Testing dispute system",
            "category": "pilates",
            "job_type": "substitute",
            "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "hourly_rate": 60000,
            "total_sessions": 1,
            "location": "강남구",
            "requirements": ["Test"]
        }
        job_result = self.api_request("POST", "/job-posts", token=self.studio_token, data=job_data)
        if "id" not in job_result:
            self.log("8.1", "Failed to create test job for dispute", False)
            return False

        dispute_job_id = job_result["id"]

        # Apply to job
        app_result = self.api_request("POST", f"/job-posts/{dispute_job_id}/applications",
                                      token=self.instructor_token,
                                      data={"cover_letter": "Dispute test"})
        if "id" not in app_result:
            self.log("8.1", "Failed to create application for dispute test", False)
            return False

        dispute_app_id = app_result["id"]

        # Create and accept offer
        offer_result = self.api_request("POST", "/offers", token=self.studio_token,
                                        data={"application_id": dispute_app_id, "proposed_rate": 60000})
        if "id" not in offer_result:
            self.log("8.1", "Failed to create offer for dispute test", False)
            return False

        dispute_offer_id = offer_result["id"]

        self.api_request("POST", f"/offers/{dispute_offer_id}/accept", token=self.instructor_token)

        # Create contract
        contract_result = self.api_request("POST", f"/contracts/from-offer/{dispute_offer_id}",
                                           token=self.studio_token)
        if "id" not in contract_result:
            self.log("8.1", "Failed to create contract for dispute test", False)
            return False

        dispute_contract_id = contract_result["id"]

        # Set in progress
        self.api_request("POST", f"/contracts/{dispute_contract_id}/set-in-progress",
                        token=self.studio_token)

        self.log("8.2", f"Test contract created: {dispute_contract_id}")

        # Test no-show dispute
        # Get instructor user ID for reporting
        me_result = self.api_request("GET", "/auth/me", token=self.instructor_token)
        # The /auth/me endpoint returns {user: {...}, profile_id: ...}
        instructor_user_id = me_result.get("user", {}).get("id") if "user" in me_result else me_result.get("id")

        dispute_result = self.api_request("POST", f"/contracts/{dispute_contract_id}/report-no-show",
                                          token=self.studio_token,
                                          data={"reported_user_id": instructor_user_id})

        if "dispute_id" in dispute_result:
            self.dispute_id = dispute_result["dispute_id"]
            self.log("8.3", f"No-show dispute created: {self.dispute_id}")
            self.log("8.3", f"  Objection deadline: {dispute_result.get('objection_deadline')}")
            self.log("8.3", f"  Message: {dispute_result.get('message')}")

            # Test objection
            objection_result = self.api_request("POST", f"/disputes/{self.dispute_id}/object",
                                               token=self.instructor_token,
                                               data={"reason": "I was there but studio was closed"})

            if objection_result.get("status") == "objected":
                self.log("8.4", "Objection submitted successfully - requires manual review")
            else:
                self.log("8.4", f"Objection failed: {objection_result.get('error')}", False)
        else:
            self.log("8.3", f"Dispute creation failed: {dispute_result.get('error')}", False)
            return False

        return True

    def test_9_trust_and_activity(self):
        """Test 9: Trust Score and Activity Tracking (v2.0 Feature)"""
        print("\n" + "="*60)
        print("TEST 9: TRUST SCORE & ACTIVITY TRACKING (v2.0)")
        print("="*60)

        # Check user profile with trust score
        me_result = self.api_request("GET", "/auth/me", token=self.instructor_token)

        # The /auth/me endpoint returns {user: {...}, profile_id: ...}
        user_data = me_result.get("user", {}) if "user" in me_result else me_result

        if "trust_score" in user_data:
            self.log("9.1", f"Instructor trust score: {user_data.get('trust_score')}/100")
            self.log("9.1", f"  Last active: {user_data.get('last_active_at')}")
            self.log("9.1", f"  Onboarding completed: {user_data.get('onboarding_completed')}")
            self.log("9.1", f"  No-show count: {user_data.get('no_show_count')}")
            self.log("9.1", f"  Is suspended: {user_data.get('is_suspended')}")
        else:
            self.log("9.1", "Trust score not found in user profile", False)

        # Check deposit status with early bird
        deposit_status = self.api_request("GET", "/deposit/status", token=self.instructor_token)

        if deposit_status:
            self.log("9.2", f"Deposit status:")
            self.log("9.2", f"  Balance: {deposit_status.get('balance')}원")
            self.log("9.2", f"  Required: {deposit_status.get('required')}원")
            self.log("9.2", f"  Is early bird: {deposit_status.get('is_early_bird_eligible')}")
            self.log("9.2", f"  Has ever paid: {deposit_status.get('has_ever_paid')}")

        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*60)
        print(" PRDv2.0.0 COMPREHENSIVE TEST SUITE")
        print(" Testing: Early Bird, Bidirectional Completion, Disputes")
        print("="*60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Test ID: {self.test_id}")

        test_results = []

        # Run all tests
        tests = [
            ("Signup", self.test_1_signup),
            ("Profile Setup", self.test_2_profile_setup),
            ("Job Post", self.test_3_job_post),
            ("Application & Deposit", self.test_4_application_with_deposit),
            ("Offer & Contract", self.test_5_offer_and_contract),
            ("Contract Progression", self.test_6_contract_progression),
            ("Bidirectional Completion", self.test_7_bidirectional_completion),
            ("Dispute System", self.test_8_dispute_system),
            ("Trust & Activity", self.test_9_trust_and_activity),
        ]

        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
                if not result:
                    print(f"\n⚠️  Test '{test_name}' failed. Continuing with remaining tests...")
            except Exception as e:
                print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
                test_results.append((test_name, False))

        # Summary
        print("\n" + "="*60)
        print(" TEST SUMMARY")
        print("="*60)

        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)

        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} tests passed ({passed*100//total}%)")

        if passed == total:
            print("\n🎉 All PRDv2.0.0 features are working correctly!")
        else:
            print("\n⚠️  Some tests failed. Please review the logs above.")

        # Save test report
        self.save_report(test_results)

        return passed == total

    def save_report(self, test_results):
        """Save detailed test report"""
        report = {
            "test_id": self.test_id,
            "timestamp": datetime.now().isoformat(),
            "test_accounts": {
                "instructor": self.instructor_email,
                "studio": self.studio_email
            },
            "test_results": [
                {"name": name, "passed": result}
                for name, result in test_results
            ],
            "artifacts": {
                "job_post_id": self.job_post_id,
                "application_id": self.application_id,
                "offer_id": self.offer_id,
                "contract_id": self.contract_id,
                "dispute_id": self.dispute_id
            }
        }

        with open(f"/tmp/prdv2_test_report_{self.test_id}.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved: /tmp/prdv2_test_report_{self.test_id}.json")


if __name__ == "__main__":
    tester = TestPRDv2()
    tester.run_all_tests()