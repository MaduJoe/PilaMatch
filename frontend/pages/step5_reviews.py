"""
Step 5: Review management with table-based display
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from api_client import APIError
from utils.helpers import get_client


def render_reviews_step():
    """Render the review management step with dual tabs."""
    st.header("5단계: 리뷰 관리")

    client = get_client()

    # Create tabs for written and received reviews
    tab1, tab2 = st.tabs(["✍️ 내가 쓴 리뷰", "⭐ 받은 리뷰"])

    with tab1:
        _render_written_reviews_tab(client)

    with tab2:
        _render_received_reviews_tab(client)


def _render_written_reviews_tab(client):
    """Render the tab for reviews written by the current user."""
    st.subheader("내가 작성한 리뷰")

    try:
        # Get all contracts to check which ones are reviewed
        contracts_response = client.get_my_contracts()
        contracts = contracts_response.get("contracts", [])

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
                except:
                    date_str = contract_date[:10]
            else:
                date_str = "-"

            if review:
                # Reviewed
                status = "✅ 작성"
                rating = _format_star_rating(review.get("rating", 0))
                comment = review.get("comment", "")[:30]
                if len(review.get("comment", "")) > 30:
                    comment += "..."
            else:
                # Not reviewed yet
                status = "⏳ 미작성"
                rating = "-"
                comment = "리뷰를 작성해주세요"

            table_data.append({
                "상태": status,
                "상대방": partner_name,
                "계약일": date_str,
                "평점": rating,
                "리뷰 내용": comment,
                "contract_id": contract_id,
                "review": review
            })

        # Sort: unreviewed first, then by date
        table_data.sort(key=lambda x: (x["상태"] == "✅ 작성", x["계약일"]), reverse=False)

        if table_data:
            # Display the table
            display_df = pd.DataFrame([
                {
                    "상태": row["상태"],
                    "상대방": row["상대방"],
                    "계약일": row["계약일"],
                    "평점": row["평점"],
                    "리뷰 내용": row["리뷰 내용"]
                }
                for row in table_data
            ])

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                height=min(400, 50 + len(table_data) * 35)
            )

            # Show review forms in expanders below the table
            st.markdown("---")
            st.markdown("### 리뷰 관리")

            # Create 2-column layout for review forms
            cols = st.columns(2)
            for idx, row in enumerate(table_data):
                col = cols[idx % 2]
                with col:
                    _render_review_form_card(client, row)

        else:
            st.info("아직 완료된 계약이 없습니다.")

    except APIError as e:
        st.error(f"리뷰 정보를 불러올 수 없습니다: {e.message}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")


def _render_received_reviews_tab(client):
    """Render the tab for reviews received by the current user."""
    st.subheader("내가 받은 리뷰")

    try:
        # Get received reviews
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
                    f"총 {total_count}건의 리뷰"
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
            # Prepare table data
            table_data = []
            for review in reviews:
                # Format date
                created_at = review.get("created_at")
                if created_at:
                    try:
                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        date_str = date_obj.strftime("%Y-%m-%d")
                    except:
                        date_str = created_at[:10]
                else:
                    date_str = "-"

                table_data.append({
                    "날짜": date_str,
                    "작성자": review.get("reviewer_name", "익명"),
                    "평점": _format_star_rating(review.get("rating", 0)),
                    "리뷰 내용": review.get("comment", "-")
                })

            # Sort by date (most recent first)
            table_data.sort(key=lambda x: x["날짜"], reverse=True)

            # Display the table
            df = pd.DataFrame(table_data)
            st.dataframe(
                df,
                hide_index=True,
                use_container_width=True,
                height=min(400, 50 + len(table_data) * 35)
            )

            # Show detailed reviews below
            if st.checkbox("리뷰 상세 보기"):
                st.markdown("---")
                for review in sorted(reviews, key=lambda x: x.get("created_at", ""), reverse=True):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{review.get('reviewer_name', '익명')}**")
                            st.markdown(_format_star_rating(review.get("rating", 0)))
                        with col2:
                            created_at = review.get("created_at")
                            if created_at:
                                try:
                                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    st.caption(date_obj.strftime("%Y년 %m월 %d일"))
                                except:
                                    st.caption(created_at[:10])

                        if review.get("comment"):
                            st.markdown(f"_{review['comment']}_")
                        st.markdown("---")

        else:
            st.info("아직 받은 리뷰가 없습니다. 계약을 완료하면 리뷰를 받을 수 있습니다.")

    except APIError as e:
        st.error(f"리뷰 정보를 불러올 수 없습니다: {e.message}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")


def _render_review_form_card(client, row):
    """Render a review form card for a contract."""
    contract_id = row["contract_id"]
    review = row["review"]
    partner_name = row["상대방"]

    with st.expander(f"{'✅' if review else '⏳'} {row['계약일']} | {partner_name}"):
        if review:
            # Show existing review with edit option
            st.markdown(f"**평점:** {_format_star_rating(review.get('rating', 0))}")
            if review.get("comment"):
                st.markdown(f"**리뷰:**")
                st.caption(review["comment"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("수정", key=f"edit_{contract_id}"):
                    st.session_state[f"editing_{contract_id}"] = True

            with col2:
                if st.button("삭제", key=f"delete_{contract_id}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{contract_id}"):
                        try:
                            client.delete_review(review["id"])
                            st.success("리뷰가 삭제되었습니다.")
                            st.rerun()
                        except APIError as e:
                            st.error(f"삭제 실패: {e.message}")
                    else:
                        st.session_state[f"confirm_delete_{contract_id}"] = True
                        st.warning("정말 삭제하시겠습니까? 다시 클릭하세요.")

            # Edit form
            if st.session_state.get(f"editing_{contract_id}"):
                _render_review_edit_form(client, contract_id, review)
        else:
            # Show new review form
            _render_new_review_form(client, contract_id, partner_name)


def _render_new_review_form(client, contract_id, partner_name):
    """Render form for creating a new review."""
    st.markdown(f"**{partner_name}**님에 대한 리뷰를 작성해주세요.")

    rating = st.radio(
        "평점",
        options=[5, 4, 3, 2, 1],
        format_func=lambda x: _format_star_rating(x),
        key=f"rating_{contract_id}",
        horizontal=True
    )

    comment = st.text_area(
        "후기 (선택사항)",
        key=f"comment_{contract_id}",
        placeholder="서비스에 대한 솔직한 후기를 남겨주세요.",
        height=100
    )

    if st.button("리뷰 작성", key=f"submit_{contract_id}", type="primary"):
        try:
            client.create_review(contract_id, {
                "rating": rating,
                "comment": comment if comment else None
            })
            st.success("리뷰가 작성되었습니다!")
            st.rerun()
        except APIError as e:
            st.error(f"리뷰 작성 실패: {e.message}")


def _render_review_edit_form(client, contract_id, review):
    """Render form for editing an existing review."""
    st.markdown("### 리뷰 수정")

    new_rating = st.radio(
        "평점",
        options=[5, 4, 3, 2, 1],
        format_func=lambda x: _format_star_rating(x),
        index=[5, 4, 3, 2, 1].index(review.get("rating", 5)),
        key=f"edit_rating_{contract_id}",
        horizontal=True
    )

    new_comment = st.text_area(
        "후기",
        value=review.get("comment", ""),
        key=f"edit_comment_{contract_id}",
        height=100
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("저장", key=f"save_edit_{contract_id}", type="primary"):
            try:
                client.update_review(review["id"], {
                    "rating": new_rating,
                    "comment": new_comment if new_comment else None
                })
                st.success("리뷰가 수정되었습니다!")
                del st.session_state[f"editing_{contract_id}"]
                st.rerun()
            except APIError as e:
                st.error(f"수정 실패: {e.message}")

    with col2:
        if st.button("취소", key=f"cancel_edit_{contract_id}"):
            del st.session_state[f"editing_{contract_id}"]
            st.rerun()


def _format_star_rating(rating):
    """Format rating as visual stars."""
    if rating is None or rating == 0:
        return "☆☆☆☆☆"

    full_stars = "⭐" * int(rating)
    empty_stars = "☆" * (5 - int(rating))
    return full_stars + empty_stars