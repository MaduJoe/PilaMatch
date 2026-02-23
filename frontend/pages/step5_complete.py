"""
Step 5: Contract completion confirmation and reviews
Uses Master-Detail pattern for review writing and dataframe for received reviews.
"""

import streamlit as st
from api_client import APIError
from utils.helpers import get_client
import pandas as pd
from datetime import datetime


def render_complete_step():
    """Render the completion confirmation and review management UI."""
    st.header("5단계: 완료 & 리뷰")

    # Check if redirected from completion for review
    auto_review = st.session_state.pop("complete_tab", None) == "review"
    if auto_review:
        tab_labels = ["✍️ 내가 쓴 리뷰", "✅ 완료 확인", "⭐ 받은 리뷰"]
        tab1, tab2, tab3 = st.tabs(tab_labels)
        with tab1:
            _render_written_reviews_tab(auto_open_form=True)
        with tab2:
            _render_completion_tab()
        with tab3:
            _render_received_reviews_tab()
    else:
        tab1, tab2, tab3 = st.tabs(["✅ 완료 확인", "✍️ 내가 쓴 리뷰", "⭐ 받은 리뷰"])
        with tab1:
            _render_completion_tab()
        with tab2:
            _render_written_reviews_tab()
        with tab3:
            _render_received_reviews_tab()


def _render_completion_tab():
    """Render the completion confirmation tab."""
    st.caption("계약이 완료되었는지 확인하고 정산을 진행하세요.")

    client = get_client()
    user = st.session_state.user
    role = user.get("role")

    try:
        with st.spinner("계약을 불러오는 중..."):
            result = client.get_my_contracts()
        all_contracts = result.get("items", [])

        pending_completion = [
            c for c in all_contracts if c["status"] == "pending_completion"
        ]
        completed = [c for c in all_contracts if c["status"] == "completed"]

        # Pending completion: action required, 2-column cards
        if pending_completion:
            st.warning(
                f"완료 확인이 필요한 계약 {len(pending_completion)}건이 있습니다."
            )
            st.caption("양쪽 모두 완료를 확인해야 정산이 진행됩니다.")

            COLS = 2
            for row_start in range(0, len(pending_completion), COLS):
                row_items = pending_completion[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, contract in enumerate(row_items):
                    with cols[col_idx]:
                        _render_pending_completion_card(contract, role, client)

        # Empty state
        if not pending_completion and not completed:
            st.info(
                "아직 완료 확인이 필요한 계약이 없습니다. "
                "계약을 진행하고 수업을 완료하면 여기에서 확인할 수 있습니다."
            )
        elif not pending_completion and completed:
            st.success(
                f"모든 계약이 완료되었습니다! (총 {len(completed)}건)"
            )

            # Show completion statistics
            total = sum(float(c["total_amount"]) for c in completed)
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("완료한 계약", f"{len(completed)}건")
            with metric_col2:
                label = "총 수익" if role == "instructor" else "총 지출"
                st.metric(label, f"₩{int(total):,}")
            with metric_col3:
                avg_amount = total / len(completed) if completed else 0
                st.metric("평균 금액", f"₩{int(avg_amount):,}")

    except Exception as e:
        st.error(f"계약 정보를 불러올 수 없습니다: {str(e)}")


@st.dialog("리뷰 작성")
def _write_review_dialog(contract_id: str, partner_name: str, client):
    """Dialog modal for writing a new review."""
    st.markdown(f"**{partner_name}**님에 대한 리뷰를 작성해주세요.")

    rating = st.radio(
        "평점",
        options=[5, 4, 3, 2, 1],
        format_func=lambda x: _format_star_rating(x),
        horizontal=True,
    )

    comment = st.text_area(
        "후기 (선택사항)",
        placeholder="서비스에 대한 솔직한 후기를 남겨주세요.",
        height=100,
    )

    if st.button("리뷰 작성", type="primary", use_container_width=True):
        try:
            with st.spinner("리뷰를 작성하는 중..."):
                client.create_review(contract_id, {
                    "rating": rating,
                    "comment": comment if comment else None,
                })
            st.success("리뷰가 작성되었습니다!")
            st.rerun()
        except APIError as e:
            st.error(f"리뷰 작성 실패: {e.message}")


@st.dialog("리뷰 수정")
def _edit_review_dialog(review_id: str, current_rating: int, current_comment: str, client):
    """Dialog modal for editing an existing review."""
    new_rating = st.radio(
        "평점",
        options=[5, 4, 3, 2, 1],
        format_func=lambda x: _format_star_rating(x),
        index=[5, 4, 3, 2, 1].index(current_rating) if current_rating in [5, 4, 3, 2, 1] else 0,
        horizontal=True,
    )

    new_comment = st.text_area(
        "후기",
        value=current_comment or "",
        height=100,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("저장", type="primary", use_container_width=True):
            try:
                with st.spinner("리뷰를 수정하는 중..."):
                    client.update_review(review_id, {
                        "rating": new_rating,
                        "comment": new_comment if new_comment else None,
                    })
                st.success("리뷰가 수정되었습니다!")
                st.rerun()
            except APIError as e:
                st.error(f"수정 실패: {e.message}")
    with c2:
        if st.button("취소", use_container_width=True):
            st.rerun()


def _render_written_reviews_tab(auto_open_form: bool = False):
    """Render the tab for reviews written by the current user.
    Uses Master-Detail: dataframe + selectbox to pick contract → review form below.
    If auto_open_form=True, auto-selects first unreviewed contract and shows inline form.
    """
    client = get_client()

    st.subheader("내가 작성한 리뷰")

    try:
        with st.spinner("리뷰를 불러오는 중..."):
            # Get all contracts to check which ones are reviewed
            contracts_response = client.get_my_contracts()
            contracts = contracts_response.get("items", [])

            # Filter for completed contracts
            completed_contracts = [c for c in contracts if c["status"] == "completed"]

            # Get written reviews
            written_reviews_response = client.get_written_reviews()
            written_reviews = written_reviews_response.get("reviews", [])

        # Create a map of contract_id to review
        review_map = {review["contract_id"]: review for review in written_reviews}

        # Calculate statistics
        reviewed_count = len(written_reviews)
        unreviewed_count = len(completed_contracts) - reviewed_count

        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ 작성 완료", f"{reviewed_count}건")
        with col2:
            st.metric("⏳ 미작성", f"{unreviewed_count}건")

        # Prepare table data
        table_data = []
        for contract in completed_contracts:
            contract_id = contract.get("id")
            review = review_map.get(contract_id)

            # Determine partner name
            if st.session_state.user.get("role") == "instructor":
                partner_name = contract.get("studio_name", "Unknown")
            else:
                partner_name = contract.get("instructor_name", "Unknown")

            # Format date
            contract_date = contract.get("date")
            if contract_date:
                try:
                    date_obj = datetime.fromisoformat(contract_date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime("%m/%d")
                except (ValueError, TypeError):
                    date_str = contract_date[:10]
            else:
                date_str = "-"

            if review:
                status = "✅ 작성"
                rating = _format_star_rating(review.get("rating", 0))
                comment = review.get("comment", "")[:30]
                if len(review.get("comment", "")) > 30:
                    comment += "..."
            else:
                status = "⏳ 미작성"
                rating = "-"
                comment = "리뷰를 작성해주세요"

            table_data.append({
                "상태": status,
                "상대방": partner_name,
                "계약일": date_str,
                "평점": rating,
                "리뷰 내용": comment,
                "_contract_id": contract_id,
                "_review": review,
                "_partner_name": partner_name,
            })

        # Sort: unreviewed first, then by date
        table_data.sort(key=lambda x: (x["상태"] == "✅ 작성", x["계약일"]))

        if table_data:
            # Display the table
            display_df = pd.DataFrame([
                {
                    "상태": row["상태"],
                    "상대방": row["상대방"],
                    "계약일": row["계약일"],
                    "평점": row["평점"],
                    "리뷰 내용": row["리뷰 내용"],
                }
                for row in table_data
            ])

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                height=min(400, 50 + len(table_data) * 35),
            )

            # Master-Detail: selectbox to pick a contract for review action
            st.markdown("---")
            st.markdown("### 리뷰 관리")

            # Build options for selectbox
            options = []
            for row in table_data:
                label = f"{row['상태']} {row['계약일']} | {row['상대방']}"
                options.append(label)

            # Auto-select first unreviewed contract when redirected from completion
            default_idx = 0
            if auto_open_form:
                for i, row in enumerate(table_data):
                    if row["_review"] is None:
                        default_idx = i
                        break

            selected_idx = st.selectbox(
                "계약 선택",
                range(len(table_data)),
                index=default_idx,
                format_func=lambda i: options[i],
            )

            selected = table_data[selected_idx]
            contract_id = selected["_contract_id"]
            review = selected["_review"]
            partner_name = selected["_partner_name"]

            # Detail: show review form or existing review
            if review:
                # Show existing review
                st.markdown(f"**평점:** {_format_star_rating(review.get('rating', 0))}")
                if review.get("comment"):
                    st.markdown(f"**리뷰:** {review['comment']}")

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("수정", key=f"edit_{contract_id}"):
                        _edit_review_dialog(
                            review["id"],
                            review.get("rating", 5),
                            review.get("comment", ""),
                            client,
                        )
                with c2:
                    if st.button("삭제", key=f"delete_{contract_id}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{contract_id}"):
                            try:
                                with st.spinner("리뷰를 삭제하는 중..."):
                                    client.delete_review(review["id"])
                                st.success("리뷰가 삭제되었습니다.")
                                st.rerun()
                            except APIError as e:
                                st.error(f"삭제 실패: {e.message}")
                        else:
                            st.session_state[f"confirm_delete_{contract_id}"] = True
                            st.warning("정말 삭제하시겠습니까? 다시 클릭하세요.")
            else:
                # Show inline review form directly (no dialog button needed)
                st.markdown(f"**{partner_name}**님에 대한 리뷰를 작성해주세요.")

                rating = st.radio(
                    "평점",
                    options=[5, 4, 3, 2, 1],
                    format_func=lambda x: _format_star_rating(x),
                    key=f"rating_{contract_id}",
                    horizontal=True,
                )

                comment = st.text_area(
                    "후기 (선택사항)",
                    key=f"comment_{contract_id}",
                    placeholder="서비스에 대한 솔직한 후기를 남겨주세요.",
                    height=100,
                )

                if st.button(
                    "리뷰 작성",
                    key=f"submit_{contract_id}",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        with st.spinner("리뷰를 작성하는 중..."):
                            client.create_review(contract_id, {
                                "rating": rating,
                                "comment": comment if comment else None,
                            })
                        st.success("리뷰가 작성되었습니다!")
                        st.rerun()
                    except APIError as e:
                        st.error(f"리뷰 작성 실패: {e.message}")
        else:
            st.info("아직 완료된 계약이 없습니다.")

    except APIError as e:
        st.error(f"리뷰 정보를 불러올 수 없습니다: {e.message}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")


def _render_received_reviews_tab():
    """Render the tab for reviews received by the current user.
    Uses dataframe with enough info. No checkbox toggle — detail shown inline.
    """
    client = get_client()

    st.subheader("내가 받은 리뷰")

    try:
        with st.spinner("리뷰를 불러오는 중..."):
            response = client.get_received_reviews()
        reviews = response.get("reviews", [])
        avg_rating = response.get("average_rating", 0)
        total_count = response.get("total_count", 0)

        # Display average rating prominently
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if avg_rating > 0:
                star_display = _format_star_rating(round(avg_rating))
                st.metric(
                    "평균 평점",
                    f"{star_display} {avg_rating:.1f} / 5.0",
                    f"총 {total_count}건의 리뷰",
                )
            else:
                st.metric("평균 평점", "아직 리뷰가 없습니다", "")

        with col2:
            st.metric("총 리뷰 수", f"{total_count}건")

        with col3:
            if avg_rating >= 4.5:
                st.success("🏆 우수")
            elif avg_rating >= 4.0:
                st.info("👍 양호")
            elif avg_rating >= 3.0:
                st.warning("📊 보통")
            elif avg_rating > 0:
                st.error("⚠️ 개선 필요")

        st.markdown("---")

        if reviews:
            # Prepare table data — include full comment in the table
            table_data = []
            for review in reviews:
                created_at = review.get("created_at")
                if created_at:
                    try:
                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        date_str = created_at[:10]
                else:
                    date_str = "-"

                table_data.append({
                    "날짜": date_str,
                    "작성자": review.get("reviewer_name", "익명"),
                    "평점": _format_star_rating(review.get("rating", 0)),
                    "리뷰 내용": review.get("comment", "-"),
                })

            # Sort by date (most recent first)
            table_data.sort(key=lambda x: x["날짜"], reverse=True)

            # Display the table with full comment visible
            df = pd.DataFrame(table_data)
            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
                height=min(400, 50 + len(table_data) * 35),
            )
        else:
            st.info("아직 받은 리뷰가 없습니다. 계약을 완료하면 리뷰를 받을 수 있습니다.")

    except APIError as e:
        st.error(f"리뷰 정보를 불러올 수 없습니다: {e.message}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")


def _format_star_rating(rating):
    """Format rating as visual stars."""
    if rating is None or rating == 0:
        return "☆☆☆☆☆"

    full_stars = "⭐" * int(rating)
    empty_stars = "☆" * (5 - int(rating))
    return full_stars + empty_stars


def _render_pending_completion_card(
    contract: dict, role: str, client
) -> None:
    """Render a contract pending completion confirmation."""
    st.markdown(
        f"**{contract.get('date', 'N/A')}** | "
        f"₩{int(float(contract.get('total_amount', 0))):,}"
    )
    st.caption(
        f"{contract.get('start_time', '-')} ~ {contract.get('end_time', '-')}"
    )

    # Confirmation status badges (2-column)
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
                with st.spinner("완료를 처리하는 중..."):
                    client.complete_contract(contract["id"])
                st.success("확인되었습니다! 상대방도 확인하면 정산이 진행됩니다.")
                st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")
    st.markdown("---")
