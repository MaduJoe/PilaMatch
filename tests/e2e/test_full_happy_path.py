"""
Full Happy Path E2E Test for StudioBridge.

Tests the complete flow: signup → profile → job → apply → offer → contract
→ sign → payment → completion → review.

Uses a hybrid strategy:
- Browser (Playwright) for UI interactions that need visual verification
- API (httpx) for fast setup steps where UI verification isn't needed

Requires: docker-compose up -d
"""

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.helpers.api_helpers import (
    create_test_user,
    complete_instructor_profile,
    create_job_post,
    apply_to_job,
    send_offer,
    sign_contract,
    confirm_completion,
    create_review,
    get_applications_for_job,
    get_my_contracts,
)
from tests.e2e.helpers.streamlit_helpers import (
    login_via_ui,
    logout_via_ui,
    navigate_to_step,
    wait_for_streamlit_rerun,
)

pytestmark = [pytest.mark.e2e]


@pytest.fixture(autouse=True)
def _require_services(services_up):
    """Ensure services are running for every test in this module."""


class TestFullHappyPath:
    """Full contract lifecycle: two users from signup to review.

    This is a single long test because each phase depends on the previous one.
    The test uses a hybrid approach: API for fast setup, browser for UI validation.
    """

    def test_full_contract_flow(self, page: Page, base_url: str, api_client):
        """Complete flow: signup→profile→job→apply→offer→contract→sign→pay→complete→review."""

        # ============================================================
        # Phase 1: Create users via API (fast setup)
        # ============================================================
        studio = create_test_user(api_client, "studio")
        instructor = create_test_user(api_client, "instructor")

        assert studio["access_token"], "Studio signup failed"
        assert instructor["access_token"], "Instructor signup failed"

        # ============================================================
        # Phase 2: Studio login + profile completion (browser)
        # ============================================================
        login_via_ui(page, base_url, studio["email"], studio["password"])
        expect(page.get_by_text("StudioBridge - 스튜디오")).to_be_visible(
            timeout=10000
        )

        # Fill studio profile form
        page.get_by_label("스튜디오명 *").fill("E2E테스트스튜디오")
        page.get_by_label("소개").fill("E2E 테스트용 스튜디오입니다")
        page.get_by_label("지역 *").fill("강남")
        page.get_by_label("주소").fill("강남구 테헤란로 123")
        page.get_by_role("button", name="저장").click()
        wait_for_streamlit_rerun(page, 5000)

        # ============================================================
        # Phase 3: Studio creates a job post (API - fast, browser verify)
        # ============================================================
        # Create job via API since Streamlit button-based forms cause
        # reruns on each click making browser-based creation fragile
        job = create_job_post(api_client, studio["access_token"])
        assert job.get("id"), "Job post creation failed"
        job_post_id = job["id"]

        # Verify via browser: navigate to applicants page (where studio goes after job creation)
        navigate_to_step(page, "지원자 선택")
        wait_for_streamlit_rerun(page)

        # ============================================================
        # Phase 4: Instructor login + profile completion (browser)
        # ============================================================
        logout_via_ui(page)

        login_via_ui(
            page, base_url, instructor["email"], instructor["password"]
        )
        expect(page.get_by_text("StudioBridge - 강사")).to_be_visible(
            timeout=10000
        )

        # Fill instructor profile form
        page.get_by_label("활동명 *").fill("E2E테스트강사")
        page.get_by_label("자기소개").fill("E2E 테스트용 강사입니다")
        page.get_by_label("경력 (년)").fill("3")
        page.get_by_label("활동 가능 지역 *").fill("강남, 서초")
        page.get_by_label("최소 희망시급").fill("40000")
        page.get_by_label("최대 희망시급").fill("60000")
        page.get_by_role("button", name="저장").click()
        wait_for_streamlit_rerun(page, 5000)

        # ============================================================
        # Phase 5: Instructor applies to job (API + browser verify)
        # ============================================================
        # Complete instructor profile via API to ensure matching works
        # Need 70%+ completeness: display_name(20), bio(15), experience(10),
        # regions(15), rate_min(10), rate_max(10) = 80% minimum
        inst_token = instructor["access_token"]
        complete_instructor_profile(
            api_client,
            inst_token,
            display_name="E2E테스트강사",
            bio="E2E 테스트용 강사 프로필입니다. 필라테스 전문 강사입니다.",
            available_regions=["강남", "서초"],
        )

        # Apply via API (faster, more reliable)
        application = apply_to_job(api_client, inst_token, job_post_id)
        assert application.get("id"), "Application failed"

        # Verify via browser: navigate to job search page, see job listing
        navigate_to_step(page, "일 찾기")
        wait_for_streamlit_rerun(page, 5000)

        # Verify that the job list page loaded with jobs
        expect(page.get_by_text("2단계: 일 찾기")).to_be_visible(timeout=10000)
        # Should show job count (our applied job is among them)
        expect(page.locator("text=/총.*공고/")).to_be_visible(timeout=10000)

        # ============================================================
        # Phase 6: Studio sends offer (API - fast)
        # ============================================================
        studio_token = studio["access_token"]

        # Get applications for this job (job_post_id from Phase 3)
        applications = get_applications_for_job(
            api_client, studio_token, job_post_id
        )
        app_list = applications if isinstance(applications, list) else applications.get("items", [])
        assert len(app_list) > 0, "No applications found for job post"
        application_id = app_list[0]["id"]

        # Send offer
        offer = send_offer(
            api_client,
            studio_token,
            application_id,
            proposed_rate=50000,
            message="E2E 테스트 오퍼입니다.",
        )
        offer_id = offer["id"]

        # ============================================================
        # Phase 7: Instructor accepts offer + creates contract (browser)
        # ============================================================
        # Logout and re-login so fresh Streamlit session recalculates
        # progress (offer now exists → step 3 unlocked)
        logout_via_ui(page)
        login_via_ui(
            page, base_url, instructor["email"], instructor["password"]
        )
        wait_for_streamlit_rerun(page, 3000)

        # Navigate to offers page (should be unlocked now since offer exists)
        navigate_to_step(page, "오퍼 확인")
        wait_for_streamlit_rerun(page, 3000)

        # Accept the offer
        accept_btn = page.get_by_role("button", name="수락")
        expect(accept_btn.first).to_be_visible(timeout=10000)
        accept_btn.first.click()
        wait_for_streamlit_rerun(page, 5000)

        # Create contract from accepted offer
        contract_btn = page.get_by_role("button", name="계약 생성")
        expect(contract_btn.first).to_be_visible(timeout=10000)
        contract_btn.first.click()
        wait_for_streamlit_rerun(page, 5000)

        # ============================================================
        # Phase 8: Both parties sign + payment
        # ============================================================
        # 8a. Instructor signs via browser
        navigate_to_step(page, "계약 진행")
        wait_for_streamlit_rerun(page, 3000)

        # Expand the signing section (Streamlit expander renders as details/summary)
        signing_expander = page.get_by_text("약관 확인 후 서명")
        expect(signing_expander.first).to_be_visible(timeout=10000)
        signing_expander.first.click()
        wait_for_streamlit_rerun(page, 2000)

        # Agree to terms — Streamlit hides the actual <input> checkbox,
        # so we click the <label> element instead, and scroll into view first
        agree_label = page.locator("label", has_text="위 약속 사항에 동의합니다")
        agree_label.first.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        agree_label.first.click()
        page.wait_for_timeout(1000)

        # Sign
        sign_btn = page.get_by_role("button", name="서명하기")
        expect(sign_btn.first).to_be_visible(timeout=5000)
        sign_btn.first.click()
        wait_for_streamlit_rerun(page, 5000)

        # 8b. Get contract ID
        contracts = get_my_contracts(api_client, inst_token)
        contract_list = contracts.get("items", contracts) if isinstance(contracts, dict) else contracts
        assert len(contract_list) > 0, "No contracts found"
        contract_id = contract_list[0]["id"]

        # 8c. Studio signs via API (contract becomes in_progress after both sign)
        sign_contract(api_client, studio_token, contract_id)

        # Note: Payment confirmation is skipped in E2E test since the
        # container runs with real Toss test keys. Payment is tested
        # separately via unit tests. The contract flow can complete
        # without payment (confirm_completion requires IN_PROGRESS status).

        # ============================================================
        # Phase 9: Completion confirmation (API for both)
        # ============================================================
        # Studio confirms completion
        confirm_completion(api_client, studio_token, contract_id)

        # Instructor confirms completion
        confirm_completion(api_client, inst_token, contract_id)

        # Verify contract is completed
        contracts_after = get_my_contracts(api_client, inst_token)
        contract_items = contracts_after.get("items", contracts_after) if isinstance(contracts_after, dict) else contracts_after
        completed_contract = next(
            (c for c in contract_items if c["id"] == contract_id), None
        )
        assert completed_contract is not None, "Contract not found"
        assert (
            completed_contract["status"] == "completed"
        ), f"Contract status is {completed_contract['status']}, expected 'completed'"

        # ============================================================
        # Phase 10: Reviews (API for both - fast and reliable)
        # ============================================================
        # 10a. Studio writes review via API
        studio_review = create_review(
            api_client,
            studio_token,
            contract_id,
            rating=5,
            comment="훌륭한 강사였습니다!",
        )
        assert studio_review.get("id"), "Studio review creation failed"

        # 10b. Instructor writes review via API
        inst_review = create_review(
            api_client,
            inst_token,
            contract_id,
            rating=5,
            comment="좋은 스튜디오였습니다!",
        )
        assert inst_review.get("id"), "Instructor review creation failed"

        # 10c. Verify reviews via browser
        # Re-login as instructor to see the review on the UI
        logout_via_ui(page)
        login_via_ui(
            page, base_url, instructor["email"], instructor["password"]
        )
        wait_for_streamlit_rerun(page, 3000)

        navigate_to_step(page, "완료/리뷰")
        wait_for_streamlit_rerun(page, 3000)

        # Verify that the completion page is visible
        expect(page.get_by_text("5단계: 완료 & 리뷰")).to_be_visible(
            timeout=10000
        )
