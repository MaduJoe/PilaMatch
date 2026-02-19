"""
utils 모듈 단위 테스트

constants.py, helpers.py의 로직을 검증합니다.
Streamlit은 conftest.py에서 mock으로 대체됩니다.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# conftest.py가 streamlit mock을 먼저 설치합니다
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
)


# ──────────────────────────────────────────────
# constants.py 테스트
# ──────────────────────────────────────────────

class TestConstants:
    """constants.py의 데이터 구조 및 값 검증"""

    def setup_method(self):
        sys.path.insert(0, FRONTEND_DIR)
        from utils.constants import (
            INSTRUCTOR_STEPS, STUDIO_STEPS, SEOUL_REGIONS,
            RATE_PRESETS, CONTRACT_TERMS
        )
        self.INSTRUCTOR_STEPS = INSTRUCTOR_STEPS
        self.STUDIO_STEPS = STUDIO_STEPS
        self.SEOUL_REGIONS = SEOUL_REGIONS
        self.RATE_PRESETS = RATE_PRESETS
        self.CONTRACT_TERMS = CONTRACT_TERMS

    def test_INSTRUCTOR_STEPS_has_5_steps(self):
        assert len(self.INSTRUCTOR_STEPS) == 5

    def test_INSTRUCTOR_STEPS_step_numbers_correct(self):
        nums = [step[0] for step in self.INSTRUCTOR_STEPS]
        assert nums == ["1", "2", "3", "4", "5"]

    def test_INSTRUCTOR_STEPS_pages_correct(self):
        pages = [step[2] for step in self.INSTRUCTOR_STEPS]
        assert pages == ["profile", "find_jobs", "offers", "contracts", "complete"]

    def test_STUDIO_STEPS_has_5_steps(self):
        assert len(self.STUDIO_STEPS) == 5

    def test_STUDIO_STEPS_pages_correct(self):
        pages = [step[2] for step in self.STUDIO_STEPS]
        assert pages == ["profile", "create_job", "applicants", "contracts", "complete"]

    def test_SEOUL_REGIONS_is_dict(self):
        assert isinstance(self.SEOUL_REGIONS, dict)

    def test_SEOUL_REGIONS_has_coordinates(self):
        for region, coords in self.SEOUL_REGIONS.items():
            assert len(coords) == 2, f"{region}의 좌표가 2개여야 함"
            lat, lng = coords
            assert 37.0 < lat < 38.0, f"{region} 위도 범위 오류: {lat}"
            assert 126.0 < lng < 128.0, f"{region} 경도 범위 오류: {lng}"

    def test_SEOUL_REGIONS_includes_major_districts(self):
        major = ["강남", "서초", "마포", "송파"]
        for district in major:
            assert district in self.SEOUL_REGIONS, f"{district}이 SEOUL_REGIONS에 없음"

    def test_RATE_PRESETS_structure(self):
        for rate, label in self.RATE_PRESETS:
            assert isinstance(rate, int), f"rate는 int여야 함: {rate}"
            assert isinstance(label, str), f"label은 str이어야 함: {label}"
            assert rate > 0

    def test_RATE_PRESETS_sorted_ascending(self):
        rates = [r for r, _ in self.RATE_PRESETS]
        assert rates == sorted(rates), "RATE_PRESETS가 오름차순이어야 함"

    def test_CONTRACT_TERMS_is_string(self):
        assert isinstance(self.CONTRACT_TERMS, str)

    def test_CONTRACT_TERMS_not_empty(self):
        assert len(self.CONTRACT_TERMS.strip()) > 0


# ──────────────────────────────────────────────
# helpers.py - init_session_state 테스트
# ──────────────────────────────────────────────

class TestInitSessionState:
    """init_session_state() 함수 테스트"""

    def test_빈_세션에서_초기값_설정(self, st_mock):
        from utils.helpers import init_session_state
        init_session_state()
        assert st_mock.session_state.get('token') is None
        assert st_mock.session_state.get('user') is None
        assert st_mock.session_state.get('profile_id') is None
        assert st_mock.session_state.get('current_step') == 1

    def test_기존_값_덮어쓰지_않음(self, st_mock):
        """이미 설정된 값은 변경하지 않아야 한다"""
        st_mock.session_state['token'] = 'existing-token'
        st_mock.session_state['user'] = {'id': 'u1'}
        from utils.helpers import init_session_state
        init_session_state()
        assert st_mock.session_state['token'] == 'existing-token'
        assert st_mock.session_state['user'] == {'id': 'u1'}

    def test_current_step_default_is_1(self, st_mock):
        from utils.helpers import init_session_state
        init_session_state()
        assert st_mock.session_state['current_step'] == 1


# ──────────────────────────────────────────────
# helpers.py - logout 테스트
# ──────────────────────────────────────────────

class TestLogout:
    """logout() 함수 테스트"""

    def test_logout_clears_token(self, st_mock):
        st_mock.session_state['token'] = 'some-token'
        from utils.helpers import logout
        logout()
        assert st_mock.session_state.get('token') is None

    def test_logout_clears_user(self, st_mock):
        st_mock.session_state['user'] = {'id': 'u1', 'email': 'a@b.com'}
        from utils.helpers import logout
        logout()
        assert st_mock.session_state.get('user') is None

    def test_logout_clears_profile_id(self, st_mock):
        st_mock.session_state['profile_id'] = 'profile-123'
        from utils.helpers import logout
        logout()
        assert st_mock.session_state.get('profile_id') is None

    def test_logout_resets_current_step_to_1(self, st_mock):
        st_mock.session_state['current_step'] = 4
        from utils.helpers import logout
        logout()
        assert st_mock.session_state['current_step'] == 1


# ──────────────────────────────────────────────
# helpers.py - get_client 테스트
# ──────────────────────────────────────────────

class TestGetClient:
    """get_client() 함수 테스트"""

    def test_get_client_반환_타입(self, st_mock):
        st_mock.session_state['token'] = 'my-token-123'
        from utils.helpers import get_client
        from api_client import APIClient
        client = get_client()
        assert isinstance(client, APIClient)

    def test_get_client_token_전달(self, st_mock):
        st_mock.session_state['token'] = 'test-bearer-token'
        from utils.helpers import get_client
        client = get_client()
        assert client.token == 'test-bearer-token'

    def test_get_client_token_없을때_None(self, st_mock):
        st_mock.session_state['token'] = None
        from utils.helpers import get_client
        client = get_client()
        assert client.token is None


# ──────────────────────────────────────────────
# helpers.py - get_user_progress 테스트
# ──────────────────────────────────────────────

class TestGetUserProgress:
    """get_user_progress() - 사용자 진행 단계 계산 로직 테스트"""

    def _make_instructor_session(self, st_mock):
        st_mock.session_state['user'] = {
            'id': 'u1', 'role': 'instructor', 'email': 'a@b.com'
        }

    def _make_studio_session(self, st_mock):
        st_mock.session_state['user'] = {
            'id': 'u2', 'role': 'studio', 'email': 'b@c.com'
        }

    def test_강사_프로필_미완성이면_step1(self, st_mock):
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "", "bio": "", "available_regions": []
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 1
        assert data["profile_complete"] is False

    def test_강사_프로필_완성이면_step2(self, st_mock):
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 2
        assert data["profile_complete"] is True

    def test_강사_오퍼_있으면_step3(self, st_mock):
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {
            "items": [{"id": "offer-1", "status": "pending"}]
        }
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 3

    def test_강사_활성_계약_있으면_step4(self, st_mock):
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {
            "items": [{"id": "c1", "status": "in_progress"}]
        }

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 4

    def test_강사_완료_계약만_있으면_step5(self, st_mock):
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {
            "items": [{"id": "c1", "status": "completed"}]
        }

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 5

    def test_스튜디오_프로필_완성이면_step2(self, st_mock):
        self._make_studio_session(st_mock)
        st_mock.session_state['profile_id'] = 'studio-u2'
        mock_client = MagicMock()
        mock_client.get_my_studio_profile.return_value = {
            "business_name": "강남스튜디오", "description": "소개", "region": "강남"
        }
        # list_job_posts: 공고 없음 (빈 목록) -> step 3으로 올라가지 않음
        mock_client.list_job_posts.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 2

    def test_스튜디오_공고_있으면_step3(self, st_mock):
        """스튜디오가 공고를 등록하면 step 3이 되어야 한다"""
        self._make_studio_session(st_mock)
        st_mock.session_state['profile_id'] = 'studio-u2'
        mock_client = MagicMock()
        mock_client.get_my_studio_profile.return_value = {
            "business_name": "강남스튜디오", "description": "소개", "region": "강남"
        }
        # 공고가 있으면 step 3
        mock_client.list_job_posts.return_value = {
            "items": [{"id": "j1", "studio_id": "studio-u2", "title": "공고"}]
        }
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 3

    def test_API_에러시_profile_complete_False(self, st_mock):
        """API 호출 실패 시 profile_complete는 False여야 한다"""
        self._make_instructor_session(st_mock)
        from api_client import APIError
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.side_effect = APIError(500, {"detail": "오류"})
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert data["profile_complete"] is False

    def test_현재_페이지_step이_계산된_step보다_크면_현재_페이지_반영(self, st_mock):
        """session_state.page가 계산된 step보다 높은 단계면 그 값 사용"""
        self._make_instructor_session(st_mock)
        st_mock.session_state['page'] = 'contracts'  # step 4
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {"items": []}

        from utils.helpers import get_user_progress
        step, data = get_user_progress(mock_client)
        assert step == 4  # 계산=2, page_step=4 -> max=4

    def test_confirmed_contract_도_active로_처리(self, st_mock):
        """confirmed 상태 계약도 step 4로 처리되어야 한다"""
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {
            "items": [{"id": "c1", "status": "confirmed"}]
        }

        from utils.helpers import get_user_progress
        step, _ = get_user_progress(mock_client)
        assert step == 4

    def test_pending_completion_contract_step4로_처리(self, st_mock):
        """pending_completion 상태도 활성 계약으로 step 4"""
        self._make_instructor_session(st_mock)
        mock_client = MagicMock()
        mock_client.get_my_instructor_profile.return_value = {
            "display_name": "홍길동", "bio": "소개", "available_regions": ["강남"]
        }
        mock_client.get_my_offers.return_value = {"items": []}
        mock_client.get_my_contracts.return_value = {
            "items": [{"id": "c1", "status": "pending_completion"}]
        }

        from utils.helpers import get_user_progress
        step, _ = get_user_progress(mock_client)
        assert step == 4
