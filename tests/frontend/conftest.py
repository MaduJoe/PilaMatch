"""
Frontend test conftest - streamlit 없이 mock 기반으로 프론트엔드 모듈 테스트
"""

import sys
import os
import types
from unittest.mock import MagicMock, patch

# frontend 경로를 Python path에 추가
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
sys.path.insert(0, os.path.abspath(FRONTEND_DIR))

# streamlit mock을 먼저 설치
def build_streamlit_mock():
    """streamlit 전체 mock 생성"""
    st_mock = MagicMock()

    # session_state는 dict-like로 동작해야 함
    class MockSessionState(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                return None

        def __setattr__(self, name, value):
            self[name] = value

        def __delattr__(self, name):
            if name in self:
                del self[name]

        def get(self, key, default=None):
            return super().get(key, default)

    st_mock.session_state = MockSessionState()

    # 기본 UI 함수들은 모두 MagicMock (반환값이 필요한 것들 설정)
    st_mock.form = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    st_mock.expander = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    st_mock.container = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
    st_mock.columns = MagicMock(return_value=[MagicMock() for _ in range(3)])
    st_mock.tabs = MagicMock(return_value=[MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)) for _ in range(2)])
    st_mock.button = MagicMock(return_value=False)
    st_mock.form_submit_button = MagicMock(return_value=False)
    st_mock.text_input = MagicMock(return_value="")
    st_mock.text_area = MagicMock(return_value="")
    st_mock.number_input = MagicMock(return_value=0)
    st_mock.selectbox = MagicMock(return_value="강남")
    st_mock.radio = MagicMock(return_value="instructor")
    st_mock.checkbox = MagicMock(return_value=False)
    st_mock.date_input = MagicMock(return_value=None)
    st_mock.time_input = MagicMock(return_value=None)
    st_mock.rerun = MagicMock()
    st_mock.set_page_config = MagicMock()

    # streamlit.components.v1 mock
    components_mock = MagicMock()
    components_mock.v1 = MagicMock()
    components_mock.v1.html = MagicMock()

    st_mock.components = components_mock

    return st_mock


# streamlit 및 관련 모듈 mock 설치
_st_mock = build_streamlit_mock()
sys.modules['streamlit'] = _st_mock
sys.modules['streamlit.components'] = _st_mock.components
sys.modules['streamlit.components.v1'] = _st_mock.components.v1

# python-dotenv mock
dotenv_mock = MagicMock()
dotenv_mock.load_dotenv = MagicMock()
sys.modules['dotenv'] = dotenv_mock

import pytest


@pytest.fixture
def st_mock():
    """Reset session_state between tests"""
    _st_mock.session_state.clear()
    _st_mock.button.return_value = False
    _st_mock.form_submit_button.return_value = False
    _st_mock.text_input.return_value = ""
    _st_mock.text_area.return_value = ""
    _st_mock.number_input.return_value = 0
    _st_mock.selectbox.return_value = "강남"
    _st_mock.radio.return_value = "instructor"
    _st_mock.checkbox.return_value = False
    return _st_mock


@pytest.fixture
def mock_api_client():
    """APIClient의 mock 인스턴스"""
    from unittest.mock import MagicMock
    client = MagicMock()

    # 기본 반환값 설정
    client.get_me.return_value = {
        "user": {"id": "user-123", "email": "test@test.com", "role": "instructor",
                 "display_name": "Test Instructor", "identity_verified": True},
        "profile_id": "profile-123"
    }
    client.get_my_instructor_profile.return_value = {
        "id": "profile-123",
        "display_name": "Test Instructor",
        "bio": "Test bio",
        "experience_years": 3,
        "available_regions": ["강남", "서초"],
        "certifications": [{"name": "Test Cert", "is_verified": False}],
        "hourly_rate_min": 40000,
        "hourly_rate_max": 60000
    }
    client.get_my_studio_profile.return_value = {
        "id": "studio-profile-123",
        "business_name": "Test Studio",
        "description": "Test description",
        "region": "강남",
        "address": "Test address"
    }
    client.get_my_offers.return_value = {"items": []}
    client.get_my_contracts.return_value = {"items": []}
    client.get_my_applications.return_value = {"items": []}
    client.list_job_posts_with_matching.return_value = {"items": []}
    client.list_job_posts.return_value = {"items": []}
    client.get_deposit_status.return_value = {
        "balance": 50000,
        "required": 50000,
        "is_sufficient": True,
        "shortfall": 0,
        "membership_tier": "free"
    }
    client.get_subscription_status.return_value = {
        "membership_tier": "free",
        "subscription": None
    }
    return client


@pytest.fixture
def instructor_session(st_mock, mock_api_client):
    """강사 세션 상태 설정"""
    st_mock.session_state['token'] = 'instructor-token-123'
    st_mock.session_state['user'] = {
        "id": "user-123",
        "email": "instructor@test.com",
        "role": "instructor",
        "display_name": "Test Instructor",
        "identity_verified": True,
        "business_verified": False
    }
    st_mock.session_state['profile_id'] = 'profile-123'
    st_mock.session_state['current_step'] = 1
    return st_mock


@pytest.fixture
def studio_session(st_mock, mock_api_client):
    """스튜디오 세션 상태 설정"""
    st_mock.session_state['token'] = 'studio-token-456'
    st_mock.session_state['user'] = {
        "id": "studio-user-456",
        "email": "studio@test.com",
        "role": "studio",
        "business_name": "Test Studio",
        "identity_verified": True,
        "business_verified": True
    }
    st_mock.session_state['profile_id'] = 'studio-profile-456'
    st_mock.session_state['current_step'] = 1
    return st_mock
