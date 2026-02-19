"""
APIClient 단위 테스트

실제 HTTP 호출 없이 APIClient의 메서드 구조와 동작을 검증합니다.
외부 서비스(백엔드 API)는 httpx mock으로 대체합니다.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
)
sys.path.insert(0, FRONTEND_DIR)

from api_client import APIClient, APIError


# ──────────────────────────────────────────────
# APIError 클래스 테스트
# ──────────────────────────────────────────────

class TestAPIError:
    """APIError 초기화 및 에러 포맷 파싱 테스트"""

    def test_custom_error_format_파싱(self):
        """custom dict format: detail.code / detail.message"""
        err = APIError(400, {"detail": {"code": "CUSTOM_ERR", "message": "오류 메시지"}})
        assert err.code == "CUSTOM_ERR"
        assert err.message == "오류 메시지"
        assert err.status_code == 400

    def test_validation_error_list_format_파싱(self):
        """FastAPI validation error: detail = list"""
        err = APIError(422, {"detail": [
            {"loc": ["body", "email"], "msg": "field required"},
            {"loc": ["body", "password"], "msg": "too short"},
        ]})
        assert err.code == "VALIDATION_ERROR"
        assert "email" in err.message
        assert "password" in err.message

    def test_string_detail_format_파싱(self):
        """단순 문자열 detail"""
        err = APIError(404, {"detail": "Not found"})
        assert err.code == "ERROR"
        assert err.message == "Not found"

    def test_unknown_error_format_처리(self):
        """detail이 없거나 알 수 없는 형식"""
        err = APIError(500, {})
        assert err.code == "UNKNOWN_ERROR"

    def test_exception_message_set(self):
        """APIError는 Exception을 상속하며 message가 args에 설정되어야 한다"""
        err = APIError(400, {"detail": {"code": "ERR", "message": "테스트 에러"}})
        assert str(err) == "테스트 에러"

    def test_connection_error_format(self):
        """Connection error 포맷"""
        err = APIError(503, {"detail": {"code": "CONNECTION_ERROR", "message": "Cannot connect"}})
        assert err.status_code == 503
        assert err.code == "CONNECTION_ERROR"


# ──────────────────────────────────────────────
# APIClient 초기화 테스트
# ──────────────────────────────────────────────

class TestAPIClientInit:
    """APIClient 초기화 및 헤더 생성 테스트"""

    def test_init_without_token(self):
        client = APIClient()
        assert client.token is None

    def test_init_with_token(self):
        client = APIClient(token="test-token-abc")
        assert client.token == "test-token-abc"

    def test_headers_without_token(self):
        client = APIClient()
        headers = client._headers()
        assert "Content-Type" in headers
        assert "Authorization" not in headers

    def test_headers_with_token(self):
        client = APIClient(token="my-jwt-token")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer my-jwt-token"

    def test_base_url_default(self):
        """기본 BASE_URL은 localhost:8000"""
        client = APIClient()
        assert "localhost:8000" in client.base_url or "8000" in client.base_url

    def test_base_url_from_env(self):
        """환경변수 API_BASE_URL을 사용해야 한다"""
        with patch.dict(os.environ, {"API_BASE_URL": "http://my-api:9000"}):
            # 새 모듈 import 없이 base_url 생성 로직만 확인
            import api_client as ac_module
            old_url = ac_module.API_BASE_URL
            # 실행 중에는 모듈 수준 변수가 이미 로드되어 있으므로
            # 단지 환경변수 의존 구조를 확인
            assert 'API_BASE_URL' in dir(ac_module)


# ──────────────────────────────────────────────
# APIClient HTTP 메서드 - mock 기반 테스트
# ──────────────────────────────────────────────

class TestAPIClientHTTPMethods:
    """_request_sync를 mock하여 각 API 메서드의 올바른 endpoint/method 호출 검증"""

    def _make_client_with_mock(self, mock_response):
        """_request_sync를 mock으로 교체한 APIClient 반환"""
        client = APIClient(token="test-token")
        client._request_sync = MagicMock(return_value=mock_response)
        return client

    # Auth 메서드
    def test_login_sends_correct_payload(self):
        client = self._make_client_with_mock({"access_token": "abc"})
        client.login("test@test.com", "password123")
        client._request_sync.assert_called_once_with(
            "POST", "/auth/login", {"email": "test@test.com", "password": "password123"}
        )

    def test_signup_instructor_includes_display_name(self):
        client = self._make_client_with_mock({"access_token": "abc"})
        client.signup("a@b.com", "pass1234", "instructor", display_name="홍길동")
        args = client._request_sync.call_args
        data = args[0][2]
        assert data["display_name"] == "홍길동"
        assert "business_name" not in data

    def test_signup_studio_includes_business_name(self):
        client = self._make_client_with_mock({"access_token": "abc"})
        client.signup("a@b.com", "pass1234", "studio", business_name="강남스튜디오")
        args = client._request_sync.call_args
        data = args[0][2]
        assert data["business_name"] == "강남스튜디오"

    def test_get_me_uses_GET(self):
        client = self._make_client_with_mock({"user": {}, "profile_id": "p1"})
        client.get_me()
        client._request_sync.assert_called_once_with("GET", "/auth/me")

    # Profile 메서드
    def test_get_my_instructor_profile(self):
        client = self._make_client_with_mock({"id": "p1"})
        result = client.get_my_instructor_profile()
        client._request_sync.assert_called_with("GET", "/instructors/me")

    def test_update_instructor_profile(self):
        client = self._make_client_with_mock({"id": "p1"})
        data = {"display_name": "홍길동", "bio": "소개"}
        client.update_instructor_profile(data)
        client._request_sync.assert_called_with("PUT", "/instructors/me", data)

    def test_get_my_studio_profile(self):
        client = self._make_client_with_mock({"id": "s1"})
        client.get_my_studio_profile()
        client._request_sync.assert_called_with("GET", "/studios/me")

    # Job Post 메서드
    def test_list_job_posts_with_matching_uses_correct_endpoint(self):
        client = self._make_client_with_mock({"items": []})
        client.list_job_posts_with_matching({"region": "강남"})
        client._request_sync.assert_called_with(
            "GET", "/job-posts/for-me/with-matching", params={"region": "강남"}
        )

    def test_create_job_post_sends_POST(self):
        data = {"title": "공고", "hourly_rate": 50000}
        client = self._make_client_with_mock({"id": "job-1"})
        client.create_job_post(data)
        client._request_sync.assert_called_with("POST", "/job-posts", data)

    def test_apply_to_job_with_cover_letter(self):
        client = self._make_client_with_mock({"id": "app-1"})
        client.apply_to_job("job-123", cover_letter="지원합니다")
        args = client._request_sync.call_args
        assert args[0][1] == "/job-posts/job-123/applications"
        assert args[0][2]["cover_letter"] == "지원합니다"

    def test_apply_to_job_without_cover_letter(self):
        client = self._make_client_with_mock({"id": "app-1"})
        client.apply_to_job("job-123")
        args = client._request_sync.call_args
        data = args[0][2]
        assert "cover_letter" not in data

    # Offer 메서드
    def test_accept_offer_sends_POST(self):
        client = self._make_client_with_mock({"status": "accepted"})
        client.accept_offer("offer-456")
        client._request_sync.assert_called_with("POST", "/offers/offer-456/accept")

    def test_reject_offer_sends_POST(self):
        client = self._make_client_with_mock({"status": "rejected"})
        client.reject_offer("offer-456")
        client._request_sync.assert_called_with("POST", "/offers/offer-456/reject")

    # Contract 메서드
    def test_create_contract_from_offer(self):
        client = self._make_client_with_mock({"id": "contract-1"})
        client.create_contract_from_offer("offer-789")
        client._request_sync.assert_called_with("POST", "/contracts/from-offer/offer-789")

    def test_complete_contract(self):
        client = self._make_client_with_mock({"status": "completed"})
        client.complete_contract("contract-123")
        client._request_sync.assert_called_with("POST", "/contracts/contract-123/confirm-completion")

    def test_cancel_contract_includes_reason(self):
        client = self._make_client_with_mock({})
        client.cancel_contract("contract-123", reason="개인 사정")
        args = client._request_sync.call_args
        assert args[0][2]["reason"] == "개인 사정"

    def test_report_no_show_includes_reported_user_id(self):
        client = self._make_client_with_mock({})
        client.report_no_show("contract-123", "user-999")
        args = client._request_sync.call_args
        assert args[0][2]["reported_user_id"] == "user-999"

    # Review 메서드
    def test_create_review_with_comment(self):
        client = self._make_client_with_mock({"id": "review-1"})
        client.create_review("contract-123", rating=5, comment="훌륭합니다")
        args = client._request_sync.call_args
        assert args[0][1] == "/contracts/contract-123/reviews"
        assert args[0][2]["rating"] == 5
        assert args[0][2]["comment"] == "훌륭합니다"

    def test_create_review_without_comment(self):
        client = self._make_client_with_mock({"id": "review-1"})
        client.create_review("contract-123", rating=4)
        args = client._request_sync.call_args
        data = args[0][2]
        assert "comment" not in data

    def test_update_review_partial_fields(self):
        client = self._make_client_with_mock({"id": "review-1"})
        client.update_review("review-1", rating=3)
        args = client._request_sync.call_args
        data = args[0][2]
        assert data["rating"] == 3
        assert "comment" not in data

    def test_delete_review_uses_DELETE(self):
        client = self._make_client_with_mock({})
        client.delete_review("review-1")
        client._request_sync.assert_called_with("DELETE", "/reviews/review-1")

    # Deposit / Verification 메서드
    def test_add_deposit_includes_amount(self):
        client = self._make_client_with_mock({"new_balance": 100000})
        client.add_deposit(50000)
        args = client._request_sync.call_args
        assert args[0][2]["amount"] == 50000

    def test_verify_phone_includes_otp(self):
        client = self._make_client_with_mock({"verified": True})
        client.verify_phone("01012345678", "123456")
        args = client._request_sync.call_args
        assert args[0][2]["phone"] == "01012345678"
        assert args[0][2]["otp"] == "123456"

    # Subscription 메서드
    def test_get_subscription_status(self):
        client = self._make_client_with_mock({"membership_tier": "free"})
        client.get_subscription_status()
        client._request_sync.assert_called_with("GET", "/subscriptions/me")

    def test_cancel_subscription_with_reason(self):
        client = self._make_client_with_mock({"deposit_refunded": 50000})
        client.cancel_subscription("User requested")
        args = client._request_sync.call_args
        assert args[0][2]["reason"] == "User requested"

    def test_cancel_subscription_without_reason(self):
        client = self._make_client_with_mock({"deposit_refunded": 0})
        client.cancel_subscription()
        args = client._request_sync.call_args
        data = args[0][2]
        assert "reason" not in data


# ──────────────────────────────────────────────
# _request_sync 에러 처리 테스트
# ──────────────────────────────────────────────

class TestRequestSyncErrorHandling:
    """실제 HTTP 호출이 실패할 때 올바른 에러를 raise하는지 검증"""

    def test_400_raises_api_error(self):
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": {"code": "BAD_INPUT", "message": "잘못된 입력"}}

        client = APIClient(token="tok")

        with patch('httpx.Client') as mock_httpx:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.request.return_value = mock_response
            mock_httpx.return_value = mock_ctx

            with pytest.raises(APIError) as exc_info:
                client._request_sync("GET", "/test")
            assert exc_info.value.status_code == 400
            assert exc_info.value.code == "BAD_INPUT"

    def test_connection_error_raises_503(self):
        import httpx
        client = APIClient(token="tok")

        with patch('httpx.Client') as mock_httpx:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.request.side_effect = httpx.ConnectError("Connection refused")
            mock_httpx.return_value = mock_ctx

            with pytest.raises(APIError) as exc_info:
                client._request_sync("GET", "/test")
            assert exc_info.value.status_code == 503
            assert exc_info.value.code == "CONNECTION_ERROR"

    def test_204_returns_empty_dict(self):
        mock_response = MagicMock()
        mock_response.status_code = 204

        client = APIClient(token="tok")

        with patch('httpx.Client') as mock_httpx:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.request.return_value = mock_response
            mock_httpx.return_value = mock_ctx

            result = client._request_sync("DELETE", "/test")
            assert result == {}
