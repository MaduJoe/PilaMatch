"""
Step 4: Contract management - signing, progress tracking, completion
"""

from datetime import datetime, date
import streamlit as st
from api_client import APIError
from utils.helpers import get_client
from utils.constants import CONTRACT_TERMS


def render_contracts_step():
    """Render active contract management for both instructors and studios."""
    st.header("4단계: 계약 진행")
    st.caption("진행 중인 계약을 관리하고 수업 완료를 확인하세요.")

    client = get_client()
    user = st.session_state.user

    try:
        result = client.get_my_contracts()
        contracts = result.get("items", [])

        active = [
            c
            for c in contracts
            if c["status"] in ["confirmed", "in_progress", "pending_completion"]
        ]
        completed = [
            c for c in contracts if c["status"] in ["completed", "cancelled"]
        ]

        if not contracts:
            st.info("아직 계약이 없습니다.")
            st.caption("강사: 오퍼 수락 후 계약이 생성됩니다.")
            st.caption("스튜디오: 강사가 오퍼를 수락하면 계약이 생성됩니다.")
            return

        # Active contracts: 2-column cards
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

        # Completed/cancelled contracts (expander, 2-column summary)
        if completed:
            with st.expander(f"완료/취소된 계약 ({len(completed)})"):
                COLS = 2
                for row_start in range(0, len(completed), COLS):
                    row_contracts = completed[row_start : row_start + COLS]
                    cols = st.columns(COLS)
                    for col_idx, contract in enumerate(row_contracts):
                        with cols[col_idx]:
                            _render_completed_contract_summary(contract)

    except APIError as e:
        st.error(f"계약 로드 실패: {e.message}")


def _render_contract_card(contract: dict, user: dict, client) -> None:
    """Render a single active contract card."""
    role = user.get("role")
    status = contract["status"]

    # Status badge
    status_emoji = {
        "confirmed": "",
        "in_progress": "",
        "pending_completion": "",
    }.get(status, "")
    status_label = {
        "confirmed": "서명 대기",
        "in_progress": "진행 중",
        "pending_completion": "완료 대기",
    }.get(status, status)

    st.markdown(f"### {status_emoji} {status_label}")
    st.caption(f"계약 ID: {contract['id'][:8]}...")

    # Contract party info box
    with st.container():
        st.markdown("**계약 상세 정보**")

        party_col1, party_col2 = st.columns(2)
        with party_col1:
            st.markdown("**강사 정보**")
            instructor_id = contract.get("instructor_id", "-")
            st.caption(f"강사 ID: {str(instructor_id)[:8]}...")
            if contract.get("instructor_name"):
                st.caption(f"이름: {contract['instructor_name']}")

        with party_col2:
            st.markdown("**스튜디오 정보**")
            studio_id = contract.get("studio_id", "-")
            st.caption(f"스튜디오 ID: {str(studio_id)[:8]}...")
            if contract.get("studio_name"):
                st.caption(f"이름: {contract['studio_name']}")

        st.markdown("---")

        # Contract terms (2-column)
        st.markdown("**계약 조건**")
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.caption(f"날짜: **{contract['date']}**")
            st.caption(
                f"시간: **{contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}**"
            )
            if contract.get("start_time") and contract.get("end_time"):
                try:
                    start = datetime.strptime(contract["start_time"], "%H:%M:%S")
                    end = datetime.strptime(contract["end_time"], "%H:%M:%S")
                    duration = (end - start).total_seconds() / 3600
                    st.caption(f"수업 시간: **{duration:.1f}시간**")
                except Exception:
                    pass

        with detail_col2:
            hourly_rate = contract.get("hourly_rate", 0)
            total_amount = float(contract.get("total_amount", 0))
            st.caption(f"시급: **₩{int(float(hourly_rate)):,}**")
            st.caption(f"총액: **₩{int(total_amount):,}**")
            platform_fee = total_amount * 0.05
            settlement = total_amount - platform_fee
            st.caption(f"정산금: **₩{int(settlement):,}** (수수료 5%)")

    st.markdown("---")

    if status == "confirmed":
        _render_signing_section(contract, role, client)
    elif status == "in_progress":
        _render_in_progress_section(contract, user, client)
    elif status == "pending_completion":
        _render_pending_completion_section(contract, role, client)


def _render_signing_section(contract: dict, role: str, client) -> None:
    """Render the contract signing UI for 'confirmed' status contracts."""
    if role == "instructor":
        my_signed = contract.get("instructor_signed_at") is not None
        other_signed = contract.get("studio_signed_at") is not None
        other_party = "스튜디오"
    else:
        my_signed = contract.get("studio_signed_at") is not None
        other_signed = contract.get("instructor_signed_at") is not None
        other_party = "강사"

    # Signature status badges (2-column)
    sig_col1, sig_col2 = st.columns(2)
    with sig_col1:
        if role == "instructor":
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
        if role == "instructor":
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
        if other_signed:
            st.info(f"{other_party}가 서명했습니다. 서명을 완료해주세요.")
        with st.expander("약관 확인 후 서명"):
            st.markdown(CONTRACT_TERMS)
            agree = st.checkbox(
                "위 약속 사항에 동의합니다",
                key=f"agree_{contract['id']}",
            )
            if agree:
                btn_text = (
                    "서명하고 계약 시작하기" if other_signed else "서명하기"
                )
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
                            st.success(
                                f"서명 완료. {other_party}의 서명을 기다리고 있습니다."
                            )
                        st.rerun()
                    except APIError as e:
                        if "Already signed" in str(e):
                            st.warning("이미 서명하셨습니다.")
                        else:
                            st.error(f"오류: {e.message}")


def _render_in_progress_section(contract: dict, user: dict, client) -> None:
    """Render the active contract UI for 'in_progress' status contracts."""
    st.success("계약 체결 완료! 수업을 진행해주세요.")

    with st.container():
        st.markdown("**수업 진행 정보**")
        progress_col1, progress_col2 = st.columns(2)
        with progress_col1:
            contract_date = contract.get("date", "")
            try:
                c_date = datetime.strptime(contract_date, "%Y-%m-%d").date()
                today = date.today()
                if c_date == today:
                    st.info("오늘 수업입니다!")
                elif c_date < today:
                    st.warning("수업일이 지났습니다")
                else:
                    days_left = (c_date - today).days
                    st.caption(f"수업까지 {days_left}일 남음")
            except Exception:
                pass

        with progress_col2:
            st.caption("수업 완료 후 '수업 완료' 버튼을 클릭해주세요")
            st.caption("양측 모두 완료 확인 시 정산됩니다")

    st.markdown("---")

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button(
            "수업 완료",
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

    # Cancel form (expander)
    if st.session_state.get(f"show_cancel_{contract['id']}"):
        with st.expander("취소 사유 입력", expanded=True):
            with st.form(key=f"cancel_form_{contract['id']}"):
                reason = st.text_input("취소 사유")
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("취소 확정", use_container_width=True):
                        try:
                            client.cancel_contract(contract["id"], reason or "취소")
                            st.warning(
                                "취소 처리되었습니다. "
                                "약관에 따라 페널티가 적용될 수 있습니다."
                            )
                            st.session_state[f"show_cancel_{contract['id']}"] = False
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")
                with c2:
                    if st.form_submit_button("돌아가기", use_container_width=True):
                        st.session_state[f"show_cancel_{contract['id']}"] = False

    # No-show report form (expander)
    if st.session_state.get(f"show_noshow_{contract['id']}"):
        with st.expander("노쇼 신고", expanded=True):
            with st.form(key=f"noshow_form_{contract['id']}"):
                user = st.session_state.user
                if user.get("role") == "studio":
                    reported_id = contract.get("instructor_id", "")
                    report_msg = "강사가 수업에 불참했나요?"
                else:
                    reported_id = contract.get("studio_id", "")
                    report_msg = "스튜디오에서 수업을 진행하지 않았나요?"
                st.warning(report_msg)
                st.caption(
                    "노쇼 신고 시 24시간 내 이의제기가 없으면 패널티가 적용됩니다."
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button(
                        "노쇼 신고", type="primary", use_container_width=True
                    ):
                        try:
                            client.report_no_show(contract["id"], reported_id)
                            st.warning(
                                "신고가 접수되었습니다. "
                                "상대방에게 24시간 이의제기 기간이 부여됩니다."
                            )
                            st.session_state[f"show_noshow_{contract['id']}"] = False
                            st.rerun()
                        except APIError as e:
                            st.error(f"오류: {e.message}")
                with c2:
                    if st.form_submit_button("돌아가기", use_container_width=True):
                        st.session_state[f"show_noshow_{contract['id']}"] = False


def _render_pending_completion_section(
    contract: dict, role: str, client
) -> None:
    """Render the completion confirmation UI for 'pending_completion' contracts."""
    studio_confirmed = contract.get("studio_confirmed_at") is not None
    instructor_confirmed = contract.get("instructor_confirmed_at") is not None

    # Completion status badges (2-column)
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


def _render_completed_contract_summary(contract: dict) -> None:
    """Render a compact summary card for completed or cancelled contracts."""
    status_emoji = {"completed": "", "cancelled": ""}.get(
        contract["status"], ""
    )
    status_label = {"completed": "완료", "cancelled": "취소"}.get(
        contract["status"], contract["status"]
    )
    st.markdown(f"### {status_emoji} {status_label}")

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.caption(f"📅 {contract['date']}")
        st.caption(
            f"⏰ {contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}"
        )
    with info_col2:
        total_amount = float(contract.get("total_amount", 0))
        st.caption(f"💰 ₩{int(total_amount):,}")

        if contract["status"] == "completed":
            platform_fee = total_amount * 0.05
            settlement = total_amount - platform_fee
            st.caption(f"정산: ₩{int(settlement):,}")
        elif (
            contract["status"] == "cancelled"
            and contract.get("cancellation_reason")
        ):
            st.caption(f"사유: {contract['cancellation_reason'][:20]}...")

    st.markdown("---")
