"""
Streamlit-specific Playwright helpers for E2E tests.

Handles the quirks of testing Streamlit apps:
- Tab panels: All panels exist in DOM simultaneously, need scoping via aria-controls
- Radio buttons: Hidden <input>, must click <label>
- Form submissions: Trigger Streamlit rerun, need wait after submit
- Navigation: Step buttons rendered as st.button in columns
"""

from playwright.sync_api import Page, Locator, expect


# Default timeouts
RERUN_WAIT_MS = 3000
ELEMENT_TIMEOUT_MS = 10000


def wait_for_streamlit_rerun(page: Page, ms: int = RERUN_WAIT_MS) -> None:
    """Wait for Streamlit to complete a rerun after an action."""
    page.wait_for_timeout(ms)


def navigate_to_tab(page: Page, tab_name: str) -> Locator:
    """Click a Streamlit tab and return the associated panel locator.

    Streamlit renders all tab panels in the DOM simultaneously.
    We use aria-controls to scope to the active panel.
    """
    tab = page.get_by_role("tab", name=tab_name)
    tab.click()
    page.wait_for_timeout(1000)

    panel_id = tab.get_attribute("aria-controls")
    if panel_id:
        return page.locator(f"#{panel_id}")
    # Fallback: get the visible tabpanel
    return page.get_by_role("tabpanel").locator("visible=true").first


def login_via_ui(
    page: Page, base_url: str, email: str, password: str
) -> None:
    """Log in through the Streamlit UI."""
    page.goto(base_url)
    page.wait_for_timeout(2000)

    panel = navigate_to_tab(page, "로그인")

    panel.get_by_label("이메일").fill(email)
    panel.get_by_label("비밀번호").fill(password)
    panel.get_by_role("button", name="로그인").click()

    # Wait for login to complete and main app to render
    expect(page.locator("text=StudioBridge")).to_be_visible(
        timeout=ELEMENT_TIMEOUT_MS
    )
    wait_for_streamlit_rerun(page)


def logout_via_ui(page: Page) -> None:
    """Log out through the Streamlit UI."""
    page.get_by_role("button", name="로그아웃").click()
    # Wait for redirect back to auth page
    expect(page.get_by_role("tab", name="로그인")).to_be_visible(
        timeout=ELEMENT_TIMEOUT_MS
    )
    wait_for_streamlit_rerun(page)


def navigate_to_step(page: Page, step_label: str) -> None:
    """Click a step navigation button (e.g., '일 찾기', '공고 등록').

    Step navigation buttons are rendered in columns. Some may be disabled
    (locked or current page). We click only enabled ones.
    """
    btn = page.get_by_role("button", name=step_label)
    # If button exists and is enabled, click it
    if btn.count() > 0:
        first_btn = btn.first
        if first_btn.is_enabled():
            first_btn.click()
            wait_for_streamlit_rerun(page)


def fill_instructor_profile(page: Page) -> None:
    """Fill in the instructor profile form on step 1.

    Expects to be on the profile page already.
    """
    page.get_by_label("활동명 *").fill("E2E테스트강사")
    page.get_by_label("자기소개").fill("E2E 테스트용 강사입니다.")
    page.get_by_label("경력 (년)").fill("3")
    page.get_by_label("활동 가능 지역 *").fill("강남, 서초")
    page.get_by_label("최소 희망시급").fill("40000")
    page.get_by_label("최대 희망시급").fill("60000")

    page.get_by_role("button", name="저장").click()
    wait_for_streamlit_rerun(page)


def fill_studio_profile(page: Page) -> None:
    """Fill in the studio profile form on step 1.

    Expects to be on the profile page already.
    """
    page.get_by_label("스튜디오명 *").fill("E2E테스트스튜디오")
    page.get_by_label("소개").fill("E2E 테스트용 스튜디오입니다.")
    page.get_by_label("지역 *").fill("강남")
    page.get_by_label("주소").fill("강남구 테헤란로 123")

    page.get_by_role("button", name="저장").click()
    wait_for_streamlit_rerun(page)


def create_job_via_ui(page: Page) -> None:
    """Create a job post through the UI on step 2 (studio).

    Expects to be on the '공고 등록' page already.
    Clicks category, type, region, rate buttons and fills date/time.
    """
    # Category: 필라테스
    page.get_by_role("button", name="필라테스").click()
    page.wait_for_timeout(500)

    # Job type: 대타 (1회)
    page.get_by_role("button", name="대타 (1회)").click()
    page.wait_for_timeout(500)

    # Rate: 5만
    page.get_by_role("button", name="5만").click()
    page.wait_for_timeout(500)

    # Register
    page.get_by_role("button", name="공고 등록하기").click()
    wait_for_streamlit_rerun(page, 5000)
