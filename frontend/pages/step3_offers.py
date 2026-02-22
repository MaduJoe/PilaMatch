"""
Step 3: Offers management (instructor) and applicant selection (studio)
"""

import streamlit as st
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

        # Pending offers: 2-column cards
        if pending:
            st.subheader(f"수락/거절 대기 중 ({len(pending)})")
            COLS = 2
            for row_start in range(0, len(pending), COLS):
                row_offers = pending[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, offer in enumerate(row_offers):
                    with cols[col_idx]:
                        _render_pending_offer_card(offer, client)

        # Accepted offers awaiting contract creation: 2-column
        if accepted:
            st.subheader(f"계약 생성 대기 ({len(accepted)})")
            COLS = 2
            for row_start in range(0, len(accepted), COLS):
                row_offers = accepted[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, offer in enumerate(row_offers):
                    with cols[col_idx]:
                        _render_accepted_offer_card(offer, client)

        if not pending and not accepted:
            st.info(
                "아직 받은 오퍼가 없습니다. "
                "공고에 지원하면 스튜디오에서 오퍼를 보냅니다."
            )
            if st.button("일 찾기로 돌아가기"):
                st.session_state.page = "find_jobs"
                st.rerun()

        # Processed offer history (expander)
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
                            status_label = status_map.get(
                                offer["status"], offer["status"].upper()
                            )
                            st.markdown(
                                f"**{status_label}** - "
                                f"₩{int(float(offer['proposed_rate'])):,}/시간"
                            )
                            if offer["id"] in existing_contract_offer_ids:
                                st.caption("계약 생성됨 (계약 내역에서 확인)")
                            if offer.get("message"):
                                st.caption(offer["message"][:50])
                            st.markdown("---")

    except APIError as e:
        st.error(f"오퍼 로드 실패: {e.message}")


def _render_pending_offer_card(offer: dict, client) -> None:
    """Render a single pending offer card with accept/reject buttons."""
    st.markdown(f"**제안 시급: ₩{int(float(offer['proposed_rate'])):,}**")
    if offer.get("message"):
        msg = offer["message"]
        st.caption(msg[:60] + "..." if len(msg) > 60 else msg)

    # Full message expander
    if offer.get("message") and len(offer["message"]) > 60:
        with st.expander("전체 메시지 보기"):
            st.write(offer["message"])

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


def render_applicants_step():
    """Render the applicant selection UI for studios."""
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

        st.subheader("내 공고")

        for job in jobs:
            app_count = job.get("application_count", 0)
            type_label = {
                "substitute": "대타",
                "regular": "정규",
                "contract": "계약",
            }.get(job.get("job_type", ""), job.get("job_type", ""))

            # FB-1: Mark past jobs
            job_is_past = False
            try:
                job_is_past = date_today.fromisoformat(str(job.get("date", ""))) < date_today.today()
            except (ValueError, TypeError):
                pass
            past_label = " [지난공고]" if job_is_past else ""
            with st.expander(
                f"**{job['title']}**{past_label} | {job['date']} | 지원자 {app_count}명",
                expanded=(app_count > 0 and not job_is_past),
            ):
                # Job summary info (1 line)
                st.caption(
                    f"유형: {type_label} | "
                    f"시급: ₩{int(float(job['hourly_rate'])):,} | "
                    f"지역: {job.get('region', '-')}"
                )

                try:
                    with st.spinner("지원자를 불러오는 중..."):
                        result = client.get_job_post_applications(job["id"])
                    applications = result.get("items", [])

                    if not applications:
                        st.caption("아직 지원자가 없습니다.")
                    else:
                        # 2-column applicant cards
                        COLS = 2
                        for row_start in range(0, len(applications), COLS):
                            row_apps = applications[row_start : row_start + COLS]
                            cols = st.columns(COLS)

                            for col_idx, app in enumerate(row_apps):
                                with cols[col_idx]:
                                    _render_applicant_card(app)

                except APIError as e:
                    st.caption(f"지원자 정보를 불러올 수 없습니다: {e.message}")

        # FB-3: Process offer send if triggered
        if st.session_state.get("_offer_send"):
            _process_offer_send(client)

    except APIError as e:
        st.error(f"로드 실패: {e.message}")


def _render_applicant_card(app: dict) -> None:
    """Render a single applicant card."""
    instructor_name = app.get("instructor_name", "강사")
    exp_years = app.get("instructor_experience_years", 0)
    rating = app.get("instructor_rating")

    st.markdown(f"**{instructor_name}** (경력 {exp_years}년)")

    if rating:
        st.caption(f"평점: {rating:.1f} / 5.0")

    if app.get("cover_letter"):
        cl = app["cover_letter"]
        st.caption(cl[:50] + "..." if len(cl) > 50 else cl)
        if len(cl) > 50:
            with st.expander("전체 보기"):
                st.write(cl)

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

    # Send offer button - inline expander (FB-3: no scroll needed)
    if app["status"] == "pending" and not app.get("has_offer"):
        offer_key = f"offer_open_{app['id']}"
        if st.session_state.get(offer_key):
            st.markdown(f"**오퍼 작성 - {instructor_name}**")
            proposed_rate = st.number_input(
                "제안 시급 (원)",
                min_value=0,
                step=5000,
                value=50000,
                key=f"rate_{app['id']}",
            )
            message = st.text_area(
                "메시지 (선택)",
                placeholder="근무 조건을 자유롭게 작성하세요.",
                height=80,
                key=f"msg_{app['id']}",
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("오퍼 전송", type="primary", use_container_width=True, key=f"send_{app['id']}"):
                    st.session_state._offer_send = {
                        "app_id": app["id"],
                        "rate": proposed_rate,
                        "message": message,
                        "name": instructor_name,
                        "key": offer_key,
                    }
            with c2:
                if st.button("취소", use_container_width=True, key=f"cancel_offer_{app['id']}"):
                    st.session_state[offer_key] = False
                    st.rerun()
        else:
            if st.button(
                "오퍼 보내기",
                key=f"offer_{app['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[offer_key] = True
                st.rerun()

    st.markdown("---")


def _process_offer_send(client) -> None:
    """Process the offer send action from inline expander form."""
    data = st.session_state.pop("_offer_send")
    try:
        with st.spinner("오퍼를 전송하는 중..."):
            client.create_offer(
                {
                    "application_id": data["app_id"],
                    "proposed_rate": data["rate"],
                    "message": data["message"],
                }
            )
        st.success(f"{data['name']} 강사에게 오퍼를 전송했습니다!")
        st.session_state[data["key"]] = False
        st.rerun()
    except APIError as e:
        st.error(f"오류: {e.message}")
