import streamlit as st
import streamlit.components.v1 as components
import os
import time
from dotenv import load_dotenv

load_dotenv()

from api_client import APIClient, APIError

# Kakao Map Key
KAKAO_MAP_KEY = os.getenv("KAKAO_MAP_KEY", "")

# Page configuration
st.set_page_config(
    page_title="StudioBridge",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Session state initialization
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "profile_id" not in st.session_state:
    st.session_state.profile_id = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 1


def get_client():
    return APIClient(st.session_state.token)


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.profile_id = None
    st.session_state.current_step = 1


# ============================================================
# PROGRESS TRACKER
# ============================================================

INSTRUCTOR_STEPS = [
    ("1", "프로필 완성", "profile"),
    ("2", "일 찾기", "find_jobs"),
    ("3", "오퍼 확인", "offers"),
    ("4", "계약 진행", "contracts"),
    ("5", "완료/리뷰", "complete"),
]

STUDIO_STEPS = [
    ("1", "프로필 완성", "profile"),
    ("2", "공고 등록", "create_job"),
    ("3", "지원자 선택", "applicants"),
    ("4", "계약 진행", "contracts"),
    ("5", "완료/리뷰", "complete"),
]

# 서울 지역 목록 + 좌표
SEOUL_REGIONS = {
    "강남": (37.5172, 127.0473),
    "서초": (37.4837, 127.0324),
    "송파": (37.5145, 127.1050),
    "강동": (37.5301, 127.1238),
    "마포": (37.5663, 126.9014),
    "용산": (37.5326, 126.9909),
    "성동": (37.5633, 127.0371),
    "광진": (37.5384, 127.0822),
    "동대문": (37.5744, 127.0396),
    "중랑": (37.6063, 127.0925),
    "성북": (37.5894, 127.0167),
    "강북": (37.6397, 127.0255),
    "도봉": (37.6688, 127.0471),
    "노원": (37.6542, 127.0568),
    "은평": (37.6027, 126.9291),
    "서대문": (37.5791, 126.9368),
    "종로": (37.5735, 126.9790),
    "중구": (37.5641, 126.9979),
    "영등포": (37.5264, 126.8963),
    "동작": (37.5124, 126.9393),
    "관악": (37.4784, 126.9516),
    "금천": (37.4519, 126.9020),
    "구로": (37.4955, 126.8876),
    "양천": (37.5169, 126.8664),
    "강서": (37.5509, 126.8495),
}

RATE_PRESETS = [
    (30000, "3만"),
    (40000, "4만"),
    (50000, "5만"),
    (60000, "6만"),
    (70000, "7만+"),
]


def render_kakao_map(region: str, height: int = 300):
    """Render Kakao Map for a given region."""
    if not KAKAO_MAP_KEY:
        st.caption("🗺️ 지도를 표시하려면 KAKAO_MAP_KEY를 설정하세요.")
        return

    lat, lng = SEOUL_REGIONS.get(region, (37.5665, 126.9780))  # Default: Seoul City Hall

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_MAP_KEY}&libraries=services"></script>
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ width: 100%; height: {height}px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var container = document.getElementById('map');
            var options = {{
                center: new kakao.maps.LatLng({lat}, {lng}),
                level: 5
            }};
            var map = new kakao.maps.Map(container, options);

            // Add marker
            var marker = new kakao.maps.Marker({{
                position: new kakao.maps.LatLng({lat}, {lng})
            }});
            marker.setMap(map);

            // Add circle overlay for area
            var circle = new kakao.maps.Circle({{
                center: new kakao.maps.LatLng({lat}, {lng}),
                radius: 1500,
                strokeWeight: 2,
                strokeColor: '#FF6B6B',
                strokeOpacity: 0.8,
                fillColor: '#FF6B6B',
                fillOpacity: 0.2
            }});
            circle.setMap(map);
        </script>
    </body>
    </html>
    """
    components.html(html, height=height + 10)


def get_user_progress(client):
    """Calculate user's current progress step."""
    user = st.session_state.user
    if not user:
        return 1, {}

    data = {"profile_complete": False, "has_jobs": False, "has_offers": False,
            "has_contracts": False, "has_completed": False, "pending_offers": 0,
            "active_contracts": 0, "applications": [], "job_posts": []}

    try:
        # Check profile completeness
        if user["role"] == "instructor":
            profile = client.get_my_instructor_profile()
            # Ensure all required fields are properly filled
            data["profile_complete"] = bool(
                profile.get("display_name") and
                profile.get("available_regions") and
                len(profile.get("available_regions", [])) > 0
            )
        else:
            profile = client.get_my_studio_profile()
            # Check that region is not just an empty string or "None"
            region = profile.get("region", "")
            # Handle "None" string from API (when DB value is NULL)
            if region == "None" or region is None:
                region = ""
            data["profile_complete"] = bool(
                profile.get("business_name") and
                region and
                region.strip()  # Ensure region is not empty or whitespace
            )

        # Check verification & deposit
        identity_ok = user.get("identity_verified", False)
        if not identity_ok:
            data["profile_complete"] = False
    except Exception as e:
        # If API call fails, explicitly set profile as incomplete
        data["profile_complete"] = False
        # Optional: Log the error for debugging
        # st.error(f"Profile check failed: {str(e)}")

    try:
        if user["role"] == "instructor":
            # Check offers
            offers = client.get_my_offers().get("items", [])
            data["pending_offers"] = len([o for o in offers if o["status"] == "pending"])
            data["has_offers"] = len(offers) > 0
        else:
            # Check job posts
            jobs = client.list_job_posts({"studio_id": str(st.session_state.profile_id)}).get("items", [])
            data["job_posts"] = jobs
            data["has_jobs"] = len(jobs) > 0
    except Exception:
        # If API call fails, keep default False values
        data["has_offers"] = False
        data["has_jobs"] = False

    try:
        contracts = client.get_my_contracts().get("items", [])
        data["active_contracts"] = len([c for c in contracts if c["status"] in ["confirmed", "in_progress", "pending_completion"]])
        data["has_contracts"] = len(contracts) > 0
        # Consider both pending_completion (waiting for other party) and completed
        data["has_completed"] = any(c["status"] in ["completed", "pending_completion"] for c in contracts)
    except Exception:
        # If API call fails, keep default False values
        data["has_contracts"] = False
        data["has_completed"] = False
        data["active_contracts"] = 0

    # Determine current step
    if not data["profile_complete"]:
        return 1, data

    if user["role"] == "instructor":
        if data["has_completed"]:
            return 5, data
        if data["active_contracts"] > 0:
            return 4, data
        if data["has_offers"]:
            return 3, data
        return 2, data
    else:  # studio
        # Prioritize completed contracts (step 5)
        if data["has_completed"]:
            return 5, data
        # Then active contracts (step 4)
        if data["active_contracts"] > 0:
            return 4, data
        # Then applicants/jobs (step 3)
        if data["has_jobs"]:
            return 3, data
        # Otherwise profile/create job (step 2)
        return 2, data


def render_progress_bar(current_step, steps):
    """Render the progress tracker at the top."""
    cols = st.columns(len(steps))

    for i, (num, label, _) in enumerate(steps):
        step_num = int(num)
        with cols[i]:
            if step_num < current_step:
                # Completed
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                    <div style="font-size: 24px;">✓</div>
                    <div style="font-size: 12px; color: #155724;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            elif step_num == current_step:
                # Current
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #fff3cd; border-radius: 10px; border: 3px solid #ffc107;">
                    <div style="font-size: 24px; font-weight: bold;">📍 {num}</div>
                    <div style="font-size: 12px; font-weight: bold; color: #856404;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Future
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #e9ecef; border-radius: 10px; border: 2px solid #dee2e6;">
                    <div style="font-size: 24px; color: #6c757d;">{num}</div>
                    <div style="font-size: 12px; color: #6c757d;">{label}</div>
                </div>
                """, unsafe_allow_html=True)


def render_step_navigation(current_step, steps):
    """Render navigation buttons for each step."""
    st.markdown("---")
    cols = st.columns(len(steps))

    # Get current page
    current_page = st.session_state.get("page", steps[current_step - 1][2])

    for i, (num, label, page) in enumerate(steps):
        step_num = int(num)
        with cols[i]:
            # Can only access completed steps and the current step
            # Cannot skip ahead if current step is not complete
            disabled = step_num > current_step
            is_active = (page == current_page)  # Check if this is the current page

            # Use different button type for active page
            if is_active:
                # Show active state with primary button
                if st.button(f"📍 {label}", key=f"nav_{page}", disabled=disabled, use_container_width=True, type="primary"):
                    st.session_state.page = page
                    st.rerun()
            else:
                # Show normal button
                if st.button(f"{label}", key=f"nav_{page}", disabled=disabled, use_container_width=True):
                    st.session_state.page = page
                    st.rerun()


# ============================================================
# AUTH PAGES
# ============================================================

def render_auth_page():
    st.title("StudioBridge")
    st.subheader("🧘‍♀️ 요가·필라테스 강사 연결 플랫폼")
    st.caption("'작지만 믿을 수 있는 플랫폼'")

    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
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

    with tab2:
        # Radio button outside the form for dynamic UI update
        role = st.radio(
            "회원 유형을 선택하세요",
            ["instructor", "studio"],
            format_func=lambda x: "🧘 강사" if x == "instructor" else "🏢 스튜디오",
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


# ============================================================
# STEP 1: PROFILE (Both)
# ============================================================

def render_profile_step():
    st.header("1단계: 프로필 완성")
    st.info("서비스 이용을 위해 프로필을 완성하고 본인인증을 해주세요.")

    client = get_client()
    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("기본 정보")

        try:
            if user["role"] == "instructor":
                profile = client.get_my_instructor_profile()

                with st.form("instructor_profile_form"):
                    display_name = st.text_input("활동명 *", value=profile.get("display_name", ""))
                    bio = st.text_area("자기소개", value=profile.get("bio", "") or "")
                    experience_years = st.number_input("경력 (년)", value=profile.get("experience_years", 0), min_value=0)

                    regions = st.text_input(
                        "활동 가능 지역 * (쉼표로 구분)",
                        value=", ".join(profile.get("available_regions", [])),
                        placeholder="강남, 서초, 송파"
                    )

                    certs = st.text_area(
                        "자격증 (줄바꿈으로 구분)",
                        value="\n".join([c.get("name", c) if isinstance(c, dict) else c for c in profile.get("certifications", [])])
                    )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        rate_min = st.number_input("최소 희망시급", value=int(float(profile.get("hourly_rate_min", 0) or 0)), step=5000)
                    with col_b:
                        rate_max = st.number_input("최대 희망시급", value=int(float(profile.get("hourly_rate_max", 0) or 0)), step=5000)

                    submitted = st.form_submit_button("저장", use_container_width=True)

                if submitted:
                    with st.spinner("프로필을 저장하는 중..."):
                        try:
                            new_certs = [{"name": c.strip(), "is_verified": False} for c in certs.strip().split("\n") if c.strip()]
                            region_list = [r.strip() for r in regions.split(",") if r.strip()]

                            client.update_instructor_profile({
                                "display_name": display_name,
                                "bio": bio,
                                "experience_years": experience_years,
                                "available_regions": region_list,
                                "certifications": new_certs,
                                "hourly_rate_min": rate_min if rate_min > 0 else None,
                                "hourly_rate_max": rate_max if rate_max > 0 else None,
                            })
                            st.success("프로필이 성공적으로 저장되었습니다")
                            # Update user display name in session
                            if 'user' in st.session_state and st.session_state.user:
                                st.session_state.user['display_name'] = display_name
                            time.sleep(1)
                            # Auto-navigate to next step (find jobs)
                            st.session_state.page = "find_jobs"
                            st.rerun()
                        except APIError as e:
                            st.session_state["profile_save_error"] = e.message
                            st.rerun()

                if "profile_save_error" in st.session_state:
                    st.error(f"프로필 저장에 실패했습니다: {st.session_state.pop('profile_save_error')}")
            else:
                profile = client.get_my_studio_profile()

                with st.form("studio_profile_form"):
                    business_name = st.text_input("스튜디오명 *", value=profile.get("business_name", ""))
                    description = st.text_area("소개", value=profile.get("description", "") or "")
                    region = st.text_input("지역 *", value=profile.get("region", "") or "", placeholder="강남")
                    address = st.text_input("주소", value=profile.get("address", "") or "")

                    studio_submitted = st.form_submit_button("저장", use_container_width=True)

                if studio_submitted:
                    with st.spinner("프로필을 저장하는 중..."):
                        try:
                            client.update_studio_profile({
                                "business_name": business_name,
                                "description": description,
                                "region": region,
                                "address": address,
                            })
                            st.success("프로필이 성공적으로 저장되었습니다")
                            # Update studio business name in session
                            if 'user' in st.session_state and st.session_state.user:
                                st.session_state.user['business_name'] = business_name
                            time.sleep(1)
                            # Auto-navigate to next step (create job)
                            st.session_state.page = "create_job"
                            st.rerun()
                        except APIError as e:
                            st.session_state["profile_save_error"] = e.message
                            st.rerun()

                if "profile_save_error" in st.session_state:
                    st.error(f"프로필 저장에 실패했습니다: {st.session_state.pop('profile_save_error')}")
        except APIError as e:
            st.error(f"프로필 로드 실패: {e.message}")

    with col2:
        st.subheader("본인인증")

        # Phone verification
        if user.get("identity_verified"):
            st.success("✓ 휴대폰 인증 완료")
        else:
            st.warning("휴대폰 인증 필요")
            with st.form("phone_form"):
                phone = st.text_input("휴대폰 번호", placeholder="01012345678")
                if st.form_submit_button("인증번호 발송"):
                    try:
                        result = client.request_phone_verification(phone)
                        st.session_state.verify_phone = phone
                        st.info(f"인증번호가 발송되었습니다. (개발모드: {result.get('_dev_otp', '')})")
                    except APIError as e:
                        st.error(f"오류: {e.message}")

            if "verify_phone" in st.session_state:
                with st.form("otp_form"):
                    otp = st.text_input("인증번호 6자리")
                    if st.form_submit_button("확인"):
                        try:
                            client.verify_phone(st.session_state.verify_phone, otp)
                            st.success("인증 완료!")
                            del st.session_state.verify_phone
                            # Refresh user data
                            me = client.get_me()
                            st.session_state.user = me["user"]
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")

        # Business verification (studio only)
        if user["role"] == "studio":
            st.markdown("---")
            if user.get("business_verified"):
                st.success("✓ 사업자 인증 완료")
            else:
                st.warning("사업자 인증 필요")
                with st.form("biz_form"):
                    biz_num = st.text_input("사업자등록번호", placeholder="000-00-00000")
                    if st.form_submit_button("인증"):
                        try:
                            client.verify_business(biz_num)
                            st.success("인증 완료!")
                            me = client.get_me()
                            st.session_state.user = me["user"]
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")

        # Premium Membership Status
        st.markdown("---")
        st.subheader("⭐ 멤버십 상태")

        try:
            subscription_status = client.get_subscription_status()
            membership_tier = subscription_status.get("membership_tier", "free")

            if membership_tier == "premium":
                # Premium user
                col_mem1, col_mem2 = st.columns(2)
                with col_mem1:
                    st.success("⭐ 프리미엄 회원")
                    st.caption("보증금 없이 모든 기능을 이용하실 수 있습니다")
                with col_mem2:
                    if subscription_status.get("subscription"):
                        sub = subscription_status["subscription"]
                        if sub.get("next_billing_date"):
                            next_date = sub["next_billing_date"][:10]
                            st.info(f"다음 결제일: {next_date}")
                        if st.button("구독 취소", type="secondary"):
                            try:
                                result = client.cancel_subscription("User requested")
                                st.success(f"구독이 취소되었습니다. 보증금 {result['deposit_refunded']:,.0f}원이 환불됩니다.")
                                st.rerun()
                            except APIError as e:
                                st.error(f"구독 취소 실패: {e.message}")
            else:
                # Free user - show upgrade option
                st.info("📌 무료 회원")
                col_up1, col_up2 = st.columns([2, 1])
                with col_up1:
                    st.markdown(
                        "**🎯 프리미엄 멤버십 혜택** (월 9,900원)\n"
                        "- ✅ **보증금 완전 면제** - 3-5만원 보증금 불필요\n"
                        "- ⭐ **우선 매칭** - 더 많은 기회\n"
                        "- 💎 **프리미엄 뱃지** - 신뢰도 상승\n"
                        "- 🚀 **24/7 우선 지원** - 빠른 문제 해결"
                    )
                with col_up2:
                    if st.button("⭐ 프리미엄 업그레이드", type="primary", use_container_width=True):
                        st.session_state.show_upgrade_modal = True

                # Upgrade modal
                if st.session_state.get("show_upgrade_modal"):
                    with st.container():
                        st.markdown("### 프리미엄 멤버십 결제")
                        st.info("월 9,900원으로 보증금 없이 모든 기능을 이용하세요!")

                        col_pay1, col_pay2 = st.columns(2)
                        with col_pay1:
                            if st.button("결제 진행", type="primary", use_container_width=True):
                                try:
                                    # Initialize payment
                                    result = client.initialize_premium_upgrade()
                                    st.session_state.premium_order_id = result["order_id"]
                                    st.session_state.premium_amount = result["amount"]
                                    st.success(f"주문번호: {result['order_id']}")
                                    st.info("토스페이먼츠 결제 페이지로 이동합니다...")
                                    # In production, redirect to TossPayments
                                    # For now, simulate payment completion
                                    time.sleep(1)
                                    # Simulate payment confirmation
                                    confirm_result = client.confirm_subscription_payment(
                                        "test_payment_key",
                                        result["order_id"]
                                    )
                                    st.success("🎉 프리미엄 회원이 되신 것을 축하합니다!")
                                    del st.session_state.show_upgrade_modal
                                    st.rerun()
                                except APIError as e:
                                    st.error(f"업그레이드 실패: {e.message}")
                        with col_pay2:
                            if st.button("취소", type="secondary", use_container_width=True):
                                del st.session_state.show_upgrade_modal
                                st.rerun()
        except APIError as e:
            st.warning("멤버십 정보를 불러올 수 없습니다")

        # Deposit (only for free users)
        st.markdown("---")
        st.subheader("💰 보증금")

        # Show message if navigated from job application
        if st.session_state.get("deposit_message"):
            st.warning(f"⚠️ {st.session_state.deposit_message}")
            # Clear the message after showing
            del st.session_state.deposit_message

        # Check if we should auto-expand the deposit section
        expand_deposit = st.session_state.get("show_deposit_section", False)

        with st.expander("보증금 관리", expanded=expand_deposit):
            try:
                deposit = client.get_deposit_status()
                membership_tier = deposit.get("membership_tier", "free")

                # Premium users don't need deposit
                if membership_tier == "premium":
                    st.success("⭐ 프리미엄 회원은 보증금이 면제됩니다!")
                    st.info("프리미엄 멤버십이 활성화되어 있어 보증금 없이 모든 기능을 이용하실 수 있습니다.")
                    if deposit.get("balance", 0) > 0:
                        st.warning(f"기존 보증금 잔액 ₩{deposit['balance']:,.0f}이 있습니다. 구독 취소 시 환불됩니다.")
                else:
                    # Free users need deposit
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("현재 잔액", f"₩{deposit['balance']:,.0f}")
                    with col2:
                        st.metric("필요 금액", f"₩{deposit['required']:,.0f}")

                    if deposit["is_sufficient"]:
                        st.success("✅ 보증금이 충분합니다. 지원하실 수 있어요!")
                    else:
                        st.warning(f"💸 보증금이 ₩{deposit['shortfall']:,.0f} 부족합니다")

                        # Check user role to show relevant benefits
                        user = st.session_state.user
                        if user.get("role") == "instructor":
                            st.info(
                                "**🛡️ 강사님을 위한 보증금 혜택**\n\n"
                                "**현재 제공:**\n"
                                "- ✅ **100% 수업료 보장** - 에스크로로 안전하게 보호\n"
                                "- ✅ **부당 신고 보호** - 24시간 이의신청 권리\n"
                                "- 💎 **프로필 인증 마크** - 신뢰도 상승\n"
                                "- ⭐ **우선 매칭** - 더 많은 기회\n\n"
                                "**곧 추가될 혜택:**\n"
                                "- 🔜 스튜디오 노쇼 시 보상\n"
                                "- 🔜 당일 취소 수수료 지급\n"
                                "- 🔜 우수 강사 즉시 정산\n\n"
                                "💡 보증금은 언제든 환불 가능합니다.\n\n"
                                "💰 **또는 프리미엄 멤버십으로 보증금 면제받기!**"
                            )
                        else:  # studio
                            st.info(
                                "**🏢 스튜디오를 위한 보증금 혜택**\n\n"
                                "- ✅ **강사 노쇼 보호** - 노쇼 시 전액 보상\n"
                                "- ✅ **신뢰있는 강사 매칭** - 검증된 강사만\n"
                                "- 💎 **프로필 인증 마크** - 강사들의 신뢰 획득\n"
                                "- ⭐ **우선 노출** - 더 많은 강사 지원\n\n"
                                "💡 보증금은 언제든 환불 가능합니다.\n\n"
                                "💰 **또는 프리미엄 멤버십으로 보증금 면제받기!**"
                            )

                        with st.form("deposit_form"):
                            st.write("**보증금 충전하기**")
                            amount = st.number_input(
                                "충전 금액",
                                value=int(float(deposit["shortfall"])),
                                min_value=10000,
                                step=10000,
                                help="최소 10,000원부터 충전 가능합니다"
                            )
                            if st.form_submit_button("💳 충전하기", type="primary", use_container_width=True):
                                try:
                                    result = client.add_deposit(amount)
                                    st.balloons()
                                    st.success(f"✨ 충전 완료! 잔액: ₩{result['new_balance']:,.0f}")
                                    st.info("이제 구인 공고에 지원하실 수 있어요! 🎉")
                                    # Clear the expand flag after successful charge
                                    if "show_deposit_section" in st.session_state:
                                        del st.session_state.show_deposit_section
                                    time.sleep(2)
                                    st.rerun()
                                except APIError as e:
                                    st.error(f"오류: {e.message}")
            except APIError:
                st.error("보증금 정보를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")

        # Reset the flag after the expander is rendered
        if expand_deposit and "show_deposit_section" in st.session_state:
            del st.session_state.show_deposit_section


# ============================================================
# STEP 2: FIND JOBS (Instructor)
# ============================================================

def render_find_jobs_step():
    st.header("2단계: 일 찾기")

    client = get_client()

    # Get list of already applied jobs
    applied_job_ids = set()
    try:
        my_applications = client.get_my_applications()
        applied_job_ids = {app.get("job_post_id") for app in my_applications.get("items", [])}
    except:
        pass  # If error, assume no applications

    # 필터 행 (컴팩트)
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 1])
    with filter_col1:
        category_filter = st.radio(
            "종목",
            ["전체", "필라테스", "요가"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with filter_col2:
        region_filter = st.selectbox(
            "지역",
            ["전체"] + list(SEOUL_REGIONS.keys()),
            label_visibility="collapsed",
        )
    with filter_col3:
        sort_by_score = st.checkbox("매칭순", value=True)

    params = {}
    if category_filter == "필라테스":
        params["category"] = "pilates"
    elif category_filter == "요가":
        params["category"] = "yoga"
    if region_filter != "전체":
        params["region"] = region_filter

    try:
        result = client.list_job_posts_with_matching(params)
        jobs = result.get("items", [])

        if sort_by_score:
            jobs = sorted(jobs, key=lambda x: x.get("matching", {}).get("total", 0), reverse=True)

        if not jobs:
            st.info("등록된 공고가 없습니다.")
            st.caption("스튜디오가 공고를 등록하면 여기에 표시됩니다.")
        else:
            applied_count = sum(1 for item in jobs if item.get("job", item)["id"] in applied_job_ids)
            st.caption(f"총 {len(jobs)}개 공고 | 지원 완료 {applied_count}건")

            # 3열 그리드로 카드 배치
            COLS = 3
            for row_start in range(0, len(jobs), COLS):
                row_items = jobs[row_start : row_start + COLS]
                cols = st.columns(COLS)

                for col_idx, item in enumerate(row_items):
                    job = item.get("job", item)
                    matching = item.get("matching", {})
                    score = matching.get("total", 0)
                    is_applied = job["id"] in applied_job_ids

                    with cols[col_idx]:
                        # --- 카드 스타일 컨테이너 ---
                        type_emoji = {
                            "substitute": "⚡",
                            "regular": "📅",
                            "contract": "📝",
                        }.get(job["job_type"], "📋")
                        type_label = {
                            "substitute": "대타",
                            "regular": "정규",
                            "contract": "계약",
                        }.get(job["job_type"], "")

                        # 매칭 점수 배지 색상
                        if score >= 80:
                            score_badge = f":green[**{score}%**]"
                        elif score >= 60:
                            score_badge = f":orange[**{score}%**]"
                        else:
                            score_badge = f":gray[{score}%]"

                        applied_mark = " :white_check_mark:" if is_applied else ""

                        st.markdown(
                            f"**{type_emoji} {type_label}{applied_mark}** &nbsp; {score_badge}"
                        )

                        # 핵심 정보 (2줄 컴팩트)
                        st.caption(
                            f"📍 {job.get('region', '-')} &nbsp;|&nbsp; "
                            f"📆 {job['date']}"
                        )
                        st.markdown(
                            f"**₩{int(float(job['hourly_rate'])):,}** / 시간"
                        )

                        # 메모 (있을 때만, 1줄 truncate)
                        if job.get("description"):
                            desc = job["description"]
                            st.caption(
                                desc[:40] + "..." if len(desc) > 40 else desc
                            )

                        # 상세 정보 expander
                        with st.expander("상세 보기"):
                            breakdown = matching.get("breakdown", {})
                            if breakdown:
                                st.caption(
                                    f"지역 {breakdown.get('region', 0)}점 | "
                                    f"경력 {breakdown.get('experience', 0)}점 | "
                                    f"자격 {breakdown.get('certifications', 0)}점 | "
                                    f"시급 {breakdown.get('hourly_rate', 0)}점"
                                )
                            st.caption(
                                f"시간: {job.get('start_time', '-')} ~ {job.get('end_time', '-')}"
                            )

                        # 버튼 (카드 하단 정렬)
                        if is_applied:
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                st.button(
                                    "지원완료",
                                    key=f"applied_{job['id']}",
                                    disabled=True,
                                    use_container_width=True,
                                )
                            with btn_col2:
                                if st.button(
                                    "내역 보기",
                                    key=f"view_{job['id']}",
                                    use_container_width=True,
                                ):
                                    st.session_state.page = "offers"
                                    st.rerun()
                        else:
                            if st.button(
                                "지원하기",
                                key=f"apply_{job['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    client.apply_to_job(job["id"])
                                    st.success("지원 완료! 스튜디오 응답을 기다려주세요.")
                                    time.sleep(1)
                                    st.rerun()
                                except APIError as e:
                                    if "ALREADY_APPLIED" in str(e.code):
                                        st.warning("이미 지원한 공고입니다.")
                                        st.rerun()
                                    elif "INSUFFICIENT_DEPOSIT" in str(e.code) or "Deposit required" in str(e.message):
                                        st.session_state.page = "profile"
                                        st.session_state.show_deposit_section = True
                                        st.session_state.deposit_message = "보증금이 부족합니다. 보증금을 충전해주세요."
                                        st.rerun()
                                    else:
                                        st.error(f"오류: {e.message}")

                        st.markdown("---")

    except APIError as e:
        st.error(f"공고 로드 실패: {e.message}")


# ============================================================
# STEP 2: CREATE JOB (Studio)
# ============================================================

def render_create_job_step():
    st.header("2단계: 공고 등록")
    st.caption("3클릭 + 1줄이면 끝!")

    client = get_client()

    # 변수 초기화
    category = st.session_state.get("job_category", "pilates")
    job_type = st.session_state.get("job_type", "substitute")
    if "job_region" not in st.session_state:
        st.session_state.job_region = "강남"

    # 2개 컬럼으로 나누기
    main_col1, main_col2 = st.columns(2)

    # 왼쪽 컬럼: 종목, 유형, 지역
    with main_col1:
        # 1. 종목 선택 (버튼)
        st.subheader("1️⃣ 종목")
        col1, col2 = st.columns(2)
        with col1:
            pilates_selected = st.button("🧘‍♀️ 필라테스", use_container_width=True,
                                          type="primary" if st.session_state.get("job_category") == "pilates" else "secondary")
            if pilates_selected:
                st.session_state.job_category = "pilates"
                st.rerun()
        with col2:
            yoga_selected = st.button("🧘 요가", use_container_width=True,
                                       type="primary" if st.session_state.get("job_category") == "yoga" else "secondary")
            if yoga_selected:
                st.session_state.job_category = "yoga"
                st.rerun()

        # 2. 유형 선택 (버튼)
        st.subheader("2️⃣ 유형")
        col1, col2, col3 = st.columns(3)
        with col1:
            sub_selected = st.button("⚡ 대타 (1회)", use_container_width=True,
                                      type="primary" if st.session_state.get("job_type") == "substitute" else "secondary")
            if sub_selected:
                st.session_state.job_type = "substitute"
                st.rerun()
        with col2:
            reg_selected = st.button("📅 정규 (주기적)", use_container_width=True,
                                      type="primary" if st.session_state.get("job_type") == "regular" else "secondary")
            if reg_selected:
                st.session_state.job_type = "regular"
                st.rerun()
        with col3:
            con_selected = st.button("📝 계약 (장기)", use_container_width=True,
                                      type="primary" if st.session_state.get("job_type") == "contract" else "secondary")
            if con_selected:
                st.session_state.job_type = "contract"
                st.rerun()

        # 3. 지역 선택 + 지도
        st.subheader("3️⃣ 지역")
        # 지역 선택 (드롭다운)
        regions = list(SEOUL_REGIONS.keys())
        st.session_state.job_region = st.selectbox(
            "서울 지역 선택",
            regions,
            index=regions.index(st.session_state.job_region) if st.session_state.job_region in regions else 0,
            label_visibility="collapsed"
        )
        render_kakao_map(st.session_state.job_region, height=200)

    # 오른쪽 컬럼: 시급, 언제, 한 줄 메모
    with main_col2:
        # 4. 시급 선택 (프리셋 버튼)
        st.subheader("4️⃣ 시급")
        rate_cols = st.columns(2)
        for i, (rate, label) in enumerate(RATE_PRESETS[:4]):  # 처음 4개만 표시 (2x2 그리드)
            with rate_cols[i % 2]:
                if st.button(label, key=f"rate_{rate}", use_container_width=True,
                            type="primary" if st.session_state.get("job_rate") == rate else "secondary"):
                    st.session_state.job_rate = rate
                    st.rerun()

        hourly_rate = st.session_state.get("job_rate", 50000)
        st.caption(f"선택: ₩{hourly_rate:,}/시간")

        # 5. 날짜/시간
        st.subheader("5️⃣ 언제")
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("날짜")
        with col2:
            start_time = st.time_input("시작", value=None)
        with col3:
            end_time = st.time_input("종료", value=None)

        # 6. 한 줄 메모 (선택)
        st.subheader("6️⃣ 한 줄 메모 (선택)")
        memo = st.text_input("", placeholder="예: 리포머 수업, 초급자 대상, 주차 가능", label_visibility="collapsed")

    st.markdown("---")

    # 자동 생성 제목 미리보기
    type_labels = {"substitute": "대타", "regular": "정규", "contract": "계약"}
    auto_title = f"[{type_labels[job_type]}] {st.session_state.job_region}구 {'필라테스' if category == 'pilates' else '요가'} 강사"
    if memo:
        auto_title += f" - {memo}"

    st.info(f"📋 **공고 제목:** {auto_title}")

    # 등록 버튼
    if st.button("🚀 공고 등록하기", type="primary", use_container_width=True):
        try:
            client.create_job_post({
                "title": auto_title,
                "category": category,
                "job_type": job_type,
                "date": str(date),
                "start_time": str(start_time) if start_time else "09:00:00",
                "end_time": str(end_time) if end_time else "10:00:00",
                "hourly_rate": hourly_rate,
                "description": memo,
                "region": st.session_state.job_region,
                "total_sessions": 1,
            })
            st.success("✅ 공고가 등록되었습니다!")
            # Reset form state
            for key in ["job_category", "job_type", "job_rate", "job_region"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "applicants"
            st.rerun()
        except APIError as e:
            st.error(f"오류: {e.message}")


# ============================================================
# STEP 3: OFFERS (Instructor)
# ============================================================

def render_offers_step():
    st.header("3단계: 오퍼 확인")

    client = get_client()

    try:
        result = client.get_my_offers()
        offers = result.get("items", [])

        # Get existing contracts to filter out offers that already have contracts
        contracts_result = client.get_my_contracts()
        existing_contract_offer_ids = {c.get("offer_id") for c in contracts_result.get("items", []) if c.get("offer_id")}

        # Filter out offers that already have contracts
        offers = [o for o in offers if o["id"] not in existing_contract_offer_ids]

        pending = [o for o in offers if o["status"] == "pending"]
        accepted = [o for o in offers if o["status"] == "accepted"]
        others = [o for o in offers if o["status"] not in ("pending", "accepted")]

        # --- 대기 중인 오퍼: 2열 카드 ---
        if pending:
            st.subheader(f"수락/거절 대기 중 ({len(pending)})")
            COLS = 2
            for row_start in range(0, len(pending), COLS):
                row_offers = pending[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, offer in enumerate(row_offers):
                    with cols[col_idx]:
                        # 카드 헤더
                        st.markdown(f"**제안 시급: ₩{int(float(offer['proposed_rate'])):,}**")
                        if offer.get("message"):
                            msg = offer["message"]
                            st.caption(msg[:60] + "..." if len(msg) > 60 else msg)

                        # 상세 메시지 expander
                        if offer.get("message") and len(offer["message"]) > 60:
                            with st.expander("전체 메시지 보기"):
                                st.write(offer["message"])

                        # 수락/거절 버튼 (카드 하단)
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button(
                                "수락",
                                key=f"accept_{offer['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    client.accept_offer(offer["id"])
                                    st.success("오퍼를 수락했습니다!")
                                    st.rerun()
                                except APIError as e:
                                    st.error(f"오류: {e.message}")
                        with btn_col2:
                            if st.button(
                                "거절",
                                key=f"reject_{offer['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    client.reject_offer(offer["id"])
                                    st.info("오퍼를 거절했습니다.")
                                    st.rerun()
                                except APIError as e:
                                    st.error(f"오류: {e.message}")
                        st.markdown("---")

        # --- 수락한 오퍼 - 계약 생성 대기: 2열 ---
        if accepted:
            st.subheader(f"계약 생성 대기 ({len(accepted)})")
            COLS = 2
            for row_start in range(0, len(accepted), COLS):
                row_offers = accepted[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, offer in enumerate(row_offers):
                    with cols[col_idx]:
                        st.markdown(f"**시급: ₩{int(float(offer['proposed_rate'])):,}**")
                        st.caption("수락 완료 - 계약을 생성하세요")
                        if st.button(
                            "계약 생성",
                            key=f"contract_{offer['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            try:
                                client.create_contract_from_offer(offer["id"])
                                st.success("계약이 생성되었습니다!")
                                st.session_state.page = "contracts"
                                st.rerun()
                            except APIError as e:
                                st.error(f"오류: {e.message}")
                        st.markdown("---")

        if not pending and not accepted:
            st.info("아직 받은 오퍼가 없습니다. 공고에 지원하면 스튜디오에서 오퍼를 보냅니다.")
            if st.button("일 찾기로 돌아가기"):
                st.session_state.page = "find_jobs"
                st.rerun()

        # --- 처리 완료 오퍼 내역 (expander) ---
        if others:
            with st.expander(f"처리된 오퍼 내역 ({len(others)})"):
                status_map = {
                    "accepted": "수락됨",
                    "rejected": "거절됨",
                    "expired": "만료됨",
                    "cancelled": "취소됨",
                }
                COLS = 2
                for row_start in range(0, len(others), COLS):
                    row_offers = others[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, offer in enumerate(row_offers):
                        with cols[col_idx]:
                            status_label = status_map.get(offer["status"], offer["status"].upper())
                            st.markdown(f"**{status_label}** - ₩{int(float(offer['proposed_rate'])):,}/시간")
                            if offer["id"] in existing_contract_offer_ids:
                                st.caption("계약 생성됨 (계약 내역에서 확인)")
                            if offer.get("message"):
                                st.caption(offer["message"][:50])
                            st.markdown("---")

    except APIError as e:
        st.error(f"오퍼 로드 실패: {e.message}")


# ============================================================
# STEP 3: APPLICANTS (Studio)
# ============================================================

def render_applicants_step():
    st.header("3단계: 지원자 선택")

    client = get_client()

    try:
        # Get all job posts
        all_jobs = client.list_job_posts().get("items", [])

        # Filter to only my jobs
        my_studio_id = str(st.session_state.profile_id)
        jobs = [job for job in all_jobs if job.get("studio_id") == my_studio_id]

        if not jobs:
            st.info("등록된 공고가 없습니다.")
            if st.button("공고 등록하기"):
                st.session_state.page = "create_job"
                st.rerun()
            return

        st.subheader("내 공고")

        for job in jobs:
            app_count = job.get("application_count", 0)
            type_label = {"substitute": "대타", "regular": "정규", "contract": "계약"}.get(
                job.get("job_type", ""), job.get("job_type", "")
            )
            with st.expander(
                f"**{job['title']}** | {job['date']} | 지원자 {app_count}명",
                expanded=(app_count > 0),
            ):
                # 공고 요약 정보 (1줄)
                st.caption(
                    f"유형: {type_label} | 시급: ₩{int(float(job['hourly_rate'])):,} | 지역: {job.get('region', '-')}"
                )

                # Get applications for this job
                try:
                    result = client.get_job_post_applications(job["id"])
                    applications = result.get("items", [])

                    if not applications:
                        st.caption("아직 지원자가 없습니다.")
                    else:
                        # 2열 카드로 지원자 배치
                        COLS = 2
                        for row_start in range(0, len(applications), COLS):
                            row_apps = applications[row_start : row_start + COLS]
                            cols = st.columns(COLS)

                            for col_idx, app in enumerate(row_apps):
                                with cols[col_idx]:
                                    instructor_name = app.get("instructor_name", "강사")
                                    exp_years = app.get("instructor_experience_years", 0)
                                    rating = app.get("instructor_rating")

                                    # 카드 헤더: 이름 + 경력
                                    st.markdown(f"**{instructor_name}** (경력 {exp_years}년)")

                                    # 평점
                                    if rating:
                                        st.caption(f"평점: {rating:.1f} / 5.0")

                                    # 자기소개 (짧게)
                                    if app.get("cover_letter"):
                                        cl = app["cover_letter"]
                                        st.caption(cl[:50] + "..." if len(cl) > 50 else cl)
                                        if len(cl) > 50:
                                            with st.expander("전체 보기"):
                                                st.write(cl)

                                    # 오퍼 상태 표시
                                    if app.get("has_offer"):
                                        status_labels = {
                                            "pending": "오퍼 전송됨 (응답 대기)",
                                            "accepted": "수락됨",
                                            "rejected": "거절됨",
                                        }
                                        st.caption(status_labels.get(app["status"], app["status"]))
                                    else:
                                        status_labels = {
                                            "pending": "대기중",
                                            "withdrawn": "철회됨",
                                        }
                                        st.caption(status_labels.get(app["status"], app["status"]))

                                    # 오퍼 보내기 버튼
                                    if app["status"] == "pending" and not app.get("has_offer"):
                                        already_open = (
                                            st.session_state.get("show_offer_modal")
                                            and st.session_state.get("selected_application", {}).get("id") == app["id"]
                                        )
                                        if already_open:
                                            if st.button(
                                                "오퍼 작성 중 (아래 확인)",
                                                key=f"offer_{app['id']}",
                                                use_container_width=True,
                                            ):
                                                st.session_state.offer_scroll_trigger = (
                                                    st.session_state.get("offer_scroll_trigger", 0) + 1
                                                )
                                                st.rerun()
                                        else:
                                            if st.button(
                                                "오퍼 보내기",
                                                key=f"offer_{app['id']}",
                                                type="primary",
                                                use_container_width=True,
                                            ):
                                                st.session_state.show_offer_modal = False
                                                st.session_state.selected_application = None
                                                st.session_state.selected_application = app
                                                st.session_state.show_offer_modal = True
                                                st.rerun()

                                    st.markdown("---")

                except APIError as e:
                    st.caption(f"지원자 정보를 불러올 수 없습니다: {e.message}")

        # Offer form section - rendered below applicant list
        if st.session_state.get("show_offer_modal"):
            app = st.session_state.selected_application
            instructor_name = app.get("instructor_name", "강사")

            # Auto-scroll anchor: JavaScript scrolls to this element after rerun.
            # A unique scroll_key (based on offer_scroll_trigger) forces the browser
            # to re-execute the scroll script even when the anchor already exists in DOM.
            scroll_key = st.session_state.get("offer_scroll_trigger", 0)
            st.markdown(
                f"""
                <div id="offer-form-anchor" data-scroll-key="{scroll_key}"></div>
                <script>
                    // Scroll to offer form after short delay to allow DOM render.
                    // data-scroll-key attribute changes on each trigger so the browser
                    // treats this as a new element and re-runs the scroll.
                    (function() {{
                        var anchor = document.getElementById('offer-form-anchor');
                        if (anchor) {{
                            setTimeout(function() {{
                                anchor.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                            }}, 300);
                        }}
                    }})();
                </script>
                """,
                unsafe_allow_html=True,
            )

            # Top notification banner to draw attention
            st.info(
                f"**{instructor_name}** 강사에게 오퍼를 작성 중입니다. "
                "아래 양식을 작성한 후 오퍼를 전송하세요.",
                icon="✏️",
            )

            # Visually highlighted offer form card
            st.markdown(
                f"""
                <style>
                .offer-card {{
                    background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
                    border: 2px solid #1a73e8;
                    border-radius: 12px;
                    padding: 24px 28px 8px 28px;
                    margin: 8px 0 16px 0;
                    box-shadow: 0 4px 16px rgba(26, 115, 232, 0.15);
                }}
                .offer-card-title {{
                    color: #1a73e8;
                    font-size: 1.15rem;
                    font-weight: 700;
                    margin-bottom: 4px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                .offer-card-subtitle {{
                    color: #555;
                    font-size: 0.9rem;
                    margin-bottom: 16px;
                }}
                </style>
                <div class="offer-card">
                    <div class="offer-card-title">
                        &#9997;&#65039; 오퍼 작성 중...
                    </div>
                    <div class="offer-card-subtitle">
                        대상 강사: <strong>{instructor_name}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("offer_form"):
                proposed_rate = st.number_input(
                    "제안 시급 (원)",
                    min_value=0,
                    step=5000,
                    value=50000,
                    help="강사에게 제안할 시간당 급여를 입력하세요.",
                )
                message = st.text_area(
                    "메시지 (선택)",
                    placeholder="스튜디오 소개나 구체적인 근무 조건을 자유롭게 작성하세요.",
                    height=100,
                )

                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button(
                        "오퍼 전송",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            client.create_offer({
                                "application_id": app["id"],
                                "proposed_rate": proposed_rate,
                                "message": message,
                            })
                            st.success(
                                f"{instructor_name} 강사에게 오퍼를 전송했습니다! "
                                "강사의 응답을 기다려주세요."
                            )
                            st.session_state.show_offer_modal = False
                            st.session_state.selected_application = None
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")
                with col2:
                    if st.form_submit_button(
                        "취소",
                        use_container_width=True,
                    ):
                        st.session_state.show_offer_modal = False
                        st.session_state.selected_application = None
                        st.rerun()

    except APIError as e:
        st.error(f"로드 실패: {e.message}")


# ============================================================
# STEP 4: CONTRACTS (Both)
# ============================================================

# 계약 약관
CONTRACT_TERMS = """
### 📋 상호 약속 사항

**스케줄 관련**
- 지각 (10분 이상): 해당 금액의 10% 페널티
- 당일 취소: 해당 금액의 30% 페널티
- 무단 불참: 해당 금액의 50% 페널티

**계정 제재**
- 위반 누적 3회: 1개월 이용 정지
- 악의적 반복 위반: 영구 이용 정지

*양측 모두 동의 시 계약이 체결됩니다.*
"""


def _render_contract_card(contract: dict, user: dict, client) -> None:
    """단일 계약 카드를 렌더링합니다 (진행 중 계약용)."""
    role = user.get("role")
    status = contract["status"]

    # 상태 배지
    status_emoji = {"confirmed": "📝", "in_progress": "🔵", "pending_completion": "⏳"}.get(status, "")
    status_label = {"confirmed": "서명 대기", "in_progress": "진행 중", "pending_completion": "완료 대기"}.get(status, status)

    # 카드 헤더 - 상태와 계약 번호
    st.markdown(f"### {status_emoji} {status_label}")
    st.caption(f"계약 ID: {contract['id'][:8]}...")

    # 계약 당사자 정보 박스
    with st.container():
        st.markdown("📋 **계약 상세 정보**")

        # 당사자 정보 (2열)
        party_col1, party_col2 = st.columns(2)
        with party_col1:
            st.markdown("**👤 강사 정보**")
            # 강사 이름은 offer 정보나 별도 API로 가져와야 할 수 있음
            instructor_id = contract.get('instructor_id', '-')
            st.caption(f"강사 ID: {str(instructor_id)[:8]}...")
            if contract.get('instructor_name'):
                st.caption(f"이름: {contract['instructor_name']}")

        with party_col2:
            st.markdown("**🏢 스튜디오 정보**")
            studio_id = contract.get('studio_id', '-')
            st.caption(f"스튜디오 ID: {str(studio_id)[:8]}...")
            if contract.get('studio_name'):
                st.caption(f"이름: {contract['studio_name']}")

        st.markdown("---")

        # 계약 조건 정보 (2열)
        st.markdown("💰 **계약 조건**")
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.caption(f"📅 날짜: **{contract['date']}**")
            st.caption(f"⏰ 시간: **{contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}**")

            # 시간 계산
            if contract.get('start_time') and contract.get('end_time'):
                try:
                    from datetime import datetime
                    start = datetime.strptime(contract['start_time'], "%H:%M:%S")
                    end = datetime.strptime(contract['end_time'], "%H:%M:%S")
                    duration = (end - start).total_seconds() / 3600
                    st.caption(f"⏱️ 수업 시간: **{duration:.1f}시간**")
                except:
                    pass

        with detail_col2:
            hourly_rate = contract.get('hourly_rate', 0)
            total_amount = float(contract.get('total_amount', 0))
            st.caption(f"💵 시급: **₩{int(float(hourly_rate)):,}**")
            st.caption(f"💰 총액: **₩{int(total_amount):,}**")

            # 플랫폼 수수료 표시 (5%)
            platform_fee = total_amount * 0.05
            settlement = total_amount - platform_fee
            st.caption(f"📊 정산금: **₩{int(settlement):,}** (수수료 5%)")

    st.markdown("---")

    # --- 서명 대기 (confirmed) ---
    if status == "confirmed":
        my_role = role
        if my_role == "instructor":
            my_signed = contract.get("instructor_signed_at") is not None
            other_signed = contract.get("studio_signed_at") is not None
            other_party = "스튜디오"
        else:
            my_signed = contract.get("studio_signed_at") is not None
            other_signed = contract.get("instructor_signed_at") is not None
            other_party = "강사"

        # 서명 상태 시각화 (2열 배지)
        sig_col1, sig_col2 = st.columns(2)
        with sig_col1:
            if my_role == "instructor":
                label = "내 서명 (강사)"
                done = contract.get("instructor_signed_at") is not None
            else:
                label = "내 서명 (스튜디오)"
                done = contract.get("studio_signed_at") is not None
            if done:
                st.success(f"{label}: 완료")
            else:
                st.warning(f"{label}: 대기")
        with sig_col2:
            if my_role == "instructor":
                label = f"{other_party} 서명"
                done = contract.get("studio_signed_at") is not None
            else:
                label = f"{other_party} 서명"
                done = contract.get("instructor_signed_at") is not None
            if done:
                st.success(f"{label}: 완료")
            else:
                st.warning(f"{label}: 대기")

        if my_signed and other_signed:
            st.info("양측 서명 완료 - 계약이 곧 시작됩니다")
        elif my_signed:
            st.caption(f"{other_party} 서명을 기다리는 중입니다")
        else:
            # 약관 + 서명 버튼 (expander로 공간 절약)
            if other_signed:
                st.info(f"{other_party}가 서명했습니다. 서명을 완료해주세요.")
            with st.expander("약관 확인 후 서명"):
                st.markdown(CONTRACT_TERMS)
                agree = st.checkbox(
                    "위 약속 사항에 동의합니다",
                    key=f"agree_{contract['id']}",
                )
                if agree:
                    btn_text = "서명하기" if not other_signed else "서명하고 계약 시작하기"
                    if st.button(
                        btn_text,
                        key=f"sign_{contract['id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            client.set_contract_in_progress(contract["id"])
                            if other_signed:
                                st.success("계약이 체결되었습니다! 수업을 진행해주세요.")
                                st.balloons()
                            else:
                                st.success(f"서명 완료. {other_party}의 서명을 기다리고 있습니다.")
                            st.rerun()
                        except APIError as e:
                            if "Already signed" in str(e):
                                st.warning("이미 서명하셨습니다.")
                            else:
                                st.error(f"오류: {e.message}")

    # --- 진행 중 (in_progress) ---
    elif status == "in_progress":
        st.success("✅ 계약 체결 완료! 수업을 진행해주세요.")

        # 수업 진행 정보 표시
        with st.container():
            st.markdown("📌 **수업 진행 정보**")
            progress_col1, progress_col2 = st.columns(2)
            with progress_col1:
                # 오늘 날짜와 비교
                from datetime import datetime, date
                contract_date = contract.get('date', '')
                try:
                    c_date = datetime.strptime(contract_date, "%Y-%m-%d").date()
                    today = date.today()
                    if c_date == today:
                        st.info("🔴 오늘 수업입니다!")
                    elif c_date < today:
                        st.warning("⚠️ 수업일이 지났습니다")
                    else:
                        days_left = (c_date - today).days
                        st.caption(f"📅 수업까지 {days_left}일 남음")
                except:
                    pass

            with progress_col2:
                st.caption("💡 수업 완료 후 '수업 완료' 버튼을 클릭해주세요")
                st.caption("💡 양측 모두 완료 확인 시 정산됩니다")

        st.markdown("---")

        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button(
                "🎉 수업 완료",
                key=f"complete_{contract['id']}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    client.complete_contract(contract["id"])
                    st.success("완료 확인! 상대방도 확인하면 정산이 진행됩니다.")
                    st.session_state.page = "complete"
                    st.rerun()
                except APIError as e:
                    st.error(f"오류: {e.message}")
        with action_col2:
            if st.button(
                "취소",
                key=f"cancel_btn_{contract['id']}",
                use_container_width=True,
            ):
                st.session_state[f"show_cancel_{contract['id']}"] = True
        with action_col3:
            if st.button(
                "불참 신고",
                key=f"noshow_btn_{contract['id']}",
                use_container_width=True,
            ):
                st.session_state[f"show_noshow_{contract['id']}"] = True

        # 취소 폼 (expander)
        if st.session_state.get(f"show_cancel_{contract['id']}"):
            with st.expander("취소 사유 입력", expanded=True):
                with st.form(key=f"cancel_form_{contract['id']}"):
                    reason = st.text_input("취소 사유")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("취소 확정", use_container_width=True):
                            try:
                                client.cancel_contract(contract["id"], reason or "취소")
                                st.warning("취소 처리되었습니다. 약관에 따라 페널티가 적용될 수 있습니다.")
                                st.session_state[f"show_cancel_{contract['id']}"] = False
                                st.rerun()
                            except APIError as e:
                                st.error(f"오류: {e.message}")
                    with c2:
                        if st.form_submit_button("돌아가기", use_container_width=True):
                            st.session_state[f"show_cancel_{contract['id']}"] = False

        # 노쇼 신고 폼 (expander)
        if st.session_state.get(f"show_noshow_{contract['id']}"):
            with st.expander("노쇼 신고", expanded=True):
                with st.form(key=f"noshow_form_{contract['id']}"):
                    if user.get("role") == "studio":
                        reported_id = contract.get("instructor_id", "")
                        report_msg = "강사가 수업에 불참했나요?"
                    else:
                        reported_id = contract.get("studio_id", "")
                        report_msg = "스튜디오에서 수업을 진행하지 않았나요?"
                    st.warning(report_msg)
                    st.caption("노쇼 신고 시 24시간 내 이의제기가 없으면 패널티가 적용됩니다.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("노쇼 신고", type="primary", use_container_width=True):
                            try:
                                client.report_no_show(contract["id"], reported_id)
                                st.warning("신고가 접수되었습니다. 상대방에게 24시간 이의제기 기간이 부여됩니다.")
                                st.session_state[f"show_noshow_{contract['id']}"] = False
                                st.rerun()
                            except APIError as e:
                                st.error(f"오류: {e.message}")
                    with c2:
                        if st.form_submit_button("돌아가기", use_container_width=True):
                            st.session_state[f"show_noshow_{contract['id']}"] = False

    # --- 완료 확인 대기 (pending_completion) ---
    elif status == "pending_completion":
        studio_confirmed = contract.get("studio_confirmed_at") is not None
        instructor_confirmed = contract.get("instructor_confirmed_at") is not None

        # 완료 확인 상태 배지 (2열)
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if studio_confirmed:
                st.success("스튜디오: 확인 완료")
            else:
                st.warning("스튜디오: 대기 중")
        with conf_col2:
            if instructor_confirmed:
                st.success("강사: 확인 완료")
            else:
                st.warning("강사: 대기 중")

        my_confirmed = studio_confirmed if role == "studio" else instructor_confirmed
        if my_confirmed:
            st.info("이미 완료 확인하셨습니다. 상대방의 확인을 기다리는 중입니다.")
        else:
            if st.button(
                "수업 완료 확인",
                key=f"complete_pending_{contract['id']}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    client.complete_contract(contract["id"])
                    st.success("완료 확인되었습니다! 상대방도 확인하면 정산이 진행됩니다.")
                    st.session_state.page = "complete"
                    st.rerun()
                except APIError as e:
                    st.error(f"오류: {e.message}")


def render_contracts_step():
    st.header("4단계: 계약 진행")
    st.caption("진행 중인 계약을 관리하고 수업 완료를 확인하세요.")

    client = get_client()
    user = st.session_state.user
    role = user.get("role")

    try:
        result = client.get_my_contracts()
        contracts = result.get("items", [])

        active = [c for c in contracts if c["status"] in ["confirmed", "in_progress", "pending_completion"]]
        completed = [c for c in contracts if c["status"] in ["completed", "cancelled"]]

        if not contracts:
            st.info("아직 계약이 없습니다.")
            st.caption("강사: 오퍼 수락 후 계약이 생성됩니다.")
            st.caption("스튜디오: 강사가 오퍼를 수락하면 계약이 생성됩니다.")
            return

        # --- 진행 중인 계약: 2열 카드 ---
        if active:
            st.subheader(f"진행 중인 계약 ({len(active)})")

            COLS = 2
            for row_start in range(0, len(active), COLS):
                row_contracts = active[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, contract in enumerate(row_contracts):
                    with cols[col_idx]:
                        with st.container():
                            _render_contract_card(contract, user, client)
                            st.markdown("---")

        # --- 완료/취소된 계약 (expander, 2열 요약) ---
        if completed:
            with st.expander(f"완료/취소된 계약 ({len(completed)})"):
                COLS = 2
                for row_start in range(0, len(completed), COLS):
                    row_contracts = completed[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, contract in enumerate(row_contracts):
                        with cols[col_idx]:
                            status_emoji = {"completed": "✅", "cancelled": "❌"}.get(contract["status"], "")
                            status_label = {"completed": "완료", "cancelled": "취소"}.get(
                                contract["status"], contract["status"]
                            )
                            st.markdown(f"### {status_emoji} {status_label}")

                            # 계약 정보
                            info_col1, info_col2 = st.columns(2)
                            with info_col1:
                                st.caption(f"📅 {contract['date']}")
                                st.caption(f"⏰ {contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}")
                            with info_col2:
                                total_amount = float(contract.get('total_amount', 0))
                                st.caption(f"💰 ₩{int(total_amount):,}")

                                # 완료된 계약인 경우 정산 정보
                                if contract["status"] == "completed":
                                    platform_fee = total_amount * 0.05
                                    settlement = total_amount - platform_fee
                                    st.caption(f"📊 정산: ₩{int(settlement):,}")
                                # 취소된 계약인 경우 취소 사유
                                elif contract["status"] == "cancelled" and contract.get("cancellation_reason"):
                                    st.caption(f"📝 사유: {contract['cancellation_reason'][:20]}...")

                            st.markdown("---")

    except APIError as e:
        st.error(f"계약 로드 실패: {e.message}")


# ============================================================
# STEP 5: COMPLETE (Both)
# ============================================================

def _render_review_form(contract: dict, user: dict, client, existing_review: dict | None) -> None:
    """리뷰 작성/수정 폼을 expander 안에 렌더링합니다."""
    rating_options = {"1점": 1, "2점": 2, "3점": 3, "4점": 4, "5점": 5}

    if existing_review:
        # 기존 리뷰 표시
        rating_val = existing_review.get("rating", 0)
        rating_stars = "별" * rating_val
        st.caption(f"내 평점: {rating_stars} ({rating_val}점)")
        if existing_review.get("comment"):
            st.caption(f"후기: {existing_review['comment']}")

        edit_key = f"edit_mode_{contract['id']}"
        if st.session_state.get(edit_key, False):
            with st.form(f"edit_review_form_{contract['id']}"):
                current_idx = existing_review.get("rating", 3) - 1
                rating_display = st.radio(
                    "평점",
                    options=list(rating_options.keys()),
                    index=current_idx,
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"edit_rating_{contract['id']}",
                )
                new_rating = rating_options[rating_display]
                prompt = "스튜디오에 대한 후기" if user["role"] == "instructor" else "강사님에 대한 후기"
                new_comment = st.text_area(
                    prompt,
                    value=existing_review.get("comment", ""),
                    height=80,
                    key=f"edit_comment_{contract['id']}",
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.form_submit_button("저장", type="primary", use_container_width=True):
                        try:
                            client.update_review(existing_review["id"], new_rating, new_comment)
                            st.success("리뷰가 수정되었습니다!")
                            del st.session_state[edit_key]
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")
                with c2:
                    if st.form_submit_button("삭제", use_container_width=True):
                        try:
                            client.delete_review(existing_review["id"])
                            st.success("리뷰가 삭제되었습니다.")
                            del st.session_state[edit_key]
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")
                with c3:
                    if st.form_submit_button("취소", use_container_width=True):
                        del st.session_state[edit_key]
                        st.rerun()
        else:
            if st.button("수정/삭제", key=f"edit_btn_{contract['id']}", use_container_width=True):
                st.session_state[edit_key] = True
                st.rerun()
    else:
        # 신규 리뷰 작성
        form_key = f"show_review_form_{contract['id']}"
        if form_key not in st.session_state:
            st.session_state[form_key] = False

        if not st.session_state[form_key]:
            if st.button(
                "리뷰 작성",
                key=f"review_btn_{contract['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[form_key] = True
                st.rerun()
        else:
            with st.form(f"review_form_{contract['id']}"):
                rating_display = st.radio(
                    "평점",
                    options=list(rating_options.keys()),
                    index=2,
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"rating_{contract['id']}",
                )
                rating = rating_options[rating_display]
                prompt = "스튜디오에 대한 후기 (선택)" if user["role"] == "instructor" else "강사님에 대한 후기 (선택)"
                placeholder = "예: 시설이 깨끗하고 운영이 체계적입니다." if user["role"] == "instructor" else "예: 전문적이고 친절한 강사님입니다."
                comment = st.text_area(
                    prompt,
                    placeholder=placeholder,
                    height=80,
                    key=f"comment_{contract['id']}",
                )
                sub_col1, sub_col2 = st.columns(2)
                submitted = sub_col1.form_submit_button("제출", type="primary", use_container_width=True)
                cancelled = sub_col2.form_submit_button("취소", use_container_width=True)

                if submitted:
                    try:
                        client.create_review(contract["id"], rating, comment)
                        st.success("리뷰가 등록되었습니다!")
                        st.session_state[form_key] = False
                        st.rerun()
                    except APIError as e:
                        if "already exists" in str(e.message).lower():
                            st.error("이미 리뷰를 작성하셨습니다.")
                        else:
                            st.error(f"오류: {e.message}")
                    except Exception as e:
                        st.error(f"예상치 못한 오류: {str(e)}")

                if cancelled:
                    st.session_state[form_key] = False
                    st.rerun()


def render_complete_step():
    st.header("5단계: 완료 & 리뷰")
    st.caption("완료된 계약을 확인하고 상대방에 대한 리뷰를 작성하세요.")

    client = get_client()
    user = st.session_state.user
    role = user.get("role")

    try:
        result = client.get_my_contracts()
        all_contracts = result.get("items", [])

        pending_completion = [c for c in all_contracts if c["status"] == "pending_completion"]
        completed = [c for c in all_contracts if c["status"] == "completed"]

        # --- 완료 확인 대기 중인 계약 (action required, 2열 카드) ---
        if pending_completion:
            st.warning(f"완료 확인이 필요한 계약 {len(pending_completion)}건이 있습니다.")
            st.caption("양쪽 모두 완료를 확인해야 정산이 진행됩니다.")

            COLS = 2
            for row_start in range(0, len(pending_completion), COLS):
                row_items = pending_completion[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, contract in enumerate(row_items):
                    with cols[col_idx]:
                        st.markdown(f"**{contract.get('date', 'N/A')}** | ₩{int(float(contract.get('total_amount', 0))):,}")
                        st.caption(f"{contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}")

                        # 확인 상태 배지 (2열)
                        studio_confirmed = contract.get("studio_confirmed_at") is not None
                        instructor_confirmed = contract.get("instructor_confirmed_at") is not None
                        badge_col1, badge_col2 = st.columns(2)
                        with badge_col1:
                            if studio_confirmed:
                                st.success("스튜디오: 완료")
                            else:
                                st.warning("스튜디오: 대기")
                        with badge_col2:
                            if instructor_confirmed:
                                st.success("강사: 완료")
                            else:
                                st.warning("강사: 대기")

                        my_confirmed = studio_confirmed if role == "studio" else instructor_confirmed
                        if my_confirmed:
                            st.info("이미 확인하셨습니다. 상대방을 기다리는 중입니다.")
                        else:
                            if st.button(
                                "수업 완료 확인",
                                key=f"confirm_{contract['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    client.complete_contract(contract["id"])
                                    st.success("확인되었습니다! 상대방도 확인하면 정산이 진행됩니다.")
                                    st.rerun()
                                except APIError as e:
                                    st.error(f"오류: {e.message}")
                        st.markdown("---")

        # --- 빈 상태 ---
        if not pending_completion and not completed:
            st.info("아직 완료된 계약이 없습니다. 계약을 진행하고 수업을 완료하면 여기에서 확인할 수 있습니다.")

        # --- 완료된 계약 그리드 + 리뷰 ---
        if completed:
            total = sum(float(c["total_amount"]) for c in completed)
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("완료한 계약", f"{len(completed)}건")
            with metric_col2:
                label = "총 수익" if role == "instructor" else "총 지출"
                st.metric(label, f"₩{int(total):,}")

            st.markdown("---")
            st.subheader("리뷰 관리")

            # 리뷰 조회 (배치)
            review_map: dict[str, dict | None] = {}
            for contract in completed:
                try:
                    resp = client.get_my_review_for_contract(contract["id"])
                    review_map[contract["id"]] = resp if (resp and resp.get("id")) else None
                except APIError as e:
                    review_map[contract["id"]] = None
                except Exception:
                    review_map[contract["id"]] = None

            # 리뷰 미작성 건 먼저, 작성 완료 건 뒤로 정렬
            no_review = [c for c in completed if not review_map.get(c["id"])]
            has_review = [c for c in completed if review_map.get(c["id"])]
            sorted_contracts = no_review + has_review

            # 2열 카드 그리드
            COLS = 2
            for row_start in range(0, len(sorted_contracts), COLS):
                row_items = sorted_contracts[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, contract in enumerate(row_items):
                    existing_review = review_map.get(contract["id"])
                    with cols[col_idx]:
                        review_badge = "리뷰 완료" if existing_review else "리뷰 미작성"
                        expander_label = f"{contract.get('date', 'N/A')} | ₩{int(float(contract.get('total_amount', 0))):,} | {review_badge}"
                        with st.expander(expander_label, expanded=(not existing_review)):
                            st.caption(
                                f"시간: {contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}"
                            )
                            _render_review_form(contract, user, client, existing_review)

    except Exception as e:
        st.error(f"완료/리뷰 섹션 오류: {str(e)}")

    st.markdown("---")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        btn_label = "새로운 일 찾기" if user["role"] == "instructor" else "새 공고 등록"
        if st.button(btn_label, use_container_width=True):
            st.session_state.page = "find_jobs" if user["role"] == "instructor" else "create_job"
            st.rerun()
    with nav_col2:
        if st.button("계약 내역 보기", use_container_width=True):
            st.session_state.page = "contracts"
            st.rerun()


# ============================================================
# MAIN
# ============================================================

def main():
    if st.session_state.token is None:
        render_auth_page()
        return

    # Ensure user is loaded
    if st.session_state.user is None:
        try:
            client = get_client()
            me = client.get_me()
            st.session_state.user = me.get("user")
            st.session_state.profile_id = me.get("profile_id")
        except Exception as e:
            st.error(f"세션 오류: {e}")
            logout()
            st.rerun()
            return

    client = get_client()
    user = st.session_state.user

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        role_text = "강사" if user["role"] == "instructor" else "스튜디오"
        st.title(f"StudioBridge - {role_text}")
    with col2:
        # 사용자 정보와 로그아웃 버튼을 세로로 정렬
        user_email = user.get("email", "")
        user_name = user.get("display_name") if user["role"] == "instructor" else user.get("business_name")

        # # 이름 또는 프로필 안내 표시
        # if user_name:
        #     st.caption(user_name)
        # else:
        #     st.caption("프로필을 완성해주세요")
            
        # 이메일 표시
        st.markdown(f"**{user_email}** ({user_name})")


        # 로그아웃 버튼
        if st.button("로그아웃", use_container_width=True):
            logout()
            st.rerun()

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
        st.info(f"👋 환영합니다! 먼저 프로필을 완성해주세요. {'강사' if user['role'] == 'instructor' else '스튜디오'} 정보를 입력하면 매칭을 시작할 수 있습니다.")
    elif current_step == 2:
        if user["role"] == "instructor":
            st.info("🔍 이제 일자리를 찾아볼 수 있습니다! 매칭 점수가 높은 공고부터 확인해보세요.")
        else:
            st.info("📝 첫 공고를 등록해보세요! 3클릭만으로 강사 모집이 가능합니다.")
    elif current_step == 3:
        if user["role"] == "instructor":
            st.info("💌 받은 오퍼를 확인하고 수락/거절을 선택해주세요.")
        else:
            st.info("👥 지원한 강사들을 검토하고 오퍼를 보내주세요.")
    elif current_step == 4:
        st.info("📋 진행 중인 계약을 확인하고 관리해주세요.")
    elif current_step == 5:
        st.success("🎉 완료된 계약입니다! 리뷰를 남겨주세요.")

    st.markdown("---")

    # Determine which page to show
    # If profile is not complete (step 1), always show profile page
    if current_step == 1 and not data.get("profile_complete", False):
        page = "profile"
        # Clear any stored page in session to avoid conflicts
        if "page" in st.session_state:
            del st.session_state.page
    else:
        # Use stored page or default to current step's page
        page = st.session_state.get("page", steps[current_step - 1][2])

    # Render appropriate page based on role
    if page == "profile":
        render_profile_step()
    elif page == "find_jobs":
        # Only instructors can access find_jobs
        if user["role"] == "instructor":
            render_find_jobs_step()
        else:
            # Redirect studios to their appropriate page
            st.session_state.page = "create_job"
            st.rerun()
    elif page == "create_job":
        # Only studios can create jobs
        if user["role"] == "studio":
            render_create_job_step()
        else:
            # Redirect instructors to find jobs
            st.session_state.page = "find_jobs"
            st.rerun()
    elif page == "offers":
        render_offers_step()
    elif page == "applicants":
        # Only studios can view applicants
        if user["role"] == "studio":
            render_applicants_step()
        else:
            # Redirect instructors to offers
            st.session_state.page = "offers"
            st.rerun()
    elif page == "contracts":
        render_contracts_step()
    elif page == "complete":
        render_complete_step()
    else:
        # Default to current step
        st.session_state.page = steps[current_step - 1][2]
        st.rerun()


if __name__ == "__main__":
    main()
