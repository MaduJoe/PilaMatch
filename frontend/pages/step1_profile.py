"""
Step 1: Profile completion - both instructor and studio
"""

import time
import streamlit as st
from api_client import APIError
from utils.helpers import get_client


def render_profile_step():
    """Render the profile completion step for instructors and studios."""
    st.header("1단계: 프로필 완성")

    client = get_client()
    user = st.session_state.user

    # v3.0: Show profile completeness and Trust Score
    col_score1, col_score2 = st.columns(2)

    with col_score1:
        try:
            completeness = client.get_profile_completeness()
            percentage = completeness.get("percentage", 0)
            message = completeness.get("message", "")

            # Progress bar with color based on percentage
            if percentage < 70:
                st.error(f"프로필 {percentage}% 완성")
            elif percentage < 90:
                st.warning(f"프로필 {percentage}% 완성")
            else:
                st.success(f"프로필 {percentage}% 완성")

            st.progress(percentage / 100)
            if percentage < 100:
                st.caption("프로필을 완성하면 Trust Score가 올라갑니다")
        except:
            pass

    with col_score2:
        try:
            trust_data = client.get_trust_display()
            score = trust_data.get("score", 40)
            level = trust_data.get("level", "신진")
            level_color = trust_data.get("level_color", "bronze")

            # Color based on level
            if level_color == "platinum":
                st.success(f"Trust Score: {score}점 ({level})")
            elif level_color == "gold":
                st.info(f"Trust Score: {score}점 ({level})")
            elif level_color == "silver":
                st.warning(f"Trust Score: {score}점 ({level})")
            else:
                st.error(f"Trust Score: {score}점 ({level})")

            st.progress(score / 100)

            if st.button("점수 새로고침", key="refresh_trust"):
                try:
                    result = client.refresh_trust_score()
                    st.success(f"새 점수: {result['new_score']}점")
                    st.rerun()
                except:
                    st.error("1시간에 한 번만 새로고침 가능합니다")
        except:
            pass

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("기본 정보")

        try:
            if user["role"] == "instructor":
                _render_instructor_profile_form(client)
            else:
                _render_studio_profile_form(client)
        except APIError as e:
            st.error(f"프로필 로드 실패: {e.message}")

    with col2:
        st.subheader("본인인증")
        _render_verification_section(client, user)

        # Premium Membership Status
        st.markdown("---")
        st.subheader("멤버십 상태")
        _render_membership_section(client)

        # v3.0: Deposit section removed - no longer required


def _render_instructor_profile_form(client):
    """Render profile form for instructors."""
    profile = client.get_my_instructor_profile()

    with st.form("instructor_profile_form"):
        display_name = st.text_input("활동명 *", value=profile.get("display_name", ""))
        bio = st.text_area("자기소개", value=profile.get("bio", "") or "")
        experience_years = st.number_input(
            "경력 (년)", value=profile.get("experience_years", 0), min_value=0
        )

        regions = st.text_input(
            "활동 가능 지역 * (쉼표로 구분)",
            value=", ".join(profile.get("available_regions", [])),
            placeholder="강남, 서초, 송파",
        )

        certs = st.text_area(
            "자격증 (줄바꿈으로 구분)",
            value="\n".join(
                [
                    c.get("name", c) if isinstance(c, dict) else c
                    for c in profile.get("certifications", [])
                ]
            ),
        )

        col_a, col_b = st.columns(2)
        with col_a:
            rate_min = st.number_input(
                "최소 희망시급",
                value=int(float(profile.get("hourly_rate_min", 0) or 0)),
                step=5000,
            )
        with col_b:
            rate_max = st.number_input(
                "최대 희망시급",
                value=int(float(profile.get("hourly_rate_max", 0) or 0)),
                step=5000,
            )

        submitted = st.form_submit_button("저장", use_container_width=True)

    if submitted:
        with st.spinner("프로필을 저장하는 중..."):
            try:
                new_certs = [
                    {"name": c.strip(), "is_verified": False}
                    for c in certs.strip().split("\n")
                    if c.strip()
                ]
                region_list = [r.strip() for r in regions.split(",") if r.strip()]

                client.update_instructor_profile(
                    {
                        "display_name": display_name,
                        "bio": bio,
                        "experience_years": experience_years,
                        "available_regions": region_list,
                        "certifications": new_certs,
                        "hourly_rate_min": rate_min if rate_min > 0 else None,
                        "hourly_rate_max": rate_max if rate_max > 0 else None,
                    }
                )
                st.success("프로필이 성공적으로 저장되었습니다")
                # Update user display name in session
                if "user" in st.session_state and st.session_state.user:
                    st.session_state.user["display_name"] = display_name
                time.sleep(1)
                # Auto-navigate to next step (find jobs)
                st.session_state.page = "find_jobs"
                st.rerun()
            except APIError as e:
                st.session_state["profile_save_error"] = e.message
                st.rerun()

    if "profile_save_error" in st.session_state:
        st.error(
            f"프로필 저장에 실패했습니다: {st.session_state.pop('profile_save_error')}"
        )


def _render_studio_profile_form(client):
    """Render profile form for studios."""
    profile = client.get_my_studio_profile()

    with st.form("studio_profile_form"):
        business_name = st.text_input(
            "스튜디오명 *", value=profile.get("business_name", "")
        )
        description = st.text_area(
            "소개", value=profile.get("description", "") or ""
        )
        region = st.text_input(
            "지역 *",
            value=profile.get("region", "") or "",
            placeholder="강남",
        )
        address = st.text_input("주소", value=profile.get("address", "") or "")

        studio_submitted = st.form_submit_button("저장", use_container_width=True)

    if studio_submitted:
        with st.spinner("프로필을 저장하는 중..."):
            try:
                client.update_studio_profile(
                    {
                        "business_name": business_name,
                        "description": description,
                        "region": region,
                        "address": address,
                    }
                )
                st.success("프로필이 성공적으로 저장되었습니다")
                # Update studio business name in session
                if "user" in st.session_state and st.session_state.user:
                    st.session_state.user["business_name"] = business_name
                time.sleep(1)
                # Auto-navigate to next step (create job)
                st.session_state.page = "create_job"
                st.rerun()
            except APIError as e:
                st.session_state["profile_save_error"] = e.message
                st.rerun()

    if "profile_save_error" in st.session_state:
        st.error(
            f"프로필 저장에 실패했습니다: {st.session_state.pop('profile_save_error')}"
        )


def _render_verification_section(client, user):
    """Render phone and business verification UI."""
    # Phone verification
    if user.get("identity_verified"):
        st.success("휴대폰 인증 완료")
    else:
        st.warning("휴대폰 인증 필요")
        with st.form("phone_form"):
            phone = st.text_input("휴대폰 번호", placeholder="01012345678")
            if st.form_submit_button("인증번호 발송"):
                try:
                    result = client.request_phone_verification(phone)
                    st.session_state.verify_phone = phone
                    st.info(
                        f"인증번호가 발송되었습니다. (개발모드: {result.get('_dev_otp', '')})"
                    )
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
            st.success("사업자 인증 완료")
        else:
            st.warning("사업자 인증 필요")
            with st.form("biz_form"):
                biz_num = st.text_input(
                    "사업자등록번호", placeholder="000-00-00000"
                )
                if st.form_submit_button("인증"):
                    try:
                        client.verify_business(biz_num)
                        st.success("인증 완료!")
                        me = client.get_me()
                        st.session_state.user = me["user"]
                        st.rerun()
                    except APIError as e:
                        st.error(f"오류: {e.message}")


def _render_membership_section(client):
    """Render premium membership status and upgrade UI."""
    try:
        subscription_status = client.get_subscription_status()
        membership_tier = subscription_status.get("membership_tier", "free")

        if membership_tier == "premium":
            col_mem1, col_mem2 = st.columns(2)
            with col_mem1:
                st.success("프리미엄 회원")
                st.caption("더 빠른 성공을 위한 도구를 이용하실 수 있습니다")
            with col_mem2:
                if subscription_status.get("subscription"):
                    sub = subscription_status["subscription"]
                    if sub.get("next_billing_date"):
                        next_date = sub["next_billing_date"][:10]
                        st.info(f"다음 결제일: {next_date}")
                    if st.button("구독 취소", type="secondary"):
                        try:
                            result = client.cancel_subscription("User requested")
                            st.success("구독이 취소되었습니다.")
                            st.rerun()
                        except APIError as e:
                            st.error(f"구독 취소 실패: {e.message}")
        else:
            st.info("무료 회원")
            col_up1, col_up2 = st.columns([2, 1])
            with col_up1:
                st.markdown(
                    "**프리미엄 멤버십 혜택** (월 9,900원)\n"
                    "- **수수료 40% 할인** - 5% → 3%로 절감\n"
                    "- **우선 검색 노출** - 상위 30% 노출\n"
                    "- **무제한 동시 지원** - 더 많은 기회\n"
                    "- **프리미엄 골드 뱃지** - Trust Score +10점\n"
                    "- **즉시 정산** - D+1 정산 옵션"
                )
            with col_up2:
                if st.button(
                    "프리미엄 업그레이드",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.show_upgrade_modal = True

            # Upgrade modal
            if st.session_state.get("show_upgrade_modal"):
                with st.container():
                    st.markdown("### 프리미엄 멤버십 결제")
                    st.info("월 9,900원으로 더 빠른 계약 성공을 경험하세요!")

                    col_pay1, col_pay2 = st.columns(2)
                    with col_pay1:
                        if st.button("결제 진행", type="primary", use_container_width=True):
                            try:
                                result = client.initialize_premium_upgrade()
                                st.session_state.premium_order_id = result["order_id"]
                                st.session_state.premium_amount = result["amount"]
                                st.success(f"주문번호: {result['order_id']}")
                                st.info("토스페이먼츠 결제 페이지로 이동합니다...")
                                time.sleep(1)
                                confirm_result = client.confirm_subscription_payment(
                                    "test_payment_key",
                                    result["order_id"],
                                )
                                st.success("프리미엄 회원이 되신 것을 축하합니다!")
                                del st.session_state.show_upgrade_modal
                                st.rerun()
                            except APIError as e:
                                st.error(f"업그레이드 실패: {e.message}")
                    with col_pay2:
                        if st.button("취소", type="secondary", use_container_width=True):
                            del st.session_state.show_upgrade_modal
                            st.rerun()
    except APIError:
        st.warning("멤버십 정보를 불러올 수 없습니다")


# v3.0: Deposit section removed - no longer required
