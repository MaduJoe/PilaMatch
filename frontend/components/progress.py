"""
Progress tracking and navigation components
"""

import streamlit as st

def render_progress_bar(current_step, steps):
    """Render the progress tracker at the top."""
    cols = st.columns(len(steps))

    for i, (num, label, _) in enumerate(steps):
        step_num = int(num)
        with cols[i]:
            if step_num < current_step:
                # Completed
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #d4edda; border-radius: 10px; border: 2px solid #28a745;">
                    <div style="font-size: 24px; color: #28a745;">✓</div>
                    <div style="font-size: 14px; font-weight: bold; color: #155724;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            elif step_num == current_step:
                # Current
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #fff3cd; border-radius: 10px; border: 2px solid #ffc107;">
                    <div style="font-size: 24px; font-weight: bold; color: #856404;">{num}</div>
                    <div style="font-size: 14px; font-weight: bold; color: #856404;">{label}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Future
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 10px; border: 2px solid #dee2e6;">
                    <div style="font-size: 24px; color: #6c757d;">{num}</div>
                    <div style="font-size: 14px; color: #6c757d;">{label}</div>
                </div>
                """, unsafe_allow_html=True)


def render_step_navigation(current_step, steps):
    """Render navigation buttons for each step."""
    st.markdown("---")
    cols = st.columns(len(steps))

    # Get current page (default to profile page)
    current_page = st.session_state.get("page", "profile")

    for i, (num, label, page) in enumerate(steps):
        step_num = int(num)
        with cols[i]:
            is_current_page = page == current_page
            is_accessible = step_num <= current_step

            if is_current_page:
                # Current page button (highlighted)
                st.button(
                    label,
                    key=f"nav_{page}",
                    use_container_width=True,
                    type="primary",
                    disabled=True
                )
            elif is_accessible:
                # Accessible page button
                if st.button(
                    label,
                    key=f"nav_{page}",
                    use_container_width=True
                ):
                    st.session_state.page = page
                    st.rerun()
            else:
                # Locked page button
                st.button(
                    f"🔒 {label}",
                    key=f"nav_{page}",
                    use_container_width=True,
                    disabled=True
                )