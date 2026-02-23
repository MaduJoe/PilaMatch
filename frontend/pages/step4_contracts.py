"""
Step 4: Contract management - signing, progress tracking, completion
Uses @st.dialog modals for signing, cancellation, and no-show reporting.
"""

from datetime import datetime, date
import time
import streamlit as st
import pandas as pd
from api_client import APIError
from utils.helpers import get_client
from utils.constants import CONTRACT_TERMS
from components import render_toss_payment_widget


def render_contracts_step():
    """Render active contract management for both instructors and studios."""
    st.header("4단계: 계약 진행")
    st.caption("진행 중인 계약을 관리하고 수업 완료를 확인하세요.")

    client = get_client()
    user = st.session_state.user

    try:
        with st.spinner("계약을 불러오는 중..."):
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

            for contract in active:
                with st.container():
                    _render_contract_card(contract, user, client)

        # Completed/cancelled contracts (table format)
        if completed:
            st.subheader(f"완료/취소된 계약 ({len(completed)})")
            _render_completed_contracts_table(completed, user)

    except APIError as e:
        st.error(f"계약 로드 실패: {e.message}")


def _render_contract_card(contract: dict, user: dict, client) -> None:
    """Render a single active contract card."""
    role = user.get("role")
    status = contract["status"]

    # Determine partner name prominently
    if role == "instructor":
        partner_name = contract.get("studio_name") or "스튜디오"
        partner_label = "스튜디오"
    else:
        partner_name = contract.get("instructor_name") or "강사"
        partner_label = "강사"

    # Status config
    status_emoji = {
        "confirmed": "📝",
        "in_progress": "🏃",
        "pending_completion": "⏳",
    }.get(status, "📋")
    status_label = {
        "confirmed": "서명 대기",
        "in_progress": "진행 중",
        "pending_completion": "완료 대기",
    }.get(status, status)

    # Time info for header
    time_str = ""
    if contract.get("start_time"):
        try:
            start = datetime.strptime(contract["start_time"], "%H:%M:%S")
            time_str = f" {start.strftime('%H:%M')}"
        except Exception:
            pass

    # Header: partner name + date + status (most important info at a glance)
    st.markdown(
        f"### {status_emoji} {partner_name}  \n"
        f":gray[{contract['date']}{time_str} · {status_label}]"
    )

    # Compact contract details
    with st.container():
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            if contract.get("start_time") and contract.get("end_time"):
                try:
                    start = datetime.strptime(contract["start_time"], "%H:%M:%S")
                    end = datetime.strptime(contract["end_time"], "%H:%M:%S")
                    duration = (end - start).total_seconds() / 3600
                    start_formatted = start.strftime("%H:%M")
                    end_formatted = end.strftime("%H:%M")
                    duration_display = f"{duration:.2f}".rstrip('0').rstrip('.')
                    st.caption(f"수업: **{duration_display}시간** ({start_formatted} ~ {end_formatted})")
                except Exception:
                    st.caption(f"시간: {contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}")
            st.caption(f"{partner_label}: **{partner_name}**")

        with detail_col2:
            hourly_rate = contract.get("hourly_rate", 0)
            total_amount = float(contract.get("total_amount", 0))
            st.caption(f"시급: **₩{int(float(hourly_rate)):,}**")
            st.caption(f"총액: **₩{int(total_amount):,}**")

    st.markdown("---")

    if status == "confirmed":
        _render_signing_section(contract, role, client)
    elif status == "in_progress":
        _render_in_progress_section(contract, user, client)
        # Studio: show payment section during in_progress too
        if role == "studio":
            st.markdown("---")
            _render_contract_payment_section(contract, client)
    elif status == "pending_completion":
        _render_pending_completion_section(contract, role, client)
        # Studio: show payment section during pending_completion too
        if role == "studio":
            st.markdown("---")
            _render_contract_payment_section(contract, client)


@st.dialog("계약 서명")
def _sign_contract_dialog(contract_id: str, other_signed: bool, other_party: str, client):
    """Dialog modal for contract signing with terms agreement."""
    st.markdown(CONTRACT_TERMS)
    agree = st.checkbox("위 약속 사항에 동의합니다")
    if agree:
        btn_text = "서명하고 계약 시작하기" if other_signed else "서명하기"
        if st.button(btn_text, type="primary", use_container_width=True):
            try:
                with st.spinner("서명을 처리하는 중..."):
                    client.set_contract_in_progress(contract_id)
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


@st.dialog("계약 취소")
def _cancel_contract_dialog(contract_id: str, client):
    """Dialog modal for contract cancellation with reason input."""
    st.warning("계약을 취소하시겠습니까?")
    st.caption("약관에 따라 페널티가 적용될 수 있습니다.")
    reason = st.text_input("취소 사유")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("취소 확정", type="primary", use_container_width=True):
            try:
                with st.spinner("취소를 처리하는 중..."):
                    client.cancel_contract(contract_id, reason or "취소")
                st.warning("취소 처리되었습니다.")
                st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")
    with c2:
        if st.button("돌아가기", use_container_width=True):
            st.rerun()


@st.dialog("불참 신고")
def _noshow_report_dialog(contract_id: str, reported_id: str, report_msg: str, client):
    """Dialog modal for no-show reporting."""
    st.warning(report_msg)
    st.caption("노쇼 신고 시 24시간 내 이의제기가 없으면 패널티가 적용됩니다.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("노쇼 신고", type="primary", use_container_width=True):
            try:
                with st.spinner("신고를 접수하는 중..."):
                    client.report_no_show(contract_id, reported_id)
                st.warning("신고가 접수되었습니다. 상대방에게 24시간 이의제기 기간이 부여됩니다.")
                st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")
    with c2:
        if st.button("돌아가기", use_container_width=True):
            st.rerun()


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
        # "서명하기" button opens modal dialog
        if st.button(
            "서명하기",
            key=f"sign_{contract['id']}",
            type="primary",
            use_container_width=True,
        ):
            _sign_contract_dialog(contract["id"], other_signed, other_party, client)


def _render_contract_payment_section(contract: dict, client) -> None:
    """Render payment widget for studio to pay for a confirmed contract."""
    contract_id = contract["id"]
    total_amount = float(contract.get("total_amount", 0))
    st.subheader("계약금 결제")
    st.caption(f"계약금 ₩{int(total_amount):,} + 플랫폼 수수료 5%를 결제해주세요.")

    payment_key = f"contract_payment_{contract_id}"
    auto_pay = st.session_state.pop(f"auto_pay_{contract_id}", False)

    # Check if payment order already initialized
    if payment_key not in st.session_state:
        # Auto-initialize payment if triggered by "수업 완료" button
        if auto_pay:
            try:
                with st.spinner("결제를 준비하는 중..."):
                    result = client.initialize_payment(contract_id)
                st.session_state[payment_key] = {
                    "order_id": result["order_id"],
                    "amount": int(float(result["amount"])),
                    "order_name": result.get("order_name", f"계약 {contract_id[:8]}"),
                }
                st.rerun()
            except APIError as e:
                st.error(f"결제 준비 실패: {e.message}")

        if st.button(
            "계약금 결제하기",
            key=f"init_pay_{contract_id}",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("결제를 준비하는 중..."):
                    result = client.initialize_payment(contract_id)
                st.session_state[payment_key] = {
                    "order_id": result["order_id"],
                    "amount": int(float(result["amount"])),
                    "order_name": result.get("order_name", f"계약 {contract_id[:8]}"),
                }
                st.rerun()
            except APIError as e:
                st.error(f"결제 준비 실패: {e.message}")
    else:
        import os
        order_data = st.session_state[payment_key]
        order_id = order_data["order_id"]
        toss_client_key = os.getenv("TOSS_CLIENT_KEY", "")

        # Check if mock payment completed
        completed = st.session_state.get(f"payment_completed_{order_id}")
        if completed:
            try:
                with st.spinner("결제를 확인하는 중..."):
                    client.confirm_payment(
                        completed["payment_key"],
                        completed["order_id"],
                        completed["amount"],
                    )
                st.success("계약금 결제가 완료되었습니다!")
                st.session_state.pop(payment_key, None)
                st.session_state.pop(f"payment_completed_{order_id}", None)
                time.sleep(1)
                st.rerun()
            except APIError as e:
                st.error(f"결제 확인 실패: {e.message}")
                st.session_state.pop(f"payment_completed_{order_id}", None)

        elif st.session_state.get(f"payment_cancelled_{order_id}"):
            st.session_state.pop(payment_key, None)
            st.session_state.pop(f"payment_cancelled_{order_id}", None)
            st.rerun()
        else:
            user = st.session_state.user
            render_toss_payment_widget(
                client_key=toss_client_key,
                order_id=order_id,
                order_name=order_data["order_name"],
                amount=order_data["amount"],
                customer_key=str(user.get("id", "guest")),
                payment_type="contract",
            )
            if st.button("결제 취소", key=f"cancel_contract_pay_{contract_id}"):
                st.session_state.pop(payment_key, None)
                st.rerun()


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

    role = user.get("role")
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button(
            "수업 완료",
            key=f"complete_{contract['id']}",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner("완료를 처리하는 중..."):
                    client.complete_contract(contract["id"])
                st.success("완료 확인! 상대방도 확인하면 정산이 진행됩니다.")
                if role == "studio":
                    # Studio: auto-initialize payment after completion
                    st.session_state[f"auto_pay_{contract['id']}"] = True
                    st.rerun()
                else:
                    # Instructor: go to review tab
                    st.session_state.page = "complete"
                    st.session_state["complete_tab"] = "review"
                    st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")

    with action_col2:
        if st.button(
            "취소",
            key=f"cancel_btn_{contract['id']}",
            use_container_width=True,
        ):
            _cancel_contract_dialog(contract["id"], client)

    with action_col3:
        # Determine reported party
        if user.get("role") == "studio":
            reported_id = contract.get("instructor_id", "")
            report_msg = "강사가 수업에 불참했나요?"
        else:
            reported_id = contract.get("studio_id", "")
            report_msg = "스튜디오에서 수업을 진행하지 않았나요?"

        if st.button(
            "불참 신고",
            key=f"noshow_btn_{contract['id']}",
            use_container_width=True,
        ):
            _noshow_report_dialog(contract["id"], reported_id, report_msg, client)


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
                with st.spinner("완료를 처리하는 중..."):
                    client.complete_contract(contract["id"])
                st.success("완료 확인되었습니다! 상대방도 확인하면 정산이 진행됩니다.")
                if role == "studio":
                    # Studio: auto-initialize payment after completion
                    st.session_state[f"auto_pay_{contract['id']}"] = True
                    st.rerun()
                else:
                    st.session_state.page = "complete"
                    st.session_state["complete_tab"] = "review"
                    st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")


def _render_completed_contracts_table(contracts: list, user: dict) -> None:
    """Render completed/cancelled contracts as an interactive table."""
    if not contracts:
        return

    # Prepare data for the table
    table_data = []

    for contract in contracts:
        # Status and label
        status = contract["status"]
        status_label = "✅ 완료" if status == "completed" else "❌ 취소"

        # Get partner name based on user role
        if user.get("role") == "instructor":
            partner_name = contract.get("studio_name") or "스튜디오"
        else:
            partner_name = contract.get("instructor_name") or "강사"

        # Format date and time
        contract_date = contract.get("date", "-")
        start_time = contract.get("start_time", "-")
        end_time = contract.get("end_time", "-")

        # Calculate duration and format class time
        class_time = "-"
        if start_time != "-" and end_time != "-":
            try:
                start_dt = datetime.strptime(start_time, "%H:%M:%S")
                end_dt = datetime.strptime(end_time, "%H:%M:%S")
                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                start_formatted = start_dt.strftime("%H:%M")
                duration_display = f"{duration_hours:.2f}".rstrip('0').rstrip('.')
                class_time = f"{start_formatted} ({duration_display}시간)"
            except (ValueError, TypeError):
                class_time = f"{start_time[:5] if len(start_time) > 5 else start_time}"
        else:
            class_time = "-"

        # Calculate amounts
        total_amount = float(contract.get("total_amount", 0))
        platform_fee = total_amount * 0.05
        settlement = total_amount - platform_fee if status == "completed" else 0

        # Add to table data
        table_data.append({
            "상태": status_label,
            "상대방": partner_name,
            "날짜": contract_date,
            "클래스 시간": class_time,
            "계약금액": f"₩{int(total_amount):,}",
            "정산금액": f"₩{int(settlement):,}" if status == "completed" else "-",
        })

    # Sort by date (most recent first)
    table_data.sort(key=lambda x: x["날짜"], reverse=True)

    # Display the table
    st.dataframe(
        pd.DataFrame(table_data),
        hide_index=True,
        use_container_width=True,
        height=min(400, 50 + len(table_data) * 35),
    )

    # Summary statistics
    st.markdown("---")
    completed_count = len([c for c in table_data if "완료" in c["상태"]])
    cancelled_count = len([c for c in table_data if "취소" in c["상태"]])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 계약", len(table_data))
    with col2:
        st.metric("완료", completed_count)
    with col3:
        st.metric("취소", cancelled_count)
