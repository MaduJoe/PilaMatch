"""
Authentication page - Login and Signup
"""

import streamlit as st
from api_client import APIClient, APIError
from utils.helpers import get_client

def render_auth_page():
    """Render login and signup forms"""
    st.title("StudioBridge") 
    st.subheader("웰니스 강사 채용·계약 플랫폼")
    st.caption("'작지만 믿을 수 있는 플랫폼'")

    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        render_login_form()

    with tab2:
        render_signup_form()


def render_login_form():
    """Render login form"""
    with st.form("login_form"):
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 입력하세요")
            else:
                try:
                    client = APIClient()
                    result = client.login(email, password)
                    st.session_state.token = result["access_token"]

                    client = get_client()
                    me = client.get_me()
                    st.session_state.user = me["user"]
                    st.session_state.profile_id = me.get("profile_id")

                    st.success("로그인 성공!")
                    st.rerun()
                except APIError as e:
                    st.error(f"로그인 실패: {e.message}")


def render_signup_form():
    """Render signup form"""
    # Radio button outside the form for dynamic UI update
    role = st.radio(
        "회원 유형을 선택하세요",
        ["instructor", "studio"],
        format_func=lambda x: "강사" if x == "instructor" else "스튜디오",
        horizontal=True,
        key="signup_role_select"
    )

    with st.form("signup_form"):
        email = st.text_input("이메일", key="signup_email")
        password = st.text_input("비밀번호 (8자 이상)", type="password", key="signup_password")

        # Show only the relevant input field based on role selection
        display_name = None
        business_name = None

        if role == "instructor":
            display_name = st.text_input("활동명", placeholder="강사님의 활동명을 입력하세요", key="signup_display_name")
        else:
            business_name = st.text_input("스튜디오명", placeholder="스튜디오 이름을 입력하세요", key="signup_business_name")

        submitted = st.form_submit_button("가입하기", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("이메일과 비밀번호를 입력하세요")
            elif len(password) < 8:
                st.error("비밀번호는 8자 이상이어야 합니다")
            elif role == "instructor" and not display_name:
                st.error("활동명을 입력하세요")
            elif role == "studio" and not business_name:
                st.error("스튜디오명을 입력하세요")
            else:
                try:
                    client = APIClient()
                    result = client.signup(email, password, role, display_name, business_name)
                    st.session_state.token = result["access_token"]

                    client = get_client()
                    me = client.get_me()
                    st.session_state.user = me["user"]
                    st.session_state.profile_id = me.get("profile_id")

                    st.success("가입 완료! 프로필을 완성해주세요.")
                    st.rerun()
                except APIError as e:
                    st.error(f"가입 실패: {e.message}")