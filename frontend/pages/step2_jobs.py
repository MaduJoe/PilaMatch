"""
Step 2: Job finding (instructor) and job creation (studio)
"""

import time
import streamlit as st
from api_client import APIError
from utils.helpers import get_client
from utils.constants import SEOUL_REGIONS, RATE_PRESETS
from components.map import render_kakao_map


def render_find_jobs_step():
    """Render job listing and application UI for instructors."""
    st.header("2단계: 일 찾기")

    client = get_client()

    # v3.0 Phase 2: Show application limit status for Free tier users
    with st.spinner("지원 현황을 불러오는 중..."):
        try:
            subscription_status = client.get_subscription_status()
            membership_tier = subscription_status.get("membership_tier", "free")

            if membership_tier == "free":
                # Count active applications
                my_applications = client.get_my_applications()
                active_count = sum(
                    1 for app in my_applications.get("items", [])
                    if app.get("status") == "pending"
                )

                MAX_FREE_APPLICATIONS = 5
                remaining = MAX_FREE_APPLICATIONS - active_count

                if remaining <= 0:
                    st.error(f"📋 지원 한도 도달: {active_count}/{MAX_FREE_APPLICATIONS}개 (무료 회원)")
                    st.info("💎 프리미엄으로 업그레이드하면 무제한 지원이 가능합니다!")
                elif remaining <= 2:
                    st.warning(f"📋 지원 가능: {remaining}개 남음 ({active_count}/{MAX_FREE_APPLICATIONS})")
                else:
                    st.info(f"📋 지원 현황: {active_count}/{MAX_FREE_APPLICATIONS} (무료 회원)")
            else:
                st.success("💎 프리미엄 회원 - 무제한 지원 가능")
        except Exception:
            pass

    # Get list of already applied jobs
    applied_job_ids = set()
    with st.spinner("지원 내역을 불러오는 중..."):
        try:
            my_applications = client.get_my_applications()
            applied_job_ids = {
                app.get("job_post_id")
                for app in my_applications.get("items", [])
            }
        except Exception:
            pass  # If error, assume no applications

    # Filter row (compact)
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
        with st.spinner("공고를 불러오는 중..."):
            result = client.list_job_posts_with_matching(params)
        jobs = result.get("items", [])

        if sort_by_score:
            jobs = sorted(
                jobs,
                key=lambda x: x.get("matching", {}).get("total", 0),
                reverse=True,
            )

        if not jobs:
            st.info("등록된 공고가 없습니다.")
            st.caption("스튜디오가 공고를 등록하면 여기에 표시됩니다.")
        else:
            applied_count = sum(
                1
                for item in jobs
                if item.get("job", item)["id"] in applied_job_ids
            )
            st.caption(
                f"총 {len(jobs)}개 공고 | 지원 완료 {applied_count}건"
            )

            # 3-column grid layout
            COLS = 3
            for row_start in range(0, len(jobs), COLS):
                row_items = jobs[row_start : row_start + COLS]
                cols = st.columns(COLS)

                for col_idx, item in enumerate(row_items):
                    job = item.get("job", item)
                    matching = item.get("matching", {})
                    score = matching.get("total", 0)
                    is_applied = job["id"] in applied_job_ids
                    is_urgent = item.get("is_urgent", False)  # v3.0 Phase 2

                    with cols[col_idx]:
                        _render_job_card(
                            job, matching, score, is_applied, client, is_urgent
                        )

    except APIError as e:
        st.error(f"공고 로드 실패: {e.message}")


def _render_job_card(job: dict, matching: dict, score: int, is_applied: bool, client, is_urgent: bool = False) -> None:
    """Render a single job posting card."""
    type_emoji = {
        "substitute": "",
        "regular": "",
        "contract": "",
    }.get(job["job_type"], "")
    type_label = {
        "substitute": "대타",
        "regular": "정규",
        "contract": "계약",
    }.get(job["job_type"], "")

    # v3.0 Phase 2: Premium badge and urgent indicator
    premium_badge = ""
    is_premium = job.get("is_premium", False)
    if is_premium:
        premium_badge = " 💎"

    urgent_badge = ""
    if is_urgent:
        urgent_badge = " 🚨"  # Emergency/urgent indicator

    # Matching score badge color - boosted scores may be higher
    is_boosted = matching.get("is_boosted", False)
    if score >= 80:
        score_badge = f":green[**{score}%**]"
    elif score >= 60:
        score_badge = f":orange[**{score}%**]"
    else:
        score_badge = f":gray[{score}%]"

    # Add boost indicator if score was boosted
    if is_boosted:
        score_badge += " ↗️"

    applied_mark = " :white_check_mark:" if is_applied else ""

    st.markdown(
        f"**{type_emoji} {type_label}{applied_mark}{premium_badge}{urgent_badge}** &nbsp; {score_badge}"
    )

    # Core info (2-line compact)
    st.caption(
        f"📍 {job.get('region', '-')} &nbsp;|&nbsp; "
        f"📆 {job['date']}"
    )
    st.markdown(f"**₩{int(float(job['hourly_rate'])):,}** / 시간")

    # Memo (only when present, 1-line truncate)
    if job.get("description"):
        desc = job["description"]
        st.caption(desc[:40] + "..." if len(desc) > 40 else desc)

    # Detail expander
    with st.expander("상세 보기"):
        breakdown = matching.get("breakdown", {})
        if breakdown:
            st.caption(
                f"지역 {breakdown.get('region', 0)}점 | "
                f"경력 {breakdown.get('experience', 0)}점 | "
                f"자격 {breakdown.get('certifications', 0)}점 | "
                f"시급 {breakdown.get('hourly_rate', 0)}점"
            )

        # v3.0 Phase 2: Show boost info if applicable
        if is_boosted:
            original_score = matching.get("original_score", score)
            st.info(f"💎 프리미엄 부스트 적용: {original_score}% → {score}% (+30%)")
        elif is_premium:
            st.info("💎 프리미엄 스튜디오")

        # v3.0 Phase 2: Show urgent status
        if is_urgent:
            st.warning("🚨 긴급 매칭 - 24시간 내 수업 (프리미엄 회원 전용)")
        st.caption(
            f"시간: {job.get('start_time', '-')} ~ {job.get('end_time', '-')}"
        )

    # Buttons at card bottom
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
                with st.spinner("지원서를 제출하는 중..."):
                    client.apply_to_job(job["id"])
                st.success("지원 완료! 스튜디오 응답을 기다려주세요.")
                time.sleep(1)
                st.rerun()
            except APIError as e:
                if "ALREADY_APPLIED" in str(e.code):
                    st.warning("이미 지원한 공고입니다.")
                    st.rerun()
                # v3.0: Profile completeness check replaces deposit check
                elif "INCOMPLETE_PROFILE" in str(e.code):
                    st.warning(f"프로필 미완성: {e.message}")
                    st.info("프로필 페이지로 이동합니다...")
                    time.sleep(2)
                    st.session_state.page = "profile"
                    st.rerun()
                # v3.0 Phase 2: Application limit for Free tier
                elif "APPLICATION_LIMIT" in str(e.code):
                    st.error(f"{e.message}")
                    st.info("💎 프리미엄으로 업그레이드하면 무제한 지원이 가능합니다!")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("프리미엄 업그레이드", type="primary", use_container_width=True):
                            st.session_state.page = "profile"
                            st.session_state.show_upgrade_modal = True
                            st.rerun()
                else:
                    st.error(f"오류: {e.message}")

    st.markdown("---")


def render_create_job_step():
    """Render job posting creation UI for studios."""
    st.header("2단계: 공고 등록")
    st.caption("3클릭 + 1줄이면 끝!")

    client = get_client()

    # Initialize variables
    category = st.session_state.get("job_category", "pilates")
    job_type = st.session_state.get("job_type", "substitute")
    if "job_region" not in st.session_state:
        st.session_state.job_region = "강남"

    # Two-column layout
    main_col1, main_col2 = st.columns(2)

    with main_col1:
        # 1. Category selection (buttons)
        st.subheader("1. 종목")
        col1, col2 = st.columns(2)
        with col1:
            pilates_selected = st.button(
                "필라테스",
                use_container_width=True,
                type="primary" if st.session_state.get("job_category") == "pilates" else "secondary",
            )
            if pilates_selected:
                st.session_state.job_category = "pilates"
                st.rerun()
        with col2:
            yoga_selected = st.button(
                "요가",
                use_container_width=True,
                type="primary" if st.session_state.get("job_category") == "yoga" else "secondary",
            )
            if yoga_selected:
                st.session_state.job_category = "yoga"
                st.rerun()

        # 2. Type selection (buttons)
        st.subheader("2. 유형")
        col1, col2, col3 = st.columns(3)
        with col1:
            sub_selected = st.button(
                "대타 (1회)",
                use_container_width=True,
                type="primary" if st.session_state.get("job_type") == "substitute" else "secondary",
            )
            if sub_selected:
                st.session_state.job_type = "substitute"
                st.rerun()
        with col2:
            reg_selected = st.button(
                "정규 (주기적)",
                use_container_width=True,
                type="primary" if st.session_state.get("job_type") == "regular" else "secondary",
            )
            if reg_selected:
                st.session_state.job_type = "regular"
                st.rerun()
        with col3:
            con_selected = st.button(
                "계약 (장기)",
                use_container_width=True,
                type="primary" if st.session_state.get("job_type") == "contract" else "secondary",
            )
            if con_selected:
                st.session_state.job_type = "contract"
                st.rerun()

        # 3. Region selection + map
        st.subheader("3. 지역")
        regions = list(SEOUL_REGIONS.keys())
        st.session_state.job_region = st.selectbox(
            "서울 지역 선택",
            regions,
            index=(
                regions.index(st.session_state.job_region)
                if st.session_state.job_region in regions
                else 0
            ),
            label_visibility="collapsed",
        )
        render_kakao_map(st.session_state.job_region, height=200)

    with main_col2:
        # 4. Hourly rate presets
        st.subheader("4. 시급")
        rate_cols = st.columns(2)
        for i, (rate, label) in enumerate(RATE_PRESETS[:4]):
            with rate_cols[i % 2]:
                if st.button(
                    label,
                    key=f"rate_{rate}",
                    use_container_width=True,
                    type="primary" if st.session_state.get("job_rate") == rate else "secondary",
                ):
                    st.session_state.job_rate = rate
                    st.rerun()

        hourly_rate = st.session_state.get("job_rate", 50000)
        st.caption(f"선택: ₩{hourly_rate:,}/시간")

        # 5. Date/time
        st.subheader("5. 언제")
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("날짜")
        with col2:
            start_time = st.time_input("시작", value=None)
        with col3:
            end_time = st.time_input("종료", value=None)

        # 6. One-line memo (optional)
        st.subheader("6. 한 줄 메모 (선택)")
        memo = st.text_input(
            "",
            placeholder="예: 리포머 수업, 초급자 대상, 주차 가능",
            label_visibility="collapsed",
        )

    st.markdown("---")

    # Auto-generated title preview
    type_labels = {"substitute": "대타", "regular": "정규", "contract": "계약"}
    auto_title = (
        f"[{type_labels[job_type]}] {st.session_state.job_region}구 "
        f"{'필라테스' if category == 'pilates' else '요가'} 강사"
    )
    if memo:
        auto_title += f" - {memo}"

    st.info(f"공고 제목: {auto_title}")

    # Register button
    if st.button("공고 등록하기", type="primary", use_container_width=True):
        try:
            with st.spinner("공고를 등록하는 중..."):
                client.create_job_post(
                    {
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
                    }
                )
            st.success("공고가 등록되었습니다!")
            # Reset form state
            for key in ["job_category", "job_type", "job_rate", "job_region"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.page = "applicants"
            st.rerun()
        except APIError as e:
            st.error(f"오류: {e.message}")
