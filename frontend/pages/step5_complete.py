"""
Step 5: Completion confirmation and review management
"""

import streamlit as st
from api_client import APIError
from utils.helpers import get_client


def render_complete_step():
    """Render the completion and review UI for both instructors and studios."""
    st.header("5단계: 완료 & 리뷰")
    st.caption("완료된 계약을 확인하고 상대방에 대한 리뷰를 작성하세요.")

    client = get_client()
    user = st.session_state.user
    role = user.get("role")

    try:
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
                "아직 완료된 계약이 없습니다. "
                "계약을 진행하고 수업을 완료하면 여기에서 확인할 수 있습니다."
            )

        # Completed contracts grid + reviews
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

            # Fetch all reviews in batch
            review_map: dict[str, dict | None] = {}
            for contract in completed:
                try:
                    resp = client.get_my_review_for_contract(contract["id"])
                    review_map[contract["id"]] = (
                        resp if (resp and resp.get("id")) else None
                    )
                except APIError:
                    review_map[contract["id"]] = None
                except Exception:
                    review_map[contract["id"]] = None

            # Sort: unreviewed first, reviewed last
            no_review = [c for c in completed if not review_map.get(c["id"])]
            has_review = [c for c in completed if review_map.get(c["id"])]
            sorted_contracts = no_review + has_review

            # 2-column card grid
            COLS = 2
            for row_start in range(0, len(sorted_contracts), COLS):
                row_items = sorted_contracts[row_start : row_start + COLS]
                cols = st.columns(COLS)
                for col_idx, contract in enumerate(row_items):
                    existing_review = review_map.get(contract["id"])
                    with cols[col_idx]:
                        review_badge = (
                            "리뷰 완료" if existing_review else "리뷰 미작성"
                        )
                        expander_label = (
                            f"{contract.get('date', 'N/A')} | "
                            f"₩{int(float(contract.get('total_amount', 0))):,} | "
                            f"{review_badge}"
                        )
                        with st.expander(
                            expander_label, expanded=(not existing_review)
                        ):
                            st.caption(
                                f"시간: {contract.get('start_time', '-')} ~ "
                                f"{contract.get('end_time', '-')}"
                            )
                            _render_review_form(
                                contract, user, client, existing_review
                            )

    except Exception as e:
        st.error(f"완료/리뷰 섹션 오류: {str(e)}")

    st.markdown("---")


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
                client.complete_contract(contract["id"])
                st.success("확인되었습니다! 상대방도 확인하면 정산이 진행됩니다.")
                st.rerun()
            except APIError as e:
                st.error(f"오류: {e.message}")
    st.markdown("---")


def _render_review_form(
    contract: dict,
    user: dict,
    client,
    existing_review: dict | None,
) -> None:
    """Render the review creation or edit form."""
    rating_options = {"1점": 1, "2점": 2, "3점": 3, "4점": 4, "5점": 5}

    if existing_review:
        _render_existing_review(contract, user, client, existing_review, rating_options)
    else:
        _render_new_review_form(contract, user, client, rating_options)


def _render_existing_review(
    contract: dict,
    user: dict,
    client,
    existing_review: dict,
    rating_options: dict,
) -> None:
    """Render an existing review with optional edit/delete form."""
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
            prompt = (
                "스튜디오에 대한 후기"
                if user["role"] == "instructor"
                else "강사님에 대한 후기"
            )
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
                        client.update_review(
                            existing_review["id"], new_rating, new_comment
                        )
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
        if st.button(
            "수정/삭제",
            key=f"edit_btn_{contract['id']}",
            use_container_width=True,
        ):
            st.session_state[edit_key] = True
            st.rerun()


def _render_new_review_form(
    contract: dict,
    user: dict,
    client,
    rating_options: dict,
) -> None:
    """Render the form to create a new review."""
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
            prompt = (
                "스튜디오에 대한 후기 (선택)"
                if user["role"] == "instructor"
                else "강사님에 대한 후기 (선택)"
            )
            placeholder = (
                "예: 시설이 깨끗하고 운영이 체계적입니다."
                if user["role"] == "instructor"
                else "예: 전문적이고 친절한 강사님입니다."
            )
            comment = st.text_area(
                prompt,
                placeholder=placeholder,
                height=80,
                key=f"comment_{contract['id']}",
            )
            sub_col1, sub_col2 = st.columns(2)
            submitted = sub_col1.form_submit_button(
                "제출", type="primary", use_container_width=True
            )
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
