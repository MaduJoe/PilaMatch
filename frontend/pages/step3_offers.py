"""
Step 3: Offers management (instructor) and applicant selection (studio)
Uses tabs (instructor) and Master-Detail + @st.dialog (studio) patterns.
"""

import streamlit as st
import pandas as pd
from datetime import date as date_today
from api_client import APIError
from utils.helpers import get_client


def render_offers_step():
    """Render the offers review UI for instructors."""
    st.header("3단계: 오퍼 확인")

    client = get_client()

    try:
        with st.spinner("오퍼를 불러오는 중..."):
            result = client.get_my_offers()
            offers = result.get("items", [])

            # Get existing contracts to filter out offers that already have contracts
            contracts_result = client.get_my_contracts()
            existing_contract_offer_ids = {
                c.get("offer_id")
                for c in contracts_result.get("items", [])
                if c.get("offer_id")
            }

        # Filter out offers that already have contracts
        offers = [o for o in offers if o["id"] not in existing_contract_offer_ids]

        pending = [o for o in offers if o["status"] == "pending"]
        accepted = [o for o in offers if o["status"] == "accepted"]
        others = [
            o for o in offers if o["status"] not in ("pending", "accepted")
        ]

        # 3 tabs: Pending / Accepted / History
        tab_pending, tab_accepted, tab_history = st.tabs([
            f"📬 대기 중 ({len(pending)})",
            f"✅ 수락됨 ({len(accepted)})",
            f"📋 처리 내역 ({len(others)})",
        ])

        with tab_pending:
            if pending:
                COLS = 2
                for row_start in range(0, len(pending), COLS):
                    row_offers = pending[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, offer in enumerate(row_offers):
                        with cols[col_idx]:
                            _render_pending_offer_card(offer, client)
            else:
                st.info(
                    "아직 받은 오퍼가 없습니다. "
                    "공고에 지원하면 스튜디오에서 오퍼를 보냅니다."
                )
                if st.button("일 찾기로 돌아가기"):
                    st.session_state.page = "find_jobs"
                    st.rerun()

        with tab_accepted:
            if accepted:
                COLS = 2
                for row_start in range(0, len(accepted), COLS):
                    row_offers = accepted[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, offer in enumerate(row_offers):
                        with cols[col_idx]:
                            _render_accepted_offer_card(offer, client)
            else:
                st.caption("수락된 오퍼가 없습니다.")

        with tab_history:
            if others:
                _render_offer_history_table(others, existing_contract_offer_ids)
            else:
                st.caption("처리된 오퍼 내역이 없습니다.")

    except APIError as e:
        st.error(f"오퍼 로드 실패: {e.message}")


def _render_pending_offer_card(offer: dict, client) -> None:
    """Render a single pending offer card with accept/reject buttons."""
    st.markdown(f"**제안 시급: ₩{int(float(offer['proposed_rate'])):,}**")

    # Show full message directly (no expander)
    if offer.get("message"):
        st.caption(offer["message"])

    # Accept / Reject buttons
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button(
            "수락",
            key=f"accept_{offer['id']}",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("오퍼를 수락하는 중..."):
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
                with st.spinner("오퍼를 거절하는 중..."):
                    client.reject_offer(offer["id"])
                st.info("오퍼를 거절했습니다.")
                st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")
    st.markdown("---")


def _render_accepted_offer_card(offer: dict, client) -> None:
    """Render an accepted offer card with contract creation button."""
    st.markdown(f"**시급: ₩{int(float(offer['proposed_rate'])):,}**")
    st.caption("수락 완료 - 계약을 생성하세요")
    if st.button(
        "계약 생성",
        key=f"contract_{offer['id']}",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("계약을 생성하는 중..."):
                client.create_contract_from_offer(offer["id"])
            st.success("계약이 생성되었습니다!")
            st.session_state.page = "contracts"
            st.rerun()
        except APIError as e:
            st.error(f"오류: {e.message}")
    st.markdown("---")


def _render_offer_history_table(others: list, existing_contract_offer_ids: set) -> None:
    """Render processed offers as a dataframe table."""
    status_map = {
        "accepted": "수락됨",
        "rejected": "거절됨",
        "expired": "만료됨",
        "cancelled": "취소됨",
    }

    table_data = []
    for offer in others:
        status_label = status_map.get(offer["status"], offer["status"].upper())
        has_contract = "✅" if offer["id"] in existing_contract_offer_ids else "-"
        msg = (offer.get("message") or "-")[:50]
        table_data.append({
            "상태": status_label,
            "시급": f"₩{int(float(offer['proposed_rate'])):,}",
            "계약": has_contract,
            "메시지": msg,
        })

    st.dataframe(
        pd.DataFrame(table_data),
        hide_index=True,
        use_container_width=True,
        height=min(400, 50 + len(table_data) * 35),
    )


def render_applicants_step():
    """Render the applicant selection UI for studios.
    Uses Master-Detail pattern: selectbox for job → applicant cards.
    """
    st.header("3단계: 지원자 선택")

    client = get_client()

    try:
        # Get all job posts
        with st.spinner("공고를 불러오는 중..."):
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

        # Master: selectbox to pick a job
        job_options = []
        for job in jobs:
            app_count = job.get("application_count", 0)
            type_label = {
                "substitute": "대타",
                "regular": "정규",
                "contract": "계약",
            }.get(job.get("job_type", ""), job.get("job_type", ""))

            job_is_past = False
            try:
                job_is_past = date_today.fromisoformat(str(job.get("date", ""))) < date_today.today()
            except (ValueError, TypeError):
                pass
            past_label = " [지난공고]" if job_is_past else ""
            label = f"{job['title']}{past_label} | {job['date']} | 지원자 {app_count}명"
            job_options.append(label)

        selected_idx = st.selectbox(
            "내 공고 선택",
            range(len(jobs)),
            format_func=lambda i: job_options[i],
        )
        selected_job = jobs[selected_idx]

        # Detail: show applicants for selected job
        st.markdown("---")
        type_label = {
            "substitute": "대타",
            "regular": "정규",
            "contract": "계약",
        }.get(selected_job.get("job_type", ""), selected_job.get("job_type", ""))
        st.caption(
            f"유형: {type_label} | "
            f"시급: ₩{int(float(selected_job['hourly_rate'])):,} | "
            f"지역: {selected_job.get('region', '-')}"
        )

        try:
            with st.spinner("지원자를 불러오는 중..."):
                result = client.get_job_post_applications(selected_job["id"])
            applications = result.get("items", [])

            if not applications:
                st.info("아직 지원자가 없습니다.")
            else:
                st.subheader(f"지원자 ({len(applications)}명)")
                # 2-column applicant cards
                COLS = 2
                for row_start in range(0, len(applications), COLS):
                    row_apps = applications[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, app in enumerate(row_apps):
                        with cols[col_idx]:
                            _render_applicant_card(app, client)

        except APIError as e:
            st.error(f"지원자 정보를 불러올 수 없습니다: {e.message}")

    except APIError as e:
        st.error(f"로드 실패: {e.message}")


@st.dialog("오퍼 보내기")
def _send_offer_dialog(app_id: str, instructor_name: str, client):
    """Dialog modal for sending an offer to an applicant."""
    st.markdown(f"**{instructor_name}** 강사에게 오퍼를 보냅니다.")
    proposed_rate = st.number_input(
        "제안 시급 (원)",
        min_value=0,
        step=5000,
        value=50000,
    )
    message = st.text_area(
        "메시지 (선택)",
        placeholder="근무 조건을 자유롭게 작성하세요.",
        height=80,
    )
    if st.button("오퍼 전송", type="primary", use_container_width=True):
        try:
            with st.spinner("오퍼를 전송하는 중..."):
                client.create_offer({
                    "application_id": app_id,
                    "proposed_rate": proposed_rate,
                    "message": message,
                })
            st.success(f"{instructor_name} 강사에게 오퍼를 전송했습니다!")
            st.rerun()
        except APIError as e:
            st.error(f"오류: {e.message}")


def _render_applicant_card(app: dict, client) -> None:
    """Render a single applicant card with offer dialog trigger."""
    instructor_name = app.get("instructor_name", "강사")
    exp_years = app.get("instructor_experience_years", 0)
    rating = app.get("instructor_rating")

    st.markdown(f"**{instructor_name}** (경력 {exp_years}년)")

    if rating:
        st.caption(f"평점: {rating:.1f} / 5.0")

    # Show full cover letter (no expander)
    if app.get("cover_letter"):
        st.caption(app["cover_letter"])

    # Offer status display
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

    # Send offer button → opens dialog modal
    if app["status"] == "pending" and not app.get("has_offer"):
        if st.button(
            "오퍼 보내기",
            key=f"offer_{app['id']}",
            type="primary",
            use_container_width=True,
        ):
            _send_offer_dialog(app["id"], instructor_name, client)

    st.markdown("---")
