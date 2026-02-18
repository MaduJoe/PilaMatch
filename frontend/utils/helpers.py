"""
Helper functions for StudioBridge frontend
"""

import streamlit as st
from api_client import APIClient

def get_client():
    """Get API client with current session token"""
    return APIClient(st.session_state.token)

def logout():
    """Clear session and logout user"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.profile_id = None
    st.session_state.current_step = 1

def init_session_state():
    """Initialize session state variables"""
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "profile_id" not in st.session_state:
        st.session_state.profile_id = None
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1

def get_user_progress(client):
    """Get user's current progress step and data"""
    user = st.session_state.user

    # Check profile completeness
    profile_complete = False
    try:
        if user["role"] == "instructor":
            profile = client.get_my_instructor_profile()
            required_fields = ["display_name", "bio", "available_regions"]
            profile_complete = all([
                profile.get("display_name") and
                profile.get("bio") and
                profile.get("available_regions")
            ])
        else:  # studio
            profile = client.get_my_studio_profile()
            required_fields = ["business_name", "description", "region"]
            profile_complete = all([
                profile.get("business_name") and
                profile.get("description") and
                profile.get("region")
            ])
    except:
        profile_complete = False

    # Determine current step based on data availability
    current_step = 1  # Default to profile

    if profile_complete:
        current_step = 2  # Can now create/browse jobs

        # Check for applications/offers
        try:
            if user["role"] == "instructor":
                offers = client.get_my_offers()
                if offers.get("items"):
                    current_step = 3  # Has offers to review
            else:
                jobs = client.list_job_posts(
                    {"studio_id": str(st.session_state.profile_id)}
                )
                if jobs.get("items"):
                    current_step = 3  # Has job posts with potential applicants
        except:
            pass

        # Check for contracts
        try:
            contracts = client.get_my_contracts()
            if contracts.get("items"):
                active_contracts = [
                    c for c in contracts["items"]
                    if c["status"] in ["confirmed", "in_progress", "pending_completion"]
                ]
                completed_contracts = [
                    c for c in contracts["items"]
                    if c["status"] == "completed"
                ]

                if completed_contracts:
                    current_step = 5  # Has completed contracts (can write reviews)
                elif active_contracts:
                    current_step = 4  # Has active contracts but none completed yet
        except:
            pass

    # Get current page from session state
    current_page = st.session_state.get("page")
    if current_page:
        # Map page to step number
        page_to_step = {
            "profile": 1,
            "find_jobs": 2,
            "create_job": 2,
            "offers": 3,
            "applicants": 3,
            "contracts": 4,
            "complete": 5,
        }
        page_step = page_to_step.get(current_page, current_step)
        current_step = max(current_step, page_step)

    return current_step, {"profile_complete": profile_complete}