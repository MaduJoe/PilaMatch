"""
Step 3: Offers management (instructor) and applicant selection (studio)
"""

import streamlit as st
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

            with st.expander(
                f"**{job['title']}** | {job['date']} | 지원자 {app_count}명",
                expanded=(app_count > 0),
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

        # Offer form section - rendered below applicant list
        if st.session_state.get("show_offer_modal"):
            _render_offer_form(client)

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

    # Send offer button
    if app["status"] == "pending" and not app.get("has_offer"):
        already_open = (
            st.session_state.get("show_offer_modal")
            and st.session_state.get("selected_application", {}).get("id")
            == app["id"]
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


def _render_offer_form(client) -> None:
    """Render the offer creation form anchored below the applicant list."""
    app = st.session_state.selected_application
    instructor_name = app.get("instructor_name", "강사")

    # Auto-scroll anchor
    scroll_key = st.session_state.get("offer_scroll_trigger", 0)
    st.markdown(
        f"""
        <div id="offer-form-anchor" data-scroll-key="{scroll_key}"></div>
        <script>
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

    st.info(
        f"**{instructor_name}** 강사에게 오퍼를 작성 중입니다. "
        "아래 양식을 작성한 후 오퍼를 전송하세요.",
        icon="✏️",
    )

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
                    with st.spinner("오퍼를 전송하는 중..."):
                        client.create_offer(
                            {
                                "application_id": app["id"],
                                "proposed_rate": proposed_rate,
                                "message": message,
                            }
                        )
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
            if st.form_submit_button("취소", use_container_width=True):
                st.session_state.show_offer_modal = False
                st.session_state.selected_application = None
                st.rerun()
