"""
StudioBridge - Pilates & Yoga Instructor Matching Platform
Main application entry point
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import utilities
from utils import (
    init_session_state,
    get_client,
    get_user_progress,
    logout,
    INSTRUCTOR_STEPS,
    STUDIO_STEPS
)

# Import components
from components import render_progress_bar, render_step_navigation

# Import page modules
from pages import (
    render_auth_page,
    render_profile_step,
    render_find_jobs_step,
    render_create_job_step,
    render_offers_step,
    render_applicants_step,
    render_contracts_step,
    render_complete_step
)

# Page configuration
st.set_page_config(
    page_title="StudioBridge",
    page_icon="🧘",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Mobile-responsive CSS
st.markdown("""
<style>
/* Responsive column stacking on narrow screens */
@media (max-width: 640px) {
    /* Stack Streamlit columns vertically */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    /* Reduce padding for mobile */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* Smaller headers on mobile */
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.1rem !important; }
    /* Make buttons more tappable */
    .stButton > button {
        min-height: 44px;
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()


def render_header():
    """Render the application header with user info and logout"""
    user = st.session_state.user

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        role_text = "강사" if user["role"] == "instructor" else "스튜디오"
        st.title(f"StudioBridge - {role_text}")
    with col2:
        # Display user info and logout button vertically
        user_email = user.get("email", "")
        user_name = user.get("display_name") if user["role"] == "instructor" else user.get("business_name")

        # Show email
        st.markdown(f"**{user_email}**")

        # Show name or profile prompt
        if user_name:
            st.caption(user_name)
        else:
            st.caption("프로필을 완성해주세요")

        # Logout button
        if st.button("로그아웃", use_container_width=True):
            logout()
            st.rerun()


def render_main_app():
    """Render the main application after login"""
    client = get_client()
    user = st.session_state.user

    # Render header
    render_header()

    # Get current progress
    current_step, data = get_user_progress(client)
    steps = INSTRUCTOR_STEPS if user["role"] == "instructor" else STUDIO_STEPS

    # Show progress bar
    render_progress_bar(current_step, steps)

    # Show navigation
    render_step_navigation(current_step, steps)

    st.markdown("---")

    # Show current task helper message
    if current_step == 1 and not data.get("profile_complete", False):
        st.info(f"환영합니다! 먼저 프로필을 완성해주세요. {'강사' if user['role'] == 'instructor' else '스튜디오'} 정보를 입력하면 매칭을 시작할 수 있습니다.")
    elif current_step == 2:
        if user["role"] == "instructor":
            st.info("이제 일자리를 찾아볼 수 있습니다! 매칭 점수가 높은 공고부터 확인해보세요.")
        else:
            st.info("첫 공고를 등록해보세요! 3클릭만으로 강사 모집이 가능합니다.")
    elif current_step == 3:
        if user["role"] == "instructor":
            st.info("받은 오퍼를 확인하고 수락/거절을 선택해주세요.")
        else:
            st.info("지원한 강사들을 검토하고 오퍼를 보내주세요.")
    elif current_step == 4:
        st.info("계약 내용을 확인하고 서명해주세요. 양측이 모두 서명하면 계약이 시작됩니다.")
    elif current_step == 5:
        st.info("수업이 완료되면 양측이 모두 확인해야 정산이 진행됩니다.")

    st.markdown("---")

    # Render current page
    render_current_page()


def render_current_page():
    """Render the current page based on navigation state"""
    page = st.session_state.get("page", "profile")
    user = st.session_state.user

    # Step 1: Profile
    if page == "profile":
        render_profile_step()

    # Step 2: Jobs
    elif page == "find_jobs":
        if user["role"] == "instructor":
            render_find_jobs_step()
        else:
            st.warning("스튜디오는 공고를 등록할 수 있습니다.")
            if st.button("공고 등록하기"):
                st.session_state.page = "create_job"
                st.rerun()

    elif page == "create_job":
        if user["role"] == "studio":
            render_create_job_step()
        else:
            st.warning("강사는 일자리를 찾을 수 있습니다.")
            if st.button("일자리 찾기"):
                st.session_state.page = "find_jobs"
                st.rerun()

    # Step 3: Offers/Applications
    elif page == "offers":
        if user["role"] == "instructor":
            render_offers_step()
        else:
            st.warning("스튜디오는 지원자를 검토할 수 있습니다.")
            if st.button("지원자 보기"):
                st.session_state.page = "applicants"
                st.rerun()

    elif page == "applicants":
        if user["role"] == "studio":
            render_applicants_step()
        else:
            st.warning("강사는 오퍼를 확인할 수 있습니다.")
            if st.button("오퍼 확인하기"):
                st.session_state.page = "offers"
                st.rerun()

    # Step 4: Contracts
    elif page == "contracts":
        render_contracts_step()

    # Step 5: Complete/Review
    elif page == "complete":
        render_complete_step()

    else:
        st.error(f"Unknown page: {page}")


def main():
    """Main application entry point"""
    # Check authentication
    if not st.session_state.token or not st.session_state.user:
        render_auth_page()
    else:
        render_main_app()


if __name__ == "__main__":
    main()