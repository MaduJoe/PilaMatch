"""
E2E tests for authentication flow (signup + login).

Tests interact with the Streamlit frontend via Playwright.
Requires: docker-compose up -d

Note on Streamlit tabs:
  Streamlit renders ALL tab panels in the DOM simultaneously (hidden via CSS).
  So `get_by_label("이메일")` matches elements in BOTH the login and signup tabs.
  We must scope selectors to the active tabpanel using `get_by_role("tabpanel")`.
  When a tab is clicked, only one tabpanel is visible at a time.
"""

import pytest
from playwright.sync_api import Page, Locator, expect

pytestmark = [pytest.mark.e2e]


@pytest.fixture(autouse=True)
def _require_services(services_up):
    """Ensure services are running for every test in this module."""


def _get_active_tabpanel(page: Page) -> Locator:
    """Return the currently visible Streamlit tabpanel."""
    # Streamlit marks inactive tabpanels with aria-hidden or display:none.
    # The visible one has `[aria-hidden="false"]` or simply no aria-hidden attribute.
    # We use :visible pseudo-selector to reliably get the active panel.
    panels = page.get_by_role("tabpanel")
    # Filter to the visible one
    return panels.locator("visible=true").first


def _navigate_to_signup(page: Page, base_url: str) -> Locator:
    """Navigate to the signup tab and return its panel locator."""
    page.goto(base_url)
    tab = page.get_by_role("tab", name="회원가입")
    tab.click()
    # Wait for Streamlit to re-render after tab switch
    page.wait_for_timeout(1000)
    # Get the tabpanel controlled by the selected tab via aria-controls
    panel_id = tab.get_attribute("aria-controls")
    if panel_id:
        return page.locator(f"#{panel_id}")
    # Fallback: second tabpanel
    return page.get_by_role("tabpanel").nth(1)


def _navigate_to_login(page: Page, base_url: str) -> Locator:
    """Navigate to the login tab and return its panel locator."""
    page.goto(base_url)
    tab = page.get_by_role("tab", name="로그인")
    tab.click()
    page.wait_for_timeout(1000)
    # Get the tabpanel controlled by the selected tab via aria-controls
    panel_id = tab.get_attribute("aria-controls")
    if panel_id:
        return page.locator(f"#{panel_id}")
    # Fallback: first tabpanel
    return page.get_by_role("tabpanel").nth(0)


class TestInstructorSignup:
    def test_instructor_signup(
        self, page: Page, base_url: str, instructor_credentials: dict
    ):
        """Instructor can sign up with valid credentials."""
        panel = _navigate_to_signup(page, base_url)

        # Select instructor role via radio label
        # Streamlit hides the actual <input> radio; the clickable element is the <label>
        panel.locator("label", has_text="강사").click()

        # Fill signup form - scoped to the signup tabpanel
        panel.get_by_label("이메일").fill(instructor_credentials["email"])
        panel.get_by_label("비밀번호 (8자 이상)").fill(
            instructor_credentials["password"]
        )
        panel.get_by_label("활동명").fill(instructor_credentials["display_name"])

        # Submit
        panel.get_by_role("button", name="가입하기").click()

        # Verify redirect to main app (header shows role)
        expect(page.get_by_text("StudioBridge - 강사")).to_be_visible(timeout=10000)


class TestStudioSignup:
    def test_studio_signup(
        self, page: Page, base_url: str, studio_credentials: dict
    ):
        """Studio can sign up with valid credentials."""
        panel = _navigate_to_signup(page, base_url)

        # Select studio role via radio label
        panel.locator("label", has_text="스튜디오").click()

        # Fill signup form - scoped to the signup tabpanel
        panel.get_by_label("이메일").fill(studio_credentials["email"])
        panel.get_by_label("비밀번호 (8자 이상)").fill(
            studio_credentials["password"]
        )
        panel.get_by_label("스튜디오명").fill(studio_credentials["business_name"])

        # Submit
        panel.get_by_role("button", name="가입하기").click()

        # Verify redirect to main app (header shows role)
        expect(page.get_by_text("StudioBridge - 스튜디오")).to_be_visible(
            timeout=10000
        )


class TestLogin:
    def test_login_success(
        self, page: Page, base_url: str, api_client, instructor_credentials: dict
    ):
        """User can log in with correct credentials after signup via API."""
        # Create user via API first
        api_client.post(
            "/auth/signup",
            json={
                "email": instructor_credentials["email"],
                "password": instructor_credentials["password"],
                "role": instructor_credentials["role"],
                "display_name": instructor_credentials["display_name"],
            },
        )

        # Login via UI - scoped to the login tabpanel
        panel = _navigate_to_login(page, base_url)

        panel.get_by_label("이메일").fill(instructor_credentials["email"])
        panel.get_by_label("비밀번호").fill(instructor_credentials["password"])
        panel.get_by_role("button", name="로그인").click()

        # Verify redirect to main app
        expect(page.get_by_text("StudioBridge - 강사")).to_be_visible(timeout=10000)

    def test_login_wrong_password(
        self, page: Page, base_url: str, api_client, instructor_credentials: dict
    ):
        """Login fails with wrong password and shows error message."""
        # Create user via API first
        api_client.post(
            "/auth/signup",
            json={
                "email": instructor_credentials["email"],
                "password": instructor_credentials["password"],
                "role": instructor_credentials["role"],
                "display_name": instructor_credentials["display_name"],
            },
        )

        # Try login with wrong password - scoped to the login tabpanel
        panel = _navigate_to_login(page, base_url)

        panel.get_by_label("이메일").fill(instructor_credentials["email"])
        panel.get_by_label("비밀번호").fill("wrongpassword123")
        panel.get_by_role("button", name="로그인").click()

        # Verify error message
        expect(page.get_by_text("로그인 실패")).to_be_visible(timeout=10000)
