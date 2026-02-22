"""Trust Score breakdown component for StudioBridge."""

import streamlit as st


# Level badge emojis
LEVEL_BADGES = {
    "bronze": "🥉",
    "silver": "🥈",
    "gold": "🥇",
    "platinum": "🏆",
}

# Factor display order (most impactful first)
FACTOR_ORDER = [
    "identity_verification",
    "contract_history",
    "profile_completeness",
    "review_average",
    "certifications",
    "premium_membership",
    "response_rate",
    "account_age",
    "no_show_penalty",
]


def render_trust_score_detail(trust_data: dict):
    """Render detailed Trust Score with breakdown, recommendations, and gamification."""
    score = trust_data.get("score", 0)
    level = trust_data.get("level", "신진")
    level_color = trust_data.get("level_color", "bronze")
    breakdown = trust_data.get("breakdown", {})
    recommendations = trust_data.get("recommendations", [])
    points_to_next = trust_data.get("points_to_next_level", 0)
    next_level_score = trust_data.get("next_level_score", 100)
    factor_labels = trust_data.get("factor_labels", {})
    level_thresholds = trust_data.get("level_thresholds", [])

    badge = LEVEL_BADGES.get(level_color, "🥉")

    # --- Header: Score + Level + Gamification ---
    st.markdown(f"""
<div style="text-align:center; padding:12px 0;">
    <div style="font-size:48px; font-weight:bold; color:#333;">{badge} {score}<span style="font-size:18px; color:#888;">/100</span></div>
    <div style="font-size:18px; color:#666; margin-top:4px;">{level} 등급</div>
</div>
""", unsafe_allow_html=True)

    # Level progress bar (within current level band)
    if level_thresholds:
        current_threshold = None
        next_threshold = None
        for i, t in enumerate(level_thresholds):
            if t["min"] <= score <= t["max"]:
                current_threshold = t
                if i + 1 < len(level_thresholds):
                    next_threshold = level_thresholds[i + 1]
                break

        if current_threshold:
            level_range = current_threshold["max"] - current_threshold["min"] + 1
            level_progress = (score - current_threshold["min"]) / level_range
            st.progress(min(1.0, level_progress))

            if points_to_next > 0 and next_threshold:
                st.caption(f"**{points_to_next}점**만 더 올리면 **{next_threshold['level']}** 등급 달성!")
            elif score >= 80:
                st.caption("최고 등급을 유지하고 있습니다!")

    # --- Factor Breakdown ---
    st.markdown("#### 점수 상세")

    for factor_key in FACTOR_ORDER:
        current = breakdown.get(factor_key, 0)
        label_info = factor_labels.get(factor_key, {})
        name = label_info.get("name", factor_key)
        max_pts = label_info.get("max", 0)

        # Skip no_show_penalty if no penalty
        if factor_key == "no_show_penalty" and current == 0:
            continue

        # Handle penalty (negative values)
        if factor_key == "no_show_penalty":
            st.markdown(f"**{name}**: {current}점")
            st.caption("노쇼 기록 시 건당 -20점이 적용됩니다")
            continue

        # Normal factor
        col_label, col_bar, col_score = st.columns([2, 4, 1])
        with col_label:
            st.markdown(f"**{name}**")
        with col_bar:
            if max_pts > 0:
                progress = max(0.0, min(1.0, current / max_pts))
                st.progress(progress)
            else:
                st.progress(0.0)
        with col_score:
            st.markdown(f"**{current}**/{max_pts}")

    # --- Recommendations ---
    if recommendations:
        st.markdown("#### 점수 올리기")
        for i, rec in enumerate(recommendations):
            st.info(f"💡 {rec}")

    # --- Level Guide ---
    with st.expander("등급 안내"):
        for t in level_thresholds:
            t_badge = LEVEL_BADGES.get(t["color"], "")
            is_current = t["min"] <= score <= t["max"]
            marker = " ← 현재" if is_current else ""
            st.markdown(f"{t_badge} **{t['level']}** ({t['min']}~{t['max']}점){marker}")
        st.caption("Trust Score가 높을수록 매칭 우선순위가 올라가고, 상대방에게 신뢰를 줍니다.")
